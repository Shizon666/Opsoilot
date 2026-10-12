"""Minimal evaluation runner for Legacy cases.yaml (Phase 11) and V1 P0.

V1 金标（Hardening H3）：
  python -m app.evaluation.runner --v1
  → agent/app/evaluation/v1/cases_c42.yaml

Legacy（VPN / GitLab / Permission，不能当 V1 PASS）：
  python -m app.evaluation.runner
  → agent/app/evaluation/cases.yaml

Requires:
  - LLM_API_KEY (or OPENAI_API_KEY)
  - Backend reachable for get_*/create_* cases (GO_BACKEND_URL / BACKEND_BASE_URL)
  - Demo login (EVAL_USERNAME / EVAL_PASSWORD) or EVAL_JWT

C-4.3 extra assertions (ignored when fields absent — Legacy cases.yaml unchanged):
  required_tools / forbidden_tools / expect_interrupt / text_must / text_must_not
  optional: turns[], resume, isolation=thread_owner
  required_tools item may be a list (any-of), e.g. [list_services, get_service_status]

Outputs one PASS/FAIL line per case, then a summary.
Exit code 0 only when all executed cases PASS (SKIP does not fail the run).
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml

from jwt import InvalidTokenError

from app.auth.jwt import JWTError, TokenClaims
from app.graph.agent import (
    WRITE_TOOLS,
    AgentError,
    AgentResult,
    reset_graph_for_tests,
    resume_agent,
    run_agent,
)
from app.request_context import user_context
from app.thread_store import ThreadOwnershipError, thread_ownership

V1_CASES_PATH = Path(__file__).with_name("v1") / "cases_c42.yaml"

CASES_PATH = Path(__file__).with_name("cases.yaml")


@dataclass
class CaseResult:
    case_id: str
    status: str  # PASS | FAIL | SKIP | ERROR
    tools_called: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    reply_preview: str = ""


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"cases.yaml must be a list, got {type(raw)}")
    return raw


def _load_dotenv() -> None:
    """Load repo /.env into os.environ without python-dotenv (setdefault only)."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",  # repo root
        Path(__file__).resolve().parents[2] / ".env",  # agent/
    ]
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, _, val = s.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
        break


def _backend_base() -> str:
    return (
        os.getenv("GO_BACKEND_URL")
        or os.getenv("BACKEND_BASE_URL")
        or os.getenv("BACKEND_URL")
        or "http://localhost:8080"
    ).rstrip("/")


def _obtain_jwt() -> tuple[str, str, str]:
    """Return (raw_jwt, user_id, role). Prefer EVAL_JWT; else demo login; else mint."""
    explicit = (os.getenv("EVAL_JWT") or "").strip()
    if explicit:
        claims = _claims_from_eval_token(explicit)
        return claims.raw_token, claims.user_id, claims.role

    if (os.getenv("EVAL_MINT_JWT") or "").strip() in ("1", "true", "yes"):
        return _mint_local_jwt()

    username = os.getenv("EVAL_USERNAME", "demo@opspilot.local")
    password = os.getenv("EVAL_PASSWORD", "password123")
    url = f"{_backend_base()}/api/v1/auth/login"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json={"username": username, "password": password})
            resp.raise_for_status()
            body = resp.json()
    except Exception as exc:
        # Fallback for knowledge-only local smoke when backend is down.
        print(f"WARN: backend login failed ({exc}); minting local JWT", file=sys.stderr)
        return _mint_local_jwt()

    if body.get("code", 0) != 0:
        raise RuntimeError(f"login failed: {body}")
    data = body.get("data") or {}
    jwt_token = data.get("token") or ""
    if not jwt_token:
        raise RuntimeError(f"login response missing token: {body}")
    claims = _claims_from_eval_token(jwt_token)
    return claims.raw_token, claims.user_id, claims.role


def _claims_from_eval_token(token: str) -> TokenClaims:
    """Verify eval JWT with clock leeway (host vs Docker iat skew)."""
    raw = token.strip()
    if raw.lower().startswith("bearer "):
        raw = raw.split(None, 1)[1].strip()
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        raise JWTError("JWT_SECRET is not configured")
    try:
        import jwt as pyjwt

        payload = pyjwt.decode(
            raw,
            secret,
            algorithms=["HS256"],
            leeway=120,
            options={"require": ["exp", "sub"]},
        )
    except InvalidTokenError as exc:
        raise JWTError(f"invalid token: {exc}") from exc
    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise JWTError("token missing sub")
    role = payload.get("role") or ""
    if not isinstance(role, str):
        role = str(role)
    return TokenClaims(user_id=user_id, role=role, raw_token=raw)


def _mint_local_jwt() -> tuple[str, str, str]:
    """HS256 token with JWT_SECRET — valid for Agent context, not for Go API."""
    import time

    import jwt as pyjwt

    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET required to mint eval JWT")
    user_id = os.getenv("EVAL_USER_ID", "00000000-0000-4000-8000-000000000001")
    role = os.getenv("EVAL_ROLE", "EMPLOYEE")
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    raw = pyjwt.encode(payload, secret, algorithm="HS256")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return raw, user_id, role


def _tool_required_met(req: Any, called: set[str]) -> bool:
    """A required item is a name, or a list of names (any-of)."""
    if isinstance(req, (list, tuple)):
        names = [str(x).strip() for x in req if str(x).strip()]
        return any(n in called for n in names)
    name = str(req).strip()
    return bool(name) and name in called


def _check_tools(case: dict[str, Any], tools_called: list[str]) -> list[str]:
    called = set(tools_called)
    reasons: list[str] = []
    required = list(case.get("required_tools") or [])
    forbidden = list(case.get("forbidden_tools") or [])

    # Fallback when machine fields absent: treat expected_tools as required
    # except create_* which stay optional.
    if "required_tools" not in case and "forbidden_tools" not in case:
        expected = list(case.get("expected_tools") or [])
        required = [t for t in expected if not t.startswith("create_")]
        # soft parse forbidden from expected_behavior
        for line in case.get("expected_behavior") or []:
            if "不调用" in line or "禁" in line:
                for name in (
                    "create_ticket",
                    "create_permission",
                    "get_my_tickets",
                    "get_my_permissions",
                    "search_knowledge",
                ):
                    if name in line:
                        # "不以 search_knowledge" is different — skip that pattern
                        if "不以" in line and name == "search_knowledge":
                            continue
                        if "不调用" in line or (name.startswith("create_") and "禁" in line):
                            forbidden.append(name)

    missing = [t for t in required if not _tool_required_met(t, called)]
    if missing:
        reasons.append(f"missing required tools: {missing}")
    hit_forbidden = [t for t in forbidden if t in called]
    if hit_forbidden:
        reasons.append(f"called forbidden tools: {hit_forbidden}")
    return reasons


def _check_interrupt(expect: Any, pending: bool) -> list[str]:
    if expect is None:
        return []
    wanted = bool(expect)
    if wanted != bool(pending):
        return [f"expect_interrupt={wanted} but pending={bool(pending)}"]
    return []


def _check_text(needles: Any, message: str, *, must: bool) -> list[str]:
    text = message or ""
    reasons: list[str] = []
    for raw in needles or []:
        needle = str(raw)
        if not needle:
            continue
        if must and needle not in text:
            reasons.append(f"missing text: {needle}")
        if not must and needle in text:
            reasons.append(f"forbidden text: {needle}")
    return reasons


def _check_silent_write(tools_called: list[str], *, pending: bool, resumed: bool) -> list[str]:
    """Fail Closed: write tools in a non-resume turn must have HITL pending."""
    if resumed or pending:
        return []
    writes = [t for t in tools_called if t in WRITE_TOOLS]
    if writes:
        return [f"silent write without interrupt: {writes}"]
    return []


def _iter_turns(case: dict[str, Any]) -> list[dict[str, Any]]:
    turns = case.get("turns")
    if isinstance(turns, list) and turns:
        return [t for t in turns if isinstance(t, dict)]
    return [case]


def _turn_question(turn: dict[str, Any]) -> str:
    return str(turn.get("question") or turn.get("text") or "").strip()


def _assert_result(
    spec: dict[str, Any],
    result: AgentResult,
    *,
    resumed: bool,
) -> list[str]:
    reasons = _check_tools(spec, result.tools_called)
    reasons.extend(_check_interrupt(spec.get("expect_interrupt"), result.pending))
    reasons.extend(_check_silent_write(result.tools_called, pending=result.pending, resumed=resumed))
    reasons.extend(_check_text(spec.get("text_must"), result.message, must=True))
    reasons.extend(_check_text(spec.get("text_must_not"), result.message, must=False))
    return reasons


def evaluate_case(
    case: dict[str, Any],
    *,
    user_jwt: str,
    user_id: str,
    role: str,
) -> CaseResult:
    case_id = str(case.get("id") or "unknown")
    turns = _iter_turns(case)
    if not turns or not any(_turn_question(t) for t in turns):
        return CaseResult(case_id=case_id, status="SKIP", reasons=["empty question"])

    thread_id = f"eval_{case_id}_{uuid.uuid4().hex[:8]}"
    thread_ownership.bind_or_check(thread_id, user_id)

    tools_all: list[str] = []
    reasons: list[str] = []
    preview = ""

    try:
        with user_context(
            user_jwt=user_jwt,
            user_id=user_id,
            role=role,
            request_id=f"eval_{uuid.uuid4().hex[:10]}",
        ):
            for idx, turn in enumerate(turns):
                question = _turn_question(turn)
                if not question:
                    reasons.append(f"turn[{idx}] empty question")
                    break
                result: AgentResult = run_agent(question, thread_id=thread_id)
                tools_all.extend(result.tools_called)

                resume_action = str(turn.get("resume") or "").strip().lower()
                if resume_action:
                    reasons.extend(_check_tools(turn, result.tools_called))
                    reasons.extend(
                        _check_interrupt(turn.get("expect_interrupt", True), result.pending)
                    )
                    reasons.extend(
                        _check_silent_write(
                            result.tools_called, pending=result.pending, resumed=False
                        )
                    )
                    if not result.pending:
                        reasons.append("resume requested but no interrupt")
                    else:
                        result = resume_agent(thread_id=thread_id, action=resume_action)
                        tools_all.extend(result.tools_called)
                        reasons.extend(
                            _check_text(turn.get("text_must"), result.message, must=True)
                        )
                        reasons.extend(
                            _check_text(turn.get("text_must_not"), result.message, must=False)
                        )
                else:
                    reasons.extend(_assert_result(turn, result, resumed=False))

                preview = (result.message or "")[:120].replace("\n", " ")
                if reasons:
                    break

            if not reasons and str(case.get("isolation") or "") == "thread_owner":
                other = str(case.get("other_user_id") or "").strip()
                if not other:
                    reasons.append("isolation=thread_owner missing other_user_id")
                else:
                    try:
                        thread_ownership.bind_or_check(thread_id, other)
                        reasons.append("thread_owner: other user was allowed to bind thread")
                    except ThreadOwnershipError:
                        pass
    except AgentError as exc:
        return CaseResult(
            case_id=case_id,
            status="ERROR",
            tools_called=tools_all,
            reasons=[f"AgentError {exc.code}: {exc.message}"],
        )
    except Exception as exc:  # noqa: BLE001
        return CaseResult(
            case_id=case_id,
            status="ERROR",
            tools_called=tools_all,
            reasons=[f"{type(exc).__name__}: {exc}"],
        )

    if reasons:
        return CaseResult(
            case_id=case_id,
            status="FAIL",
            tools_called=tools_all,
            reasons=reasons,
            reply_preview=preview,
        )
    return CaseResult(
        case_id=case_id,
        status="PASS",
        tools_called=tools_all,
        reply_preview=preview,
    )


def run_all(
    *,
    case_ids: list[str] | None = None,
    cases_path: Path = CASES_PATH,
) -> list[CaseResult]:
    cases = load_cases(cases_path)
    if case_ids:
        wanted = set(case_ids)
        cases = [c for c in cases if c.get("id") in wanted]

    try:
        user_jwt, user_id, role = _obtain_jwt()
    except JWTError as exc:
        print(f"ERROR: JWT setup failed: {exc}", file=sys.stderr)
        return [
            CaseResult(case_id="*", status="ERROR", reasons=[f"JWT: {exc}"]),
        ]
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot obtain eval JWT ({exc})", file=sys.stderr)
        print(
            "Hint: start Go backend, or set EVAL_JWT / EVAL_USERNAME+EVAL_PASSWORD",
            file=sys.stderr,
        )
        return [
            CaseResult(case_id="*", status="ERROR", reasons=[str(exc)]),
        ]

    if not (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip():
        print("ERROR: LLM_API_KEY / OPENAI_API_KEY not set", file=sys.stderr)
        return [
            CaseResult(case_id="*", status="ERROR", reasons=["LLM_API_KEY missing"]),
        ]

    # Fresh graph/checkpointer so eval threads do not collide with server state
    # when runner is imported into a long-lived process.
    reset_graph_for_tests()
    thread_ownership.clear()

    results: list[CaseResult] = []
    for case in cases:
        cr = evaluate_case(case, user_jwt=user_jwt, user_id=user_id, role=role)
        results.append(cr)
        tools = ",".join(cr.tools_called) if cr.tools_called else "-"
        detail = f" | {'; '.join(cr.reasons)}" if cr.reasons else ""
        print(f"[{cr.status}] {cr.case_id} tools=[{tools}]{detail}")
    return results


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    # Compose uses BUSINESS_API_BASE_URL=http://backend:8080 inside the agent container.
    # Local runner should hit localhost unless explicitly overridden.
    if (os.getenv("BUSINESS_API_BASE_URL") or "").startswith("http://backend"):
        os.environ["BUSINESS_API_BASE_URL"] = "http://localhost:8080"
        os.environ.setdefault("GO_BACKEND_URL", "http://localhost:8080")

    parser = argparse.ArgumentParser(
        description="OpsPilot eval runner. V1 gold: --v1 (cases_c42.yaml). Default: Legacy cases.yaml."
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help="Run only this case id (repeatable)",
    )
    parser.add_argument(
        "--cases-file",
        type=Path,
        default=CASES_PATH,
        help="Path to cases yaml (default: Legacy cases.yaml)",
    )
    parser.add_argument(
        "--v1",
        action="store_true",
        help="Use V1 gold file app/evaluation/v1/cases_c42.yaml",
    )
    parser.add_argument(
        "--mint-jwt",
        action="store_true",
        help="Mint HS256 JWT with JWT_SECRET (no backend login; query/create tools will fail)",
    )
    args = parser.parse_args(argv)

    if args.mint_jwt:
        os.environ["EVAL_MINT_JWT"] = "1"
    if args.v1:
        args.cases_file = V1_CASES_PATH

    results = run_all(case_ids=args.cases, cases_path=args.cases_file)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    errors = sum(1 for r in results if r.status == "ERROR")
    skipped = sum(1 for r in results if r.status == "SKIP")
    total = len(results)
    print("-" * 60)
    print(
        f"SUMMARY total={total} PASS={passed} FAIL={failed} "
        f"ERROR={errors} SKIP={skipped}"
    )
    if failed or errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
