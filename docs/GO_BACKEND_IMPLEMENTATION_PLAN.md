# OpsPilot — Go Backend 实施规划

> Version: v1.1  
> Status: **历史 Go Phase 0–14 规划**；**V1 Backend 差集以 `docs/phases/PHASE_A_V1_CONTRACT.md` 为准（Phase B 才改代码）**  
> Project: OpsPilot — AI 运维故障工单助手  
> 下文 Phase 表仍是原 IT 服务底座落地顺序，**不要当作 V1 下一刀**。 Permission 已落地且 **Legacy 冻结**。

---

## 0. 冻结约束（不可再议）

### 0.1 技术栈（已冻结）

| 项 | 取值 |
|---|---|
| 语言 | Go **1.22** |
| Web | **Gin** |
| ORM | **GORM** |
| DB | **PostgreSQL**（Compose：`postgres:16-alpine`） |
| 部署 | **Docker Compose** + Nginx |
| Cache | MVP **不引入 Redis** |

### 0.2 分层铁律（每阶段必须遵守）

```text
Handler  → 仅：绑定 / 基础格式校验 / 调 Service / 写 Response
Service  → 业务规则核心：RBAC、Ownership、状态机、事务编排、审计触发
Repository → 仅：数据访问（CRUD / 查询）；不含业务裁决；禁止业务语义方法名
Model    → 表映射与枚举；不含状态机 / 授权逻辑
Agent    → 禁止直连 PostgreSQL；业务读写一律经 Go `/api/v1/*`
```

禁止：

- Handler 直接操作 GORM / Repository
- Service 绕过 Repository 散落 SQL（除明确的事务边界封装）
- 为 Agent 开「后门 API」或弱化鉴权的内部特例
- 用 LLM / Prompt 决定状态迁移、审批结果、字段权限

**Repository 方法命名铁律（防「看起来像数据层、实际含业务」）：**

| 允许（纯数据访问） | 禁止（业务语义，必须由 Service 编排） |
|---|---|
| `GetByID()` / `ListByUser()` / `Create()` / `Update()` | `Approve()` / `Reject()` / `AssignTicket()` / `ResolveTicket()` |
| `ListByFilter()` / `UpdateFields()` / `Count()` | `GrantPermission()` / `CloseAsResolved()` / 任何隐含状态机/审批结果的方法名 |

业务动作（审批、指派、解决、拒绝等）**只能**出现在 Service；Repository 只做字段级读写与查询条件拼装。

### 0.3 契约真源

| 主题 | 真源 |
|---|---|
| **V1 HTTP / 表差集** | `docs/phases/PHASE_A_V1_CONTRACT.md` |
| 历史 HTTP 路径 / Method / 响应包络 | `docs/API.md` |
| 表结构 / 状态集合 / 事务示例 | `docs/DATABASE.md`（V1 列以 Phase A 为准） |
| 分层与状态机语义 | `docs/ARCHITECTURE.md` |
| 二次鉴权 / 身份不可信 body | `docs/SECURITY.md` |

冲突消解规则：**V1 差集跟 Phase A；其余 HTTP 跟 API.md；库表跟 DATABASE.md；业务裁决在 Service。**

### 0.4 当前仓库起点（事实）

- 已有：`cmd/server` + Gin + `GET /health`、空分层目录、Compose/Nginx
- 缺失：GORM 依赖、Model、Migration、JWT、全部 `/api/v1/*`、Audit、种子数据

---

## 1. 总览：开发阶段

| Phase | 名称 | 性质 | 产出锚点 |
|---|---|---|---|
| **0** | 契约冲突修正 | 文档决议（阻塞编码） | 决议清单勾选完毕 |
| **1** | 基础工程 | 横切能力 | Config / DB 连接 / 统一响应 / 路由骨架 |
| **2** | Database Migration | 结构落地 | migration + model 映射；无业务 Service/API |
| **3** | Auth / RBAC | 身份闭环 | Login + `/users/me` + JWT Middleware |
| **4** | Ticket + 状态机 | 核心业务闭环 A | Ticket CRUD/PATCH + Service 状态机 |
| **5** | Permission / Approval | 核心业务闭环 B | 申请 + 审批/拒绝 + 终态冲突 |
| **6** | Audit 打穿 | 可追溯 | 关键路径 Append-Only 审计 |
| **7** | Seed / Demo 可跑通 | 演示就绪 | Compose 下一键演示路径 |
| **8** | Agent 对接就绪 | 边界加固（仍无 Agent 代码） | 同一套 API 可被 Agent Client 调用 |

建议节奏（对齐 7 日计划中的 Backend 日）：**Phase 0→3 ≈ Day 2；Phase 4→6 ≈ Day 3；Phase 7→8 收尾并联调准备。**

---

## 2. Phase 0 — 契约冲突修正

### 目标

在写业务代码前，消解分析报告指出的文档冲突，形成**可勾选决议**，避免实现中途改字段形状。

### 涉及模块

- 文档：`API.md` / `DATABASE.md`（必要时 `ARCHITECTURE.md` 补一句说明）
- 不涉及 Go 业务代码

### 新增文件

- 无强制新文件；可将决议摘要回写本规划 §2.1（推荐）或在各文档「已知差异」节标注「已决议」

### 数据库变化

- 无实际 Migration；仅确认字段命名与类型约定

### API 变化

- **仅文档级对齐**，不扩端点、不删 MVP 端点

### 决议清单（MVP 必须拍板）

| # | 冲突 | MVP 决议（冻结） |
|---|---|---|
| R1 | ID：API 示例整数 vs DB UUID | **统一 UUID**；API 示例改为 UUID 字符串 |
| R2 | 登录：`username` vs `email` | **请求字段保留 `username`**，语义 = 登录标识，**存储与查找以 `users.email` 为准**（`username` 传 email） |
| R3 | Ticket 更新：万能 PATCH vs 显式动作 | **对外 HTTP 用 `PATCH`**（跟 API.md）；**Service 内映射为动作**（assign/start/wait/resolve/close/reject），禁止非法跳转 |
| R4 | Ticket 创建：`creator_id` vs `requester_id`；缺 `service_id` | **库表用 `requester_id`**；创建时 requester 从 JWT 取，**禁止信任 body 用户 ID**；**`service_id` 为创建必填**（API 补齐） |
| R5 | Permission：`resource/permission` vs `resource_type/name/permission_level` + `service_id` | **库字段为准**；API 请求/响应字段对齐 DB；HTTP 资源名仍为 `/permissions` |
| R6 | 状态/角色大小写 | **库内大写枚举**；API 边界可接受小写，**Handler/DTO 映射层统一转大写进 Service** |
| R7 | JWT `expires_in` | **以配置 `JWT_EXPIRE_*` 为准**；登录响应 `expires_in` 与配置一致 |
| R8 | Agent 入口：Go 代理 vs Nginx 直达 | **MVP 保持 Nginx → Agent**；Go 对 Agent→Go 调用做二次鉴权；不改路由架构 |
| R9 | Admin / 用户管理 | **MVP 不做用户 CRUD API**；Admin 能力靠种子用户 + 审批/工单权限 |
| R10 | Onboarding HTTP | **不做独立 Onboarding API**；表可在 Phase 2 建 + model；**不**在未开 Phase 时写 Onboarding Service / 暴露 HTTP |

### 验收标准

- [ ] R1–R10 全部勾选，且与 `API.md` §18.3 建议不矛盾或已回写文档
- [ ] 后续 Phase 不得在未改本文档的情况下擅自改字段形状
- [ ] 明确：**不新增表、不新增 MVP 未列出的公开 API**

---

## 3. Phase 1 — 基础工程

### 目标

把可运行的 Gin 骨架升级为「可接业务」的工程底座：配置完整、PostgreSQL 可连、统一响应/错误码、路由分组、依赖注入方向清晰。

### 涉及模块

- `cmd/server`
- `internal/config`
- `internal/database`
- `internal/router`
- `internal/middleware`（Request-ID / Recovery；JWT 留 Phase 3）
- 公共包：`internal/pkg/response`、`internal/pkg/errors`（或等价命名）

### 新增文件（建议路径，实现时可微调文件名，不得破坏分层）

```text
backend/
├── cmd/server/main.go                    # 装配：config → db → repo → service → handler → router
├── internal/config/config.go             # 补齐 JWT / DB DSN / expire
├── internal/database/database.go         # GORM Open + Ping
├── internal/pkg/response/response.go     # {code,message,data}
├── internal/pkg/apperr/apperr.go         # 40001/40101/40301/40401/40901/5000x
├── internal/middleware/request_id.go
├── internal/middleware/recovery.go
└── internal/router/router.go             # /health + /api/v1 分组占位
```

引入依赖（规划级）：`gorm.io/gorm`、`gorm.io/driver/postgres`；JWT/crypto 在 Phase 3。

### 数据库变化

- 无表结构变更；仅验证 Compose 中 Postgres 连通

### API 变化

| 方法 | 路径 | 变化 |
|---|---|---|
| GET | `/health` | 保持；可增强为含 DB ping 状态（可选，不破坏契约） |
| — | `/api/v1/*` | 路由组存在，业务 handler 尚未挂载 |

### 验收标准

- [ ] `go.mod` 含 GORM + postgres driver；`go build ./...` 通过
- [ ] Compose 下 Backend 启动可 Ping PostgreSQL
- [ ] 统一错误响应形状与 `API.md` 一致
- [ ] **仍无**业务逻辑落在 Handler；空 Service/Repo 仅占位也可，但禁止 Handler→GORM
- [ ] Redis / MQ / 微服务拆分 **未引入**

### 当前 Phase 完成定义（禁止提前实现）

**只实现本阶段验收内容。** 即使目录/接口骨架已准备好，也**不要填充**后续业务逻辑。

禁止在本 Phase 提前实现：

- JWT / Token 签发与校验
- User API（含 `/users/me`）
- Ticket 相关 Handler/Service/Repository 业务逻辑
- Permission / Approval 业务逻辑
- Agent Client 或任何 Agent 对接代码
- Auth Service、密码校验、RBAC 裁决

允许：空目录、空接口、TODO 占位、依赖注入接线方向注释；**禁止**把占位填成可运行业务。

### MVP / 延期

| MVP | 延期 |
|---|---|
| 同步 HTTP、标准库或 Zap 级日志、Request-ID | Redis、分布式 tracing、复杂配置中心、热更新 |

---

## 4. Phase 2 — Database Migration

### 目标

**仅完成 `DATABASE.md` 定义的业务数据结构落地**：按文档建表与必要索引；结构真相来自 Migration，不以 AutoMigrate 作为唯一真相。

本阶段交付物仅限：**Migration SQL + GORM Model 映射**。  
**不**因「表已建」而顺带实现 Repository / Service / HTTP。

### 涉及模块

- `backend/migrations/`
- `internal/model/*`
- （可选）Migration runner 脚本或 Compose 启动步骤说明

### 新增文件

```text
backend/migrations/
├── 000001_init_roles.up.sql
├── 000001_init_roles.down.sql
├── 000002_init_users.up.sql / .down.sql
├── 000003_init_services.up.sql / .down.sql
├── 000004_init_tickets.up.sql / .down.sql
├── 000005_init_ticket_comments.up.sql / .down.sql
├── 000006_init_access_requests.up.sql / .down.sql
├── 000007_init_approvals.up.sql / .down.sql
├── 000008_init_role_resources.up.sql / .down.sql
├── 000009_init_user_resources.up.sql / .down.sql
├── 000010_init_knowledge_documents.up.sql / .down.sql
└── 000011_init_audit_logs.up.sql / .down.sql

backend/internal/model/
├── role.go
├── user.go
├── service.go
├── ticket.go
├── ticket_comment.go
├── access_request.go
├── approval.go
├── role_resource.go
├── user_resource.go
├── knowledge_document.go
└── audit_log.go
```

建表顺序（冻结）：

```text
roles → users → services → tickets → ticket_comments
→ access_requests → approvals → role_resources → user_resources
→ knowledge_documents → audit_logs
```

### 数据库变化

| 变化 | 说明 |
|---|---|
| 按 `DATABASE.md` 建表 | 字段、FK、索引对齐文档；**不得自行增删字段** |
| 主键 | 全部 **UUID** |
| 状态字段 | VARCHAR + 应用层枚举；不做复杂 PG ENUM |
| audit_logs | Append Only；无业务更新路径 |
| 不做 | 新表、Agent Trace 表、Evaluation 表、Memory 独立表 |

**未来能力预留表（建表 ≠ 实现能力）：**

| 表 | 本 Phase | 后续 |
|---|---|---|
| `knowledge_documents` | 仅 migration + model | Knowledge HTTP / RAG 对接另开 Phase |
| `role_resources` | 仅 migration + model | Resource 管理接口另开 Phase |
| `user_resources` | 仅 migration + model | Resource 管理接口另开 Phase |

> Onboarding 相关表若在 `DATABASE.md` 中定义：同样 **只建表 + model**；不暴露 HTTP、不写 Onboarding Service（对齐 R10）。

### API 变化

- 无 HTTP 变化

### 验收标准

- [ ] 空库执行 up migration 成功；down 可回滚（至少 init 可逆）
- [ ] GORM Model 与表字段一一对应；**Model 内无状态机/授权代码**
- [ ] 索引覆盖：`tickets(requester_id, assignee_id, service_id, status, created_at)`、`ticket_no` 唯一等（按 DATABASE）
- [ ] Agent 进程配置中 **无** 业务库直连用途（边界声明写进本阶段检查单）
- [ ] **无** Knowledge / Onboarding / Resource 的 Repository 业务方法、Service、HTTP Handler

### 当前 Phase 完成定义（禁止提前实现）

**只实现本阶段验收内容：migration + model 映射。**

禁止在本 Phase 实现（即使表已存在）：

- `knowledge_repository.go` 及一切 Knowledge HTTP API
- `onboarding_service.go` 及 Onboarding 业务编排
- Resource 管理接口（`role_resources` / `user_resources` 的 CRUD API）
- Agent Tool 对接
- JWT、User API、Ticket Service、Permission Service、Auth 业务逻辑

除非后续 Phase **明确开启**，否则不得因「表齐了」而填充上述逻辑。

### MVP / 延期

| MVP | 延期 |
|---|---|
| Migration + Model 映射（含预留表结构） | Knowledge HTTP、Onboarding Service、Resource 管理接口、Agent Tool 对接、多级审批表、策略引擎表、软删除平台化、分区表 |

---

## 5. Phase 3 — Auth / RBAC

### 目标

实现登录发 JWT、鉴权中间件、当前用户查询；角色进入 Token / Context，为后续 Service 授权奠基。

### 涉及模块

- `handler/auth`、`handler/user`
- `service/auth`、`service/user`
- `repository/user`、`repository/role`
- `middleware/auth`（JWT）
- `pkg/jwt`（或 `internal/auth/token`）

### 新增文件

```text
backend/internal/handler/auth_handler.go
backend/internal/handler/user_handler.go
backend/internal/service/auth_service.go
backend/internal/service/user_service.go
backend/internal/repository/user_repository.go
backend/internal/repository/role_repository.go
backend/internal/middleware/jwt.go
backend/internal/pkg/jwt/jwt.go
```

### 数据库变化

- 无新表；依赖 `users` / `roles`
- **密码字段必须以 `DATABASE.md` 为准**（例如文档已定的哈希字段名/类型）
- **禁止**在实现过程中「发现缺字段就补 migration / 改 Model」

若缺少认证所需字段：

1. **先暂停本 Phase 实现**
2. 提交 `DATABASE.md` 变更建议（字段名、类型、是否可空、索引）
3. **未经确认不得修改** Migration、Model 或数据库结构
4. 确认并回写 `DATABASE.md` 后，再继续 Auth 实现

### API 变化

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/login` | `username`(=email) + password → token + expires_in + 用户摘要 |
| GET | `/api/v1/users/me` | 需 JWT；返回当前用户与角色 |
| — | `/api/v1/users` 等 | **不做** |

角色（冻结）：`EMPLOYEE` / `IT_SUPPORT` / `ADMIN`（API 边界可映射为小写）。

### 验收标准

- [ ] 错误密码 → `40101`；无 Token 访问受保护路由 → `40101`
- [ ] Token 中身份可被 Middleware 解析进 Context；**Handler/Service 不信任 body 中的 user_id/role**
- [ ] `/users/me` 仅返回当前用户
- [ ] Handler 无密码校验/哈希逻辑细节外泄到层外——校验在 Service，持久化在 Repository
- [ ] 三角色种子用户可登录（可与 Phase 7 合并种子，本阶段至少 1 个可测用户）

### MVP / 延期

| MVP | 延期 |
|---|---|
| 密码登录 + JWT + 三角色 RBAC 基础 | OAuth/OIDC、LDAP/AD、Refresh Token 轮换、用户管理 CRUD、细粒度权限策略引擎 |

---

## 6. Phase 4 — Ticket + 状态机

### 目标

落地工单列表/创建/详情/PATCH；在 **Service** 内实现状态机与字段级权限；Employee 可见范围与 IT Support/Admin 处理范围符合 `API.md`。

### 涉及模块

- `handler/ticket`
- `service/ticket`（含状态机）
- `repository/ticket`、`repository/ticket_comment`（评论可先内部写，HTTP 评论 API 若未在 MVP 总览则不暴露）
- `repository/service`（IT Service 目录只读查询，支撑创建校验）
- DTO / 映射：API 小写 ↔ DB 大写；`requester_id` 等

### 新增文件

```text
backend/internal/handler/ticket_handler.go
backend/internal/service/ticket_service.go
backend/internal/service/ticket_state_machine.go   # 合法迁移表；禁止散落 if
backend/internal/repository/ticket_repository.go
backend/internal/repository/ticket_comment_repository.go
backend/internal/repository/service_repository.go
backend/internal/dto/ticket_dto.go                # 可选：请求/响应映射
```

### 数据库变化

- 读写 `tickets`；状态变更时可写 `ticket_comments`（SYSTEM / SUPPORT_NOTE）
- 无新表

### API 变化

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/tickets` | 分页；可见范围按角色 |
| POST | `/api/v1/tickets` | 创建；requester 来自 JWT；需 `service_id` 等（按 Phase 0 R4） |
| GET | `/api/v1/tickets/{id}` | 详情 + Ownership |
| PATCH | `/api/v1/tickets/{id}` | 部分更新；`{}` → `40001` |

**Service 内 PATCH 语义（冻结）：**

- Employee：仅 `title` / `description` / `priority`（且受 Ownership）
- IT Support / Admin：另可改 `status` / `assignee_id`，但 **status 必须是合法迁移**
- 非法迁移 / 无权限字段 → `40301` 或 `40901`（按契约语义区分）

状态集合（DB）：

```text
OPEN → ASSIGNED → IN_PROGRESS ↔ WAITING_USER → RESOLVED → CLOSED
OPEN → REJECTED
```

### 验收标准

- [ ] Employee 不能查看/修改他人工单
- [ ] Employee PATCH `status` 被拒绝
- [ ] IT Support 合法 `OPEN→ASSIGNED→…` 成功；`OPEN→CLOSED` 等非法跳转失败
- [ ] 创建不接受客户端伪造的 requester
- [ ] Handler 无状态判断；状态机仅在 Service
- [ ] Repository 无「是否允许迁移」判断

### MVP / 延期

| MVP | 延期 |
|---|---|
| 上述 4 个 HTTP + Service 状态机 + 列表过滤 | 独立 `assignTicket` HTTP 端点拆分、SLA、工单合并/关联、完整评论公开 API、附件 |

---

## 7. Phase 5 — Permission / Approval

### 目标

实现权限申请与审批闭环；HTTP 资源名 `/permissions`，Repository 映射 `access_requests` + `approvals`。

### 涉及模块

- `handler/permission`
- `service/access_request`（或 `permission_service`）
- `repository/access_request`、`repository/approval`
- 事务：创建申请、审批通过/拒绝

### 新增文件

```text
backend/internal/handler/permission_handler.go
backend/internal/service/access_request_service.go
backend/internal/repository/access_request_repository.go
backend/internal/repository/approval_repository.go
backend/internal/dto/permission_dto.go
```

### 数据库变化

- 写 `access_requests`、`approvals`
- 创建事务（对齐 DATABASE §20）：

```text
BEGIN
  Create AccessRequest (PENDING)
  Create Approval (PENDING)
  Create AuditLog          # 可与 Phase 6 同步接入
COMMIT
```

- 审批事务：校验 PENDING → 更新 AccessRequest + Approval → AuditLog

### API 变化

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/permissions` | 创建申请 |
| GET | `/api/v1/permissions` | 列表 |
| GET | `/api/v1/permissions/{id}` | 详情 |
| POST | `/api/v1/permissions/{id}/approve` | 仅 IT Support / Admin |
| POST | `/api/v1/permissions/{id}/reject` | 仅 IT Support / Admin |

字段对齐 Phase 0 R5：`service_id`、`resource_type`、`resource_name`、`permission_level`、`reason`。

状态：`PENDING / APPROVED / REJECTED / CANCELLED`（MVP 可不暴露 cancel HTTP）。

### 验收标准

- [ ] Employee 可申请；不能 approve/reject
- [ ] 非处理角色审批 → `40301`
- [ ] 终态再审 → `40901`
- [ ] 列表可见范围符合角色（申请人看自己；Support/Admin 看处理范围）
- [ ] 无 Handler 内直接改两表；事务边界在 Service

### MVP / 延期

| MVP | 延期 |
|---|---|
| 单级审批 + 五端点 | 多级审批、审批模板、CANCELLED 公开 API、真实 GitLab/LDAP 开通 |

---

## 8. Phase 6 — Audit 打穿

### 目标

关键路径写入 `audit_logs`（Append Only）；为安全验收与演示提供可追溯证据。

### 涉及模块

- `service/audit` + `repository/audit_log`
- 由 Auth / Ticket / AccessRequest Service **调用**，不由 Handler 直接写

### 新增文件

```text
backend/internal/service/audit_service.go
backend/internal/repository/audit_log_repository.go
backend/internal/model/audit_log.go   # 若 Phase 2 已建则复用
```

### 数据库变化

- 仅插入 `audit_logs`；**禁止** Update/Delete 业务路径

### API 变化

- **MVP 不新增** 审计查询公开 API（Admin 审计 UI 可后续再开只读接口）
- 既有写接口行为增加副作用：成功路径落审计

### 必须审计的动作（MVP）

| 动作 | 触发点（Service） |
|---|---|
| 登录成功/失败（失败可选） | AuthService |
| 创建工单 | TicketService |
| 工单状态/关键字段变更 | TicketService |
| 创建权限申请 | AccessRequestService |
| 审批通过/拒绝 | AccessRequestService |

### 验收标准

- [ ] 上述成功路径均有审计行；含 actor、action、resource、request_id（若有）
- [ ] 无 Repository/Handler 提供「改审计」方法
- [ ] Agent 即使未来调用同一 API，审计仍记真实 JWT 身份

### MVP / 延期

| MVP | 延期 |
|---|---|
| Append-Only 写入关键路径 | 审计检索 API、导出、完整性签名、SIEM 对接 |

---

## 9. Phase 7 — Seed / Demo 可跑通

### 目标

最小种子数据 + Compose 验证「登录 → 建单 → 处理 → 权限申请 → 审批」全路径，无需前端也可 curl/httpie 验收。

### 涉及模块

- `migrations` seed 或 `cmd/seed` / `scripts/seed.sql`
- Docker Compose 文档说明（README 补运行步骤即可，非必须新大文档）

### 新增文件

```text
backend/migrations/000012_seed_demo.up.sql   # 或
backend/cmd/seed/main.go
backend/scripts/demo_smoke.sh               # 可选：HTTP 冒烟顺序
```

### 数据库变化

种子内容（对齐 DATABASE §21，可裁剪）：

```text
Roles:     EMPLOYEE / IT_SUPPORT / ADMIN
Services:  至少 3–5 个（含 GitLab / DB / DevEnv 等）
Users:     每角色 ≥1，密码已知
Tickets:   覆盖多种状态（可选预置）
AccessRequest: 至少 1 条 PENDING 供审批演示
RoleResource / UserResource: 可选预置（不暴露 HTTP）
```

### API 变化

- 无新端点；仅数据就绪

### 验收标准

- [ ] Compose：`postgres` + `backend` 启动后 migration + seed 成功
- [ ] 手测路径（L2）：员工登录 → 创建工单 → Support 登录 → PATCH 推进状态 → 员工创建 permission → Support approve
- [ ] 非法路径手测：跨用户读工单、非法状态、员工审批 → 均失败且错误码正确
- [ ] `/health` 对外可用

### MVP / 延期

| MVP | 延期 |
|---|---|
| 可演示闭环种子 | 大规模知识导入、压测数据、多租户数据 |

---

## 10. Phase 8 — Agent 对接就绪（Backend 侧）

### 目标

在不实现 Agent 业务代码的前提下，保证 **同一套** `/api/v1/*` 可被未来 Agent Business Client 调用：鉴权、错误码、无后门。

### 涉及模块

- 既有 Middleware / Service 授权复查
- （可选）内部健康与超时配置文档化
- **不**新增 Agent 专用路由

### 新增文件

- 通常无强制新文件；可增加 `docs` 中「Agent→Go 调用约定」一小节（若 SECURITY 已覆盖则不重复造文档）

### 数据库变化

- 无

### API 变化

- **禁止**新增「internal bypass」API
- 确认：Authorization Bearer 用户 JWT；Go **再次**独立鉴权（SECURITY 原则）

### 验收标准

- [ ] 用伪造/过期/他角 Token 调 Ticket/Permission → 拒绝
- [ ] 用合法 Employee Token 尝试 approve → `40301`
- [ ] 无直连 DB 的 Agent 配置进入本仓库 Backend 职责说明
- [ ] 分层抽检：关键写路径仍是 Handler→Service→Repository

### MVP / 延期

| MVP | 延期 |
|---|---|
| 二次鉴权与无后门 | Browser→Go→Agent 代理改造、mTLS、独立 Service Account、Tool 级 ACL 引擎（P1） |

---

## 11. MVP 实现 vs 明确延期（总表）

### 11.1 Go Backend MVP 必须实现

| 域 | 内容 |
|---|---|
| 工程 | Go 1.22 + Gin + GORM + PostgreSQL + Compose |
| 横切 | 统一响应、错误码、JWT Middleware、Request-ID |
| Auth | `POST /auth/login`、`GET /users/me` |
| Ticket | 列表/创建/详情/PATCH + Service 状态机 + 字段权限 |
| Permission | 创建/列表/详情/approve/reject + 单级审批事务 |
| Data | Migration + Model 映射（含预留表结构）；Demo Seed |
| Audit | 关键路径 Append-Only |
| 边界 | Agent 不直连库；无用户管理 API；无 Onboarding HTTP |

### 11.2 明确延期（本规划不排期实现）

| 类别 | 延期项 |
|---|---|
| API | 用户 CRUD、Onboarding HTTP、评论独立公开 API、审计查询 API、PUT/DELETE |
| 基础设施 | Redis、Kafka/RabbitMQ、K8s、微服务拆分、复杂 CI/CD |
| 业务深度 | 多级审批、完整 ITIL/CMDB/SLA、真实 GitLab/LDAP 开通 |
| Agent 侧（非本规划交付） | LangGraph/RAG/Tool 实现本身；Evaluation 平台；Memory 独立向量库 |
| 架构变体 | 强制改为 Browser→Go→Agent 统一代理（除非先改契约） |
| 安全增强（P1+） | Prompt Injection 体系化测试、完整 Tool Permission 矩阵、Failure Recovery 框架 |

---

## 12. 跨阶段工程约束（检查清单）

每完成一个 Phase，用下表自检；任一项 ❌ 不得进入下一业务 Phase。

| # | 约束 | 说明 |
|---|---|---|
| C1 | Handler 无业务裁决 | 无状态机、无 RBAC 决策、无多表事务编排 |
| C2 | Service 为唯一业务核心 | 状态机、Ownership、字段权限、审批规则在此 |
| C3 | Repository 只访问数据 | 无「能不能做」；**禁止** `Approve`/`Reject`/`AssignTicket` 等业务语义方法名；业务动作由 Service 编排 |
| C4 | Agent 不直连 DB | 无连接串给 Agent 写业务表 |
| C5 | 不扩 MVP API | 新增端点必须先改 `API.md` |
| C6 | 不增表 / 不自改库 | 新增表或字段必须先改 `DATABASE.md`；**禁止**实现中途擅自补字段 |
| C7 | 身份从 Token 来 | 拒绝信任 body 的 user_id/role |
| C8 | 技术栈冻结 | 不得换成其他 Web/ORM/DB「顺便一试」 |
| C9 | 单 Phase 交付 | **禁止**一次实现多个 Phase；未确认不得扩范围 |

---

## 13. 建议实施顺序（一句话）

```text
Phase0 决议 → Phase1 底座 → Phase2 Migration
→ Phase3 Auth → Phase4 Ticket 状态机 → Phase5 Permission/Approval
→ Phase6 Audit → Phase7 Seed 演示 → Phase8 Agent 对接就绪
```

**下一步进入编码时的第一刀：** 完成 Phase 0 文档回写（若尚未回写）后，**仅**从 Phase 1 开始；Phase 1 验收通过后再开 Phase 2，**禁止**一次打包 Phase 1+2+3。

---

## 14. 验收总锚点（Backend V0 Done）

当且仅当以下全部成立，视为 Go Backend V0 可交接前端 / Agent：

1. Compose 下 Backend + PostgreSQL 稳定运行；`GET /health` 正常  
2. MVP 公开端点与 `API.md` §10 一致（Auth + Ticket + Permission + Health）  
3. Ticket 状态机与 Permission 终态冲突行为符合契约  
4. 员工越权、非法状态、伪造身份均被 Service 拒绝  
5. 关键写路径有 Audit；分层抽检无 Handler→GORM  
6. 种子数据可走完演示故事；延期项均未偷偷实现  

---

## 15. Cursor Implementation Protocol

实现任何 Phase 前，**必须先输出**（未经用户确认不得动手改代码/库表）：

1. **当前 Phase 目标理解**（用自己的话复述本阶段交付边界）  
2. **将修改文件列表**  
3. **不会修改的范围**（明确列出本阶段禁止触碰的后续能力）  
4. **验收方式**（对齐本 Phase 验收标准）

**未经确认，不得：**

- 修改技术栈  
- 修改数据库设计（含 Migration / 字段补丁）  
- 增加 API（含「顺手加一个内部接口」）  
- 引入基础设施（Redis / MQ / 新中间件栈等）

完成后**必须输出**：

1. **修改文件列表**（实际变更）  
2. **运行命令**（build / migrate / 手测命令）  
3. **验收结果**（对照本 Phase 勾选）  
4. **遗留问题**（缺口、需改 `DATABASE.md`/`API.md` 的建议）

**硬性禁止：**

- **禁止一次实现多个 Phase**
- 禁止因「表已建」提前写 Knowledge / Onboarding / Resource / Agent Tool
- 禁止缺字段时自改库；必须先提交文档变更建议并等待确认

---

*本文档只规划实施顺序与边界，不包含业务代码。实现阶段以本规划的 Phase 验收标准为完成定义；执行纪律以 §15 为准。*
