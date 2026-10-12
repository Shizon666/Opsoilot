---
doc_id: OPS-IR-OFFWINDOW-RELEASE
title: 变更窗口外发布引发回滚复盘
category: INCIDENT_REPORT
source_type: markdown
service: PLATFORM
department: 平台工程
severity: HIGH
created_at: 2026-03-11
visibility: INTERNAL
status: active
version: 1.0.0
---

# 变更窗口外发布引发回滚复盘

虚构叙事单 `OPS-IR-NARR-404`。

## 时间线

窗口外热修入口超时。发布后多服务 504。按回滚手册退回上一版本后恢复。

## 影响

短时全站变慢，不限于支付。证明「只有 Checkout 文档」无法覆盖值班真实事故。

## 根因

窗口外发布未执行检查单，超时配置与网关不一致。

## 行动项

窗口外发布默认升级。回滚后 24 小时内禁止同一构建再发。
