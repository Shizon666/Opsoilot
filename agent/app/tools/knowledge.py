"""search_knowledge — Phase 10 minimal RAG Tool (local top-k snippets)."""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.rag.retriever import retrieve

_TOOL_DOC = """运维知识库查询（只读，自动执行）。故障排查 / Runbook 的唯一知识来源。

用途：在故障 Context Gathering 中检索运维知识片段，供「知识依据」板块引用。
返回 hits（doc_id、title、path、section、snippet、score、confidence_level）；回答依据是 snippet，不是 confidence_level。

confidence_level 仅辅助判断匹配强弱，不得作为事实可信度：
- high / medium：提示匹配强弱；内容对错仍看 snippet
- low / 无命中：明确未知，禁止用常识猜公司内部规则或编造根因

何时用：
- 故障咨询的三类调查之一（与 get_service_status、search_tickets 一起用）
- 排查步骤 / Runbook / 怎么办 → 先本工具再组织分析回复
- 查「我的工单/身份」→ 用 get_current_user / search_tickets / get_ticket，不要用本工具代替

明确不是：
- 不代表已经授权、已定位根因或必须创建工单
- 本工具只读；创建/更新工单是 escalation，仅用户明确要求升级且已有分析后才用 create_ticket / update_ticket（HITL）

无有效命中（reliable=false 或 confidence_level=low）时：告知知识库暂无直接命中 / 无法确认，可询问是否升级，禁止编造，禁止因此强制建单。
"""


class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="员工问题或检索关键词")
    top_k: int = Field(default=3, ge=1, le=5, description="返回片段条数，默认 3，最大 5")


@tool("search_knowledge", args_schema=SearchKnowledgeInput, description=_TOOL_DOC)
def search_knowledge(
    query: Annotated[str, Field(description="检索查询")],
    top_k: Annotated[int, Field(description="top-k")] = 3,
) -> str:
    hits = retrieve(query, top_k=top_k)
    reliable = len(hits) > 0
    if not hits:
        overall_confidence = "low"
    elif any(h.get("confidence_level") == "high" for h in hits):
        overall_confidence = "high"
    else:
        overall_confidence = "medium"
    payload = {
        "ok": True,
        "data": {
            "query": query,
            "hit_count": len(hits),
            "reliable": reliable,
            "confidence_level": overall_confidence,
            "hits": hits,
            "note": (
                "回答依据 snippet；confidence_level 仅辅助匹配强弱、非事实可信度；不代表已授权/审批；不替代 get_*。"
                if reliable
                else "无足够相关知识片段（confidence_level=low）；勿用常识编造公司规则；可引导创建工单或联系 Support。"
            ),
        },
    }
    return json.dumps(payload, ensure_ascii=False)


KNOWLEDGE_TOOLS = [search_knowledge]
