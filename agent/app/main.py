"""OpsPilot Agent Service (FastAPI + Tool Calling → Go Backend).

Business data: Go Business API only (never business PostgreSQL tables).
Phase 11.1: optional Checkpoint DB ``opspilot_agent`` for LangGraph state + thread ownership.
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.auth.jwt import JWTError, TokenClaims, verify_authorization
from app.db import checkpoint_backend, close_pool
from app.graph.agent import AgentError, AgentResult, resume_agent, run_agent
from app.graph.stream import format_sse, iter_agent_events
from app.memory import get_checkpointer
from app.request_context import user_context
from app.thread_store import ThreadOwnershipError, thread_ownership

logging.basicConfig(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Warm checkpointer (and Agent DB pool) on startup; close pool on shutdown."""
    backend = checkpoint_backend()
    logger.info("agent starting checkpointer_backend=%s", backend)
    try:
        get_checkpointer()
    except Exception:
        logger.exception("checkpointer init failed (backend=%s)", backend)
        raise
    yield
    if backend == "postgres":
        close_pool()


app = FastAPI(title="OpsPilot Agent", version="0.5.0", lifespan=lifespan)


class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ResumeRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    action: Literal["approve", "reject"]


class ChatData(BaseModel):
    thread_id: str
    message_id: str
    message: str
    pending: bool = False
    confirmation: dict | None = None
    metadata: dict | None = None


class Envelope(BaseModel):
    code: int = 0
    message: str = "success"
    data: ChatData | dict | None = None


def _resolve_request_id(incoming: str | None) -> str:
    """Use client X-Request-ID when present; otherwise generate one."""
    if incoming and incoming.strip():
        return incoming.strip()
    return f"req_{uuid.uuid4().hex}"


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Keep Agent errors in {code, message, data} shape when detail is a dict."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        content = exc.detail
    else:
        content = {"code": exc.status_code, "message": str(exc.detail), "data": None}
    headers: dict[str, str] = {}
    rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    if rid:
        headers["X-Request-ID"] = rid
    return JSONResponse(status_code=exc.status_code, content=content, headers=headers)


@app.get("/internal/health")
def internal_health() -> dict[str, str]:
    """Container / self probe only. Public /health is served by Go via Nginx."""
    return {
        "status": "ok",
        "service": "agent",
        "checkpointer": checkpoint_backend(),
    }


@app.post("/agent/chat", response_model=Envelope)
def agent_chat(
    body: ChatRequest,
    request: Request,
    response: Response,
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> Envelope:
    """Synchronous chat: JWT → DeepSeek Tool Calling → LangGraph → Go API."""
    request_id = _resolve_request_id(x_request_id)
    request.state.request_id = request_id
    response.headers["X-Request-ID"] = request_id

    try:
        claims = verify_authorization(authorization)
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": 40101, "message": str(exc), "data": None},
        ) from exc

    try:
        thread_ownership.bind_or_check(body.thread_id, claims.user_id)
    except ThreadOwnershipError as exc:
        raise HTTPException(
            status_code=403,
            detail={"code": 40301, "message": exc.message, "data": None},
        ) from exc

    with user_context(
        user_jwt=claims.raw_token,
        user_id=claims.user_id,
        role=claims.role,
        request_id=request_id,
    ):
        try:
            result = run_agent(body.message, thread_id=body.thread_id)
        except AgentError as exc:
            raise _agent_http(exc) from exc

    return _chat_envelope(body.thread_id, claims, request_id, result)


@app.post("/agent/chat/resume", response_model=Envelope)
def agent_chat_resume(
    body: ResumeRequest,
    request: Request,
    response: Response,
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> Envelope:
    """Resume WRITE HITL with Command(resume=...); never appends a HumanMessage."""
    request_id = _resolve_request_id(x_request_id)
    request.state.request_id = request_id
    response.headers["X-Request-ID"] = request_id

    try:
        claims = verify_authorization(authorization)
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": 40101, "message": str(exc), "data": None},
        ) from exc

    try:
        thread_ownership.bind_or_check(body.thread_id, claims.user_id)
    except ThreadOwnershipError as exc:
        raise HTTPException(
            status_code=403,
            detail={"code": 40301, "message": exc.message, "data": None},
        ) from exc

    with user_context(
        user_jwt=claims.raw_token,
        user_id=claims.user_id,
        role=claims.role,
        request_id=request_id,
    ):
        try:
            result = resume_agent(thread_id=body.thread_id, action=body.action)
        except AgentError as exc:
            raise _agent_http(exc) from exc

    return _chat_envelope(body.thread_id, claims, request_id, result)


def _agent_http(exc: AgentError) -> HTTPException:
    if exc.code in (40901, 40902):
        status = 409
    elif exc.code == 40001:
        status = 400
    else:
        status = 503
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message, "data": None},
    )


def _chat_envelope(thread_id: str, claims: TokenClaims, request_id: str, result: AgentResult) -> Envelope:
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    metadata = {
        "tools_called": result.tools_called,
        "mode": result.mode,
        "user_id": getattr(claims, "user_id", ""),
        "role": getattr(claims, "role", ""),
        "request_id": request_id,
        "checkpointer": checkpoint_backend(),
        "pending": result.pending,
    }
    if result.confirmation:
        metadata["confirmation"] = result.confirmation
    if result.tool_results:
        metadata["tool_results"] = result.tool_results
    return Envelope(
        data=ChatData(
            thread_id=thread_id,
            message_id=message_id,
            message=result.message,
            pending=result.pending,
            confirmation=result.confirmation,
            metadata=metadata,
        )
    )


def _unauthorized(exc: JWTError) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": 40101, "message": str(exc), "data": None},
    )


def _forbidden_thread(exc: ThreadOwnershipError) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": 40301, "message": exc.message, "data": None},
    )


@app.post("/agent/chat/stream")
def agent_chat_stream(
    body: ChatRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> StreamingResponse:
    """SSE chat: same graph / JWT / thread / tools as POST /agent/chat."""
    request_id = _resolve_request_id(x_request_id)
    request.state.request_id = request_id

    try:
        claims = verify_authorization(authorization)
    except JWTError as exc:
        raise _unauthorized(exc) from exc

    try:
        thread_ownership.bind_or_check(body.thread_id, claims.user_id)
    except ThreadOwnershipError as exc:
        raise _forbidden_thread(exc) from exc

    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    def event_bytes() -> Iterator[bytes]:
        for event in iter_agent_events(
            body.message,
            thread_id=body.thread_id,
            user_jwt=claims.raw_token,
            user_id=claims.user_id,
            role=claims.role,
            request_id=request_id,
            message_id=message_id,
        ):
            yield format_sse(event)

    return StreamingResponse(
        event_bytes(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_id,
        },
    )


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
