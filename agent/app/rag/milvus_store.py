"""Milvus collection helpers (C-3.3). Default collection is knowledge_docs."""

from __future__ import annotations

import logging
import os
from typing import Any

from pymilvus import DataType, MilvusClient

from app.rag.embedding import embed_dim

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION = "knowledge_docs"
# Backward-compatible alias: the protected default name (not the active runtime target).
COLLECTION = DEFAULT_COLLECTION
DEFAULT_URI = "http://127.0.0.1:19530"
ENV_COLLECTION = "MILVUS_COLLECTION"


class ProtectedCollectionError(RuntimeError):
    """Raised when a destructive rebuild targets the default collection without opt-in."""


def milvus_uri() -> str:
    return (os.getenv("MILVUS_URI") or DEFAULT_URI).strip()


def collection_name() -> str:
    """Active Milvus collection: MILVUS_COLLECTION or knowledge_docs."""
    raw = (os.getenv(ENV_COLLECTION) or DEFAULT_COLLECTION).strip()
    return raw or DEFAULT_COLLECTION


def connect(uri: str | None = None) -> MilvusClient:
    target = uri or milvus_uri()
    logger.info("milvus connect uri=%s", target)
    return MilvusClient(uri=target)


def _schema() -> Any:
    schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
    schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, max_length=128)
    schema.add_field(field_name="doc_id", datatype=DataType.VARCHAR, max_length=128)
    schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=8192)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=embed_dim())
    schema.add_field(field_name="metadata", datatype=DataType.JSON)
    return schema


def _index_params() -> Any:
    params = MilvusClient.prepare_index_params()
    params.add_index(
        field_name="embedding",
        index_type="FLAT",
        metric_type="COSINE",
    )
    return params


def rebuild_collection(
    client: MilvusClient,
    *,
    name: str | None = None,
    allow_drop_default: bool = False,
) -> str:
    """Drop+create collection. Protects knowledge_docs unless allow_drop_default=True.

    Returns the collection name that was rebuilt.
    """
    target = (name or collection_name()).strip() or DEFAULT_COLLECTION
    if target == DEFAULT_COLLECTION and not allow_drop_default:
        raise ProtectedCollectionError(
            f"refusing to drop/rebuild protected collection {DEFAULT_COLLECTION!r}; "
            f"pass allow_drop_default=True / --allow-drop-default-collection for the "
            f"legacy payment index, or set {ENV_COLLECTION} to an isolated name "
            f"(e.g. knowledge_docs_dayi)"
        )
    if client.has_collection(collection_name=target):
        logger.info("drop collection %s", target)
        client.drop_collection(collection_name=target)
    client.create_collection(
        collection_name=target,
        schema=_schema(),
        index_params=_index_params(),
    )
    logger.info("created collection %s dim=%s", target, embed_dim())
    return target


def insert_rows(
    client: MilvusClient,
    rows: list[dict[str, Any]],
    *,
    name: str | None = None,
) -> int:
    target = (name or collection_name()).strip() or DEFAULT_COLLECTION
    if not rows:
        return 0
    result = client.insert(collection_name=target, data=rows)
    inserted = int(result.get("insert_count") or len(rows))
    client.flush(collection_name=target)
    logger.info("inserted %s rows into %s", inserted, target)
    return inserted


def count_rows(client: MilvusClient, *, name: str | None = None) -> int:
    target = (name or collection_name()).strip() or DEFAULT_COLLECTION
    stats = client.get_collection_stats(collection_name=target)
    if isinstance(stats, dict) and stats.get("row_count") is not None:
        return int(stats["row_count"])
    rows = client.query(collection_name=target, filter="id >= 0", output_fields=["id"], limit=16384)
    return len(rows)
