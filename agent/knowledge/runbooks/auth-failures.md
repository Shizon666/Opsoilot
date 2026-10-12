---
doc_id: OPS-RB-AUTH-FAILURES
title: Auth Service 登录失败排查手册
source: 运维 Runbook / 身份域
source_type: markdown
---

# Auth Service 登录失败排查手册

来源：运维 Runbook（身份域）。用于区分「账号问题」与「认证服务故障」。

## 现象

登录接口失败、会话无法建立、偶发 401/500。对应服务一般为 `AUTH_SERVICE`。

## 先看服务健康

若 `AUTH_SERVICE` 为 `HEALTHY`，优先排除用户密码错误、账号锁定，不要把个案写成全站故障。若为 `DEGRADED`/`DOWN`，按服务故障处理。

## 排查步骤

1. 确认是否全员无法登录，还是单个账号。
2. 单账号：引导重置密码，可建低优先级工单。
3. 全员失败：检查认证服务依赖、证书、最近发布。
4. 与 Checkout 5xx 同时出现时，先分开验证两条链路，禁止把支付失败直接归因于登录。

## 何时建单

大面积登录失败：绑定 `AUTH_SERVICE`，优先级 high。单个账号问题：优先级 low，analysis 写明「非全站故障」。
