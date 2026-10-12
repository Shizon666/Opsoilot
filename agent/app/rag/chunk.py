"""Phase C-3.2: Document JSON → Chunk JSON. No embedding, no Milvus."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from app.rag.catalog import default_ops_root, eligible_entries, load_catalog
from app.rag.chunking import chunk_document
from app.rag.document import Document
from app.rag.integrity import assert_index_inputs_ready, resolve_catalog_path

logger = logging.getLogger(__name__)


def documents_dir(ops_root: Path) -> Path:
    return ops_root / "processed" / "documents"


def chunks_dir(ops_root: Path) -> Path:
    return ops_root / "processed" / "chunks"


def load_processed_documents(input_dir: Path) -> tuple[list[Document], list[dict[str, str]]]:
    paths = sorted(input_dir.glob("*.json"))
    docs: list[Document] = []
    skipped: list[dict[str, str]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            skipped.append({"doc_id": path.stem, "error": "document_json_not_object"})
            logger.warning("skip %s: not an object", path.name)
            continue
        parse_status = data.get("parse_status")
        if parse_status != "ok":
            skipped.append(
                {
                    "doc_id": str(data.get("doc_id") or path.stem),
                    "error": f"parse_status_not_ok:{parse_status or '(empty)'}",
                }
            )
            logger.warning("skip %s: not an ok Document JSON", path.name)
            continue
        docs.append(Document.from_dict(data))
    return docs, skipped


def write_chunks(out_dir: Path, doc: Document, chunks: list[Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{doc.doc_id}.json"
    payload = {
        "doc_id": doc.doc_id,
        "chunk_count": len(chunks),
        "chunks": [c.to_dict() for c in chunks],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _purge_chunk(out_dir: Path, doc_id: str) -> None:
    path = out_dir / f"{doc_id}.json"
    if path.is_file():
        path.unlink()
        logger.warning("purged stale chunk artifact %s", path)


def chunk_all(*, ops_root: Path) -> dict[str, Any]:
    in_dir = documents_dir(ops_root)
    out_dir = chunks_dir(ops_root)
    docs, skipped_parse = load_processed_documents(in_dir)
    by_category: Counter[str] = Counter()
    by_source_type: Counter[str] = Counter()
    doc_rows: list[dict[str, Any]] = []
    total_chunks = 0
    failed: list[dict[str, str]] = list(skipped_parse)

    for doc in docs:
        try:
            chunks = chunk_document(doc)
        except Exception as exc:  # noqa: BLE001 — CLI report, continue others
            failed.append({"doc_id": doc.doc_id, "error": str(exc)})
            _purge_chunk(out_dir, doc.doc_id)
            logger.error("chunk failed %s: %s", doc.doc_id, exc)
            continue
        if not chunks:
            failed.append({"doc_id": doc.doc_id, "error": "no_chunks"})
            _purge_chunk(out_dir, doc.doc_id)
            continue
        write_chunks(out_dir, doc, chunks)
        total_chunks += len(chunks)
        by_category[doc.category] += len(chunks)
        by_source_type[doc.source_type] += len(chunks)
        doc_rows.append(
            {
                "doc_id": doc.doc_id,
                "category": doc.category,
                "source_type": doc.source_type,
                "chunk_count": len(chunks),
                "sections": [c.section for c in chunks],
            }
        )

    catalog = load_catalog(resolve_catalog_path(ops_root))
    eligible = len(eligible_entries(catalog))
    return {
        "phase": "C-3.2",
        "catalog_eligible": eligible,
        "documents": len(docs),
        "chunks": total_chunks,
        "failed": len(failed),
        "by_category": dict(by_category),
        "by_source_type": dict(by_source_type),
        "input_dir": str(in_dir.resolve()),
        "output_dir": str(out_dir.resolve()),
        "embedding": False,
        "milvus": False,
        "rerank": False,
        "per_document": doc_rows,
        "failures": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="C-3.2 Knowledge Chunk Pipeline (no embedding / no Milvus)")
    parser.add_argument("--ops-root", type=Path, default=default_ops_root())
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = chunk_all(ops_root=args.ops_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Fail closed: no chunk failures; every eligible doc must be inventory-ready.
    if report["failed"] or report["documents"] != report["catalog_eligible"]:
        raise SystemExit(1)
    try:
        expected = assert_index_inputs_ready(args.ops_root)
    except Exception as exc:  # noqa: BLE001 — CLI gate
        logger.error("chunk inventory gate failed: %s", exc)
        raise SystemExit(1) from exc
    if report["chunks"] != expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
