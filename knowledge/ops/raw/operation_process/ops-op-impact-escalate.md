---
doc_id: OPS-OP-IMPACT-ESCALATE
title: 故障影响范围与升级判定
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: MEDIUM
created_at: 2026-10-09
updated_at: 2026-10-09
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C6
basis:
  - code
  - contract
  - simulated
basis_notes: "priority 四档与 HITL/咨询默认不建单见 Backend 与 Agent Prompt；影响面维度为演示约定；不采用分钟硬阈值（PENDING-SLA-01）。P 级口语见 OPS-OP-DUTY-P-LEVEL，但该文中的分钟表述不得当作本篇强制规则。"
related_docs:
  - OPS-OP-DUTY-P-LEVEL
  - OPS-OP-INCIDENT-MINSET
  - OPS-OP-TICKET-LIFECYCLE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-RB-ESCALATE
  - OPS-SG-AGENT-TOOL-BOUNDARY
  - OPS-SM-SERVICE-CATALOG
simulation_notice: true
---

# 故障影响范围与升级判定

本文用于 OpsPilot **模拟运维环境**。供 Agent 在分析故障时判断：**影响有多大、是否建议升级建单、工单 priority 如何建议**。  
本文**不是**正式 SLA，也**不**把值班 P1–P4 写成工单 API 字段。

## 1. 使用场景（为何独立成篇）

- `OPS-OP-DUTY-P-LEVEL` 只给出口语 P 级示例，缺少「影响维度 → 是否升级 → priority 建议」的可检索决策结构。  
- 各 Runbook 有各自升级节，缺少跨故障的统一影响面问法。  
- 需要与 HITL、咨询默认不建单的契约对齐，避免「无法定位就建单」或「DOWN 自动 urgent」。

## 2. 适用范围与输入证据

**适用：** 故障咨询、报障澄清、准备建议升级时。  
**不适用：** 已由用户明确点名 `ticket_id` 的改单细节（见 `OPS-OP-TICKET-LIFECYCLE`）；权限/VPN 等 Phase 10 事项。

**输入证据（能用的）：** 用户描述的影响面；`get_service_status` 模拟快照；`search_tickets` 可见历史；知识 Runbook。  
**不能用的：** 真实用户数大盘、成功率曲线、未接入的监控告警。

## 3. 影响范围维度（先澄清）

向用户澄清（可与 `OPS-OP-INCIDENT-MINSET` 并用）：

| 维度 | 问题示例 | 用途 |
|------|----------|------|
| 广度 | 个人 / 多人 / 看似全站？ | 升级倾向 |
| 业务面 | 是否影响支付成交、登录、订单履约？ | 选服务与 Runbook |
| 持续性 | 仍在发生还是已恢复？ | 是否仍建议升级 |
| 可绕过 | 是否有明显绕过路径？ | priority 建议偏低 |

信息不足时：**先澄清，不下「全站事故」结论，也不强制建单。**

## 4. 分支：分析即可 vs 建议升级

### 分支 A — 默认可分析、不建单（contract）

- **触发：** 用户在咨询/排查，未明确要求建单或升级。  
- **动作：** 完成调查与分析回复；文末询问是否需要升级处理。  
- **停止：** 禁止静默 `create_ticket`。

### 分支 B — 建议升级（建议，非后端强制规则）

在下列情况**建议**人工跟进或请用户确认后建单（无分钟硬阈值）：

- 多用户或全站，且支付/登录/订单履约明显受阻；或  
- 证据缺口大，现有 Tool 无法继续定位，且影响仍在发生；或  
- 下一步涉及高风险人工操作（见 `OPS-SG-AGENT-TOOL-BOUNDARY` / `OPS-SG-HIGH-RISK`）；或  
- 用户明确要求「建单 / 升级处理」。

### 分支 C — 用户已明确要求建单

- **动作：** 按契约先完成必要调查与分析，再调用 `create_ticket`（HITL）。  
- **勿用**「请再确认 A/B」替代写工具调用（Prompt 契约）。

## 5. priority 建议（仅建议）

工单字段仅允许：`low` / `medium` / `high` / `urgent`（code）。

| 情形（演示约定） | 建议 priority |
|------------------|---------------|
| 个案、可绕过、噪声 | `low` 或 `medium` |
| 局部多用户，业务受影响但未停摆 | `medium` 或 `high` |
| 支付/登录/履约大范围受阻且需立即跟进 | `high` 或 `urgent` |

**禁止：**

- 使用 `critical` 作为工单 priority。  
- 把 `health_status=DOWN` **自动**映射为 `urgent`（快照只是线索）。  
- 把 P1–P4 **直接**写成 API 必填映射；口语 P 级见 `OPS-OP-DUTY-P-LEVEL`，填写 priority 时用上表建议。

## 6. 与 P 级文档的关系

- 需要值班口语标签时可读 `OPS-OP-DUTY-P-LEVEL`。  
- 若该文出现「超过 N 分钟」类表述：以 **PENDING-SLA-01** 为准，**本篇升级判定不采用分钟硬阈值**。

## 7. Agent 边界

| 能做 | 不能做 |
|------|--------|
| 澄清影响面；建议是否升级与 priority | 批准写操作；绕过写操作确认；编造影响人数 |

## 8. 关联

见 `related_docs`。具体排障步骤仍以各服务 Runbook 为准。
