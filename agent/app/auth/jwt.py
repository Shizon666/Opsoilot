"""Verify user JWTs issued by Go Business API.

Agent and Go share JWT_SECRET and HS256. user_id comes from claim ``sub``;
role from claim ``role``. Never trust body/query identity fields.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import InvalidTokenError


class JWTError(Exception):
    """Raised when Authorization is missing or the token is invalid/expired."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: str
    role: str
    raw_token: str


def _secret() -> str:
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        raise JWTError("JWT_SECRET is not configured")
    return secret


def parse_bearer(authorization: str | None) -> str:
    """Extract raw token from ``Authorization: Bearer <token>``."""
    if not authorization or not authorization.strip():
        raise JWTError("missing Authorization header")
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise JWTError("invalid Authorization header")
    return parts[1].strip()


def verify_token(token: str, *, secret: str | None = None) -> TokenClaims:
    """Validate HS256 JWT and return user_id (sub) + role."""
    key = secret if secret is not None else _secret()
    if not key:
        raise JWTError("JWT_SECRET is not configured")
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except InvalidTokenError as exc:
        raise JWTError(f"invalid token: {exc}") from exc

    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise JWTError("token missing sub")
    role = payload.get("role") or ""
    if not isinstance(role, str):
        role = str(role)

    return TokenClaims(user_id=user_id, role=role, raw_token=token)


def verify_authorization(authorization: str | None, *, secret: str | None = None) -> TokenClaims:
    """Parse Bearer header then verify token."""
    return verify_token(parse_bearer(authorization), secret=secret)
