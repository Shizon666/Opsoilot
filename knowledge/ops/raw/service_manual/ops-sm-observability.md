---
doc_id: OPS-SM-OBSERVABILITY
title: 可观测性约定
category: SERVICE_MANUAL
source_type: markdown
service: PLATFORM
department: 平台工程
severity: INFO
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 可观测性约定

## 日志字段

对外请求应能用 `request_id` 串联网关、Checkout、Auth、Worker。工单 analysis 优先引用 `request_id` 与时间窗，而不是粘贴整段原始日志。

## 禁止写入日志的内容

密码、Cookie 全量、支付密钥、证件号、银行卡号。发现明文密钥按安全规范升级，不要在群里转发完整日志文件。

## 健康与知识的边界

`health_summary` 是当前快照一句话，不是排查全书。步骤来自 Runbook，个案来自工单检索。

## 导出

生产日志导出边界见 `OPS-SG-LOG-EXPORT`。V1 无真实 Prometheus 接入，本文约定字段口径，不描述监控产品操作。
