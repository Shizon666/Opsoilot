"""Markdown loader: YAML front matter + ATX headings."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from app.rag.document import Document, DocumentElement
from app.rag.loaders.common import (
    LoadError,
    build_document,
    content_hash,
    merge_metadata,
)

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.+)$")


def parse_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    m = _FRONT_MATTER_RE.match(raw)
    if not m:
        return {}, raw
    data = yaml.safe_load(m.group(1)) or {}
    if not isinstance(data, dict):
        raise LoadError("invalid_front_matter", "front matter is not a mapping")
    return data, raw[m.end() :]


def _flush_buffer(buffer: list[str], kind: str, location: str, elements: list[DocumentElement]) -> None:
    if not buffer:
        return
    text = "\n".join(buffer).strip()
    buffer.clear()
    if not text:
        return
    el_type = "list" if kind == "list" else "paragraph"
    elements.append(DocumentElement(type=el_type, text=text, source_location=location))


def parse_markdown_body(body: str) -> list[DocumentElement]:
    elements: list[DocumentElement] = []
    location = "全文"
    buffer: list[str] = []
    kind = "paragraph"
    for line in body.splitlines():
        heading = _HEADING_RE.match(line)
        if heading:
            _flush_buffer(buffer, kind, location, elements)
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                location = title
            else:
                location = title
            elements.append(
                DocumentElement(type="heading", text=title, source_location=location, level=level)
            )
            kind = "paragraph"
            continue
        if not line.strip():
            _flush_buffer(buffer, kind, location, elements)
            kind = "paragraph"
            continue
        if _LIST_RE.match(line):
            if kind != "list":
                _flush_buffer(buffer, kind, location, elements)
                kind = "list"
            buffer.append(line.rstrip())
            continue
        if kind == "list":
            _flush_buffer(buffer, kind, location, elements)
            kind = "paragraph"
        buffer.append(line.rstrip())
    _flush_buffer(buffer, kind, location, elements)
    return elements


def load_markdown(source_file: Path, catalog_entry: dict[str, Any]) -> Document:
    raw = source_file.read_text(encoding="utf-8")
    file_meta, body = parse_front_matter(raw)
    meta = merge_metadata(catalog_entry, file_meta)
    elements = parse_markdown_body(body)
    return build_document(meta=meta, elements=elements, content_hash_hex=content_hash(source_file))
