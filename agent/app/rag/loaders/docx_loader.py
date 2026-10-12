"""DOCX loader: Heading styles, lists, flattened tables. Sidecar metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator

from docx import Document as DocxFile
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.rag.document import Document, DocumentElement
from app.rag.loaders.common import (
    LoadError,
    build_document,
    content_hash,
    merge_metadata,
    read_sidecar,
)

_HEADING_RE = re.compile(r"^Heading\s+(\d+)$", re.I)


def _iter_blocks(doc: DocxFile) -> Iterator[Paragraph | Table]:
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def _is_list_paragraph(paragraph: Paragraph) -> bool:
    num_pr = paragraph._p.find(qn("w:pPr"))
    if num_pr is not None and num_pr.find(qn("w:numPr")) is not None:
        return True
    style = (paragraph.style.name or "") if paragraph.style is not None else ""
    return "List" in style


def _table_markdown(table: Table) -> str:
    rows: list[list[str]] = []
    for row in table.rows:
        cells = [" ".join(cell.text.split()) for cell in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    normalized = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(normalized[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for r in normalized[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def extract_docx_elements(source_file: Path) -> list[DocumentElement]:
    try:
        doc = DocxFile(str(source_file))
    except Exception as exc:
        raise LoadError("docx_open_failed", f"cannot open docx: {exc}") from exc

    location = "全文"
    elements: list[DocumentElement] = []
    list_buf: list[str] = []

    def flush_list() -> None:
        if not list_buf:
            return
        text = "\n".join(list_buf).strip()
        list_buf.clear()
        if text:
            elements.append(DocumentElement(type="list", text=text, source_location=location))

    for block in _iter_blocks(doc):
        if isinstance(block, Table):
            flush_list()
            md = _table_markdown(block)
            if md:
                elements.append(DocumentElement(type="paragraph", text=md, source_location=location))
            continue
        text = block.text.strip()
        style_name = (block.style.name or "") if block.style is not None else ""
        heading = _HEADING_RE.match(style_name)
        if heading:
            flush_list()
            level = int(heading.group(1))
            if not text:
                continue
            if 1 <= level <= 3:
                location = text
                elements.append(
                    DocumentElement(type="heading", text=text, source_location=location, level=level)
                )
            else:
                elements.append(DocumentElement(type="paragraph", text=text, source_location=location))
            continue
        if not text:
            flush_list()
            continue
        if _is_list_paragraph(block):
            list_buf.append(text)
            continue
        flush_list()
        elements.append(DocumentElement(type="paragraph", text=text, source_location=location))
    flush_list()
    if not elements:
        raise LoadError("docx_empty", f"{source_file.name} has no paragraphs")
    return elements


def load_docx(source_file: Path, catalog_entry: dict[str, Any]) -> Document:
    file_meta = read_sidecar(source_file)
    meta = merge_metadata(catalog_entry, file_meta)
    elements = extract_docx_elements(source_file)
    return build_document(meta=meta, elements=elements, content_hash_hex=content_hash(source_file))
