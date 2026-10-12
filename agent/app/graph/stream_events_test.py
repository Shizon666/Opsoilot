"""Stdlib tests for Phase 13 public SSE event shaping (no LLM)."""

from __future__ import annotations

import json
import unittest

from app.graph.stream import PUBLIC_EVENT_TYPES, _public_event, format_sse


class StreamEventTests(unittest.TestCase):
    def test_public_types_only(self) -> None:
        self.assertEqual(
            PUBLIC_EVENT_TYPES,
            frozenset(
                {
                    "start",
                    "token",
                    "tool_start",
                    "tool_end",
                    "confirmation",
                    "error",
                    "done",
                }
            ),
        )
        self.assertIsNone(_public_event({"type": "langgraph_node"}))
        self.assertIsNone(_public_event({"type": "on_chat_model_stream"}))
        self.assertIsNone(_public_event({"type": "thinking"}))

    def test_drop_empty_token(self) -> None:
        self.assertIsNone(_public_event({"type": "token", "content": ""}))
        self.assertEqual(
            _public_event({"type": "token", "content": "你"}),
            {"type": "token", "content": "你"},
        )

    def test_tool_lifecycle_fields(self) -> None:
        start = _public_event(
            {"type": "tool_start", "tool": "get_current_user", "tool_call_id": "c1"}
        )
        self.assertEqual(
            start,
            {
                "type": "tool_start",
                "tool": "get_current_user",
                "tool_call_id": "c1",
            },
        )
        end = _public_event(
            {
                "type": "tool_end",
                "tool": "get_current_user",
                "tool_call_id": "c1",
                "ok": True,
                "result": {"secret": "nope"},
            }
        )
        self.assertEqual(
            end,
            {
                "type": "tool_end",
                "tool": "get_current_user",
                "tool_call_id": "c1",
                "ok": True,
            },
        )
        self.assertNotIn("result", end or {})

    def test_confirmation_public_fields(self) -> None:
        ev = _public_event(
            {
                "type": "confirmation",
                "thread_id": "t1",
                "tool": "create_ticket",
                "tool_call_id": "c9",
                "args": {"title": "VPN 故障"},
                "jwt": "secret",
            }
        )
        self.assertEqual(
            ev,
            {
                "type": "confirmation",
                "thread_id": "t1",
                "tool": "create_ticket",
                "tool_call_id": "c9",
                "args": {"title": "VPN 故障"},
            },
        )
        self.assertNotIn("jwt", ev or {})

    def test_sse_data_line(self) -> None:
        raw = format_sse({"type": "token", "content": "研发部"})
        self.assertTrue(raw.startswith(b"data: "))
        self.assertTrue(raw.endswith(b"\n\n"))
        payload = json.loads(raw.decode("utf-8")[len("data: ") :].strip())
        self.assertEqual(payload["content"], "研发部")


if __name__ == "__main__":
    unittest.main()
