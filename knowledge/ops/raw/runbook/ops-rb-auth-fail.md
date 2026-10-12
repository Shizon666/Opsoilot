---
doc_id: OPS-RB-AUTH-FAIL
title: Auth Service 登录失败与会话异常排查手册
category: RUNBOOK
source_type: markdown
service: AUTH_SERVICE
department: 运维部
severity: HIGH
created_at: 2026-10-03
updated_at: 2026-10-09
visibility: PUBLIC
status: active
version: 1.1.1
knowledge_role: C3
supersedes: OPS-RB-AUTH-FAILURES
basis:
  - code
  - contract
  - simulated
basis_notes: "AUTH_SERVICE 与健康/priority 枚举见 Backend；个案 vs 全站分支为契约与演示约定；证书仅外链 OPS-RB-CERT-EXPIRY（PENDING-PLT-01）；已删除分钟硬阈值（SLA-01）。"
related_docs:
  - OPS-SM-AUTH
  - OPS-RB-CERT-EXPIRY
  - OPS-RB-CHECKOUT-5XX
  - OPS-RB-ESCALATE
  - OPS-OP-DUTY-P-LEVEL
  - OPS-OP-TICKET-ANALYSIS
  - OPS-SM-OBSERVABILITY
simulation_notice: true
---

# Auth Service 登录失败与会话异常排查手册

本文用于 OpsPilot **模拟运维环境**。稳定 ID 为 `OPS-RB-AUTH-FAIL`（废止草稿 ID 见元数据 `supersedes`）。

## 1. 适用服务与触发条件

| 适用 | 不适用 |
|------|--------|
| 登录失败、会话无法建立、大范围或偶发 401/5xx（登录域） | 收银台入口 5xx → `OPS-RB-CHECKOUT-5XX` |
| 需区分「单账号」与「大范围登录异常」 | 支付通道无结果且无登录问题 → `OPS-RB-PAY-TIMEOUT` |
| | 订单状态不更新 → `OPS-RB-WORKER-BACKLOG` |

单个用户密码错误属于**个案路径**，不是全站故障默认假设。

## 2. 用户可见现象与可取得证据

**现象：** 无法登录、反复掉线、会话建立失败等。

**可取得：** `get_service_status`（`AUTH_SERVICE` 模拟健康）、`search_tickets`、`search_knowledge`。

**不可取得：** 认证审计日志、IdP 后台、证书私钥操作、Prometheus。禁止声称已查询上述系统。

## 3. 初步判断与易混淆鉴别

| 线索 | 判断 | 局限 |
|------|------|------|
| 多用户/全员无法登录 | 全站路径 | 快照不能单独定根因 |
| 单用户、可复现密码错误 | 个案路径 | 勿写成全站事故 |
| `health_status=HEALTHY` | **线索**：可优先排个案；**不能**排除所有认证故障 | seed 常见 HEALTHY 仅为模拟快照 |
| 证书/TLS 线索 | 阅读 `OPS-RB-CERT-EXPIRY`；本篇不写轮转步骤 | PENDING-PLT-01 |
| 与 Checkout 同时告警 | 分开验证两条链路；同时出现只是核查线索，**禁止直接断言依赖故障** | 无调用链证据 Tool |

## 4. 分支排查步骤

### 步骤 A — 影响面分流

- **动作：** 确认是单账号还是多用户/全员；是否特定客户端。
- **前置：** 问题描述涉及登录/会话。
- **预期：** 进入「个案」或「全站」分支。
- **若不同：** 信息不足 → 先澄清影响面，不下根因。

### 步骤 B — 读取 Auth 健康快照

- **动作：** `get_service_status`（`AUTH_SERVICE`）。
- **前置：** 已定位到身份域或需对照。
- **预期：** 得到 `HEALTHY` / `DEGRADED` / `DOWN` 与 summary。
- **若不同：**
  - `HEALTHY` + 单账号 → 走步骤 C（个案）。
  - `HEALTHY` + 多用户仍失败 → **不排除**故障；记录不一致，继续步骤 D 并考虑升级。
  - `DEGRADED`/`DOWN` → 走步骤 D（全站/服务路径）。

### 步骤 C — 个案账号路径

- **动作：** 先澄清该用户的时间窗、是否可复现、是否仅本账号/本客户端，以及是否已确认密码输入无误；**不要**仅凭「登不上」断定根因。说明密码错误、账号锁定等仍可能是用户侧原因。若用户需要重置密码或账号权限类操作：建议其通过组织内**既有**的人工 Support / 账号管理员渠道处理。当前 V1 ops 知识库**没有**账号自助重置操作指南；不要编造联系方式、网址、重置命令或统一「公司自助流程」。
- **前置：** 影响面为单个或极少账号，且无明确全站证据。
- **预期：** 不把个案写成全站故障；不暗示存在可检索的自助专文；若建单，analysis 写明「非全站」。
- **若不同：** 影响面扩大为多用户，或澄清后仍无法区分个案与服务异常 → 转入步骤 D，并按本节及 §7 建议人工进一步核查（非后端强制规则）。
- **priority 建议：** 个案引导类可用 `low` 或 `medium`。

### 步骤 D — 全站 / 服务路径

- **动作：** 基于知识说明需人工核查的方向：认证服务依赖、近期发布、证书/TLS（外链 `OPS-RB-CERT-EXPIRY`，**不扩写**轮转操作）。
- **前置：** 多用户影响，或快照异常，或 HEALTHY 与全站现象冲突。
- **预期：** 列出人工核查项；不编造已确认根因。
- **若不同 / 建议人工进一步核查（建议，非系统强制升级规则）：** 影响范围无法确认、登录异常已涉及多个用户，或现有 Tool/用户描述仍不足以区分「账号个案」与「服务/依赖异常」时，建议人工继续核查或请用户明确是否升级建单（口径同 §7：多用户受阻、快照与现象冲突、高风险操作、用户明确要求升级）。

### 步骤 E — 与 Checkout 并行告警时

- **动作：** 分别按本手册与 `OPS-RB-CHECKOUT-5XX` 收集证据；禁止把支付失败直接归因于登录，也禁止未证明时把 Checkout 502 改绑为 Auth。
- **预期：** 两条独立结论或明确「尚未证明关联」。

## 5. 缓解建议与风险（人工）

原则级建议（PENDING-ACT-01）：由有权限人员核查配置、发布与证书相关项。Agent **不能**执行配置变更、证书操作，也不得绕过写操作确认。

## 6. Agent 能力边界

| 能做 | 能建议 | 不能执行 |
|------|--------|----------|
| 查模拟健康、知识、工单；分支分析 | 升级建单；人工核查方向；个案自助方向 | 查日志；改会话存储；轮转证书；断言依赖根因 |

## 7. 停止条件与升级条件

**停止强行下结论：** 影响面未澄清；已确认为个案且用户不要求升级；应移交证书专册且本篇无更多依据。

**建议升级（无正式 SLA / 无分钟硬阈值）：**

- 多用户或全员登录受阻。
- 快照与现象冲突或证据不足以定位。
- 需证书/配置等高风险人工操作。
- 用户明确要求升级建单。

**priority 建议：** 大范围登录受阻建议 `high` 或 `urgent`；个案建议 `low`/`medium`。勿使用 `critical`。P 级仅为口语参考。

## 8. 恢复验证

| 检查项 | 含义 | 谁验证 |
|--------|------|--------|
| 健康快照变化 | 仅快照变化 | Agent 可复查 status |
| 业务恢复（可登录） | **待验证**；`HEALTHY` ≠ 登录成功 | 用户/人工确认 |

## 9. 依据与关联

code：服务与枚举；contract：Tool/HITL/分支纪律；simulated：依赖与证书外链边界。关联见 `related_docs`。
