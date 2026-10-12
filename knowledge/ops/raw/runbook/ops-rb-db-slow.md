---
doc_id: OPS-RB-DB-SLOW
title: 慢查询导致接口超时排查手册
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

# 慢查询导致接口超时排查手册

数据库慢查询拖垮接口超时。禁止在 Chat 中粘贴完整 SQL 里的生产数据行。

## 现象

接口超时与数据库等待同时出现；CPU 或锁等待升高；个别接口远慢于基线。

## 先看服务健康

先确认业务服务健康，再判断是应用池满还是数据库本身慢。不要用重启应用掩盖慢 SQL。

## 排查步骤

1. 从可观测约定取出 `request_id`，对到慢查询样本（脱敏）。
2. 看是否缺索引、执行计划回退、统计信息过期、长事务。
3. 临时：杀明显无业务价值的长查询、限流写路径；禁止值班直接删表或关防火墙。
4. 需要改索引或下线语句时升级 DBA/平台，不在本手册执行 DDL。

## 何时建单 / 升级

慢查询已造成对外超时：建单绑受影响业务服务，analysis 注明平台数据库。涉及 DDL 或杀连接批量操作必须升级。
