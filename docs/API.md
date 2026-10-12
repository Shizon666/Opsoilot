# OpsPilot API

> OpsPilot 企业 IT 服务智能协作平台 — MVP API 设计（接口契约）  
> API Version: `v1`  
> Status: Design Contract（**部分被 V1 覆盖**）  
>
> **V1 产品化（2026-10-03）**：故障工单助手的 HTTP 差集、Legacy 范围与字段增量以  
> [`docs/phases/PHASE_A_V1_CONTRACT.md`](phases/PHASE_A_V1_CONTRACT.md) **为准**。  
> 本文保留历史 MVP 叙述与 Permission 形状；Permission 为 **Legacy**（现网可保留，不再扩展、不进 Agent 主链）。  
> 实现尚未改代码前，下列 V1 新路径（`/services`、`/audit-logs`、tickets.`q`/`analysis`）**仅契约，未落地**。

---

## 1. 整体架构

OpsPilot MVP 分成两个后端职责，**不**设计成 Agent 直连数据库。

### 1.1 职责划分

| 服务 | 技术栈 | 职责 |
|---|---|---|
| Business API | Go + Gin | 用户、工单、权限申请等业务数据；PostgreSQL 访问；对外提供 Business API |
| Agent API | Python + FastAPI + LangGraph | 意图识别、RAG、Tool Calling、流程编排、多轮会话 |

### 1.2 调用链路

```text
React
  → Nginx
  → Go Business API  /  FastAPI Agent API
```

Agent 查询或修改业务数据时：

```text
Agent
  → Tool
  → Business Client
  → Go Business API
  → PostgreSQL
```

**明确禁止：**

```text
Agent → PostgreSQL
```

### 1.3 Nginx 路由

```text
/api/v1/*  → Go Backend   (例如 :8080)
/agent/*   → FastAPI Agent (例如 :8000)
/health    → Go Business API (例如 :8080)
```

示例：

```text
GET  /api/v1/tickets  → Nginx → Go:8080
POST /agent/chat      → Nginx → FastAPI:8000
GET  /health          → Nginx → Go:8080
```

对外统一健康检查：`GET /health` 由 **Nginx → Go Business API** 处理。  
FastAPI 可提供内部健康检查（用于容器 / 服务自身探测），但**不作为本 MVP 对外统一 `/health` 接口**。

---

## 2. API 前缀

| 前缀 | 服务 | 说明 |
|---|---|---|
| `/api/v1/*` | Go Business API | 业务资源与动作 |
| `/agent/*` | FastAPI Agent API | Agent 对话（同步 / 流式） |
| `/health` | Go Business API | 对外统一健康检查 |

**不要**为了统一前缀，把 Agent 强行放进 `/api/v1`。

---

## 3. HTTP Method

| Method | 用途 | MVP 是否使用 |
|---|---|---|
| GET | 查询 | ✓ |
| POST | 创建资源 / 执行业务动作 | ✓ |
| PATCH | 部分更新资源 | ✓ |
| PUT | 完整替换资源 | ✗ 暂不使用 |
| DELETE | 删除资源 | ✗ 暂不使用 |

工单等资源以部分字段更新为主，因此使用 **PATCH**，不使用 PUT。

示例：

```http
PATCH /api/v1/tickets/{id}
```

```json
{
  "status": "resolved"
}
```

---

## 4. 统一响应格式

所有非 SSE 接口默认返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 成功

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 失败

```json
{
  "code": 40001,
  "message": "invalid request",
  "data": null
}
```

---

## 5. 错误码

| Code | 含义 |
|---:|---|
| 0 | 成功 |
| 40001 | 请求参数错误 |
| 40101 | 未登录 |
| 40102 | Token 无效或已过期 |
| 40301 | 无权限 |
| 40401 | 资源不存在 |
| 40901 | 资源状态冲突 |
| 50001 | 服务内部错误 |
| 50002 | 数据库错误 |
| 50003 | Agent 服务异常 |

说明：

- 权限申请已是 `approved` / `rejected` 时再次 `approve` / `reject` → **40901**
- 访问不属于当前用户的 `thread_id` → **40301**（或 40401，实现时二选一并在服务层统一）

---

## 6. 认证（JWT）

除登录接口外，需要认证的 API 使用：

```http
Authorization: Bearer <JWT>
```

Go 后端处理流程：

```text
Request
  → JWT Middleware
  → Token 校验
  → user_id / role
  → Handler
```

Agent API 同样校验 JWT，并从 Token 中解析 `user_id`，用于 `thread_id` 归属校验与业务 Tool 调用身份传递。  
Agent 调用 Go Business API 时，必须携带当前用户的认证上下文；Go Business API 仍必须独立完成最终鉴权与资源权限校验，不能信任 Agent 或客户端传入的 `user_id` 等可控字段。

---

## 7. RBAC

MVP 只保留三个角色：

```text
employee
it_support
admin
```

| 能力 | employee | it_support | admin |
|---|---|---|---|
| 查询自己的工单 | ✓ | ✓ | ✓ |
| 查询全部工单 | × | ✓（V1 冻结：全量历史） | ✓ |
| 创建工单 | ✓ | ✓ | ✓ |
| 修改自己的工单 | ✓（title / description / priority / **analysis**，见 V1 契约） | ✓ | ✓ |
| 查看服务状态 | ✓ | ✓ | ✓ |
| 修改服务健康 | × | ✓ | ✓ |
| 按 request_id 查审计 | × | ✓ | ✓ |
| 审批权限申请 | × | Legacy API 仍允许 | Legacy |
| 用户管理 | × | × | ✓（**后续功能，MVP 不提供 API**） |

权限判断必须在业务层完成，不能只依赖前端按钮控制。  
工单 PATCH 的可写字段因角色而异：`it_support` / `admin` 在具备资源权限时可额外修改 `status`、`assignee_id`（详见 12.4）。

---

## 8. 分页

列表接口统一使用：

```text
page
page_size
```

示例：

```http
GET /api/v1/tickets?page=1&page_size=20
```

`data` 内统一分页结构：

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 9. 时间格式

API 时间统一使用 ISO 8601（UTC）：

```text
2026-10-01T10:30:00Z
```

数据库统一存储 UTC；前端按用户时区展示。

---

## 10. MVP API 总览

V1 主链与增量字段见 `PHASE_A_V1_CONTRACT.md` §4。下列为合并视图。

### Auth

```text
POST /api/v1/auth/login
GET  /api/v1/users/me
```

### Services（V1 新增，未实现）

```text
GET   /api/v1/services
GET   /api/v1/services/{id}
PATCH /api/v1/services/{id}
```

### Ticket

```text
GET   /api/v1/tickets
POST  /api/v1/tickets
GET   /api/v1/tickets/{id}
PATCH /api/v1/tickets/{id}
```

### Audit（V1 新增，未实现）

```text
GET /api/v1/audit-logs?request_id=
```

### Permission（Legacy：冻结，不进 V1 Agent）

```text
POST /api/v1/permissions
GET  /api/v1/permissions
GET  /api/v1/permissions/{id}
POST /api/v1/permissions/{id}/approve
POST /api/v1/permissions/{id}/reject
```

### Agent

```text
POST /agent/chat
POST /agent/chat/stream
POST /agent/chat/resume             # HITL approve/reject；现网已有则保持
```

### Health

```text
GET /health
```

**明确不做（MVP）：**

- `GET /api/v1/users` 及完整用户管理 API
- Onboarding 独立业务 API
- PUT / DELETE 资源接口
- 其他未列出的 CRUD

---

# 11. Auth

## 11.1 用户登录

```http
POST /api/v1/auth/login
```

无需 Authorization。

### Request

```json
{
  "username": "zhangsan",
  "password": "123456"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "jwt-token",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "zhangsan",
      "name": "张三",
      "role": "employee"
    }
  }
}
```

---

## 11.2 获取当前用户

```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "22222222-2222-2222-2222-222222222201",
    "username": "demo@opspilot.local",
    "name": "张明",
    "department": "研发部",
    "position": "后端开发工程师",
    "employee_level": "P5",
    "role": "employee"
  }
}
```

说明：`department` / `position` / `employee_level` 为 Phase 12 员工上下文，仅辅助回答；**不是** JWT / RBAC 授权依据。

---

# 12. Ticket

## 12.1 工单列表

```http
GET /api/v1/tickets
Authorization: Bearer <token>
```

### Query Parameters

```text
page=1
page_size=20
status=open
priority=high
q=checkout
service_id=<uuid>
```

`q` / `service_id` 为 **V1 新增**（见 Phase A 契约）；落地前现网只有 page/status。

### 可见范围（MVP / V1 冻结）

- `employee`：只看到自己创建的工单（`q` 不可突破）
- `it_support` / `admin`：全部工单
- **不做**跨用户已解决单对 Employee 的投影

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 10001,
        "title": "无法连接公司 VPN",
        "description": "Windows 电脑无法连接 VPN",
        "status": "open",
        "priority": "high",
        "creator_id": 1,
        "assignee_id": 10,
        "created_at": "2026-10-01T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 12.2 创建工单

```http
POST /api/v1/tickets
Authorization: Bearer <token>
```

### Request

```json
{
  "title": "Checkout 下单 502",
  "description": "收银台提交订单返回 502",
  "priority": "high",
  "service_id": "33333333-3333-3333-3333-333333333401",
  "analysis": "可选；创建人可写"
}
```

V1：`service_id` **必填**，必须是 ACTIVE 服务；禁止静默默认 `GENERAL_IT`。`analysis` 可选。

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10001,
    "status": "open"
  }
}
```

---

## 12.3 工单详情

```http
GET /api/v1/tickets/{id}
Authorization: Bearer <token>
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10001,
    "title": "无法连接公司 VPN",
    "description": "Windows 电脑无法连接 VPN",
    "status": "open",
    "priority": "high",
    "creator": {
      "id": 1,
      "name": "张三"
    },
    "assignee": {
      "id": 10,
      "name": "IT 管理员"
    },
    "created_at": "2026-10-01T10:00:00Z",
    "updated_at": "2026-10-01T10:00:00Z"
  }
}
```

---

## 12.4 部分更新工单（PATCH）

```http
PATCH /api/v1/tickets/{id}
Authorization: Bearer <token>
```

只提交需要变更的字段，**不要**要求客户端提交完整 Ticket。  
请求体至少包含一个可更新字段。

若请求体为空对象：

```json
{}
```

返回：

```json
{
  "code": 40001,
  "message": "invalid request",
  "data": null
}
```

### 字段权限（按角色）

#### employee

只能修改**自己创建的工单**中的：

- `title`
- `description`
- `priority`
- `analysis`（V1）

不能修改：

- `status`
- `assignee_id`

#### it_support / admin

在具备对应资源权限的前提下，可以修改：

- `title`
- `description`
- `priority`
- `analysis`（V1）
- `status`
- `assignee_id`
- `resolution`（V1：若实现层尚未暴露则随 Phase B 一并允许 Support 写入）

### Request 示例

更新状态（仅 `it_support` / `admin`，且具备对应资源权限）：

```json
{
  "status": "resolved"
}
```

更新优先级：

```json
{
  "priority": "high"
}
```

同时更新多个字段（仍为部分更新；字段集合仍须符合当前角色权限）：

```json
{
  "status": "resolved",
  "priority": "medium"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10001,
    "status": "resolved"
  }
}
```

### 说明

- PATCH 只是部分更新接口，具体允许修改哪些字段必须由 Service 层根据当前用户角色、资源归属和工单当前状态进行校验，不能仅依赖前端控制
- 非法状态迁移由 Service 层校验，冲突返回 `40901`
- 无权限修改他人工单，或尝试修改角色不允许的字段 → `40301`
- V1 演示主路径允许 `OPEN → IN_PROGRESS`（见 Phase A 契约）

---

# 12.5 Services（V1，未实现）

完整请求/响应以 `docs/phases/PHASE_A_V1_CONTRACT.md` §4.2–4.4 为准。

# 12.6 Audit 查询（V1，未实现）

`GET /api/v1/audit-logs?request_id=` 仅 Support/Admin；`request_id` 必填。详见 Phase A 契约 §4.8。

---

# 13. Permission（Legacy）

> V1 **冻结**：表与 HTTP 保留；Agent 主流程与新前端入口不得再依赖本节。  
> 形状以现网实现 + 下文为准，不再扩展字段或审批级数。

权限申请状态机（MVP）：

```text
pending
  ├── approve → approved
  └── reject  → rejected
```

已是 `approved` 或 `rejected` 时，再次执行 approve / reject → **40901**（不允许重复审批）。

---

## 13.1 创建权限申请

```http
POST /api/v1/permissions
Authorization: Bearer <token>
```

### Request

```json
{
  "resource": "production_database",
  "permission": "read",
  "reason": "项目开发需要"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 20001,
    "status": "pending"
  }
}
```

---

## 13.2 权限申请列表

```http
GET /api/v1/permissions
Authorization: Bearer <token>
```

### Query Parameters

```text
page=1
page_size=20
status=pending
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 20001,
        "resource": "production_database",
        "permission": "read",
        "reason": "项目开发需要",
        "status": "pending",
        "applicant_id": 1,
        "created_at": "2026-10-01T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 13.3 权限申请详情

```http
GET /api/v1/permissions/{id}
Authorization: Bearer <token>
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 20001,
    "resource": "production_database",
    "permission": "read",
    "reason": "项目开发需要",
    "status": "pending",
    "applicant_id": 1,
    "created_at": "2026-10-01T10:00:00Z"
  }
}
```

---

## 13.4 审批通过

```http
POST /api/v1/permissions/{id}/approve
Authorization: Bearer <token>
```

仅 `it_support` / `admin`。

### Request

```json
{
  "comment": "审批通过"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 20001,
    "status": "approved"
  }
}
```

若当前状态不是 `pending`：

```json
{
  "code": 40901,
  "message": "resource status conflict",
  "data": null
}
```

---

## 13.5 审批拒绝

```http
POST /api/v1/permissions/{id}/reject
Authorization: Bearer <token>
```

仅 `it_support` / `admin`。

### Request

```json
{
  "comment": "权限申请理由不足"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 20001,
    "status": "rejected"
  }
}
```

若当前状态不是 `pending` → `40901`。

---

# 14. Agent

Agent API 与业务 CRUD 分离：

```text
业务 API：资源查询 / 创建 / 部分更新 / 业务动作
Agent API：自然语言 → 意图 / RAG / Tool → 回答
```

Agent **不直接访问 PostgreSQL**；需要业务数据时通过 Tool → Business Client → Go API。

---

## 14.1 同步对话

```http
POST /agent/chat
Authorization: Bearer <token>
Content-Type: application/json
```

### Request

```json
{
  "thread_id": "thread_001",
  "message": "帮我看看我的 VPN 工单处理到哪了"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| thread_id | string | ✓ | 会话 ID；必须属于当前登录用户 |
| message | string | ✓ | 用户本轮输入 |

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "thread_id": "thread_001",
    "message_id": "msg_001",
    "message": "你的 VPN 工单目前正在处理中。"
  }
}
```

**不要**把 `intent` 作为默认顶层返回字段。

如需调试信息，可放在可选 `metadata`（MVP 可不返回）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "thread_id": "thread_001",
    "message_id": "msg_001",
    "message": "你的 VPN 工单目前正在处理中。",
    "metadata": {
      "intent": "ticket_query"
    }
  }
}
```

---

## 14.2 thread_id 安全

`thread_id` **必须**与当前登录用户绑定。

不能因为客户端传入了其他用户的 `thread_id`，就允许访问其他用户的 Agent 会话。

校验逻辑：

```text
JWT
  → user_id
  → thread_id ↔ user_id
  → 校验通过
  → 加载 LangGraph Checkpointer
```

若 `thread_id` 不属于当前用户 → 拒绝请求（建议 `40301`）。

实现约定（MVP）：

1. 首次对话：客户端可生成 `thread_id`，服务端创建 `thread_id ↔ user_id` 绑定
2. 后续对话：必须校验绑定关系
3. Checkpointer 按 `thread_id` 加载短期记忆，但加载前必须完成归属校验

---

## 14.3 流式对话（SSE）

```http
POST /agent/chat/stream
Authorization: Bearer <token>
Content-Type: application/json
```

请求体与同步接口相同：

```json
{
  "thread_id": "thread_001",
  "message": "帮我看看我的 VPN 工单处理到哪了"
}
```

响应：

```http
Content-Type: text/event-stream
```

### SSE 事件类型

| type | 说明 |
|---|---|
| start | 本轮开始，携带 `thread_id` / `message_id` / `request_id` |
| token | LLM 增量文本（真实 chunk，不是整段一次性伪装） |
| tool_start | 模型已产生 tool call，对应 Tool **即将/正在**执行；含 `tool`、`tool_call_id` |
| tool_end | 该 `tool_call_id` 的 Tool **已执行完**；含 `ok`，**不含** Go 完整响应体 |
| error | 流中 Agent/LLM 失败（流开始前的 401/403 仍走 JSON 信封） |
| done | 本轮结束；`ok`；`message` 为完整回复；`metadata` 与同步接口同形（含 `tools_called` / `tool_results`） |

仅允许以上 6 种 `type`。不暴露 LangGraph node / checkpoint / 回调名。

流开始前失败（缺 JWT、thread 不属于当前用户）仍返回统一 JSON `{code, message, data}`，HTTP 401/403，与 `POST /agent/chat` 相同。

### 示例

```text
data: {"type":"start","thread_id":"thread_001","message_id":"msg_001","request_id":"req_001"}

data: {"type":"token","content":"你属于"}

data: {"type":"tool_start","tool":"get_current_user","tool_call_id":"call_abc"}

data: {"type":"tool_end","tool":"get_current_user","tool_call_id":"call_abc","ok":true}

data: {"type":"token","content":"研发部"}

data: {"type":"done","ok":true,"thread_id":"thread_001","message_id":"msg_001","message":"你属于研发部。","metadata":{"tools_called":["get_current_user"]}}
```

流式接口同样必须执行 `thread_id ↔ user_id` 校验。

---

## 14.4 Agent 与业务 API 的关系

```text
                ┌──────────────┐
                │    React     │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    Nginx     │
                └──────┬───────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       ┌───────────┐       ┌───────────┐
       │ Go / Gin  │       │ FastAPI   │
       │ Business  │◄──────│ LangGraph │
       └─────┬─────┘ Tool  └───────────┘
             │
             ▼
       ┌───────────┐
       │ PostgreSQL│
       └───────────┘
```

### 身份传递与二次鉴权

```text
用户
  ↓
JWT
  ↓
FastAPI Agent
  ↓
解析当前 user_id
  ↓
Business Client
  ↓
Go Business API
  ↓
Go 再次执行认证 / 授权 / 资源权限校验
```

安全约束：

1. Agent API 首先校验用户 JWT。
2. Agent 从 JWT 中获得当前 `user_id`。
3. Agent 调用 Go Business API 时，必须携带当前用户的认证上下文。
4. Go Business API 不能信任 Agent 或客户端传入的 `user_id` 等可控字段。
5. Go Business API 必须独立完成最终的认证、RBAC 和资源归属校验。
6. Agent 不允许通过修改 `user_id` 来访问其他用户的数据。
7. `thread_id ↔ user_id` 校验仍然保留（见 14.2）。

Agent 调用 Business API 时，应携带当前用户的认证上下文；  
Go Business API 仍必须独立完成最终鉴权与资源权限校验，  
不能信任 Agent 或客户端传入的 `user_id` 等可控字段。

示例：查询工单

```text
用户
  → Agent（校验 JWT，解析 user_id）
  → ticket_query Tool
  → Business Client（携带当前用户认证上下文）
  → GET /api/v1/tickets/{id}
  → Go Business Service（再次认证 / 授权 / 资源权限校验）
  → PostgreSQL
  → 结构化结果
  → Agent 总结
  → 用户
```

---

# 15. Health

```http
GET /health
```

对外统一健康检查接口。路由归属：

```text
/health → Go Business API
```

即：**Nginx → Go Business API**。

FastAPI 可提供内部健康检查，用于容器 / 服务自身健康检查，但**不作为本 MVP 对外统一健康检查接口**。不要因此新增其他公开 API。

### Response（建议）

```json
{
  "status": "ok"
}
```

说明：健康检查可不走统一业务响应包络；以运维探测简单可用为准。

---

# 16. Go 后端目录结构（建议）

```text
backend/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handler/
│   ├── service/
│   ├── repository/
│   ├── model/
│   ├── middleware/
│   └── router/
└── go.mod
```

请求处理链路：

```text
HTTP Request
  → Router
  → Handler
  → Service
  → Repository
  → GORM
  → PostgreSQL
```

Agent 侧建议独立目录（示例，非强制）：

```text
agent/
├── app/
│   ├── api/          # /agent/chat, /agent/chat/stream
│   ├── graph/        # LangGraph
│   ├── tools/        # Tool 定义
│   └── clients/      # 调用 Go Business API 的 Business Client
└── requirements.txt
```

---

# 17. API 设计原则

1. Business API 使用 `/api/v1`；Agent API 使用 `/agent`；对外统一健康检查 `GET /health` 由 Go Business API 提供。
2. 普通资源采用 REST 风格；**REST 是设计风格，不是技术栈**。
3. 查询用 GET；创建 / 业务动作用 POST；部分更新用 PATCH。
4. MVP 不使用 PUT / DELETE。
5. 审批等业务动作用子路径 POST（`/approve`、`/reject`）。
6. Agent 对话单独设计，不强行套 CRUD。
7. Agent 不直接操作数据库；业务事实由 Go Business API 统一管理。
8. 前端不承担最终权限校验；后端必须鉴权与鉴权失败返回对应错误码。Agent 调用 Business API 时须携带当前用户认证上下文，Go 仍须独立完成最终鉴权。
9. 非 SSE 接口返回统一 `code` / `message` / `data`。
10. 只实现本文档列出的 MVP 接口；后续确有需要再扩展。
11. 不为 MVP 引入微服务拆分、Kafka、K8s 等额外复杂度。

---

# 18. 与当前实现的差异 / TODO

> 审计结论：截至本文档修订时，仓库中 `backend/`、`agent/`、`frontend/`、`deploy/` 仅有占位（如 `.gitkeep`），`docker-compose.yml` 为 TODO 骨架。  
> **当前没有任何已实现的 HTTP 业务接口。** 下文「差异」指：相对旧版 `API.md` 的设计收敛，以及与其他设计文档 / 未来实现之间需要对齐的事项。

## 18.1 相对旧版 API.md 已收敛的内容

| 项 | 旧设计 | 当前 MVP 契约 |
|---|---|---|
| Agent 路径 | `/api/v1/agent/chat` | `/agent/chat`、`/agent/chat/stream` |
| 工单更新 | `PUT` | `PATCH`（部分更新） |
| 用户列表 | `GET /api/v1/users` | **删除**（不做完整用户管理） |
| Onboarding API | `GET/PUT /api/v1/onboarding/...` | **删除**（不作为 MVP 独立模块） |
| Agent 响应 | 顶层返回 `intent` | 默认不返回；可选 `metadata.intent` |
| HTTP Method | 含 PUT / DELETE | MVP 仅 GET / POST / PATCH |
| 双后端边界 | 图示曾暗示 Agent 可连库 | **禁止** Agent → PostgreSQL |

## 18.2 后续实现 TODO（代码尚未存在）

- [ ] Go + Gin：实现 Auth / Ticket / Permission / Health
- [x] FastAPI + LangGraph：实现 `/agent/chat`、`/agent/chat/stream`
- [ ] Agent Business Client：通过 HTTP 调用 Go `/api/v1/*`，禁止直连 PostgreSQL；调用时携带当前用户认证上下文
- [ ] JWT Middleware（Go 与 Agent 均需校验；Go 对 Agent 转发请求再次独立鉴权）
- [ ] `thread_id ↔ user_id` 绑定存储与校验
- [ ] Nginx 路由：`/api/v1/*` → Go；`/agent/*` → FastAPI；`/health` → Go
- [ ] React：按本文档对接登录、工单、权限申请、Agent 对话与 SSE

## 18.3 与其他设计文档的已知差异（实现前需对齐）

以下差异**不在本次改 API 文档时强行改代码或其他文档**；实现阶段以本 API 契约为 HTTP 边界，字段与库表细节再与 `DATABASE.md` 等对齐。

| 主题 | 本 API 契约 | 其他文档现状 | 建议 |
|---|---|---|---|
| 资源 ID | 示例使用整数 ID | `DATABASE.md` 使用 UUID | 实现前统一为 UUID 或整数，并同步改示例 |
| 登录标识 | `username` | `DATABASE.md` users 以 `email` 为主 | 实现登录时统一字段名 |
| 工单更新 | `PATCH` 按角色限制字段：employee 仅 `title`/`description`/`priority`；it_support/admin 另可改 `status`/`assignee_id` | `DATABASE.md` / `ARCHITECTURE.md` 倾向禁止万能状态 PATCH、改用显式动作 | MVP 按本契约用 PATCH；字段权限与状态合法性由 Service 校验 |
| 权限对象命名 | HTTP 资源名 `permissions` | 库表名 `access_requests` | API 可继续叫 permissions；Repository 映射到 access_requests |
| 状态枚举大小写 | 示例小写（`open` / `pending`） | 库设计多为大写（`OPEN` / `PENDING`） | 实现时统一一层映射 |
| Onboarding | API 不做 | DB 仍保留 role_resources / user_resources 支撑 | 业务可内部使用；不暴露 Onboarding HTTP API |
| 用户管理 | RBAC 表保留 admin 能力，但无管理 API | — | 后续需要时再增加，不进本轮 MVP |

## 18.4 验收口径（契约自检）

后续任一端实现完成后，至少对照：

1. 路径与 Method 与第 10 节总览完全一致  
2. Ticket 更新为 PATCH；请求体至少含一个可更新字段；`{}` 返回 `40001`；字段权限按角色校验  
3. Permission 终态再审批返回 `40901`  
4. Agent 前缀为 `/agent/*`，且默认响应不含顶层 `intent`  
5. `thread_id` 跨用户访问被拒绝  
6. SSE 至少包含 `start` / `token` / `tool_start` / `tool_end` / `done`  
7. 对外 `GET /health` 由 Go Business API 提供  
8. Agent → Go 调用携带用户认证上下文，且 Go 独立完成最终鉴权
)
