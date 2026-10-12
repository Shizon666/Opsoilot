---
doc_id: OPS-RB-CHECKOUT-5XX
title: Checkout API 5xx 排查手册
source: 运维 Runbook / 支付域
source_type: markdown
---

# Checkout API 5xx 排查手册

来源：运维 Runbook（支付域）。仅描述模拟环境，不是真实生产指标。

## 现象

收银台提交订单返回 502/504，或支付超时。用户侧表现为「下单失败」「付不了款」。对应服务一般为 `CHECKOUT_API`。

## 先看服务健康

调用服务状态：若 `health_status` 为 `DEGRADED` 或 `DOWN`，优先按本手册处理，不要当成 VPN 或权限问题。

## 排查步骤

1. 确认时间窗与是否全量失败，还是部分用户。
2. 对照历史工单检索 checkout / 502 / 支付超时，看是否有同类已解决单。
3. 常见原因：上游依赖超时、连接池打满、发布后配置错误。
4. 临时处理：限流、扩容依赖、回滚最近发布。恢复后把结论写入工单 `analysis`。

## 何时建单 / 升级

持续 5xx 超过 10 分钟、或已影响支付成交，应创建故障工单，服务绑定 `CHECKOUT_API`，优先级 high。无法定位依赖时升级人工值守。
