# OpsPilot — 数据库设计

> Version: v1.2（V1 产品化差集）  
> Status: Confirmed — **V1 表差集以 `docs/phases/PHASE_A_V1_CONTRACT.md` 为准**  
> Project: OpsPilot — AI 运维故障工单助手（原「企业 IT 服务 Agent」叙事降级）  
> Database: PostgreSQL  
> ORM: GORM  
> Core Principle: **业务优先，Agent 第二；业务面完整，实现复杂度最小。**
>
> 11 张表 DoD **不再适用于 V1**。V1 核心表：`roles/users/services/tickets/audit_logs`。  
> `access_requests` / `approvals` **Legacy 冻结**（不删）。  
> `ticket_comments` / `role_resources` / `user_resources` / `knowledge_documents` **V1 不建**。  
> Agent 不直接访问 PostgreSQL。

---

# 1. 文档目的

本文档回答：

1. OpsPilot 当前有哪些核心业务数据？
2. 为什么需要这些表？
3. Ticket 状态如何控制？
4. AccessRequest 和 Approval 如何协作？
5. Onboarding 如何利用 RoleResource / UserResource？
6. KnowledgeDocument 如何服务 RAG？
7. AuditLog 为什么存在？
8. Agent 和 PostgreSQL 的边界是什么？
9. 哪些数据由 Backend 控制？
10. 哪些复杂设计当前明确不做？

本文档不负责定义：

- HTTP API
- LangGraph Graph
- Agent Prompt
- React 页面
- Milvus Collection 内部结构
- Docker 部署细节

---

# 2. 数据库设计原则

## 2.1 数据库是业务事实源

```text
Agent Decision  → 不确定（意图）
Backend Data    → 确定（事实）
```

例如 Agent 判断“用户想申请 GitLab Developer”，只有 Backend 完成校验并写入后，`access_requests.permission_level = "DEVELOPER"` 才成立。

> Agent 产生业务动作意图，Backend 产生最终业务事实。

## 2.2 克制原则

- 不增加新表、新业务对象
- 不为“以后可能有用”预留大量字段
- 不做通用 ITSM / 完整 IAM / 复杂审批流 / 完整审计平台
- 每张表必须能回答一个明确业务问题

---

# 3. 最终表范围

## 3.1 V1 核心业务表（必须保留并演进）

```text
users
roles
services      # + health_*（Phase B）
tickets       # + analysis（Phase B）；不做 related_ticket_id
audit_logs
```

## 3.2 Legacy 表（已建，冻结）

```text
access_requests
approvals
```

## 3.3 V1 明确不建

```text
ticket_comments
role_resources
user_resources
knowledge_documents
```

## 3.4 关系概览（V1）

```text
Role ── User ── Ticket ── Service（含模拟 health）
User / Agent / System ── AuditLog
AccessRequest ── Approval     # Legacy，不进主链
```

---

# 4. ID 与通用字段

所有业务表主键使用 UUID。

```text
id          = 业务对象 ID
request_id  = 一次请求 ID（审计串联，不是业务主键）
thread_id   = 一次会话 ID（Short-term Memory，不进业务表）
```

三者不能混用。

除特殊说明外，业务表包含：

```text
id
created_at
updated_at   # 审计类 append-only 表可不含 updated_at
```

时间类型统一：`TIMESTAMPTZ`（UTC）。

---

# 5. users

## 5.1 用途

登录身份、RBAC、Ticket 请求人/负责人、AccessRequest 申请人、Approval 审批人，以及 Long-term Memory 的基础身份数据。

## 5.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 用户 ID |
| name | VARCHAR(100) | NOT NULL | 用户姓名 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 企业邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| department | VARCHAR(100) | NOT NULL | 部门（员工上下文，非授权依据） |
| position | VARCHAR(100) | NOT NULL | 岗位（原 `job_role`；员工上下文，非授权依据） |
| employee_level | VARCHAR(50) | NOT NULL | 职级（如 P5 / STANDARD；员工上下文，非授权依据） |
| role_id | UUID | FK | RBAC 角色 |
| status | VARCHAR(20) | NOT NULL | ACTIVE / INACTIVE |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

`status` 只允许 `ACTIVE` / `INACTIVE`。

不允许 Agent 通过自然语言直接修改 `users.role_id`；必须经过 Backend Authorization。

---

# 6. roles

## 6.1 用途

RBAC。当前只保留：

```text
EMPLOYEE
IT_SUPPORT
ADMIN
```

## 6.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 角色 ID |
| code | VARCHAR(30) | UNIQUE | 角色编码 |
| name | VARCHAR(100) | NOT NULL | 角色名称 |
| description | TEXT | NULL | 角色说明 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

不增加 `SUPER_ADMIN` / `ROOT` / `AI_ADMIN` 等额外角色。

---

# 7. services

## 7.1 用途

IT 服务目录在 V1 中复用为**被观测的业务系统**（Checkout / Auth / Worker），不是 ITIL Catalog。

## 7.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 服务 ID |
| code | VARCHAR(50) | UNIQUE | 服务编码 |
| name | VARCHAR(100) | NOT NULL | 服务名称 |
| description | TEXT | NULL | 服务说明 |
| category | VARCHAR(50) | NOT NULL | 服务分类 |
| status | VARCHAR(20) | NOT NULL | ACTIVE / INACTIVE（目录启用） |
| health_status | VARCHAR(20) | NOT NULL | **V1**：HEALTHY / DEGRADED / DOWN（模拟，非 Prometheus） |
| health_summary | TEXT | NULL | **V1**：现状一句话 |
| last_checked_at | TIMESTAMPTZ | NULL | **V1**：模拟探活时间 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

`status` 与 `health_status` 不可混用。INACTIVE 服务不出现在 V1 列表 API。

种子 UUID 与健康值见 Phase A 契约 §7.2。**尚未 migration。**

---

# 8. tickets

## 8.1 用途

运维故障工单：请求人、所属业务服务、现象、负责人、优先级、状态、分析摘要。

## 8.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 工单 ID |
| ticket_no | VARCHAR(30) | UNIQUE | 展示编号，例如 OPS-1001 |
| requester_id | UUID | FK, NOT NULL | 请求人 |
| assignee_id | UUID | FK, NULL | IT Support 负责人 |
| service_id | UUID | FK, NOT NULL | IT 服务 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| description | TEXT | NOT NULL | 问题描述 |
| priority | VARCHAR(20) | NOT NULL | LOW / MEDIUM / HIGH / URGENT |
| status | VARCHAR(30) | NOT NULL | 工单状态 |
| resolution | TEXT | NULL | 处理结果 |
| analysis | TEXT | NULL | **V1**：故障分析摘要；`related_ticket_id` **暂缓不建** |
| resolved_at | TIMESTAMPTZ | NULL | 解决时间 |
| closed_at | TIMESTAMPTZ | NULL | 关闭时间 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

## 8.3 Ticket 状态机

数据库只持久化当前状态，**不负责决定迁移是否合法**。

状态集合（库可存；V1 **无 REJECTED** 实现，与现网一致）：

```text
OPEN
ASSIGNED
IN_PROGRESS
WAITING_USER
RESOLVED
CLOSED
REJECTED
```

合法主路径（V1 Demo）：

```text
OPEN → IN_PROGRESS → RESOLVED → CLOSED
```

现网仍含 `ASSIGNED` / `WAITING_USER`；Phase B 必须允许 `OPEN → IN_PROGRESS`。Demo 不走 WAITING_USER。禁止 `OPEN → CLOSED`。

> Ticket 状态转换由 Backend Service 层按照状态机规则控制，不能由前端或 Agent 任意修改状态。

禁止通用：

```http
PATCH /tickets/:id
{ "status": "CLOSED" }
```

应使用明确业务动作，例如：

```text
assignTicket()
startTicket()
waitForUser()
resolveTicket()
closeTicket()
rejectTicket()
```

常见查询索引：`requester_id`、`assignee_id`、`service_id`、`status`、`created_at`；`ticket_no` 唯一。

---

# 9. ticket_comments

**V1 不建此表。** 过程用 `tickets.analysis` + `resolution` + `audit_logs`。下文字段仅为历史设计，实现禁止按本节建表。

## 9.1 用途（Legacy 设计，未落地）

工单沟通与处理记录：用户补充、IT 回复、系统记录。不单独作为新核心业务对象。

## 9.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 记录 ID |
| ticket_id | UUID | FK, NOT NULL | 所属工单 |
| author_id | UUID | FK, NOT NULL | 作者 |
| content | TEXT | NOT NULL | 内容 |
| comment_type | VARCHAR(30) | NOT NULL | USER_REPLY / SUPPORT_NOTE / SYSTEM |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

不要把全部处理历史覆盖写入 `tickets.description`；用 Ticket + TicketComment 表达过程。

---

# 10. access_requests

**V1 Legacy 冻结。** 表已存在；不新增列、不进 Agent 主链。

## 10.1 用途

权限申请。与 Ticket、Approval **分离**，不合并进 Ticket。

> AccessRequest = 用户希望获得某项资源权限。

## 10.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 权限申请 ID |
| requester_id | UUID | FK, NOT NULL | 申请人 |
| service_id | UUID | FK, NOT NULL | 对应 IT 服务 |
| resource_type | VARCHAR(50) | NOT NULL | GITLAB / DATABASE / DEV_ENV |
| resource_name | VARCHAR(200) | NOT NULL | 资源名称 |
| permission_level | VARCHAR(50) | NOT NULL | READ / DEVELOPER / ADMIN 等 |
| reason | TEXT | NOT NULL | 申请原因 |
| status | VARCHAR(30) | NOT NULL | PENDING / APPROVED / REJECTED / CANCELLED |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

## 10.3 与 Ticket 的区别

| 对象 | 含义 | 示例 |
|---|---|---|
| Ticket | 普通 IT 服务请求 | Docker 安装失败、VPN 无法连接 |
| AccessRequest | 权限申请 | GitLab Developer、Database Read |

`Ticket.status` 不能代替 `AccessRequest.status`。

---

# 11. approvals

**V1 Legacy 冻结。** 表已存在；不扩展多级审批。

## 11.1 用途

权限申请的 HITL 审批记录。独立于 Ticket。

当前只需要：

```text
AccessRequest → Approval → Approve / Reject
```

不实现多级审批、审批节点、审批模板、审批策略引擎。

## 11.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 审批 ID |
| access_request_id | UUID | FK, NOT NULL | 权限申请 |
| approver_id | UUID | FK, NOT NULL | 审批人 |
| status | VARCHAR(30) | NOT NULL | PENDING / APPROVED / REJECTED / CANCELLED |
| comment | TEXT | NULL | 审批意见 |
| decided_at | TIMESTAMPTZ | NULL | 决定时间 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

## 11.3 状态机

```text
PENDING → APPROVED
PENDING → REJECTED
PENDING → CANCELLED
```

Backend 控制迁移。Agent / Frontend 不能直接把 `PENDING` 改成 `APPROVED`。

MVP 通常一个 AccessRequest 对应一个 Approval；不为此预留多级审批扩展设计。

---

# 12. role_resources

## 12.1 用途

支撑新员工 Onboarding：某岗位默认需要哪些 IT 资源。

```text
角色 → 默认资源模板
```

例如 Backend Developer 默认需要 GitLab、Docker、Development Environment、Database Read。

这不是完整 IAM，只支撑 `get_role_resource_template()`。

## 12.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 记录 ID |
| role_id | UUID | FK, NOT NULL | 关联角色 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_name | VARCHAR(200) | NOT NULL | 资源名称 |
| permission_level | VARCHAR(50) | NOT NULL | 默认权限 |
| required | BOOLEAN | NOT NULL | 是否必须 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

---

# 13. user_resources

## 13.1 用途

用户当前已有资源，支撑 `get_user_resources()`，并与 `role_resources` 对比缺失资源。

## 13.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 资源记录 ID |
| user_id | UUID | FK, NOT NULL | 用户 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_name | VARCHAR(200) | NOT NULL | 资源名称 |
| permission_level | VARCHAR(50) | NOT NULL | 当前权限 |
| status | VARCHAR(30) | NOT NULL | ACTIVE / REVOKED |
| granted_at | TIMESTAMPTZ | NULL | 授予时间 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

不做复杂权限策略、过期策略引擎。Agent 不能直接改写 `user_resources`。

---

# 14. Onboarding 数据关系

核心场景：

> “我是新来的后端开发，帮我看看开发环境和权限还缺什么。”

```text
User
 ↓
Role / position / employee_level（员工上下文，非授权）
 ↓
RoleResource（应有）
 ↓
UserResource（已有）
 ↓
对比缺失
 ↓
创建 AccessRequest
 ↓
HITL → Approval
```

示例：

```text
应有：GitLab Developer、Database Read、Docker USER
已有：GitLab Developer
缺少：Database Read、Docker USER
```

Agent 只负责比较与建议；创建申请与审批写入必须经 Backend。

---

# 15. knowledge_documents

> **V1 不建此表。** RAG 不落 PostgreSQL。V1 检索 = 本地 embedding 索引文件（Phase C）。  
> 远期 Milvus / PG catalog 见延期的 Phase 15。实现禁止按本节建表。

## 15.1 用途

RAG 知识库：PostgreSQL 保存文档基础信息与原始文本/元数据；向量与 Chunk 由 Milvus 负责。

知识库与 Long-term Memory 分离。

## 15.2 字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 文档 ID |
| title | VARCHAR(255) | NOT NULL | 标题 |
| source_type | VARCHAR(30) | NOT NULL | PDF / MD / DOCX / XLSX / CSV / JSON / IMAGE |
| source_name | VARCHAR(255) | NOT NULL | 原始文件名 |
| category | VARCHAR(100) | NOT NULL | 分类 |
| department | VARCHAR(100) | NULL | 所属部门 |
| version | VARCHAR(50) | NULL | 版本 |
| visibility | VARCHAR(30) | NOT NULL | PUBLIC / DEPARTMENT |
| content | TEXT | NOT NULL | 解析后的统一文本 |
| metadata | JSONB | NULL | 扩展元数据 |
| status | VARCHAR(20) | NOT NULL | ACTIVE / ARCHIVED |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

## 15.3 与 Milvus

```text
PostgreSQL KnowledgeDocument
        │ document_id
        ▼
Milvus Chunk + Embedding
```

不在 PostgreSQL 中保存 embedding vector 作为主检索存储。Milvus Chunk 通过 `document_id` 回指文档即可。

---

# 16. audit_logs

## 16.1 用途

记录关键业务操作与高风险 Agent 操作，**不是完整审计平台**。

主要记录：

```text
登录
创建 / 修改工单
创建权限申请
审批
高风险 Agent Tool 调用
权限拒绝
```

## 16.2 字段（极简）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 审计 ID |
| request_id | VARCHAR(100) | NULL | 请求 ID |
| actor_id | UUID | FK, NULL | 操作者 |
| actor_type | VARCHAR(30) | NOT NULL | USER / AGENT / SYSTEM |
| action | VARCHAR(100) | NOT NULL | 动作 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_id | UUID | NULL | 资源 ID |
| result | VARCHAR(30) | NOT NULL | SUCCESS / FAILURE / DENIED |
| created_at | TIMESTAMPTZ | NOT NULL | 时间 |

不保留 `parameter_summary` / `result_summary` / `status_change` 等 JSONB 审计结构。

## 16.3 原则

- Append Only：创建后只读
- 普通业务流程不允许 UPDATE / DELETE
- 用 `request_id` 串联一次请求内的业务结果即可，不在此表重建 Agent Trace

---

# 17. Memory：不建独立表

## 17.1 Short-term Memory

```text
LangGraph Checkpointer + thread_id
```

不使用业务表保存聊天上下文。

## 17.2 Long-term Memory

复用已有结构化业务数据，例如：

```text
users.department
users.position
users.employee_level
user_resources
历史业务信息（Ticket / AccessRequest 等）
```

不新增：

```text
memory_vectors
memory_items
memory_summaries
memory_store
```

写入规则：不允许 LLM 自由写长期记忆。`role` / 权限 / `department` 等必须经 Backend 校验后才能持久化。

---

# 18. Agent 与 PostgreSQL 边界

## 18.1 唯一合法访问链

```text
Agent → Tool → Go Backend API → Service → Repository → PostgreSQL
```

禁止：

```text
Python Agent → SQLAlchemy / 直连 SQL → PostgreSQL
```

数据库连接凭证只存在于 Go Backend。

## 18.2 Agent 不能直接修改

```text
role / role_id
user_resources
approval
ticket status
用户权限
```

所有业务修改必须经过 Backend Authorization、参数校验与业务规则。

## 18.3 为什么

Agent 输出不可信。直连数据库会绕过 Authorization、校验、业务规则与 Audit。

> Agent 只拥有 Tool 能力，不拥有数据库权限。

## 18.4 Tool 与表映射（摘要）

| Tool | 主要表 |
|---|---|
| get_user_profile | users, roles |
| get_user_resources | user_resources |
| get_role_resource_template | role_resources |
| get_ticket / search_tickets | tickets（及关联） |
| create_ticket | tickets（+ ticket_comments / audit_logs） |
| add_ticket_comment | ticket_comments |
| check_access | user_resources |
| create_access_request | access_requests, approvals, audit_logs |
| get_access_request | access_requests, approvals |
| get_approval | approvals |

Tool 暴露业务能力，不暴露 SQL（禁止 `execute_sql`）。

---

# 19. 关系、约束与索引

## 19.1 主要关系

```text
roles 1 ─── N users
users 1 ─── N tickets          (requester / assignee)
services 1 ─── N tickets
tickets 1 ─── N ticket_comments
users 1 ─── N access_requests
services 1 ─── N access_requests
access_requests 1 ─── N approvals   # MVP 通常 1:1
roles 1 ─── N role_resources
users 1 ─── N user_resources
```

## 19.2 外键

```text
users.role_id                 → roles.id
tickets.requester_id          → users.id
tickets.assignee_id           → users.id
tickets.service_id            → services.id
ticket_comments.ticket_id     → tickets.id
ticket_comments.author_id     → users.id
access_requests.requester_id  → users.id
access_requests.service_id    → services.id
approvals.access_request_id   → access_requests.id
approvals.approver_id         → users.id
role_resources.role_id        → roles.id
user_resources.user_id        → users.id
audit_logs.actor_id           → users.id
```

## 19.3 唯一约束

```text
users.email
roles.code
services.code
tickets.ticket_no
```

`user_resources` 可用 `(user_id, resource_type, resource_name, permission_level)` 避免重复授予同一资源记录。

## 19.4 索引原则

只为真实查询建最小索引，例如：

- tickets：requester / assignee / service / status / created_at
- access_requests：requester / status
- approvals：access_request_id / status
- audit_logs：request_id / created_at

不做过度详细的性能优化设计。

## 19.5 删除策略

业务数据优先软状态（`INACTIVE` / `ARCHIVED` / `REVOKED`），不轻易物理删除。Ticket / AccessRequest / Approval / AuditLog 不允许普通流程物理删除。

## 19.6 状态字段

状态使用有限枚举，由 Go 枚举 + Service 状态机校验。复杂 PostgreSQL ENUM 非必须。

---

# 20. 事务原则

多表写操作使用事务。例如创建权限申请：

```text
BEGIN
  Create AccessRequest
  Create Approval
  Create AuditLog
COMMIT
```

Ticket 状态更新同理：校验状态与权限 → 更新 Ticket → 写 Comment（如需）→ 写 AuditLog → COMMIT。

失败则 ROLLBACK；Agent 只能收到成功或失败，不能伪造成功。

---

# 21. Demo 初始化（最小）

```text
Roles:     EMPLOYEE / IT_SUPPORT / ADMIN
Services:  GITLAB_PERMISSION / DATABASE_ACCESS / DEV_ENVIRONMENT / ACCOUNT_SUPPORT / SOFTWARE_INSTALLATION
Users:     普通员工、IT Support、Admin（约 5–10 人即可）

RoleResource / UserResource：准备可演示缺失资源的 Onboarding 数据
Tickets：覆盖 OPEN / ASSIGNED / IN_PROGRESS / WAITING_USER / RESOLVED
AccessRequest：覆盖 PENDING / APPROVED / REJECTED
```

---

# 22. Migration 与分层原则

Migration 按 11 张表顺序建表即可（roles → users → services → tickets → comments → access_requests → approvals → role_resources → user_resources → knowledge_documents → audit_logs）。

原则一句话：

```text
Model 映射结构 → Repository 读写 → Service 业务规则与状态机 → Handler / Internal API 对外
```

结构变更用 Migration；不把业务状态机、Authorization、HITL 写进 Model。生产结构不依赖 AutoMigrate 作为唯一真相。

---

# 23. 最终关系图

```text
roles ──1:N── users ──┬── tickets ──1:N── ticket_comments
                      ├── access_requests ──1:N── approvals
                      └── user_resources

roles ──1:N── role_resources
services ──► tickets / access_requests
knowledge_documents ──► Milvus
users/Agent/System ──► audit_logs
```

---

# 24. 当前明确不做

```text
❌ 新增业务表
❌ Agent Trace 数据库
❌ Evaluation 数据库
❌ Memory 独立表 / Memory Vector DB
❌ 复杂 IAM / 权限策略引擎
❌ 多级审批 / 审批模板 / 审批流引擎
❌ 完整审计平台（JSONB 审计详情等）
❌ 通用工作流引擎
❌ 完整 ITSM / ITIL Service Catalog
❌ 用户聊天记录业务表
❌ LDAP / AD / 真实 GitLab 权限同步表
❌ 为所有表设计完整通用 CRUD
❌ 过度索引与性能优化方案
```

原因：当前业务闭环尚未证明需要它们。

---

# 25. MVP Definition of Done

**已由 V1 契约取代。** V1 DoD 见 `docs/phases/PHASE_A_V1_CONTRACT.md`：5 张核心表演进 + 2 张 Legacy 冻结 + 不建其余预留表。

---

# 26. 最终原则

```text
业务对象少 → 关系清晰 → 状态明确
→ Backend 控制规则 → Agent 经 Tool 访问
→ 关键操作可审计 → RAG 与业务数据分离
→ 不为完整感而设计
```

```text
Agent（理解 / 决策 / Tool）
        ↓
Controlled Tool
        ↓
Go Backend（Auth / Authorization / Validation / Rules / State Machine / Audit）
        ↓
PostgreSQL（Business Facts）
```

> **PostgreSQL 保存“已经成立的业务事实”；Agent 只能通过受控 Tool 提出“想做什么”，不能直接决定数据库里“应该是什么”。**
