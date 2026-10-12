---
doc_id: OPS-RB-PAY-TIMEOUT
title: 支付通道超时与切备手册
category: RUNBOOK
source_type: markdown
service: CHECKOUT_API
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
basis_notes: "建单绑定 CHECKOUT_API 与健康/priority 枚举见 Backend；Tool/HITL 见 Agent；通道依赖与切备为原则级模拟建议（PENDING-DEP-01 / PENDING-ACT-01）；已删除分钟硬阈值（SLA-01）。"
related_docs:
  - OPS-SM-CHECKOUT
  - OPS-RB-CHECKOUT-5XX
  - OPS-RB-WORKER-BACKLOG
  - OPS-RB-ESCALATE
  - OPS-OP-TICKET-ANALYSIS
  - OPS-SG-SECRETS
  - OPS-SG-PII-TICKET
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# 支付通道超时与切备手册

本文用于 OpsPilot **模拟运维环境**。建单绑定 `CHECKOUT_API`，禁止默认 `GENERAL_IT`。入口层大面积 **HTTP 5xx** 仍以 `OPS-RB-CHECKOUT-5XX` 为准，不要与本篇混用。

## 1. 适用服务与触发条件

| 适用 | 不适用（应转向） |
|------|------------------|
| 用户已进入支付，**长时间无支付结果**；或用户/客服描述通道 timeout、未知状态 | 提交订单即返回 **5xx/502/504** → `OPS-RB-CHECKOUT-5XX` |
| 收银台相关接口**多为 200**，但支付单处于处理中/无终态 | 支付成功后订单状态长期不更新 → `OPS-RB-WORKER-BACKLOG` |
| 需讨论是否由**有权限人工**评估切备（本篇不授权 Agent 执行） | 仅登录失败 → `OPS-RB-AUTH-FAIL` |

不得仅凭口语「付不了款」直接判定为通道超时；不得假设仓库未定义的支付错误码表或通道 SLA。

## 2. 初始证据与需向用户澄清的问题

**可取得（Agent Tool）：**

- `list_services` / `get_service_status`：`CHECKOUT_API` 模拟 `health_status` / `health_summary`
- `search_tickets`、`search_knowledge`

**不可取得：** 通道后台、成功率大盘、真实日志、Prometheus、商户密钥材料。禁止声称「已查询通道监控/已看到成功率曲线」。

**建议澄清（无答案则不下根因）：**

1. 是否已进入支付页/选完通道？相关接口是否仍返回 200，还是出现 5xx？
2. 失败是否集中在某一通道、银行、客户端或时段？（用户可知范围内）
3. 是首次失败还是持续多笔？是否影响多人？
4. 是否已有同事提到「已切备」或变更窗口内的通道配置变更？（仅作线索，Agent 无法核验变更系统）

## 3. 初步判断与易混淆鉴别

| 线索 | 判断 | 局限 |
|------|------|------|
| 无接口 5xx、偏「支付无结果 / timeout」 | 本手册主路径 | 无通道侧 Tool，不能证实根因在通道 |
| 明确入口 5xx | 转 `OPS-RB-CHECKOUT-5XX` | — |
| `CHECKOUT_API` 为 `HEALTHY` 仍大面积无结果 | **线索**：可优先怀疑通道侧，而非立刻建议回滚应用 | 快照 ≠ 业务恢复；也不能单凭 HEALTHY 排除 Checkout 问题 |
| `DEGRADED`/`DOWN` 且摘要含 5xx | 可能两路径并存：先确认有无 HTTP 5xx | 分开取证，禁止一次归因 |
| 订单状态不更新但用户称支付已成功 | Worker 路径 | 见 `OPS-RB-WORKER-BACKLOG` |

## 4. 分支排查步骤

### 步骤 A — 排除入口 5xx

- **动作：** 确认用户侧是否看到 HTTP 5xx/502/504。
- **前置：** 报障涉及支付/付不了款。
- **预期：** 无 5xx → 继续本手册；有 5xx → **停止本手册主路径**，改用 `OPS-RB-CHECKOUT-5XX`。
- **若不同：** 说不清 → 先澄清，不强行绑「通道超时」结论。

### 步骤 B — 读取 Checkout 健康快照

- **动作：** `get_service_status`（`CHECKOUT_API`）。
- **前置：** 步骤 A 倾向通道路径，或需对照。
- **预期：** 得到模拟快照。
- **若不同：**
  - `HEALTHY` + 多用户无支付结果 → 记录「快照正常但业务未恢复待验证」，继续澄清通道/时段，**不要**据此断言已排除故障。
  - `DEGRADED`/`DOWN` → 记载摘要，仍须用步骤 A 区分是否入口 5xx；禁止把 DEGRADED 直接写成通道根因。

### 步骤 C — 影响面与集中度（用户可知信息）

- **动作：** 汇总是否单通道/单银行/单时段/多用户（仅基于用户描述与可见工单，不编造通道列表）。
- **前置：** 已排除或并行处理入口 5xx。
- **预期：** 形成「局部 vs 大范围」描述，供升级建议使用。
- **若不同：** 信息不足 → 明确「证据不足以定位通道」，进入停止/升级条件，禁止编造通道名。

### 步骤 D — 历史工单对照

- **动作：** `search_tickets`（如支付、超时、通道等关键词）。
- **预期：** 可见历史单或明确无命中；禁止编造 `ticket_no`。
- **若不同：** 无命中 → 如实说明。

### 步骤 E — 人工缓解方向（原则级；Agent 不可执行）

- **动作：** 说明可由**有权限运维人员**评估：是否查阅切备记录、是否在授权下切备、切备后如何观察业务结果。引用 PENDING-ACT-01：无逐步切备命令、无默认授权。
- **前置：** 倾向通道侧且影响面需处理。
- **预期：** 用户/值班理解 Agent **不能**执行切备；密钥不得写入 Chat/工单（见 `OPS-SG-SECRETS` / `OPS-SG-PII-TICKET`）。
- **若不同：** 无切备授权或不知如何操作 → 建议升级人工，不假装已切备。

## 5. 缓解建议与风险（人工）

原则级建议（PENDING-ACT-01），**不是** Agent 可执行步骤：

- 评估是否切备用通道；避免连续来回切换。
- 切备后需人工/用户侧确认支付能否完成（Agent 无成功率 Tool）。
- **风险：** 误切备或密钥泄露；在 Chat 粘贴商户私钥属禁止项。

## 6. Agent 能力边界

| 能做 | 能建议 | 不能执行 |
|------|--------|----------|
| 查模拟健康、知识、可见工单；分流 5xx vs 通道 | 是否升级建单；人工核查/切备评估方向 | 查通道后台；执行切备；回滚应用；绕过写操作确认；声称已看成功率 |

写操作仅在用户明确升级且 HITL 确认后。咨询默认不建单。

## 7. 停止条件与升级条件

**可停止强行下结论：**

- 已确认为入口 5xx 并移交 `OPS-RB-CHECKOUT-5XX`。
- 用户无法提供是否 5xx / 影响面，需继续澄清。
- 用户只要分析、明确不升级。

**建议升级（建议，非正式 SLA，无分钟硬阈值）：**

- 多用户支付无结果或成交明显受阻。
- 已倾向通道路径，但现有 Tool 无法定位，需有权限人员查通道/变更。
- 需要切备或其它高风险人工操作，且当前无授权上下文。
- 用户明确要求建单/升级。

**priority 建议：** 多用户支付受阻建议 `high` 或 `urgent`；局部可绕过建议 `medium`。仅用 `low`/`medium`/`high`/`urgent`。P 级不是工单 API 字段。

## 8. 恢复验证

| 状态 | 含义 | 谁验证 |
|------|------|--------|
| 服务健康改善 | 仅模拟 `health_*` 变化 | Agent 可复查 status |
| 业务恢复待验证 | 支付能否成功完成：**待验证**；`HEALTHY` ≠ 支付成功 | 用户/人工确认 |
| 业务恢复已验证 | 仅当用户或有权限人员**明确反馈**支付已恢复 | Agent 不得自行宣称已验证 |

禁止把「建议观察」写成「已验证恢复」；禁止编造成功率数字。

## 9. 依据与关联

- code：ACTIVE 服务、健康枚举、priority、禁止 GENERAL_IT。  
- contract：Tool/HITL、与 CHECKOUT-5XX 分流。  
- simulated：通道依赖、切备原则（PENDING-DEP-01 / PENDING-ACT-01）。  

关联见 `related_docs`。
