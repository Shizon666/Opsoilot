"""HTTP client for Go Business API.

Agent must call Backend only through this client — never PostgreSQL.
Every business call uses the caller's JWT and X-Request-ID from request context.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.request_context import get_request_id, require_user_jwt

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://backend:8080"


class BackendAPIError(RuntimeError):
    """Raised when Go Business API returns a non-success envelope or HTTP error."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class BackendClient:
    """Thin Business Client for Go /api/v1 (JWT + X-Request-ID). Never PostgreSQL."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("BUSINESS_API_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def list_services(self) -> dict[str, Any]:
        """GET /api/v1/services"""
        return self._user_request("GET", "/api/v1/services")

    def get_service(self, service_id: str) -> dict[str, Any]:
        """GET /api/v1/services/:id"""
        return self._user_request("GET", f"/api/v1/services/{service_id}")

    def get_tickets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        q: str | None = None,
        service_id: str | None = None,
    ) -> dict[str, Any]:
        """GET /api/v1/tickets"""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if q:
            params["q"] = q
        if service_id:
            params["service_id"] = service_id
        return self._user_request("GET", "/api/v1/tickets", params=params)

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        """GET /api/v1/tickets/:id"""
        return self._user_request("GET", f"/api/v1/tickets/{ticket_id}")

    def create_ticket(
        self,
        title: str,
        description: str,
        service_id: str,
        priority: str = "medium",
        analysis: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/v1/tickets (service_id required)."""
        body: dict[str, Any] = {
            "title": title,
            "description": description,
            "priority": priority,
            "service_id": service_id,
        }
        if analysis:
            body["analysis"] = analysis
        return self._user_request("POST", "/api/v1/tickets", json=body)

    def update_ticket(
        self,
        ticket_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        assignee_id: str | None = None,
        analysis: str | None = None,
        resolution: str | None = None,
    ) -> dict[str, Any]:
        """PATCH /api/v1/tickets/:id"""
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if priority is not None:
            body["priority"] = priority
        if status is not None:
            body["status"] = status
        if assignee_id is not None:
            body["assignee_id"] = assignee_id
        if analysis is not None:
            body["analysis"] = analysis
        if resolution is not None:
            body["resolution"] = resolution
        return self._user_request("PATCH", f"/api/v1/tickets/{ticket_id}", json=body)

    def get_me(self) -> dict[str, Any]:
        """GET /api/v1/users/me"""
        return self._user_request("GET", "/api/v1/users/me")

    def get_permissions(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict[str, Any]:
        """GET /api/v1/permissions"""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        return self._user_request("GET", "/api/v1/permissions", params=params)

    def create_permission(
        self,
        resource_type: str,
        resource_name: str,
        permission_level: str,
        reason: str,
        service_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/v1/permissions"""
        body: dict[str, Any] = {
            "resource_type": resource_type,
            "resource_name": resource_name,
            "permission_level": permission_level,
            "reason": reason,
        }
        if service_id:
            body["service_id"] = service_id
        return self._user_request("POST", "/api/v1/permissions", json=body)

    def _user_request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        user_jwt = require_user_jwt()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["Authorization"] = f"Bearer {user_jwt}"
        request_id = get_request_id()
        if request_id:
            headers["X-Request-ID"] = request_id
        resp = self._client.request(method, path, headers=headers, **kwargs)
        return self._unwrap(resp)

    @staticmethod
    def _unwrap(resp: httpx.Response) -> dict[str, Any]:
        try:
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise BackendAPIError(
                f"invalid JSON from backend (HTTP {resp.status_code})",
                status_code=resp.status_code,
            ) from exc

        if resp.status_code >= 400:
            raise BackendAPIError(
                f"backend HTTP {resp.status_code}: {payload.get('message', resp.text)}",
                status_code=resp.status_code,
                payload=payload,
            )

        if not isinstance(payload, dict):
            raise BackendAPIError("backend response is not an object", payload=payload)

        code = payload.get("code")
        if code not in (0, None):
            raise BackendAPIError(
                f"backend business error {code}: {payload.get('message')}",
                status_code=resp.status_code,
                payload=payload,
            )

        data = payload.get("data")
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise BackendAPIError("backend data is not an object", payload=payload)
        return data


_client: BackendClient | None = None


def get_backend_client() -> BackendClient:
    """Process-wide BackendClient singleton (stateless w.r.t. user JWT)."""
    global _client
    if _client is None:
        _client = BackendClient()
    return _client
