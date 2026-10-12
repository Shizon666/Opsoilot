---
doc_id: OPS-RB-INGRESS-5XX
title: 网关与入口 5xx 排查手册
category: RUNBOOK
source_type: markdown
service: PLATFORM
department: 平台工程
severity: HIGH
created_at: 2026-10-03
visibility: PUBLIC
status: active
version: 1.0.0
---

# 网关与入口 5xx 排查手册

入口网关、负载均衡、TLS 终止层返回 5xx。不要未分层就把所有 502 写成 Checkout 应用故障。

## 现象

多服务同时 5xx、健康检查失败、证书或上游连接错误出现在网关日志。用户侧可能是整站不可用。

## 先看服务健康

同时看 `CHECKOUT_API`、`AUTH_SERVICE`、`ORDER_WORKER`。若三者都异常，先按入口/平台处理，而不是连开三张业务单互相矛盾。

## 排查步骤

1. 确认 5xx 产生在网关还是上游应用（上游 status vs 网关自身错误）。
2. 检查最近入口配置、证书、超时、限流规则。
3. 临时：切流量到健康集群、回滚入口配置。应用层问题转对应服务 Runbook。
4. 禁止把网关管理口令写入工单。

## 何时建单 / 升级

入口层故障影响多个 ACTIVE 服务：建单服务选主要对外入口对应的业务或按值班约定绑平台影响面，优先级 critical，立即升级。
