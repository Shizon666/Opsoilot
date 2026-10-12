"""Format loaders → unified Document. HTML is reserved (skip)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.rag.document import Document
from app.rag.loaders.common import LoadError
from app.rag.loaders.docx_loader import load_docx
from app.rag.loaders.html_loader import load_html
from app.rag.loaders.markdown_loader import load_markdown
from app.rag.loaders.pdf_loader import load_pdf
from app.rag.loaders.txt_loader import load_txt

__all__ = ["LoadError", "load_document"]


def load_document(
    *,
    source_type: str,
    source_file: Path,
    catalog_entry: dict[str, Any],
) -> Document:
    if source_type == "markdown":
        return load_markdown(source_file, catalog_entry)
    if source_type == "txt":
        return load_txt(source_file, catalog_entry)
    if source_type == "pdf":
        return load_pdf(source_file, catalog_entry)
    if source_type == "docx":
        return load_docx(source_file, catalog_entry)
    if source_type == "html":
        return load_html(source_file, catalog_entry)
    raise LoadError("unsupported_source_type", f"unsupported source_type={source_type}")
