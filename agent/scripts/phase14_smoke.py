"""Phase 14 smoke: WRITE HITL interrupt → resume Command, real Go + PostgreSQL.

Requires: backend :8080, agent :8000, PostgresSaver, LLM_API_KEY, demo + support users.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _counts() -> tuple[int, int, int, int]:
    q = (
        "SELECT "
        "(SELECT COUNT(*) FROM tickets) AS tickets, "
        "(SELECT COUNT(*) FROM audit_logs WHERE action='ticket.create') AS ticket_audits, "
        "(SELECT COUNT(*) FROM access_requests) AS perms, "
        "(SELECT COUNT(*) FROM audit_logs WHERE action='access_request.create') AS perm_audits;"
    )
    out = subprocess.check_output(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "opspilot",
            "-d",
            "opspilot",
            "-t",
            "-A",
            "-c",
            q,
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    t, ta, p, pa = out.split("|")
    return int(t), int(ta), int(p), int(pa)


def _human_messages(thread_id: str) -> list[str]:
    code = (
        "from langchain_core.messages import HumanMessage\n"
        "from app.graph.agent import _get_graph, _invoke_config\n"
        f"tid={thread_id!r}\n"
        "s=_get_graph().get_state(_invoke_config(tid))\n"
        "msgs=(s.values or {}).get('messages') or []\n"
        "print('\\n'.join(str(m.content) for m in msgs if isinstance(m, HumanMessage)))\n"
    )
    return (
        subprocess.check_output(
            ["docker", "compose", "exec", "-T", "agent", "python", "-c", code],
            cwd=ROOT,
            text=True,
        )
        .strip()
        .splitlines()
    )


def main() -> int:
    _load_dotenv()
    backend = os.environ.get("GO_BACKEND_URL") or "http://localhost:8080"
    agent = os.environ.get("AGENT_URL") or "http://localhost:8000"
    failed: list[str] = []

    with httpx.Client(timeout=120.0) as client:

        def login(user: str, pw: str) -> str:
            r = client.post(
                f"{backend}/api/v1/auth/login",
                json={"username": user, "password": pw},
            )
            r.raise_for_status()
            return (r.json().get("data") or {}).get("token") or ""

        tok = login("demo@opspilot.local", "password123")
        h = {"Authorization": f"Bearer {tok}"}

        health = client.get(f"{agent}/internal/health")
        print("HEALTH", health.text)
        if (health.json() or {}).get("checkpointer") != "postgres":
            print("FAIL expected postgres checkpointer")
            failed.append("HEALTH")

        # 1 READ
        tid_read = f"p14_read_{uuid.uuid4().hex[:8]}"
        r = client.post(
            f"{agent}/agent/chat",
            headers=h,
            json={"thread_id": tid_read, "message": "我的工单有哪些？"},
        )
        d = r.json().get("data") or {}
        tools = (d.get("metadata") or {}).get("tools_called") or []
        print("READ status", r.status_code, "pending", d.get("pending"), "tools", tools)
        print("READ reply", (d.get("message") or "")[:160].replace("\n", " "))
        if r.status_code != 200 or d.get("pending") or "get_my_tickets" not in tools:
            failed.append("READ")
            print("READ FAIL")
        else:
            print("READ PASS")

        # 2 CREATE pending
        t0, ta0, p0, pa0 = _counts()
        tid = f"p14_tkt_{uuid.uuid4().hex[:8]}"
        r = client.post(
            f"{agent}/agent/chat",
            headers=h,
            json={
                "thread_id": tid,
                "message": "帮我创建一个 VPN 故障工单，标题 VPN 故障，描述回家连不上公司 VPN，优先级 high。请直接创建。",
            },
        )
        d = r.json().get("data") or {}
        conf = d.get("confirmation") or {}
        print("PENDING status", r.status_code, "pending", d.get("pending"), "tool", conf.get("tool"))
        print("PENDING message", (d.get("message") or "")[:180].replace("\n", " "))
        print("PENDING conf", json.dumps(conf, ensure_ascii=False)[:400])
        created_claim = any(
            x in (d.get("message") or "") for x in ("已为你创建", "工单已创建", "已经创建")
        )
        t1, ta1, _, _ = _counts()
        print("DB after pending tickets", t1, "delta", t1 - t0, "audits delta", ta1 - ta0)
        if not (
            r.status_code == 200
            and d.get("pending")
            and conf.get("tool") == "create_ticket"
            and t1 == t0
            and ta1 == ta0
            and not created_claim
        ):
            failed.append("PENDING_TICKET")
            print("PENDING_TICKET FAIL")
        else:
            print("PENDING_TICKET PASS")

        r2 = client.post(
            f"{agent}/agent/chat",
            headers=h,
            json={"thread_id": tid, "message": "再问一句"},
        )
        print("PENDING_CHAT", r2.status_code, r2.text[:220])
        if r2.status_code != 409:
            failed.append("PENDING_CHAT")
            print("PENDING_CHAT FAIL")
        else:
            print("PENDING_CHAT PASS")

        tok_s = login("support@opspilot.local", "password123")
        r3 = client.post(
            f"{agent}/agent/chat/resume",
            headers={"Authorization": f"Bearer {tok_s}"},
            json={"thread_id": tid, "action": "approve"},
        )
        print("OTHER_RESUME", r3.status_code, r3.text[:220])
        if r3.status_code != 403:
            failed.append("OTHER_RESUME")
            print("OTHER_RESUME FAIL")
        else:
            print("OTHER_RESUME PASS")

        r4 = client.post(
            f"{agent}/agent/chat/resume",
            headers=h,
            json={"thread_id": tid, "action": "approve"},
        )
        d4 = r4.json().get("data") or {}
        print("APPROVE status", r4.status_code, "pending", d4.get("pending"))
        print("APPROVE tools", (d4.get("metadata") or {}).get("tools_called"))
        print(
            "APPROVE results",
            json.dumps((d4.get("metadata") or {}).get("tool_results"), ensure_ascii=False)[:600],
        )
        print("APPROVE reply", (d4.get("message") or "")[:240].replace("\n", " "))
        t2, ta2, _, _ = _counts()
        print("DB after approve tickets", t2, "delta", t2 - t1, "audits delta", ta2 - ta1)
        ok_approve = (
            r4.status_code == 200
            and not d4.get("pending")
            and "create_ticket" in ((d4.get("metadata") or {}).get("tools_called") or [])
            and t2 == t1 + 1
            and ta2 == ta1 + 1
        )
        if not ok_approve:
            failed.append("APPROVE")
            print("APPROVE FAIL")
        else:
            print("APPROVE PASS")

        humans = _human_messages(tid)
        print("HUMANS", humans)
        if len(humans) != 1 or humans[0].strip() in {"确认", "approve"}:
            failed.append("NO_HUMAN_CONFIRM")
            print("NO_HUMAN_CONFIRM FAIL")
        else:
            print("NO_HUMAN_CONFIRM PASS")

        r5 = client.post(
            f"{agent}/agent/chat/resume",
            headers=h,
            json={"thread_id": tid, "action": "approve"},
        )
        print("DUP_APPROVE", r5.status_code, r5.text[:220])
        t3, _, _, _ = _counts()
        if r5.status_code != 409 or t3 != t2:
            failed.append("DUP_APPROVE")
            print("DUP_APPROVE FAIL db", t3, t2)
        else:
            print("DUP_APPROVE PASS")

        # reject
        t4, ta4, _, _ = _counts()
        tid_r = f"p14_rej_{uuid.uuid4().hex[:8]}"
        rr = client.post(
            f"{agent}/agent/chat",
            headers=h,
            json={
                "thread_id": tid_r,
                "message": "帮我创建一个 VPN 故障工单，标题 VPN 故障，描述测试取消 HITL，优先级 high。请直接创建。",
            },
        )
        dd = rr.json().get("data") or {}
        print("REJECT_PENDING pending", dd.get("pending"), "tool", (dd.get("confirmation") or {}).get("tool"))
        rj = client.post(
            f"{agent}/agent/chat/resume",
            headers=h,
            json={"thread_id": tid_r, "action": "reject"},
        )
        dj = rj.json().get("data") or {}
        print("REJECT status", rj.status_code, "pending", dj.get("pending"))
        print("REJECT reply", (dj.get("message") or "")[:240].replace("\n", " "))
        t5, ta5, _, _ = _counts()
        print("DB after reject delta tickets", t5 - t4, "audits", ta5 - ta4)
        if not (dd.get("pending") and rj.status_code == 200 and t5 == t4 and ta5 == ta4):
            failed.append("REJECT")
            print("REJECT FAIL")
        else:
            print("REJECT PASS")

        # permission HITL
        t6, ta6, p6, pa6 = _counts()
        tid_p = f"p14_perm_{uuid.uuid4().hex[:8]}"
        rp = client.post(
            f"{agent}/agent/chat",
            headers=h,
            json={
                "thread_id": tid_p,
                "message": "请帮我申请 GitLab 项目 OpsPilot 的 Developer 权限，原因是日常开发需要。参数已齐，请直接提交申请。",
            },
        )
        dp = rp.json().get("data") or {}
        print("PERM_PENDING pending", dp.get("pending"), "tool", (dp.get("confirmation") or {}).get("tool"))
        _, _, p7, pa7 = _counts()
        print("DB after perm pending perms delta", p7 - p6, "perm audits", pa7 - pa6)
        ra = client.post(
            f"{agent}/agent/chat/resume",
            headers=h,
            json={"thread_id": tid_p, "action": "approve"},
        )
        da = ra.json().get("data") or {}
        print("PERM_APPROVE status", ra.status_code)
        print(
            "PERM_APPROVE results",
            json.dumps((da.get("metadata") or {}).get("tool_results"), ensure_ascii=False)[:600],
        )
        print("PERM_APPROVE reply", (da.get("message") or "")[:260].replace("\n", " "))
        _, _, p8, pa8 = _counts()
        print("DB after perm approve perms delta", p8 - p6, "perm audits", pa8 - pa6)
        reply = da.get("message") or ""
        bad_claim = any(x in reply for x in ("已开通", "已审批通过", "审批已完成"))
        status_ok = True
        for tr in (da.get("metadata") or {}).get("tool_results") or []:
            if tr.get("tool") == "create_permission":
                st = ((tr.get("result") or {}).get("data") or {}).get("status")
                print("PERM status field", st)
                if st and str(st).lower() not in {"pending"}:
                    status_ok = False
        if not (
            dp.get("pending")
            and (dp.get("confirmation") or {}).get("tool") == "create_permission"
            and p7 == p6
            and p8 == p6 + 1
            and pa8 == pa6 + 1
            and not bad_claim
            and status_ok
        ):
            failed.append("PERM")
            print("PERM FAIL")
        else:
            print("PERM PASS")

        print("TID_TICKET", tid)
        print("FAILED", failed)
        return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
