---
doc_id: OPS-OP-TICKET-ANALYSIS
title: 故障工单 analysis 撰写规范
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: INFO
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 故障工单 analysis 撰写规范

来源：IT Support 作业规范。本篇归入运维流程，不再作为 Runbook 重复建设。早期 ID `OPS-RB-TICKET-ANALYSIS` 废止。

## 必须写什么

`analysis` 是给后续人和 Agent 看的故障摘要，不是聊天记录。至少包含：现象、所属服务、已核对的健康状态、初步原因、已做处理。

## 写法示例

- 好：上游超时导致 Checkout 5xx；对照历史单后扩容依赖，错误率回落。
- 差：修好了 / 再看看 / 用户说不行。

## 状态配合

处理中写入 `IN_PROGRESS` 并更新 `analysis`。恢复后写 `resolution` 再 `RESOLVED` 到 `CLOSED`。禁止 `OPEN` 直接 `CLOSED`。

## 不要写什么

不要把权限申请、VPN 个人接入写进运维故障分析主路径。不要写未证实的根因承诺。Employee 只能改自己的单的分析文字，不能改状态。
