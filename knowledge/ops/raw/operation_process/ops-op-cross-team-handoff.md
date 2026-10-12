---
doc_id: OPS-OP-CROSS-TEAM-HANDOFF
title: 跨团队升级与信息交接
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
knowledge_role: C6
basis:
  - contract
  - simulated
basis_notes: "无即时通讯/寻呼 Tool；交接包字段为演示约定；不编造团队通讯录或审批人；对齐 OPS-RB-ESCALATE 与 OPS-OP-DUTY-HANDOFF。"
related_docs:
  - OPS-OP-DUTY-HANDOFF
  - OPS-RB-ESCALATE
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-OP-HIGH-RISK-PRECHECK
  - OPS-SG-PII-TICKET
  - OPS-OP-COMMS-TONE
simulation_notice: true
---

# 跨团队升级与信息交接

本文用于 OpsPilot **模拟运维环境**。当需要把故障从一线分析升级到平台/安全/业务方时，规范 **升级信息包** 应包含什么，避免空喊「转给某某组」。

## 1. 独立价值

班次交接见 `OPS-OP-DUTY-HANDOFF`；本篇面向**跨职责升级**（仍不指定真实寻呼链路）。

## 2. 建议升级信息包

1. 现象与业务影响（支付/登录/订单）  
2. 时间窗、是否仍在发生  
3. 已查 ACTIVE 服务快照  
4. 已尝试的知识路径（`doc_id`）与可见工单  
5. 证据缺口与需要对方确认的问题  
6. 是否涉及高风险操作（是/否；细节不给破坏性命令）  
7. 当前工单号（若有）  

禁止粘贴密钥与过度隐私（`OPS-SG-PII-TICKET`）。

## 3. 分支

### A — 建议升级但用户未建单

先按 `OPS-OP-IMPACT-ESCALATE` 询问是否建单；信息包可写入 analysis 草稿。

### B — 已有工单

更新 analysis 附加信息包要点；`update_ticket` 须 HITL。

### C — 对方信息未回

保持「等待跨团队反馈」；不编造已处理结论。

## 4. 禁止

编造值班电话、Slack 频道、审批人姓名；声称已通知某团队（无 Tool 证明时）。

## 5. 关联

见 `related_docs`。沟通口径可参考 `OPS-OP-COMMS-TONE`（docx 资产）。
