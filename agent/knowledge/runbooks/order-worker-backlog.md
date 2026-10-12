---
doc_id: OPS-RB-WORKER-BACKLOG
title: Order Worker 队列积压排查手册
source: 运维 Runbook / 订单域
source_type: markdown
---

# Order Worker 队列积压排查手册

来源：运维 Runbook（订单域）。对应服务 `ORDER_WORKER`。

## 现象

订单状态长时间不更新、异步任务堆积、消费滞后。健康状态常见为 `DOWN`（队列不再下降）或 `DEGRADED`。

## 排查步骤

1. 看 `ORDER_WORKER` 的 `health_summary` 是否写明积压。
2. 检查消费者是否存活、是否卡在毒消息、是否下游超时。
3. 禁止用重启收银台来「修复」Worker；那是另一条链路。
4. 临时手段：扩容消费者、跳过毒消息、回滚有问题的 Worker 版本。

## 何时建单

积压持续上升或业务订单停更：绑定 `ORDER_WORKER`，优先级 high，analysis 写清积压现象与是否影响下单同步路径。
