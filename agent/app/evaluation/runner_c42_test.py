"""Unit tests for C-4.3 runner assertions (no LLM)."""

from __future__ import annotations

import unittest

from app.evaluation.runner import (
    V1_CASES_PATH,
    _assert_result,
    _check_interrupt,
    _check_silent_write,
    _check_text,
    _check_tools,
    _iter_turns,
    load_cases,
)
from app.graph.agent import AgentResult


class C42RunnerChecksTests(unittest.TestCase):
    def test_load_v1_p0_cases(self) -> None:
        cases = load_cases(V1_CASES_PATH)
        ids = [c["id"] for c in cases]
        self.assertEqual(len(cases), 20)
        self.assertIn("e1_checkout_consult_no_ticket", ids)
        self.assertIn("e7_reject_then_still_answer", ids)
        self.assertTrue(all(c.get("priority") == "P0" for c in cases))

    def test_turns_and_single_question(self) -> None:
        single = {"id": "x", "question": "hello"}
        self.assertEqual(_iter_turns(single)[0]["question"], "hello")
        multi = {"turns": [{"question": "a"}, {"question": "b"}]}
        self.assertEqual(len(_iter_turns(multi)), 2)

    def test_interrupt_and_text(self) -> None:
        self.assertEqual(_check_interrupt(None, True), [])
        self.assertTrue(_check_interrupt(True, False))
        self.assertEqual(_check_interrupt(False, False), [])
        self.assertTrue(_check_text(["问题判断"], "无此板块", must=True))
        self.assertEqual(_check_text(["问题判断"], "问题判断：ok", must=True), [])
        self.assertTrue(_check_text(["已为你创建"], "已为你创建工单", must=False))

    def test_silent_write(self) -> None:
        self.assertTrue(_check_silent_write(["create_ticket"], pending=False, resumed=False))
        self.assertEqual(_check_silent_write(["create_ticket"], pending=True, resumed=False), [])
        self.assertEqual(_check_silent_write(["create_ticket"], pending=False, resumed=True), [])
        self.assertEqual(_check_silent_write(["search_tickets"], pending=False, resumed=False), [])

    def test_required_tools_any_of(self) -> None:
        spec = {"required_tools": [["list_services", "get_service_status"], "search_tickets"]}
        self.assertEqual(_check_tools(spec, ["list_services", "search_tickets"]), [])
        self.assertEqual(_check_tools(spec, ["get_service_status", "search_tickets"]), [])
        self.assertTrue(_check_tools(spec, ["search_tickets"]))

    def test_assert_result_consult(self) -> None:
        spec = {
            "required_tools": ["search_tickets"],
            "forbidden_tools": ["create_ticket"],
            "expect_interrupt": False,
            "text_must": ["问题判断"],
            "text_must_not": ["已为你创建"],
        }
        ok = AgentResult(
            message="问题判断：咨询",
            tools_called=["search_tickets"],
            pending=False,
        )
        self.assertEqual(_assert_result(spec, ok, resumed=False), [])
        bad = AgentResult(
            message="已为你创建",
            tools_called=["search_tickets", "create_ticket"],
            pending=False,
        )
        reasons = _assert_result(spec, bad, resumed=False)
        self.assertTrue(any("forbidden tools" in r or "silent write" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
