---
doc_id: OPS-RB-CHECKOUT-5XX
title: Checkout API 5xx 排查手册
category: RUNBOOK
source_type: markdown
service: CHECKOUT_API
department: 运维部
severity: HIGH
created_at: 2026-10-03
updated_at: 2026-10-09
visibility: PUBLIC
status: active
version: 1.1.1
knowledge_role: C3
basis:
  - code
  - contract
  - simulated
basis_notes: "服务绑定与健康枚举/优先级枚举见 Backend；Tool 与 HITL 见 Agent；依赖与缓解手段为原则级模拟建议（PENDING-DEP-01 / PENDING-ACT-01）；已删除分钟级硬阈值（SLA-01）。"
related_docs:
  - OPS-SM-CHECKOUT
  - OPS-RB-PAY-TIMEOUT
  - OPS-RB-DEP-TIMEOUT
  - OPS-RB-WORKER-BACKLOG
  - OPS-RB-ESCALATE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Checkout API 5xx 排查手册

本文用于 OpsPilot **模拟运维环境**，不是真实生产指标手册。建单绑定 `CHECKOUT_API`，禁止默认 `GENERAL_IT`。

## 1. 适用服务与触发条件

| 适用 | 不适用（应转向） |
|------|------------------|
| 收银台/下单接口返回 **HTTP 5xx、502、504** 等服务错误 | 仅支付通道超时/无结果，且**没有**接口 5xx 证据 → `OPS-RB-PAY-TIMEOUT` |
| 用户可见「下单失败」「提交订单报错」且伴随 5xx | 支付成功后订单状态不更新 → `OPS-RB-WORKER-BACKLOG` |
| | 仅登录失败 → `OPS-RB-AUTH-FAIL` |

不得仅凭口语「付不了款 / 支付失败」直接判定为本手册故障；不得假设未在代码中定义的支付错误码。

## 2. 用户可见现象与可取得证据

**现象（示例）：** 提交订单失败、页面报错、接口状态码为 5xx/502/504。

**当前可取得的证据（Agent Tool）：**

- `get_service_status`（或先 `list_services`）：模拟 `health_status` / `health_summary`
- `search_tickets`：同类历史单（可见性受角色约束）
- `search_knowledge`：本手册与关联片段

**不可取得：** 真实接入日志、Prometheus、APM、通道侧后台。无此类 Tool 时禁止声称「已查询日志/监控」。

## 3. 初步判断与易混淆鉴别

| 线索 | 判断 | 局限 |
|------|------|------|
| 明确 HTTP 5xx/502/504 | 优先本手册 | 快照 DEGRADED 不能单独当根因 |
| 已进入支付、接口多为 200、长时间无支付结果 | 转向 `OPS-RB-PAY-TIMEOUT` | 本篇不覆盖切备操作细节 |
| 同时有 Auth 告警 | **核查线索**，分开验证；禁止直接断言 Auth 依赖故障 | 无调用链 Tool |
| 订单不更新但下单已成功 | Worker 路径，非「重启 Checkout」 | 见 `OPS-RB-WORKER-BACKLOG` |

## 4. 分支排查步骤

### 步骤 A — 固定服务与健康快照

- **动作：** 调用 `list_services` / `get_service_status`，确认 `CHECKOUT_API` 的 `health_status` 与 `health_summary`。
- **前置：** 用户问题属下单/支付域，或已排除纯登录问题。
- **预期：** 得到模拟快照（Demo 中常见 `DEGRADED` 及 5xx/超时类摘要）。
- **若不同：**
  - 服务不存在/非 ACTIVE → 停止臆造第四业务；澄清后按目录选型（`OPS-SM-SERVICE-CATALOG`）。
  - 快照为 `HEALTHY` 但仍报 5xx → **不排除**故障；记录「快照与现象不一致」，继续收集用户侧状态码与时间窗。
  - **建议人工跟进 / 升级建单（建议，无正式 SLA）：** 若同时满足或高度接近 §7——多用户/全站支付或下单受阻、已见入口 5xx 但证据不足以定位、缓解需高风险人工操作，或用户明确要求升级——再建议人工核查或 HITL 建单；不要在仅快照异常、影响面未明时空喊「升级」。

### 步骤 B — 确认是否入口 5xx

- **动作：** 向用户确认是否看到 HTTP 5xx/502/504，或是否「进了支付页但一直转圈且接口仍是 200」。
- **前置：** 步骤 A 完成或并行。
- **预期：** 能区分入口 5xx vs 通道无结果。
- **若不同：**
  - 无 5xx、偏通道无结果 → **停止本手册主路径**，改用 `OPS-RB-PAY-TIMEOUT`。
  - 用户说不清 → 先澄清，**不要**强行绑服务下根因结论。

### 步骤 C — 历史工单对照

- **动作：** `search_tickets`（关键词如 checkout、502、支付）。
- **前置：** 需要历史参考时。
- **预期：** 得到可见工单列表或明确无命中；个案以 Tool 结果为准。
- **若不同：** 无命中 → 写「未见同类可见历史工单」；禁止编造 `ticket_no` 或把知识复盘叙事号当现状。

### 步骤 D — 依赖方向（原则级，无执行）

- **动作：** 基于知识片段说明**可能**方向：上游依赖、配置/发布问题等（模拟常见原因，非已证实根因）。需要时交叉阅读 `OPS-RB-DEP-TIMEOUT`。
- **前置：** 已确认入口 5xx 路径。
- **预期：** 给出需人工核查的方向列表。
- **若不同：** 证据不足 → 进入「证据不足」停止/升级条件，禁止编造根因。

## 5. 缓解建议与风险（人工；Agent 不可执行）

以下为**原则级人工缓解建议**（PENDING-ACT-01），**不是** Agent 可执行步骤，也**不是**已获授权的操作手册：

- 由有权限的运维人员评估：限流、检查近期发布、扩容或回滚等选项。
- **风险：** 误操作可能扩大影响；连续来回变更可能恶化状态。
- Agent 只可**建议**人工评估，不得声称已扩容/已回滚/已切流。

## 6. Agent 能力边界

| 能做 | 能建议 | 不能执行 |
|------|--------|----------|
| 查模拟健康、知识、可见工单；组织分析回复 | 是否升级建单；原则级人工核查方向 | 查日志/监控；限流/扩容/回滚/切备；绕过写操作确认 |

写操作仅在用户明确要求升级且 HITL 确认后：`create_ticket` / `update_ticket`。咨询默认不建单。

## 7. 停止条件与升级条件

**可停止下结论（保留分析价值）：**

- 已澄清为通道超时路径并移交 `OPS-RB-PAY-TIMEOUT`。
- 现象不符合 5xx，需用户补充状态码/时间窗。
- 用户只要分析、明确不升级。

**建议升级（人工 / 建单）——无正式 SLA，不使用分钟硬阈值：**

- 影响面为多用户或全站，且支付/下单受阻。
- 已确认入口 5xx，但证据不足以定位，需有权限人员继续核查。
- 缓解涉及高风险变更或权限边界，Agent 无法执行。
- 用户明确要求建单/升级处理。

**priority 建议（工单字段，非 P 级 API）：** 多用户支付受阻且需立即跟进时建议 `high` 或 `urgent`；局部、可绕过时建议 `medium`。仅使用 `low` / `medium` / `high` / `urgent`。P1–P4 仅作值班口语参考（见 `OPS-OP-DUTY-P-LEVEL`），不是工单枚举。

## 8. 恢复验证

| 检查项 | 含义 | 谁验证 |
|--------|------|--------|
| 健康快照变化 | 仅证明模拟 `health_status`/`health_summary` 有变化 | Agent 可再调 `get_service_status` |
| 业务恢复（下单/支付成功） | **待验证**；`HEALTHY` ≠ 支付成功 | 人工或用户侧确认；Agent 无下单探针 Tool |

禁止把「建议做恢复验证」写成「已经验证恢复」。

## 9. 依据与关联

- code：ACTIVE 服务、健康枚举、priority 枚举、禁止 GENERAL_IT。  
- contract：Tool 边界、HITL、分析优先。  
- simulated：依赖与缓解原则（PENDING-DEP-01 / PENDING-ACT-01）。  

关联见 `related_docs`。analysis 写法见 `OPS-OP-TICKET-ANALYSIS`。
