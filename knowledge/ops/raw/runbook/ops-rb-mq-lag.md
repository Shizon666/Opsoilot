---
doc_id: OPS-RB-MQ-LAG
title: 消息积压与死信处理手册
category: RUNBOOK
source_type: markdown
service: ORDER_WORKER
department: 运维部
severity: HIGH
created_at: 2026-10-03
updated_at: 2026-10-09
visibility: INTERNAL
status: active
version: 1.1.0
knowledge_role: C3
basis:
  - code
  - contract
  - simulated
basis_notes: "ORDER_WORKER 与健康枚举见 Backend/seed；无队列深度/MQ 管理 Tool 见 Agent；与 WORKER-BACKLOG 分工为契约与演示约定；毒消息隔离/扩容/清队列为原则级人工建议（PENDING-ACT-01）；已删除分钟与值班阈值硬阈值（SLA-01）。"
related_docs:
  - OPS-SM-ORDER-WORKER
  - OPS-RB-WORKER-BACKLOG
  - OPS-IR-WORKER-CONCURRENCY
  - OPS-RB-CHECKOUT-5XX
  - OPS-SM-CHECKOUT
  - OPS-RB-ESCALATE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-SG-PII-TICKET
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# 消息积压与死信处理手册

本文用于 OpsPilot **模拟运维环境**。本篇偏**消息中间件 / 死信 / 重复投递**视角；业务侧 Worker 积压与订单状态不更新优先对照 `OPS-RB-WORKER-BACKLOG`。两篇互补，不要互相替代。

## 1. 适用服务与触发条件

| 适用 | 不适用（应转向） |
|------|------------------|
| 怀疑消费 lag、死信堆积、同一消息反复失败、下游重复副作用风险 | 同步下单接口 5xx → `OPS-RB-CHECKOUT-5XX` |
| 需从「broker / 毒消息 / 清队列风险」角度给人工建议 | 仅登录失败 → `OPS-RB-AUTH-FAIL` |
| 建单仍绑定 `ORDER_WORKER`（ACTIVE），禁止 `GENERAL_IT` | 支付通道无结果且无 5xx → `OPS-RB-PAY-TIMEOUT` |

Agent **没有**队列深度、死信条数或 broker 管理 Tool，不能声称已测得 lag 数值或「死信已超过阈值」。

## 2. 初始证据与需向用户澄清的问题

**可取得：** `get_service_status`（`ORDER_WORKER` 模拟健康）、`search_tickets`、`search_knowledge`。

**不可取得：** MQ 控制台、lag 曲线、消费者进程列表、真实日志/Prometheus。禁止声称「已查询队列深度 / 已确认死信条数」。

**建议澄清：**

1. 用户侧是「下单就 5xx」还是「支付/下单成功后状态不更新」？
2. 是否有多人订单停更？是否怀疑重复扣款/重复通知？（仅用户描述）
3. 值班是否已在其它系统看到 lag/死信？（Agent 无法核验；有则当线索）
4. 是否有人提议清空队列或改 topic？（高风险，见下文）

## 3. 初步判断与易混淆鉴别

| 线索 | 判断 | 局限 |
|------|------|------|
| 订单不更新 + summary 提示积压 | 先读 `OPS-RB-WORKER-BACKLOG`，本篇作中间件补充 | 快照 ≠ 真实 lag |
| 明确提到毒消息、死信、重复投递、broker | 本手册加强人工方向 | 无 MQ Tool |
| Worker `HEALTHY` 但用户仍报积压类现象 | **不能**排除中间件问题；记录不一致 | 无深度数据 |
| Checkout 5xx | 先入口故障，禁止用清队列「修」5xx | — |
| 模拟复盘并发误改 | 可参考 `OPS-IR-WORKER-CONCURRENCY`（**模拟案例**） | PENDING-IR-01 |

## 4. 分支排查步骤

### 步骤 A — 与 Worker 业务积压分流

- **动作：** 判断用户问题更偏「订单/履约状态」还是「MQ/死信/重复投递」。
- **前置：** 报障涉及异步处理。
- **预期：** 偏业务积压 → 主路径 `OPS-RB-WORKER-BACKLOG`，本篇作交叉阅读；偏中间件叙事 → 本手册主路径并交叉 Worker 篇。
- **若不同：** 分不清 → 两篇都列为待人工核查，不编造已查 MQ。

### 步骤 B — 读取 Worker 健康快照

- **动作：** `get_service_status`（`ORDER_WORKER`）。
- **前置：** 异步域问题。
- **预期：** Demo 常见 `DOWN`/`DEGRADED` 与积压类摘要。
- **若不同：**
  - 快照异常 → 记载线索，仍不能得出 lag 数值。
  - 快照「正常」但现象仍在 → 记录不一致，建议人工查 broker/路由（Agent 不能查）。

### 步骤 C — 消费者停滞 vs 毒消息（人工鉴别框架）

- **动作：** 向用户/值班说明需由有权限人员区分：「消费者未在消费」与「消息有毒反复 nack」。列出**建议人工检查方向**，不编造已执行的 MQ 命令或 message id。
- **前置：** 倾向中间件路径或 Worker 篇要求交叉本篇。
- **预期：** 明确下一步在人工侧；若涉及 message id，提醒勿把消息体内 PII 写入 Chat（`OPS-SG-PII-TICKET`）。
- **若不同：** 无人能提供中间件侧信息 → 证据不足，进入升级建议。

### 步骤 D — 历史工单与模拟复盘

- **动作：** `search_tickets`；知识可引用模拟复盘 `OPS-IR-WORKER-CONCURRENCY`。
- **预期：** 真单以 Tool 为准；叙事号不可当 tickets 真单。
- **若不同：** 无命中 → 如实说明。

### 步骤 E — 高风险操作边界（原则级）

- **动作：** 说明扩容消费者、隔离毒消息、清空队列、改 topic 等**仅**能由有权限人员在变更批准下评估（PENDING-ACT-01）。**禁止**把清空队列当作默认修复。
- **预期：** Agent 只传达风险与「需授权」，不提供逐步执行手册级命令。
- **若不同：** 用户要求 Agent「直接清队列」→ 拒绝执行并建议升级人工。

## 5. 缓解建议与风险（人工）

原则级（PENDING-ACT-01）：

- 评估消费者是否存活、毒消息是否需隔离、扩容前下游是否扛得住。
- **风险：** 盲目扩容冲击下游；清空队列可能丢数据且通常需变更批准。
- Agent **不得**执行上述操作。

## 6. Agent 能力边界

| 能做 | 能建议 | 不能执行 |
|------|--------|----------|
| 查模拟健康、知识、可见工单；与 WORKER-BACKLOG 分流 | 升级建单；人工核查 broker/死信方向 | 查 lag/死信数量；清队列；扩容；改 topic；绕过写操作确认 |

## 7. 停止条件与升级条件

**可停止强行下结论：**

- 已确认为入口 5xx 并移交 Checkout Runbook。
- 用户仅需理解「异步未完成」且不升级。
- 无任何中间件侧线索且用户不同意升级时，保留「无法从现有 Tool 确认 lag/死信」。

**建议升级（建议，无正式 SLA，无「超过值班阈值」类硬阈值）：**

- 多用户订单停更，或出现重复副作用怀疑。
- 需要动 MQ/清队列/改 topic/扩容等有权限操作。
- 快照与现象冲突或完全无法区分消费者停滞与毒消息。
- 用户明确要求升级建单。

**priority 建议：** 大范围履约受阻建议 `high`/`urgent`；局部建议 `medium`。勿用 `critical`。

## 8. 恢复验证

| 状态 | 含义 | 谁验证 |
|------|------|--------|
| 服务健康改善 | 仅模拟 `health_*` 变化 | Agent 可复查 |
| 业务恢复待验证 | 订单能否推进、是否仍重复投递：**待验证**；不能声称队列已清空 | 人工/用户 |
| 业务恢复已验证 | 仅当有权限人员或用户**明确确认**积压/死信侧已处理且业务侧恢复 | Agent 不得自行宣称 |

`HEALTHY` **不等于** MQ 已恢复或订单已追平。

## 9. 依据与关联

- code：ORDER_WORKER ACTIVE、健康枚举、priority。  
- contract：无 MQ Tool、与 WORKER-BACKLOG 分工、HITL。  
- simulated：中间件排查方向与人工缓解（PENDING-ACT-01）；模拟复盘链接（PENDING-IR-01）。  

关联见 `related_docs`。
