"""Cosine retrieve unit tests (no embedding model download)."""

from __future__ import annotations

import unittest

import numpy as np

from app.rag.local_store import KnowledgeChunk, confidence_level_for_score, retrieve_with_matrix


class CosineRetrieveTests(unittest.TestCase):
    def test_top_hit_and_threshold(self) -> None:
        chunks = [
            KnowledgeChunk("a", "Checkout", "a.md", "现象", "收银台 502 支付超时"),
            KnowledgeChunk("b", "Auth", "b.md", "现象", "登录失败密码错误"),
        ]
        # already L2-normalized-ish orthogonal-ish vectors
        embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        q = np.array([0.95, 0.05], dtype=np.float32)
        q = q / np.linalg.norm(q)
        hits = retrieve_with_matrix(q, embs, chunks, top_k=3, min_score=0.5)
        self.assertTrue(hits)
        self.assertEqual(hits[0]["doc_id"], "a")
        self.assertEqual(set(hits[0].keys()), {
            "doc_id",
            "title",
            "path",
            "section",
            "snippet",
            "score",
            "confidence_level",
        })

    def test_below_threshold_empty(self) -> None:
        chunks = [KnowledgeChunk("a", "t", "a.md", "s", "x")]
        embs = np.array([[1.0, 0.0]], dtype=np.float32)
        q = np.array([0.0, 1.0], dtype=np.float32)
        hits = retrieve_with_matrix(q, embs, chunks, top_k=3, min_score=0.4)
        self.assertEqual(hits, [])

    def test_confidence_bands(self) -> None:
        self.assertEqual(confidence_level_for_score(0.9), "high")
        self.assertIn(confidence_level_for_score(0.46), {"medium", "high"})
        self.assertEqual(confidence_level_for_score(0.1), "low")


if __name__ == "__main__":
    unittest.main()
