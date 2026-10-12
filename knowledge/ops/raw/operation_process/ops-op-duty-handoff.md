---
doc_id: OPS-OP-DUTY-HANDOFF
title: 故障值班交接与未完成事项记录
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
basis_notes: "交接字段为演示约定；无值班排班系统 Tool；敏感信息禁贴见 OPS-SG-PII-TICKET；升级喊人见 OPS-RB-ESCALATE。"
related_docs:
  - OPS-RB-ESCALATE
  - OPS-OP-CROSS-TEAM-HANDOFF
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-OP-TICKET-ANALYSIS
  - OPS-OP-IMPACT-ESCALATE
  - OPS-SG-PII-TICKET
simulation_notice: true
---

# 故障值班交接与未完成事项记录

本文用于 OpsPilot **模拟运维环境**。规范故障未结束时的**班次交接**应留下什么信息，便于下一班与 Agent 续查。

## 1. 独立价值

`OPS-RB-ESCALATE` 只回答「要不要喊人」；本篇回答「交接条写什么、未完成项如何列」。

## 2. 建议交接最小集（演示约定）

1. 时间窗与当前是否仍发生  
2. 影响面（个人/多人/全站；支付/登录/订单）  
3. 已查服务快照（模拟 health）摘要  
4. 已检索知识 `doc_id` 与可见工单号  
5. **未完成事项**列表（待澄清、待人工核查、待用户确认恢复）  
6. 是否已建单 / ticket 标识（若有）  
7. 已建议但**未执行**的人工动作（切备/回滚等）——标明未执行  

禁止交接内容含密码、密钥、完整证件/卡号。

## 3. 分支

### A — 故障仍开放

输出交接摘要；提醒下一班先复查快照与用户确认，勿假设已恢复。

### B — 等待用户

状态可能 `WAITING_USER`（见工单生命周期）；交接注明等待什么信息。

### C — 已建议升级未闭环

写明升级建议时间与原因；不编造已批准人。

## 4. Agent 边界

可整理交接草稿；不能访问排班表；不能代替签字确认。

## 5. 关联

跨团队升级内容结构见 `OPS-OP-CROSS-TEAM-HANDOFF`。
