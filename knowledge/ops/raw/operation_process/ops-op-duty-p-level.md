---
doc_id: OPS-OP-DUTY-P-LEVEL
title: 值班升级与 P 级定义
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: MEDIUM
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 值班升级与 P 级定义

## P 级（V1 运维故障）

- P1：全员登录失败、支付成交停摆、入口 TLS 失败。
- P2：单服务 DEGRADED 超过 10 分钟、Worker 积压持续上升。
- P3：局部失败、可绕过、无成交/登录停摆。
- P4：个案账号、噪声单。

工单 `priority` 字段按现有枚举填写；本定义用于值班口语与 analysis，不新增 API 字段。

## 升级

P1 立即人工。P2 按对应 Runbook 时限升级。Agent 可建议升级，不可批准写操作。

## 与知识库

步骤查 Runbook，P 级查本文。不要用模型常识发明公司 P0。
