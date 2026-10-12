---
doc_id: OPS-SM-AUTH
title: Auth Service 服务说明
category: SERVICE_MANUAL
source_type: markdown
service: AUTH_SERVICE
department: 运维部
severity: INFO
created_at: 2026-10-03
updated_at: 2026-10-09
visibility: PUBLIC
status: active
version: 1.1.0
knowledge_role: C2
basis:
  - code
  - contract
  - simulated
basis_notes: "AUTH_SERVICE ACTIVE 与健康枚举见 seed；Tool/HITL 见 Agent 契约；会话存储与证书依赖为模拟设定（PENDING-DEP-01 / PENDING-PLT-01），本篇不写轮转步骤。"
related_docs:
  - OPS-RB-AUTH-FAIL
  - OPS-RB-CERT-EXPIRY
  - OPS-RB-CHECKOUT-5XX
  - OPS-SM-CHECKOUT
  - OPS-SM-SERVICE-CATALOG
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Auth Service 服务说明

本文用于 OpsPilot **模拟运维环境**。标记为模拟设定的依赖与场景约定**不是**已验证的生产架构事实。

## 职责

`AUTH_SERVICE`（seed 描述：登录与会话服务）负责登录、会话与令牌校验相关能力。身份域故障应优先对照本服务与 `OPS-RB-AUTH-FAIL`。

## 非职责

- 不是下单/支付入口（`CHECKOUT_API`）。
- 不是订单异步消费（`ORDER_WORKER`）。
- 不负责员工 VPN/GitLab/装机制度（不在 V1 ops 索引）。
- 不提供「已查询认证审计日志」类能力（Agent 无日志 Tool）。

## 适用服务 ID 与建单

| 项 | 说明 | 依据 |
|----|------|------|
| 服务 code | `AUTH_SERVICE` | code |
| 建单 | 绑定 ACTIVE 的 Auth；禁止 `GENERAL_IT` | code |
| 应先澄清 | 「打不开」未区分登录失败 / 收银台 5xx / 订单不更新时，先澄清现象再绑服务 | contract |

## 依赖（定性；含模拟设定）

以下为**演示用定性依赖**（`simulated`，PENDING-DEP-01 / PENDING-PLT-01），无时序与超时数值：

- 会话存储（模拟设定）。
- 证书 / TLS（证书类排查只关联 `OPS-RB-CERT-EXPIRY`，**本轮不扩写**轮转操作）。
- Checkout 在需要登录态时可能依赖本服务（模拟设定）；**支付失败不可直接归因于 Auth**。

## 健康快照的用法与局限

seed 中 Auth 常为 `HEALTHY`（摘要如「登录成功率正常」）。该值是**模拟健康快照**：

- 可作为「优先排查个案账号」的**线索**，不能排除所有认证故障。
- `HEALTHY` **不等于**已证明全员可登录成功。
- `DEGRADED` / `DOWN` 时应按服务故障路径处理（见 Runbook），仍不能代替业务侧登录验证。

## 常见故障 → Runbook

| 现象 | 初步鉴别 | 优先文档 |
|------|----------|----------|
| 大范围无法登录、会话无法建立 | 服务/依赖方向 | `OPS-RB-AUTH-FAIL` |
| 单一账号密码错误/锁定 | 非全站路径；低优先级个案 | `OPS-RB-AUTH-FAIL`（个案分支） |
| TLS/证书类登录失败线索 | 外链证书手册，不在本篇操作 | `OPS-RB-CERT-EXPIRY` |
| 与 Checkout 5xx 同时出现 | **仅进一步核查线索**，禁止直接断言依赖根因 | 分别走 `OPS-RB-AUTH-FAIL` 与 `OPS-RB-CHECKOUT-5XX` |

## Agent 可读取 / 不可读取

| 可读取 | 不可读取 / 不可执行 |
|--------|---------------------|
| 服务模拟健康、知识库、可见工单 | 真实日志、Prometheus、改会话存储/证书 |
| HITL 后的建单/改单 | 跳过确认；把 `HEALTHY` 写成「已排除故障」 |

## 关联文档

见 `related_docs`。选型见 `OPS-SM-SERVICE-CATALOG`；证据边界见 `OPS-SM-OBSERVABILITY`。
