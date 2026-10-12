# Phase C-2 — 企业运维知识库设计契约

> 状态：**设计冻结（2026-10-03）**（当时只改本文）。**实现后**检索后端以 C-3 / 现网为准（bge-m3 + Milvus）。  
> **V1 现行**：北极星 = AI 运维故障工单助手；主链 Ticket / Health / Audit / HITL；本文管 **知识资产分类与 catalog**，不是「再设计一套 RAG」。  
> Permission / Phase 10 制度语料 = Legacy。知识后台 = 不做。  
> 冲突：hit JSON → Phase A；资产分类 / catalog → 本文；运行时向量存储 → C-3 现网（Milvus）。

---

## 0. 本阶段做什么 / 不做什么

### 0.1 要解决的问题

OpsPilot 知识库要回答的是：

> 当用户用自然语言描述故障或运维疑问时，Agent 能否从 **企业真实会存在的运维资产** 中拿到可追溯片段，而不是用模型常识编造公司流程？

知识库服务 **一类场景**（故障排查、服务说明、历史复盘、变更/值班流程、安全底线），不是服务 **某一个 Demo 问句**。  
Checkout 502、Auth 登录失败、Order Worker 堆积，只是检索命中的 **案例**，不能反向决定分类与规模。

### 0.2 非目标（本文件与后续实现均禁止自行加入）

```text
本设计阶段：不写 parser / ingest 脚本 / embedding 任务 / Milvus client
不实现知识管理后台、上传审批、HTTP CRUD、PostgreSQL knowledge_documents
不把 tickets / services 健康快照 / 用户画像写入知识库
不把工单全文做向量检索（工单仍走 search_tickets SQL）
不接 Prometheus / CMDB / 真实 wiki 同步
不做 OCR 平台、Rerank 默认链路、评测平台、Multi-Agent
不把 Phase 10 权限申请 / 入职 FAQ 重新做成 V1 主检索集
```

### 0.3 与现有文档的关系

| 文档 | 关系 |
|------|------|
| Phase A §6 | V1 **运行时**可先用本地向量适配器；hit 字段不改。本文把 **目标** Embedding 定为 BGE-M3、Store 定为 Milvus |
| `docs/RAG_DESIGN.md` | 描述 Phase 10 关键词现状与 Phase A 本地 embedding 过渡；C-2 实现时替换检索后端，不推翻 Tool |
| `knowledge/` Phase 10 制度 | **退出 C-2 索引名单**；文件可留仓 |
| `agent/knowledge/runbooks/` 已有 4 篇 | 视为 C-2 Runbook 分类的 **早期子集**，后续迁入本文目录，而不是知识体系的全部 |
| Phase 15 | 方向相近（异构 + Milvus），但面向旧「IT 服务制度」；C-2 面向 **运维故障知识**，分类以本文为准 |

---

## 1. Knowledge Base 定位

### 1.1 知识库解决什么问题

知识库是 Agent 的 **只读运维经验层**：把「手册里怎么排、这类事故上次怎么结、这个服务是干什么的、变更/升级有什么红线」变成可检索片段。

它解决的是 **程序性 / 经验性知识**：

| 用户在问 | 知识库应提供 |
|----------|----------------|
| 这类故障先查什么、如何止血 | Runbook 步骤 |
| 这个服务依赖谁、影响面是什么 | Service Manual |
| 以前同类事故根因与复盘结论 | Incident Report（结构化复盘，不是工单行） |
| 发布回滚、值班升级、报障怎么走 | Operation Process |
| 日志能否外发、密钥能否贴进工单 | Security Guideline |

它 **不解决**：

- 当前服务是否挂了 → `get_service_status` / `list_services`
- 有没有同类未关工单、某张单的状态与 `analysis` → `search_tickets` / `get_ticket`
- 谁登录、工单可见性 → Go + JWT，不是文档
- 创建/改单 → HITL 写 Tool，知识库只提供建议依据

### 1.2 与 `search_tickets`、`service_status` 的边界

三层权威，禁止互相替代：

```text
实时状态     → services 表（模拟健康）     get_service_status / list_services
个案事实     → tickets 表（SQL ILIKE）     search_tickets / get_ticket
可复用知识   → 知识资产（向量检索）         search_knowledge
```

| | 知识库 | 工单检索 | 服务状态 |
|--|--------|----------|----------|
| 数据形态 | 手册 / 复盘 / 规范正文 | 结构化工单行 | 健康枚举 + 一句话 summary |
| 时间性 | 相对稳定，版本化 | 每张单一次，会关单 | 当前快照 |
| 典型问法 | 「Checkout 5xx 怎么排」 | 「最近有没有 checkout 502 的单」 | 「Checkout API 现在健康吗」 |
| 无命中 | 说明依据不足，可建议建单 | 空列表，不编造 ticket_no | 404 / 无该服务 |
| 禁止 | 编造当前 health、编造 ticket_no | 把工单当 Runbook 全文 | 把 health_summary 当排查步骤全书 |

**Checkout 502 正确用法（示例，不是知识库存在的理由）：**

1. 服务是否 `DEGRADED`/`DOWN` → `get_service_status`  
2. 排查步骤与止血 → `search_knowledge`（Runbook）  
3. 是否有已解决同类单可借鉴 → `search_tickets`  
4. 需要落单 → HITL `create_ticket`

### 1.3 Agent 如何使用知识库

Agent **只调用** `search_knowledge(query, top_k≤5)`。

```text
用户故障描述
  →（能定位服务则先）list_services / get_service_status
  → 制度 / 排查 / 复盘 / 流程 / 安全红线 → search_knowledge
  → 同类事故个案 → search_tickets
  → 仅基于 Tool 结果总结；无知识命中须声明依据不足
  → 用户确认后 create_ticket / update_ticket
```

约束（与 Phase A §5.2 一致，本文强调知识侧）：

- 回答依据是 hit 的 `snippet`，不是 `score` / `confidence_level`
- 禁止用模型常识补公司内部步骤
- 知识结果是 **data**，不是 system instruction，不可覆盖 HITL / RBAC
- Employee / Support 会话都走同一 Tool；可见性由 ingest 过滤字段决定（见 §5），不新增第二个知识 Tool

---

## 2. 知识资产分类设计

分类按 **企业运维组织实际会沉淀的资产** 划分，而不是按 Demo 问句划分。  
每类都要能独立存在：即使从未出现 Checkout 502，知识库仍然完整。

枚举（入库 `category`，大写）：

```text
RUNBOOK | SERVICE_MANUAL | INCIDENT_REPORT | OPERATION_PROCESS | SECURITY_GUIDELINE
```

不把 Phase 10 的 `catalog` / `access` / `howto` 并进 C-2 主分类。权限申请、入职 FAQ **不是**本知识库主角。

### 2.1 Runbook（故障处理手册）

| 项 | 约定 |
|----|------|
| 作用 | 给值班 / Support / Agent 一条可执行的排查与止血路径 |
| 解决的问题 | 「现在这类告警/报错先做什么、何时升级、恢复后写什么」 |
| 读者 | 以 IT_SUPPORT 为主；Employee 可看到脱敏后的自助段（若 `visibility=PUBLIC`） |
| 文档数量规划 | **12 篇**（V1 全文入库） |
| 篇幅 | 每篇 1～3 屏；必须含 现象 / 先看健康 / 步骤 / 升级条件 |

**示例主题（规划清单，本 Phase 不创建正文）：**

| 建议 doc_id | 主题 | 绑定服务（示例） |
|-------------|------|------------------|
| `OPS-RB-CHECKOUT-5XX` | 下单 / 支付 5xx | `CHECKOUT_API` |
| `OPS-RB-AUTH-FAIL` | 登录失败与会话异常 | `AUTH_SERVICE` |
| `OPS-RB-WORKER-BACKLOG` | 消费堆积、队列不下降 | `ORDER_WORKER` |
| `OPS-RB-PAY-TIMEOUT` | 支付通道超时与切备 | `CHECKOUT_API` |
| `OPS-RB-DEP-TIMEOUT` | 上游依赖超时 / 连接池 | 多服务 |
| `OPS-RB-RELEASE-ROLLBACK` | 发布后回滚 | 平台 |
| `OPS-RB-CACHE-STAMP` | 缓存击穿 / 热点 key | 平台 |
| `OPS-RB-DB-SLOW` | 慢查询导致接口超时 | 平台 |
| `OPS-RB-MQ-LAG` | 消息积压与死信 | `ORDER_WORKER` 等 |
| `OPS-RB-INGRESS-5XX` | 网关 / 入口 5xx | 平台 |
| `OPS-RB-CERT-EXPIRY` | 证书过期与 TLS 失败 | 平台 |
| `OPS-RB-ESCALATE` | 何时升级人工（已有 escalate 语义） | 全局 |

已落盘的 `agent/knowledge/runbooks/*.md` 对应上表前若干 ID，**算入 12 篇，不另起一套 Checkout 专用库**。

### 2.2 Service Manual（服务说明）

| 项 | 约定 |
|----|------|
| 作用 | 说明服务职责、依赖、典型故障面、建单时该绑哪个 `service_id` |
| 解决的问题 | 「这是什么系统、谁负责、影响谁、不要误绑 GENERAL_IT」 |
| 文档数量规划 | **6 篇** |

**示例主题：**

- Checkout API 服务说明（支付域、依赖、错误码含义）
- Auth Service 服务说明（登录、会话、与 Checkout 的关系）
- Order Worker 服务说明（异步履约、积压含义）
- 平台入口 / 网关说明（可选独立篇，或并入平台手册）
- 可观测性约定（日志字段、request_id、禁止把密钥打进日志）
- 服务目录（运维视角：ACTIVE 服务如何选，**不是**旧 IT 服务台目录）

V1 seed 只有三个 ACTIVE 服务时，手册仍按这三个写实，并保留 1～2 篇平台级说明，避免知识库 = 三个 Demo 服务 FAQ。

### 2.3 Incident Report（历史事故复盘）

| 项 | 约定 |
|----|------|
| 作用 | 沉淀 **已关闭事故的根因与改进**，供检索「以前是不是这样」 |
| 解决的问题 | 与工单的差集：工单是个案流水；复盘是结构化教训（时间线、根因、影响、行动项） |
| 文档数量规划 | **6 篇** |
| 硬规则 | 不复制 `tickets` 行；不出现真实 PII；可引用虚构 `ticket_no` 作为叙事，Agent 仍须用 `search_tickets` 查真单 |

**示例主题：**

- 支付网关超时导致 Checkout 大面积 502（对应 Demo 可命中，但是复盘体裁）
- 配置错误导致 Auth 全员登录失败
- Worker 并发参数误改导致积压
- 变更窗口外发布引发回滚
- 缓存预热不足导致早高峰击穿
- 证书轮转遗漏导致 TLS 失败

有 1 篇与 Checkout 相关是合理的 **覆盖**，另外 5 篇必须覆盖其它域，防止整库围着 502 转。

### 2.4 Operation Process（运维流程规范）

| 项 | 约定 |
|----|------|
| 作用 | 人与 Agent 都要遵守的作业流程，不是单故障步骤 |
| 解决的问题 | 报障怎么写、值班如何升级、变更/回滚门禁、如何写 `analysis` |
| 文档数量规划 | **5 篇** |

**示例主题：**

- 故障工单分析写法（`ticket-analysis-guide` 归入此类或 Runbook 二选一：**归入本类**，避免与 Runbook 重复建设）
- 报障信息最低集（时间窗、影响面、service、是否可复现）
- 值班升级与 P 级定义
- 变更与回滚检查单
- 沟通口径（对员工可说什么、禁止承诺未证实根因）

### 2.5 Security Guideline（安全规范）

| 项 | 约定 |
|----|------|
| 作用 | 运维与报障场景下的安全红线，防止 Agent 把危险操作写进建议 |
| 解决的问题 | 日志/工单脱敏、密钥与生产数据、高危操作必须人工 |
| 文档数量规划 | **4 篇** |
| 注意 | 不是重建 Phase 10「权限申请指南」；不教如何绕过审批 |

**示例主题：**

- 工单与 Chat 中的敏感信息处理
- 生产日志查询与导出边界
- 密钥 / 证书 / 连接串禁止事项
- 高危操作（删库、关防火墙、批量踢登录）必须人工，Agent 只升级不执行

### 2.6 分类总览

| category | 篇数 | 主要问题 | 与 Demo 的关系 |
|----------|------|----------|----------------|
| RUNBOOK | 12 | 怎么排、怎么止血 | 可含 Checkout 1 篇 |
| SERVICE_MANUAL | 6 | 这是什么服务 | 覆盖 seed 三服务 + 平台 |
| INCIDENT_REPORT | 6 | 以前根因是什么 | 至多 1～2 篇支付域 |
| OPERATION_PROCESS | 5 | 流程与写法 | 含 analysis / 升级 |
| SECURITY_GUIDELINE | 4 | 不能做什么 | 全库通用 |
| **合计** | **33** | | 个人可维护上限；禁止再注水 FAQ |

33 篇是 **资产规划上限（含已有 Runbook 子集）**。实现阶段允许先 ingest 其中 **active** 子集，但目录与 ID 按本表预留，避免临时为某个问句加篇。

---

## 3. 文档格式支持范围

企业运维知识很少全是 Markdown：Runbook 常在 Wiki/MD；正式复盘与安全规范常是 PDF/DOCX；值班备忘可能是 TXT；内部门户可能是 HTML。  
C-2 **设计多格式进入同一 Document Object**；本阶段不写 parser。

| source_type | 为什么支持 | 后续 parser 如何处理 | 是否进入 V1 入库 |
|-------------|------------|----------------------|------------------|
| `markdown` | 仓库协作默认形态；已有 Runbook | 读 UTF-8；解析 YAML front matter；按 ATX 标题建树 | **是（主格式）** |
| `pdf` | 正式发布的复盘 / 安全规范 | 文本层抽取（页码写入 `source_location`）；忽略扫描件；**不做 OCR** | **是（少量样例，2～4 篇）**；无文本层则拒绝入库 |
| `docx` | 部门手册仍用 Word | `python-docx` 或等价：段落 + 标题样式 → 与 MD 同类结构 | **是（少量样例，2～3 篇）** |
| `txt` | 告警粘贴、值班备忘 | 编码探测；按空行分段；无标题则滑窗切块 | **是（1～2 篇即可）** |
| `html` | 内部门户导出 | 去导航/脚注，取 article 正文与 heading | **可选；V1 不入库** |

补充规则：

- **同源多格式**：同一 `doc_id` 只指定一个 `canonical` 源；禁止 PDF 与 MD 正文互相矛盾且同时可检索。
- **不进 V1**：图片 OCR、扫描 PDF、XLSX 权限矩阵、音视频。
- Parser 失败：该文件不进入 `processed/`，记录错误；**禁止**用 LLM「补全」缺失页冒充原文。

---

## 4. Knowledge Directory 设计

权威根目录：**仓库 `knowledge/ops/`**（与 Phase 10 中文制度目录隔离）。  
运行时索引产物：**`agent/data/knowledge_index/`**（gitignore，与 Phase A 一致）。  
现有 `agent/knowledge/runbooks/` 在实现阶段迁入 `knowledge/ops/raw/runbook/`，本设计阶段 **不搬文件**。

```text
knowledge/ops/
├── README.md                 # 清单真源：doc_id ↔ 路径 ↔ category ↔ V1 是否入库
├── catalog.yaml              # 机器可读清单（实现阶段创建；本 Phase 不落文件）
├── raw/                      # 只增改源文件，ingest 只读
│   ├── runbook/
│   ├── service_manual/
│   ├── incident_report/
│   ├── operation_process/
│   └── security_guideline/
├── processed/                # ingest 产物（可 gitignore）
│   ├── documents/            # 一篇一 JSON：Document Object
│   └── chunks/               # 可选：chunk JSONL，便于 diff
└── index/
    ├── local/                # 过渡：向量 + id 映射（numpy/json 等）
    └── milvus/               # 仅 schema / collection 说明；本阶段无实例
```

设计理由：

| 层 | 为什么单独存在 |
|----|----------------|
| `raw/` | 按 **分类** 而不是按 Demo 服务名建目录，避免 `checkout/` 独占 |
| `processed/` | Parser 输出可复查：切块问题出在清洗还是模型 |
| `index/local/` | 个人项目无 Milvus 时仍能跑 Agent |
| `index/milvus/` | 只放集合字段约定，实现时替换适配器 |

**禁止：**

- 把 `knowledge/VPN与远程办公/` 等 Phase 10 路径扫进 C-2 ingest
- 在 `frontend/` 或 Go migration 里放向量
- 为知识后台再建模一套「用户上传目录」

文件命名：`{doc_id}` 小写短横线或保持 ID 可读，如 `ops-rb-checkout-5xx.md`。扩展名表示 `source_type`。

---

## 5. 文档 Metadata Schema

统一对象叫 **Document Object**。Markdown 用 YAML front matter；PDF/DOCX/TXT 用同路径 `*.meta.yaml` sidecar（与 Phase 10 矩阵旁路同一思路）。

### 5.1 必填字段（V1 契约）

| 字段 | 类型 | 说明 | 为什么需要 |
|------|------|------|------------|
| `doc_id` | string | 稳定 ID，如 `OPS-RB-CHECKOUT-5XX` | 引用、upsert 替换、跨格式同源；路径可变 ID 不可变 |
| `title` | string | 中文标题 | hit.title；Agent 引用来源 |
| `category` | enum | §2 五类 | 过滤、清单、避免制度/权限类混入 |
| `source_type` | enum | `markdown` / `pdf` / `docx` / `txt` / `html` | 选择 parser；审计「这篇从哪类文件来」 |
| `service` | string | `CHECKOUT_API` / `AUTH_SERVICE` / `ORDER_WORKER` / `PLATFORM` / `MULTI` | 与 seed 服务 code 对齐；检索可加权，但 **不是** SQL `service_id` |
| `department` | string | 如 `运维部` / `信息安全` / `平台工程` | 企业知识归属；后续 INTERNAL 可见性 |
| `severity` | enum | `INFO` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` | Runbook/复盘的默认紧急度；手册类用 `INFO` |
| `created_at` | string | ISO-8601 日期或时间 | 版本新旧；复盘排序 |
| `content` | string | Parser 后的纯文本（或结构化块序列的展开） | Embedding 与展示的原文权威（相对 raw 的文本层） |

`content` 在 **raw 源文件** 里是正文本身；在 **processed Document Object** 里是清洗后全文。不要在 front matter 再复制一份全文。

### 5.2 建议扩展（实现可带，不进 Phase A hit JSON）

| 字段 | 说明 |
|------|------|
| `visibility` | `PUBLIC` / `INTERNAL`；不明则 Fail Closed 不入库 |
| `status` | `draft` / `active` / `archived`；仅 `active` 进索引 |
| `version` | 语义化版本 |
| `source_path` | raw 相对路径 |
| `canonical` | 是否主源 |
| `updated_at` | 最后修订 |

不把 `related_intent: permission` 作为 C-2 主字段。不建 Go `knowledge_documents` 表。

### 5.3 Front matter 示例（Markdown）

```yaml
---
doc_id: OPS-RB-CHECKOUT-5XX
title: Checkout API 5xx 排查手册
category: RUNBOOK
source_type: markdown
service: CHECKOUT_API
department: 运维部
severity: HIGH
created_at: 2026-10-03
visibility: PUBLIC
status: active
version: 1.0.0
---
```

### 5.4 与 `search_knowledge` hit 的映射（冻结形状，不扩展 Tool）

Phase A hit：`doc_id` / `title` / `path` / `section` / `snippet` / `score` / `confidence_level`。

| Document / Chunk | → hit |
|------------------|--------|
| `doc_id` | `doc_id` |
| `title` | `title` |
| `source_path` | `path` |
| 标题路径或页码 | `section` |
| chunk 文本 | `snippet` |
| 相似度 | `score` |
| 阈值分档 | `confidence_level` |

`category` / `service` / `severity` **暂不出现在 Tool JSON**，避免 C-1 已冻结契约膨胀。内部检索可用这些字段做过滤或加权。

---

## 6. 文档处理 Pipeline

只设计流程。离线 Job 跑在 Agent 工程内，**不是** Go API。

```text
Raw Document（knowledge/ops/raw/** + sidecar）
        ↓
     Parser
        ↓
  Document Object（processed/documents）
        ↓
     Cleaning
        ↓
      Chunk
        ↓
    Embedding
        ↓
  Vector Database（local 适配器 或 Milvus）
        ↓
  运行时：search_knowledge → hits
```

| 步骤 | 输入 | 输出 | 失败策略 |
|------|------|------|----------|
| Raw | 源文件 + 必填元数据 | 字节流 + meta | 缺必填字段：跳过该文件 |
| Parser | 按 `source_type` | 标题树 + 纯文本 + `source_location`（页/标题） | 抽不出文本：拒绝；不做 OCR |
| Document Object | parser 结果 + meta | 一篇一对象 JSON（含 `content`） | 校验 enum |
| Cleaning | `content` | 去页眉页脚、重复空白、HTML 残渣；**不改语义** | 清洗后过短（如 < 80 字）：不入库 |
| Chunk | 清洗文本 + 结构 | chunk 列表，继承 §7 元数据 | 空 chunk 丢弃 |
| Embedding | chunk 文本 | 向量；query 与 chunk **同一模型** | 模型不可用：整次 ingest 失败，不混用两个模型 |
| Vector Store | 向量 + 标量字段 | 可检索集合；按 `doc_id` upsert 替换旧 chunk | Store 不可用：`search_knowledge` 应表现为知识不可用，禁止回退编造 |

**不在 Pipeline 中：** Rerank、在线学习、把 LLM 改写后的文本当原文。

---

## 7. Chunk 策略设计

目标：一块 = **一个可执行或可引用的小节**，而不是随意 512 字符切片把步骤割裂。

### 7.1 是否按标题切分

| 格式 | 策略 |
|------|------|
| Markdown / HTML | **按 `##` / `###`（或 h2/h3）切分**；`#` 仅作文档标题不单独成块 |
| DOCX | 按 Heading 1–3 样式，对齐 MD |
| PDF | 能识别书签/字体标题则按标题；否则按页再滑窗 |
| TXT | 无标题：空行分段 + 滑窗 |

过短小节（< 80 汉字）与下一节合并。过长小节（> 1200 汉字）在标题块 **内部** 再滑窗，避免把「排查步骤」拆进无关「何时升级」。

### 7.2 规模与 overlap

| 项 | 冻结建议 |
|----|----------|
| 目标块大小 | **400～800 汉字**（或等价 token，实现时用同一计数） |
| 硬上限 | 1200 汉字 |
| overlap | **100 汉字**（约 15%）；仅用于块内滑窗，标题切分的相邻节 overlap 可为 0～50 字以免步骤重复刷屏 |
| top_k | Tool 层 ≤ 5，默认 3（Phase A） |

中文运维手册以步骤列表为主，过小 chunk 会丢掉「先看健康再搜工单」的顺序；过大则 5 条 hit 里全是同一篇。

### 7.3 metadata 如何继承

每个 chunk 必须带：

```text
doc_id, title, category, source_type, service, department, severity,
created_at, path, section
```

- `section`：标题路径（如 `排查步骤`）或 `p.12`
- 文档级字段 **原样继承**，禁止 chunk 覆盖 `severity` 除非正文显式分节（V1 不做分节覆盖）
- 向量库标量字段至少：`doc_id`, `category`, `service`, `visibility`（若有），便于后续过滤
- 删除/归档一篇文档：按 `doc_id` 删除其全部 chunk 再写入新版本

---

## 8. Embedding 与 Vector Store 设计

### 8.1 目标方案（C-2 设计冻结）

| 项 | 选择 |
|----|------|
| Embedding | **BAAI/bge-m3** |
| Vector Database | **Milvus** |
| 度量 | COSINE |
| Rerank | 默认不做 |
| Query 与 Chunk | 必须同一模型 |

### 8.2 为什么选择

**BGE-M3**

- 中英文混合（告警英文、手册中文）常见于运维语料
- 支持较长上下文，适合 400～800 字 chunk
- 多功能检索（dense；未来若要 sparse/colbert 不必换底座）
- 相对「仅中文小模型」，更接近企业知识库而非 Demo 玩具

**Milvus**

- 企业向量检索的常规落点：过滤（`category`/`service`/`visibility`）+ 向量
- 按 `doc_id` upsert、独立于 PostgreSQL 业务库
- 与「工单 SQL、知识向量」边界一致

### 8.3 当前阶段为什么先设计、不立即实现

1. **资产没定死就接 Milvus，只会为 Checkout 502 造 4 篇 MD** —— 先有分类与清单，ingestion 才有扫描范围。  
2. **C-1 刚收敛 Tool**：先保证 `query → hits` 契约稳定，再换后端。  
3. **个人项目成本**：Milvus 进程、镜像、磁盘与模型下载不是 Demo 主链阻塞项。  
4. **Phase A 仍允许本地适配器**：实现可分两步——先 ingest→chunk→**同一套 Document Object**→本地向量；再把 Store 换成 Milvus，**不改 Tool 名与 hit 字段**。  
5. **禁止**在设计未落地时把 Phase 10 关键词检索包装成「已经企业级」。

过渡允许（仅实现阶段、且须写在 ingest README）：

```text
目标：BGE-M3 + Milvus
过渡：同一 Pipeline；Embedding 可临时用已下载的兼容模型；Store 用 agent/data/knowledge_index/
切换：只替换 retriever 适配器
禁止：关键词检索作为 C-2 目标态；禁止 hit 形状分叉
```

若过渡模型不是 BGE-M3，索引必须整库重建，不得混模检索。

---

## 9. V1 知识规模规划

原则：**真实企业会有的种类都要有样本，但总量一个人能改完、能人工审完。**

| 分类 | 篇数 | 主格式 | V1 是否全部 ingest |
|------|------|--------|-------------------|
| Runbook | 12 | MD 为主，可 1 篇 TXT 备忘 | 是 |
| Service Manual | 6 | MD | 是 |
| Incident Report | 6 | MD 4 + **PDF 2**（正式复盘） | 是（PDF 无文本则改 MD） |
| Operation Process | 5 | MD 3 + **DOCX 2**（流程签发感） | 是 |
| Security Guideline | 4 | MD 2 + **PDF 1** + **DOCX 1** | 是 |
| HTML | 0 | — | V1 否 |
| **合计** | **33** | | 约 25～28 个 MD/TXT + 3 PDF + 3 DOCX |

体量对照：

| 太大（不做） | 本规划 | 太假（禁止） |
|--------------|--------|----------------|
| 上百篇网盘镜像 | 33 篇、可审 | 只 4 篇 Checkout Runbook |
| 全公司 Wiki 爬虫 | 五类齐全、每类有独立主题 | 把同一 502 改写 10 遍 |
| 扫描件 OCR | 每篇短、结构固定 | 全是「问：checkout 怎么办」FAQ |

**与 Phase A「8～12 篇 Runbook」的关系：** 那是当时最小 Demo 检索集。C-2 把 Runbook **落在 12 篇**，并补齐其它四类。后续实现若必须裁剪，优先保留五类各至少 2 篇，**禁止**只留 Checkout 相关文档。

已有文件占用配额：`checkout-5xx` / `auth-failures` / `order-worker-backlog` / `ticket-analysis-guide` 计入 12+5，不重复规划。

---

## 10. 与 Agent 的关系

### 10.1 Tool 不暴露底层

Agent 只看见：

```text
search_knowledge(query, top_k) → { ok, data: { hits: [...] } }
```

不看见：Milvus collection、embedding 模型名、chunk_id、文件 parser、本地 npy 路径。

内部可替换：

```text
Retriever Adapter
    ├─ local cosine index     （过渡 / 无中间件）
    └─ Milvus                 （目标）
最终目标：企业级知识检索（过滤 + 向量 + 来源可追溯）
```

### 10.2 消费规则

- 需要步骤 / 手册 / 复盘 / 流程 / 安全红线 → **必须先** `search_knowledge`
- hits 空或整体 `confidence_level=low` → 告知未知，引导建单或人工；**禁止**补公司流程
- 需要「现在是否故障」→ 状态 Tool，不是知识库
- 需要「哪张单」→ 工单 Tool
- 写操作仍 HITL；知识库不能 approve

### 10.3 实现顺序（供后续 Phase，本文件不执行）

```text
1. 按本文目录与 catalog 撰写/迁移 raw 资产（仍可无向量）
2. Parser + Document Object + Chunk（可先只接 MD）
3. Embedding + local index，接上 search_knowledge
4. 补 PDF/DOCX parser 与样例
5. Milvus 适配器替换 local store
禁止颠倒：先接 Milvus 再想「库里有什么文档」
```

---

## 11. 验收（设计文档必须能回答）

### 1. OpsPilot 知识库有哪些文档？

五类共 **33 篇规划**：Runbook 12、Service Manual 6、Incident Report 6、Operation Process 5、Security Guideline 4。主题见 §2 示例表与 §9 格式配比。不是「若干 markdown」，而是带 `doc_id` 的运维资产清单。

### 2. 为什么这些文档符合运维场景？

分类对应真实岗位产出：值班手册、服务说明书、事故复盘、变更/升级流程、安全红线。覆盖支付、身份、异步任务、发布、缓存、数据库、证书等 **运维故障面**，而不是 IT 服务台权限申请。

### 3. 多格式如何进入系统？

`raw/` 存放源文件 → 按 `source_type` Parser → 统一 Document Object。V1：MD/TXT 为主，PDF/DOCX 少量；HTML 可选且不进 V1。无文本层 PDF 拒绝。同源只保留 canonical。

### 4. ingestion 后产生什么数据？

`processed/documents` 的 Document Object；chunks（继承元数据）；embedding 向量；可被检索的 index（local 或 Milvus）。**不**产生工单行、**不**写 PostgreSQL 知识表、**不**产生后台 CMS。

### 5. Agent 如何消费知识？

只调 `search_knowledge`：`query → hits`。用 snippet 作答，结合状态/工单 Tool，无命中则承认依据不足。

### 6. 为什么不是为了某个 Demo 临时造文档？

清单按企业资产类型配额建设；Checkout 502 只占 Runbook/复盘中的少数篇；禁止用同一问句扩写充数；目录按 category 而不是按 `checkout/` 服务名组织。

---

## 12. Phase C-2 设计验收清单

```text
☑ 本文作为知识分类 / 目录 / 元数据 / Pipeline / chunk / 目标向量方案真源
☑ 未修改 backend / agent / frontend 业务代码
☑ 未实现 ingestion、未接 Milvus、未设计知识后台
☑ search_knowledge 仍为唯一知识 Tool；hit 字段不在本文擅自扩 JSON
☑ 工单 SQL 与服务健康不进入知识库
☑ 规模为 33 篇五类，而非 4 篇 Checkout Runbook
☑ 多格式与 V1 范围已声明
☑ Embedding 目标 BGE-M3、Store 目标 Milvus；当前只设计不实施
```
