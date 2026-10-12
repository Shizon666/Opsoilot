---
doc_id: OPS-SM-CHECKOUT
title: Checkout API 服务说明
category: SERVICE_MANUAL
source_type: markdown
service: CHECKOUT_API
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
basis_notes: "服务 code/ACTIVE/健康枚举见 seed 与 model/service.go；建单与 Tool 边界见 Agent 契约；上下游依赖为模拟设定（PENDING-DEP-01），无调用时序与超时数值。"
related_docs:
  - OPS-RB-CHECKOUT-5XX
  - OPS-RB-PAY-TIMEOUT
  - OPS-SM-AUTH
  - OPS-SM-ORDER-WORKER
  - OPS-SM-SERVICE-CATALOG
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Checkout API 服务说明

本文用于 OpsPilot **模拟运维环境**。标记为模拟设定的依赖与场景约定**不是**已验证的生产架构事实。

## 职责

`CHECKOUT_API`（seed 描述：下单与支付接口）负责收银台侧的下单与支付相关接口。用户提交订单、选择支付通道、接收支付结果，在 Demo 故事中都归到本服务。

## 非职责

- 不是登录/会话服务（见 `AUTH_SERVICE` / `OPS-SM-AUTH`）。
- 不是订单异步履约 Worker（见 `ORDER_WORKER` / `OPS-SM-ORDER-WORKER`）。
- 不负责 VPN、GitLab、装机等 Phase 10 员工 IT 事项。
- Agent **不能**通过本服务手册声称已查询生产日志或 Prometheus。

## 适用服务 ID 与建单

| 项 | 说明 | 依据 |
|----|------|------|
| 服务 code | `CHECKOUT_API` | code（seed） |
| 建单 | `service_id` 必须绑定 ACTIVE 的 Checkout，禁止默认 `GENERAL_IT`（已 INACTIVE） | code |
| 应先澄清再绑定 | 用户只说「付不了款」但未区分入口 5xx / 通道无结果 / 订单不更新时，先问现象与是否看到 HTTP 5xx，再选服务与 Runbook | contract |

## 依赖（定性；含模拟设定）

以下关系为**演示用定性依赖**（`basis: simulated`，PENDING-DEP-01），**未**给出调用顺序、超时或重试参数：

- 支付通道（通道侧超时与切备见 `OPS-RB-PAY-TIMEOUT`，非本手册操作细则）。
- 登录态/会话校验可能涉及 `AUTH_SERVICE`（同时告警时须分开验证，见 `OPS-SM-AUTH`）。
- 下单后的异步履约由 `ORDER_WORKER` 消费（同步下单成功 ≠ Worker 已处理完）。

本服务超时或 5xx **不等于** Worker 积压，也 **不等于** 用户密码错误。

## 常见故障 → Runbook

| 现象（用户/接口） | 初步鉴别 | 优先文档 |
|------------------|----------|----------|
| 提交订单返回 502/504/5xx | 入口/API 错误 | `OPS-RB-CHECKOUT-5XX` |
| 已进入支付、接口多为 200，长时间无支付结果 | 倾向通道侧，非本篇入口 5xx | `OPS-RB-PAY-TIMEOUT` |
| 支付成功但订单状态长期不更新 | 倾向异步履约 | `OPS-RB-WORKER-BACKLOG` / `OPS-SM-ORDER-WORKER` |
| 仅登录失败 | 勿绑 Checkout | `OPS-SM-AUTH` / `OPS-RB-AUTH-FAIL` |

不得仅凭口语「支付失败」直接断定 Checkout 服务故障；也不得假设仓库中未定义的支付错误码表。

## Agent 可读取 / 不可读取

| 可读取（Tool） | 不可读取 / 不可执行 |
|----------------|---------------------|
| `list_services` / `get_service_status`（模拟 `health_status`、`health_summary`） | 真实日志平台、Prometheus、链路追踪 |
| `search_knowledge`、`search_tickets` / `get_ticket` | 扩容、切备、回滚、改配置等基础设施操作 |
| 用户明确升级且 HITL 确认后的 `create_ticket` / `update_ticket` | 绕过写操作确认；把健康快照当业务已恢复的证明 |

健康枚举仅为 `HEALTHY` / `DEGRADED` / `DOWN`（模拟快照）。Demo seed 中 Checkout 常为 `DEGRADED` 且摘要提及 5xx/支付超时——那是**种子数据快照**，不是实时生产监控。

## 关联文档

见 front matter `related_docs`。服务选型总览见 `OPS-SM-SERVICE-CATALOG`；证据边界见 `OPS-SM-OBSERVABILITY`。
