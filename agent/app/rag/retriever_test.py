"""C-3.4 retriever: hit mapping (offline) + live recall cases when Milvus is up."""

from __future__ import annotations

import os
import unittest

from app.rag.retriever import HIT_KEYS, hit_from_search_row, retrieve


class HitMappingTests(unittest.TestCase):
    def test_maps_phase_a_keys_and_threshold(self) -> None:
        row = {
            "distance": 0.81,
            "entity": {
                "doc_id": "OPS-RB-CHECKOUT-5XX",
                "content": "收银台 502",
                "metadata": {
                    "title": "Checkout API 5xx 排查手册",
                    "section": "现象",
                    "source_path": "raw/runbook/ops-rb-checkout-5xx.md",
                },
            },
        }
        hit = hit_from_search_row(row, min_score=0.45)
        assert hit is not None
        self.assertEqual(set(hit.keys()), set(HIT_KEYS))
        self.assertEqual(hit["doc_id"], "OPS-RB-CHECKOUT-5XX")
        self.assertEqual(hit["path"], "raw/runbook/ops-rb-checkout-5xx.md")
        self.assertEqual(hit["section"], "现象")
        self.assertEqual(hit["score"], 0.81)
        self.assertEqual(hit["confidence_level"], "high")

    def test_below_min_score_dropped(self) -> None:
        row = {
            "distance": 0.2,
            "entity": {
                "doc_id": "OPS-RB-CHECKOUT-5XX",
                "content": "x",
                "metadata": {"title": "t", "section": "s"},
            },
        }
        self.assertIsNone(hit_from_search_row(row, min_score=0.45))

    def test_empty_query(self) -> None:
        self.assertEqual(retrieve("   ", top_k=5), [])


@unittest.skipUnless(
    os.getenv("OPSPILOT_LIVE_RETRIEVE", "1") == "1",
    "live retrieve disabled",
)
class LiveRetrieveTests(unittest.TestCase):
    def test_checkout_502_recalls_checkout_runbook(self) -> None:
        hits = retrieve("checkout接口502", top_k=5)
        self.assertTrue(hits, "expected Checkout runbook hits")
        self.assertTrue(
            any(
                str(h.get("doc_id", "")).startswith("OPS-RB-CHECKOUT")
                or "Checkout" in str(h.get("title", ""))
                for h in hits
            ),
            hits,
        )
        self.assertEqual(set(hits[0].keys()), set(HIT_KEYS))

    def test_auth_failure_recalls_auth(self) -> None:
        hits = retrieve("登录认证失败", top_k=5)
        self.assertTrue(hits, "expected Auth hits")
        self.assertTrue(
            any(
                "AUTH" in str(h.get("doc_id", "")).upper()
                or "Auth" in str(h.get("title", ""))
                or "登录" in str(h.get("title", ""))
                for h in hits
            ),
            hits,
        )

    def test_beijing_weather_no_hits(self) -> None:
        hits = retrieve("今天北京天气", top_k=5)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
