---
doc_id: OPS-RB-CACHE-STAMP
title: 缓存击穿与热点 key 排查手册
category: RUNBOOK
source_type: markdown
service: PLATFORM
department: 平台工程
severity: MEDIUM
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 缓存击穿与热点 key 排查手册

早高峰或促销时缓存失效导致打穿数据库或下游。不是 Checkout 专用 FAQ。

## 现象

接口突然变慢、数据库 QPS 尖峰、同一 key 大量回源、缓存命中率骤降。

## 先看服务健康

看受影响业务服务是否 `DEGRADED`，同时确认是否刚做过缓存清空或预热失败。

## 排查步骤

1. 定位热点 key 与失效策略（TTL 集体到期还是主动 flush）。
2. 临时：对热点 key 加锁回源、延长 TTL、打开空值缓存；禁止无脑全量预热打满带宽。
3. 检查是否与发布、配置变更同时发生。
4. 恢复后记录 key 模式，供复盘，不要把生产 key 中的用户标识写入工单。

## 何时建单 / 升级

命中率持续低于约定阈值或已打穿数据库：建单，优先级 high。需要改集群配置则升级平台值班。
