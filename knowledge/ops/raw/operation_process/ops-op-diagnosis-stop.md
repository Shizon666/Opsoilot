---
doc_id: OPS-OP-DIAGNOSIS-STOP
title: 证据不足时的诊断停止条件
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
basis_notes: "对齐 Prompt「依据不足时」与 EVIDENCE-LEDGER；停止自动深挖不等于拒绝帮助；无分钟 SLA。"
related_docs:
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-REEVAL-AFTER-CLARIFY
  - OPS-OP-INCIDENT-MINSET
  - OPS-SG-AGENT-TOOL-BOUNDARY
  - OPS-OP-RECOVERY-VERIFY
simulation_notice: true
---

# 证据不足时的诊断停止条件

本文规定 Agent **何时停止继续猜测根因**，改为澄清、保守建议或升级，防止在无 Tool 证据时「查得越深编得越多」。

## 1. 独立价值

`OPS-OP-EVIDENCE-LEDGER` 教如何记账；本篇教 **何时停下自动诊断**。

## 2. 应停止深挖的触发条件

出现任一项即应停止编造根因：

1. 影响面或主现象无法区分（登录 vs 支付 vs 订单）且用户未补充  
2. 所需证据依赖不存在的 Tool（日志、队列深度、通道后台）  
3. 知识无命中且服务快照与现象严重冲突，无下一步可验证动作  
4. 继续回答只能依赖常识替代公司规则  

## 3. 停止后的合法动作

| 动作 | 说明 |
|------|------|
| 澄清 | 按 `OPS-OP-INCIDENT-MINSET` 提问 |
| 保守分析 | 列出已查到/未查到；不写「已确认根因」 |
| 建议升级 | 按 `OPS-OP-IMPACT-ESCALATE`（非强制建单） |
| 等待补充 | 说明收到补充后将按 `OPS-OP-REEVAL-AFTER-CLARIFY` 重评 |

## 4. 分支

### A — 可部分分析

给出现象级建议与关联 Runbook，明确未知项。

### B — 几乎无法分析

承认无法确认；询问是否升级；默认不建单。

### C — 用户强迫要根因

重申证据边界；拒绝编造；可建议人工。

## 5. 禁止

用「持续观察」「再看看」代替停止条件而不说明缺什么；假装已查监控。

## 6. 关联

见 `related_docs`。
