---
doc_id: OPS-SG-PII-TICKET
title: 工单与 Chat 中的敏感信息处理
category: SECURITY_GUIDELINE
source_type: markdown
service: PLATFORM
department: 信息安全
severity: HIGH
created_at: 2026-10-03
visibility: PUBLIC
status: active
version: 1.0.0
---

# 工单与 Chat 中的敏感信息处理

## 红线

工单标题、描述、analysis、Chat 消息不得包含密码、短信验证码、完整身份证、完整银行卡、密钥、连接串。

## 允许

可写脱敏后的用户标识（如后四位）、`request_id`、大致时间窗、服务 code。

## Agent

发现用户粘贴密钥时，应提示删除并改写，不得把密钥再次写入建议步骤。不得用知识库教如何绕过审批。
