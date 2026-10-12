"""Offline isolation tests: dual collection config + protected rebuild (no live Milvus)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from app.rag import index as index_mod
from app.rag.milvus_store import (
    DEFAULT_COLLECTION,
    ENV_COLLECTION,
    ProtectedCollectionError,
    collection_name,
    count_rows,
    insert_rows,
    rebuild_collection,
)
from app.rag.retriever import _search


class CollectionNameTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(ENV_COLLECTION, None)

    def test_default_is_knowledge_docs(self) -> None:
        os.environ.pop(ENV_COLLECTION, None)
        self.assertEqual(collection_name(), DEFAULT_COLLECTION)
        self.assertEqual(DEFAULT_COLLECTION, "knowledge_docs")

    def test_env_overrides_collection(self) -> None:
        os.environ[ENV_COLLECTION] = "knowledge_docs_dayi"
        self.assertEqual(collection_name(), "knowledge_docs_dayi")

    def test_blank_env_falls_back_to_default(self) -> None:
        os.environ[ENV_COLLECTION] = "   "
        self.assertEqual(collection_name(), DEFAULT_COLLECTION)


class RebuildProtectionTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(ENV_COLLECTION, None)

    def test_refuse_drop_default_without_opt_in(self) -> None:
        client = MagicMock()
        client.has_collection.return_value = True
        with self.assertRaises(ProtectedCollectionError) as ctx:
            rebuild_collection(client, name=DEFAULT_COLLECTION, allow_drop_default=False)
        self.assertIn(DEFAULT_COLLECTION, str(ctx.exception))
        client.drop_collection.assert_not_called()
        client.create_collection.assert_not_called()

    def test_allow_drop_default_with_opt_in(self) -> None:
        client = MagicMock()
        client.has_collection.return_value = True
        with (
            patch("app.rag.milvus_store._schema", return_value="schema"),
            patch("app.rag.milvus_store._index_params", return_value="idx"),
            patch("app.rag.milvus_store.embed_dim", return_value=1024),
        ):
            name = rebuild_collection(client, name=DEFAULT_COLLECTION, allow_drop_default=True)
        self.assertEqual(name, DEFAULT_COLLECTION)
        client.drop_collection.assert_called_once_with(collection_name=DEFAULT_COLLECTION)
        client.create_collection.assert_called_once()

    def test_isolated_collection_rebuild_without_opt_in(self) -> None:
        client = MagicMock()
        client.has_collection.return_value = False
        with (
            patch("app.rag.milvus_store._schema", return_value="schema"),
            patch("app.rag.milvus_store._index_params", return_value="idx"),
            patch("app.rag.milvus_store.embed_dim", return_value=1024),
        ):
            name = rebuild_collection(client, name="knowledge_docs_dayi", allow_drop_default=False)
        self.assertEqual(name, "knowledge_docs_dayi")
        client.drop_collection.assert_not_called()
        client.create_collection.assert_called_once()
        kwargs = client.create_collection.call_args.kwargs
        self.assertEqual(kwargs["collection_name"], "knowledge_docs_dayi")


class WriteReadTargetTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(ENV_COLLECTION, None)

    def test_insert_and_count_use_explicit_name(self) -> None:
        client = MagicMock()
        client.insert.return_value = {"insert_count": 2}
        client.get_collection_stats.return_value = {"row_count": 2}
        rows = [{"chunk_id": "a"}, {"chunk_id": "b"}]
        inserted = insert_rows(client, rows, name="knowledge_docs_dayi")
        counted = count_rows(client, name="knowledge_docs_dayi")
        self.assertEqual(inserted, 2)
        self.assertEqual(counted, 2)
        self.assertEqual(client.insert.call_args.kwargs["collection_name"], "knowledge_docs_dayi")
        self.assertEqual(
            client.get_collection_stats.call_args.kwargs["collection_name"],
            "knowledge_docs_dayi",
        )

    def test_search_uses_env_collection(self) -> None:
        os.environ[ENV_COLLECTION] = "knowledge_docs_dayi"
        client = MagicMock()
        client.search.return_value = [[]]
        with patch("app.rag.retriever.connect", return_value=client):
            _search([0.0] * 4, top_k=3)
        self.assertEqual(client.search.call_args.kwargs["collection_name"], "knowledge_docs_dayi")

    def test_index_all_refuses_default_without_flag(self) -> None:
        os.environ.pop(ENV_COLLECTION, None)
        fake_chunks = [{"chunk_id": "c1", "doc_id": "D1", "content": "x", "title": "t"}]
        with (
            patch.object(index_mod, "assert_index_inputs_ready", return_value=1),
            patch.object(index_mod, "load_chunks", return_value=fake_chunks),
            patch.object(index_mod, "embed_texts", return_value=[[0.1, 0.2]]),
            patch.object(index_mod, "connect", return_value=MagicMock()),
            self.assertRaises(ProtectedCollectionError),
        ):
            index_mod.index_all(
                ops_root=Path("."),
                collection=DEFAULT_COLLECTION,
                allow_drop_default=False,
            )

    def test_index_all_writes_isolated_collection(self) -> None:
        fake_chunks: list[dict[str, Any]] = [
            {
                "chunk_id": "c1",
                "doc_id": "DY-B-INGEST-CONNECT-FAIL",
                "content": "推流连接失败",
                "title": "t",
                "section": "s",
            }
        ]
        client = MagicMock()
        client.has_collection.return_value = False
        client.insert.return_value = {"insert_count": 1}
        client.get_collection_stats.return_value = {"row_count": 1}
        with (
            patch.object(index_mod, "load_chunks", return_value=fake_chunks),
            patch.object(index_mod, "embed_texts", return_value=[[0.1] * 8]),
            patch.object(index_mod, "connect", return_value=client),
            patch("app.rag.milvus_store._schema", return_value="schema"),
            patch("app.rag.milvus_store._index_params", return_value="idx"),
            patch("app.rag.milvus_store.embed_dim", return_value=8),
            patch.object(index_mod, "embed_dim", return_value=8),
            patch.object(index_mod, "embed_model_name", return_value="BAAI/bge-m3"),
        ):
            report = index_mod.index_all(
                ops_root=Path("."),
                collection="knowledge_docs_dayi",
                allow_drop_default=False,
            )
        self.assertEqual(report["collection"], "knowledge_docs_dayi")
        self.assertEqual(report["chunks"], 1)
        self.assertEqual(client.create_collection.call_args.kwargs["collection_name"], "knowledge_docs_dayi")
        self.assertEqual(client.insert.call_args.kwargs["collection_name"], "knowledge_docs_dayi")
        client.drop_collection.assert_not_called()


class ResolveCollectionTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(ENV_COLLECTION, None)

    def test_explicit_wins_over_env(self) -> None:
        os.environ[ENV_COLLECTION] = "from_env"
        self.assertEqual(index_mod.resolve_collection("knowledge_docs_dayi"), "knowledge_docs_dayi")

    def test_env_used_when_explicit_none(self) -> None:
        os.environ[ENV_COLLECTION] = "from_env"
        self.assertEqual(index_mod.resolve_collection(None), "from_env")


if __name__ == "__main__":
    unittest.main()
