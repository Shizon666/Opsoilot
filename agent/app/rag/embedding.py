"""SiliconFlow embeddings (BAAI/bge-m3). No local sentence-transformers."""

from __future__ import annotations

import logging
import math
import os
from typing import Sequence

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"
DEFAULT_MODEL = "BAAI/bge-m3"
DEFAULT_DIM = 1024
DEFAULT_BATCH = 16


class EmbedError(RuntimeError):
    pass


def embed_model_name() -> str:
    return (os.getenv("EMBED_MODEL_NAME") or DEFAULT_MODEL).strip()


def embed_dim() -> int:
    raw = (os.getenv("EMBED_DIM") or str(DEFAULT_DIM)).strip()
    try:
        return int(raw)
    except ValueError as exc:
        raise EmbedError(f"invalid EMBED_DIM={raw}") from exc


def _base_url() -> str:
    return (os.getenv("SILICONFLOW_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def _api_key() -> str:
    key = (os.getenv("SILICONFLOW_API_KEY") or "").strip()
    if not key:
        raise EmbedError("SILICONFLOW_API_KEY is missing")
    return key


def _embeddings_url() -> str:
    base = _base_url()
    if base.endswith("/embeddings"):
        return base
    if base.endswith("/v1"):
        return f"{base}/embeddings"
    return f"{base}/v1/embeddings"


def l2_normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(float(x) * float(x) for x in vector))
    if norm == 0.0:
        return [float(x) for x in vector]
    return [float(x) / norm for x in vector]


def _parse_vectors(payload: object, expected: int) -> list[list[float]]:
    if not isinstance(payload, dict):
        raise EmbedError("embedding response is not an object")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != expected:
        raise EmbedError(f"embedding count mismatch: want {expected} got {0 if not isinstance(data, list) else len(data)}")
    ordered = sorted(data, key=lambda row: int(row.get("index", 0)) if isinstance(row, dict) else 0)
    vectors: list[list[float]] = []
    dim = embed_dim()
    for row in ordered:
        if not isinstance(row, dict) or not isinstance(row.get("embedding"), list):
            raise EmbedError("embedding item missing embedding[]")
        vec = [float(x) for x in row["embedding"]]
        if len(vec) != dim:
            raise EmbedError(f"embedding dim mismatch: want {dim} got {len(vec)}")
        vectors.append(l2_normalize(vec))
    return vectors


def embed_texts(texts: list[str], *, batch_size: int = DEFAULT_BATCH) -> list[list[float]]:
    """Map chunk texts to L2-normalized dense vectors. Any batch failure aborts the whole job."""
    if not texts:
        return []
    url = _embeddings_url()
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    model = embed_model_name()
    out: list[list[float]] = []
    with httpx.Client(timeout=60.0) as client:
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            logger.info("embed batch offset=%s size=%s model=%s", start, len(batch), model)
            try:
                resp = client.post(url, headers=headers, json={"model": model, "input": batch, "encoding_format": "float"})
            except httpx.HTTPError as exc:
                raise EmbedError(f"embedding request failed: {exc}") from exc
            if resp.status_code >= 400:
                raise EmbedError(f"embedding HTTP {resp.status_code}: {resp.text[:500]}")
            try:
                payload = resp.json()
            except ValueError as exc:
                raise EmbedError("embedding response is not JSON") from exc
            out.extend(_parse_vectors(payload, len(batch)))
    if len(out) != len(texts):
        raise EmbedError("embedding count mismatch after batches")
    return out
