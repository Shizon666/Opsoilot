"""TXT loader: sidecar metadata, encoding detect, blank-line paragraphs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from charset_normalizer import from_bytes

from app.rag.document import Document, DocumentElement
from app.rag.loaders.common import (
    LoadError,
    build_document,
    content_hash,
    merge_metadata,
    read_sidecar,
)


def decode_txt(source_file: Path) -> str:
    data = source_file.read_bytes()
    match = from_bytes(data).best()
    if match is not None:
        text = str(match)
        if text.strip():
            return text
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LoadError("decode_failed", f"cannot decode {source_file.name}") from exc


def parse_txt_body(body: str) -> list[DocumentElement]:
    chunks = [p.strip() for p in body.replace("\r\n", "\n").split("\n\n") if p.strip()]
    if not chunks:
        raise LoadError("empty_txt", "txt body is empty")
    if len(chunks) == 1:
        return [DocumentElement(type="paragraph", text=chunks[0], source_location="全文")]
    return [
        DocumentElement(type="paragraph", text=text, source_location=f"段{i}")
        for i, text in enumerate(chunks, start=1)
    ]


def load_txt(source_file: Path, catalog_entry: dict[str, Any]) -> Document:
    file_meta = read_sidecar(source_file)
    meta = merge_metadata(catalog_entry, file_meta)
    body = decode_txt(source_file)
    elements = parse_txt_body(body)
    return build_document(meta=meta, elements=elements, content_hash_hex=content_hash(source_file))
