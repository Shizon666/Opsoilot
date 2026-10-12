"""Phase 13: map one Agent turn to public SSE events.

Uses the same compiled graph as sync /agent/chat (graph.invoke + Checkpointer).
Token/tool events are pushed from agent/tools nodes via a ContextVar sink
into a queue so the HTTP generator can yield before the turn finishes.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
from collections.abc import Iterator
from typing import Any

from app.db import checkpoint_backend
from app.graph.agent import (
    AgentError,
    AgentResult,
    bind_stream_sink,
    reset_stream_sink,
    run_agent,
)
from app.request_context import user_context

logger = logging.getLogger(__name__)

PUBLIC_EVENT_TYPES = frozenset(
    {"start", "token", "tool_start", "tool_end", "confirmation", "error", "done"}
)

_INTERNAL_RESULT = "_result"
_INTERNAL_ERROR = "_error"
_INTERNAL_STOP = "_stop"


def format_sse(event: dict[str, Any]) -> bytes:
    """Encode one public event as an SSE `data:` line."""
    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    return f"data: {payload}\n\n".encode("utf-8")


def _public_event(event: dict[str, Any]) -> dict[str, Any] | None:
    ev_type = event.get("type")
    if ev_type not in PUBLIC_EVENT_TYPES:
        return None
    if ev_type == "token":
        content = event.get("content")
        if not isinstance(content, str) or content == "":
            return None
        return {"type": "token", "content": content}
    if ev_type == "tool_start":
        return {
            "type": "tool_start",
            "tool": str(event.get("tool") or ""),
            "tool_call_id": str(event.get("tool_call_id") or ""),
        }
    if ev_type == "tool_end":
        ok = event.get("ok")
        return {
            "type": "tool_end",
            "tool": str(event.get("tool") or ""),
            "tool_call_id": str(event.get("tool_call_id") or ""),
            "ok": False if ok is False else True,
        }
    if ev_type == "confirmation":
        args = event.get("args")
        return {
            "type": "confirmation",
            "thread_id": str(event.get("thread_id") or ""),
            "tool": str(event.get("tool") or ""),
            "tool_call_id": str(event.get("tool_call_id") or ""),
            "args": args if isinstance(args, dict) else {},
        }
    return event


def _done_event(
    *,
    ok: bool,
    thread_id: str,
    message_id: str,
    request_id: str,
    user_id: str,
    role: str,
    result: AgentResult | None,
    error_message: str = "",
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "tools_called": list(result.tools_called) if result else [],
        "mode": result.mode if result else "llm",
        "user_id": user_id,
        "role": role,
        "request_id": request_id,
        "checkpointer": checkpoint_backend(),
    }
    if result and result.tool_results:
        metadata["tool_results"] = result.tool_results
    pending = bool(result and result.pending)
    if pending:
        metadata["pending"] = True
        if result and result.confirmation:
            metadata["confirmation"] = result.confirmation
    event = {
        "type": "done",
        "ok": ok,
        "thread_id": thread_id,
        "message_id": message_id,
        "message": (result.message if result else "") or error_message,
        "metadata": metadata,
    }
    if pending:
        event["pending"] = True
        if result and result.confirmation:
            event["confirmation"] = result.confirmation
    return event


def iter_agent_events(
    user_message: str,
    *,
    thread_id: str,
    user_jwt: str,
    user_id: str,
    role: str,
    request_id: str,
    message_id: str,
) -> Iterator[dict[str, Any]]:
    """Yield public events for one streaming turn (same graph as run_agent)."""
    q: queue.Queue[dict[str, Any]] = queue.Queue()

    def sink(event: dict[str, Any]) -> None:
        public = _public_event(event)
        if public is not None:
            q.put(public)

    def worker() -> None:
        token = None
        try:
            with user_context(
                user_jwt=user_jwt,
                user_id=user_id,
                role=role,
                request_id=request_id,
            ):
                token = bind_stream_sink(sink)
                result = run_agent(user_message, thread_id=thread_id)
                q.put({"type": _INTERNAL_RESULT, "result": result})
        except BaseException as exc:  # noqa: BLE001
            logger.exception("stream worker failed: %s", exc)
            q.put({"type": _INTERNAL_ERROR, "exc": exc})
        finally:
            if token is not None:
                reset_stream_sink(token)
            q.put({"type": _INTERNAL_STOP})

    yield {
        "type": "start",
        "thread_id": thread_id,
        "message_id": message_id,
        "request_id": request_id,
    }

    thread = threading.Thread(target=worker, name="opspilot-agent-stream", daemon=True)
    thread.start()

    result: AgentResult | None = None
    err: BaseException | None = None
    try:
        while True:
            try:
                item = q.get(timeout=0.5)
            except queue.Empty:
                if not thread.is_alive():
                    break
                continue
            kind = item.get("type")
            if kind == _INTERNAL_STOP:
                break
            if kind == _INTERNAL_RESULT:
                result = item.get("result")
                continue
            if kind == _INTERNAL_ERROR:
                err = item.get("exc")
                continue
            yield item
    finally:
        thread.join(timeout=120)

    if err is not None:
        if isinstance(err, AgentError):
            yield {"type": "error", "code": err.code, "message": err.message}
        else:
            yield {
                "type": "error",
                "code": 50302,
                "message": f"LLM call failed: {err}",
            }
        yield _done_event(
            ok=False,
            thread_id=thread_id,
            message_id=message_id,
            request_id=request_id,
            user_id=user_id,
            role=role,
            result=result,
        )
        return

    yield _done_event(
        ok=True,
        thread_id=thread_id,
        message_id=message_id,
        request_id=request_id,
        user_id=user_id,
        role=role,
        result=result,
    )
