"""Milvus retriever for search_knowledge. Hit JSON shape is Phase A (unchanged)."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

from app.rag.catalog import default_catalog_path, load_catalog
from app.rag.embedding import EmbedError, embed_texts
from app.rag.index import load_repo_env
from app.rag.local_store import MIN_RELIABLE_SCORE, confidence_level_for_score
from app.rag.milvus_store import collection_name, connect, milvus_uri

logger = logging.getLogger(__name__)

HIT_KEYS = (
    "doc_id",
    "title",
    "path",
    "section",
    "snippet",
    "score",
    "confidence_level",
)
DEFAULT_TOP_K = 5
MAX_TOP_K = 5
SNIPPET_MAX = 600


@lru_cache(maxsize=1)
def _path_by_doc_id() -> dict[str, str]:
    try:
        catalog = load_catalog(default_catalog_path())
    except Exception:
        logger.exception("catalog load failed; hits.path will be empty")
        return {}
    out: dict[str, str] = {}
    for entry in catalog.get("documents") or []:
        if not isinstance(entry, dict):
            continue
        doc_id = str(entry.get("doc_id") or "")
        source_path = str(entry.get("source_path") or "")
        if doc_id and source_path:
            out[doc_id] = source_path
    return out


def _clip_snippet(text: str) -> str:
    snippet = (text or "").strip()
    if len(snippet) > SNIPPET_MAX:
        return snippet[:SNIPPET_MAX] + "…"
    return snippet


def hit_from_search_row(row: dict[str, Any], *, min_score: float) -> dict[str, object] | None:
    """Map one Milvus search row to a Tool hit. Drop rows below min_score."""
    entity = row.get("entity") if isinstance(row.get("entity"), dict) else row
    if not isinstance(entity, dict):
        return None
    raw_score = row.get("distance")
    if raw_score is None:
        raw_score = row.get("score")
    try:
        score = round(float(raw_score), 4)
    except (TypeError, ValueError):
        return None
    if score < min_score:
        return None
    meta = entity.get("metadata") if isinstance(entity.get("metadata"), dict) else {}
    doc_id = str(entity.get("doc_id") or "")
    title = str(meta.get("title") or "")
    section = str(meta.get("section") or "")
    path = str(meta.get("source_path") or _path_by_doc_id().get(doc_id, ""))
    content = str(entity.get("content") or "")
    return {
        "doc_id": doc_id,
        "title": title,
        "path": path,
        "section": section,
        "snippet": _clip_snippet(content),
        "score": score,
        "confidence_level": confidence_level_for_score(score),
    }


def _search(query_vec: list[float], *, top_k: int) -> list[dict[str, Any]]:
    client = connect()
    target = collection_name()
    results = client.search(
        collection_name=target,
        data=[query_vec],
        limit=top_k,
        output_fields=["doc_id", "content", "metadata", "chunk_id"],
        search_params={"metric_type": "COSINE", "params": {}},
    )
    if not results:
        return []
    first = results[0]
    if not isinstance(first, list):
        return []
    return [row for row in first if isinstance(row, dict)]


def retrieve(query: str, *, top_k: int = DEFAULT_TOP_K) -> list[dict[str, object]]:
    """Embed query with BGE-M3, search active collection, return Phase A hits (or [])."""
    load_repo_env()
    q = (query or "").strip()
    if not q:
        return []
    k = max(1, min(int(top_k), MAX_TOP_K))
    threshold = MIN_RELIABLE_SCORE
    target = collection_name()
    try:
        vectors = embed_texts([q])
    except EmbedError:
        logger.exception("query embedding failed uri=%s", milvus_uri())
        return []
    except Exception:
        logger.exception("query embedding failed")
        return []
    if not vectors:
        return []
    try:
        rows = _search(vectors[0], top_k=k)
    except Exception:
        logger.exception("milvus search failed collection=%s", target)
        return []
    hits: list[dict[str, object]] = []
    for row in rows:
        hit = hit_from_search_row(row, min_score=threshold)
        if hit is not None:
            hits.append(hit)
    return hits


def _eval_cases() -> dict[str, Any]:
    cases = [
        {"id": "checkout_502", "query": "checkout接口502", "expect": "CHECKOUT_RUNBOOK"},
        {"id": "auth_fail", "query": "登录认证失败", "expect": "AUTH_SERVICE"},
        {"id": "weather", "query": "今天北京天气", "expect": "EMPTY"},
    ]
    report: list[dict[str, Any]] = []
    ok = True
    for case in cases:
        hits = retrieve(str(case["query"]), top_k=5)
        payload = {
            "query": case["query"],
            "hit_count": len(hits),
            "hits": hits,
        }
        expect = case["expect"]
        passed = False
        if expect == "CHECKOUT_RUNBOOK":
            passed = any(
                str(h.get("doc_id", "")).startswith("OPS-RB-CHECKOUT")
                or "Checkout" in str(h.get("title", ""))
                for h in hits
            )
        elif expect == "AUTH_SERVICE":
            passed = any(
                "AUTH" in str(h.get("doc_id", "")).upper()
                or "Auth" in str(h.get("title", ""))
                or "登录" in str(h.get("title", ""))
                for h in hits
            )
        elif expect == "EMPTY":
            passed = len(hits) == 0
        payload["passed"] = passed
        payload["expect"] = expect
        if not passed:
            ok = False
        report.append(payload)
    return {"ok": ok, "collection": collection_name(), "cases": report}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_repo_env()
    result = _eval_cases()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
