---
doc_id: OPS-OP-MULTI-SERVICE-TRIAGE
title: 多服务同时异常的上下游影响判断
category: OPERATION_PROCESS
source_type: markdown
service: MULTI
department: 运维部
severity: HIGH
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C6
basis:
  - code
  - contract
  - simulated
basis_notes: "三 ACTIVE 服务与健康枚举见 seed；依赖边为模拟（PENDING-DEP-01）；技术超时细则外链 OPS-RB-DEP-TIMEOUT；建单仍绑单一 ACTIVE service_id。"
related_docs:
  - OPS-RB-DEP-TIMEOUT
  - OPS-SM-SERVICE-CATALOG
  - OPS-SM-CHECKOUT
  - OPS-SM-AUTH
  - OPS-SM-ORDER-WORKER
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-RB-ESCALATE
simulation_notice: true
---

# 多服务同时异常的上下游影响判断

本文用于 OpsPilot **模拟运维环境**。当多个 ACTIVE 服务同时 `DEGRADED`/`DOWN` 或用户现象跨域时，指导 Agent **如何取证、如何选主服务建单、如何避免一次归因**。

## 1. 独立价值

`OPS-RB-DEP-TIMEOUT` 偏连接池/上游超时技术路径；本篇偏 **分诊与影响判断**，不编造依赖时序。

## 2. 适用

- `list_services` 显示两个及以上业务服务异常；或  
- 用户同时报登录与支付/订单问题。

## 3. 步骤

### A — 分别拉取健康快照

对 `CHECKOUT_API`、`AUTH_SERVICE`、`ORDER_WORKER` 分别 `get_service_status`（或列表对照）。记录各自 `health_*`，标明模拟快照。

### B — 按用户主现象选「主绑定服务」

| 主现象 | 建议绑定（建单时） |
|--------|-------------------|
| 下单/支付入口错误 | `CHECKOUT_API` |
| 登录/会话 | `AUTH_SERVICE` |
| 支付成功后订单不更新 | `ORDER_WORKER` |

analysis 中写明其它服务快照；**禁止**发明第四 ACTIVE code；禁止默认 `GENERAL_IT`。

### C — 依赖叙事（模拟，非已证实根因）

可说明「可能存在上下游影响」（PENDING-DEP-01），但必须写：**未用调用链 Tool 证实**。需要技术超时时交叉 `OPS-RB-DEP-TIMEOUT`。

### D — 升级

多服务同时异常且业务受阻 → 按 `OPS-OP-IMPACT-ESCALATE` / `OPS-RB-ESCALATE` 建议人工；勿拆成互不相干的猜测硬下多个根因。

## 4. 停止

证据只够列出快照对比时，停止编造「谁拖垮谁」；进入澄清或升级。

## 5. 关联

见 `related_docs`。
