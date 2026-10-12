"""Permission (access request) tools — wrap Go /permissions only."""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.clients.backend import BackendAPIError, get_backend_client


class GetMyPermissionsInput(BaseModel):
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
    status: str | None = Field(
        default=None,
        description="可选状态过滤（如 pending / approved / rejected，以 Go 为准）",
    )


class CreatePermissionInput(BaseModel):
    resource_type: str = Field(
        ...,
        description="资源类型：GITLAB | DATABASE | DEV_ENV",
    )
    resource_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="资源名称，例如项目名 OpsPilot",
    )
    permission_level: str = Field(
        ...,
        description="权限级别：READ | DEVELOPER | ADMIN",
    )
    reason: str = Field(..., min_length=1, description="申请原因")
    service_id: str | None = Field(
        default=None,
        description="可选服务 ID；省略则由 Go 使用默认服务",
    )


@tool("get_my_permissions", args_schema=GetMyPermissionsInput)
def get_my_permissions(
    page: Annotated[int, Field(description="页码")] = 1,
    page_size: Annotated[int, Field(description="每页条数")] = 20,
    status: Annotated[str | None, Field(description="状态过滤")] = None,
) -> str:
    """查询当前用户的真实权限申请列表（资源类型、资源名、级别、状态等）。

    用于「我的权限申请有哪些」等查询意图。不要用 search_knowledge 编造或代替真实列表。
    """
    client = get_backend_client()
    try:
        data = client.get_permissions(page=page, page_size=page_size, status=status)
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


@tool("create_permission", args_schema=CreatePermissionInput)
def create_permission(
    resource_type: Annotated[str, Field(description="资源类型")],
    resource_name: Annotated[str, Field(description="资源名称")],
    permission_level: Annotated[str, Field(description="权限级别")],
    reason: Annotated[str, Field(description="申请原因")],
    service_id: Annotated[str | None, Field(description="可选服务 ID")] = None,
) -> str:
    """创建权限申请单据。

    仅在用户明确申请（或知识片段明确指引申请）且参数齐全时调用。
    resource_type 仅 GITLAB/DATABASE/DEV_ENV；permission_level 仅 READ/DEVELOPER/ADMIN。
    缺参先追问；禁止编造审批结果或 permission_id。
    """
    client = get_backend_client()
    try:
        data = client.create_permission(
            resource_type=resource_type,
            resource_name=resource_name,
            permission_level=permission_level,
            reason=reason,
            service_id=service_id,
        )
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


PERMISSION_TOOLS = [get_my_permissions, create_permission]
