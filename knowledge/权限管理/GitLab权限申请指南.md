---
doc_id: XXY-IT-ACC-GL-001
title: GitLab 代码仓库权限申请指南
version: 1.0.0
status: active
company: 北京小小医信息科技有限公司
owner: 信息技术部
category: access
visibility: PUBLIC
related_intent: [permission, answer, human]
rag:
  employee: true
  support: true
  primary: true
audience: [employee, it_support, admin]
resource_type: GITLAB
related_api:
  - POST /permissions
  - GET /permissions
updated: 2026-10-02
---

# GitLab 代码仓库权限申请指南

## 1. 使用场景

适用于申请公司 GitLab **仓库访问级别**（`resource_type=GITLAB`）：只读查阅、日常开发推送、仓库管理。

不适用于：GitLab 网页都登不进（先账号/VPN）；装客户端软件（软件指南）；用工单「请直接加权限」绕过审批。

级别：`READ`（只读） / `DEVELOPER`（日常开发） / `ADMIN`（仓库管理，严格控制）。

## 2. 判断流程

1. 现象是「无仓库权限 / 403 / 要加某项目 Developer」？→ **permission**：收集 `resource_name`（仓库路径）、`permission_level`、`reason` 后 `create_permission`。  
2. 仅问级别含义、要不要审批？→ **answer**（说明仍须系统申请，答复 ≠ 已授权）。  
3. 要 `ADMIN`、或角色与仓库明显不符、或要求跳过审批？→ 仍可提交申请，但必须 **human**（不得暗示会自动通过）。  
4. 无法登录账号或纯网络问题？→ **ticket** / 账号或 VPN 指南，不建 Permission。  
5. 缺仓库名或级别？→ 先追问，再调 Tool。

## 3. 边界条件

- 必须走 Permission + Approval；禁止 Ticket 代开仓库权限。  
- `resource_name` 填具体仓库路径，禁止只写「所有仓库」「生产」。  
- 禁止无关仓库「先开着备用」。  
- 申请与对话中不得粘贴私人 Token。  
- 获批前不得声称「已经可以 push」。

## 4. 示例问题

| 用户说法 | 意图 | Agent 动作 |
|----------|------|------------|
| 直播中台仓库要 Developer | permission | `create_permission`（GITLAB / DEVELOPER） |
| clone 提示 access denied，是工单还是权限？ | permission | 无权限→permission；先确认非登录/VPN 问题 |
| 产品只看代码申请哪一级？ | answer | 通常 READ；确认后可再 permission |
| 直接给我 Admin 吧，领导同意了 | human | 可引导正式申请，明确须人工审批 |
| GitLab 登录页都进不去 | ticket | 账号/网络工单，非本指南开通 |
