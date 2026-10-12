---
doc_id: OPS-OP-ROLLBACK-GATE
title: 发布失败后的回滚决策与验证
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 平台工程
severity: HIGH
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C6
basis:
  - contract
  - simulated
basis_notes: "Agent 无回滚执行 Tool（PENDING-ACT-01）；决策门禁为演示约定；操作细则外链 OPS-RB-RELEASE-ROLLBACK；恢复验证对齐 OPS-OP-RECOVERY-VERIFY；工单 priority 仅四档。"
related_docs:
  - OPS-RB-RELEASE-ROLLBACK
  - OPS-OP-CHANGE-PRECHECK
  - OPS-OP-CHANGE-ROLLBACK
  - OPS-OP-RECOVERY-VERIFY
  - OPS-OP-IMPACT-ESCALATE
  - OPS-SG-AGENT-TOOL-BOUNDARY
  - OPS-OP-TICKET-LIFECYCLE
simulation_notice: true
---

# 发布失败后的回滚决策与验证

本文用于 OpsPilot **模拟运维环境**。帮助 Agent 判断：**是否应建议回滚、回滚前缺什么信息、回滚后如何验证**。  
具体平台操作见 `OPS-RB-RELEASE-ROLLBACK`（原则级）；Agent **不能**执行回滚。

## 1. 独立价值

Runbook 写「怎么回滚」叙事；本篇写 **Agent 决策门禁**：建议 / 不建议 / 必须升级人工，以及验证分层。

## 2. 触发与澄清

**触发线索：** 用户称最近发布后出现 5xx、登录失败、Worker 异常或功能与说明不符。

**澄清：** 发布时间与版本（用户所述）、影响面、是否含不可逆迁移、当前是否仍在放量。

## 3. 分支

### A — 先排除非发布问题

若无时间相关发布线索，优先对应故障 Runbook，勿默认回滚。

### B — 可逆发布 + 业务明显受损

- **建议：** 有权限人员评估回滚；Agent 只建议并引导建单（HITL）。  
- **禁止：** 给出逐步回滚命令、声称已回滚。  
- **priority 建议：** 支付/登录大范围受阻时 `high` 或 `urgent`（非 `critical`）。

### C — 不可逆迁移或无授权

- **停止**建议值班自行「修数据」或强行回滚。  
- **动作：** 升级人工；记录证据缺口（`OPS-OP-EVIDENCE-LEDGER`）。

### D — 回滚后验证

按 `OPS-OP-RECOVERY-VERIFY`：快照改善 ≠ 业务已恢复；需用户/人工确认支付、登录或履约。

## 4. 与工单

任何生产回滚建议配套故障单（用户确认后 `create_ticket`）。analysis 写清：发布线索、是否已建议回滚、验证状态。

## 5. 关联

见 `related_docs`。
