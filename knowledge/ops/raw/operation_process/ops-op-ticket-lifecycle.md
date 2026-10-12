---
doc_id: OPS-OP-TICKET-LIFECYCLE
title: 故障工单创建更新与状态流转
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: HIGH
created_at: 2026-10-09
updated_at: 2026-10-09
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C5
basis:
  - code
  - contract
basis_notes: "状态机见 backend/internal/service/ticket_state_machine.go；priority 见 model/ticket.go 与 normalizePriority；create/update 与 HITL 见 Agent Tool 与 Prompt；Employee 不能改 status 见 tool 说明与 OPS-OP-TICKET-ANALYSIS。"
related_docs:
  - OPS-OP-TICKET-ANALYSIS
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-INCIDENT-MINSET
  - OPS-OP-RECOVERY-VERIFY
  - OPS-SM-SERVICE-CATALOG
  - OPS-SG-AGENT-TOOL-BOUNDARY
simulation_notice: true
---

# 故障工单创建更新与状态流转

本文依据 **Go Backend 状态机与 Agent 写工具契约**，说明 V1 故障工单如何创建、更新与流转。  
有别于 `OPS-OP-TICKET-ANALYSIS`（侧重 analysis 文案）：本篇侧重**状态、角色、HITL 与非法跳转**。

## 1. 使用场景

- 用户要求建单/升级，或更新已有工单。  
- Agent 需判断用 `create_ticket` 还是 `update_ticket`。  
- 解释为何不能 `OPEN` 直接 `CLOSED`。

## 2. 合法状态与迁移（code）

状态集合：`OPEN`、`ASSIGNED`、`IN_PROGRESS`、`WAITING_USER`、`RESOLVED`、`CLOSED`。

```text
OPEN → ASSIGNED | IN_PROGRESS
ASSIGNED → IN_PROGRESS
IN_PROGRESS → WAITING_USER | RESOLVED
WAITING_USER → IN_PROGRESS
RESOLVED → CLOSED
CLOSED → （无出口）
```

**禁止示例：** `OPEN → CLOSED`；任意未知状态；从 `CLOSED` 再迁出。

API/Tool 常见小写入参，存储为大写；以 Backend 校验为准。

## 3. priority（code）

仅：`low` / `medium` / `high` / `urgent`（及对应大写）。  
**无** `critical`。建议取值见 `OPS-OP-IMPACT-ESCALATE`，不是状态机的一部分。

## 4. 创建 `create_ticket`（contract）

| 项 | 要求 |
|----|------|
| 时机 | 用户明确要求建单/升级；咨询默认不建单 |
| 必要参数 | `title`、`description`、`service_id`（必须为 **ACTIVE** 服务 UUID） |
| 服务 | 三选一业务：Checkout / Auth / Worker；禁止默认 `GENERAL_IT` |
| analysis | 尽量填写本次分析摘要（写法见 `OPS-OP-TICKET-ANALYSIS`） |
| HITL | 必须用户确认后才真正落库；禁止静默建单、禁止假装已建单 |

缺参先追问，禁止编造 `ticket_no` / `service_id`。

## 5. 更新 `update_ticket`（contract）

| 项 | 要求 |
|----|------|
| 必要 | `ticket_id`；按需 `status` / `analysis` / `priority` 等 |
| 用途 | 已有工单的写更新；用户点名某单时 |
| HITL | 同样必须确认 |
| Employee | 不能改 `status`（以 Tool/Backend 为准）；可更新自己单的分析类字段（见 analysis 规范） |

非法状态迁移由 Backend 拒绝；Agent 不得声称已跳过校验。

## 6. 分支

### 分支 A — 新建

用户明确建单且无点名旧单 → 调查后 `create_ticket` → HITL。

### 分支 B — 更新点名单据

用户给出可见范围内的 `ticket_id` → `get_ticket` 核对后 `update_ticket` → HITL。

### 分支 C — 拒绝/取消写操作

用户 reject → 保留分析价值，不强制再次建单（Prompt）。

## 7. 停止条件

- 服务无法确定且用户拒绝澄清 → 不建单或建单前继续澄清。  
- 目标状态非法 → 说明合法下一步，不编造成功。  
- 高风险内容写入工单 → 见安全规范，脱敏后再写。

## 8. 关联

见 `related_docs`。恢复后如何对待 `RESOLVED`/`CLOSED` 见 `OPS-OP-RECOVERY-VERIFY`。
