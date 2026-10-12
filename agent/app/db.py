"""Agent Checkpoint DB helpers (Phase 11.1).

Isolated database ``opspilot_agent`` — never the Go business DB tables.
Used only for LangGraph checkpoints + thread ownership.
"""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urlparse, urlunparse

from psycopg import Connection
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None

DEFAULT_CHECKPOINT_URL = (
    "postgres://opspilot:opspilot@postgres:5432/opspilot_agent?sslmode=disable"
)

_OWNERS_DDL = """
CREATE TABLE IF NOT EXISTS agent_thread_owners (
    thread_id   TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def checkpoint_backend() -> str:
    """Return ``postgres`` or ``memory``.

    Explicit CHECKPOINT_BACKEND wins. Otherwise: postgres if URL set, else memory.
    """
    raw = (os.getenv("CHECKPOINT_BACKEND") or "").strip().lower()
    if raw in ("postgres", "memory"):
        return raw
    if checkpoint_database_url():
        return "postgres"
    return "memory"


def checkpoint_database_url() -> str:
    return (os.getenv("CHECKPOINT_DATABASE_URL") or "").strip()


def _resolve_url() -> str:
    url = checkpoint_database_url() or DEFAULT_CHECKPOINT_URL
    return url


def _admin_url(db_url: str) -> tuple[str, str]:
    """Return (admin_conninfo pointing at maintenance DB, target db name)."""
    parsed = urlparse(db_url)
    dbname = (parsed.path or "/").lstrip("/") or "opspilot_agent"
    # strip query for path swap; keep query on admin URL
    admin = parsed._replace(path="/postgres")
    return urlunparse(admin), dbname


def ensure_agent_database(db_url: str | None = None) -> None:
    """CREATE DATABASE opspilot_agent if missing (connect via /postgres)."""
    url = db_url or _resolve_url()
    admin_url, dbname = _admin_url(url)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", dbname):
        raise RuntimeError(f"unsafe checkpoint database name: {dbname!r}")

    with Connection.connect(admin_url, autocommit=True) as conn:
        row = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (dbname,),
        ).fetchone()
        if row is None:
            logger.info("creating agent checkpoint database %s", dbname)
            conn.execute(f'CREATE DATABASE "{dbname}"')


def ensure_ownership_schema(pool: ConnectionPool | None = None) -> None:
    p = pool or get_pool()
    with p.connection() as conn:
        conn.execute(_OWNERS_DDL)


def get_pool() -> ConnectionPool:
    """Process-level connection pool to opspilot_agent."""
    global _pool
    if _pool is not None:
        return _pool

    url = _resolve_url()
    ensure_agent_database(url)
    _pool = ConnectionPool(
        conninfo=url,
        min_size=1,
        max_size=int(os.getenv("CHECKPOINT_POOL_MAX", "5")),
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=True,
    )
    ensure_ownership_schema(_pool)
    logger.info("agent checkpoint pool ready url_host=%s", urlparse(url).hostname)
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
