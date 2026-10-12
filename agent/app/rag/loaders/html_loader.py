"""HTML loader: V1 reserved. Catalog must not include html; encountering it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.rag.document import Document
from app.rag.loaders.common import LoadError


def load_html(_source_file: Path, catalog_entry: dict[str, Any]) -> Document:
    doc_id = catalog_entry.get("doc_id", "?")
    raise LoadError("html_not_implemented", f"html source_type is reserved in V1; skip {doc_id}")
