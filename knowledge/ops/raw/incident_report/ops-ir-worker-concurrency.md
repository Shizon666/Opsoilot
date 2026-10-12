---
doc_id: OPS-IR-WORKER-CONCURRENCY
title: Worker 并发参数误改导致积压复盘
category: INCIDENT_REPORT
source_type: markdown
service: ORDER_WORKER
department: 运维部
severity: HIGH
created_at: 2026-05-22
visibility: INTERNAL
status: active
version: 1.0.0
---

# Worker 并发参数误改导致积压复盘

虚构叙事单 `OPS-IR-NARR-403`。不要到 tickets 表里查找该号。

## 时间线

有人将消费者并发从 16 改为 2 并在窗口外生效。队列开始单边上涨。误重启 Checkout 无效果。恢复并发后积压在 40 分钟内消化。

## 影响

已支付订单长时间「处理中」。同步下单接口大部分成功，造成「支付好了但订单没有」的客诉。

## 根因

并发参数无变更审批，监控只看 Checkout 5xx 导致发现偏晚。

## 行动项

Worker 参数纳入变更检查单。积压 Runbook 明确禁止重启收银台。
