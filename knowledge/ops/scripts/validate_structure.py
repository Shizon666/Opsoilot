#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K0 static structure checks for knowledge/ops (read-only).

Does NOT: load/chunk/index, touch Milvus, rewrite raw bodies, or call embeddings.

Usage (repo root or any cwd):
  python knowledge/ops/scripts/validate_structure.py
  python knowledge/ops/scripts/validate_structure.py --strict-basis
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_CATALOG_FIELDS = (
    "doc_id",
    "title",
    "category",
    "source_type",
    "source_path",
    "service",
    "department",
    "severity",
    "visibility",
    "status",
    "version",
    "created_at",
    "canonical",
    "v1_ingest",
)

ALLOWED_CATEGORIES = frozenset(
    {
        "RUNBOOK",
        "SERVICE_MANUAL",
        "INCIDENT_REPORT",
        "OPERATION_PROCESS",
        "SECURITY_GUIDELINE",
    }
)
ALLOWED_SOURCE_TYPES = frozenset({"markdown", "pdf", "docx", "txt"})
ALLOWED_SERVICES = frozenset(
    {"CHECKOUT_API", "AUTH_SERVICE", "ORDER_WORKER", "PLATFORM", "MULTI"}
)
ALLOWED_SEVERITY = frozenset({"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"})
ALLOWED_VISIBILITY = frozenset({"PUBLIC", "INTERNAL"})
ALLOWED_STATUS = frozenset({"draft", "active", "archived"})
ALLOWED_BASIS = frozenset({"code", "contract", "simulated"})

FORBIDDEN_PATH_SNIPPETS = (
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

# Documented superseded IDs (STANDARDS.md §7.2) — not valid related_docs targets.
DEPRECATED_DOC_IDS = frozenset(
    {
        "OPS-RB-AUTH-FAILURES",
        "OPS-RB-TICKET-ANALYSIS",
    }
)

# Simulated narrative ticket ids (not catalog documents).
NARRATIVE_ID_PREFIX = "OPS-IR-NARR-"

DOC_ID_PATTERN = re.compile(r"\bOPS-[A-Z]+-[A-Z0-9-]+\b")

# Heuristic: claiming real observability / agent execution (review false positives).
SUSPICIOUS_PHRASES = (
    "已对接生产 Prometheus",
    "已查询 ELK",
    "已查询 Prometheus",
    "Agent 已执行扩容",
    "Agent 已执行回滚",
    "Agent 已执行切备",
    "跳过 HITL",
)

# Ticket priority misuse (knowledge severity CRITICAL is OK in front matter).
PRIORITY_CRITICAL_MISUSE = re.compile(
    r"(?:priority|优先级)\s*[:=：]?\s*`?critical`?",
    re.IGNORECASE,
)


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def repo_root_from_script() -> Path:
    # knowledge/ops/scripts/this.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def split_front_matter(text: str) -> tuple[dict[str, Any] | None, str]:
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        return None, text
    return meta, parts[2]


def normalize_basis(raw: Any) -> list[str] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return None


def check_entry_enums(entry: dict[str, Any], findings: Findings, where: str) -> None:
    cat = entry.get("category")
    if cat not in ALLOWED_CATEGORIES:
        findings.err(f"{where}: invalid category={cat!r}")
    st = entry.get("source_type")
    if st not in ALLOWED_SOURCE_TYPES:
        findings.err(f"{where}: invalid source_type={st!r}")
    svc = entry.get("service")
    if svc not in ALLOWED_SERVICES:
        findings.err(f"{where}: invalid service={svc!r}")
    sev = entry.get("severity")
    if sev not in ALLOWED_SEVERITY:
        findings.err(f"{where}: invalid severity={sev!r}")
    vis = entry.get("visibility")
    if vis not in ALLOWED_VISIBILITY:
        findings.err(f"{where}: invalid visibility={vis!r}")
    status = entry.get("status")
    if status not in ALLOWED_STATUS:
        findings.err(f"{where}: invalid status={status!r}")


def compare_meta(
    catalog_entry: dict[str, Any],
    file_meta: dict[str, Any],
    findings: Findings,
    doc_id: str,
) -> None:
    for key in (
        "doc_id",
        "title",
        "category",
        "source_type",
        "service",
        "department",
        "severity",
        "visibility",
        "status",
        "version",
        "created_at",
    ):
        cval = catalog_entry.get(key)
        fval = file_meta.get(key)
        if fval is None:
            findings.warn(f"{doc_id}: file meta missing {key}")
            continue
        if cval != fval:
            findings.err(f"{doc_id}: catalog.{key}={cval!r} != file.{key}={fval!r}")


def scan_body(
    doc_id: str,
    body: str,
    known_ids: set[str],
    findings: Findings,
    *,
    strict_body: bool,
) -> None:
    for phrase in SUSPICIOUS_PHRASES:
        if phrase in body:
            findings.warn(f"{doc_id}: suspicious phrase {phrase!r} (manual review)")
    if PRIORITY_CRITICAL_MISUSE.search(body):
        msg = (
            f"{doc_id}: body appears to use ticket priority=critical "
            "(API allows only low/medium/high/urgent); fix in K1 rewrite"
        )
        if strict_body:
            findings.err(msg)
        else:
            findings.warn(msg)
    for match in DOC_ID_PATTERN.findall(body):
        if match == doc_id:
            continue
        if match.startswith(NARRATIVE_ID_PREFIX):
            continue
        if match in DEPRECATED_DOC_IDS:
            msg = (
                f"{doc_id}: body references deprecated {match} "
                "(allowed only as supersession note; clean up in K1)"
            )
            if strict_body:
                findings.err(msg)
            else:
                findings.warn(msg)
            continue
        if match not in known_ids:
            findings.warn(
                f"{doc_id}: body references unknown doc_id {match} "
                "(add to catalog or deprecated list)"
            )


def validate(ops_root: Path, *, strict_basis: bool, strict_body: bool) -> Findings:
    findings = Findings()
    catalog_path = ops_root / "catalog.yaml"
    if not catalog_path.is_file():
        findings.err(f"missing catalog: {catalog_path}")
        return findings

    catalog = load_yaml(catalog_path)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("documents"), list):
        findings.err("catalog.yaml must be a mapping with documents: list")
        return findings

    documents: list[dict[str, Any]] = [
        d for d in catalog["documents"] if isinstance(d, dict)
    ]
    ids = [str(d.get("doc_id") or "") for d in documents]
    known_ids = {i for i in ids if i}
    seen: set[str] = set()

    for entry in documents:
        doc_id = str(entry.get("doc_id") or "").strip()
        where = doc_id or "<missing doc_id>"
        if not doc_id:
            findings.err("catalog entry missing doc_id")
            continue
        if doc_id in seen:
            findings.err(f"duplicate doc_id in catalog: {doc_id}")
        seen.add(doc_id)
        if doc_id in DEPRECATED_DOC_IDS:
            findings.err(f"{doc_id}: deprecated id must not appear in catalog")

        for field in REQUIRED_CATALOG_FIELDS:
            if field not in entry:
                findings.err(f"{doc_id}: catalog missing field {field}")

        check_entry_enums(entry, findings, doc_id)

        source_path = entry.get("source_path")
        if not isinstance(source_path, str) or not source_path.startswith("raw/"):
            findings.err(f"{doc_id}: source_path must start with raw/")
            continue

        posix = source_path.replace("\\", "/")
        for snippet in FORBIDDEN_PATH_SNIPPETS:
            if snippet.rstrip("/") in posix:
                findings.err(f"{doc_id}: source_path hits forbidden prefix {snippet}")

        if entry.get("v1_ingest") is True and entry.get("status") != "active":
            findings.err(f"{doc_id}: v1_ingest true requires status=active")
        if entry.get("v1_ingest") is True and entry.get("canonical") is not True:
            findings.err(f"{doc_id}: v1_ingest true requires canonical=true")

        source_file = (ops_root / source_path).resolve()
        raw_root = (ops_root / "raw").resolve()
        try:
            source_file.relative_to(raw_root)
        except ValueError:
            findings.err(f"{doc_id}: source escapes raw/: {source_path}")
            continue
        if not source_file.is_file():
            findings.err(f"{doc_id}: missing source file {source_path}")
            continue

        file_meta: dict[str, Any] | None = None
        body = ""
        source_type = entry.get("source_type")
        if source_type == "markdown":
            text = source_file.read_text(encoding="utf-8")
            file_meta, body = split_front_matter(text)
            if file_meta is None:
                findings.err(f"{doc_id}: markdown missing YAML front matter")
            else:
                compare_meta(entry, file_meta, findings, doc_id)
        else:
            side = source_file.parent / f"{source_file.stem}.meta.yaml"
            if not side.is_file():
                findings.err(f"{doc_id}: missing sidecar {side.name}")
            else:
                raw_meta = load_yaml(side)
                if not isinstance(raw_meta, dict):
                    findings.err(f"{doc_id}: sidecar is not a mapping")
                else:
                    file_meta = raw_meta
                    compare_meta(entry, file_meta, findings, doc_id)
            # non-md: light scan sidecar text only
            body = side.read_text(encoding="utf-8") if side.is_file() else ""

        meta_for_basis = file_meta or {}
        basis_list = normalize_basis(meta_for_basis.get("basis"))
        if basis_list is None:
            msg = f"{doc_id}: missing basis (required from K1; K0 warning)"
            if strict_basis:
                findings.err(msg)
            else:
                findings.warn(msg)
        else:
            for b in basis_list:
                if b not in ALLOWED_BASIS:
                    findings.err(f"{doc_id}: invalid basis value {b!r}")

        related = meta_for_basis.get("related_docs")
        if related is None:
            findings.warn(f"{doc_id}: missing related_docs (recommended from K1)")
        elif not isinstance(related, list):
            findings.err(f"{doc_id}: related_docs must be a list")
        else:
            for rid in related:
                rid_s = str(rid)
                if rid_s in DEPRECATED_DOC_IDS:
                    findings.err(f"{doc_id}: related_docs contains deprecated {rid_s}")
                elif rid_s not in known_ids:
                    findings.err(f"{doc_id}: related_docs unknown {rid_s}")

        if body:
            scan_body(
                doc_id, body, known_ids, findings, strict_body=strict_body
            )

        if entry.get("category") == "INCIDENT_REPORT":
            text_all = body
            if "模拟" not in text_all and "虚构" not in text_all:
                findings.warn(
                    f"{doc_id}: incident report body/sidecar may lack simulation notice"
                )

    # Phase 10 exclusion: ensure no catalog path points outside ops/raw
    for entry in documents:
        sp = entry.get("source_path")
        if isinstance(sp, str) and not sp.startswith("raw/"):
            findings.err(f"{entry.get('doc_id')}: refuses non-raw path (Phase10 guard)")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate knowledge/ops structure (K0)")
    parser.add_argument(
        "--ops-root",
        type=Path,
        default=None,
        help="Path to knowledge/ops (default: <repo>/knowledge/ops)",
    )
    parser.add_argument(
        "--strict-basis",
        action="store_true",
        help="Treat missing basis as error (enable from K1)",
    )
    parser.add_argument(
        "--strict-body",
        action="store_true",
        help="Treat priority=critical / deprecated body refs as errors (enable from K1)",
    )
    args = parser.parse_args()
    ops_root = (args.ops_root or (repo_root_from_script() / "knowledge" / "ops")).resolve()

    findings = validate(
        ops_root, strict_basis=args.strict_basis, strict_body=args.strict_body
    )

    print(f"ops_root={ops_root}")
    print(f"errors={len(findings.errors)} warnings={len(findings.warnings)}")
    for msg in findings.errors:
        print(f"ERROR  {msg}")
    for msg in findings.warnings:
        print(f"WARN   {msg}")

    if findings.errors:
        print("RESULT FAIL")
        return 1
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
