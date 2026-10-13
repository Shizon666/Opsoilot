# OpsPilot — AI Development Context

> 本文档是 Cursor / AI Coding Assistant 的**长期开发上下文**。
>
> **不是 README，不介绍项目故事。**
>
> 开工前优先阅读本文件；冲突时以契约真源为准（见 §5）。
>
> 重大实现进度或冻结决策变化时，必须同步更新本文档。
>
> **V1 现行口径（Hardening H4）**：北极星 = **AI 运维故障工单助手**。RAG = **bge-m3 + Milvus**。Memory = **Checkpointer + thread_id**。主链 = **Ticket / Service Health / Audit / HITL**。Permission / 关键词 RAG / 本地 bge-small = **Legacy**。Demo 只走 [`docs/DEMO.md`](docs/DEMO.md) §1。

---

## 0. 如何使用本文档

| 场景 | 行为 |
|---|---|
| 实现功能 / 修 bug | 先读 §1–§3、§5–§7；再打开对应契约文档 |
| 想加新技术 / 新表 / 新 API | 先对照 §5 与 §7；默认拒绝，除非用户确认并回写契约 |
| 不确定 Phase 边界 | **V1：** A–E 已完成；下一刀只做 `docs/ENGINEERING_HARDENING.md` 中的单一切片 |
| 文档互相打架 | **V1 产品 / 差集 HTTP / 表增量** → `PHASE_A_V1_CONTRACT.md`；其余历史字段 → `docs/API.md` / `docs/DATABASE.md`；业务裁决在 Go Service |

**优先级（不可颠倒）：**

```text
Business Requirement
  >
Security
  >
Maintainability
  >
Engineering Practice
  >
Technology Showcase
```

**优先级（不可颠倒）：**

```text
Business Requirement
  >
Security
  >
Maintainability
  >
Engineering Practice
  >
Technology Showcase
```

---

## 1. 当前项目真实状态（以代码为准）

OpsPilot 是个人开发的 **AI 运维故障工单助手**。**V1 产品化 A–E 已完成**（2026-10-04）。  
下一阶段：**Engineering Hardening**（不扩功能）。真源：`docs/ENGINEERING_HARDENING.md`。  
Tool/hit/HTTP 差集：`docs/phases/PHASE_A_V1_CONTRACT.md`（含 RAG 运行时勘误）。

### 1.1 已落地（可运行）

| 层 | 真实状态 |
|---|---|
| **文档** | A–E 完成；Hardening 计划已写。旧 PRD/ARCHITECTURE 大量历史叙事，**禁止按「B 未开始」实现** |
| **Infra** | 主 Compose：`postgres` + `backend` + `agent`。Milvus **独立** `docker-compose.milvus.yml`。Nginx 未进主 Compose |
| **Go Backend** | Gin；JWT；Ticket + 健康服务 + `analysis` + `q`；Audit **读+写**；Permission **Legacy 全套仍在、不进 Agent 主链** |
| **DB** | roles/users/services（含 health_*）/tickets（含 analysis）/audit_logs；access_requests/approvals 冻结；seed `000015` |
| **Agent** | `/agent/chat` + stream + resume；JWT 透传；ReAct；**白名单 8 Tool（无 Permission）**；`search_knowledge` → Milvus；Checkpointer + HITL |
| **Frontend** | 登录后默认 `/agent/chat`；服务状态只读页；工单 + Support 工作台 |
| **Demo** | Checkout 502 双角色；`docs/DEMO.md` + `DEMO_CHECKLIST.md` |

### 1.2 已知限制（不是下一刀功能）

| 项 | 说明 |
|---|---|
| RAG 环境 | 知识步依赖 Milvus 已起 + ingest；失败记环境 |
| thread_id | 刷新 Chat 默认新会话（H2 可选 sessionStorage） |
| Support UI | 无 analysis 表单、无 Audit 页（API 手测） |
| 双路径遗留 | `local_store` 存在但 **不得** 接回 Tool |

### 1.3 产品演进位

```text
V1 故障工单助手     ← A–E 已完成
Engineering Hardening ← 当前（文档 / Demo 可重复 / 安全验证 / eval 分表）
V2+                 ← Phase 15 知识平台 / Phase 16 画像 / Planner / Multi-Agent
```

Permission / Onboarding / 知识后台 = **冻结或延期**，不是 Hardening 范围。

### 1.4 Known Limitations

> 下列为**已知范围裁剪 / 未来增强**，**不是**当前 Phase 5 / 6 Lite / 7 验收缺陷。  
> **禁止**据此擅自新增 API、表或改 Phase 状态；实现前须先改契约并经确认。

| ID | 主题 | 说明 | 归类 |
|---|---|---|---|
| KL-01 | `ticket_comments` 未实现 | **无** `ticket_comments` migration / Model / HTTP / 前端时间线。多轮评论仍未建表；过程协作先复用工单字段。 | **未来增强：Ticket Collaboration** |
| KL-02 | `WAITING_USER` 最小闭环 | **已落地（最小方案）**：Support「等待用户」必填 `analysis`；Employee 详情可见说明并补充 `description`，申请人可 `WAITING_USER → IN_PROGRESS`。非评论时间线；多轮仍靠字段覆盖/追加。 | **已缓解** |
| KL-03 | Agent 当前 system token | ~~Agent → Go 使用系统用户账号~~ **已关闭（Phase 8）**：业务路径用户 JWT 透传。 | **已关闭** |
| KL-04 | Agent JWT / 记忆 | JWT 透传 + thread 归属已做。Checkpointer **已落地**（Agent 库 `opspilot_agent`）。HITL 写确认 **已落地**。V1 保留 HITL，不扩审批。 | **已关闭（记忆/HITL）；V1 只改 Tool 集** |

演示建议：可用「等待用户」最小闭环（`analysis` + 用户补充 `description`）。多轮评论时间线仍属 KL-01，**不新建** `ticket_comments`。

---

## 2. 已完成 / 进行中的 Phase

**V1 产品化：** Phase A–E **完成**。下一步 **Engineering Hardening**（须用户确认切片后再改代码）。  
旧 Go Phase 0–14 视为历史底座，禁止借 Hardening 重做业务。

依据：`docs/ENGINEERING_HARDENING.md` + Phase A（含 RAG 勘误）。  
**禁止一次实现多个切片。禁止新增 Tool / 表 / 知识后台。**

| Phase | 名称 | 状态 | 说明 |
|---|---|---|---|
| **A** | V1 契约冻结 | **完成** | 产品/API/表差集/Tool；RAG 存储见勘误 |
| **B** | 数据 + Backend 主链 | **完成** | health、analysis、检索、Audit GET、seed |
| **C** | Agent 主链 + RAG | **完成** | 白名单、ops 语料、Milvus、`search_knowledge` |
| **D** | 前端演示面 | **完成** | Chat 第一入口、服务状态 |
| **E** | Demo 固化 | **完成** | Checkout 双角色 |
| **H** | Engineering Hardening | **当前** | 见 `docs/ENGINEERING_HARDENING.md` |

以下为 **历史 Go/Agent Phase**（已完成或过期计划，勿当作 V1 下一刀）：

| Phase | 名称 | 状态 | 说明 |
|---|---|---|---|
| **1** | 基础工程 | **完成** | Config / GORM 连接 / 统一响应与错误码 / Request-ID / Recovery / 路由骨架 |
| **2** | Database Migration | **部分完成（Slice A）** | 仅核心 5 表 + seed；预留表未建 |
| **3** | Auth / RBAC | **完成（最小闭环）** | `POST /auth/login`、`GET /users/me`、JWT Middleware；三角色枚举；用户 CRUD **不做** |
| **4** | Ticket + 状态机 | **完成（MVP，无 REJECTED）** | Create/List/Get/PATCH；状态机；角色字段权限；Ownership；Support seed |
| **4.5** | Frontend 工单闭环 | **完成（V0）** | Login→Create→List→Detail→Support 推进→Closed；Backend 零改动；无 Permission/Agent |
| **5** | Permission / Approval | **完成** | Create/List/Get/approve/reject；`access_requests` + `approvals`；单级审批事务 |
| **6** | Audit 打穿 | **完成（Lite）** | Ticket / Permission 写路径 Append-Only 入 `audit_logs`；**无**查询 API；Auth 登录审计未做 |
| **7** | Seed / Demo | **Completed** | Seed：Employee/Support/Agent + `GENERAL_IT`；`scripts/demo_phase7.ps1` 可重复执行；Ticket + Permission + Audit 主流程验证通过 |
| **8** | Agent 对接就绪 | **完成（8 / 8.1）** | 用户 JWT 透传；内存 thread 归属；五业务 Tool；无后门 |
| **9** | Employee Chat 入口 | **完成（最小闭环）** | `/agent/chat`；复用登录 JWT；消息列表 + Ticket/Permission 卡片；无流式/多会话/历史库 |
| **9.1** | Demo 收敛打磨 | **完成** | seed 场景数据；Agent 口语化回复规范；`docs/DEMO.md` + `DEMO_CHECKLIST.md`；不扩 Tool/API |
| **10** | Knowledge 最小 RAG | **完成（最小）** | 8 篇语料正文；`search_knowledge` top-k；无向量库/无 rerank/无知识后台 |
| **12** | Employee Context | **完成（最小）** | `users.position` + `employee_level`；`/users/me` 返回员工上下文；Agent 可引用、不可作授权；无画像表 |
| **13** | Agent Streaming | **完成（最小 SSE）** | `POST /agent/chat/stream`；真实 LLM token；`tool_start/end` 对齐 tool_call_id；同步 `/agent/chat` 保留 |

**Phase 0 冻结决议（实现时不得擅自改形状）：**

| # | 决议 |
|---|---|
| R1 | ID 统一 **UUID** |
| R2 | 登录字段名 `username`，语义=登录标识，**按 `users.email` 查找** |
| R3 | HTTP 用 `PATCH`；**Service 内映射合法动作**，禁止非法状态跳转 |
| R4 | 库字段 `requester_id`；创建 requester **只从 JWT**；`service_id` 创建必填（实现可有默认 service，但仍须合法存在） |
| R5 | Permission API 字段以 **DB** 为准（`resource_type` / `resource_name` / `permission_level` + `service_id`） |
| R6 | 库内**大写枚举**；API 可收小写，Handler/DTO 转大写进 Service |
| R7 | `expires_in` 跟配置 `JWT_EXPIRE_*` |
| R8 | MVP：Nginx → Agent；Go 对 Agent→Go **二次鉴权**；不改路由架构 |
| R9 | MVP **无用户管理 CRUD API** |
| R10 | **无独立 Onboarding HTTP**；表可建 ≠ 写 Service/API |

---

## 3. 当前代码架构

### 3.1 运行单元（当前 Compose）

```text
React :5173（Vite proxy → Go `/api` + Agent `/agent`；未进 Compose）
        │
        │  （目标：Nginx；当前开发用 proxy）
        ▼
┌───────────────┐     ┌────────────────┐
│  Go Backend   │◄────│ Python Agent   │
│  Gin :8080    │     │ FastAPI :8000  │
└───────┬───────┘     └────────────────┘
        │
        ▼
   PostgreSQL 16
```

- Agent **禁止**直连 PostgreSQL。
- 开发前端：`/api` → `:8080`；`/agent` → `:8000`（超时 120s）。
- 业务事实只在 Go：`Handler → Service → Repository → GORM → PostgreSQL`。

### 3.2 Go Backend 分层（必须保持）

```text
backend/
├── cmd/server/          # 装配：config → db → repo → service → handler → router
├── internal/
│   ├── handler/         # 绑定 / 格式校验 / 调 Service / 写 Response
│   ├── service/         # 业务规则唯一归属
│   ├── repository/      # 纯数据访问；禁止业务语义方法名
│   ├── model/           # 表映射 + 枚举常量；无状态机/授权
│   ├── middleware/      # Request-ID / Recovery / JWT
│   ├── router/
│   ├── config/
│   ├── database/
│   └── pkg/             # response / apperr / jwt
└── （migrations 在仓库根 ./migrations，Compose 挂载）
```

### 3.3 已挂载的 HTTP（真实）

```text
GET  /health
POST /api/v1/auth/login
GET  /api/v1/users/me                    # JWT
POST /api/v1/tickets                     # JWT
GET  /api/v1/tickets                     # JWT（Employee 仅自己；Support/Admin 全量）
GET  /api/v1/tickets/:id                 # JWT
PATCH /api/v1/tickets/:id                # JWT + 状态机 / 字段权限
POST /api/v1/permissions                 # JWT（字段：resource_type / resource_name / permission_level / reason）
GET  /api/v1/permissions                 # JWT
GET  /api/v1/permissions/:id             # JWT
POST /api/v1/permissions/:id/approve     # JWT（IT_SUPPORT / ADMIN）
POST /api/v1/permissions/:id/reject      # JWT（IT_SUPPORT / ADMIN）
# 无 GET /audit* — Audit Lite 仅写库，用 SQL 验收
```

Agent：

```text
GET  /internal/health          # 容器自检，非对外统一 /health
POST /agent/chat
```

### 3.4 Agent 当前结构（最小）

```text
agent/app/
├── main.py
├── clients/backend.py       # Business Client（JWT 透传）
├── graph/agent.py           # DeepSeek + LangGraph ReAct + HITL
├── rag/retriever.py         # 现网：Milvus + bge-m3
├── rag/local_store.py       # 遗留；禁止接回 Tool
└── tools/
    ├── user / service / ticket / knowledge  # 运行时白名单
    └── permission.py                        # Legacy 包内仍在，不绑定 Graph
```

Checkpointer / HITL **已落地**。运行时 RAG = Milvus。评测平台 **不做**；V1 P0 见 `app.evaluation.runner --v1`。

### 3.5 核心业务对象

```text
User / Role / Service / Ticket / AuditLog     # V1 主链
AccessRequest / Approval                      # Legacy 已建，冻结
KnowledgeDocument / ticket_comments / role_resources / user_resources  # V1 不建
```

角色仅：`EMPLOYEE` / `IT_SUPPORT` / `ADMIN`。

---

## 4. 已确定的技术选型（冻结）

| 层 | 选型 | 状态 |
|---|---|---|
| Frontend | React + TypeScript + Vite + React Router + Zustand + Ant Design + Axios | **已在用**（Chat 默认入口） |
| Backend | **Go 1.22 + Gin + GORM + JWT** | 已确认并在用 |
| DB | **PostgreSQL 16**（Compose：`postgres:16-alpine`） | 已确认并在用 |
| Agent | Python + **FastAPI + LangGraph** | FastAPI + ReAct + Checkpointer + HITL + SSE **已在用** |
| Embedding（V1） | SiliconFlow **`BAAI/bge-m3`** | 运行时；local bge-small 为遗留 |
| Vector DB | **Milvus**（独立 compose，`knowledge_docs`） | C-3 已接入；禁止知识后台 |
| Short-term Memory | LangGraph Checkpointer + `thread_id` | **已实现** |
| Long-term Memory | PostgreSQL 结构化事实（`users.*` + 工单） | 不新建 Memory 向量库 |
| 部署 | Docker Compose（+ 契约中的 Nginx） | Compose 部分服务；Nginx 延期 |
| Cache | **MVP 不引入 Redis** | 冻结为非必须 |

**明确拒绝 / 延期（不要「顺便加」）：**

```text
Kubernetes / Kafka / RabbitMQ / Service Mesh / 微服务拆分
完整 ITIL / CMDB / SLA / 真实 GitLab·LDAP·AD
Memory 独立向量库 / 强制 Rerank / 复杂 CI/CD
用户管理 CRUD API / Onboarding 独立 HTTP / PUT·DELETE
为 Agent 开后门 API 或弱化鉴权的 internal 特例
```

---

## 5. 不能破坏的工程约束

### 5.1 契约真源

| 主题 | 真源 |
|---|---|
| **V1 产品 / 新 API / 表差集 / Tool 名与 hit** | **`docs/phases/PHASE_A_V1_CONTRACT.md`** |
| **下一阶段范围** | **`docs/ENGINEERING_HARDENING.md`** |
| 运行时 RAG 存储 | C-3 / Phase A 勘误（Milvus + bge-m3） |
| 历史 HTTP 包络 / Permission Legacy 形状 | `docs/API.md` |
| 历史全库叙述（11 表已作废 DoD） | `docs/DATABASE.md`（差集以 Phase A 为准） |
| 分层与状态机语义 | `docs/ARCHITECTURE.md`（产品叙事以 Phase A 为准） |
| 二次鉴权 / 身份不可信 body / HITL≠Approval | `docs/SECURITY.md` |
| 旧 Backend Phase 纪律 | `docs/GO_BACKEND_IMPLEMENTATION_PLAN.md` |
| 产品原则（须服从 V1 北极星） | `PROJECT_CONTEXT.md` |

新增端点 / 新表 / 新字段：**先改文档并经确认，再改代码。**  
实现中途缺字段：**禁止擅自补 migration**；先提 `DATABASE.md` 变更建议。

### 5.2 分层铁律

```text
Handler  → 无业务裁决、无状态机、无多表事务编排、不直连 GORM
Service  → RBAC / Ownership / 字段权限 / 状态机 / 事务 / 触发审计
Repository → 仅 CRUD/查询；禁止 Approve/Reject/AssignTicket 等业务语义方法名
Model    → 映射与枚举；无授权逻辑
Agent    → 不直连业务库；业务读写一律 Go /api/v1/*
```

### 5.3 安全铁律

```text
前端隐藏按钮 ≠ 安全边界
LLM / Prompt ≠ 业务授权
Tool 被调用 ≠ 操作已授权
Go Service = 最终业务授权边界

user_id / role 只从可信 JWT 解析，禁止信任 body / query
Agent → Go 必须再次独立鉴权
HITL Confirmation ≠ 业务 Approval
```

### 5.4 Ticket / Approval 语义

- Ticket 状态迁移由 **Service 状态机**控制，禁止万能随意改 `status`。
- AccessRequest 与 Approval **分离**；不能用 Ticket.status 代替审批。
- 终态再审批 → `40901`；无权限 → `40301`。

### 5.5 范围铁律

- **V1 业务范围**以故障工单闭环为准；Permission 冻结；不为凑 11 张表建预留表。
- **不为流行加组件**（Redis / MQ / 微服务等无当前业务驱动则不做）。
- **不提前设计未来问题**（不为 V2/V3 预建复杂基础设施）。
- **功能优先最小可运行闭环**。
- **禁止一次实现多个 Phase**。

### 5.6 Cursor 实现协议（Backend）

动手前必须先输出并经用户确认：

1. 当前 Phase 目标理解  
2. 将修改文件列表  
3. 不会修改的范围  
4. 验收方式  

完成后输出：实际改动、运行命令、验收结果、遗留问题。

---

## 6. 下一阶段开发目标

**立即目标：Engineering Hardening**（仅在用户明确要求开始某一切片时改代码）。  
不要补 Permission UI、知识后台、Phase 16 画像、11 表、新 Tool。

切片顺序（摘录）：

```text
H0 文档对齐     ← 本批已做主体
H1 Demo 可重复  ← 环境 + checklist，不改业务
H4 Evaluation   ← V1 yaml 为金标；Legacy 分表
H2 thread_id    ← 仅 sessionStorage，须另开确认
H3 安全验证     ← 补用例，不改鉴权模型
H5 双路径克制   ← 不把 local_store 接回 Tool
```

| 主题 | Hardening | 备注 |
|---|---|---|
| Agent | 不新增 Tool | 白名单已冻 |
| RAG | 保持 Milvus 单路径 | 禁止第二套生产索引 |
| HITL | 保持写确认 | HITL ≠ Approval |
| Memory | 不新建系统 | H2 只动前端 thread 复用 |

### 6.3 明确不是下一阶段

```text
Router / Multi-Agent / Planner / Executor
Evaluation 平台化
知识 CMS / 可见性平台 / Memory 向量库
用户 CRUD / Onboarding HTTP
Nginx 之前先堆微服务
```

---

## 7. 开发原则

### 7.1 总原则

1. **业务优先，Agent 第二** — 技术必须回答「业务为什么需要它」。  
2. **业务面完整，技术面克制** — 大体量业务边界，小实现。  
3. **能力做真实，数据做最小** — 演示数据少，能力边界不造假。  
4. **架构允许演进，当前只解决当前问题** — Workflow → Single Agent → Router → Multi-Agent → Planner，逐步有业务理由再升级。  
5. **安全不能依赖 LLM** — 权限、校验、状态迁移、写库、高风险操作由 Backend 最终控制。  
6. **最小可运行闭环** — 每次交付必须能演示一条完整路径，而不是半套框架。

### 7.2 AI 助手行为准则

- 不擅自扩大业务范围或 MVP API。  
- 不为展示技术栈添加组件。  
- 提出新技术方案时必须说明：解决什么问题、为何需要、替代方案、复杂度代价。  
- 发现架构/契约漏洞应直接指出并提议修正，而不是延续错误。  
- 外部企业系统集成必须标注 **Simulated / Mocked**，不虚构真实集成经验。  
- 确定性业务用 Backend / Workflow，不交给 LLM。  
- Agent 只做：理解、规划、选工具、自然语言交互。  
- 不为 Multi-Agent / Planner 而强行上 Multi-Agent / Planner。

### 7.3 实现节奏

```text
钉可验收需求 → 对齐契约 → 单 Phase 最小实现 → 自检分层/安全 → 更新本文件进度
```

验收优先看：**用户/调用方能完成的主路径** + 契约字段一致 + 关键态（无权限/冲突）正确；不是「目录里有文件」。

---

## 8. 文档索引（按需打开，禁止整本塞进上下文）

| 文件 | 用途 |
|---|---|
| `AI_CONTEXT.md`（本文件） | AI 长期开发上下文与真实进度 |
| `PROJECT_CONTEXT.md` | 产品总地图、原则、决策与演进叙事 |
| `docs/API.md` | HTTP 契约 |
| `docs/DATABASE.md` | 库表契约 |
| `docs/ARCHITECTURE.md` | 系统分层与职责边界 |
| `docs/SECURITY.md` | 安全边界 |
| `docs/GO_BACKEND_IMPLEMENTATION_PLAN.md` | Backend Phase 纪律（历史） |
| `docs/ENGINEERING_HARDENING.md` | V1.1 完成度 / 风险 / Hardening 切片 |
| `docs/DEMO.md` / `DEMO_CHECKLIST.md` | V1 Checkout Demo |
| `ROADMAP.md` | 路线总表（A–E 完成） |
| `docs/PRD.md` / `AGENT_DESIGN.md` / `EVALUATION.md` | 历史需求与评测（V1 金标是 `cases_c42.yaml`） |

---

## 9. North Star（一句话）

> 从真实 IT 服务业务出发，先建确定性业务系统，再让 Agent 进入业务；技术复杂度必须由业务复杂度推动，而不是反过来。

---

*最后根据仓库真实代码整理。若实现推进导致 Phase 状态变化，请更新 §1 与 §2。*
