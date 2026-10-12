---
doc_id: OPS-OP-TLS-VS-APP
title: 证书 TLS 异常与应用故障鉴别
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 信息安全
severity: HIGH
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C6
basis:
  - contract
  - simulated
basis_notes: "鉴别逻辑对齐已有 Runbook 边界；证书更换步骤不扩写（PENDING-PLT-01）；Agent 无证书查询 Tool；禁止工单粘贴私钥（OPS-SG-SECRETS）。"
related_docs:
  - OPS-RB-CERT-EXPIRY
  - OPS-RB-AUTH-FAIL
  - OPS-RB-CHECKOUT-5XX
  - OPS-RB-INGRESS-5XX
  - OPS-IR-CERT-ROTATION
  - OPS-SG-SECRETS
  - OPS-SG-AGENT-TOOL-BOUNDARY
  - OPS-OP-IMPACT-ESCALATE
simulation_notice: true
---

# 证书 TLS 异常与应用故障鉴别

本文用于 OpsPilot **模拟运维环境**。在「登不上 / 付不了款 / HTTPS 报错」交织时，帮助 Agent **选对手册**，避免把 TLS 问题当成应用 5xx 回滚，或把应用故障当成换证书。

## 1. 独立价值

`OPS-RB-CERT-EXPIRY` 已覆盖证书排查提纲；本篇不重复更换步骤，只提供**鉴别树**与停止条件。

## 2. 可取得 / 不可取得

**可取得：** 用户描述（浏览器证书无效、TLS error、握手失败）；相关服务模拟健康；知识检索。  
**不可取得：** 证书到期日自动探测、私钥、mTLS 配置后台。禁止声称已检查证书链。

## 3. 鉴别分支

### A — 明确 TLS/证书现象

用户提到证书无效、过期、握手失败 → 主路径 `OPS-RB-CERT-EXPIRY`；私钥操作必须人工（`OPS-SG-SECRETS` / `OPS-SG-AGENT-TOOL-BOUNDARY`）。

### B — 应用 HTTP 5xx，无 TLS 线索

→ `OPS-RB-CHECKOUT-5XX` 或入口 `OPS-RB-INGRESS-5XX`，**不要**建议换证书。

### C — 登录失败为主

先 `OPS-RB-AUTH-FAIL` 分流个案/全站；仅当出现 TLS 线索再交叉证书手册。禁止未证明时把 Checkout 502 改绑 Auth。

### D — 同时出现

分开记录两条线索；结论写「尚未证明同一根因」；影响大则按 `OPS-OP-IMPACT-ESCALATE` 建议升级。

## 4. 复盘引用

历史轮转遗漏见模拟复盘 `OPS-IR-CERT-ROTATION`（非生产事故记录）。

## 5. 关联

见 `related_docs`。证书操作细节仍以 `OPS-RB-CERT-EXPIRY` 为准（原则级，无逐步私钥命令）。
