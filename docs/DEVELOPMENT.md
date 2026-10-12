# OpsPilot Development Workflow

> 文档定位：OpsPilot **开发规范**（个人可长期维护），不是架构设计文档。  
> 依据：`docs/API.md`、`docs/DATABASE.md`、`docs/ARCHITECTURE.md`、`docs/SECURITY.md`、`docs/GO_BACKEND_IMPLEMENTATION_PLAN.md`  
> 目标：固定功能进入开发的方式、文档与代码关系、Backend 分层、AI/Cursor 协作，以及 Phase/Slice 执行节奏，避免架构、配置、代码边界反复漂移。

---

## 1. 开发原则

1. **契约优先**  
   实现以已确认文档为准。HTTP 跟 `API.md`；表结构跟 `DATABASE.md`；分层与业务语义跟 `ARCHITECTURE.md`；鉴权边界跟 `SECURITY.md`。冲突时先改文档并确认，再写代码。

2. **小步实现**  
   一次只做一个 Phase / Slice。禁止「顺便」扩范围、改技术栈、加目录或补未排期能力。

3. **每个 Slice 必须可运行**  
   完成后应能本地跑通本 Slice 的验收路径（至少 build / 相关手测），而不是留下半成品骨架。

4. **不提前实现未确认需求**  
   文档未写、未决议的接口、表字段、中间件、目录结构，一律不进代码。缺口只提建议，等确认。

5. **AI 辅助开发必须经过确认**  
   Cursor / AI 在动手前输出计划，经确认后再改；改完对照验收标准输出结果。禁止静默扩需求或重构无关结构。

---

## 2. 功能开发流程

固定顺序（不可跳步）：

```text
需求确认
  ↓
设计 / 契约确认
  ↓
Implementation Plan（Phase / Slice）
  ↓
代码实现
  ↓
测试验证
  ↓
Commit
```

### 2.1 文档与代码的关系

| 变更类型 | 必须先更新 | 再写代码 |
|---|---|---|
| 涉及 API（路径 / Method / 请求响应 / 错误语义） | `docs/API.md` | 是 |
| 涉及数据库（表 / 字段 / 状态集合 / 事务约定） | `docs/DATABASE.md` | 是 |
| 涉及架构（分层职责 / 调用边界 / 状态机语义） | `docs/ARCHITECTURE.md` | 是 |
| 涉及鉴权或安全边界 | `docs/SECURITY.md`（按需） | 是 |
| 纯实现细节且契约已覆盖 | 可不改设计文档 | 直接按 Plan 实现 |

说明：

- 文档是契约真源；代码是契约落地。
- **禁止**实现中途擅自改字段形状、加端点、加表。
- Go Backend 的阶段顺序与边界以 `docs/GO_BACKEND_IMPLEMENTATION_PLAN.md` 为准；本文件规定「怎么做」，不重复「做什么」。

---

## 3. Backend 分层规则

固定分层（与架构 / 实施规划一致）：

```text
Handler → Service → Repository → Model / DB
```

### Handler

负责：

- HTTP 输入输出
- 参数绑定与基础格式校验
- 调用 Service
- 写统一 Response

禁止：

- SQL / GORM
- 直接调用 Repository（业务路径）
- 业务判断（RBAC 裁决、状态机、多表事务编排）

### Service

负责：

- 业务规则
- 权限（RBAC / Ownership / 字段权限）
- 状态机
- 事务编排
- 审计触发（若本阶段要求）

业务动作（审批、指派、解决、拒绝等）**只能**出现在 Service。

### Repository

负责：

- 数据访问（CRUD / 查询 / 字段级更新）

禁止：

- 权限判断
- 状态迁移判断
- 业务语义方法名（如 `Approve` / `Reject` / `AssignTicket`）；此类动作由 Service 编排，Repository 只做读写与查询条件拼装

### Model

只负责：

- 数据映射
- 字段定义 / 枚举常量

禁止：

- 状态机逻辑
- 授权逻辑
- HTTP / Service 编排

### Agent 边界（开发时不可违反）

- Agent **禁止**直连 PostgreSQL
- 业务读写一律经 Go Business API（`/api/v1/*`）

---

## 4. AI / Cursor 协作规则

### 4.1 每次修改前必须输出

未经确认，不得改代码 / 库表 / 契约文件。动手前必须写清：

1. **当前 Phase / Slice**
2. **修改文件列表**
3. **修改原因**
4. **不修改范围**（本阶段禁止触碰的能力与文件）
5. **验收标准**（对齐本 Phase / Slice 的 Acceptance Criteria）

### 4.2 禁止

- 未确认新增技术栈
- 未确认新增目录
- 扩大需求范围（「顺手」加接口、表、中间件）
- 修改无关文件
- 重构已有结构（除非当前 Slice 明确要求）
- 一次实现多个 Phase
- 缺字段时自改库或自改契约形状

### 4.3 修改后必须输出

1. **修改文件**（实际变更）
2. **测试结果**（命令 + 结论；对照验收勾选）
3. **当前状态**（本 Slice 是否完成；遗留 / 需确认项）

---

## 5. Phase / Slice 管理

### 5.1 每个 Phase 必须包含

| 项 | 含义 |
|---|---|
| **Goal** | 本阶段要达成什么 |
| **Scope** | 做什么（边界内清单） |
| **Files** | 预期涉及的文件 / 目录 |
| **Not Included** | 明确不做、禁止提前做的内容 |
| **Acceptance Criteria** | 可勾选的完成定义 |

Slice 是 Phase 内的更小可运行增量；规则同上。未写清上述五项，不得开始实现。

### 5.2 推进规则

- **未完成当前 Slice 前，不进入下一阶段。**
- 验收未通过不得宣称 Phase Done。
- Backend 阶段顺序遵循 `docs/GO_BACKEND_IMPLEMENTATION_PLAN.md`；不得跳 Phase 抢做后续业务。

### 5.3 建议自检（每 Slice 结束）

- Handler 无业务裁决 / 无 GORM
- Service 为唯一业务核心
- Repository 只访问数据
- 未擅自扩 API / 表 / 技术栈
- 本 Slice 可运行且验收项可勾选

---

## 6. Git 规范

保持简单，适合单人维护；不引入复杂分支模型或企业流程。

### 分支

| 分支 | 含义 |
|---|---|
| `main` | 稳定版本 |

日常在可运行增量上提交；不为本仓库强制 feature 分支、GitFlow 或 release 流程。

### Commit 格式

```text
feat:  新增功能
fix:   修复问题
chore: 工程配置
```

示例：

```text
feat: add ticket list and create handlers
fix: reject illegal ticket status transition
chore: add database config loader
```

说明：

- Commit 对应已验收的小步结果，避免半成品大提交。
- 不在本规范中引入 Jira、CI/CD 流水线要求或强制 PR 模板。

---

## 7. 本规范不覆盖的内容

以下内容**故意不写**，以免流程膨胀：

- Jira / 工单系统 / 多人评审流程
- 复杂 CI/CD、分支策略、发布火车
- Kubernetes、微服务治理、服务网格等未来规划
- 未确认的技术选型与目录扩张

需要架构、API、库表细节时，查阅对应设计文档；需要 Backend 落地顺序时，查阅实施规划。本文件只固定「一个人 + AI 如何持续、可控地开发」。
```
