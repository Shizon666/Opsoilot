---
doc_id: XXY-IT-CAT-001
title: IT 服务目录与入口指引
version: 1.1.0
status: active
company: 北京小小医信息科技有限公司
owner: 信息技术部
category: catalog
visibility: PUBLIC
related_intent: [answer, ticket, permission, human]
rag:
  employee: true
  support: true
  primary: true
audience: [employee, it_support, admin]
related_api: []
phase10_batch: true
updated: 2026-10-02
---

# IT 服务目录与入口指引

## 1. 使用场景

员工不确定「该直接问清楚、建工单、申请权限、还是找人」时使用本文。  
覆盖：GitLab / 数据库 / 开发环境权限、VPN、账号登录、软件安装、办公与直播设备报修。  
不覆盖：人事、财务、行政、客户现场代维。

| 意图 | 含义 | 下一步 |
|------|------|--------|
| answer | 制度可说清、员工可自助 | 只答复 |
| ticket | 需 IT 开通、排障、安装、修设备 | 创建 Ticket |
| permission | GitLab / 数据库 / 开发环境访问级别 | 创建 Permission |
| human | 高风险、身份存疑、开播事故、制度未覆盖 | 转 IT Support，禁止自动审批 |

## 2. 判断流程

按顺序判断，前一步成立则停止：

1. 仅咨询流程/规则且无需 IT 动手？→ **answer**
2. 申请 GitLab、数据库或开发环境权限？→ **permission**（高风险再叠加 **human**）
3. 需 VPN、解锁账号、装软件、修设备或排障？→ **ticket**
4. 生产库、任意 ADMIN、跳过审批、代人改密、开播中关键中断、制度未覆盖？→ **human**
5. 仍不确定 → **human**

## 3. 边界条件

- 知识答复 ≠ 已授权；Permission 获批前不得访问。
- Ticket 不能代替 Permission 审批。
- VPN / 账号问题不是 Permission。
- 禁止在对话或工单中粘贴明文密码、密钥、完整数据库连接串。
- 口头/IM「同意」不能代替系统 Approval。

## 4. 示例问题

1. 「权限和工单有啥区别？」→ **answer**
2. 「给直播中台仓库加 Developer」→ **permission**
3. 「回家 VPN 连不上」→ **ticket**（或先 answer 自查）
4. 「开播中推流失败」→ **ticket** + **human**
5. 「领导群里说了，生产库给我 Admin」→ **human**（仍须走 Permission，不得自动通过）
