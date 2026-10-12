---
doc_id: OPS-SM-INGRESS
title: 平台入口与网关说明
category: SERVICE_MANUAL
source_type: markdown
service: PLATFORM
department: 平台工程
severity: INFO
created_at: 2026-10-03
visibility: INTERNAL
status: active
version: 1.0.0
---

# 平台入口与网关说明

## 职责

入口网关负责 TLS 终止、路由、限流与健康检查。它不是 V1 seed 里的第四个 ACTIVE 业务服务，而是平台层。多服务同时 5xx 时先怀疑入口。

## 依赖

证书、上游 ACTIVE 服务、DNS。入口配置错误会造成「所有业务都挂」的假象。

## 典型故障面

网关 5xx、健康检查误杀、证书问题、超时过短。操作入口配置按发布回滚手册与变更检查单。

## 建单提示

V1 可检索服务仍是三个 ACTIVE code。入口故障在 analysis 写明平台入口，服务绑定选主要对外影响面，禁止绑 `GENERAL_IT`。
