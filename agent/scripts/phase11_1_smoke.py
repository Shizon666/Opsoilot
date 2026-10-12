"""Phase 11.1 smoke: PostgresSaver persists across checkpointer re-init.

Requires: Postgres on CHECKPOINT_DATABASE_URL (default localhost:5432/opspilot_agent).
Optional LLM turn if LLM_API_KEY set.
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
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    _load_dotenv()
    os.environ.setdefault("CHECKPOINT_BACKEND", "postgres")
    # Local smoke: prefer localhost even if .env points at compose hostname.
    url = os.environ.get("CHECKPOINT_DATABASE_URL") or ""
    if "://opspilot:opspilot@postgres:" in url:
        os.environ["CHECKPOINT_DATABASE_URL"] = url.replace("@postgres:", "@localhost:")
    os.environ.setdefault(
        "CHECKPOINT_DATABASE_URL",
        "postgres://opspilot:opspilot@localhost:5432/opspilot_agent?sslmode=disable",
    )
    os.environ["KNOWLEDGE_DIR"] = str(ROOT / "knowledge")

    from app.db import checkpoint_backend, close_pool, ensure_agent_database, get_pool
    from app.graph.agent import _get_graph, reset_graph_for_tests, run_agent
    from app.memory import checkpointer_backend_in_use, get_checkpointer
    from app.request_context import user_context
    from app.thread_store import ThreadOwnershipError, thread_ownership

    assert checkpoint_backend() == "postgres", checkpoint_backend()

    try:
        ensure_agent_database()
        get_pool()
    except Exception as exc:  # noqa: BLE001
        print(f"SKIP_NO_POSTGRES: {exc}")
        return 2

    reset_graph_for_tests()
    cp = get_checkpointer()
    print(f"CHECKPOINTER {type(cp).__name__} backend={checkpointer_backend_in_use()}")

    tid = f"pg_smoke_{uuid.uuid4().hex[:10]}"
    uid_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    uid_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    # ownership bind + cross-user reject
    thread_ownership.bind_or_check(tid, uid_a)
    try:
        thread_ownership.bind_or_check(tid, uid_b)
        print("OWNERSHIP_CROSS_USER FAIL (expected reject)")
        return 1
    except ThreadOwnershipError:
        print("OWNERSHIP_CROSS_USER PASS")

    # simulate process restart: new pool + checkpointer, same thread ownership row
    reset_graph_for_tests()
    get_checkpointer()
    try:
        thread_ownership.bind_or_check(tid, uid_b)
        print("OWNERSHIP_AFTER_REINIT FAIL")
        return 1
    except ThreadOwnershipError:
        print("OWNERSHIP_PERSIST PASS")
    thread_ownership.bind_or_check(tid, uid_a)
    print("OWNERSHIP_SAME_USER PASS")

    has_llm = bool((os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip())
    if not has_llm:
        print("SKIP_LLM: no LLM_API_KEY — checkpoint message persistence not exercised")
        close_pool()
        return 0

    import jwt

    secret = os.environ.get("JWT_SECRET") or "change-me-in-local-dev"
    raw = jwt.encode(
        {"sub": uid_a, "role": "EMPLOYEE", "exp": int(time.time()) + 3600},
        secret,
        algorithm="HS256",
    )
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    with user_context(user_jwt=raw, user_id=uid_a, role="EMPLOYEE", request_id="req_pg1"):
        r1 = run_agent("权限和工单有啥区别？请简短回答。", thread_id=tid)
    print(f"TURN1 tools={r1.tools_called}")

    # simulate agent process restart
    reset_graph_for_tests()
    get_checkpointer()
    graph = _get_graph()
    st = graph.get_state({"configurable": {"thread_id": tid}})
    n = len((st.values or {}).get("messages") or [])
    print(f"AFTER_REINIT_MSGS {n}")
    if n < 2:
        print("CHECKPOINT_PERSIST FAIL")
        return 1
    print("CHECKPOINT_PERSIST PASS")

    with user_context(user_jwt=raw, user_id=uid_a, role="EMPLOYEE", request_id="req_pg2"):
        r2 = run_agent("刚才我说的是哪个问题？一句话复述。", thread_id=tid)
    text = r2.message or ""
    recall = any(k in text for k in ("权限", "工单", "区别"))
    print(f"TURN2 reply={text[:160].replace(chr(10), ' ')}")
    print(f"MEMORY_RECALL {'PASS' if recall else 'FAIL'}")
    close_pool()
    return 0 if recall else 1


if __name__ == "__main__":
    raise SystemExit(main())
