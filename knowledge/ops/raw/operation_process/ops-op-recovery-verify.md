---
doc_id: OPS-OP-RECOVERY-VERIFY
title: 故障恢复验证与关闭条件
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
knowledge_role: C5
basis:
  - code
  - contract
basis_notes: "健康枚举为模拟快照；Agent 无业务探针/日志/队列深度 Tool；状态 RESOLVED→CLOSED 见 ticket_state_machine；Employee 不能改 status。"
related_docs:
  - OPS-OP-TICKET-LIFECYCLE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-OP-IMPACT-ESCALATE
  - OPS-SM-OBSERVABILITY
  - OPS-SG-AGENT-TOOL-BOUNDARY
simulation_notice: true
---

# 故障恢复验证与关闭条件

本文用于 OpsPilot **模拟运维环境**。统一说明：**什么叫健康改善、什么叫业务恢复待验证/已验证、何时才适合走向 RESOLVED/CLOSED**。  
各 Runbook 的恢复节应与本篇一致，避免把快照变化写成业务已恢复。

## 1. 使用场景（为何独立）

- Runbook 各自写了恢复表，缺少跨故障的关闭纪律。  
- Agent 易把 `HEALTHY` 或「建议观察」说成已验证。  
- 需要与工单状态机对齐：谁能改状态、缺什么不能关单。

## 2. 三种恢复状态（必须区分）

| 状态 | 含义 | Agent 可否单独宣称 |
|------|------|-------------------|
| 服务健康改善 | 再次 `get_service_status` 见 `health_*` 变化 | 可以描述快照变化，须标明模拟快照 |
| 业务恢复待验证 | 支付/登录/订单等用户结果尚未被证实 | **必须**标记待验证；列出需人工/用户确认项 |
| 业务恢复已验证 | 用户或有权限人员**明确反馈**业务侧已恢复 | 仅在有该反馈时可以引用；禁止自行宣称 |

**硬规则：** `HEALTHY` ≠ 支付成功 ≠ 登录成功 ≠ 订单已追平。无对应业务验证 Tool 时，不得伪造验证结果。

## 3. 验证动作（能力内）

| 动作 | 预期 | 不足时 |
|------|------|--------|
| 复查服务快照 | 记录最新 `health_status`/`health_summary` | 快照与用户现象冲突 → 写入证据缺口 |
| 询问用户是否已恢复 | 得到肯定/否定/未知 | 未知 → 保持「待验证」 |
| 对照工单 analysis/resolution | 文案与事实一致 | 无 resolution 勿假装已关闭 |

**不可做：** 查真实日志、Prometheus、队列深度、通道成功率以「证明」恢复。

## 4. 关闭相关状态（code + contract）

建议路径（Support 侧能力，Agent 经 HITL 更新时须合法）：

- 处理中：`IN_PROGRESS`，持续更新 `analysis`。  
- 认为已修复：写清 `resolution`（依据）后迁到 `RESOLVED`。  
- 归档：`RESOLVED → CLOSED`。  
- **禁止** `OPEN → CLOSED`。

Employee **不能**改 `status`。Agent 不得暗示员工可自行关单绕过状态机。

## 5. 分支

### 分支 A — 仅快照改善

- **动作：** 告知快照变化 + 业务仍待验证；询问用户侧是否恢复。  
- **停止：** 不建议仅因快照变为 `HEALTHY` 就关闭工单。

### 分支 B — 用户确认业务恢复

- **动作：** 记录确认内容；若需改状态，走 `update_ticket` + HITL，且迁移合法。  
- **停止：** 无确认则保持待验证。

### 分支 C — 未恢复或反复出现

- **动作：** 回到对应 Runbook / `OPS-OP-IMPACT-ESCALATE`；更新 analysis，勿关闭。

## 6. 写入 analysis / resolution 的最低要求

- 写明验证了什么、谁确认的、哪些仍未知。  
- 禁止空泛「已恢复」「观察中没事了」而无依据（与 `OPS-OP-TICKET-ANALYSIS` 一致）。

## 7. 关联

见 `related_docs`。
