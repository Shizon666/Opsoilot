---
doc_id: OPS-OP-CHANGE-PRECHECK
title: 发布前检查与变更风险评估
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 平台工程
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
basis_notes: "Agent 无变更平台 Tool；检查项为演示约定；与 OPS-OP-CHANGE-ROLLBACK（docx 检查单）及发布后 OPS-RB-RELEASE-ROLLBACK 分工；无正式变更窗口 SLA（PENDING-PLT-01 / PENDING-SLA-01）。"
related_docs:
  - OPS-OP-CHANGE-ROLLBACK
  - OPS-RB-RELEASE-ROLLBACK
  - OPS-OP-ROLLBACK-GATE
  - OPS-OP-HIGH-RISK-PRECHECK
  - OPS-SG-AGENT-TOOL-BOUNDARY
  - OPS-OP-IMPACT-ESCALATE
simulation_notice: true
---

# 发布前检查与变更风险评估

本文用于 OpsPilot **模拟运维环境**。供 Agent 在用户讨论「能不能发版 / 变更风险大不大」时，组织**发布前**澄清与风险判断。  
**不是**发布后回滚步骤（见 `OPS-RB-RELEASE-ROLLBACK` / `OPS-OP-ROLLBACK-GATE`），也**不能**代替人工变更系统审批。

## 1. 独立价值

`OPS-OP-CHANGE-ROLLBACK` 为 docx 检查单资产；`OPS-RB-RELEASE-ROLLBACK` 偏发布**后**止血。本篇补齐 Agent 可检索的**发布前**风险问法与停止条件。

## 2. 适用与证据

**适用：** 计划发布、配置变更、窗口外是否可发等咨询。  
**可取得：** 用户描述的变更范围；相关服务模拟健康；知识与可见工单。  
**不可取得：** 变更工单系统、灰度进度、真实错误率大盘。

## 3. 建议澄清的输入

1. 变更影响哪些 ACTIVE 服务（Checkout / Auth / Worker）？  
2. 是否含数据迁移 / 不可逆步骤？（用户所述）  
3. 是否在约定变更窗口内？（无代码定义窗口时，仅记录用户说法，标模拟/待确认）  
4. 回滚是否已准备、谁有权执行？（Agent 不指定具体人名）  
5. 当前是否已有生产故障在途？

## 4. 分支

### A — 信息不足

停止给出「可以发」结论；列出缺口；建议人工评估。

### B — 高风险迹象（建议升级人工）

含不可逆迁移、无回滚方案、已有全站级故障、需动证书私钥/清队列等（见 `OPS-OP-HIGH-RISK-PRECHECK`）→ **不建议** Agent 鼓励立即发布；建议走人工变更流程。

### C — 仅一般风险咨询

说明 Agent **不能**批准发布；可建议对照 `OPS-OP-CHANGE-ROLLBACK` 检查单由有权限人为核；发布后异常转 `OPS-OP-ROLLBACK-GATE`。

## 5. 禁止

- 编造变更窗口时刻表、审批人、发布命令。  
- 把模拟健康 `HEALTHY` 当成「可以安全发布」的证明。  
- 代为执行或声称已批准变更。

## 6. 关联

见 `related_docs`。
