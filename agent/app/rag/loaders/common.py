"""Shared metadata merge, cleaning, hashing, and Document assembly."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from app.rag.document import (
    CATEGORIES,
    REQUIRED_META,
    SEVERITIES,
    SOURCE_TYPES,
    STATUSES,
    VISIBILITIES,
    Document,
    DocumentElement,
)

logger = logging.getLogger(__name__)

MIN_HANZI = 80
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")
_HANZI_RE = re.compile(r"[\u4e00-\u9fff]")


class LoadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def sidecar_path(source_file: Path) -> Path:
    return source_file.with_name(source_file.stem + ".meta.yaml")


def read_sidecar(source_file: Path) -> dict[str, Any]:
    path = sidecar_path(source_file)
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise LoadError("invalid_sidecar", f"sidecar is not a mapping: {path}")
    return {str(k): v for k, v in data.items()}


def content_hash(source_file: Path) -> str:
    h = hashlib.sha256()
    h.update(source_file.read_bytes())
    side = sidecar_path(source_file)
    if side.is_file():
        h.update(b"\n")
        h.update(side.read_bytes())
    return h.hexdigest()


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def merge_metadata(catalog_entry: dict[str, Any], file_meta: dict[str, Any]) -> dict[str, str]:
    merged: dict[str, str] = {}
    keys = set(catalog_entry) | set(file_meta)
    for key in keys:
        if key in {"canonical", "v1_ingest"}:
            continue
        catalog_val = catalog_entry.get(key)
        file_val = file_meta.get(key)
        if file_val is not None and _stringify(file_val) != "":
            merged[key] = _stringify(file_val)
        elif catalog_val is not None and _stringify(catalog_val) != "":
            merged[key] = _stringify(catalog_val)
    catalog_id = _stringify(catalog_entry.get("doc_id"))
    file_id = _stringify(file_meta.get("doc_id"))
    if file_id and catalog_id and file_id != catalog_id:
        raise LoadError("doc_id_mismatch", f"file doc_id={file_id} != catalog {catalog_id}")
    merged["doc_id"] = catalog_id
    merged["source_path"] = _stringify(catalog_entry.get("source_path"))
    return merged


def validate_metadata(meta: dict[str, str]) -> None:
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        raise LoadError("missing_metadata", f"missing required metadata: {','.join(missing)}")
    if meta["category"] not in CATEGORIES:
        raise LoadError("invalid_category", f"category={meta['category']}")
    if meta["severity"] not in SEVERITIES:
        raise LoadError("invalid_severity", f"severity={meta['severity']}")
    if meta["source_type"] not in SOURCE_TYPES:
        raise LoadError("invalid_source_type", f"source_type={meta['source_type']}")
    visibility = meta.get("visibility", "")
    if visibility not in VISIBILITIES:
        raise LoadError("fail_closed_visibility", "visibility missing or unknown; not ingested")
    status = meta.get("status", "")
    if status not in STATUSES:
        raise LoadError("invalid_status", f"status={status or '(empty)'}")
    if status != "active":
        raise LoadError("status_not_active", f"status={status}")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = _HTML_TAG_RE.sub("", text)
    lines = [_MULTI_SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def hanzi_count(text: str) -> int:
    return len(_HANZI_RE.findall(text))


def content_from_elements(elements: list[DocumentElement]) -> str:
    parts: list[str] = []
    for el in elements:
        if el.type == "page_break":
            continue
        if el.text.strip():
            parts.append(el.text.strip())
    return clean_text("\n\n".join(parts))


def build_document(
    *,
    meta: dict[str, str],
    elements: list[DocumentElement],
    content_hash_hex: str,
) -> Document:
    validate_metadata(meta)
    content = content_from_elements(elements)
    if hanzi_count(content) < MIN_HANZI:
        raise LoadError(
            "content_too_short",
            f"{meta.get('doc_id')} cleaned content hanzi={hanzi_count(content)} < {MIN_HANZI}",
        )
    return Document(
        doc_id=meta["doc_id"],
        title=meta["title"],
        category=meta["category"],
        source_type=meta["source_type"],
        service=meta["service"],
        department=meta["department"],
        severity=meta["severity"],
        created_at=meta["created_at"],
        source_path=meta["source_path"],
        visibility=meta["visibility"],
        status=meta["status"],
        content=content,
        elements=elements,
        content_hash=content_hash_hex,
        parse_status="ok",
        version=meta.get("version", ""),
    )
