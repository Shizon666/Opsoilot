# Phase 10 最小 RAG 准备（设计）

> **V1 RAG 以 Phase A 契约 §6 为准**（本地 embedding）。本文是 Phase 10 关键词方案的历史设计。  
>
> 状态：准备就绪（知识第一批正文已收敛；**本文件是设计，不是已上线实现说明**）  
> 目标：`knowledge → RAG → Agent → answer/tool` 最小闭环  
> 非目标：Multi-Agent、rerank、graph router、知识后台、复杂评测、扩展企业文库

---

## 1. 第一批知识（8 篇，`phase10_batch: true`）

| doc_id | 路径 |
|--------|------|
| XXY-IT-CAT-001 | `knowledge/服务目录/IT服务目录与入口指引.md` |
| XXY-IT-POL-TKT-001 | `knowledge/制度规范/IT服务请求工单规范.md` |
| XXY-IT-POL-ACL-001 | `knowledge/制度规范/信息系统访问与权限管理规范.md` |
| XXY-IT-ACC-GL-001 | `knowledge/权限管理/GitLab权限申请指南.md` |
| XXY-IT-HOW-VPN-001 | `knowledge/VPN与远程办公/VPN与远程办公接入指南.md` |
| XXY-IT-HOW-EQP-001 | `knowledge/办公与直播设备/办公与直播设备报修指引.md` |
| XXY-IT-HOW-SW-001 | `knowledge/软件安装/标准软件安装与例外申请指南.md` |
| XXY-IT-HOW-ACC-001 | `knowledge/账号登录/账号与登录处理指南.md` |

入库过滤：

- `status: active`
- `rag.employee: true`
- `phase10_batch: true`（第一期可先只扫这 8 篇）
- 跳过 `README.md`、`元数据/`、`visibility: INTERNAL`

每篇结构统一：使用场景 → 判断流程 → 边界条件 → 示例问题。

---

## 2. `search_knowledge` Tool 设计（新增，不改现有五 Tool）

### 2.1 契约

| 项 | 约定 |
|----|------|
| 名称 | `search_knowledge` |
| 入参 | `query: string`（用户问题或改写后的检索句）；可选 `top_k: int`（默认 3，最大 5） |
| 出参 | JSON：`{ "ok": true, "hits": [ { "doc_id", "title", "excerpt", "score?" } ] }` |
| 失败 | `{ "ok": false, "error": "..." }`（与现有 Tool 风格一致） |
| 鉴权 | 仅 Employee 会话；只检索 `rag.employee=true` 文档 |

**不做：** rerank、多路召回融合、写操作、跨用户知识、返回整篇原文（只返回片段）。

### 2.2 最小实现选项（实现阶段二选一）

| 选项 | 说明 | 适用 |
|------|------|------|
| A. 本地切片 + 向量（BGE-M3 + Milvus） | 与 ARCHITECTURE 一致 | 正式 Phase 10 |
| B. 本地 MD 扫描 + 关键词/嵌入简易检索 | 无 Milvus 也可冒烟 | 开发过渡 |

准备阶段不绑定实现；Agent 侧只依赖上述 JSON 契约。

### 2.3 Agent 使用约定

```text
制度/入口/自助类问题
  → 先 search_knowledge（必要时）
  → 仅依据 hits.excerpt 做 answer，或决定调业务 Tool
  → 禁止用知识片段编造「已开通/已审批」

写操作
  → create_ticket / create_permission（五 Tool 不变）
  → 缺参先追问

查询自身状态
  → get_current_user / get_my_tickets / get_my_permissions
  → 不靠 RAG 编列表

human
  → 口头升级；不调用 approve；可建 ticket 但须说明转人工
```

现有五 Tool **保持**：`get_current_user`、`get_my_tickets`、`create_ticket`、`get_my_permissions`、`create_permission`。

---

## 3. 最小闭环方案

```text
用户消息
    │
    ▼
Agent（单 ReAct）
    │
    ├─ 需要制度/自助依据？ ──► search_knowledge(query, top_k)
    │                              │
    │                              ▼
    │                         向量/简易检索（仅 phase10_batch 8 篇）
    │                              │
    │                              ▼
    │                         top-k excerpts → 模型
    │
    ├─ answer：基于片段答复（可引用 doc_id）
    ├─ ticket：create_ticket
    ├─ permission：create_permission
    ├─ query：get_* 三 Tool
    └─ human：说明转 IT Support，禁止自动审批话术
```

**闭环验收（手测，非评测平台）：**

| 问法 | 期望 |
|------|------|
| 权限和工单有啥区别？ | search_knowledge → answer，不调写 Tool |
| 回家 VPN 连不上 | 检索 VPN 篇 → create_ticket 或先 answer 自查 |
| 申请 OpsPilot 仓库 Developer | 检索 GitLab/权限篇 → create_permission |
| 开播推流黑屏 | 设备/目录篇 → ticket + human 话术 |
| 我的工单有哪些 | get_my_tickets，不以 RAG 编造 |

---

## 4. 明确不做

- 新增大批知识目录/正文（数据安全、DB/DEV 指南等可后续批次）
- Multi-Agent / graph router / rerank
- 文档管理后台、Knowledge HTTP CRUD
- 复杂评测平台、SLA/治理字段扩写

---

## 5. 实现阶段待办（非本准备交付）

1. 切片入库（按 `##` 或固定窗）+ `doc_id` 元数据  
2. 实现 `search_knowledge` 并挂入 `PHASE8_TOOLS` 旁的工具列表（建议改名 `AGENT_TOOLS`）  
3. System Prompt 增加：制度问题先检索；仅用 excerpt  
4. Compose/配置：嵌入模型与向量库（若选方案 A）
