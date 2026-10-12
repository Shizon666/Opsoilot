---
doc_id: XXY-IT-HOW-COM-001
title: 常见 IT 问题处理指南
version: 0.1.0-outline
status: outline
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
updated: 2026-10-01
---

# 常见 IT 问题处理指南

> 状态：大纲（正文待写）  
> 覆盖：过渡索引；VPN、登录、软件、设备、数据安全等**优先引用专篇**，本篇不注水扩写 FAQ。

## 1. 文档目的

- 常见问题：直接回答 vs 创建 Ticket vs 转人工
- 明确上述问题**默认不走** Permission API

## 2. 适用范围

- 【待写】VPN 开通/故障、办公账号登录、密码重置路径、标准/非标软件安装
- 【待写】医学直播现场网络与账号应急（优先级联动工单规范）
- 【待写】不适用：GitLab / Database / DevEnv 授权

## 3. 分类处理（大纲）

### 3.1 VPN

| 情况 | intent |
|------|--------|
| 询问客户端/入口 | answer |
| 首次开通或排查后仍失败 | ticket |
| 开播中大面积中断 | ticket + human |

### 3.2 登录失败 / 账号

| 情况 | intent |
|------|--------|
| 自助重置路径说明 | answer |
| 锁定需解锁 | ticket |
| 代他人重置 / 疑似盗用 | human |

### 3.3 软件安装

| 情况 | intent |
|------|--------|
| 标准清单内自助说明 | answer |
| 需 IT 安装或例外审批安装 | ticket |
| 明确禁止类软件 | answer（拒绝） |

## 4. 流程（大纲）

1. 对照服务目录排除 Permission 类诉求  
2. 能自助 → `answer`  
3. 需 IT 操作 → Ticket（优先级按工单规范）  
4. 身份核验/盗用/开播应急 → `human`

## 5. 限制条件（大纲）

- 禁止收集或回传用户明文密码
- 禁止将 VPN/账号问题建成 Permission
- 禁止未核验身份为他人解锁
- 禁止在工单中粘贴密钥

## 6. 示例问题

1. 回家连不上公司网，要申请什么权限？
2. 密码忘了怎么处理？
3. 能帮开会中的同事重置密码吗？
4. 安装某某设计软件走什么流程？
5. VPN 通了但 GitLab 403，下一步？

## 7. 相关文档

- `服务目录/IT服务目录与入口指引.md`
- `制度规范/IT服务请求工单规范.md`
- `账号登录/账号与登录处理指南.md`
- `VPN与远程办公/VPN与远程办公接入指南.md`
- `办公与直播设备/办公与直播设备报修指引.md`
- `软件安装/标准软件安装与例外申请指南.md`
- `数据安全/数据安全与敏感信息处理须知.md`
- `权限管理/GitLab权限申请指南.md`
- `作业手册/IT-Support内部处理规范.md`
