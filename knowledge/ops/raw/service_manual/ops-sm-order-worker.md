---
doc_id: OPS-SM-ORDER-WORKER
title: Order Worker 服务说明
category: SERVICE_MANUAL
source_type: markdown
service: ORDER_WORKER
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
basis_notes: "ORDER_WORKER ACTIVE 与 seed 健康摘要见迁移；MQ/库存依赖为模拟设定（PENDING-DEP-01）；OPS-IR-WORKER-CONCURRENCY 为模拟复盘（PENDING-IR-01），非生产事故记录。"
related_docs:
  - OPS-RB-WORKER-BACKLOG
  - OPS-RB-MQ-LAG
  - OPS-IR-WORKER-CONCURRENCY
  - OPS-SM-CHECKOUT
  - OPS-SM-SERVICE-CATALOG
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Order Worker 服务说明

本文用于 OpsPilot **模拟运维环境**。标记为模拟设定的依赖与案例**不是**已验证的生产事实。

## 职责

`ORDER_WORKER`（seed 描述：订单异步消费 Worker）负责订单异步履约：消费队列、更新订单状态、触发下游通知（Demo 叙事）。**同步下单成功不代表 Worker 已处理完。**

## 非职责

- 不是收银台同步下单/支付入口（`CHECKOUT_API`）。
- 不是登录服务（`AUTH_SERVICE`）。
- Agent 无队列深度、消费者进程管理或 MQ 管理 Tool，不能声称「已确认队列已清空」。

## 适用服务 ID 与建单

| 项 | 说明 | 依据 |
|----|------|------|
| 服务 code | `ORDER_WORKER` | code |
| 建单 | 绑定 ACTIVE 的 Worker；禁止 `GENERAL_IT` | code |
| 应先澄清 | 「订单一直处理中」需区分：同步下单是否已 5xx、还是支付成功后状态不更新 | contract |

## 依赖（定性；含模拟设定）

以下为**演示用定性依赖**（`simulated`，PENDING-DEP-01），无时序/超时数值：

- 消息队列（中间件视角见 `OPS-RB-MQ-LAG`）。
- 下游库存/履约接口（模拟设定）。
- 数据库（模拟设定）。

并发参数误改等叙事见模拟复盘 `OPS-IR-WORKER-CONCURRENCY`（**模拟案例**，虚构标识见该文；不得当作真实生产事故或可查 tickets 真单）。

## 健康快照的用法与局限

seed 中 Worker 常为 `DOWN`，摘要含「消费积压，队列不再下降」。该快照：

- 可提示优先阅读 `OPS-RB-WORKER-BACKLOG`。
- **不能**证明当前真实队列深度或订单已追平。
- `CHECKOUT_API` 为 `HEALTHY` **不能**证明 Worker 正常。

## 常见故障 → Runbook

| 现象 | 初步鉴别 | 优先文档 |
|------|----------|----------|
| 订单状态长期不更新、summary 提示积压 | Worker/业务积压路径 | `OPS-RB-WORKER-BACKLOG` |
| 侧重 broker lag、死信、毒消息 | 消息中间件路径 | `OPS-RB-MQ-LAG` |
| 收银台同步 5xx | 不是重启 Checkout 能修 Worker | `OPS-RB-CHECKOUT-5XX` |
| 仅想「重启收银台清积压」 | **禁止**作为修复手段（无代码依据支持） | 见 `OPS-RB-WORKER-BACKLOG` |

## Agent 可读取 / 不可读取

| 可读取 | 不可读取 / 不可执行 |
|--------|---------------------|
| 模拟健康、知识、可见工单 | 队列深度、杀消费者、清空队列、扩容参数 |
| HITL 后建单/改单 | 把 health 从 DOWN→其它写成「订单已全部处理完」 |

## 关联文档

见 `related_docs`。`OPS-IR-WORKER-CONCURRENCY` 仅作模拟案例参考。
