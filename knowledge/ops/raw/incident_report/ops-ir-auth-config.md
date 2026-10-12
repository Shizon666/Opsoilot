---
doc_id: OPS-IR-AUTH-CONFIG
title: 配置错误导致 Auth 全员登录失败复盘
category: INCIDENT_REPORT
source_type: markdown
service: AUTH_SERVICE
department: 运维部
severity: CRITICAL
created_at: 2026-04-09
visibility: INTERNAL
status: active
version: 1.0.0
---

# 配置错误导致 Auth 全员登录失败复盘

本文是结构化复盘，不是工单行复制。叙事工单号 `OPS-IR-NARR-401` 为虚构引用。

## 时间线

变更窗口内错误地把会话存储地址指到未初始化实例。发布后 3 分钟全员登录失败。回滚配置后 8 分钟恢复。

## 影响

员工无法登录内部系统；Checkout 因无会话间接受阻，但根因在 Auth 配置。

## 根因

配置项缺少校验，错误地址仍可发布。值班最初误判为「密码重置高峰」。

## 行动项

发布回滚手册增加「登录成功率」门禁。配置变更必须走检查单。禁止把连接串写入 Chat。
