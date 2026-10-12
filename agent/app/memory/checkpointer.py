"""LangGraph Checkpointer factory (Phase 11.1).

Backends:
- postgres (default when CHECKPOINT_DATABASE_URL set / production Compose)
- memory   (local / eval fallback via CHECKPOINT_BACKEND=memory)

No Redis. No long-term user memory.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.db import checkpoint_backend, close_pool, get_pool

logger = logging.getLogger(__name__)

_checkpointer: Any = None
_backend_in_use: str | None = None


def get_checkpointer() -> Any:
    """Singleton checkpointer shared by the compiled graph."""
    global _checkpointer, _backend_in_use
    if _checkpointer is not None:
        return _checkpointer

    backend = checkpoint_backend()
    if backend == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver

        pool = get_pool()
        saver = PostgresSaver(pool)
        saver.setup()
        _checkpointer = saver
        _backend_in_use = "postgres"
        logger.info("using PostgresSaver checkpointer")
    else:
        _checkpointer = MemorySaver()
        _backend_in_use = "memory"
        logger.info("using MemorySaver checkpointer")
    return _checkpointer


def checkpointer_backend_in_use() -> str | None:
    return _backend_in_use


def reset_checkpointer_for_tests() -> None:
    """Clear checkpointer (+ pool when postgres). Tests / eval only."""
    global _checkpointer, _backend_in_use
    _checkpointer = None
    _backend_in_use = None
    if checkpoint_backend() == "postgres":
        close_pool()
