---
doc_id: OPS-SM-SERVICE-CATALOG
title: 运维视角服务目录
category: SERVICE_MANUAL
source_type: markdown
service: PLATFORM
department: 运维部
severity: INFO
created_at: 2026-10-03
visibility: PUBLIC
status: active
version: 1.0.0
---

# 运维视角服务目录

## 用途

帮助值班和 Agent 选择正确的 `service` / 建单 `service_id`。这不是旧 IT 服务台「VPN/软件安装」目录。

## ACTIVE 服务如何选

- 下单、支付、收银台 5xx：`CHECKOUT_API`
- 登录、会话、全员无法进系统：`AUTH_SERVICE`
- 订单状态不更新、队列积压：`ORDER_WORKER`

## 不要选什么

`GENERAL_IT` 已 INACTIVE，禁止作为建单默认。权限申请、入职 FAQ 不属于本知识库主角，不要把故障单开成权限单。

## 平台级问题

入口、证书、缓存、数据库属于平台故障面，analysis 写清，服务绑定仍选受影响的 ACTIVE 业务；不要发明第四个未入库业务 code。
