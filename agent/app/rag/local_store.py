"""V1 local embedding RAG: Runbook chunks + cosine over a file index (no Milvus)."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
METRIC = "COSINE"
# BGE Chinese retrieval query prefix (documents encoded without prefix).
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

MIN_RELIABLE_SCORE = float(os.getenv("KNOWLEDGE_MIN_SCORE", "0.45"))
_CONFIDENCE_NEAR_BAND = float(os.getenv("KNOWLEDGE_CONFIDENCE_BAND", "0.08"))

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class KnowledgeChunk:
    doc_id: str
    title: str
    path: str
    section: str
    text: str


def runbook_dir() -> Path:
    env = (os.getenv("KNOWLEDGE_RUNBOOK_DIR") or "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "knowledge" / "runbooks"


def index_dir() -> Path:
    env = (os.getenv("KNOWLEDGE_INDEX_DIR") or "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data" / "knowledge_index"


def confidence_level_for_score(score: float) -> str:
    """Map cosine score → confidence_level. Not a factuality label."""
    if score >= MIN_RELIABLE_SCORE + _CONFIDENCE_NEAR_BAND:
        return "high"
    if score >= MIN_RELIABLE_SCORE:
        return "medium"
    return "low"


def _parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    m = _FRONT_MATTER_RE.match(raw)
    if not m:
        return meta, raw
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if key in {"doc_id", "title", "source", "source_type"}:
            meta[key] = val.strip().strip('"').strip("'")
    return meta, raw[m.end() :]


def _chunk_markdown(path: str, body: str, meta: dict[str, str]) -> list[KnowledgeChunk]:
    doc_id = meta.get("doc_id") or path
    title = meta.get("title") or Path(path).stem
    matches = list(_HEADING_RE.finditer(body))
    if not matches:
        text = body.strip()
        if not text:
            return []
        return [KnowledgeChunk(doc_id=doc_id, title=title, path=path, section="全文", text=text)]

    chunks: list[KnowledgeChunk] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section = match.group(1).strip()
        text = body[start:end].strip()
        if not text:
            continue
        chunks.append(
            KnowledgeChunk(doc_id=doc_id, title=title, path=path, section=section, text=text)
        )
    return chunks


def load_runbook_chunks(root: Path | None = None) -> list[KnowledgeChunk]:
    base = root or runbook_dir()
    if not base.is_dir():
        logger.warning("runbook dir missing: %s", base)
        return []
    chunks: list[KnowledgeChunk] = []
    for fp in sorted(base.glob("*.md")):
        raw = fp.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(raw)
        rel = fp.name
        chunks.extend(_chunk_markdown(rel, body, meta))
    return chunks


def chunk_embed_text(chunk: KnowledgeChunk) -> str:
    return f"{chunk.title}\n{chunk.section}\n{chunk.text}"


def _hit_dict(chunk: KnowledgeChunk, score: float) -> dict[str, object]:
    snippet = chunk.text
    if len(snippet) > 600:
        snippet = snippet[:600] + "…"
    rounded = round(float(score), 4)
    return {
        "doc_id": chunk.doc_id,
        "title": chunk.title,
        "path": chunk.path,
        "section": chunk.section,
        "snippet": snippet,
        "score": rounded,
        "confidence_level": confidence_level_for_score(rounded),
    }


@lru_cache(maxsize=1)
def _load_index() -> tuple[np.ndarray, tuple[KnowledgeChunk, ...]] | None:
    d = index_dir()
    meta_path = d / "meta.json"
    chunks_path = d / "chunks.json"
    emb_path = d / "embeddings.npy"
    if not (meta_path.is_file() and chunks_path.is_file() and emb_path.is_file()):
        logger.warning("knowledge index missing under %s (run ingest)", d)
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("model") != EMBEDDING_MODEL or meta.get("metric") != METRIC:
        logger.warning("knowledge index model/metric mismatch: %s", meta)
        return None
    raw_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = tuple(
        KnowledgeChunk(
            doc_id=str(c["doc_id"]),
            title=str(c["title"]),
            path=str(c["path"]),
            section=str(c["section"]),
            text=str(c["text"]),
        )
        for c in raw_chunks
    )
    embs = np.load(emb_path)
    if embs.ndim != 2 or embs.shape[0] != len(chunks):
        logger.warning("knowledge index shape mismatch embs=%s chunks=%s", embs.shape, len(chunks))
        return None
    return embs.astype(np.float32), chunks


def reset_index_cache() -> None:
    _load_index.cache_clear()
    _embedder.cache_clear()


@lru_cache(maxsize=1)
def _embedder() -> Any:
    from sentence_transformers import SentenceTransformer

    model_name = os.getenv("KNOWLEDGE_EMBEDDING_MODEL", EMBEDDING_MODEL)
    logger.info("loading embedding model %s", model_name)
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], *, is_query: bool = False) -> np.ndarray:
    model = _embedder()
    payload = [QUERY_PREFIX + t if is_query else t for t in texts]
    vecs = model.encode(
        payload,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vecs, dtype=np.float32)


def retrieve_with_matrix(
    query_vec: np.ndarray,
    embeddings: np.ndarray,
    chunks: tuple[KnowledgeChunk, ...] | list[KnowledgeChunk],
    *,
    top_k: int = 3,
    min_score: float | None = None,
) -> list[dict[str, object]]:
    """Pure cosine top-k (expects L2-normalized rows). Used by retrieve and tests."""
    k = max(1, min(int(top_k), 5))
    threshold = MIN_RELIABLE_SCORE if min_score is None else min_score
    q = np.asarray(query_vec, dtype=np.float32).reshape(-1)
    scores = embeddings @ q
    if scores.size == 0:
        return []
    order = np.argsort(-scores)[:k]
    hits: list[dict[str, object]] = []
    chunk_list = list(chunks)
    for idx in order:
        score = float(scores[int(idx)])
        if score < threshold:
            continue
        hits.append(_hit_dict(chunk_list[int(idx)], score))
    return hits


def retrieve(query: str, *, top_k: int = 3) -> list[dict[str, object]]:
    """Embed query, cosine against local index; empty if index/model unavailable."""
    q = (query or "").strip()
    if not q:
        return []
    loaded = _load_index()
    if loaded is None:
        return []
    embeddings, chunks = loaded
    try:
        qv = embed_texts([q], is_query=True)[0]
    except Exception:
        logger.exception("query embedding failed")
        return []
    return retrieve_with_matrix(qv, embeddings, chunks, top_k=top_k)
