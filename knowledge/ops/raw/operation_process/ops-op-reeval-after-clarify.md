---
doc_id: OPS-OP-REEVAL-AFTER-CLARIFY
title: 用户补充信息后的重新评估
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: INFO
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C6
basis:
  - contract
basis_notes: "多轮 thread 与重新调查对齐 Agent Prompt；同一 thread_id 下补充信息后应重跑关键只读 Tool，不得沿用过时结论。"
related_docs:
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-OP-DIAGNOSIS-STOP
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-DUPLICATE-TICKET
  - OPS-OP-MULTI-SERVICE-TRIAGE
  - OPS-SM-SERVICE-CATALOG
simulation_notice: true
---

# 用户补充信息后的重新评估

本文用于指导 Agent：用户补充时间窗、影响面、是否 5xx、是否已恢复等之后，**必须重新评估**服务选择、Runbook 路径与升级建议，而不是坚持首轮猜测。

## 1. 独立价值

证据台账记录缺口；本篇规定 **缺口被填上之后怎么走**。

## 2. 触发

用户在同一对话中补充关键事实，或纠正先前描述。

## 3. 强制重评清单

1. 服务绑定是否仍正确（必要时重 `list_services` / `get_service_status`）  
2. Runbook 路径是否切换（如 5xx ↔ 通道超时 ↔ Worker）  
3. 影响面与升级建议是否变化（`OPS-OP-IMPACT-ESCALATE`）  
4. 是否出现新的重复工单线索（可再 `search_tickets`）  
5. 先前「待验证恢复」是否被用户确认/推翻（`OPS-OP-RECOVERY-VERIFY`）

## 4. 分支

### A — 路径切换

明确告知「根据新信息调整判断」；引用新 `doc_id`；废弃旧根因表述。

### B — 信息仍不足

回到澄清或 `OPS-OP-DIAGNOSIS-STOP`。

### C — 用户确认已恢复

按恢复验证文处理；勿自动关单（Employee 不能改 status）。

## 5. 禁止

无视补充信息；用过时健康快照当现状（应重查）。

## 6. 关联

见 `related_docs`。
