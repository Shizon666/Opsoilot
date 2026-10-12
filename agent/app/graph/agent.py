"""Phase 8/10/11 Single Agent: DeepSeek + LangGraph ReAct + Checkpointer.

Business Tools (Phase 8) + search_knowledge (Phase 10 local RAG).
Phase 11/11.1: thread_id → Checkpointer (MemorySaver or PostgresSaver).
No mock planner. Missing LLM key → clear error, no business Tools.
"""

from __future__ import annotations

import json
import logging
import os
import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphInterrupt
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.graph.state import AgentState
from app.memory import get_checkpointer, reset_checkpointer_for_tests
from app.prompts import SYSTEM_PROMPT
from app.tools import AGENT_TOOLS

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4
WRITE_TOOLS = frozenset({"create_ticket", "update_ticket"})
PENDING_USER_MESSAGE = "需要你确认后才会提交。确认前不会创建或更新工单。"

# Streaming sink: bound by iter_agent_events for SSE. Sync invoke leaves this None.
StreamSink = Callable[[dict[str, Any]], None]
_event_sink: ContextVar[StreamSink | None] = ContextVar("opspilot_stream_sink", default=None)


class AgentError(Exception):
    """Raised when the Agent cannot run (config / LLM). Business Tools are not called."""

    def __init__(self, message: str, *, code: int = 50301) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class AgentResult:
    message: str
    tools_called: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "llm"
    pending: bool = False
    confirmation: dict[str, Any] | None = None


def _llm_api_key() -> str | None:
    key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    return key or None


def run_agent(user_message: str, *, thread_id: str) -> AgentResult:
    """Run one DeepSeek + LangGraph ReAct turn under thread_id Checkpointer.

    Raises AgentError on config/LLM failure.
    """
    message = (user_message or "").strip()
    if not message:
        raise AgentError("message is empty", code=40001)

    tid = (thread_id or "").strip()
    if not tid:
        raise AgentError("thread_id is empty", code=40001)

    if not _llm_api_key():
        raise AgentError(
            "LLM_API_KEY is not configured; Agent requires DeepSeek to run",
            code=50301,
        )

    try:
        return _run_langgraph_agent(message, thread_id=tid)
    except AgentError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("DeepSeek / LangGraph agent failed: %s", exc)
        raise AgentError(
            f"LLM call failed: {exc}",
            code=50302,
        ) from exc


def resume_agent(*, thread_id: str, action: str) -> AgentResult:
    """Resume a HITL interrupt with Command(resume=...). Never appends a HumanMessage."""
    tid = (thread_id or "").strip()
    if not tid:
        raise AgentError("thread_id is empty", code=40001)

    decision = (action or "").strip().lower()
    if decision not in {"approve", "reject"}:
        raise AgentError("action must be approve or reject", code=40001)

    if not _llm_api_key():
        raise AgentError(
            "LLM_API_KEY is not configured; Agent requires DeepSeek to run",
            code=50301,
        )

    try:
        return _resume_langgraph_agent(thread_id=tid, action=decision)
    except AgentError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("DeepSeek / LangGraph resume failed: %s", exc)
        raise AgentError(
            f"LLM call failed: {exc}",
            code=50302,
        ) from exc


# ---------------------------------------------------------------------------
# LangGraph ReAct
# ---------------------------------------------------------------------------

_compiled_graph = None


def _build_llm():
    from langchain_openai import ChatOpenAI

    api_key = _llm_api_key()
    if not api_key:
        raise AgentError(
            "LLM_API_KEY is not configured; Agent requires DeepSeek to run",
            code=50301,
        )
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com"
    model = os.getenv("LLM_MODEL", "deepseek-flash")
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        streaming=True,
    ).bind_tools(AGENT_TOOLS)


def emit_stream_event(event: dict[str, Any]) -> None:
    """Push a public stream event when a sink is bound (SSE). No-op on sync invoke."""
    sink = _event_sink.get()
    if sink is None:
        return
    sink(event)


def bind_stream_sink(sink: StreamSink | None):
    """Bind/reset the per-run event sink. Returns a token for ContextVar.reset."""
    return _event_sink.set(sink)


def reset_stream_sink(token: Any) -> None:
    _event_sink.reset(token)


def _get_graph():
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    llm = _build_llm()
    tools_by_name = {t.name: t for t in AGENT_TOOLS}

    def agent_node(state: AgentState) -> dict[str, list[BaseMessage]]:
        msgs = list(state["messages"])
        if not msgs or not isinstance(msgs[0], SystemMessage):
            msgs = [SystemMessage(content=SYSTEM_PROMPT), *msgs]
        # Always llm.stream so SSE can emit real token deltas; graph.invoke
        # still waits for the assembled AIMessage (sync /agent/chat unchanged).
        assembled: Any = None
        for chunk in llm.stream(msgs):
            text = chunk_text(chunk)
            if text:
                emit_stream_event({"type": "token", "content": text})
            assembled = chunk if assembled is None else assembled + chunk
        if assembled is None:
            assembled = AIMessage(content="")
        return {"messages": [assembled]}

    def tools_node(
        state: AgentState,
        config: RunnableConfig,
    ) -> dict[str, list[BaseMessage]]:
        """Run tool_calls. WRITE tools interrupt before tool.invoke()."""
        msgs = list(state["messages"] or [])
        last = msgs[-1] if msgs else None
        if not isinstance(last, AIMessage) or not last.tool_calls:
            return {"messages": []}

        parsed: list[tuple[str, str, dict[str, Any]]] = []
        seen: set[str] = set()
        for call in last.tool_calls:
            name, call_id, args = _parse_tool_call(call)
            if call_id and call_id in seen:
                continue
            if call_id:
                seen.add(call_id)
            parsed.append((name, call_id, args))

        writes = [item for item in parsed if item[0] in WRITE_TOOLS]
        reads = [item for item in parsed if item[0] not in WRITE_TOOLS]
        outputs: list[BaseMessage] = []

        if len(writes) > 1:
            for name, call_id, args in reads:
                outputs.append(
                    _run_tool_call(tools_by_name, name=name, call_id=call_id, args=args)
                )
            for name, call_id, _args in writes:
                outputs.append(
                    _cancelled_tool_message(
                        name=name,
                        call_id=call_id,
                        error="multiple WRITE tools in one round are not allowed",
                    )
                )
            return {"messages": outputs}

        for name, call_id, args in reads:
            outputs.append(
                _run_tool_call(tools_by_name, name=name, call_id=call_id, args=args)
            )

        if writes:
            name, call_id, args = writes[0]
            thread_id = ""
            if config:
                thread_id = str((config.get("configurable") or {}).get("thread_id") or "")
            payload = {
                "thread_id": thread_id,
                "tool": name,
                "tool_call_id": call_id,
                "args": _public_tool_args(args),
            }
            emit_stream_event({"type": "confirmation", **payload})
            decision = interrupt(payload)
            if _is_approve(decision):
                outputs.append(
                    _run_tool_call(
                        tools_by_name,
                        name=name,
                        call_id=call_id,
                        args=args,
                    )
                )
            else:
                outputs.append(
                    _cancelled_tool_message(
                        name=name,
                        call_id=call_id,
                        error="user rejected the write",
                    )
                )
        return {"messages": outputs}

    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        msgs = state["messages"]
        last = msgs[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            # Count tool rounds in the *current* user turn only (after last HumanMessage).
            last_human_idx = 0
            for i, m in enumerate(msgs):
                if isinstance(m, HumanMessage):
                    last_human_idx = i
            turn_msgs = msgs[last_human_idx:]
            tool_rounds = sum(
                1
                for m in turn_msgs
                if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)
            )
            if tool_rounds > MAX_TOOL_ROUNDS:
                return "__end__"
            return "tools"
        return "__end__"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "__end__": END},
    )
    graph.add_edge("tools", "agent")
    _compiled_graph = graph.compile(checkpointer=get_checkpointer())
    return _compiled_graph


def reset_graph_for_tests() -> None:
    """Clear compiled graph + checkpointer singletons (tests / eval only)."""
    global _compiled_graph
    _compiled_graph = None
    reset_checkpointer_for_tests()


def _invoke_config(thread_id: str) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_TOOL_ROUNDS * 2 + 2,
    }


def get_hitl_confirmation(thread_id: str) -> dict[str, Any] | None:
    """Return public confirmation payload if this thread is paused on WRITE HITL."""
    tid = (thread_id or "").strip()
    if not tid:
        return None
    graph = _get_graph()
    try:
        snapshot = graph.get_state(_invoke_config(tid))
    except Exception:  # noqa: BLE001
        return None
    interrupts = list(getattr(snapshot, "interrupts", None) or ())
    if not interrupts:
        for task in getattr(snapshot, "tasks", None) or ():
            interrupts.extend(list(getattr(task, "interrupts", None) or ()))
    if not interrupts:
        return None
    value = getattr(interrupts[0], "value", None)
    if isinstance(value, dict):
        tool = str(value.get("tool") or "")
        if tool not in WRITE_TOOLS:
            return None
        return {
            "thread_id": str(value.get("thread_id") or tid),
            "tool": tool,
            "tool_call_id": str(value.get("tool_call_id") or ""),
            "args": value.get("args") if isinstance(value.get("args"), dict) else {},
        }
    return None


def _run_langgraph_agent(message: str, *, thread_id: str) -> AgentResult:
    graph = _get_graph()
    config = _invoke_config(thread_id)
    if get_hitl_confirmation(thread_id):
        raise AgentError(
            "thread has a pending confirmation; resume or reject it before sending a new message",
            code=40901,
        )

    final_state = _invoke_graph(
        graph,
        {"messages": [HumanMessage(content=message)]},
        config,
    )
    pending = _confirmation_from_invoke(final_state, thread_id) or get_hitl_confirmation(
        thread_id
    )
    if pending:
        return AgentResult(
            message=PENDING_USER_MESSAGE,
            tools_called=[pending["tool"]] if pending.get("tool") else [],
            mode="llm",
            pending=True,
            confirmation=pending,
        )

    messages: list[BaseMessage] = _messages_from_state(final_state)
    turn_messages = _messages_since_last_human(messages)
    tools_called, tool_results = _extract_tool_trace(turn_messages)
    reply = _last_ai_text(turn_messages) or _last_ai_text(messages) or "已完成。"
    return AgentResult(
        message=reply,
        tools_called=tools_called,
        tool_results=tool_results,
        mode="llm",
    )


def _resume_langgraph_agent(*, thread_id: str, action: str) -> AgentResult:
    graph = _get_graph()
    config = _invoke_config(thread_id)
    if not get_hitl_confirmation(thread_id):
        raise AgentError(
            "thread has no pending confirmation",
            code=40902,
        )

    final_state = _invoke_graph(graph, Command(resume=action), config)
    if get_hitl_confirmation(thread_id) or _confirmation_from_invoke(final_state, thread_id):
        raise AgentError("resume did not clear pending confirmation", code=50302)

    messages: list[BaseMessage] = _messages_from_state(final_state)
    if not messages:
        snapshot = graph.get_state(config)
        messages = list((snapshot.values or {}).get("messages") or [])
    turn_messages = _messages_since_last_human(messages)
    tools_called, tool_results = _extract_tool_trace(turn_messages)
    reply = _last_ai_text(turn_messages) or _last_ai_text(messages) or "已完成。"
    return AgentResult(
        message=reply,
        tools_called=tools_called,
        tool_results=tool_results,
        mode="llm",
    )


def _invoke_graph(graph: Any, payload: Any, config: dict[str, Any]) -> Any:
    try:
        return graph.invoke(payload, config=config)
    except GraphInterrupt as exc:
        interrupts = exc.args[0] if exc.args else ()
        return {"__interrupt__": interrupts}


def _message_count(graph: Any, config: dict[str, Any]) -> int:
    try:
        snapshot = graph.get_state(config)
        if snapshot and snapshot.values:
            return len(snapshot.values.get("messages") or [])
    except Exception:  # noqa: BLE001
        return 0
    return 0


def _messages_from_state(final_state: Any) -> list[BaseMessage]:
    if isinstance(final_state, dict):
        return list(final_state.get("messages") or [])
    return []


def _messages_since_last_human(messages: list[BaseMessage]) -> list[BaseMessage]:
    last_human = 0
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            last_human = i
    return messages[last_human:] if messages else []


def _confirmation_from_invoke(final_state: Any, thread_id: str) -> dict[str, Any] | None:
    if not isinstance(final_state, dict):
        return None
    raw = final_state.get("__interrupt__") or []
    if not raw:
        return None
    first = raw[0]
    value = getattr(first, "value", None)
    if isinstance(first, dict):
        value = first.get("value")
    if isinstance(value, dict):
        return {
            "thread_id": str(value.get("thread_id") or thread_id),
            "tool": str(value.get("tool") or ""),
            "tool_call_id": str(value.get("tool_call_id") or ""),
            "args": value.get("args") if isinstance(value.get("args"), dict) else {},
        }
    return None


def _extract_tool_trace(messages: list[BaseMessage]) -> tuple[list[str], list[dict[str, Any]]]:
    tools_called: list[str] = []
    tool_results: list[dict[str, Any]] = []
    pending_args: dict[str, dict[str, Any]] = {}

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for call in msg.tool_calls:
                name, call_id, args = _parse_tool_call(call)
                if name:
                    tools_called.append(name)
                if call_id:
                    pending_args[call_id] = {"tool": name, "args": args}
        elif isinstance(msg, ToolMessage):
            entry = pending_args.pop(msg.tool_call_id, {"tool": "unknown", "args": {}})
            entry["result"] = _safe_json(str(msg.content))
            tool_results.append(entry)
    return tools_called, tool_results


def _last_ai_text(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            return _message_text(msg)
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return _message_text(msg)
    return ""


def chunk_text(chunk: Any) -> str:
    """User-visible text delta from an LLM stream chunk (not reasoning / tool JSON)."""
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "".join(parts)
    return ""


def tool_message_ok(msg: ToolMessage) -> bool:
    payload = _safe_json(str(msg.content))
    if payload.get("ok") is False:
        return False
    return True


def _parse_tool_call(call: Any) -> tuple[str, str, dict[str, Any]]:
    if isinstance(call, dict):
        name = str(call.get("name") or "")
        call_id = str(call.get("id") or "")
        raw_args = call.get("args") or {}
    else:
        name = str(getattr(call, "name", None) or "")
        call_id = str(getattr(call, "id", None) or "")
        raw_args = getattr(call, "args", None) or {}
    args = raw_args if isinstance(raw_args, dict) else {}
    return name, call_id, args


def _is_approve(decision: Any) -> bool:
    if decision == "approve":
        return True
    if isinstance(decision, str) and decision.strip().lower() == "approve":
        return True
    if isinstance(decision, dict) and str(decision.get("action") or "").strip().lower() == "approve":
        return True
    return False


def _public_tool_args(args: dict[str, Any]) -> dict[str, Any]:
    blocked = {"authorization", "token", "jwt", "password", "secret", "api_key"}
    safe: dict[str, Any] = {}
    for key, value in (args or {}).items():
        if str(key).lower() in blocked:
            continue
        try:
            json.dumps(value)
        except TypeError:
            safe[str(key)] = str(value)
            continue
        safe[str(key)] = value
    return safe


def _run_tool_call(
    tools_by_name: dict[str, Any],
    *,
    name: str,
    call_id: str,
    args: dict[str, Any],
) -> ToolMessage:
    emit_stream_event({"type": "tool_start", "tool": name, "tool_call_id": call_id})
    tool_msg = _execute_tool(tools_by_name, name=name, call_id=call_id, args=args)
    emit_stream_event(
        {
            "type": "tool_end",
            "tool": tool_msg.name or name or "unknown",
            "tool_call_id": tool_msg.tool_call_id or call_id,
            "ok": tool_message_ok(tool_msg),
        }
    )
    return tool_msg


def _cancelled_tool_message(*, name: str, call_id: str, error: str) -> ToolMessage:
    content = json.dumps(
        {"ok": False, "cancelled": True, "error": error},
        ensure_ascii=False,
    )
    msg = ToolMessage(content=content, tool_call_id=call_id, name=name or "unknown")
    emit_stream_event(
        {
            "type": "tool_end",
            "tool": name or "unknown",
            "tool_call_id": call_id,
            "ok": False,
        }
    )
    return msg


def _execute_tool(
    tools_by_name: dict[str, Any],
    *,
    name: str,
    call_id: str,
    args: dict[str, Any],
) -> ToolMessage:
    tool = tools_by_name.get(name)
    if tool is None:
        payload = json.dumps(
            {"ok": False, "error": f"unknown tool: {name}"},
            ensure_ascii=False,
        )
        return ToolMessage(content=payload, tool_call_id=call_id, name=name or "unknown")
    try:
        raw = tool.invoke(args)
        content = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("tool %s failed: %s", name, exc)
        content = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return ToolMessage(content=content, tool_call_id=call_id, name=name)


def _message_text(msg: Any) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts).strip()
    return str(content).strip()


def _safe_json(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"raw": value}
    except json.JSONDecodeError:
        return {"raw": raw}


def extract_vpn_title(message: str) -> str:
    """Helper kept for tests / future prompt tuning."""
    if re.search(r"vpn", message, re.I):
        return "VPN 故障"
    return "IT 故障工单"
