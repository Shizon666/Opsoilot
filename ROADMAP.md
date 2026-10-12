# OpsPilot 项目总路线

> **V1.1（2026-10-04）**：故障工单助手产品化 **A–E 已完成**。  
> 当前下一阶段：**Engineering Hardening**（不新增功能）。真源：[`docs/ENGINEERING_HARDENING.md`](docs/ENGINEERING_HARDENING.md)。  
> 运行时 RAG：`search_knowledge` → SiliconFlow `BAAI/bge-m3` → Milvus `knowledge_docs`（C-3）。Tool 名与 hit 字段仍以 [`docs/phases/PHASE_A_V1_CONTRACT.md`](docs/phases/PHASE_A_V1_CONTRACT.md) 为准。  
> Phase A §6「本地 bge-small、禁止 Milvus」已被 C-3 运行时替代；下文 Phase 15 指 **知识平台化 / 更大规模异构**，不是「从零再接一次 Milvus」。  
> 已完成的 V0 业务底座与 Phase 8–14 Agent 能力**保留**，不推倒重来。

## 一、项目定位

OpsPilot V1 = **AI 运维故障工单助手**

核心链路：

```text
员工提出故障
  → Agent 理解（缺参追问）
  → 查询服务状态（services 表模拟健康）
  → RAG 检索运维 Runbook（C-3：bge-m3 + Milvus；离线 ingest）
  → SQL 检索历史工单
  → 生成分析与建议
  → HITL 确认后 create / update 工单
  → Go 写 audit_logs
```

涉及写操作时：读自动执行；`create_ticket` / `update_ticket` 必须 HITL。

Permission / AccessRequest / Approval = **Legacy 冻结**。

外围能力（V1 克制）：
- Evaluation：V1 P0 runner（`cases_c42.yaml`）；**不建**评测平台
- Security：Go 二次鉴权 + Ownership；HITL ≠ Approval
- SSE / UX：过程可见；Chat 作为第一入口（Phase D 已完成）

---

## 二、已完成阶段

## V0 — Deterministic Business System

已经完成。

核心：
- Go Business API
- PostgreSQL
- 用户 / 角色
- Ticket
- Access Request
- Approval
- Audit
- JWT
- 基础 RBAC

---

## V1 — Single Agent

已经完成基础能力。

包括：
- LangGraph
- Tool Calling
- Business API Tool
- Knowledge Tool
- Memory / Checkpointer
- thread_id
- Agent 与 Business DB 解耦
- Go Business API 作为业务数据权威入口

---

## Phase 14 — HITL

**状态：PASS**

已经完成：

- READ / WRITE Tool 区分
- WRITE Tool 人工确认
- interrupt / Command(resume)
- confirmation SSE
- pending 状态
- thread ownership
- duplicate resume 防重复执行
- HITL smoke test
- DB 结果验证

已知技术债保持记录，但暂不扩展范围。

---

## 三、V1 产品化（已完成）与下一阶段

## V1 产品化 A–E

| Phase | 内容 | 状态 |
|---|---|---|
| **A** | 契约 / API 差集 / Seed / 文档冻结 | **完成** |
| **B** | services 健康、tickets.analysis 与 SQL 检索、Audit GET、seed | **完成** |
| **C** | Tool 白名单、`knowledge/ops`、Milvus RAG、`search_knowledge` | **完成** |
| **D** | Chat 第一入口、服务状态页 | **完成** |
| **E** | 双角色 Demo 固化 | **完成** |

完成度矩阵、剩余风险、Hardening 切片：**[`docs/ENGINEERING_HARDENING.md`](docs/ENGINEERING_HARDENING.md)**。

运行时 RAG：**不是**关键词检索；**不是** Phase A 原文的本地 bge-small 主路径。现网为 SiliconFlow `BAAI/bge-m3` + 独立 Milvus `knowledge_docs`。本地 `local_store` 为遗留适配器，禁止接回 Tool。

## 下一阶段 — Engineering Hardening（当前）

**不新增功能。** 只做：文档与代码对齐、Demo 可重复、thread_id 刷新体验（可选）、安全边界可重复验证、V1 Evaluation 与 Legacy 分表。

禁止：新业务对象、新 Tool、Multi-Agent、Planner、Memory 系统、知识后台。

一次只做一个 Hardening 切片（H0→H1→H4→H2→H3→H5），实现前须用户确认。

---

## Phase 15 — Enterprise Knowledge Base（V2+ 延期）

> 原「下一阶段」全文保留作远期设计，**V1 不实施知识平台**。  
> V1 **已经**用独立 Milvus + bge-m3 服务 `search_knowledge`（C-3）。Phase 15 剩余含义是：异构 20～30 源、OCR/CMS、知识后台、可见性平台——**仍禁止作为 Hardening 范围**。

目标（远期）：

让 OpsPilot 从目前的简单 Markdown keyword retrieval，升级为一个**小规模但真实企业场景的知识库系统**。

核心问题不是“多放几个文档”，而是：

> 异构企业知识源如何变成可靠、可追踪、可检索的知识单元，并被 Agent 正确使用？

知识源保持小规模，但要有真实异构性。

目标规模：

**约 20～30 个真实知识源。**

允许的主要格式：

- PDF
- DOCX
- Markdown
- CSV / XLSX
- 图片

典型内容：

- IT 政策
- 服务使用规范
- 操作流程
- FAQ
- 服务目录
- 权限矩阵
- 配置截图 / 操作截图

核心链路：

异构文档
→ Parse
→ Unified Knowledge Representation
→ Structure-aware Chunk
→ BGE-M3 Embedding
→ Milvus
→ Retrieval
→ Agent

必须考虑：

- source tracking
- document_id
- file_name
- file_type
- title
- section
- source_location
- version
- updated_at
- visibility

以及：

- 文档结构保留
- 文档版本 / 更新
- 权限可见性
- 检索不到时正确拒答
- 来源追踪
- 基础 Retrieval Evaluation

暂时**不默认加入 reranker**。

只有 Evaluation 证明向量检索存在明显的排序问题时，再考虑 reranker。

不要建设完整的企业文档管理平台。

Phase 15 完成标准：

> Agent 能够基于企业知识可靠回答知识类问题，并能够追踪答案来源。

---

## Phase 16 — User Context

这不是做一个“用户画像页面”。

目标是让 Agent 真正理解：

> “这个用户是谁？他属于什么组织？他拥有什么资源？他当前处于什么业务状态？”

用户上下文可以包含：

- department
- role
- team / manager
- services / resources
- current permissions
- recent tickets
- recent access requests
- 其他稳定业务事实

但不要把所有动态业务数据复制到 profile 表。

动态信息应该通过 Go Business API 查询。

三类状态明确分离：

### Short-term Memory

LangGraph Checkpointer + thread_id

负责：

- 当前对话
- 多轮上下文
- 当前任务状态

### Enterprise Knowledge

Milvus / RAG

负责：

- 企业政策
- 操作规范
- FAQ
- 知识文档

### User Context

Go Business API / PostgreSQL

负责：

- 用户身份
- 组织
- 角色
- 资源
- 权限
- 工单
- Access Request
- 其他业务状态

目标：

Agent 能够把：

**“这个用户是谁”**

和：

**“企业规定是什么”**

以及：

**“这个用户当前业务状态是什么”**

结合起来进行判断。

---

## Phase 17 — Agent Reliability

单独处理 Reliability，不和 Security 混为一谈。

目标：

> 正常失败发生时，Agent 能够正确失败。

需要覆盖：

- 参数错误
- Tool business error
- HTTP 4xx
- HTTP 5xx
- timeout
- connection failure
- MCP failure
- malformed tool result
- retry
- retry limit
- fallback
- final failure response
- Agent loop failure

基本原则：

READ failure：

可以进行有限重试。

WRITE failure：

不能简单重试。

因为：

> timeout 不代表 WRITE 一定没有成功。

因此需要考虑：

- idempotency
- request_id
- duplicate write prevention

Agent 必须：

- 不无限循环
- 不无限重试
- 不重复写入
- 失败后给出明确用户反馈
- 根据失败类型选择 retry / ask / fallback / stop

当前：

`MAX_TOOL_ROUNDS=4`

作为基础保护继续保留。

完成标准：

> Tool 正常失败时，Agent 能按照明确策略 retry / ask / fallback / stop，并且不会产生重复写入或无限循环。

---

## Phase 18 — Evaluation

目标不是单纯增加 Unit Test。

而是建立：

> Agent Regression Evaluation System

规模：

**约 50～100 个高质量业务 Case。**

不追求几千条。

覆盖：

### RAG

- correct retrieval
- no result
- semantic match
- distractor
- wrong rank
- numbers / rules
- groundedness
- abstention

### Agent

- routing
- multi-intent
- missing parameters
- clarification

### Tool

- correct tool
- correct arguments
- tool failure
- duplicate calls

### Memory / Context

- multi-turn
- reference
- thread isolation
- user context

### HITL

- approve
- reject
- no bypass
- duplicate resume

### Security

- prompt injection
- RAG poisoning
- authorization
- data leakage

### E2E

- correctness
- latency
- failure handling

目标链路：

Case
→ Agent
→ Trace / Result
→ Expected
→ Pass / Fail
→ Regression Report

完成标准：

> 修改 Prompt / RAG / Tool / Context 后，可以知道 Agent 是否发生行为回归。

---

## Phase 19 — Security

现有基础安全能力继续保留：

- JWT
- identity propagation
- RBAC
- thread ownership
- tool allowlist
- Pydantic validation
- HITL
- Go authorization

在此基础上增加 LLM / Agent 特有安全问题：

### Prompt Injection

用户输入不能突破：

- Tool 权限
- Business API 权限
- HITL
- 数据访问边界

### RAG Poisoning

检索到的文档内容必须被视为：

> data

而不是：

> system instructions

### Tool Abuse

Agent 不能因为模型判断就绕过业务权限。

### Data Leakage

必须防止：

- User A 获取 User B 数据
- User A 获取 User B thread
- 越权读取私有知识
- 工具结果泄露敏感信息

### Fail Closed

身份、权限、HITL、Tool 状态不明确时：

**拒绝执行，而不是猜测执行。**

核心原则：

> Prompt 不是 Security Boundary。

真正的安全边界必须在：

- Tool
- Business API
- JWT
- Authorization
- HITL
- Data access layer

---

## Phase 20 — SSE / Agent UX

当前后端已经存在 SSE 基础能力，但前端还没有完整消费。

目标：

让 Agent 从：

“请求 → 等待 → 最终答案”

变成：

“可观察的 Agent 工作过程”。

可以逐步支持：

- message_start
- status
- tool_start
- tool_end
- confirmation
- message_delta
- error
- done

但绝不能把以下内容直接暴露给前端：

- system prompt
- internal prompt
- JWT
- sensitive tool arguments
- raw exception
- SQL
- 内部数据库细节

需要处理：

- disconnect
- reconnect
- error
- pending
- HITL confirmation
- final response

完成标准：

> 用户可以看到有意义的 Agent 工作状态、Tool 状态、HITL 确认和最终结果。

---

## 四、V2：Planner + Executor

**现在不做。**

只有当 Single Agent 在 Phase 15～20 成熟后，真实出现：

> 多个有依赖关系的步骤难以通过当前 Tool Loop 稳定控制

才进入 V2。

典型例子：

检查权限
→ 查询政策
→ 判断缺失权限
→ 创建权限申请
→ HITL
→ 提交
→ 查询申请状态

届时可以演进成：

Single Agent
→ Planner
→ Execution Plan
→ Executor
→ Tools / HITL
→ Final Answer

Planner / Executor 不要求成为两个独立 Agent。

可以继续保持 Single Agent 架构，只是在内部增加规划与执行控制。

---

## 五、Multi-Agent

**取消作为固定路线阶段。**

Multi-Agent 不是 OpsPilot 必须完成的目标。

只有未来出现真正的业务职责分裂，例如：

- 不同 Agent 有明显不同的工具边界
- 不同 Agent 有不同权限边界
- 不同 Agent 有不同业务上下文
- 不同 Agent 有不同推理职责

才重新评估。

如果 Single Agent + Planner / Executor 已经足够：

**就保持 Single Agent。**

---

## 六、项目总体原则

以后所有技术决策都遵守：

### 1. 业务优先，Agent 第二

先问：

> 业务为什么需要？

再问：

> Agent 如何解决？

而不是为了 Agent 而 Agent。

### 2. 数据做小，问题做真

不追求百万级数据。

但每一个数据和场景都应该是真实企业问题的缩小版。

### 3. 技术复杂度由业务复杂度推动

不为了简历主动增加：

- Multi-Agent
- Reranker
- Kafka
- Redis
- MQ
- 微服务
- 复杂 Planner

如果业务没有需要，就不加。

### 4. Prompt 不是安全边界

真正边界必须由：

- Authentication
- Authorization
- Tool
- Business API
- HITL
- Database access

承担。

### 5. Reliability ≠ Security

Reliability：

> 系统正常失败时，如何正确失败。

Security：

> 不可信输入如何不能突破系统边界。

两者分别建设。

### 6. 不允许 Cursor 自行扩展路线

后续每一个 Phase：

Cursor 只负责实现已经确定的设计。

如果实现过程中发现：

- 需求矛盾
- 架构问题
- 数据模型冲突
- 现有代码与 Phase 目标不一致

必须先报告，不得自行扩大范围。

---

## 七、最终产品目标

最终不是：

“堆了一堆 Agent 技术的 Demo”。

而是一个完整的：

**企业内部 IT Support Agent**

能够完成：

员工
→ 身份识别
→ 用户上下文
→ 企业知识检索
→ 当前业务状态查询
→ Agent 决策
→ Tool 调用
→ HITL
→ Go Business API
→ PostgreSQL
→ Audit
→ 最终回答

同时具备：

- Memory
- RAG
- Tool Calling
- HITL
- Reliability
- Evaluation
- Security
- SSE / UX

必要时再增加：

- Planner / Executor

而：

**Multi-Agent 永远是可选架构，不是毕业条件。**
