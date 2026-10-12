# OpsPilot V1 契约（Phase A）

> 状态：**已冻结（2026-10-03）**；同日产品决策已书面确认（见 §0）  
> 本 Phase：**只改文档，不改业务代码 / 不新建 migration / 不换语料文件**  
> 产品北极星：**AI 运维故障工单助手**  
>
> 实现 Phase B 起，若本文与 `docs/API.md` / `docs/DATABASE.md` / `ROADMAP.md` / `PROJECT_CONTEXT.md` / Phase 15 计划冲突，**产品北极星、HTTP/表差集、Tool 名与 hit 字段以本文为准**。  
> **运行时勘误（2026-10-04）**：§0/§6 原文「禁止 Milvus / 本地 bge-small」已被 Phase C-3 **运行时替代**为 SiliconFlow `BAAI/bge-m3` + Milvus `knowledge_docs`。禁止回退关键词检索；禁止再引入第二套生产索引；禁止知识后台。详见 [`docs/ENGINEERING_HARDENING.md`](../ENGINEERING_HARDENING.md)。  
> 未在本文出现的旧能力默认视为 Legacy 或延期。

---

## 0. 产品确认（2026-10-03）

不推翻现有工程基础。下列决策为 V1 终裁，后续实现不得回退：

| # | 主题 | 终裁 |
|---|---|---|
| 1 | 产品主链 | 故障分析闭环为北极星。`access_requests` / `approvals` / Permission **保留代码与表，冻结为 Legacy，不进 Agent 主流程** |
| 2 | 服务状态 | `services` 字段模拟健康；**不接** Prometheus / CMDB |
| 3 | RAG | **运行时：bge-m3 + Milvus**（C-3）。禁止退化为关键词检索。本地 bge-small 仅为遗留适配器。知识 CMS / Phase 15 平台 **不做** |
| 4 | 工单检索 | **SQL**（`q` ILIKE + `service_id`）。RAG 管知识，Ticket Search 管历史事故。不引入 ES / 工单向量 |
| 5 | Demo 账号 | 双角色：Employee 报障；IT_SUPPORT 分析、处理、关单 |
| 6 | HITL | 读自动执行；写操作 `create_ticket` / `update_ticket` **必须确认** |
| 7 | 历史工单 | Employee 只看自己的单；IT_SUPPORT 看全部。**不做**跨用户已解决单投影 |
| 8 | 数据模型 | 增加 `tickets.analysis`。`related_ticket_id` **暂缓**（非 Demo 必需则不建） |

---

## 1. 产品冻结

```text
用户提出故障
  → Agent 理解（缺参追问）
  → 查询服务状态（services 表模拟健康）
  → RAG 检索运维 Runbook（bge-m3 + Milvus，`search_knowledge`）
  → SQL 检索历史工单
  → 生成分析与建议
  → HITL 确认后 create / update 工单
  → Go 写 audit_logs（同一 request_id）
```

| 角色 | 登录 | 职责 |
|---|---|---|
| Employee | `demo@opspilot.local` / `password123` | 报障、Chat、只看自己的工单 |
| IT_SUPPORT | `support@opspilot.local` / `password123` | 分析、改状态、关单、看全部工单与审计 |
| ADMIN | 不作为 Demo 主角 | 权限同 Support 的业务可见性；无管理后台 |

### 1.1 明确非目标（V1 全程）

```text
Permission / AccessRequest / Approval 进入 Agent 或新前端
Prometheus / CMDB / 真实探活
OCR / 异构知识 CMS / 可见性平台 / 再扩 20～30 源（Phase 15 平台）
related_ticket_id
ticket_comments / role_resources / user_resources / knowledge_documents
跨用户已解决工单投影给 Employee
ES / 工单向量检索
Multi-Agent / Planner / 评测平台
用户 CRUD、知识后台、Nginx 改造
删除 Legacy 表或 Permission HTTP（冻结，不删除）
```

---

## 2. 模块策略

| 模块 | V1 |
|---|---|
| Auth / JWT / RBAC / Request-ID | 保留 |
| users / roles | 保留；不扩展画像 |
| services + 模拟健康 | **主链（Phase B 已落地）** |
| tickets + 状态机 + analysis | **主链** |
| audit_logs 写 + 按 request_id 查 | **主链** |
| Agent ReAct / SSE / Checkpointer / HITL 写确认 | **主链** |
| 前端登录 / 工单 / Chat | **主链**（Chat 第一入口） |
| access_requests / approvals / Permission API / Permission Tools | **Legacy：保留代码与表，禁止新功能与 Agent 主流程** |
| Phase 10 关键词 RAG + IT 制度语料 | **Legacy**；运行时已换 `knowledge/ops` + Milvus |
| Phase 15 知识平台（CMS / 异构 20～30 / OCR） | **V2+ 延期**（V1 已用独立 Milvus 服务检索，不等于做完 Phase 15） |

---

## 3. 数据模型差集（Phase B migration，本 Phase 不建）

不删表、不加 `related_ticket_id`。

### 3.1 `services` 新增

| 列 | 类型 | 约束 | 说明 |
|---|---|---|---|
| health_status | VARCHAR(20) | NOT NULL，默认 `HEALTHY` | `HEALTHY` / `DEGRADED` / `DOWN` |
| health_summary | TEXT | NULL | 给 Agent 引用的一句话现状 |
| last_checked_at | TIMESTAMPTZ | NULL | 模拟探活时间 |

已有 `code/name/description/category/status` 保留。`status` 仍是目录启用态（`ACTIVE`/`INACTIVE`），与 `health_status` 正交。

### 3.2 `tickets` 新增

| 列 | 类型 | 约束 | 说明 |
|---|---|---|---|
| analysis | TEXT | NULL | 故障分析摘要；创建时可写 |

### 3.3 工单状态机（Service 层）

库内枚举仍为大写。演示主路径：

```text
OPEN → IN_PROGRESS → RESOLVED → CLOSED
```

Phase B **必须**允许 `OPEN → IN_PROGRESS`（跳过 `ASSIGNED`）。

保留现有 `ASSIGNED` / `WAITING_USER` 合法边，Demo **不走**。禁止 `OPEN → CLOSED`。无 `REJECTED`。

### 3.4 冻结表（零新 migration）

```text
access_requests
approvals
```

继续不建：`ticket_comments`、`role_resources`、`user_resources`、`knowledge_documents`。

### 3.5 `audit_logs`

不加列。V1 至少记录：`TICKET_CREATE`、`TICKET_UPDATE`、`SERVICE_HEALTH_UPDATE`（action 字符串以 Go 实现枚举为准，文档用上述语义）。查询不做成审计平台。

---

## 4. HTTP 契约差集

信封、错误码、JWT、分页、`PATCH` 风格与现网 Go 实现一致。库内大写，HTTP 可收小写、Handler 转大写（维持 R6）。

ID 一律 UUID。登录 `username` = email。

### 4.1 V1 对外总览

**主链（实现 / 保持）：**

```text
POST /api/v1/auth/login
GET  /api/v1/users/me

GET   /api/v1/services
GET   /api/v1/services/:id
PATCH /api/v1/services/:id          # 仅健康字段；IT_SUPPORT / ADMIN

GET   /api/v1/tickets               # + q, service_id
POST  /api/v1/tickets               # service_id 必填
GET   /api/v1/tickets/:id
PATCH /api/v1/tickets/:id           # + analysis

GET   /api/v1/audit-logs            # request_id 必填

POST /agent/chat
POST /agent/chat/stream
POST /agent/chat/resume             # 已有则保持；HITL approve/reject

GET /health
GET /internal/health                # Agent 探针，非对外统一健康
```

**Legacy（保持现网，文档不再扩展）：**

```text
POST/GET /api/v1/permissions
GET  /api/v1/permissions/:id
POST /api/v1/permissions/:id/approve
POST /api/v1/permissions/:id/reject
```

### 4.2 `GET /api/v1/services`

鉴权：任意登录用户。

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "33333333-3333-3333-3333-333333333401",
        "code": "CHECKOUT_API",
        "name": "Checkout API",
        "description": "下单与支付接口",
        "category": "PAYMENTS",
        "status": "ACTIVE",
        "health_status": "DEGRADED",
        "health_summary": "近 15 分钟 5xx 升高，支付超时增多",
        "last_checked_at": "2026-10-03T12:00:00Z"
      }
    ]
  }
}
```

V1 服务列表不分页（条数 ≤ 10）。仅返回 `status=ACTIVE`。

### 4.3 `GET /api/v1/services/:id`

鉴权：任意登录用户。不存在 → `40401`。`INACTIVE` → `40401`（对外当不存在）。

### 4.4 `PATCH /api/v1/services/:id`

鉴权：`IT_SUPPORT` / `ADMIN`。Employee → `40301`。

可写字段（至少一）：`health_status`、`health_summary`。禁止改 `code`/`name`/`category`/`status`。

空 `{}` → `40001`。非法 `health_status` → `40001`。成功写 Audit。

### 4.5 `GET /api/v1/tickets` 增量

| Query | 说明 |
|---|---|
| page / page_size | 保持 |
| status | 保持 |
| q | 可选；`title`/`description` ILIKE；最长 100 |
| service_id | 可选 UUID |

可见性：

- Employee：仅 `requester_id = 自己`
- IT_SUPPORT / ADMIN：**全部**历史

禁止跨用户已解决投影。`q` 不能突破可见性。

列表项在现有字段上增加：`service_id`、`ticket_no`、`analysis`（可 null）。

### 4.6 `POST /api/v1/tickets` 增量

```json
{
  "title": "Checkout 下单 502",
  "description": "从 10:20 起收银台提交订单返回 502",
  "priority": "high",
  "service_id": "33333333-3333-3333-3333-333333333401",
  "analysis": "疑似 Checkout API 依赖超时（可选）"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| title | 是 | ≤200 |
| description | 是 | |
| priority | 否 | 默认 `MEDIUM` |
| service_id | **是** | 必须是 ACTIVE 服务；禁止再静默落到 `GENERAL_IT` |
| analysis | 否 | 创建人可写 |

`requester_id` 只来自 JWT。非法/停用 `service_id` → `40001`。成功写 Audit。

### 4.7 `PATCH /api/v1/tickets/:id` 增量

| 角色 | 可写 |
|---|---|
| Employee（仅自己的单） | `title` / `description` / `priority` / **`analysis`** |
| IT_SUPPORT / ADMIN | 上列 + `status` / `assignee_id` / `resolution`（若现网已支持 resolution 则保持；未支持则 Phase B 一并允许 Support 写） |

Employee 写 `status` → `40301`。非法迁移 → `40901`。成功写 Audit。

### 4.8 `GET /api/v1/audit-logs`

```text
GET /api/v1/audit-logs?request_id={id}
```

- `request_id` **必填**，否则 `40001`
- 仅 `IT_SUPPORT` / `ADMIN`；Employee → `40301`
- 按 `created_at ASC` 返回该请求下全部记录
- 不分页（单请求条目少）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "...",
        "request_id": "req_...",
        "actor_id": "...",
        "actor_type": "USER",
        "action": "TICKET_CREATE",
        "resource_type": "TICKET",
        "resource_id": "...",
        "result": "SUCCESS",
        "created_at": "2026-10-03T12:00:00Z"
      }
    ]
  }
}
```

不返回密码、JWT、Prompt。

---

## 5. Agent 契约（Phase C 实现，此处冻结形状）

### 5.1 Tool 白名单（完整集合，禁止再叠 Permission）

| Tool | Go | 读写 | HITL |
|---|---|---|---|
| get_current_user | GET /users/me | R | 否 |
| list_services | GET /services | R | 否 |
| get_service_status | GET /services/:id | R | 否 |
| search_tickets | GET /tickets（q/status/service_id） | R | 否 |
| get_ticket | GET /tickets/:id | R | 否 |
| search_knowledge | Milvus 向量检索 | R | 否 |
| create_ticket | POST /tickets | W | **是** |
| update_ticket | PATCH /tickets/:id | W | **是** |

卸载出主链：`get_my_permissions`、`create_permission`、`get_my_tickets`（由 `search_tickets` 覆盖）。

读自动执行；写必须 `approve`/`reject` resume。现有 interrupt 语义保持。

### 5.2 推荐编排（Prompt 约束，不是独立 Graph 节点）

```text
能定位服务 → get_service_status 或 list_services
制度/排查步骤 → search_knowledge
同类事故 → search_tickets
仅基于 Tool 结果总结
用户确认 → create_ticket / update_ticket
```

禁止编造 `ticket_no`、健康状态、知识步骤。无 RAG 命中须说明依据不足，仍可建议建单。

### 5.3 入口

开发期维持：浏览器 Vite proxy → Agent；Agent → Go。V1 **不改成** Browser→Go→Agent。

---

## 6. RAG 契约（Phase C）

`search_knowledge(query, top_k≤5)` JSON 形状保持：`ok`、`hits[]`（`doc_id/title/path/section/snippet/score/confidence_level`）。

**检索后端（V1 运行时，C-3，2026-10-04 勘误）：**

```text
knowledge/ops（catalog.yaml 白名单）
  → 离线 load / chunk / embed
  → SiliconFlow BAAI/bge-m3
  → Milvus collection knowledge_docs（独立 compose）
  → search_knowledge COSINE top-k + 阈值
  → 无命中 hits=[] ，禁止用常识补公司流程
```

| 项 | 冻结值 |
|---|---|
| 模型 | `BAAI/bge-m3`（chunk 与 query 同一模型） |
| 度量 | COSINE |
| 存储 | Milvus `knowledge_docs`；**禁止**把 `local_store` 接回 Tool |
| 入库 | 离线脚本；Agent 运行时只检索 |
| Rerank | 不做 |
| PG knowledge 表 | 不建 |

Tool 名与 hit 字段不因存储替换而改变。`agent/app/rag/local_store.py` 为遗留适配器。

语料：`knowledge/ops`（C-2 catalog）。Phase 10 IT 制度 **不再作为 V1 检索集**（文件可留在仓库，索引名单换掉）。

计划 doc（实现时落文件，本 Phase 不创建正文）：

| 建议路径 | 用途 |
|---|---|
| `knowledge/runbooks/checkout-5xx.md` | 下单 5xx |
| `knowledge/runbooks/auth-failures.md` | 登录失败 |
| `knowledge/runbooks/order-worker-backlog.md` | Worker 堆积 |
| `knowledge/runbooks/ticket-analysis-guide.md` | 如何写 analysis |
| `knowledge/runbooks/escalate-to-human.md` | 何时升级 |
| 另 3～7 篇同类短手册 | 依赖超时、发布回滚、支付超时等 |

---

## 7. Seed 设计（Phase B migration，本 Phase 不执行）

新 migration（建议序号 `000014`），**不改写**已落地的 `000001`–`000013`。旧 VPN/GitLab 行（`000012`）可保留为 Legacy 数据；**Demo 剧本不再使用**。

密码哈希复用现网 `password123` 的 bcrypt（与 `000006`/`000009` 相同）。不在文档中新写明文以外的哈希。

### 7.1 账号

| id | email | 角色 | name | 部门 | 来源 |
|---|---|---|---|---|---|
| `22222222-2222-2222-2222-222222222201` | demo@opspilot.local | EMPLOYEE | 张明 | 研发部 | 已有；可 UPDATE 展示名 |
| `22222222-2222-2222-2222-222222222203` | support@opspilot.local | IT_SUPPORT | 王运维 | 运维部 | 已有；可 UPDATE 展示名 |
| `22222222-2222-2222-2222-222222222204` | lihua@opspilot.local | EMPLOYEE | 李华 | 研发部 | **新增夹具**；**非 Demo 登录主角** |
| `22222222-2222-2222-2222-222222222202` | agent@opspilot.local | EMPLOYEE | （保持） | — | Legacy 系统账号；V1 Demo **不用** |

密码：`demo` / `support` / `lihua` 均为 `password123`。不新增 ADMIN Demo 登录。

### 7.2 服务（稳定 UUID）

| id | code | name | category | status | health_status | health_summary |
|---|---|---|---|---|---|---|
| `33333333-3333-3333-3333-333333333401` | CHECKOUT_API | Checkout API | PAYMENTS | ACTIVE | DEGRADED | 近 15 分钟 5xx 升高，支付超时增多 |
| `33333333-3333-3333-3333-333333333402` | AUTH_SERVICE | Auth Service | IDENTITY | ACTIVE | HEALTHY | 登录成功率正常 |
| `33333333-3333-3333-3333-333333333403` | ORDER_WORKER | Order Worker | ORDERS | ACTIVE | DOWN | 消费积压，队列不再下降 |
| `33333333-3333-3333-3333-333333333301` | GENERAL_IT | General IT Support | IT | **INACTIVE** | HEALTHY | 目录停用，禁止作为建单默认 |

`last_checked_at`：seed 时写成固定 UTC（建议 `2026-10-03T12:00:00Z`），便于 Demo 复述。

### 7.3 工单剧本（稳定 UUID）

| id | ticket_no | requester_id | service_id | status | analysis |
|---|---|---|---|---|---|
| `44444444-4444-4444-4444-444444444501` | OPS-V1-2001 | 张明 | CHECKOUT_API | RESOLVED | 上游超时导致 5xx；扩容 Checkout 依赖后恢复 |
| `44444444-4444-4444-4444-444444444502` | OPS-V1-2002 | 张明 | AUTH_SERVICE | CLOSED | 密码重置后恢复（噪声单） |
| `44444444-4444-4444-4444-444444444503` | OPS-V1-2003 | 李华 | CHECKOUT_API | RESOLVED | 支付网关超时；切备用通道后恢复 |

建议标题（检索用）：

| ticket_no | title | description 要点 |
|---|---|---|
| OPS-V1-2001 | Checkout 下单间歇 502 | 收银台提交订单 502，与支付超时同时出现 |
| OPS-V1-2002 | 登录偶发失败 | 与 checkout 无关 |
| OPS-V1-2003 | Checkout 支付超时 | 李华侧同类事故；张明 **不可见** |

`assignee_id`：已解决单可指向王运维。`priority`：2001/2003=`HIGH`，2002=`LOW`。

新 Demo 主路径工单 **由 Chat 现场创建**，不预置 OPEN 的 checkout 单。

### 7.4 知识索引名单

Seed **不**生成向量文件。Phase C ingest 只扫契约 §6 的 Runbook 名单；Phase 10 制度语料留在仓库但不进 V1 索引。

---

## 8. 双角色 Demo 剧本（Phase E 手测真源）

**完成定义：** 张明 Chat 里看到已创建的 `ticket_no`；工单列表刷新后也有；王运维能搜到该单、写入 analysis、关到 CLOSED；用建单时的 `X-Request-ID` 能查出 Audit。

1. 将 CHECKOUT_API 置为 `DEGRADED`（seed 已是，或 Support PATCH）
2. 张明登录 → **默认进 Chat**（Phase D）
3. 「下单一直 502 / checkout 付不了款」
4. Agent 只读：服务状态、RAG、历史 OPS-V1-2001
5. HITL 确认后 `create_ticket`（`service_id=CHECKOUT_API`）
6. 张明打开「我的工单」能看到新单（禁止只看 Chat 气泡）
7. 王运维登录 → 全量列表/`q=checkout` 看到张明新单 **和** 李华历史单
8. Support PATCH：`OPEN→IN_PROGRESS`，写 `analysis`，再 `RESOLVED→CLOSED`
9. 张明不能 GET 李华的单（`40301`/`40401` 实现时二选一，Go 层统一）

---

## 9. 后续 Phase（一次只做一段）

| Phase | 改什么 | 不改什么 |
|---|---|---|
| **B** | migration + Services API + tickets q/service_id/analysis + 状态捷径 + audit 查询 + seed | Agent Tool、前端、语料 |
| **C** | Agent 白名单、Prompt、`knowledge/ops` + Milvus RAG | Go 契约形状 |
| **D** | Chat 默认入口、服务状态页、SSE 过程、工单卡片 | 新 API |
| **E** | Demo 脚本与 DEMO 文档换成上述剧本 | 新功能 |

---

## 10. Phase A 验收

```text
☑ 本文作为 V1 HTTP / 表差集 / Tool / RAG / Seed 真源
☑ 产品 8 条决策已写入 §0
☑ API.md / DATABASE.md / AI_CONTEXT / ROADMAP / PRD 指向本文
☑ Permission 标明 Legacy
☑ 未改 backend/internal、agent/app 业务逻辑、frontend/src、migrations/*.sql
☑ related_ticket_id 未写入待建列
☑ RAG 运行时勘误：bge-m3 + Milvus；禁止回退关键词；禁止知识后台
```
