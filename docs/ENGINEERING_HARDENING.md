# V1 完成度 · 剩余风险 · Engineering Hardening

> 版本：**v1.1**（2026-10-04）  
> 前置：Phase A–E **产品化已完成**（契约 → Backend → Agent/RAG → Frontend → Demo 文档）。  
> 本文件是 **下一阶段真源**。不新增业务对象、Tool、Multi-Agent、Planner、Memory 系统、知识后台。  
> 路线总表：[`ROADMAP.md`](../ROADMAP.md)。Demo：[`DEMO.md`](DEMO.md) / [`DEMO_CHECKLIST.md`](DEMO_CHECKLIST.md)。

---

## 1. 当前 V1 完成度矩阵

判定口径：**现网代码 + 可演示主链**，不是 PRD 历史清单。

| 域 | 能力 | 状态 | 说明 |
|---|---|---|---|
| A 契约 | 北极星 / HTTP 差集 / Tool 白名单形状 | **完成** | `PHASE_A_V1_CONTRACT.md`；检索存储以 C-3 现网为准（见 §勘误） |
| B Backend | services 健康、tickets.analysis、`q`/`service_id`、Audit GET、seed `000015` | **完成** | Permission API **Legacy 保留** |
| C Agent | 8 Tool 白名单；Permission 不进 Graph | **完成** | `AGENT_TOOLS`；写工具仅 `create_ticket` / `update_ticket` |
| C RAG | `knowledge/ops` + ingest + `search_knowledge` | **完成** | 运行时 **SiliconFlow bge-m3 + Milvus `knowledge_docs`** |
| C 行为 | 分析优先 / HITL 升级 | **完成** | C-4 / C-4.1 Prompt；C-4.3 `cases_c42.yaml` |
| D Frontend | Chat 默认入口、SSE、HITL、服务状态只读页 | **完成** | 刷新产生新 `thread_id`（已知） |
| E Demo | Checkout 双角色剧本 | **完成** | 文档已固化；可重复性依赖 Milvus/ingest 环境 |
| 短期 Memory | Checkpointer + `thread_id` + 归属 | **完成** | `PostgresSaver` / `opspilot_agent` |
| 长期 Memory | `users.department/position/employee_level` + `/users/me` | **最小完成** | 无画像表；不扩展 |
| HITL / 安全底座 | JWT 透传、Go 二次鉴权、Ownership、写确认 | **完成** | HITL ≠ Approval |
| Evaluation | V1 P0 runner | **部分** | `--v1` 有套件；Legacy `cases.yaml` 仍是 IT/Permission 口径 |
| 文档一致 | ROADMAP / AI_CONTEXT / Phase A §6 | **部分** | Hardening 收口对象 |

**V1 产品闭环（已通）：**

```text
登录 → Chat 报 Checkout 502
  → get_service_status + search_knowledge + search_tickets
  → 分析回复（默认可不建单）
  → 明确升级 → HITL → create_ticket
  → 我的工单可见 → Support 关单 → Ownership 拒绝跨用户
```

---

## 2. V1 剩余风险列表

| ID | 风险 | 等级 | 为何还在 | Hardening 切片 |
|---|---|---|---|---|
| R1 | Demo 知识步依赖独立 Milvus + ingest + `SILICONFLOW_API_KEY` | **高** | 主 compose 无 Milvus；未 ingest 会「暂无命中」 | H1 |
| R2 | 双检索路径（`local_store` npy vs Milvus retriever） | **中** | 遗留适配器仍在仓内，易接错 | H1 / H5 |
| R3 | Phase A §6「禁止 Milvus / bge-small」与现网不一致 | **中** | 实现已走 C-3；旧句仍会误导下一刀 | H0 |
| R4 | Chat 刷新丢失 `thread_id` / HITL pending | **中** | `useState(newThreadId)`；无会话库（有意） | H2 |
| R5 | 过期 `AI_CONTEXT` 把 V1 写成「未改代码」 | **高（文档）** | 会诱导重做 B/C 或再接 Permission Tool | H0 |
| R6 | Legacy Permission HTTP 仍可用 | **低** | 冻结不删除；Agent 主链已卸 | 不改代码；评测禁调 |
| R7 | `EVALUATION.md` 与 Legacy cases 仍是 VPN/GitLab | **中** | 易把旧 PASS 当 V1 金标 | H4 |
| R8 | Prompt 注入 / RAG 投毒 / 越权话术覆盖不足 | **中** | C-4.2 有设计；P0 套件未铺满安全面 | H3 / H4 |
| R9 | 旧 seed（如 `000012` VPN 单）混在列表 | **低** | Demo 已声明噪音 | H1 文档即可 |
| R10 | 知识 `visibility` 未在检索过滤 | **低** | V1 不做知识权限平台 | **不做** |
| R11 | Support UI 无 analysis 表单 / 无 Audit 页 | **低** | Demo 用手测 API | **不做**（非本阶段） |
| R12 | `CHECKPOINT_BACKEND=memory` 误配导致重启丢会话 | **低** | Compose 默认 postgres | H1 环境核对 |

**明确不是风险、不要当缺口修：** Multi-Agent、Planner、知识 CMS、Memory 向量库、用户画像、Prometheus。

---

## 3. Engineering Hardening 计划

**完成定义：** 同一台机器按清单能重复跑通 Demo；文档与代码检索后端一致；thread 刷新不断会话（可选落地）；安全边界有可重复检查；V1 eval 与 Legacy 分表。

**非目标：** 新 Tool、新表、新业务 API、知识后台、评测平台、改 Graph 拓扑。

### H0 — 文档状态同步

| 做 | 不做 |
|---|---|
| ROADMAP v1.1；本文件；`AI_CONTEXT.md` §1/§2/§6 | 重写 PRD / ARCHITECTURE 全书 |
| Phase A **运行时勘误**（Tool/hit 不变；存储以 C-3 为准） | 推翻 Phase A 产品北极星 |
| DEMO 技术链路与「Milvus ingest」前提对齐 | 新 Demo 剧本 |

### H1 — Demo 可重复运行

| 做 | 不做 |
|---|---|
| 核对 `DEMO_CHECKLIST`：主 compose + `docker-compose.milvus.yml` + index/ingest 顺序 | 把 Milvus 塞进 Go |
| 知识失败记 **环境**，禁止改 Tool 凑命中 | 自动 mock LLM |
| 主路径仍用 `000015` + Checkout 502 | 清掉 Legacy seed 表数据（除非另开） |

建议手测顺序：起 postgres/backend/agent → 起 milvus → ingest/index → Vite → `DEMO_CHECKLIST` A3 知识步。

### H2 — thread_id 体验

| 做 | 不做 |
|---|---|
| Chat：**同一浏览器标签**用 `sessionStorage` 复用 `thread_id`（刷新不断 HITL） | 多会话历史库、跨用户共享 thread |
| 退出登录清除绑定 | Checkpointer 换 Redis |

Agent 侧归属校验保持：`thread_id` 绑定 `user_id`，禁止串会话。

### H3 — Agent 安全边界（加固，不扩面）

现网已有（保持）：JWT 双端校验、Tool 不收伪造 `user_id`、Go Ownership、写路径 HITL、白名单无 Permission、跨用户 GET 拒绝。

本切片只补 **可重复验证**，不补新机制：

- 张明 token GET 李华工单 → `40301`/`40401`（Demo 已有）
- 评测 `forbidden_tools`：`create_permission` / `get_my_permissions`
- 注入/跳过 HITL 话术：不执行写库；`expect_interrupt` 仍要确认
- 不把 RAG snippet 当授权成功

### H4 — Evaluation 补充

| 做 | 不做 |
|---|---|
| 以 `cases_c42.yaml` + `python -m app.evaluation.runner --v1` 为 V1 金标 | 50～100 Case 平台（Phase 18） |
| `EVALUATION.md` 标明 Legacy 表不可作 V1 PASS | LLM-as-Judge |
| 可选：1～3 条检索烟测（Checkout 命中 / 天气空）已有 `retriever` eval | 新评测框架 |

### H5 — 检索路径克制

| 做 | 不做 |
|---|---|
| 运行时只走 `app.rag.retriever` → Milvus | 把 `local_store.retrieve` 接回 Tool |
| 代码注释/模块头标明遗留 | 删除全部 local_store（可留测试） |

---

## 4. 建议实施顺序

```text
H0 文档（本批）
  → H1 Demo 环境手册可执行（无新功能）
  → H4 EVALUATION 口径（文档 + 现有 runner）
  → H2 sessionStorage thread_id（唯一允许的小 UX）
  → H3 安全用例补进 V1 yaml（不改鉴权模型）
  → H5 不接双路径（默认零 diff，除非发现误用）
```

一次只做一刀。做 H2 前须用户确认「允许改 Chat 一处 UX」。

---

## 5. 验收（本阶段）

| # | 看见什么 |
|---|---|
| A | ROADMAP A–E 为完成；下一阶段写 Hardening 而非 Phase F 功能 |
| B | `AI_CONTEXT` 不再写「业务代码尚未按 V1 改」 |
| C | 按 DEMO_CHECKLIST 能复跑；知识步失败归因环境 |
| D | （H2 落地后）刷新 Chat 仍同一 `thread_id`，HITL 框还在 |
| E | `runner --v1` 与 Legacy cases 分表；不把 Permission 当 V1 主链 |
