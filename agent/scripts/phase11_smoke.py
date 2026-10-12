"""Phase 11 smoke: MemorySaver multi-turn + knowledge-only eval subset."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import jwt

ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = ROOT / "agent"
sys.path.insert(0, str(AGENT_ROOT))
os.chdir(AGENT_ROOT)


def _load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, _, val = s.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    _load_dotenv()
    os.environ["KNOWLEDGE_DIR"] = str(ROOT / "knowledge")
    os.environ["BUSINESS_API_BASE_URL"] = "http://localhost:8080"
    os.environ["EVAL_MINT_JWT"] = "1"

    from app.graph.agent import _get_graph, reset_graph_for_tests, run_agent
    from app.memory import get_checkpointer
    from app.request_context import user_context

    reset_graph_for_tests()
    cp = get_checkpointer()
    print(f"CHECKPOINTER_OK {type(cp).__name__}")

    secret = os.environ.get("JWT_SECRET") or ""
    if not secret:
        print("FAIL: JWT_SECRET missing")
        return 1
    if not (os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("FAIL: LLM_API_KEY missing")
        return 1

    uid = "11111111-1111-4111-8111-111111111111"
    raw = jwt.encode(
        {"sub": uid, "role": "EMPLOYEE", "exp": int(time.time()) + 3600},
        secret,
        algorithm="HS256",
    )
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    tid = "mem_smoke_001"
    with user_context(user_jwt=raw, user_id=uid, role="EMPLOYEE", request_id="req_mem1"):
        r1 = run_agent("权限和工单有啥区别？请简短回答。", thread_id=tid)
    print(f"TURN1 tools={r1.tools_called}")
    print(f"TURN1 reply={(r1.message or '')[:160].replace(chr(10), ' ')}")

    with user_context(user_jwt=raw, user_id=uid, role="EMPLOYEE", request_id="req_mem2"):
        r2 = run_agent("刚才我说的是哪个问题？用一句话复述。", thread_id=tid)
    print(f"TURN2 tools={r2.tools_called}")
    print(f"TURN2 reply={(r2.message or '')[:200].replace(chr(10), ' ')}")

    graph = _get_graph()
    st = graph.get_state({"configurable": {"thread_id": tid}})
    n = len((st.values or {}).get("messages") or [])
    print(f"STATE_MSGS {n}")
    text = r2.message or ""
    recall_ok = any(k in text for k in ("权限", "工单", "区别", "申请"))
    print(f"MEMORY_RECALL {'PASS' if recall_ok and n >= 3 else 'FAIL'} msgs={n}")

    # knowledge-only eval cases (no Go backend)
    from app.evaluation.runner import run_all

    reset_graph_for_tests()
    knowledge_cases = [
        "baseline_knowledge_ticket_vs_permission",
        "high_risk_admin_skip_approval",
        "missing_params_gitlab_permission",
        "knowledge_abstain_wifi_password",
        "rag_hit_vpn_howto",
        "rag_hit_or_weak_permission_sla",
        "rag_abstain_db_root_password",
    ]
    results = run_all(case_ids=knowledge_cases)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    errors = sum(1 for r in results if r.status == "ERROR")
    print(
        f"EVAL_KNOWLEDGE_SUBSET PASS={passed} FAIL={failed} ERROR={errors} "
        f"total={len(results)}"
    )
    if not recall_ok or n < 3:
        return 1
    if failed or errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
