# Phase C-3 — 知识处理链路设计契约（raw → Milvus → search_knowledge）

> 状态：**设计冻结（2026-10-04）**（当时只改本文）。**实现后** `load` / `chunk` / `index` + Milvus 已落地。  
> **V1 现行 RAG**：SiliconFlow `BAAI/bge-m3` + Milvus `knowledge_docs`。`local_store` / `app.rag.ingest` = Legacy。  
> 北极星：AI 运维故障工单助手。Demo 入库命令见 [`docs/DEMO.md`](../DEMO.md) §1.3。  
> 冲突：hit JSON → Phase A；扫哪些文件 → C-2；embedding / Milvus collection → 本文（已实现）。

---

## 0. 本阶段做什么 / 不做什么

### 0.1 要解决的问题

C-2 解决了「库里有什么」。C-3 解决：

> 一篇企业运维 PDF / DOCX / Markdown / TXT，如何变成 Agent 能引用、可重建、与工单 SQL 隔离的检索片段？

目标链路（冻结）：

```text
raw document（仅 knowledge/ops/raw）
        ↓
     loader
        ↓
  统一 Document
        ↓
      chunk
        ↓
    embedding（SiliconFlow · BAAI/bge-m3 · 1024）
        ↓
  Milvus collection knowledge_docs
        ↓
  search_knowledge Tool（契约不变）
```

### 0.2 非目标（本文件与后续实现均禁止自行加入）

```text
本设计阶段：不写 parser / ingest 脚本 / SiliconFlow client / pymilvus
不扫描 knowledge/制度规范、权限管理、服务目录、VPN、常见问题 等 Phase 10 语料
不把 agent/knowledge/runbooks/ 作为 ingest 根（canonical 已在 knowledge/ops/raw）
不改 search_knowledge 入参/出参形状；不新增第二个知识 Tool
不建 PostgreSQL knowledge_* 表；不写 Go XML/MyBatis；不改 frontend 知识后台
不做 OCR、HTML 实现、Rerank、在线学习、把 LLM 改写当原文
不把 tickets / services 健康快照 / 用户画像写入向量库
```

### 0.3 前后端 / 库表现状（契约边界，禁止发明）

| 层 | 路径要点 | 与知识 Pipeline 的关系 |
|----|----------|------------------------|
| Frontend | `frontend/` Chat 调 Agent；**无**知识 CMS、无上传页 | C-3 不改 UI |
| Agent | `search_knowledge` → `app.rag.retriever`（Milvus）。`local_store.py` 为设计时/遗留基线 | **禁止**改 Tool JSON |
| Go Backend | `internal/` + `migrations/`：`users` / `roles` / `services` / `tickets` / `access_requests` / `approvals` / `audit_logs` | **无** knowledge 表；工单仍 SQL |
| Mapper XML | 本仓是 Go SQL migration，**没有** MyBatis XML 知识 SQL | 禁止为 RAG 补业务表 |
| 权威资产 | `knowledge/ops/raw/**` + `knowledge/ops/catalog.yaml` | **唯一** ingest 输入 |
| 禁止根 | `knowledge/制度规范`、`knowledge/权限管理`、`knowledge/服务目录`、以及同级旧 IT 目录 | 硬过滤 |

---

## 1. 扫描边界（硬约束）

### 1.1 只处理

```text
仓库根相对路径：knowledge/ops/raw/
机器清单：      knowledge/ops/catalog.yaml
人类清单：      knowledge/ops/README.md
```

ingest **必须以 catalog 为白名单**，再打开 `source_path` 指向的文件。  
禁止 `os.walk(knowledge/)`。禁止按扩展名全库 glob。

准入（全部满足才入库）：

| 条件 | 值 |
|------|----|
| `v1_ingest` | `true` |
| `status` | `active` |
| `canonical` | `true` |
| `source_path` | 必须以 `raw/` 开头，且解析后仍落在 `knowledge/ops/raw/` 内（防路径穿越） |
| `source_type` | `markdown` / `pdf` / `docx` / `txt` |
| 必填元数据 | C-2 §5.1：`doc_id` `title` `category` `source_type` `service` `department` `severity` `created_at` |

### 1.2 禁止扫描（显式名单）

```text
knowledge/制度规范/
knowledge/权限管理/
knowledge/服务目录/
knowledge/VPN与远程办公/
knowledge/账号登录/
knowledge/数据安全/
knowledge/常见问题/
knowledge/作业手册/
knowledge/软件安装/
knowledge/办公与直播设备/
knowledge/元数据/
agent/knowledge/runbooks/
```

这些目录文件可留仓，**零字节进入** `knowledge_docs`。

### 1.3 格式闸门

| source_type | V1 loader | 说明 |
|-------------|-----------|------|
| `markdown` | **实现** | front matter + 正文 |
| `pdf` | **实现** | 文本层抽取；无文本层拒绝；不做 OCR |
| `docx` | **实现** | 段落 + Heading 样式 |
| `txt` | **实现** | UTF-8 / 编码探测；sidecar 元数据 |
| `html` | **只预留枚举与接口形状** | catalog 不得出现 `html`；loader 遇到即 skip + 错误日志 |

---

## 2. 模块与命令落点（实现阶段，本文不写代码）

全部在 **Agent 工程**，工作目录 `agent/`：

```text
agent/app/rag/
├── ingest.py              # python -m app.rag.ingest 入口
├── catalog.py             # 只读 knowledge/ops/catalog.yaml
├── loaders/               # md / pdf / docx / txt；（html 空实现/显式 NotImplemented）
├── document.py            # 统一 Document Object
├── chunking.py
├── embedder.py            # SiliconFlow BAAI/bge-m3
├── milvus_store.py        # collection knowledge_docs
└── retriever.py           # 查询向量 + search → hit 映射

知识源（git）：knowledge/ops/raw + catalog.yaml
中间产物：   knowledge/ops/processed/   （可 gitignore）
运行时：     Milvus knowledge_docs；Agent 启动只读检索
```

Go / frontend / `migrations/` **零改动**。

---

## 3. 统一 Document Object

Parser 之后、chunk 之前的权威内存/落盘对象。一篇 canonical 源文件 ↔ 一个 Document。  
**禁止**把 PDF 二进制或 DOCX zip 丢进模型；**禁止**用 LLM「补全」抽空的页。

### 3.1 字段

| 字段 | 类型 | 必填 | 来源 | 说明 |
|------|------|------|------|------|
| `doc_id` | string | 是 | front matter / sidecar / catalog | 稳定 ID，upsert 键 |
| `title` | string | 是 | 同上 | 对应 hit.title |
| `category` | enum | 是 | 同上 | `RUNBOOK` / `SERVICE_MANUAL` / `INCIDENT_REPORT` / `OPERATION_PROCESS` / `SECURITY_GUIDELINE` |
| `service` | string | 是 | 同上 | `CHECKOUT_API` / `AUTH_SERVICE` / `ORDER_WORKER` / `PLATFORM` / `MULTI` |
| `department` | string | 是 | 同上 | 如 `运维部` |
| `severity` | enum | 是 | 同上 | `INFO` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `source_type` | enum | 是 | 同上 | `markdown` / `pdf` / `docx` / `txt`（`html` 预留） |
| `source_path` | string | 是 | catalog | 相对 `knowledge/ops/`，映射 hit.path |
| `visibility` | enum | 是 | 元数据 | `PUBLIC` / `INTERNAL`；不明则 Fail Closed 不入库 |
| `status` | enum | 是 | 元数据 | 仅 `active` 进索引 |
| `created_at` | string | 是 | 元数据 | ISO 日期 |
| `version` | string | 建议 | 元数据 | 语义化版本 |
| `content` | string | 是 | loader 清洗后全文 | Embedding 前再切块；不进 Tool 全文 |
| `elements` | list | 是 | loader | 有序块：heading / paragraph / list / page_break |
| `content_hash` | string | 是 | sha256(源文件字节 + sidecar) | 未变可跳过重嵌 |
| `parse_status` | enum | 是 | loader | `ok`；失败不写 processed、不写 Milvus |

catalog 与文件元数据冲突：以 **文件内 front matter / sidecar 为准**，但 `doc_id` 必须与 catalog 行一致，否则 skip。

落盘建议：`knowledge/ops/processed/documents/{doc_id}.json`（复查用，不是 Agent 运行时依赖）。

### 3.2 各格式如何变成统一结构

#### Markdown

1. 读 UTF-8。  
2. 解析 YAML front matter → 文档级元数据。  
3. 去掉 front matter 后的正文：ATX 标题（`#` / `##` / `###`）→ `heading`；连续非标题行 → `paragraph` 或 `list`。  
4. `#` 文档标题不单独成检索块（与 C-2 §7.1 一致）。  
5. `content` = 标题树展开后的纯文本（保留换行与步骤编号）。  
6. `source_location` 用标题路径，如 `排查步骤`。

#### PDF

1. 同路径 `{stem}.meta.yaml` 为元数据；正文来自 PDF 文本层。  
2. 按页抽取；页界写入 `page_break` + `source_location=p.{n}`。  
3. 能识别书签/字体标题则升为 `heading`；否则该页为 `paragraph`。  
4. 无文本层或清洗后全文 < 80 字：`parse_status=failed`，**拒绝入库**。  
5. 忽略嵌入图片；不做 OCR。

#### DOCX

1. sidecar `*.meta.yaml`。  
2. `python-docx`（实现阶段）：`Heading 1–3` → `heading`；Normal 段落 → `paragraph`；列表 → `list`。  
3. 对齐 Markdown 标题树；表格拍成 Markdown 管道表（V1 允许拍扁，不丢表头）。  
4. 页眉页脚去掉。

#### TXT

1. sidecar 必填（无 front matter）。  
2. 编码探测，失败则 utf-8 严格模式失败即 skip。  
3. 无标题：空行分段为 `paragraph`；`section` 默认 `全文`。  
4. 例：`ops-rb-escalate.txt`。

#### HTML（预留）

接口形状与 MD 相同（去导航后 heading + article），**V1 不实现、catalog 不收录**。

### 3.3 Cleaning（切块前）

- 去重复空白、页眉页脚样板、HTML 残渣。  
- **不改语义、不让 LLM 改写。**  
- 清洗后 `content` < 80 汉字：不入库。

---

## 4. Chunk 设计

目标：一块 = 一个可引用小节（步骤 / 复盘段落 / 红线条款），而不是随意切片割裂「先看健康再排查」。

### 4.1 切分规则

| 格式 | 策略 |
|------|------|
| Markdown | **按 `##` / `###` 切分**；保留标题文本进 `section`；`#` 只作文档标题 |
| DOCX | Heading 2–3 对齐 `##` / `###` |
| PDF | 有标题则按标题；否则按页，页内过长再滑窗 |
| TXT | 空行分段 + 滑窗；`section=全文` 或 `段{n}` |

过短小节（< 80 汉字）与下一节合并。  
过长小节（> 1200 汉字）在 **该标题块内部** 滑窗，避免把「排查步骤」切进「何时升级」。

### 4.2 规模与 overlap（冻结）

| 项 | 值 |
|----|----|
| 目标块大小 | **400～800 汉字**（实现用同一计数器，禁止 token/汉字混用两套阈值） |
| 硬上限 | 1200 汉字 |
| overlap | **100 汉字**；仅块内滑窗。标题相邻节 overlap **0～50 字** |
| 空块 | 丢弃 |
| 送入 embedding 的文本 | `title + "\n" + section + "\n" + chunk正文`（与现 local_store 的「标题增强」同思路，换模型后仍用） |

Markdown **标题必须保留在 `section`**，并作为 embedding 前缀的一部分，便于「Checkout 5xx 排查步骤」与正文对齐。

### 4.3 metadata 继承

每个 chunk **原样继承** Document 级字段，V1 **禁止** chunk 覆盖 `severity` / `category` / `service`。

chunk 必带：

```text
doc_id, title, category, service, department, severity, source_type,
visibility, source_path, section, chunk_id, content
```

| 字段 | 规则 |
|------|------|
| `chunk_id` | `{doc_id}::{section_slug}::{ordinal}`；同一 `doc_id` 重 ingest 时 ordinal 从 0 重排 |
| `section` | 标题路径（`排查步骤`）或 `p.12` / `全文` |
| `content` | 该块正文（可含标题行），即未来 hit.snippet 的来源 |
| 删除/更新文档 | **先按 `doc_id` 删除该文档全部 chunk，再插入新 chunk**（避免孤儿向量） |

`category` / `service` / `severity` / `department` **不出现在 Tool JSON**（C-2 §5.4），仅存在于 Milvus 标量，供过滤与审计。

---

## 5. Embedding（冻结）

| 项 | 值 |
|----|----|
| 供应商 | **SiliconFlow API**（OpenAI 兼容 embeddings） |
| 模型 | **`BAAI/bge-m3`** |
| dimension | **1024** |
| 度量 | COSINE（向量写入前 L2 normalize，与检索一致） |
| Query 与 Chunk | **同一模型、同一 API、同一维度** |
| Rerank | 不做 |
| 本地 sentence-transformers / bge-small-zh | 实现切换后 **退出** 主检索路径，禁止混模 |

失败策略：单次 ingest 中任一 batch embedding 失败 → **整次失败**，不提交半截 collection 版本（见 §7 幂等）。  
密钥：环境变量（如 `SILICONFLOW_API_KEY`），禁止写入仓库。

运行时 `search_knowledge`：对 `query` 调同一 SiliconFlow 接口得到 1024 维向量，再搜 Milvus。Agent **看不见**模型名。

---

## 6. Milvus collection `knowledge_docs`

### 6.1 职责

只存 **chunk 级** 行。一篇文档多行。不存 raw 文件、不存用户会话。

### 6.2 Schema（冻结）

用户指定字段 + 为 Phase A hit 映射补齐的标量（补齐字段 **不** 进入 Tool JSON）：

| 字段 | milvus 类型（实现建议） | 必填 | 说明 |
|------|-------------------------|------|------|
| `id` | INT64 PK，auto_id | 是 | 内部主键；Agent 不可见 |
| `doc_id` | VARCHAR | 是 | 文档稳定 ID |
| `title` | VARCHAR | 是 | 文档标题 → hit.title |
| `category` | VARCHAR | 是 | 五类枚举 |
| `service` | VARCHAR | 是 | 服务 code |
| `department` | VARCHAR | 是 | 归属 |
| `severity` | VARCHAR | 是 | 紧急度 |
| `source_type` | VARCHAR | 是 | md/pdf/docx/txt |
| `chunk_id` | VARCHAR | 是 | 块稳定 ID；建 **unique** 索引 |
| `content` | VARCHAR（足够长，建议 8192） | 是 | 块正文 → hit.snippet |
| `embedding` | FLOAT_VECTOR **dim=1024** | 是 | BGE-M3 dense |
| `section` | VARCHAR | 是（映射补齐） | → hit.section |
| `source_path` | VARCHAR | 是（映射补齐） | → hit.path |
| `visibility` | VARCHAR | 是（过滤补齐） | 不进 Tool |

索引：

- `embedding`：COSINE；语料约百级 chunk，V1 用 **HNSW** 或 **FLAT** 均可；禁止与 1024 以外维度共存。  
- 标量索引：`doc_id`（删除/重建）、可选 `category` / `service` / `visibility`。

V1 过滤：仅检索 `visibility` 允许当前角色看到的行（Employee 默认可 `PUBLIC`；Support 可含 `INTERNAL`）。过滤在 retriever 内完成，**不**给 Agent 新参数。

### 6.3 与 `search_knowledge` hit 映射（禁止改 Tool）

Phase A hit 键：`doc_id` / `title` / `path` / `section` / `snippet` / `score` / `confidence_level`。

本任务验收口述可写成 `title, doc_id, section, snippet, score`；**实现仍输出完整 Phase A 形状**（含 `path`、`confidence_level`），否则与已冻结 C-1 运行时不一致。

| Milvus 行 | → hit |
|-----------|--------|
| `doc_id` | `doc_id` |
| `title` | `title` |
| `source_path` | `path` |
| `section` | `section` |
| `content`（可截断至 600 字 + `…`，与现 local_store 行为对齐） | `snippet` |
| COSINE 相似度 | `score` |
| 阈值分档（沿用现 `KNOWLEDGE_MIN_SCORE` 思路） | `confidence_level` |

**不映射：** `id`、`embedding`、`chunk_id`、`category`、`service`、`department`、`severity`、`source_type`、collection 名、模型名。

---

## 7. ingestion 命令设计

### 7.1 入口

在 `agent/` 下：

```text
python -m app.rag.ingest
```

等价语义：离线 Job，只读 catalog + raw，写 processed（可选）+ Milvus。

### 7.2 输入

| 项 | 默认 | 覆盖 |
|----|------|------|
| 清单 | 仓库 `knowledge/ops/catalog.yaml` | `--catalog` |
| 源根 | 仓库 `knowledge/ops/`（相对路径按 catalog 的 `raw/...`） | `--ops-root` |
| 范围 | 仅 `v1_ingest=true` 且 `status=active` | 无「全 knowledge/ 扫描」开关 |
| Milvus | 环境变量 `MILVUS_URI` 等 | 禁止写死生产地址进代码仓 |
| Embedding | SiliconFlow + `BAAI/bge-m3` | 禁止换模型除非整库 `--rebuild` |

不接受把 `--src knowledge/` 指到旧制度目录。若解析后的路径逃出 `knowledge/ops/raw`，该条失败。

### 7.3 输出

| 产物 | 位置 | 用途 |
|------|------|------|
| Document JSON | `knowledge/ops/processed/documents/{doc_id}.json` | 人工核对 loader |
| chunk JSONL（可选） | `knowledge/ops/processed/chunks.jsonl` | diff 切块 |
| 向量行 | Milvus `knowledge_docs` | 运行时检索 |
| 运行报告 | stdout JSON：成功/跳过/失败 `doc_id`、chunk 数、模型名、dim=1024 | CI / 手测 |

**不输出：** PostgreSQL 行、Go API、frontend 包、把 raw 文件复制进 Agent 镜像以外的第二套正文（镜像只读挂载 `knowledge/ops` 即可）。

### 7.4 幂等

| 场景 | 行为 |
|------|------|
| 同一 `doc_id` 源文件 `content_hash` 未变 | **跳过** embedding 与写入（仍计入报告 skipped） |
| 源文件变了 | 删除该 `doc_id` 全部旧 chunk → 重新 chunk/embed/insert |
| 重复跑且无变化 | collection 行数不变，结果可重复 |
| `chunk_id` 冲突 | 视为同一块 upsert，不得双行 |
| catalog 去掉某篇或 `status≠active` | 按 `doc_id` **删除**向量行（避免已下架文档仍能搜到） |

「幂等」= 相同输入重复执行不产生重复命中、不残留孤儿 chunk；不是「永远不调 API」。hash 未变才跳过 API。

### 7.5 如何重建索引

```text
python -m app.rag.ingest --rebuild
```

语义（冻结）：

1. 确认扫描根仍是 `knowledge/ops/raw`（rebuild **不**放宽扫描范围）。  
2. `drop` collection `knowledge_docs` 或等价「清空全部实体」。  
3. 按 schema §6 重建 collection + 向量索引。  
4. 忽略 `content_hash` 跳过逻辑，对 catalog 准入全集重新 loader → chunk → embedding → insert。  
5. 失败则保持「不可检索」：`search_knowledge` 返回空 hits / `ok` 语义按现 Tool（知识不可用不得编造）。

换模型、换 dim、换度量：**必须 --rebuild**，禁止 1024 与旧 512 维共存。

实现阶段可另提供 `--doc-id OPS-RB-CHECKOUT-5XX` 单篇刷新（仍先删后写）。V1 最小集是全量命令 + `--rebuild`。

---

## 8. `search_knowledge` 保持不变

C-1 已挂白名单。C-3 只替换 `retrieve()` 后端。

### 8.1 对 Agent 可见契约

输入：`query`（必填）；`top_k` 默认 3、最大 5（Phase A 已有，不删）。

输出（形状不变）：

```text
ok, data.query, data.hits[], data.hit_count, data.reliable, data.confidence_level, data.note

hits[]:
  title, doc_id, path, section, snippet, score, confidence_level
```

验收口述的五字段是命中语义的核心；**完整 JSON 仍含 `path` 与 `confidence_level`**。

### 8.2 为什么不改 Tool

- Agent 编排与 Prompt 只认识「查知识 → 片段」。  
- 换 loader / Milvus / SiliconFlow 是运维侧细节。  
- 若把 `collection`、`embedding`、`chunk_id` 暴露给模型，会诱导编造过滤条件或把向量当事实。  
- 前端 Chat 不解析 hit 以外的检索协议。

内部：`retriever.py` 调 SiliconFlow embed(query) → Milvus search → `_hit_dict`。Agent 不知道 Milvus。

Milvus / API 不可用：与现 local 索引缺失相同——空 hits，Prompt 已要求依据不足时不得用常识补公司流程。

---

## 9. 端到端：一个 PDF 如何进入 Milvus

以 `OPS-IR-CHECKOUT-GW-TIMEOUT`（`raw/incident_report/ops-ir-checkout-gw-timeout.pdf` + `.meta.yaml`）为例：

```text
1. ingest 读 catalog.yaml，命中该 doc_id，v1_ingest=true，source_type=pdf
2. 校验路径落在 knowledge/ops/raw/incident_report/，禁止落到 knowledge/制度规范
3. 读 sidecar 元数据（title/category/service/department/severity/…）
4. PDF loader 抽文本层 → elements（页码）→ 清洗 → Document.content
5. 按标题或页切 chunk；每块继承 metadata；生成 chunk_id / section=p.n 或标题
6. 每块文本经 SiliconFlow BAAI/bge-m3 → 1024 维 embedding
7. 若该 doc_id 已有旧行：先删后插
8. insert knowledge_docs：id(auto), doc_id, title, category, service, department,
   severity, source_type=pdf, chunk_id, content, embedding, section, source_path, visibility
9. 运行时：用户问「Checkout 大面积 502 以前怎么复盘」
   → search_knowledge(query)
   → 同模型 embed query
   → Milvus 搜 knowledge_docs
   → hits 只含 title/doc_id/section/snippet/score（及 path/confidence_level）
```

---

## 10. 为什么不把 raw 直接丢给模型

| 原因 | 说明 |
|------|------|
| 格式不可读 | PDF/DOCX 是二进制；模型吃不到稳定正文 |
| 上下文与费用 | 33 篇全文超出可靠窗口，且每次对话重复计费 |
| 不可追溯 | 没有 `doc_id` / `section` / `snippet`，无法引用手册章节 |
| 污染 | 若不做白名单，旧「权限申请 / 服务目录」会混进运维故障回答 |
| 幻觉面 | 未检索时模型会用常识编造公司流程；C-1 Prompt 要求无命中须声明依据不足 |
| 更新 | 手册改一页应重建该 `doc_id` 的向量，而不是指望模型「记住仓库」 |
| 边界 | 实时健康与工单个案必须走 SQL Tool；把 raw 塞进 Prompt 会让模型用过期手册冒充现状 |

知识库的价值是 **可检索的程序性片段**，不是把网盘当 system prompt。

---

## 11. 验收（设计文档必须能回答）

### 1. 一个 PDF 如何进入 Milvus？

见 §9：catalog 白名单 → sidecar 元数据 → 文本层 loader → Document → chunk → SiliconFlow `BAAI/bge-m3`（1024）→ 按 `doc_id` 删旧插入 `knowledge_docs`。无文本层则拒绝。不经过 Go 表、不经过旧 `knowledge/制度规范`。

### 2. 一个 chunk 保存哪些 metadata？

继承：`doc_id` `title` `category` `service` `department` `severity` `source_type` `visibility` `source_path`。  
自身：`chunk_id` `section` `content` + `embedding`(1024)。  
Milvus 另有内部 `id`。Tool 只露出 title / doc_id / path / section / snippet / score / confidence_level。

### 3. 为什么不用直接把 raw 丢给模型？

见 §10：二进制不可读、窗口与费用、不可追溯、旧 IT 语料污染、幻觉、更新与 Tool 边界。

### 4. `search_knowledge` 为什么不需要修改？

它已经是「query → hits」的稳定边界。C-3 替换的是 retrieve 适配器（本地 bge-small 文件 → SiliconFlow + Milvus）。Agent 不需要知道 collection 名或 embedding API。改 Tool 会破坏 C-1 白名单与 Prompt。

### 5. 如何重新生成索引？

```text
cd agent
python -m app.rag.ingest --rebuild
```

清空并按 §6 重建 `knowledge_docs`，对 catalog 准入的 `knowledge/ops/raw` 全量重嵌。换模型必须 rebuild。日常重复执行无变更则幂等跳过（`--rebuild` 除外）。

---

## 12. 与现实现的差集（留给下一编码 Phase，本文不执行）

| 现状 | C-3 目标 |
|------|----------|
| ingest 扫 `agent/knowledge/runbooks/*.md` | 只扫 `knowledge/ops/raw` + catalog |
| `BAAI/bge-small-zh-v1.5` 本地 | SiliconFlow `BAAI/bge-m3` dim 1024 |
| `embeddings.npy` | Milvus `knowledge_docs` |
| 仅 Markdown `##` | MD + PDF + DOCX + TXT |
| 无 Document JSON | processed Document Object |

切换完成前，禁止双根扫描导致同一 `doc_id` 两套正文同时可检索。

---

## 13. Phase C-3 设计验收清单

```text
☑ 本文作为 loader / Document / chunk / SiliconFlow embedding / Milvus schema / ingest CLI 真源
☑ 未修改 backend / agent / frontend / migrations 业务代码
☑ 扫描根冻结为 knowledge/ops/raw；显式禁止旧 IT 助手目录
☑ collection=knowledge_docs；embedding=BAAI/bge-m3 dim=1024 COSINE
☑ V1 格式：MD/PDF/DOCX/TXT；HTML 只预留
☑ search_knowledge 入参 query、hit 形状不扩展
☑ 幂等（按 doc_id 删后写 + hash 跳过）与 --rebuild 已说明
☑ 五个验收问题可在 §11 直接回答
```
