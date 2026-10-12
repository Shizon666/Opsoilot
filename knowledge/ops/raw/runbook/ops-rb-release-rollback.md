---
doc_id: OPS-RB-RELEASE-ROLLBACK
title: 发布后回滚手册
category: RUNBOOK
source_type: markdown
service: PLATFORM
department: 平台工程
severity: HIGH
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 发布后回滚手册

发布后错误率升高、功能回退或配置错误时的止血路径。变更门禁见流程类 `OPS-OP-CHANGE-ROLLBACK`，本篇只写值班怎么回滚。

## 现象

最近一次发布后出现 5xx、登录失败、Worker 不消费，或功能与发布说明不符。

## 先看服务健康

确认受影响服务当前健康，并记下发布时间、版本号、操作人。健康仍 GREEN 但业务错乱，同样可以回滚，不要只看枚举。

## 排查步骤

1. 确认变更是否在窗口内、是否可回滚、是否有数据迁移不可逆。
2. 可逆发布：按平台回滚到上一稳定版本，观察错误率与队列。
3. 不可逆迁移：停止继续放量，升级人工，禁止值班自行「修数据」。
4. 回滚后不要立刻重新发布同一构建；先写 analysis 与复盘入口。

## 何时建单 / 升级

任何生产回滚都必须建单。涉及支付、登录或不可逆迁移：优先级 critical，立即升级。
