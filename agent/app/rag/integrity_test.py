"""Unit tests for processed inventory + index count integrity (no Milvus / embed)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.rag.integrity import (
    IndexIntegrityError,
    assert_index_counts_match,
    assert_index_inputs_ready,
    build_processed_inventory,
)
from app.rag import index as index_mod
from app.rag.milvus_store import DEFAULT_COLLECTION


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _minimal_catalog(doc_ids: list[str]) -> dict:
    return {
        "documents": [
            {
                "doc_id": doc_id,
                "title": doc_id,
                "category": "RUNBOOK",
                "source_type": "markdown",
                "source_path": f"raw/{doc_id}.md",
                "service": "PLATFORM",
                "department": "OPS",
                "severity": "MEDIUM",
                "status": "active",
                "canonical": True,
                "v1_ingest": True,
            }
            for doc_id in doc_ids
        ]
    }


def _ok_document(doc_id: str) -> dict:
    return {
        "doc_id": doc_id,
        "title": doc_id,
        "category": "RUNBOOK",
        "source_type": "markdown",
        "service": "PLATFORM",
        "department": "OPS",
        "severity": "MEDIUM",
        "created_at": "2026-01-01",
        "status": "active",
        "visibility": "INTERNAL",
        "content": "正文",
        "content_hash": "abc",
        "parse_status": "ok",
        "elements": [],
    }


def _ok_chunks(doc_id: str, n: int = 1) -> dict:
    chunks = [
        {
            "chunk_id": f"{doc_id}#{i}",
            "doc_id": doc_id,
            "title": doc_id,
            "content": f"chunk-{i}",
            "section": "s",
        }
        for i in range(n)
    ]
    return {"doc_id": doc_id, "chunk_count": n, "chunks": chunks}


class InventoryTests(unittest.TestCase):
    def test_ready_inventory_counts_chunks_not_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cat = root / "catalog.yaml"
            # two docs, three chunks total
            import yaml

            cat.write_text(
                yaml.safe_dump(_minimal_catalog(["A", "B"]), allow_unicode=True),
                encoding="utf-8",
            )
            _write_json(root / "processed" / "documents" / "A.json", _ok_document("A"))
            _write_json(root / "processed" / "documents" / "B.json", _ok_document("B"))
            _write_json(root / "processed" / "chunks" / "A.json", _ok_chunks("A", 2))
            _write_json(root / "processed" / "chunks" / "B.json", _ok_chunks("B", 1))
            inv = build_processed_inventory(root, catalog_path=cat)
            self.assertEqual(inv["catalog_eligible"], 2)
            self.assertEqual(inv["ok_documents"], 2)
            self.assertEqual(inv["expected_chunks"], 3)
            self.assertEqual(inv["problems"], [])
            self.assertEqual(assert_index_inputs_ready(root, catalog_path=cat), 3)

    def test_missing_document_is_problem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            import yaml

            cat = root / "catalog.yaml"
            cat.write_text(
                yaml.safe_dump(_minimal_catalog(["A", "B"]), allow_unicode=True),
                encoding="utf-8",
            )
            _write_json(root / "processed" / "documents" / "A.json", _ok_document("A"))
            _write_json(root / "processed" / "chunks" / "A.json", _ok_chunks("A", 1))
            inv = build_processed_inventory(root, catalog_path=cat)
            self.assertTrue(any(p["doc_id"] == "B" and "missing_document" in p["error"] for p in inv["problems"]))
            with self.assertRaises(IndexIntegrityError):
                assert_index_inputs_ready(root, catalog_path=cat)

    def test_parse_failed_never_counts_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            import yaml

            cat = root / "catalog.yaml"
            cat.write_text(
                yaml.safe_dump(_minimal_catalog(["A"]), allow_unicode=True),
                encoding="utf-8",
            )
            failed = _ok_document("A")
            failed["parse_status"] = "failed"
            _write_json(root / "processed" / "documents" / "A.json", failed)
            _write_json(root / "processed" / "chunks" / "A.json", _ok_chunks("A", 1))
            inv = build_processed_inventory(root, catalog_path=cat)
            self.assertEqual(inv["ok_documents"], 0)
            self.assertEqual(inv["expected_chunks"], 0)
            self.assertTrue(any("parse_status_not_ok" in p["error"] for p in inv["problems"]))
            with self.assertRaises(IndexIntegrityError):
                assert_index_inputs_ready(root, catalog_path=cat)

    def test_missing_chunks_is_problem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            import yaml

            cat = root / "catalog.yaml"
            cat.write_text(
                yaml.safe_dump(_minimal_catalog(["A"]), allow_unicode=True),
                encoding="utf-8",
            )
            _write_json(root / "processed" / "documents" / "A.json", _ok_document("A"))
            with self.assertRaises(IndexIntegrityError) as ctx:
                assert_index_inputs_ready(root, catalog_path=cat)
            self.assertIn("missing_chunk", str(ctx.exception))


class CountMatchTests(unittest.TestCase):
    def test_counts_must_equal_expected(self) -> None:
        report = {"chunks": 5, "embedded": 5, "inserted": 5, "count": 5}
        assert_index_counts_match(report, expected_chunks=5)

    def test_abort_when_embedded_short(self) -> None:
        report = {"chunks": 5, "embedded": 4, "inserted": 4, "count": 4}
        with self.assertRaises(IndexIntegrityError) as ctx:
            assert_index_counts_match(report, expected_chunks=5)
        self.assertIn("mismatch", str(ctx.exception))

    def test_quantity_change_uses_new_expected(self) -> None:
        # Replaces old hard-coded 43: any positive expected is valid if counts agree.
        report = {"chunks": 60, "embedded": 60, "inserted": 60, "count": 60}
        assert_index_counts_match(report, expected_chunks=60)
        with self.assertRaises(IndexIntegrityError):
            assert_index_counts_match(report, expected_chunks=43)


class IndexAllIntegrityTests(unittest.TestCase):
    def test_default_collection_stops_before_milvus_when_inventory_bad(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            import yaml

            cat = root / "catalog.yaml"
            cat.write_text(
                yaml.safe_dump(_minimal_catalog(["A"]), allow_unicode=True),
                encoding="utf-8",
            )
            # document ok but chunks missing → integrity error, no connect
            _write_json(root / "processed" / "documents" / "A.json", _ok_document("A"))
            with (
                patch.object(index_mod, "connect") as connect_mock,
                self.assertRaises(IndexIntegrityError),
            ):
                index_mod.index_all(
                    ops_root=root,
                    collection=DEFAULT_COLLECTION,
                    allow_drop_default=True,
                )
            connect_mock.assert_not_called()

    def test_count_mismatch_after_insert_raises(self) -> None:
        fake_chunks = [
            {"chunk_id": "c1", "doc_id": "D1", "content": "x", "title": "t", "section": "s"}
        ]
        client = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
        client.has_collection.return_value = False
        client.insert.return_value = {"insert_count": 1}
        client.get_collection_stats.return_value = {"row_count": 0}  # abort / incomplete
        with (
            patch.object(index_mod, "load_chunks", return_value=fake_chunks),
            patch.object(index_mod, "embed_texts", return_value=[[0.1] * 4]),
            patch.object(index_mod, "connect", return_value=client),
            patch("app.rag.milvus_store._schema", return_value="schema"),
            patch("app.rag.milvus_store._index_params", return_value="idx"),
            patch("app.rag.milvus_store.embed_dim", return_value=4),
            patch.object(index_mod, "embed_dim", return_value=4),
            patch.object(index_mod, "embed_model_name", return_value="BAAI/bge-m3"),
            self.assertRaises(IndexIntegrityError),
        ):
            index_mod.index_all(
                ops_root=Path("."),
                collection="knowledge_docs_isolated",
                allow_drop_default=False,
            )


if __name__ == "__main__":
    unittest.main()
