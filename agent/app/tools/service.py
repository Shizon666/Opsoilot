"""Service catalog tools — wrap Go /services only (no DB access)."""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.clients.backend import BackendAPIError, get_backend_client


class ListServicesInput(BaseModel):
    """No parameters — returns ACTIVE services with simulated health."""


class GetServiceStatusInput(BaseModel):
    service_id: str = Field(..., min_length=1, description="服务 UUID")


@tool("list_services", args_schema=ListServicesInput)
def list_services() -> str:
    """列出当前可观测的业务服务及其健康状态（HEALTHY / DEGRADED / DOWN）。只读，自动执行。

    故障 Context Gathering：用于消歧并定位服务，再配合 get_service_status。
    结果写入「当前状态」；不要编造健康状态。INACTIVE 服务不会出现。
    列出服务不等于要建单；咨询类故障默认只分析。
    """
    client = get_backend_client()
    try:
        data = client.list_services()
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


@tool("get_service_status", args_schema=GetServiceStatusInput)
def get_service_status(
    service_id: Annotated[str, Field(description="服务 UUID")],
) -> str:
    """查询单个业务服务的详情与模拟健康状态。只读，自动执行。

    故障 Context Gathering 必查项之一；结果写入「当前状态」。
    不存在或已停用的服务由 Backend 返回错误；禁止用常识补健康值或声称已定位根因。
    查到 DEGRADED/DOWN 也不要自动 create_ticket，除非用户明确要求升级处理。
    """
    client = get_backend_client()
    try:
        data = client.get_service(service_id)
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


SERVICE_TOOLS = [list_services, get_service_status]
