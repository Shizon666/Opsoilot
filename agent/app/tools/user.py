"""User tools — wrap Go /users/me only (no DB access)."""

from __future__ import annotations

import json

from langchain_core.tools import tool
from pydantic import BaseModel

from app.clients.backend import BackendAPIError, get_backend_client


class GetCurrentUserInput(BaseModel):
    """No parameters — identity comes from the caller's JWT."""


@tool("get_current_user", args_schema=GetCurrentUserInput)
def get_current_user() -> str:
    """查询当前登录用户的真实身份与员工上下文。只读，自动执行。

    返回字段包括：姓名、部门(department)、岗位(position)、职级(employee_level)、系统角色(role)等。

    用途：
    - 「我是谁 / 我的部门 / 我的岗位」等自我信息
    - 故障分析时可引用报障人上下文作说明

    明确不是：
    - 员工上下文不是授权依据，也不能代替服务状态/知识/历史调查
    - 禁止传入 user_id；身份由调用方 JWT 决定
    - 不要用 search_knowledge 代替本工具；本工具不会创建工单
    """
    client = get_backend_client()
    try:
        data = client.get_me()
    except BackendAPIError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


USER_TOOLS = [get_current_user]
