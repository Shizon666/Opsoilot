# OpsPilot V1 运维知识库建设规范（K0 冻结）

> **状态：** K0 规范冻结（2026-10-09）  
> **适用范围：** 仅 `knowledge/ops/`（`catalog.yaml` + `raw/**`）  
> **非适用范围：** Phase 10 中文制度目录（`knowledge/制度规范/`、VPN、GitLab 等）、`agent/knowledge/runbooks/` 遗留副本  
> **Phase 10 元数据：** 见 [`../元数据/文档元数据规范.md`](../元数据/文档元数据规范.md)（**不**用于 V1 ops）  
> **本阶段禁止：** 为凑规范而批量改写正文、改 RAG/Milvus/检索配置、把未确认设定写成生产事实  

配套：

| 文件 | 用途 |
|------|------|
| [`PENDING_CONFIRMATIONS.md`](PENDING_CONFIRMATIONS.md) | 未确认模拟设定清单 |
| [`scripts/validate_structure.py`](scripts/validate_structure.py) | 静态结构校验（只读） |
| [`README.md`](README.md) | 清单与入库命令入口 |
| [`catalog.yaml`](catalog.yaml) | 机器可读入库白名单 |

---

## 1. 事实边界（不可违反）

1. V1 **ACTIVE** 业务服务仅：`CHECKOUT_API`、`AUTH_SERVICE`、`ORDER_WORKER`（seed / Backend）。  
2. `HEALTHY` / `DEGRADED` / `DOWN` 为**模拟健康快照**，禁止写成真实 Prometheus / 指标平台。  
3. Agent **无**真实日志查询、Prometheus、基础设施变更、权限写入 Tool；仅有：用户、服务健康、工单读写、`search_knowledge`。  
4. 工单状态、`priority`、角色与 HITL 以 Go Backend + Agent Tool/Prompt 契约为准（见 §6）。  
5. Phase 10 语料 **不得**进入 V1 `catalog.yaml` / ingest。  
6. 模拟事故、虚构时间线、假设根因、模拟依赖必须标注；不得冒充生产事实。  
7. 未经确认的错误码、超时阈值、SLA、成功率门禁、依赖时序、操作授权：**不得**写入 `basis: code`；见待确认清单。

---

## 2. 八类知识用途与 catalog `category` 映射

V1 **入库分类**仍使用既有五类枚举（与 `load` / C-2 契约兼容）。八类是**用途角色**，一篇文档对应一个主角色；禁止一篇同时充当互斥角色（例如既是完整 Runbook 又是复盘正文）。

| 用途 ID | 用途名称 | 适用 `category` | 适用范围（写什么） | 不写什么 |
|---------|----------|-----------------|--------------------|----------|
| C1 | 服务目录与依赖 | `SERVICE_MANUAL` | ACTIVE 选型、禁止 `GENERAL_IT`、依赖总览（须标依据）、指向 SM/RB | 第四个虚构 ACTIVE 业务 code；VPN/权限目录 |
| C2 | 服务操作手册 | `SERVICE_MANUAL` | 职责/非职责、依赖、故障模式→Runbook、建单绑定 | 逐步排障全文（应链到 C3） |
| C3 | 故障 Runbook | `RUNBOOK` | 触发条件、证据、鉴别、分步排查、缓解、升级、恢复验证 | 未授权的「已执行切流/杀连」口吻；假日志平台步骤 |
| C4 | 事故复盘 | `INCIDENT_REPORT` | 模拟案例：时间线、影响、事实/推测分栏、行动项 | 真实生产事故编号；可查 tickets 表的假单号 |
| C5 | 工单与状态规范 | `OPERATION_PROCESS` | 建单时机、最低信息、analysis、状态迁移、角色 | 发明新状态；OPEN→CLOSED |
| C6 | 分级升级与协作 | `OPERATION_PROCESS`（短备忘可用 `RUNBOOK`） | P 级、与 priority 映射、升级路径、HITL 边界 | 把 P 级写成 API 新字段 |
| C7 | 安全与高风险 | `SECURITY_GUIDELINE` | PII、密钥、导出、高危须人工；对照 Agent 能力 | 授予 Agent 不存在的权限 |
| C8 | 可观测与能力边界 | `SERVICE_MANUAL`（可与 C7 交叉引用） | V1 有哪些证据、没有哪些 Tool | Prometheus 操作手册 |

**横切（可选专文，`category` 用 `OPERATION_PROCESS` 或挂在 C1）：** 术语、别名、易混故障对、doc 索引。不是第九业务域。

目录约定（已有）：

```text
raw/runbook/              → 主要为 C3（偶发 C6 短备忘）
raw/service_manual/       → C1 / C2 / C8
raw/incident_report/      → C4
raw/operation_process/    → C5 / C6 / 横切
raw/security_guideline/   → C7
```

---

## 3. 每类必填内容与验收清单

K0 **冻结模板**；K1 起新建/重写正文必须满足。现有 33 篇未达标者记为技术债，**不在本阶段批量改写**。

### 3.1 通用（所有用途）

- [ ] 元数据完整（§4）且 `status`/`canonical`/`v1_ingest` 与 catalog 一致  
- [ ] 文首或专节含模拟环境声明（§5）  
- [ ] `basis` / `basis_notes` 已填或显式指向待确认项 ID  
- [ ] 服务名 / 状态 / priority 用词符合 §6  
- [ ] `related_docs` 仅引用现行 `active` doc_id  
- [ ] 未声称使用不存在的 Agent Tool  
- [ ] 未把 Phase 10 制度当 V1 依据  

### 3.2 C1 服务目录与依赖

- [ ] ACTIVE 三选一规则 + 禁止 `GENERAL_IT`  
- [ ] 平台问题如何绑定业务服务（不发明第四 ACTIVE）  
- [ ] 依赖说明带 `basis`；未确认项只引用 `PENDING-*`  
- [ ] 指向各服务 C2 / 核心 C3  

### 3.3 C2 服务手册

- [ ] 职责与非职责  
- [ ] 上下游依赖（区分 code / simulated）  
- [ ] 已知故障模式 → Runbook `doc_id` 表  
- [ ] 建单必须绑定本服务 code  
- [ ] 健康字段如何读（模拟快照）  

### 3.4 C3 Runbook

- [ ] 适用服务与触发条件  
- [ ] 现象与可观察证据（含可用 Tool：`get_service_status` / `search_tickets` / `search_knowledge`）  
- [ ] 初步判断 + **易混淆手册鉴别**  
- [ ] 分步排查：每步含动作 / 输入 / 预期结果 / 分支  
- [ ] 缓解措施及风险；标明 **Agent 不可执行、仅建议人工** 的步骤  
- [ ] 升级条件与停止条件  
- [ ] 恢复验证与后续（写 analysis 等）  
- [ ] 关联文档；无未确认数值冒充 SLA  

### 3.5 C4 事故复盘

- [ ] 文首：模拟案例声明 + 虚构标识规则（§5.2）  
- [ ] 时间线 / 影响范围  
- [ ] **已确认事实** vs **推测** 分栏  
- [ ] 根因与证据（模拟设定须标 `basis: simulated`）  
- [ ] 后续行动；关联 Runbook  
- [ ] 禁止写「请到 tickets 表查找该叙事单号」之外的误导为真单  

### 3.6 C5 工单规范

- [ ] 与 Go 状态机一致（§6.2）  
- [ ] priority 仅 `low|medium|high|urgent`（API 小写 / 库内大写）  
- [ ] analysis 最低要素；禁止 OPEN→CLOSED  
- [ ] Employee / Support 权限边界与 HITL 关系  

### 3.7 C6 分级升级

- [ ] P1–P4 定义用于值班口语与 analysis  
- [ ] 提供 **建议** 映射到 `priority`（非 API 字段）  
- [ ] Agent 可建议升级，不可批准写操作 / 不可跳过 HITL  

### 3.8 C7 安全

- [ ] 敏感信息、密钥、导出、高危人工  
- [ ] **Agent 能力对照表**（能调用的 Tool / 不能做的事）  
- [ ] 不暗示已接入真实日志平台  

### 3.9 C8 可观测边界

- [ ] V1 证据：模拟 `health_status` / `health_summary`、工单、知识 snippet  
- [ ] 明确无真实 Prometheus / 日志平台 Tool  
- [ ] analysis 推荐引用字段（如 `request_id`、时间窗）  

---

## 4. 统一元数据规范

### 4.1 存放位置

| 源类型 | 元数据位置 |
|--------|------------|
| `markdown` | 文件 YAML front matter |
| `pdf` / `docx` / `txt` | 同路径 `*.meta.yaml` sidecar + `catalog.yaml` 条目 |

`catalog.yaml` 为入库白名单真源之一；正文 front matter / sidecar 必须与 catalog **同名字段一致**（冲突以修齐为准，禁止静默以一方覆盖另一方而不改文件）。

### 4.2 必填字段（V1 ops）

| 字段 | 类型 | 说明 |
|------|------|------|
| `doc_id` | string | 稳定 ID，如 `OPS-RB-CHECKOUT-5XX`；全局唯一 |
| `title` | string | 中文标题 |
| `category` | enum | `RUNBOOK` \| `SERVICE_MANUAL` \| `INCIDENT_REPORT` \| `OPERATION_PROCESS` \| `SECURITY_GUIDELINE` |
| `source_type` | enum | `markdown` \| `pdf` \| `docx` \| `txt`（`html` 不入库） |
| `service` | enum | `CHECKOUT_API` \| `AUTH_SERVICE` \| `ORDER_WORKER` \| `PLATFORM` \| `MULTI` |
| `department` | string | 归属（如运维部 / 平台工程 / 信息安全） |
| `severity` | enum | 文档紧急度标签：`INFO` \| `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL`。**不是**工单 `priority` |
| `created_at` | date | `YYYY-MM-DD` |
| `visibility` | enum | `PUBLIC` \| `INTERNAL` |
| `status` | enum | `draft` \| `active` \| `archived`；仅 `active` 可 `v1_ingest` |
| `version` | string | 语义化版本，如 `1.0.0` |
| `source_path` | string | catalog 必填：`raw/...` |
| `canonical` | bool | catalog 必填；同源只一份 `true` |
| `v1_ingest` | bool | catalog 必填；`true` 才预留给 load |

### 4.3 K1 起强制扩展（K0 定义 schema；现网缺省时校验告警）

| 字段 | 类型 | 说明 |
|------|------|------|
| `basis` | enum / list | 见 §4.4；单值或列表 |
| `basis_notes` | string | 简述依据或 `PENDING-*` ID |
| `related_docs` | string[] | 关联 `doc_id` 列表 |
| `knowledge_role` | enum | 可选：`C1`…`C8` 或 `CROSSCUT`，便于验收 |
| `simulation_notice` | bool | 建议 `true`；复盘类必须体现模拟声明 |
| `narrative_ids` | string[] | 复盘虚构标识（如 `OPS-IR-NARR-401`） |
| `supersedes` | string | 废止的旧 `doc_id` |
| `updated_at` | date | 最后修订 |

### 4.4 `basis` 规范

| 取值 | 含义 | 允许写入的内容示例 |
|------|------|-------------------|
| `code` | 可由仓库代码/迁移/seed 证实 | ACTIVE 服务 code、健康枚举、工单状态机、priority 枚举、Tool 名单 |
| `contract` | 设计/API/Prompt/本 STANDARDS 冻结契约 | HITL、「咨询默认不建单」、analysis 板块约定 |
| `simulated` | 为 Demo/模拟运维场景补充 | 叙事依赖、复盘时间线、假设根因、演练用阈值 |

**混合依据：**

```yaml
basis: [code, simulated]
basis_notes: "服务 code 与健康枚举见 seed；依赖边与超时为模拟设定 PENDING-DEP-01"
```

规则：

- 同一段落若混合，**以最弱依据标注整段**（含 simulated 则不得标纯 `code`）。  
- 仅 `simulated` 的结论，正文须可读出「模拟设定」。  
- 待确认且未批准写入模拟的，正文不写死数值，只引用 `PENDING-*`。  

### 4.5 `doc_id` 命名

```text
OPS-{RB|SM|IR|OP|SG|GL}-<短名>
```

| 前缀 | category |
|------|----------|
| `OPS-RB-` | RUNBOOK |
| `OPS-SM-` | SERVICE_MANUAL |
| `OPS-IR-` | INCIDENT_REPORT |
| `OPS-OP-` | OPERATION_PROCESS |
| `OPS-SG-` | SECURITY_GUIDELINE |
| `OPS-GL-` | 横切（glossary/links；category 仍用 OP 或 SM） |

废止 ID 写入 `supersedes` 与 README 对照表，**不得**再 `v1_ingest: true`。

---

## 5. 模拟声明与虚构事故标识

### 5.1 模拟声明（正文）

每篇至少一处明确语句，推荐固定句式：

> 本文用于 OpsPilot **模拟运维环境**。其中标记为模拟设定的依赖、步骤、阈值与案例**不是**已验证的生产事实。

复盘类额外：

> 本文为**模拟事故复盘**，叙事标识不可在工单库中当作真实 `ticket_no` 查询。

### 5.2 虚构事故 / 叙事单号

| 规则 | 要求 |
|------|------|
| 前缀 | 使用 `OPS-IR-NARR-` 或文内声明的同等前缀；**禁止**使用 seed 真单样式冒充（如演示真单 `OPS-V1-20xx` 仅可作「对照真单机制」说明，不得写入复盘冒充事故编号） |
| 元数据 | `narrative_ids` 列出 |
| 检索边界 | 写明「不要到 tickets 表查找该号」 |
| 根因 | 默认 `basis: simulated`，除非另有 `code`/`contract` 依据 |

### 5.3 禁止冒充的表述（校验启发式 + 人工审）

- 「已对接生产 Prometheus / ELK 并完成查询」  
- 「Agent 已执行扩容 / 切备 / 回滚」  
- 将 `PENDING-*` 未决项写成已生效 SLA  
- Phase 10 权限/VPN 流程作为 V1 故障主路径依据  

---

## 6. 术语口径（与 Backend / Agent 对齐）

### 6.1 服务与健康

| 术语 | 合法取值 | 依据 |
|------|----------|------|
| 目录状态 | `ACTIVE` / `INACTIVE` | `backend/internal/model/service.go` |
| 健康 | `HEALTHY` / `DEGRADED` / `DOWN` | 同上（模拟） |
| 业务 code | `CHECKOUT_API` / `AUTH_SERVICE` / `ORDER_WORKER` | seed `000015` |
| 知识 `service` 标签 | 上列三者 + `PLATFORM` + `MULTI` | C-2 / catalog；**不是** SQL `service_id` |
| `GENERAL_IT` | INACTIVE，禁止作建单默认 | seed + 服务目录文 |

### 6.2 工单状态（知识正文必须大写枚举名或明确「API 小写」）

合法迁移（`ticket_state_machine.go`）：

```text
OPEN → ASSIGNED | IN_PROGRESS
ASSIGNED → IN_PROGRESS
IN_PROGRESS → WAITING_USER | RESOLVED
WAITING_USER → IN_PROGRESS
RESOLVED → CLOSED
CLOSED → （无出口）
```

禁止：`OPEN → CLOSED` 等未列出的跳转。

### 6.3 `priority`（工单字段）

| API / Tool（常见小写） | 存储 |
|------------------------|------|
| `low` / `medium` / `high` / `urgent` | `LOW` / `MEDIUM` / `HIGH` / `URGENT` |

- **禁止**把工单 priority 写成 `critical`（`normalizePriority` 会拒绝）。  
- 文档字段 `severity: CRITICAL` 仅表示**知识文档**紧急度标签，写入工单时映射建议为 `urgent`，并在 C6 说明。  

### 6.4 P 级 vs priority

| 概念 | 用途 |
|------|------|
| P1–P4 | 值班口语与 analysis；**不是** API 字段 |
| `priority` | 工单字段，四档上表 |

知识中提供「建议映射」时必须写「建议」，不得声称 Backend 存 P 级。

### 6.5 HITL 与写操作

- 写工具：仅 `create_ticket` / `update_ticket`，须用户确认（interrupt）。  
- 咨询类故障：默认分析，不建单。  
- Agent 不得声称已跳过确认或已批准高危变更。  

### 6.6 Agent 工具能力（知识不得扩展）

可读：`get_current_user`、`list_services`、`get_service_status`、`search_tickets`、`get_ticket`、`search_knowledge`。  
可写（HITL）：`create_ticket`、`update_ticket`。  
**不在白名单：** 日志查询、监控写、权限写、基础设施变更。

---

## 7. 跨文档引用与失效检查

### 7.1 引用方式

1. **优先**使用稳定 `doc_id`（正文反引号或链接表）。  
2. 元数据 `related_docs: [OPS-RB-..., OPS-SM-...]`。  
3. 废止 ID 只出现在 `supersedes` / README 对照，不出现在 `related_docs`。  

### 7.2 失效规则（结构校验）

| 检查 | 失败条件 |
|------|----------|
| 悬空引用 | `related_docs` 或正文中的 `OPS-XX-...` 模式指向不在 catalog 的 ID，且不在「已声明废止」列表 |
| 废止仍入库 | `status=archived` 或 README 标明废止，但仍 `v1_ingest: true` |
| 自引用环仅告警 | A↔B 允许；A→已 archived 失败 |
| 旧路径 | `source_path` 含 Phase 10 前缀或 `agent/knowledge/runbooks/` → 失败 |

正文 `OPS-[A-Z]+-[A-Z0-9-]+` 启发式扫描：未知 ID → **error**（废止表除外）。

已声明废止（维护时更新本表）：

| 废止 doc_id | 替代 |
|-------------|------|
| `OPS-RB-AUTH-FAILURES` | `OPS-RB-AUTH-FAIL` |
| `OPS-RB-TICKET-ANALYSIS` | `OPS-OP-TICKET-ANALYSIS` |

---

## 8. 维护流程（新增 / 修改 / 废弃）

### 8.1 新增

1. 确认对应**业务知识缺口**（非测试题驱动）；查 `PENDING_CONFIRMATIONS.md`。  
2. 选定用途 C1–C8 与 `category`；申请 `doc_id`。  
3. 按模板写正文；元数据含 `basis` / `related_docs`。  
4. 登记 `catalog.yaml`（`canonical: true`，按需 `v1_ingest`）。  
5. 跑 `scripts/validate_structure.py`；人工过 §3 验收清单。  
6. **另批授权**后再 `load` / `chunk` / `index`（K0 不做）。  

### 8.2 修改

1. 升高 `version` / `updated_at`。  
2. 依据变更同步 `basis_notes`；若改模拟数值 → 更新或关闭 PENDING。  
3. 检查入链/出链 `related_docs`。  
4. 再跑结构校验。  

### 8.3 废弃

1. catalog：`status: archived`，`v1_ingest: false`（或移出 documents 并记入废止表）。  
2. 替代文档填 `supersedes`。  
3. 全库消除 `related_docs` 与正文硬引用。  
4. 更新 README 对照表。  

### 8.4 禁止

- 扫描 Phase 10 路径入库  
- 无 PENDING 关闭证明把猜测写成 `basis: code`  
- 为同一主题保留矛盾的 PDF+MD 双 canonical  

---

## 9. 结构性校验要求

### 9.1 必须检查项

| # | 检查 | 期望 |
|---|------|------|
| 1 | catalog ↔ 源文件 | 每个 `v1_ingest` 条目的 `source_path` 存在；无多余强制项策略见脚本 |
| 2 | `doc_id` 唯一 | catalog 内无重复 |
| 3 | 元数据完整 | §4.2 字段齐全；枚举合法 |
| 4 | `related_docs` | 若存在则目标为 active 且可 ingest 或至少存在于 catalog |
| 5 | 服务 / 状态 / priority 口径 | `service` 枚举合法；正文禁止工单 priority=`critical`（启发式） |
| 6 | Phase 10 排除 | catalog 路径不得命中禁止前缀 |
| 7 | 工具/生产事实 | 启发式旗标（见脚本）；人工复核假阳性 |
| 8 | front matter ↔ catalog | 同 doc 关键字段一致（MD/sidecar） |

### 9.2 如何运行

在仓库根或任意目录：

```text
python knowledge/ops/scripts/validate_structure.py
```

可选：

```text
python knowledge/ops/scripts/validate_structure.py --ops-root knowledge/ops --strict-basis --strict-body
```

- 默认：缺 `basis` / `related_docs`、正文 `priority=critical`、正文提及废止 ID → **warning**（现网 33 篇 K0 预期可 PASS）。  
- `--strict-basis`：缺 `basis` → **error**（K1 起启用）。  
- `--strict-body`：工单 priority 误用 / 废止 ID 正文残留 → **error**（K1 正文清理后启用）。  
- `OPS-IR-NARR-*` 叙事号不要求出现在 catalog。  
- 退出码：存在 error → `1`；仅 warning → `0`。  

**本脚本只读**，不写 Milvus、不改 raw、不跑 embed。

---

## 10. 与入库流水线的关系

| 步骤 | K0 |
|------|-----|
| 规范与校验脚本 | ✅ 本文件 + validate |
| 批量改正文 / catalog 条目内容扩充 | ❌ |
| `load` / `chunk` / `index` | ❌ 不在本阶段执行 |
| 改 `agent/app/rag/*` | ❌ |

K1 开始正文建设时：先关/确认 PENDING → 按本规范改写 → `validate_structure.py` → 再另批入库。
