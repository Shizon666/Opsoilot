"""PDF loader: text layer only (no OCR). Sidecar metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.rag.document import Document, DocumentElement
from app.rag.loaders.common import (
    LoadError,
    build_document,
    content_hash,
    merge_metadata,
    read_sidecar,
)


def _outline_titles(reader: PdfReader) -> dict[int, str]:
    titles: dict[int, str] = {}
    try:
        outline = reader.outline
    except Exception:
        return titles
    if not outline:
        return titles

    def walk(items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, list):
                walk(item)
                continue
            title = getattr(item, "title", None) or (item.get("title") if isinstance(item, dict) else None)
            if not title:
                continue
            try:
                dest = reader.get_destination_page_number(item)
            except Exception:
                dest = None
            if dest is not None:
                titles[int(dest) + 1] = str(title).strip()

    walk(outline)
    return titles


def extract_pdf_elements(source_file: Path) -> list[DocumentElement]:
    try:
        reader = PdfReader(str(source_file))
    except Exception as exc:
        raise LoadError("pdf_open_failed", f"cannot open pdf: {exc}") from exc
    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception as exc:
            raise LoadError("pdf_encrypted", "encrypted pdf is not supported") from exc

    bookmarks = _outline_titles(reader)
    elements: list[DocumentElement] = []
    for i, page in enumerate(reader.pages, start=1):
        loc = f"p.{i}"
        raw = page.extract_text() or ""
        text = raw.strip()
        heading = bookmarks.get(i)
        if heading:
            elements.append(DocumentElement(type="heading", text=heading, source_location=loc, level=2))
        if i > 1:
            elements.append(DocumentElement(type="page_break", text="", source_location=loc))
        if text:
            elements.append(DocumentElement(type="paragraph", text=text, source_location=loc))
    if not any(el.type == "paragraph" and el.text.strip() for el in elements):
        raise LoadError("pdf_no_text_layer", f"{source_file.name} has no extractable text layer")
    return elements


def load_pdf(source_file: Path, catalog_entry: dict[str, Any]) -> Document:
    file_meta = read_sidecar(source_file)
    meta = merge_metadata(catalog_entry, file_meta)
    elements = extract_pdf_elements(source_file)
    return build_document(meta=meta, elements=elements, content_hash_hex=content_hash(source_file))
