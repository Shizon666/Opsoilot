---
doc_id: OPS-IR-CACHE-WARMUP
title: 缓存预热不足导致早高峰击穿复盘
category: INCIDENT_REPORT
source_type: markdown
service: PLATFORM
department: 平台工程
severity: MEDIUM
created_at: 2026-07-02
visibility: INTERNAL
status: active
version: 1.0.0
---

# 缓存预热不足导致早高峰击穿复盘

虚构叙事单 `OPS-IR-NARR-405`。

## 时间线

凌晨维护清空热点缓存但未预热。早高峰集体回源，数据库打满，接口超时。对热点 key 加锁回源后逐渐恢复。

## 影响

多个读接口变慢。支付通道本身正常，但商品页打不开导致下单下降。

## 根因

维护手册只有「清空」没有「预热完成标准」。

## 行动项

缓存击穿 Runbook 补充预热完成门禁。清空缓存列为高危，必须人工确认。
