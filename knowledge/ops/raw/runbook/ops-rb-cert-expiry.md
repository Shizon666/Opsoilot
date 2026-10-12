---
doc_id: OPS-RB-CERT-EXPIRY
title: 证书过期与 TLS 失败排查手册
category: RUNBOOK
source_type: markdown
service: PLATFORM
department: 信息安全
severity: CRITICAL
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 证书过期与 TLS 失败排查手册

TLS 握手失败、浏览器报证书无效、服务间 mTLS 失败。高危更换步骤必须人工，Agent 只给升级建议。

## 现象

客户端 TLS error、证书过期告警、登录或支付在 HTTPS 层失败。可能伴随 Auth 全员失败。

## 先看服务健康

相关服务可能显示 `DOWN`。先确认是证书问题还是应用 5xx，避免按错手册回滚应用。

## 排查步骤

1. 核对证书到期时间、域名、是否漏轮转中间证书。
2. 按安全规范更换证书，禁止把私钥贴进 Chat 或工单。
3. 更换后验证握手与依赖服务，再观察登录与支付。
4. 轮转遗漏的历史教训见复盘 `OPS-IR-CERT-ROTATION`。

## 何时建单 / 升级

证书将在 7 天内到期或已导致 TLS 失败：立即建单并升级信息安全/平台，优先级 critical。
