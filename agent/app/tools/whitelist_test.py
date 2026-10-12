"""Phase C-1: V1 tool whitelist (no LLM)."""

from __future__ import annotations

import unittest

from app.graph.agent import WRITE_TOOLS
from app.tools import AGENT_TOOLS


class ToolWhitelistTests(unittest.TestCase):
    def test_runtime_names(self) -> None:
        names = {t.name for t in AGENT_TOOLS}
        self.assertEqual(
            names,
            {
                "get_current_user",
                "list_services",
                "get_service_status",
                "search_tickets",
                "get_ticket",
                "create_ticket",
                "update_ticket",
                "search_knowledge",
            },
        )
        self.assertTrue({"get_my_permissions", "create_permission", "get_my_tickets"}.isdisjoint(names))

    def test_write_tools(self) -> None:
        self.assertEqual(WRITE_TOOLS, frozenset({"create_ticket", "update_ticket"}))
        self.assertNotIn("create_permission", WRITE_TOOLS)
