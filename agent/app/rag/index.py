"""Phase C-3.3: chunks JSON → SiliconFlow embedding → Milvus collection."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from app.rag.catalog import default_ops_root, repo_root
from app.rag.embedding import EmbedError, embed_dim, embed_model_name, embed_texts
from app.rag.integrity import (
    IndexIntegrityError,
    assert_index_counts_match,
    assert_index_inputs_ready,
)
from app.rag.milvus_store import (
    DEFAULT_COLLECTION,
    ENV_COLLECTION,
    collection_name,
    connect,
    count_rows,
    insert_rows,
    milvus_uri,
    rebuild_collection,
)

logger = logging.getLogger(__name__)

META_KEYS = (
    "title",
    "category",
    "service",
    "department",
    "severity",
    "source_type",
    "section",
)


def load_repo_env() -> None:
    """Fill missing process env from repo .env. Never logs secret values."""
    path = repo_root() / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def chunks_dir(ops_root: Path) -> Path:
    return ops_root / "processed" / "chunks"


def load_chunks(input_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("chunks") if isinstance(data, dict) else None
        if not isinstance(items, list):
            logger.warning("skip %s: no chunks[]", path.name)
            continue
        for item in items:
            if isinstance(item, dict) and item.get("chunk_id") and item.get("content"):
                rows.append(item)
    rows.sort(key=lambda r: str(r.get("chunk_id")))
    return rows


def embed_input(chunk: dict[str, Any]) -> str:
    title = str(chunk.get("title") or "").strip()
    section = str(chunk.get("section") or "").strip()
    content = str(chunk.get("content") or "").strip()
    parts = [p for p in (title, section, content) if p]
    return "\n".join(parts)


def to_milvus_row(chunk: dict[str, Any], vector: list[float]) -> dict[str, Any]:
    metadata = {key: chunk.get(key, "") for key in META_KEYS}
    return {
        "chunk_id": str(chunk["chunk_id"]),
        "doc_id": str(chunk.get("doc_id") or ""),
        "content": str(chunk.get("content") or ""),
        "embedding": vector,
        "metadata": metadata,
    }


def resolve_collection(explicit: str | None) -> str:
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    return collection_name()


def index_all(
    *,
    ops_root: Path,
    collection: str | None = None,
    allow_drop_default: bool = False,
    expected_chunks: int | None = None,
) -> dict[str, Any]:
    target = resolve_collection(collection)
    # Default collection: full catalog coverage required before any Milvus I/O.
    # Isolated collections: optional expected_chunks; still count-check after write.
    if target == DEFAULT_COLLECTION:
        ready = assert_index_inputs_ready(ops_root)
        if expected_chunks is not None and expected_chunks != ready:
            raise IndexIntegrityError(
                f"expected_chunks override {expected_chunks} != inventory {ready}"
            )
        expected_chunks = ready
    input_dir = chunks_dir(ops_root)
    chunks = load_chunks(input_dir)
    if expected_chunks is not None and len(chunks) != expected_chunks:
        raise IndexIntegrityError(
            f"loaded chunks={len(chunks)} != expected_chunks={expected_chunks}"
        )
    texts = [embed_input(c) for c in chunks]
    vectors = embed_texts(texts)
    if len(vectors) != len(chunks):
        raise EmbedError("embedded count != chunks")
    rows = [to_milvus_row(chunk, vec) for chunk, vec in zip(chunks, vectors, strict=True)]
    client = connect()
    rebuilt = rebuild_collection(client, name=target, allow_drop_default=allow_drop_default)
    inserted = insert_rows(client, rows, name=rebuilt)
    counted = count_rows(client, name=rebuilt)
    report = {
        "phase": "C-3.3",
        "chunks": len(chunks),
        "embedded": len(vectors),
        "inserted": inserted,
        "collection": rebuilt,
        "count": counted,
        "model": embed_model_name(),
        "dim": embed_dim(),
        "milvus_uri": milvus_uri(),
        "input_dir": str(input_dir.resolve()),
        "allow_drop_default": allow_drop_default,
        "expected_chunks": expected_chunks if expected_chunks is not None else len(chunks),
        "rerank": False,
        "hybrid_search": False,
    }
    assert_index_counts_match(report, expected_chunks=int(report["expected_chunks"]))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="C-3.3 index chunks into Milvus (no Tool / Graph changes)")
    parser.add_argument("--ops-root", type=Path, default=None)
    parser.add_argument(
        "--collection",
        default=None,
        help=f"Milvus collection name (default: env {ENV_COLLECTION} or {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--allow-drop-default-collection",
        action="store_true",
        help=f"Required to drop/rebuild protected default collection {DEFAULT_COLLECTION}",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_repo_env()
    ops_root = args.ops_root or default_ops_root()
    target = resolve_collection(args.collection)
    if args.collection:
        os.environ[ENV_COLLECTION] = target
    try:
        report = index_all(
            ops_root=ops_root,
            collection=target,
            allow_drop_default=args.allow_drop_default_collection,
        )
    except IndexIntegrityError as exc:
        logger.error("index integrity failed: %s", exc)
        raise SystemExit(1) from exc
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
