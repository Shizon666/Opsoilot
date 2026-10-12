"""Unified Document Object (parser output, before chunk/embedding)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ParseStatus = Literal["ok", "failed"]
ElementType = Literal["heading", "paragraph", "list", "page_break"]

CATEGORIES = frozenset(
    {"RUNBOOK", "SERVICE_MANUAL", "INCIDENT_REPORT", "OPERATION_PROCESS", "SECURITY_GUIDELINE"}
)
SEVERITIES = frozenset({"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"})
SOURCE_TYPES = frozenset({"markdown", "pdf", "docx", "txt", "html"})
VISIBILITIES = frozenset({"PUBLIC", "INTERNAL"})
STATUSES = frozenset({"active", "draft", "archived"})

REQUIRED_META = (
    "doc_id",
    "title",
    "category",
    "source_type",
    "service",
    "department",
    "severity",
    "created_at",
)


@dataclass
class DocumentElement:
    type: ElementType
    text: str
    source_location: str
    level: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "text": self.text,
            "source_location": self.source_location,
        }
        if self.level is not None:
            payload["level"] = self.level
        return payload


@dataclass
class Document:
    doc_id: str
    title: str
    category: str
    source_type: str
    service: str
    department: str
    severity: str
    created_at: str
    source_path: str
    visibility: str
    status: str
    content: str
    elements: list[DocumentElement]
    content_hash: str
    parse_status: ParseStatus
    version: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["elements"] = [el.to_dict() for el in self.elements]
        extra = data.pop("extra", {}) or {}
        data.update(extra)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        elements: list[DocumentElement] = []
        for raw in data.get("elements") or []:
            if not isinstance(raw, dict):
                continue
            el_type = raw.get("type") or "paragraph"
            elements.append(
                DocumentElement(
                    type=el_type,  # type: ignore[arg-type]
                    text=str(raw.get("text") or ""),
                    source_location=str(raw.get("source_location") or ""),
                    level=raw.get("level"),
                )
            )
        return cls(
            doc_id=str(data.get("doc_id") or ""),
            title=str(data.get("title") or ""),
            category=str(data.get("category") or ""),
            source_type=str(data.get("source_type") or ""),
            service=str(data.get("service") or ""),
            department=str(data.get("department") or ""),
            severity=str(data.get("severity") or ""),
            created_at=str(data.get("created_at") or ""),
            source_path=str(data.get("source_path") or ""),
            visibility=str(data.get("visibility") or ""),
            status=str(data.get("status") or ""),
            content=str(data.get("content") or ""),
            elements=elements,
            content_hash=str(data.get("content_hash") or ""),
            parse_status=data.get("parse_status") or "ok",  # type: ignore[arg-type]
            version=str(data.get("version") or ""),
        )
