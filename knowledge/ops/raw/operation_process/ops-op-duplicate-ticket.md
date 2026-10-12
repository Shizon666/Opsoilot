---
doc_id: OPS-OP-DUPLICATE-TICKET
title: 重复工单识别与关联处理
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: MEDIUM
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C5
basis:
  - code
  - contract
basis_notes: "仅能 search_tickets/get_ticket 见可见范围；隔离规则见 Backend；即使用户要求建单，契约允许在 analysis 注明已见在途单后仍 create_ticket（Prompt）；禁止编造不可见他人工单。"
related_docs:
  - OPS-OP-TICKET-LIFECYCLE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-REEVAL-AFTER-CLARIFY
  - OPS-SG-AGENT-TOOL-BOUNDARY
simulation_notice: true
---

# 重复工单识别与关联处理

本文依据 **工单检索 Tool 与可见性契约**，说明如何识别可能的重复/关联工单，以及与「用户仍要求新建」之间的处理方式。

## 1. 独立价值

生命周期文不谈查重；本篇专责 **search → 判断相似 → 建议关联或新建**。

## 2. 步骤

### A — 检索

`search_tickets`：关键词含服务现象（checkout/502、登录、积压等）+ 时间相关描述。

### B — 判断相似（建议，非自动合并）

相似线索：同一服务、相近现象、未关闭状态。  
**局限：** 不可见他人工单不得猜测；无自动「合并工单」API。

### C — 分支

| 情况 | 动作 |
|------|------|
| 发现用户可见的在途相似单 | 告知单号/摘要；问是否更新该单或仍要新建 |
| 用户明确要求新建 | 调查后仍可 `create_ticket`（HITL），analysis **注明**已见在途单 |
| 用户点名旧单 | `get_ticket` + `update_ticket`（HITL） |
| 无命中 | 如实说明；按影响面决定是否建议新建 |

## 3. 禁止

编造 `OPS-V1-*` 或他人工单内容；把知识复盘叙事号当重复工单。

## 4. 关联

见 `related_docs`。
