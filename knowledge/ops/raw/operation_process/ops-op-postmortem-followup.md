---
doc_id: OPS-OP-POSTMORTEM-FOLLOWUP
title: 故障复盘与纠正措施跟踪
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
  - simulated
basis_notes: "复盘结构为演示约定；具体 IR 为模拟案例（PENDING-IR-01）；Agent 无项目跟踪系统 Tool；不得把虚构叙事单号当生产事故。"
related_docs:
  - OPS-IR-CHECKOUT-GW-TIMEOUT
  - OPS-IR-AUTH-CONFIG
  - OPS-IR-WORKER-CONCURRENCY
  - OPS-IR-OFFWINDOW-RELEASE
  - OPS-IR-CACHE-WARMUP
  - OPS-IR-CERT-ROTATION
  - OPS-OP-TICKET-ANALYSIS
  - OPS-OP-RECOVERY-VERIFY
simulation_notice: true
---

# 故障复盘与纠正措施跟踪

本文用于 OpsPilot **模拟运维环境**。说明复盘应区分**事实 / 推测 / 行动项**，以及 Agent 如何引用模拟 IR、如何跟踪纠正措施状态（无专项跟踪 Tool 时的边界）。

## 1. 独立价值

各 `OPS-IR-*` 是案例正文；本篇是**复盘过程规范**，避免把案例根因抄成当前故障结论。

## 2. 复盘结构（建议）

1. 时间线（已确认 vs 未确认）  
2. 影响范围  
3. 已确认事实 / 推测分栏  
4. 根因（须标依据置信度；模拟案例必须标明）  
5. 纠正措施（owner 角色类型即可，不编造人名）与验证方式  
6. 关联工单与知识 `doc_id`  

## 3. 分支

### A — 引用历史 IR

必须声明「模拟案例 / 非当前现状」；叙事号不可查 tickets 表。

### B — 当前故障尚在进行

优先 Runbook 与恢复验证；**不要**提前写完整复盘定论。

### C — 纠正措施跟踪

Agent 可列出「待跟踪项」并问用户是否已完成；**不能**访问 Jira/看板；未确认则保持开放。

## 4. 禁止

把 PENDING-IR 未批准细节写成生产事故；把复盘行动项伪装成已在生产落地。

## 5. 关联

见 `related_docs`。
