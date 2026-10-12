"""Document JSON → chunks. No embedding, no Milvus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.rag.document import Document, DocumentElement

TARGET_HANZI = 500
OVERLAP_HANZI = 100
HARD_MAX_HANZI = 1200
MIN_SECTION_HANZI = 80

_HANZI_RE = re.compile(r"[\u4e00-\u9fff]")
_HEADING_SPLIT_LEVELS = frozenset({2, 3})


@dataclass
class KnowledgeChunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    service: str
    department: str
    severity: str
    source_type: str
    section: str
    content: str
    source_path: str = ""
    visibility: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "category": self.category,
            "service": self.service,
            "department": self.department,
            "severity": self.severity,
            "source_type": self.source_type,
            "section": self.section,
            "content": self.content,
            "source_path": self.source_path,
            "visibility": self.visibility,
            "created_at": self.created_at,
        }


def hanzi_count(text: str) -> int:
    return len(_HANZI_RE.findall(text or ""))


def _unit_size(text: str) -> int:
    n = hanzi_count(text)
    return n if n > 0 else len((text or "").strip())


def _join_units(units: list[str]) -> str:
    return "\n\n".join(u.strip() for u in units if u and u.strip())


def _overlap_prefix(units: list[str]) -> list[str]:
    if not units:
        return []
    acc: list[str] = []
    total = 0
    for text in reversed(units):
        acc.insert(0, text)
        total += _unit_size(text)
        if total >= OVERLAP_HANZI:
            break
    return acc


def _char_windows(text: str) -> list[str]:
    chars = list(text)
    if not chars:
        return []
    # Walk by hanzi budget: advance index until hanzi_count(slice) ~= TARGET
    windows: list[str] = []
    start = 0
    n = len(chars)
    while start < n:
        end = start
        while end < n and hanzi_count("".join(chars[start:end])) < TARGET_HANZI:
            end += 1
        if end < n:
            while end < n and hanzi_count("".join(chars[start:end])) < HARD_MAX_HANZI:
                # keep going slightly if we haven't hit a paragraph break; caller already last-resort
                if hanzi_count("".join(chars[start:end])) >= TARGET_HANZI:
                    break
                end += 1
        piece = "".join(chars[start:end]).strip()
        if piece:
            windows.append(piece)
        if end >= n:
            break
        # move start forward with ~OVERLAP hanzi leftover
        back = end
        overlap = 0
        while back > start and overlap < OVERLAP_HANZI:
            back -= 1
            if "\u4e00" <= chars[back] <= "\u9fff":
                overlap += 1
        if back == start:
            start = end
        else:
            start = back
        if start >= end:
            start = end
    return windows


def pack_units(units: list[str]) -> list[str]:
    cleaned = [u.strip() for u in units if u and u.strip()]
    if not cleaned:
        return []
    windows: list[list[str]] = []
    current: list[str] = []
    current_size = 0
    for unit in cleaned:
        size = _unit_size(unit)
        if size > HARD_MAX_HANZI or size > TARGET_HANZI:
            if current:
                windows.append(current)
                current, current_size = [], 0
            windows.append([unit])
            continue
        if current and current_size + size > TARGET_HANZI:
            windows.append(current)
            current = _overlap_prefix(current)
            current_size = sum(_unit_size(u) for u in current)
            if current_size + size > HARD_MAX_HANZI:
                current, current_size = [], 0
        current.append(unit)
        current_size += size
    if current:
        windows.append(current)

    texts: list[str] = []
    for group in windows:
        joined = _join_units(group)
        if hanzi_count(joined) > HARD_MAX_HANZI and len(group) == 1:
            texts.extend(_char_windows(joined))
        elif joined.strip():
            texts.append(joined)
    return texts


def _merge_short_sections(sections: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    if not sections:
        return []
    merged: list[tuple[str, list[str]]] = []
    for name, units in sections:
        body = _join_units(units)
        if merged and hanzi_count(body) < MIN_SECTION_HANZI:
            prev_name, prev_units = merged[-1]
            merged[-1] = (prev_name, prev_units + units)
        else:
            merged.append((name, list(units)))
    if len(merged) >= 2 and hanzi_count(_join_units(merged[-1][1])) < MIN_SECTION_HANZI:
        last_name, last_units = merged.pop()
        prev_name, prev_units = merged[-1]
        merged[-1] = (prev_name, prev_units + last_units)
        _ = last_name
    return merged


def _heading_sections(elements: list[DocumentElement]) -> list[tuple[str, list[str]]] | None:
    has_split = any(
        el.type == "heading" and (el.level in _HEADING_SPLIT_LEVELS)
        for el in elements
    )
    if not has_split:
        return None
    sections: list[tuple[str, list[str]]] = []
    preamble: list[str] = []
    current_name: str | None = None
    current_units: list[str] = []
    for el in elements:
        if el.type == "page_break":
            continue
        if el.type == "heading" and el.level == 1:
            continue
        if el.type == "heading" and el.level in _HEADING_SPLIT_LEVELS:
            if current_name is None:
                preamble.extend(current_units)
            else:
                sections.append((current_name, current_units))
            current_name = el.text.strip() or el.source_location or "未命名"
            current_units = [el.text.strip()] if el.text.strip() else []
            continue
        text = (el.text or "").strip()
        if not text:
            continue
        if current_name is None:
            preamble.append(text)
        else:
            current_units.append(text)
    if current_name is not None:
        sections.append((current_name, current_units))
    if preamble:
        if sections:
            name, units = sections[0]
            sections[0] = (name, preamble + units)
        else:
            sections.append(("全文", preamble))
    return _merge_short_sections(sections)


def _page_or_plain_sections(doc: Document) -> list[tuple[str, list[str]]]:
    page_units: dict[str, list[str]] = {}
    order: list[str] = []
    for el in doc.elements:
        if el.type in {"page_break", "heading"}:
            continue
        text = (el.text or "").strip()
        if not text:
            continue
        loc = (el.source_location or "").strip()
        if loc.startswith("p.") or loc.startswith("段"):
            key = loc
        else:
            key = ""
        if key:
            if key not in page_units:
                order.append(key)
                page_units[key] = []
            page_units[key].append(text)
    if order and all(k.startswith("段") for k in order):
        units: list[str] = []
        for key in order:
            units.extend(page_units[key])
        return [("全文", units)]
    if order:
        return [(key, page_units[key]) for key in order]
    content = (doc.content or "").strip()
    if not content:
        return []
    paras = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paras:
        paras = [content]
    if len(paras) == 1:
        return [("全文", paras)]
    return [(f"段{i}", [p]) for i, p in enumerate(paras, start=1)]


def section_units(doc: Document) -> list[tuple[str, list[str]]]:
    headed = _heading_sections(doc.elements)
    if headed:
        return headed
    return _page_or_plain_sections(doc)


def chunk_document(doc: Document) -> list[KnowledgeChunk]:
    sections = section_units(doc)
    raw_chunks: list[tuple[str, str]] = []
    for section, units in sections:
        packed = pack_units(units)
        if len(packed) == 1:
            raw_chunks.append((section, packed[0]))
            continue
        if len(packed) > 1:
            for i, text in enumerate(packed, start=1):
                label = section if section else "全文"
                if len(packed) > 1 and section not in {"全文"} and not section.startswith("段"):
                    label = f"{section} ({i}/{len(packed)})"
                elif section == "全文" or not section:
                    label = f"段{i}" if len(packed) > 1 else "全文"
                raw_chunks.append((label, text))
    if not raw_chunks:
        body = (doc.content or "").strip()
        if body:
            raw_chunks.append(("全文", body))
    chunks: list[KnowledgeChunk] = []
    for i, (section, content) in enumerate(raw_chunks, start=1):
        if not content.strip():
            continue
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{doc.doc_id}-{i:03d}",
                doc_id=doc.doc_id,
                title=doc.title,
                category=doc.category,
                service=doc.service,
                department=doc.department,
                severity=doc.severity,
                source_type=doc.source_type,
                section=section or "全文",
                content=content.strip(),
                source_path=doc.source_path,
                visibility=doc.visibility,
                created_at=doc.created_at,
            )
        )
    return chunks
