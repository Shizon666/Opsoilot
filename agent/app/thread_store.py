"""thread_id ↔ user_id ownership (Phase 8.1 / 11.1).

postgres backend: table agent_thread_owners in opspilot_agent DB.
memory backend: process-local dict (lost on restart).

Only ownership — never chat content / user profile.
"""

from __future__ import annotations

import logging
import threading

from app.db import checkpoint_backend, get_pool

logger = logging.getLogger(__name__)


class ThreadOwnershipError(Exception):
    """Raised when thread_id is bound to a different user_id."""

    def __init__(self, message: str = "thread_id does not belong to current user") -> None:
        super().__init__(message)
        self.message = message


class ThreadOwnershipStore:
    """bind_or_check: first use binds; later uses must match owner."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._owners: dict[str, str] = {}

    def bind_or_check(self, thread_id: str, user_id: str) -> None:
        tid = (thread_id or "").strip()
        uid = (user_id or "").strip()
        if not tid:
            raise ThreadOwnershipError("thread_id is empty")
        if not uid:
            raise ThreadOwnershipError("user_id is empty")

        if checkpoint_backend() == "postgres":
            self._bind_or_check_postgres(tid, uid)
        else:
            self._bind_or_check_memory(tid, uid)

    def _bind_or_check_memory(self, tid: str, uid: str) -> None:
        with self._lock:
            owner = self._owners.get(tid)
            if owner is None:
                self._owners[tid] = uid
                return
            if owner != uid:
                raise ThreadOwnershipError(
                    "thread_id does not belong to current user"
                )

    def _bind_or_check_postgres(self, tid: str, uid: str) -> None:
        pool = get_pool()
        with pool.connection() as conn:
            row = conn.execute(
                "SELECT user_id FROM agent_thread_owners WHERE thread_id = %s",
                (tid,),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO agent_thread_owners (thread_id, user_id) VALUES (%s, %s)",
                    (tid, uid),
                )
                return
            owner = row[0] if not isinstance(row, dict) else row.get("user_id")
            if owner != uid:
                raise ThreadOwnershipError(
                    "thread_id does not belong to current user"
                )

    def clear(self) -> None:
        """Tests only — clears memory map and/or ownership rows."""
        with self._lock:
            self._owners.clear()
        if checkpoint_backend() == "postgres":
            try:
                pool = get_pool()
                with pool.connection() as conn:
                    conn.execute("DELETE FROM agent_thread_owners")
            except Exception as exc:  # noqa: BLE001
                logger.warning("clear agent_thread_owners failed: %s", exc)


thread_ownership = ThreadOwnershipStore()
