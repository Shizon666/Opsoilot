---
doc_id: OPS-RB-DEP-TIMEOUT
title: 上游依赖超时与连接池排查手册
category: RUNBOOK
source_type: markdown
service: MULTI
department: 运维部
severity: HIGH
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 上游依赖超时与连接池排查手册

适用于多个 ACTIVE 服务同时出现超时、连接池打满、线程等待。不要默认当成单一 Checkout 故障。

## 现象

接口 P99 升高、日志出现 connection pool exhausted、upstream timeout、大量 504。可能同时影响 `CHECKOUT_API` 与 `AUTH_SERVICE`。

## 先看服务健康

分别拉取相关服务健康，记录哪些是 `DEGRADED`/`DOWN`。禁止只看一个服务就下结论。

## 排查步骤

1. 列出超时的上游名字（支付网关、会话存储、内部 HTTP），确认是单依赖还是扇出。
2. 检查连接池配置是否刚变更、是否有泄漏（只增不还）。
3. 临时：降低并发、缩短超时、切断有问题的下游；禁止无授权放大连接池后不管泄漏。
4. 与慢查询手册交叉：若超时伴随数据库等待，转 `OPS-RB-DB-SLOW`。

## 何时建单 / 升级

两个及以上服务同时超时：建单绑主要影响面服务，analysis 写明 MULTI 依赖，优先级 high。根因不清 10 分钟内升级。
