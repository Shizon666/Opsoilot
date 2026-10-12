---
doc_id: XXY-IT-RB-SUP-001
title: IT Support 内部处理规范
version: 0.1.0-outline
status: outline
company: 北京小小医信息科技有限公司
owner: 信息技术部
category: runbooks
visibility: INTERNAL
related_intent: [human, ticket, permission]
rag:
  employee: false
  support: true
  primary: true
audience: [it_support, admin]
related_api:
  - PATCH /tickets/:id
  - POST /permissions/:id/approve
  - POST /permissions/:id/reject
updated: 2026-10-01
---

# IT Support 内部处理规范

> 状态：大纲（正文待写）  
> **visibility: INTERNAL** — 不进入 Employee RAG；仅 Support/Admin 检索通道

## 1. 文档目的

- 什么情况必须人工介入
- 权限审批检查要点
- Audit / 留痕要求（业务表述，对应系统已写 audit）

## 2. 适用范围

- 【待写】IT Support / Admin 处理 Ticket 与 Permission 审批
- 【待写】Employee 会话不得召回本文审批检查细节

## 3. 必须人工介入（大纲）

1. 生产数据库访问、任意 ADMIN  
2. 账号盗用、代人重置密码、跳过审批请求  
3. 医学直播进行中的关键故障  
4. 申请人与资源明显不匹配、用途不清  
5. 制度未覆盖的新系统  
6. 驳回争议升级

## 4. 工单处理要点（大纲）

- 核对是否误用 Ticket（本应 Permission）→ 纠正引导
- 优先级与直播窗口
- 状态流转符合业务预期；需用户补充则等待用户
- 处理说明可追溯

## 5. 审批检查清单（大纲）

- [ ] resource_type / resource_name / permission_level / reason 完整
- [ ] 对照对应 access 指南与最小权限
- [ ] 高风险项身份/用途复核
- [ ] 通过或驳回原因可理解
- [ ] 不存在无 Approval 记录的私下开通
- [ ] 需要时查阅 `权限管理/权限与审批关系矩阵.xlsx`（非 RAG 主数据）

## 6. Audit 要求（大纲）

- 申请创建、审批通过/驳回须落在系统记录中
- 禁止口头授权替代 Approval
- 工单重要状态变更应可追踪（与现有 ticket 审计能力对齐）
- 不编造外部法规审计条款

## 7. 限制条件（大纲）

- 禁止自动 approve 高风险级别
- 禁止索要用户现有密码
- 禁止在记录中粘贴密钥明文

## 8. 示例问题（Support 侧）

1. 用户称领导已同意，能否直接通过生产库申请？
2. 开播中断工单已建，Support 先做什么？
3. 权限申请误建成工单如何纠正？
4. Agent 可否自行批准 DEVELOPER？
5. 驳回理由怎样写才规范？

## 9. 相关文档

- `服务目录/IT服务目录与入口指引.md`
- `制度规范/IT服务请求工单规范.md`
- `制度规范/信息系统访问与权限管理规范.md`
- `权限管理/GitLab权限申请指南.md`
- `权限管理/数据库访问权限申请指南.md`
- `权限管理/开发环境权限申请指南.md`
- `权限管理/权限与审批关系矩阵.xlsx`
- `常见问题/常见IT问题处理指南.md`
