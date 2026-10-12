"""Minimal LangGraph AgentState for Phase 8 ReAct loop."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Conversation messages only; user JWT lives in request_context."""

    messages: Annotated[list, add_messages]
