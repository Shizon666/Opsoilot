"""Phase 11.1 smoke: Postgres Checkpointer survives process-local reset.

Simulates Agent restart by clearing graph/checkpointer/pool singletons,
then reloading the same thread_id from opspilot_agent.

Usage (repo root or agent/):
  set CHECKPOINT_BACKEND=postgres
  set CHECKPOINT_DATABASE_URL=postgres://opspilot:opspilot@localhost:5432/opspilot_agent?sslmode=disable
  python agent/scripts/phase11_1_restart_smoke.py
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

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
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    _load_dotenv()
    os.environ["CHECKPOINT_BACKEND"] = "postgres"
    # Local host (Compose service name "postgres" won't resolve outside network)
    url = os.environ.get("CHECKPOINT_DATABASE_URL") or ""
    if "://opspilot:opspilot@postgres:" in url or not url or "127.0.0.1" in url:
        # Prefer localhost (often ::1 → Docker publish). 127.0.0.1 may hit a local PG.
        os.environ["CHECKPOINT_DATABASE_URL"] = (
            "postgres://opspilot:opspilot@localhost:5432/opspilot_agent?sslmode=disable"
        )
    os.environ["KNOWLEDGE_DIR"] = str(ROOT / "knowledge")
    os.environ.setdefault("BUSINESS_API_BASE_URL", "http://127.0.0.1:8080")

    if not (os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("FAIL: LLM_API_KEY missing")
        return 1

    from app.db import checkpoint_backend, ensure_agent_database, get_pool
    from app.graph.agent import _get_graph, reset_graph_for_tests, run_agent
    from app.memory import checkpointer_backend_in_use, get_checkpointer
    from app.request_context import user_context
    from app.thread_store import ThreadOwnershipError, thread_ownership

    print(f"BACKEND_ENV={checkpoint_backend()}")
    ensure_agent_database()
    reset_graph_for_tests()
    cp = get_checkpointer()
    print(f"CHECKPOINTER={type(cp).__name__} in_use={checkpointer_backend_in_use()}")

    import jwt

    secret = os.environ.get("JWT_SECRET") or "change-me-in-local-dev"
    uid = "22222222-2222-4222-8222-222222222222"
    other = "33333333-3333-4333-8333-333333333333"
    raw = jwt.encode(
        {"sub": uid, "role": "EMPLOYEE", "exp": int(time.time()) + 3600},
        secret,
        algorithm="HS256",
    )
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    tid = f"restart_smoke_{uuid.uuid4().hex[:10]}"
    thread_ownership.bind_or_check(tid, uid)

    with user_context(user_jwt=raw, user_id=uid, role="EMPLOYEE", request_id="r1"):
        r1 = run_agent("权限和工单有啥区别？请用一句话回答。", thread_id=tid)
    print(f"TURN1 tools={r1.tools_called}")
    print(f"TURN1 reply={(r1.message or '')[:120].replace(chr(10), ' ')}")

    graph = _get_graph()
    n1 = len(
        (graph.get_state({"configurable": {"thread_id": tid}}).values or {}).get(
            "messages"
        )
        or []
    )
    print(f"STATE_BEFORE_RESET msgs={n1}")

    # --- simulate process restart: drop in-process singletons, keep Postgres ---
    reset_graph_for_tests()
    cp2 = get_checkpointer()
    print(f"AFTER_RESET checkpointer={type(cp2).__name__}")

    # ownership must still bind same user
    thread_ownership.bind_or_check(tid, uid)
    try:
        thread_ownership.bind_or_check(tid, other)
        print("OWNERSHIP_CROSS_USER FAIL (expected 403-equivalent)")
        return 1
    except ThreadOwnershipError:
        print("OWNERSHIP_CROSS_USER PASS")

    with user_context(user_jwt=raw, user_id=uid, role="EMPLOYEE", request_id="r2"):
        r2 = run_agent("刚才我问的是什么？一句话复述。", thread_id=tid)
    print(f"TURN2 tools={r2.tools_called}")
    print(f"TURN2 reply={(r2.message or '')[:160].replace(chr(10), ' ')}")

    graph2 = _get_graph()
    n2 = len(
        (graph2.get_state({"configurable": {"thread_id": tid}}).values or {}).get(
            "messages"
        )
        or []
    )
    print(f"STATE_AFTER_RELOAD msgs={n2}")

    text = r2.message or ""
    recall = any(k in text for k in ("权限", "工单", "区别"))
    owners = get_pool().connection()
    with owners as conn:
        row = conn.execute(
            "SELECT user_id FROM agent_thread_owners WHERE thread_id = %s",
            (tid,),
        ).fetchone()
    print(f"OWNER_ROW={row}")

    ok = (
        checkpointer_backend_in_use() == "postgres"
        and n1 >= 2
        and n2 > n1
        and recall
        and row is not None
    )
    print(f"RESTART_RECOVERY {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
