"""Per-request identity for Agent → Go Business Client.

Set once in /agent/chat after JWT verification; Tools/Client read via require_*.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_user_jwt: ContextVar[str | None] = ContextVar("opspilot_user_jwt", default=None)
_user_id: ContextVar[str | None] = ContextVar("opspilot_user_id", default=None)
_role: ContextVar[str | None] = ContextVar("opspilot_role", default=None)
_request_id: ContextVar[str | None] = ContextVar("opspilot_request_id", default=None)


class MissingUserJWTError(RuntimeError):
    """Raised when a Tool/Client needs user JWT but request context is empty."""


def require_user_jwt() -> str:
    token = _user_jwt.get()
    if not token:
        raise MissingUserJWTError("user JWT not set in request context")
    return token


def get_user_id() -> str | None:
    return _user_id.get()


def get_role() -> str | None:
    return _role.get()


def get_request_id() -> str | None:
    return _request_id.get()


def require_request_id() -> str:
    rid = _request_id.get()
    if not rid:
        raise RuntimeError("request_id not set in request context")
    return rid


@contextmanager
def user_context(
    *,
    user_jwt: str,
    user_id: str,
    role: str = "",
    request_id: str = "",
) -> Iterator[None]:
    """Bind caller identity for the duration of one /agent/chat turn."""
    t_jwt: Token = _user_jwt.set(user_jwt)
    t_id: Token = _user_id.set(user_id)
    t_role: Token = _role.set(role)
    t_rid: Token = _request_id.set(request_id or None)
    try:
        yield
    finally:
        _user_jwt.reset(t_jwt)
        _user_id.reset(t_id)
        _role.reset(t_role)
        _request_id.reset(t_rid)
