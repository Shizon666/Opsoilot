---
doc_id: OPS-OP-HIGH-RISK-PRECHECK
title: 高风险操作前检查与授权确认
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 信息安全
severity: CRITICAL
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C7
basis:
  - contract
  - simulated
basis_notes: "高危操作类型对齐 OPS-SG-HIGH-RISK；Agent 无执行与授权系统（PENDING-ACT-01）；不编造审批人/双人名单；写操作仍仅工单 HITL。"
related_docs:
  - OPS-SG-HIGH-RISK
  - OPS-SG-AGENT-TOOL-BOUNDARY
  - OPS-SG-SECRETS
  - OPS-OP-CHANGE-PRECHECK
  - OPS-OP-ROLLBACK-GATE
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-CROSS-TEAM-HANDOFF
simulation_notice: true
---

# 高风险操作前检查与授权确认

本文用于 OpsPilot **模拟运维环境**。在建议切备、回滚、清队列、换证书私钥等之前，强制走 **风险识别 → 停止自动执行 → 确认需人工授权** 的门禁。

## 1. 独立价值

`OPS-SG-AGENT-TOOL-BOUNDARY` 列 Tool 与禁区；本篇是 **「建议高风险动作之前」的检查清单**，不提供操作步骤。

## 2. 视为高风险的请求（示例）

用户或分析结论指向：清队列、删数据/DDL、关防火墙、批量踢登录、替换 TLS 私钥、无授权回滚/切备、索要密钥。

## 3. 检查清单（全部过完再说话）

1. Agent 是否具备执行 Tool？→ **否**则不得假装可做  
2. 是否涉及密钥/隐私粘贴？→ 禁止，见 `OPS-SG-SECRETS`  
3. 是否已说明业务影响与回滚/恢复验证思路？  
4. 是否已建议走人工与（如需要）故障单 HITL？  
5. 是否误把咨询当成已授权变更？

## 4. 分支

### A — 高风险且无授权上下文

停止给出可复制破坏性命令；说明须有权限人员双人确认类流程（演示原则，不编造具体人名）；建议升级。

### B — 用户要求 Agent「直接做」

拒绝执行；重申边界；可帮写升级信息包（`OPS-OP-CROSS-TEAM-HANDOFF`）。

### C — 仅工单写操作

那是 HITL 工单，不是基础设施变更授权；二者不可混淆。

## 5. 禁止

编造审批人、授权令牌、操作命令；关闭 PENDING-ACT 未决细节当成已批准手册。

## 6. 关联

见 `related_docs`。
