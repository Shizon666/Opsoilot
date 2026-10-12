---
doc_id: OPS-RB-WORKER-BACKLOG
title: Order Worker 队列积压排查手册
category: RUNBOOK
source_type: markdown
service: ORDER_WORKER
department: 运维部
severity: HIGH
created_at: 2026-10-03
updated_at: 2026-10-09
visibility: PUBLIC
status: active
version: 1.1.0
knowledge_role: C3
basis:
  - code
  - contract
  - simulated
basis_notes: "ORDER_WORKER 与健康枚举见 seed/Backend；无队列深度 Tool 见 Agent 白名单；MQ 细节外链 OPS-RB-MQ-LAG；缓解为原则级人工建议（PENDING-ACT-01）；模拟复盘 OPS-IR-WORKER-CONCURRENCY（PENDING-IR-01）；已删除分钟硬阈值（SLA-01）。"
related_docs:
  - OPS-SM-ORDER-WORKER
  - OPS-RB-MQ-LAG
  - OPS-IR-WORKER-CONCURRENCY
  - OPS-RB-CHECKOUT-5XX
  - OPS-SM-CHECKOUT
  - OPS-RB-ESCALATE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Order Worker 队列积压排查手册

本文用于 OpsPilot **模拟运维环境**。积压是异步履约问题，**不等于**收银台同步下单 5xx。

## 1. 适用服务与触发条件

| 适用 | 不适用 |
|------|--------|
| 订单状态长时间不更新、异步任务堆积、消费滞后 | 同步下单接口 5xx → `OPS-RB-CHECKOUT-5XX` |
| `ORDER_WORKER` 健康摘要提示积压/队列不下降（模拟快照线索） | 仅登录失败 → `OPS-RB-AUTH-FAIL` |
| 需区分 Worker 业务积压 vs MQ/死信细节 | 侧重 broker lag/死信操作细节 → 同时阅读 `OPS-RB-MQ-LAG` |

**禁止：** 建议通过重启 Checkout 解决 Worker 积压（无代码/契约依据支持该修复）。

## 2. 用户可见现象与可取得证据

**现象：** 「支付成功但订单一直处理中」、履约通知延迟、状态不刷新等。

**可取得：** `get_service_status`（`ORDER_WORKER` 模拟健康）、`search_tickets`、`search_knowledge`。

**不可取得：** 队列深度、消费者进程列表、MQ 管理台、真实日志/Prometheus。因此 **不能声称**「已验证队列已清空」或「订单已全部追平」。

## 3. 初步判断与易混淆鉴别

| 线索 | 判断 | 局限 |
|------|------|------|
| 下单同步已成功，卡在后续状态 | 本手册主路径 | Agent 无业务订单查询 Tool |
| Checkout 同时 5xx | 先按入口 5xx 处理；**订单未更新 ≠ Checkout 一定故障** | 分开取证 |
| summary 写积压且 Worker `DOWN`/`DEGRADED` | 优先本手册 | 快照 ≠ 真实队列深度 |
| 毒消息/死信/broker lag 细节 | 交叉 `OPS-RB-MQ-LAG` | 两篇互补，非互相替代 |
| 模拟复盘并发误改 | 可参考 `OPS-IR-WORKER-CONCURRENCY`（**模拟案例**，非生产事故记录） | PENDING-IR-01 |

## 4. 分支排查步骤

### 步骤 A — 排除同步入口故障

- **动作：** 确认用户是否遇到下单/支付接口 5xx，或仅状态不更新。
- **前置：** 报障涉及订单。
- **预期：** 纯异步积压 → 继续本手册；明确 5xx → 转 `OPS-RB-CHECKOUT-5XX`（可并行记录，但修复手段不可混用）。
- **若不同：** 说不清 → 先澄清，不绑错服务。

### 步骤 B — 读取 Worker 健康快照

- **动作：** `get_service_status`（`ORDER_WORKER`），阅读 `health_status` 与 `health_summary`。
- **前置：** 已倾向异步路径。
- **预期：** Demo 中常见 `DOWN` + 积压类摘要。
- **若不同：**
  - Checkout `HEALTHY` 而 Worker 异常 → 证明两条链路独立，**不要**用 Checkout 健康否定积压。
  - Worker 快照「正常」但用户仍报订单不更新 → 记录不一致，继续人工核查/升级，禁止宣称已排除。

### 步骤 C — Worker 路径 vs MQ 路径

- **动作：** 用知识区分：本篇偏 Worker 进程/业务积压；`OPS-RB-MQ-LAG` 偏消息中间件、死信、重复投递。
- **前置：** 步骤 B 完成或并行检索知识。
- **预期：** 给出应人工重点查看的方向（进程是否消费、是否毒消息等），**不编造**已执行的 MQ 命令。
- **若不同：** 信息不足以区分 → 两条都列为待核查，升级人工。

### 步骤 D — 历史工单与模拟复盘

- **动作：** `search_tickets`；知识中可引用模拟复盘 `OPS-IR-WORKER-CONCURRENCY` 作案例学习。
- **预期：** 真单以 Tool 为准；复盘叙事号不可当 tickets 真单查询。
- **若不同：** 无命中 → 如实说明。

## 5. 缓解建议与风险（人工）

原则级建议（PENDING-ACT-01），须由有权限运维人员评估：

- 检查消费者是否存活、是否卡在毒消息、下游是否超时。
- 评估扩容消费者、隔离毒消息、回滚有问题的 Worker 版本等选项。
- **风险：** 盲目扩容可能压垮下游；清空队列可能丢数据且通常需变更批准（见 `OPS-RB-MQ-LAG` 口径）。
- Agent **不得**执行上述操作，也不得写成已获授权步骤。

## 6. Agent 能力边界

| 能做 | 能建议 | 不能执行 |
|------|--------|----------|
| 查模拟健康、知识、可见工单；组织分析 | 升级建单；人工核查方向；区分 MQ 专册 | 查队列深度；重启/扩容/清队列；重启 Checkout「修复」积压 |

## 7. 停止条件与升级条件

**停止强行下结论：** 实为入口 5xx 已移交；用户仅需理解「异步未完成」且不升级；证据不足且用户不同意升级时保留「无法确认」。

**建议升级（无正式 SLA / 无分钟硬阈值）：**

- 多用户订单停更或履约明显受阻。
- 快照提示积压且无法用现有 Tool 定位。
- 需要动 MQ/消费者/回滚等高风险人工操作。
- 用户明确要求升级建单。

**priority 建议：** 订单履约大面积受阻建议 `high` 或 `urgent`；局部个案建议 `medium`。勿使用 `critical`。

## 8. 恢复验证

| 检查项 | 含义 | 谁验证 |
|--------|------|--------|
| 健康快照变化 | 仅证明模拟状态字段变化 | Agent 可复查 |
| 业务恢复（订单推进/追平） | **待验证**；无队列深度 Tool，不能声称已清空或已追平 | 人工/用户确认 |

`HEALTHY` **不等于**订单处理已恢复。

## 9. 依据与关联

code：服务与健康枚举；contract：Tool 边界与禁止重启 Checkout 修积压；simulated：依赖、缓解原则、模拟复盘链接。关联见 `related_docs`。
