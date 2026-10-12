"""Processed-artifact inventory and index count integrity (no Milvus I/O)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.rag.catalog import default_catalog_path, eligible_entries, load_catalog

logger = logging.getLogger(__name__)


class IndexIntegrityError(RuntimeError):
    """Raised when index inputs or post-index counts are incomplete/inconsistent."""


def documents_dir(ops_root: Path) -> Path:
    return ops_root / "processed" / "documents"


def chunks_dir(ops_root: Path) -> Path:
    return ops_root / "processed" / "chunks"


def resolve_catalog_path(ops_root: Path, catalog_path: Path | None = None) -> Path:
    if catalog_path is not None:
        return catalog_path
    local = ops_root / "catalog.yaml"
    if local.is_file():
        return local
    return default_catalog_path()


def build_processed_inventory(
    ops_root: Path,
    *,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    """Compare catalog-eligible docs against processed documents/chunks on disk.

    A document counts toward expected_chunks only when:
    - Document JSON exists with parse_status == \"ok\"
    - Chunk JSON exists with chunk_count > 0 and a non-empty chunks list
    Parse failures and missing artifacts are listed in problems (never counted as ready).
    """
    cat_path = resolve_catalog_path(ops_root, catalog_path)
    catalog = load_catalog(cat_path)
    entries = eligible_entries(catalog)
    doc_dir = documents_dir(ops_root)
    chunk_dir = chunks_dir(ops_root)

    problems: list[dict[str, str]] = []
    per_document: list[dict[str, Any]] = []
    expected_chunks = 0
    ok_docs = 0

    for entry in entries:
        doc_id = str(entry.get("doc_id") or "")
        if not doc_id:
            problems.append({"doc_id": "", "error": "missing_doc_id_in_catalog"})
            continue
        doc_path = doc_dir / f"{doc_id}.json"
        chunk_path = chunk_dir / f"{doc_id}.json"
        row: dict[str, Any] = {
            "doc_id": doc_id,
            "parse_status": None,
            "chunk_count": 0,
            "ready": False,
        }
        if not doc_path.is_file():
            problems.append({"doc_id": doc_id, "error": "missing_document_json"})
            per_document.append(row)
            continue
        try:
            doc_data = json.loads(doc_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append({"doc_id": doc_id, "error": f"document_json_unreadable:{exc}"})
            per_document.append(row)
            continue
        if not isinstance(doc_data, dict):
            problems.append({"doc_id": doc_id, "error": "document_json_not_object"})
            per_document.append(row)
            continue
        parse_status = str(doc_data.get("parse_status") or "")
        row["parse_status"] = parse_status
        if parse_status != "ok":
            problems.append({"doc_id": doc_id, "error": f"parse_status_not_ok:{parse_status or '(empty)'}"})
            per_document.append(row)
            continue
        if not chunk_path.is_file():
            problems.append({"doc_id": doc_id, "error": "missing_chunk_json"})
            per_document.append(row)
            continue
        try:
            chunk_data = json.loads(chunk_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append({"doc_id": doc_id, "error": f"chunk_json_unreadable:{exc}"})
            per_document.append(row)
            continue
        if not isinstance(chunk_data, dict):
            problems.append({"doc_id": doc_id, "error": "chunk_json_not_object"})
            per_document.append(row)
            continue
        items = chunk_data.get("chunks")
        if not isinstance(items, list) or not items:
            problems.append({"doc_id": doc_id, "error": "empty_or_missing_chunks"})
            per_document.append(row)
            continue
        declared = chunk_data.get("chunk_count", len(items))
        try:
            n = int(declared)
        except (TypeError, ValueError):
            n = len(items)
        if n != len(items):
            problems.append(
                {
                    "doc_id": doc_id,
                    "error": f"chunk_count_mismatch:declared={declared},actual={len(items)}",
                }
            )
            per_document.append(row)
            continue
        # Only count chunks that would be accepted by load_chunks (chunk_id + content).
        usable = sum(
            1
            for item in items
            if isinstance(item, dict) and item.get("chunk_id") and item.get("content")
        )
        if usable != n:
            problems.append(
                {
                    "doc_id": doc_id,
                    "error": f"unusable_chunks:usable={usable},declared={n}",
                }
            )
            per_document.append(row)
            continue
        row["chunk_count"] = n
        row["ready"] = True
        ok_docs += 1
        expected_chunks += n
        per_document.append(row)

    return {
        "catalog_eligible": len(entries),
        "ok_documents": ok_docs,
        "expected_chunks": expected_chunks,
        "problems": problems,
        "per_document": per_document,
        "catalog": str(cat_path.resolve()),
        "documents_dir": str(doc_dir.resolve()),
        "chunks_dir": str(chunk_dir.resolve()),
    }


def assert_index_inputs_ready(
    ops_root: Path,
    *,
    catalog_path: Path | None = None,
) -> int:
    """Require full eligible coverage with ok parse + non-empty chunks. Return expected_chunks."""
    inv = build_processed_inventory(ops_root, catalog_path=catalog_path)
    if inv["problems"]:
        sample = inv["problems"][:8]
        raise IndexIntegrityError(
            f"index inputs incomplete: eligible={inv['catalog_eligible']} "
            f"ok_documents={inv['ok_documents']} problems={len(inv['problems'])} sample={sample}"
        )
    expected = int(inv["expected_chunks"])
    if expected < 1:
        raise IndexIntegrityError("index inputs empty: expected_chunks=0")
    if int(inv["ok_documents"]) != int(inv["catalog_eligible"]):
        raise IndexIntegrityError(
            f"ok_documents={inv['ok_documents']} != catalog_eligible={inv['catalog_eligible']}"
        )
    return expected


def assert_index_counts_match(report: dict[str, Any], *, expected_chunks: int) -> None:
    """Require chunks/embedded/inserted/count all equal expected_chunks (abort detection)."""
    if expected_chunks < 1:
        raise IndexIntegrityError(f"invalid expected_chunks={expected_chunks}")
    keys = ("chunks", "embedded", "inserted", "count")
    values = {}
    for key in keys:
        try:
            values[key] = int(report[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise IndexIntegrityError(f"report missing/invalid {key}") from exc
    mismatched = {k: v for k, v in values.items() if v != expected_chunks}
    if mismatched:
        raise IndexIntegrityError(
            f"index count mismatch: expected_chunks={expected_chunks} got={values}"
        )
