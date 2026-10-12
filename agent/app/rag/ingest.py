"""Offline ingest: Runbook Markdown → chunks → bge-small embeddings → local files."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.rag.local_store import (
    EMBEDDING_MODEL,
    METRIC,
    MIN_RELIABLE_SCORE,
    chunk_embed_text,
    embed_texts,
    index_dir,
    load_runbook_chunks,
    runbook_dir,
)

logger = logging.getLogger(__name__)


def ingest(*, src: Path | None = None, dest: Path | None = None) -> dict:
    root = src or runbook_dir()
    out = dest or index_dir()
    chunks = load_runbook_chunks(root)
    if not chunks:
        raise SystemExit(f"no runbook chunks under {root}")

    texts = [chunk_embed_text(c) for c in chunks]
    embs = embed_texts(texts, is_query=False)
    if embs.shape[0] != len(chunks):
        raise SystemExit("embedding count mismatch")

    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "embeddings.npy", embs.astype(np.float32))
    payload = [
        {
            "doc_id": c.doc_id,
            "title": c.title,
            "path": c.path,
            "section": c.section,
            "text": c.text,
        }
        for c in chunks
    ]
    (out / "chunks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {
        "model": EMBEDDING_MODEL,
        "metric": METRIC,
        "dim": int(embs.shape[1]),
        "chunk_count": len(chunks),
        "min_score_default": MIN_RELIABLE_SCORE,
        "source_dir": str(root),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("wrote index %s chunks=%s dim=%s", out, len(chunks), embs.shape[1])
    return meta


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    meta = ingest()
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
