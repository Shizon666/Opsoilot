---
doc_id: OPS-OP-INCIDENT-MINSET
title: 报障信息最低集
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: INFO
created_at: 2026-10-03
visibility: PUBLIC
status: active
version: 1.0.0
---

# 报障信息最低集

## 适用范围

员工报障与 Support 建故障单时，信息低于本最低集则无法有效检索知识或对照健康。

## 最低字段

1. 时间窗（开始时间、是否仍在发生）。
2. 影响面（个人 / 部门 / 全站；是否影响成交或登录）。
3. 服务猜测（三选一 ACTIVE：Checkout / Auth / Worker；不确定就写现象，不要填 `GENERAL_IT`）。
4. 是否可复现、是否仅某一端。
5. `request_id`（如有）。

## 禁止

不要为凑字数粘贴密码、短信验证码、完整日志密钥。不要用「打不开」代替现象。
