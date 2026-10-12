"""Read-only knowledge/ops/catalog.yaml whitelist (no os.walk of knowledge/)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

ALLOWED_SOURCE_TYPES = frozenset({"markdown", "pdf", "docx", "txt"})
FORBIDDEN_PREFIXES = (
    "knowledge/制度规范/",
    "knowledge/权限管理/",
    "knowledge/服务目录/",
    "knowledge/VPN与远程办公/",
    "knowledge/账号登录/",
    "knowledge/数据安全/",
    "knowledge/常见问题/",
    "knowledge/作业手册/",
    "knowledge/软件安装/",
    "knowledge/办公与直播设备/",
    "knowledge/元数据/",
    "agent/knowledge/runbooks/",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_ops_root() -> Path:
    return repo_root() / "knowledge" / "ops"


def default_catalog_path() -> Path:
    return default_ops_root() / "catalog.yaml"


def load_catalog(catalog_path: Path) -> dict[str, Any]:
    raw = catalog_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict) or not isinstance(data.get("documents"), list):
        raise ValueError(f"invalid catalog: {catalog_path}")
    return data


def resolve_source_file(ops_root: Path, source_path: str) -> Path | None:
    """Map catalog source_path (raw/...) onto disk; reject escape from knowledge/ops/raw."""
    if not isinstance(source_path, str) or not source_path.startswith("raw/"):
        return None
    raw_root = (ops_root / "raw").resolve()
    candidate = (ops_root / source_path).resolve()
    try:
        candidate.relative_to(raw_root)
    except ValueError:
        return None
    posix = candidate.as_posix().replace("\\", "/")
    for prefix in FORBIDDEN_PREFIXES:
        needle = prefix.rstrip("/")
        if needle in posix:
            return None
    return candidate


def is_eligible(entry: dict[str, Any]) -> tuple[bool, str]:
    if entry.get("v1_ingest") is not True:
        return False, "v1_ingest!=true"
    if entry.get("status") != "active":
        return False, "status!=active"
    if entry.get("canonical") is not True:
        return False, "canonical!=true"
    source_type = entry.get("source_type")
    if source_type == "html":
        return False, "html_reserved"
    if source_type not in ALLOWED_SOURCE_TYPES:
        return False, f"unsupported_source_type:{source_type}"
    source_path = entry.get("source_path")
    if not isinstance(source_path, str) or not source_path.startswith("raw/"):
        return False, "source_path_not_under_raw"
    return True, ""


def eligible_entries(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in catalog.get("documents") or []:
        if not isinstance(entry, dict):
            continue
        ok, reason = is_eligible(entry)
        if not ok:
            logger.info("catalog skip %s: %s", entry.get("doc_id"), reason)
            continue
        out.append(entry)
    return out
