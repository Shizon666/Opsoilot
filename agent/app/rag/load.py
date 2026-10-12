"""Phase C-3.1: load knowledge/ops/raw → Document JSON. No embedding, no Milvus."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from app.rag.catalog import default_catalog_path, default_ops_root, eligible_entries, load_catalog, resolve_source_file
from app.rag.loaders import LoadError, load_document

logger = logging.getLogger(__name__)


def processed_dir(ops_root: Path) -> Path:
    return ops_root / "processed" / "documents"


def write_document(ops_root: Path, document: Any) -> Path:
    out_dir = processed_dir(ops_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{document.doc_id}.json"
    path.write_text(json.dumps(document.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _purge_stale_processed(ops_root: Path, doc_id: str) -> None:
    """Remove prior processed artifacts so a failed parse cannot be counted as success."""
    if not doc_id:
        return
    for path in (
        processed_dir(ops_root) / f"{doc_id}.json",
        ops_root / "processed" / "chunks" / f"{doc_id}.json",
    ):
        if path.is_file():
            path.unlink()
            logger.warning("purged stale processed artifact %s", path)


def load_all(*, catalog_path: Path, ops_root: Path) -> dict[str, Any]:
    catalog = load_catalog(catalog_path)
    entries = eligible_entries(catalog)
    ok_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    by_type: Counter[str] = Counter()
    by_category: Counter[str] = Counter()

    for entry in entries:
        doc_id = str(entry.get("doc_id") or "")
        source_type = str(entry.get("source_type") or "")
        source_file = resolve_source_file(ops_root, str(entry.get("source_path") or ""))
        if source_file is None:
            failed_rows.append({"doc_id": doc_id, "error": "path_escape_or_invalid"})
            _purge_stale_processed(ops_root, doc_id)
            logger.error("skip path escape %s %s", doc_id, entry.get("source_path"))
            continue
        if not source_file.is_file():
            failed_rows.append({"doc_id": doc_id, "error": f"missing_file:{source_file.name}"})
            _purge_stale_processed(ops_root, doc_id)
            logger.error("missing file %s -> %s", doc_id, source_file)
            continue
        try:
            document = load_document(
                source_type=source_type,
                source_file=source_file,
                catalog_entry=entry,
            )
        except LoadError as exc:
            row = {"doc_id": doc_id, "error": exc.code, "message": exc.message}
            if exc.code in {"html_not_implemented"}:
                skipped_rows.append(row)
            else:
                failed_rows.append(row)
            _purge_stale_processed(ops_root, doc_id)
            logger.error("load failed %s: %s %s", doc_id, exc.code, exc.message)
            continue
        if document.parse_status != "ok":
            failed_rows.append(
                {
                    "doc_id": doc_id,
                    "error": "parse_status_not_ok",
                    "message": f"parse_status={document.parse_status}",
                }
            )
            _purge_stale_processed(ops_root, doc_id)
            logger.error("load rejected %s: parse_status=%s", doc_id, document.parse_status)
            continue
        write_document(ops_root, document)
        by_type[document.source_type] += 1
        by_category[document.category] += 1
        ok_rows.append(
            {
                "doc_id": document.doc_id,
                "title": document.title,
                "category": document.category,
                "source_type": document.source_type,
                "service": document.service,
                "department": document.department,
                "severity": document.severity,
                "created_at": document.created_at,
                "parse_status": document.parse_status,
                "hanzi": sum(1 for ch in document.content if "\u4e00" <= ch <= "\u9fff"),
                "elements": len(document.elements),
                "content_hash": document.content_hash[:12],
            }
        )

    report = {
        "phase": "C-3.1",
        "input_root": str((ops_root / "raw").resolve()),
        "catalog": str(catalog_path.resolve()),
        "catalog_eligible": len(entries),
        "ok": len(ok_rows),
        "failed": len(failed_rows),
        "skipped": len(skipped_rows),
        "by_source_type": dict(by_type),
        "by_category": dict(by_category),
        "processed_dir": str(processed_dir(ops_root)),
        "embedding": False,
        "milvus": False,
        "documents": ok_rows,
        "failures": failed_rows,
        "skips": skipped_rows,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="C-3.1 Knowledge Loader (no embedding / no Milvus)")
    parser.add_argument("--catalog", type=Path, default=default_catalog_path())
    parser.add_argument("--ops-root", type=Path, default=default_ops_root())
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = load_all(catalog_path=args.catalog, ops_root=args.ops_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Integrity: every catalog-eligible doc must parse ok; failures never count as success.
    if report["failed"] or report["skipped"] or report["ok"] != report["catalog_eligible"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
