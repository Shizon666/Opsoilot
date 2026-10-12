---
doc_id: OPS-SG-AGENT-TOOL-BOUNDARY
title: Agent 工具能力与高风险操作边界
category: SECURITY_GUIDELINE
source_type: markdown
service: PLATFORM
department: 信息安全
severity: CRITICAL
created_at: 2026-10-09
updated_at: 2026-10-09
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C7
basis:
  - code
  - contract
basis_notes: "运行时白名单见 agent/app/tools/__init__.py AGENT_TOOLS；写工具 HITL 见 graph/agent.py WRITE_TOOLS 与 Prompt；高危操作清单与「不给破坏性命令」原则对齐 OPS-SG-HIGH-RISK（docx）；日志边界见 OPS-SG-LOG-EXPORT。"
related_docs:
  - OPS-SG-HIGH-RISK
  - OPS-SG-LOG-EXPORT
  - OPS-SG-SECRETS
  - OPS-SG-PII-TICKET
  - OPS-OP-TICKET-LIFECYCLE
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Agent 工具能力与高风险操作边界

本文用于 OpsPilot **模拟运维环境**。把 **V1 Agent 实际能调用的工具** 与 **必须人工的高风险操作** 写成可检索边界，避免 Agent 声称已查日志、已切备、已清队列或已绕过确认。

有别于 `OPS-SG-HIGH-RISK`（列举删库/清队列等破坏性操作）：本篇给出 **Tool 白名单对照表** 与 HITL 规则，供每次故障回答前核对。

## 1. V1 运行时工具（code / contract）

| 工具 | 读写 | HITL | 用途 |
|------|------|------|------|
| `get_current_user` | 读 | 否 | 当前用户（非授权依据） |
| `list_services` / `get_service_status` | 读 | 否 | ACTIVE 服务与**模拟**健康 |
| `search_knowledge` | 读 | 否 | 运维知识片段 |
| `search_tickets` / `get_ticket` | 读 | 否 | 可见范围内工单 |
| `create_ticket` / `update_ticket` | 写 | **是** | 升级建单/改单 |

**不在白名单（不得假装可用）：** 生产日志查询/导出执行、Prometheus、MQ 管理、扩容/切备/回滚、权限写入、防火墙/DDL/踢登录等。

Legacy Permission 工具不在 V1 主链，不得调用。

## 2. 高风险操作（人工）

下列操作 **Agent 不得执行、不得给出可直接复制的破坏性命令套路**，也不得声称已执行（与 `OPS-SG-HIGH-RISK` 一致，演示约定）：

- 删库或删除业务表、生产 DDL  
- 关闭防火墙、批量踢登录  
- 清空消息队列、替换 TLS 私钥  
- 未授权的切备、扩容、回滚等变更（细节见各 Runbook 原则级建议 + PENDING-ACT-01）

**正确行为：** 说明须有权限人员处理；可建议升级建单（HITL）；引用本规范与对应 Runbook。

## 3. 分支

### 分支 A — 能力内只读调查

- **动作：** 使用健康/知识/工单 Tool；按证据台账记录（`OPS-OP-EVIDENCE-LEDGER`）。  
- **停止：** 结果以外的事实一律不编造。

### 分支 B — 用户要求能力外操作

- **动作：** 明确「当前 Agent 无该 Tool / 无执行权限」；指向人工与高危规范。  
- **停止：** 禁止扮演已完成日志平台查询、已清队列或已切备。

### 分支 C — 写操作

- **动作：** 仅 `create_ticket` / `update_ticket`，且必须 HITL；咨询默认不建单。  
- **停止：** 禁止绕过写操作确认；禁止同回合伪装已批准。

## 4. 与敏感信息

工单与 Chat 禁止粘贴密钥、完整隐私日志（`OPS-SG-SECRETS`、`OPS-SG-PII-TICKET`）。  
V1 无真实日志平台接入时的导出口径见 `OPS-SG-LOG-EXPORT`。

## 5. 关联

见 `related_docs`。排障步骤仍以服务 Runbook 为准；本篇只约束「能不能做、能不能说已做过」。
