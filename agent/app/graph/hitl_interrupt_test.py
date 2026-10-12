"""HITL hard-gate tests: interrupt before tool.invoke, Command(resume), no HumanMessage."""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

os.environ["CHECKPOINT_BACKEND"] = "memory"
os.environ.setdefault("LLM_API_KEY", "test-hitl-key")

from app.graph.agent import (  # noqa: E402
    AgentError,
    _get_graph,
    _invoke_config,
    _is_approve,
    _public_tool_args,
    reset_graph_for_tests,
    resume_agent,
    run_agent,
)


def _scripted_llm(tool_calls: list[dict]):
    class ScriptedLLM:
        def bind_tools(self, _tools):
            return self

        def stream(self, msgs):
            if any(isinstance(m, ToolMessage) for m in msgs):
                last = [m for m in msgs if isinstance(m, ToolMessage)][-1]
                try:
                    payload = json.loads(str(last.content))
                except json.JSONDecodeError:
                    payload = {}
                if payload.get("cancelled"):
                    yield AIMessage(content="操作已取消，没有提交。")
                else:
                    yield AIMessage(content="已根据工具结果完成。")
                return
            yield AIMessage(content="", tool_calls=tool_calls)

    return ScriptedLLM()


class HitlInterruptTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_graph_for_tests()

    def test_public_args_drop_secrets(self) -> None:
        out = _public_tool_args(
            {"title": "VPN 故障", "authorization": "Bearer x", "jwt": "hidden"}
        )
        self.assertEqual(out.get("title"), "VPN 故障")
        self.assertNotIn("authorization", out)
        self.assertNotIn("jwt", out)

    def test_is_approve(self) -> None:
        self.assertTrue(_is_approve("approve"))
        self.assertTrue(_is_approve({"action": "approve"}))
        self.assertFalse(_is_approve("reject"))
        self.assertFalse(_is_approve("yes"))

    def test_write_interrupts_before_invoke_then_command_resume(self) -> None:
        invokes: list[str] = []

        @tool("create_ticket")
        def create_ticket(title: str, description: str, priority: str = "medium") -> str:
            """Create a ticket (test stub)."""
            invokes.append(title)
            return json.dumps(
                {"ok": True, "data": {"id": "t1", "ticket_no": "T-HITL", "status": "open"}},
                ensure_ascii=False,
            )

        llm = _scripted_llm(
            [
                {
                    "name": "create_ticket",
                    "id": "call_hitl_1",
                    "args": {
                        "title": "VPN 故障",
                        "description": "连不上",
                        "priority": "high",
                    },
                }
            ]
        )
        thread_id = "hitl_unit_ticket"
        with (
            patch("app.graph.agent.AGENT_TOOLS", [create_ticket]),
            patch("app.graph.agent._build_llm", return_value=llm),
        ):
            reset_graph_for_tests()
            pending = run_agent("帮我创建一个 VPN 故障工单", thread_id=thread_id)
            self.assertTrue(pending.pending)
            self.assertEqual(pending.confirmation["tool"], "create_ticket")
            self.assertEqual(invokes, [])

            with self.assertRaises(AgentError) as chat_exc:
                run_agent("再问一句", thread_id=thread_id)
            self.assertEqual(chat_exc.exception.code, 40901)

            done = resume_agent(thread_id=thread_id, action="approve")
            self.assertFalse(done.pending)
            self.assertEqual(invokes, ["VPN 故障"])
            self.assertIn("create_ticket", done.tools_called)

            humans = [
                m
                for m in (_get_graph().get_state(_invoke_config(thread_id)).values or {}).get(
                    "messages"
                )
                or []
                if isinstance(m, HumanMessage)
            ]
            self.assertEqual(len(humans), 1)
            self.assertEqual(humans[0].content, "帮我创建一个 VPN 故障工单")
            self.assertFalse(any("确认" == (h.content or "").strip() for h in humans))

            with self.assertRaises(AgentError) as dup:
                resume_agent(thread_id=thread_id, action="approve")
            self.assertEqual(dup.exception.code, 40902)
            self.assertEqual(invokes, ["VPN 故障"])

    def test_reject_does_not_invoke(self) -> None:
        invokes: list[str] = []

        @tool("create_ticket")
        def create_ticket(title: str, description: str, priority: str = "medium") -> str:
            """Create a ticket (test stub)."""
            invokes.append(title)
            return json.dumps({"ok": True, "data": {}}, ensure_ascii=False)

        llm = _scripted_llm(
            [
                {
                    "name": "create_ticket",
                    "id": "call_hitl_rej",
                    "args": {"title": "VPN 故障", "description": "取消", "priority": "high"},
                }
            ]
        )
        thread_id = "hitl_unit_reject"
        with (
            patch("app.graph.agent.AGENT_TOOLS", [create_ticket]),
            patch("app.graph.agent._build_llm", return_value=llm),
        ):
            reset_graph_for_tests()
            pending = run_agent("创建工单", thread_id=thread_id)
            self.assertTrue(pending.pending)
            done = resume_agent(thread_id=thread_id, action="reject")
            self.assertEqual(invokes, [])
            self.assertFalse(done.pending)
            self.assertIn("取消", done.message)

    def test_multiple_writes_cancelled_without_invoke(self) -> None:
        invokes: list[str] = []

        @tool("create_ticket")
        def create_ticket(title: str, description: str, priority: str = "medium") -> str:
            """Create a ticket (test stub)."""
            invokes.append("ticket")
            return json.dumps({"ok": True, "data": {}}, ensure_ascii=False)

        @tool("update_ticket")
        def update_ticket(ticket_id: str, status: str = "in_progress") -> str:
            """Update a ticket (test stub)."""
            invokes.append("update")
            return json.dumps({"ok": True, "data": {}}, ensure_ascii=False)

        llm = _scripted_llm(
            [
                {
                    "name": "create_ticket",
                    "id": "c1",
                    "args": {
                        "title": "A",
                        "description": "d",
                        "service_id": "33333333-3333-3333-3333-333333333401",
                        "priority": "low",
                    },
                },
                {
                    "name": "update_ticket",
                    "id": "c2",
                    "args": {"ticket_id": "t1", "status": "in_progress"},
                },
            ]
        )
        with (
            patch("app.graph.agent.AGENT_TOOLS", [create_ticket, update_ticket]),
            patch("app.graph.agent._build_llm", return_value=llm),
        ):
            reset_graph_for_tests()
            result = run_agent("同时建单和改单", thread_id="hitl_multi")
            self.assertFalse(result.pending)
            self.assertEqual(invokes, [])
            self.assertTrue(
                any(
                    (tr.get("result") or {}).get("cancelled")
                    for tr in result.tool_results
                )
            )


if __name__ == "__main__":
    unittest.main()
