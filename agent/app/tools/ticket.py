"""Ticket tools — wrap Go /tickets only (no DB access)."""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.clients.backend import BackendAPIError, get_backend_client


class SearchTicketsInput(BaseModel):
    q: str | None = Field(default=None, max_length=100, description="标题/描述模糊检索")
    status: str | None = Field(default=None, description="状态过滤，如 open / in_progress")
    service_id: str | None = Field(default=None, description="按服务 UUID 过滤")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class GetTicketInput(BaseModel):
    ticket_id: str = Field(..., min_length=1, description="工单 UUID")


class CreateTicketInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="工单标题")
    description: str = Field(..., min_length=1, description="问题描述")
    service_id: str = Field(..., min_length=1, description="所属业务服务 UUID（必填）")
    priority: str = Field(default="medium", description="优先级：low / medium / high / urgent")
    analysis: str | None = Field(default=None, description="可选故障分析摘要")


class UpdateTicketInput(BaseModel):
    ticket_id: str = Field(..., min_length=1, description="工单 UUID")
    title: str | None = Field(default=None, description="标题")
    description: str | None = Field(default=None, description="描述")
    priority: str | None = Field(default=None, description="优先级")
    status: str | None = Field(default=None, description="状态，如 in_progress / resolved / closed")
    assignee_id: str | None = Field(default=None, description="负责人用户 UUID")
    analysis: str | None = Field(default=None, description="故障分析摘要")
    resolution: str | None = Field(default=None, description="处理结论（Support）")


@tool("search_tickets", args_schema=SearchTicketsInput)
def search_tickets(
    q: Annotated[str | None, Field(description="模糊检索")] = None,
    status: Annotated[str | None, Field(description="状态过滤")] = None,
    service_id: Annotated[str | None, Field(description="服务 UUID")] = None,
    page: Annotated[int, Field(description="页码")] = 1,
    page_size: Annotated[int, Field(description="每页条数")] = 20,
) -> str:
    """检索真实历史工单（标题/描述模糊匹配，可按服务过滤）。只读，自动执行。

    故障 Context Gathering 必查项之一；结果写入「历史参考」。
    Employee 只能看到自己的单；IT_SUPPORT 可看到全部。不要用知识库编造工单列表。
    检索历史不等于创建工单；无匹配时写「未见同类可见历史工单」。
    """
    client = get_backend_client()
    try:
        data = client.get_tickets(
            page=page,
            page_size=page_size,
            status=status,
            q=q,
            service_id=service_id,
        )
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


@tool("get_ticket", args_schema=GetTicketInput)
def get_ticket(
    ticket_id: Annotated[str, Field(description="工单 UUID")],
) -> str:
    """按 ID 查询一张真实工单详情（含 analysis）。只读，自动执行。

    用户点名某张单或需要细节时再用；无权或不存在由 Backend 判定。
    """
    client = get_backend_client()
    try:
        data = client.get_ticket(ticket_id)
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


@tool("create_ticket", args_schema=CreateTicketInput)
def create_ticket(
    title: Annotated[str, Field(description="工单标题")],
    description: Annotated[str, Field(description="问题描述")],
    service_id: Annotated[str, Field(description="服务 UUID")],
    priority: Annotated[str, Field(description="优先级")] = "medium",
    analysis: Annotated[str | None, Field(description="可选分析")] = None,
) -> str:
    """升级处理：创建故障工单。写操作，必须 HITL 用户确认后才会真正提交。

    用户明确说「提交/创建工单/帮我建单/升级」时：完成调查与分析后必须调用本工具进入 HITL。
    即使已有同类在途工单，只要用户要求新建/提交工单，仍应调用本工具（勿只口头追问）。
    禁止：普通故障咨询自动调用；禁止没有分析就建单。
    调用前须已完成服务状态/知识/历史调查；analysis 应填写分析摘要。
    service_id 必填且为 ACTIVE 服务 UUID。缺参先追问；禁止编造 ticket_no。
    """
    client = get_backend_client()
    try:
        data = client.create_ticket(
            title=title,
            description=description,
            service_id=service_id,
            priority=priority,
            analysis=analysis,
        )
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


@tool("update_ticket", args_schema=UpdateTicketInput)
def update_ticket(
    ticket_id: Annotated[str, Field(description="工单 UUID")],
    title: Annotated[str | None, Field(description="标题")] = None,
    description: Annotated[str | None, Field(description="描述")] = None,
    priority: Annotated[str | None, Field(description="优先级")] = None,
    status: Annotated[str | None, Field(description="状态")] = None,
    assignee_id: Annotated[str | None, Field(description="负责人")] = None,
    analysis: Annotated[str | None, Field(description="分析")] = None,
    resolution: Annotated[str | None, Field(description="处理结论")] = None,
) -> str:
    """升级/闭环：更新已有工单（状态、analysis 等）。写操作，必须 HITL 确认。

    仅在已有工单语境且用户意图为更新时使用；不得用本工具代替故障分析。
    合法迁移由 Backend 状态机裁决。Employee 不能改 status。禁止编造状态结果。
    """
    client = get_backend_client()
    try:
        data = client.update_ticket(
            ticket_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            assignee_id=assignee_id,
            analysis=analysis,
            resolution=resolution,
        )
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


TICKET_TOOLS = [search_tickets, get_ticket, create_ticket, update_ticket]
