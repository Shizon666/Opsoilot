---
doc_id: XXY-IT-POL-TKT-001
title: IT 服务请求（工单）申请规范
version: 1.1.0
status: active
company: 北京小小医信息科技有限公司
owner: 信息技术部
category: policies
visibility: PUBLIC
related_intent: [ticket, answer, human]
rag:
  employee: true
  support: true
  primary: true
audience: [employee, it_support, admin]
related_api:
  - POST /tickets
  - GET /tickets
phase10_batch: true
updated: 2026-10-02
---

# IT 服务请求（工单）申请规范

## 1. 使用场景

需要 IT 动手处理，且**不是** GitLab / 数据库 / 开发环境权限申请时，使用工单（Ticket）。

典型：VPN 开通或故障、账号锁定解锁、软件安装、办公/会议/直播设备报修。

优先级（员工申报，Support 可纠正）：`low` | `medium` | `high` | `urgent`。  
开播进行中的关键故障默认 **urgent**，并转人工。

## 2. 判断流程

1. 是否三类资源权限（GITLAB / DATABASE / DEV_ENV）？→ 否走工单；是 → **permission**（离开本文）
2. 仅问「要不要建单 / 优先级怎么选 / 标题怎么写」？→ **answer**
3. 需 IT 执行配置、开通、排障、安装、现场支持？→ **ticket**（`create_ticket`）
4. 开播中关键中断、代人改密、身份不清？→ **ticket** 可建，同时 **human**
5. 查询「我的工单」→ 调业务查询，不靠本文编造列表

建单建议：标题 `【场景】现象`；描述含现象、影响范围、是否直播场次、已尝试步骤。

## 3. 边界条件

- **应当用工单**：VPN、账号登录/解锁、软件安装、设备报修等。
- **不得用工单代替**：GitLab / 数据库 / 开发环境授权 → Permission。
- 禁止写入：明文密码、令牌、完整连接串；「直接开生产库 Admin」类指令（应改 Permission，高风险 human）。
- 人事/财务/行政 → 非 IT 渠道，不建 IT 工单。

## 4. 示例问题

1. 「要不要给我建个单？」→ 先判断：能自助则 **answer**，需 IT 则 **ticket**
2. 「VPN 连不上，帮建单」→ **ticket**（建议 title=`VPN 故障`，priority=`high`）
3. 「会议室投屏坏了」→ **ticket**
4. 「今晚开播推流机黑屏」→ **ticket** + **human**（urgent）
5. 「工单里写一下数据库密码方便处理」→ **answer**（禁止）后引导安全描述现象
