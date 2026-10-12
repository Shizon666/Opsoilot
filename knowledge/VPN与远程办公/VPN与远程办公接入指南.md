---
doc_id: XXY-IT-HOW-VPN-001
title: VPN 与远程办公接入指南
version: 1.0.0
status: active
company: 北京小小医信息科技有限公司
owner: 信息技术部
category: howto
visibility: PUBLIC
related_intent: [answer, ticket, human]
rag:
  employee: true
  support: true
  primary: true
audience: [employee, it_support, admin]
related_api:
  - POST /tickets
  - GET /tickets
updated: 2026-10-02
---

# VPN 与远程办公接入指南

## 1. 使用场景

适用于公司 VPN / 远程接入：首次如何使用、连接失败、居家办公上不了内网。

不适用于：把 VPN 当成 GitLab / 数据库 / 开发环境「权限类型」申请；VPN 已通但仍无仓库或库权限（走权限申请）。

## 2. 判断流程

1. 用户要申请 `GITLAB` / `DATABASE` / `DEV_ENV`？→ **permission**（离开本指南）。  
2. 仅问客户端入口、基本自查（账号是否锁定、是否连错环境）？→ **answer**。  
3. 首次开通需 IT 配置，或自查后仍无法连接？→ **ticket**（建议标题含「VPN」；优先级常用 high）。  
4. 开播中或临近开播、疑似多人无法接入？→ **ticket** + **human**。  
5. 「申请 VPN 的 Developer 权限」？→ **answer** 纠正（无此 Permission 类型）后按需 **ticket**。

## 3. 边界条件

- VPN 不是 Permission 三类资源；禁止用 `create_permission` 表达开 VPN。  
- VPN 连通 ≠ 已获仓库 / 库 / 环境授权。  
- 禁止在记录中粘贴预共享密钥或完整客户端配置明文。  
- 禁止指导未批准的个人隧道软件绕过公司接入。

## 4. 示例问题

| 用户说法 | 意图 | Agent 动作 |
|----------|------|------------|
| 第一次用 VPN，客户端怎么装？ | answer | 按知识说明；可不建单 |
| 回家连不上公司网 | ticket | 先可简短 answer 自查；仍失败则 `create_ticket` |
| 帮我申请 VPN Developer 权限 | answer → ticket | 纠正后引导工单，不调 permission |
| VPN 通了克隆仓库还是 403 | permission | `create_permission`（GITLAB） |
| 今晚直播现场大面积上不了内网 | ticket + human | 建紧急工单并明确转值班 |
