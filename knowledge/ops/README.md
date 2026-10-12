# OpsPilot V1 运维知识资产清单

> 真源：本 README + [`catalog.yaml`](catalog.yaml)  
> **建设规范（K0 冻结）：** [`STANDARDS.md`](STANDARDS.md)  
> **待确认模拟设定：** [`PENDING_CONFIRMATIONS.md`](PENDING_CONFIRMATIONS.md)  
> **结构校验（只读）：** `python knowledge/ops/scripts/validate_structure.py`  
> Demo 怎么跑：[`docs/DEMO.md`](../../docs/DEMO.md) §1.3  
> 分类契约：[`docs/phases/PHASE_C2_KNOWLEDGE_BASE_DESIGN.md`](../../docs/phases/PHASE_C2_KNOWLEDGE_BASE_DESIGN.md)  
> Phase 10 `knowledge/` 中文制度语料 **退出** 索引名单，文件仍留在原路径。  
> Phase 10 元数据规范**不适用于**本目录；见 [`../元数据/文档元数据规范.md`](../元数据/文档元数据规范.md)。

## 当前唯一知识链路（不要用旧 ingest）

运行时 `search_knowledge` 只检索 Milvus。仓库里的入库命令只有这三步（在 `agent/` 下执行，读仓库根 `.env`）：

```text
python -m app.rag.load     # catalog + knowledge/ops/raw → processed/documents
python -m app.rag.chunk    # → processed/chunks
python -m app.rag.index --allow-drop-default-collection
# SiliconFlow bge-m3 → Milvus knowledge_docs（默认集合受保护，须显式允许 drop）
```

对应代码：`agent/app/rag/load.py`、`chunk.py`、`index.py`。

**禁止** `python -m app.rag.ingest`（遗留本地 `embeddings.npy`，不是现网检索后端）。

`processed/` 被 gitignore，clone 后必须自己跑三步。期望：load 33 篇成功；index 写入 **43** 条 chunk。

本目录提供 **raw 资产 + catalog 白名单**。Parser / embedding / Milvus client 在 Agent 工程内，不在本 README 实现。

## 规模

| category | 篇数 | 约定 |
|----------|------|------|
| RUNBOOK | 12 | 12 |
| SERVICE_MANUAL | 6 | 6 |
| INCIDENT_REPORT | 6 | 6（MD 4 + PDF 2） |
| OPERATION_PROCESS | 5 | 5（MD 3 + DOCX 2） |
| SECURITY_GUIDELINE | 4 | 4（MD 2 + PDF 1 + DOCX 1） |
| **合计** | **33** | **33** |

格式计数：markdown=26，txt=1，pdf=3，docx=3。HTML 不入库。

## 目录

```text
knowledge/ops/
├── README.md
├── catalog.yaml
├── raw/                      # 源文件（git 跟踪）
│   ├── runbook/
│   ├── service_manual/
│   ├── incident_report/
│   ├── operation_process/
│   └── security_guideline/
└── processed/                # load/chunk 产物（gitignore；勿提交）
```

Markdown 元数据在 YAML front matter；PDF / DOCX / TXT 使用同路径 `*.meta.yaml` sidecar。

## 全量清单（V1 预入库）

| doc_id | title | category | source_type | path | service | severity | visibility | V1 ingest |
|--------|-------|----------|-------------|------|---------|----------|------------|-----------|
| `OPS-RB-CHECKOUT-5XX` | Checkout API 5xx 排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-checkout-5xx.md` | `CHECKOUT_API` | HIGH | PUBLIC | 是 |
| `OPS-RB-AUTH-FAIL` | Auth Service 登录失败与会话异常排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-auth-fail.md` | `AUTH_SERVICE` | HIGH | PUBLIC | 是 |
| `OPS-RB-WORKER-BACKLOG` | Order Worker 队列积压排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-worker-backlog.md` | `ORDER_WORKER` | HIGH | PUBLIC | 是 |
| `OPS-RB-PAY-TIMEOUT` | 支付通道超时与切备手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-pay-timeout.md` | `CHECKOUT_API` | HIGH | PUBLIC | 是 |
| `OPS-RB-DEP-TIMEOUT` | 上游依赖超时与连接池排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-dep-timeout.md` | `MULTI` | HIGH | INTERNAL | 是 |
| `OPS-RB-RELEASE-ROLLBACK` | 发布后回滚手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-release-rollback.md` | `PLATFORM` | HIGH | INTERNAL | 是 |
| `OPS-RB-CACHE-STAMP` | 缓存击穿与热点 key 排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-cache-stamp.md` | `PLATFORM` | MEDIUM | INTERNAL | 是 |
| `OPS-RB-DB-SLOW` | 慢查询导致接口超时排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-db-slow.md` | `PLATFORM` | HIGH | INTERNAL | 是 |
| `OPS-RB-MQ-LAG` | 消息积压与死信处理手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-mq-lag.md` | `ORDER_WORKER` | HIGH | INTERNAL | 是 |
| `OPS-RB-INGRESS-5XX` | 网关与入口 5xx 排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-ingress-5xx.md` | `PLATFORM` | HIGH | PUBLIC | 是 |
| `OPS-RB-CERT-EXPIRY` | 证书过期与 TLS 失败排查手册 | RUNBOOK | markdown | `raw/runbook/ops-rb-cert-expiry.md` | `PLATFORM` | CRITICAL | INTERNAL | 是 |
| `OPS-RB-ESCALATE` | 值班升级备忘 | RUNBOOK | txt | `raw/runbook/ops-rb-escalate.txt` | `PLATFORM` | MEDIUM | INTERNAL | 是 |
| `OPS-SM-CHECKOUT` | Checkout API 服务说明 | SERVICE_MANUAL | markdown | `raw/service_manual/ops-sm-checkout.md` | `CHECKOUT_API` | INFO | PUBLIC | 是 |
| `OPS-SM-AUTH` | Auth Service 服务说明 | SERVICE_MANUAL | markdown | `raw/service_manual/ops-sm-auth.md` | `AUTH_SERVICE` | INFO | PUBLIC | 是 |
| `OPS-SM-ORDER-WORKER` | Order Worker 服务说明 | SERVICE_MANUAL | markdown | `raw/service_manual/ops-sm-order-worker.md` | `ORDER_WORKER` | INFO | PUBLIC | 是 |
| `OPS-SM-INGRESS` | 平台入口与网关说明 | SERVICE_MANUAL | markdown | `raw/service_manual/ops-sm-ingress.md` | `PLATFORM` | INFO | INTERNAL | 是 |
| `OPS-SM-OBSERVABILITY` | 可观测性约定 | SERVICE_MANUAL | markdown | `raw/service_manual/ops-sm-observability.md` | `PLATFORM` | INFO | INTERNAL | 是 |
| `OPS-SM-SERVICE-CATALOG` | 运维视角服务目录 | SERVICE_MANUAL | markdown | `raw/service_manual/ops-sm-service-catalog.md` | `PLATFORM` | INFO | PUBLIC | 是 |
| `OPS-IR-CHECKOUT-GW-TIMEOUT` | 支付网关超时导致 Checkout 大面积 502 复盘 | INCIDENT_REPORT | pdf | `raw/incident_report/ops-ir-checkout-gw-timeout.pdf` | `CHECKOUT_API` | HIGH | INTERNAL | 是 |
| `OPS-IR-AUTH-CONFIG` | 配置错误导致 Auth 全员登录失败复盘 | INCIDENT_REPORT | markdown | `raw/incident_report/ops-ir-auth-config.md` | `AUTH_SERVICE` | CRITICAL | INTERNAL | 是 |
| `OPS-IR-WORKER-CONCURRENCY` | Worker 并发参数误改导致积压复盘 | INCIDENT_REPORT | markdown | `raw/incident_report/ops-ir-worker-concurrency.md` | `ORDER_WORKER` | HIGH | INTERNAL | 是 |
| `OPS-IR-OFFWINDOW-RELEASE` | 变更窗口外发布引发回滚复盘 | INCIDENT_REPORT | markdown | `raw/incident_report/ops-ir-offwindow-release.md` | `PLATFORM` | HIGH | INTERNAL | 是 |
| `OPS-IR-CACHE-WARMUP` | 缓存预热不足导致早高峰击穿复盘 | INCIDENT_REPORT | markdown | `raw/incident_report/ops-ir-cache-warmup.md` | `PLATFORM` | MEDIUM | INTERNAL | 是 |
| `OPS-IR-CERT-ROTATION` | 证书轮转遗漏导致 TLS 失败复盘 | INCIDENT_REPORT | pdf | `raw/incident_report/ops-ir-cert-rotation.pdf` | `PLATFORM` | CRITICAL | INTERNAL | 是 |
| `OPS-OP-TICKET-ANALYSIS` | 故障工单 analysis 撰写规范 | OPERATION_PROCESS | markdown | `raw/operation_process/ops-op-ticket-analysis.md` | `PLATFORM` | INFO | INTERNAL | 是 |
| `OPS-OP-INCIDENT-MINSET` | 报障信息最低集 | OPERATION_PROCESS | markdown | `raw/operation_process/ops-op-incident-minset.md` | `PLATFORM` | INFO | PUBLIC | 是 |
| `OPS-OP-DUTY-P-LEVEL` | 值班升级与 P 级定义 | OPERATION_PROCESS | markdown | `raw/operation_process/ops-op-duty-p-level.md` | `PLATFORM` | MEDIUM | INTERNAL | 是 |
| `OPS-OP-CHANGE-ROLLBACK` | 变更与回滚检查单 | OPERATION_PROCESS | docx | `raw/operation_process/ops-op-change-rollback.docx` | `PLATFORM` | MEDIUM | INTERNAL | 是 |
| `OPS-OP-COMMS-TONE` | 故障沟通口径 | OPERATION_PROCESS | docx | `raw/operation_process/ops-op-comms-tone.docx` | `PLATFORM` | INFO | INTERNAL | 是 |
| `OPS-SG-PII-TICKET` | 工单与 Chat 中的敏感信息处理 | SECURITY_GUIDELINE | markdown | `raw/security_guideline/ops-sg-pii-ticket.md` | `PLATFORM` | HIGH | PUBLIC | 是 |
| `OPS-SG-LOG-EXPORT` | 生产日志查询与导出边界 | SECURITY_GUIDELINE | markdown | `raw/security_guideline/ops-sg-log-export.md` | `PLATFORM` | HIGH | INTERNAL | 是 |
| `OPS-SG-SECRETS` | 密钥、证书与连接串禁止事项 | SECURITY_GUIDELINE | pdf | `raw/security_guideline/ops-sg-secrets.pdf` | `PLATFORM` | CRITICAL | INTERNAL | 是 |
| `OPS-SG-HIGH-RISK` | 高危操作必须人工 | SECURITY_GUIDELINE | docx | `raw/security_guideline/ops-sg-high-risk.docx` | `PLATFORM` | CRITICAL | INTERNAL | 是 |

全部 `status=active` 且 `canonical=true`。`load.py` 只扫本清单且 `v1_ingest=true`，**禁止**扫描 `knowledge/VPN与远程办公/` 等 Phase 10 路径。

## 与已有 Runbook 子集

早期文件仍留在 `agent/knowledge/runbooks/`，避免本批改 Agent 扫描根。canonical 正文以本目录为准：

| 旧路径 | 旧 doc_id | canonical |
|--------|-----------|-----------|
| `agent/knowledge/runbooks/checkout-5xx.md` | `OPS-RB-CHECKOUT-5XX` | `OPS-RB-CHECKOUT-5XX` |
| `agent/knowledge/runbooks/auth-failures.md` | `OPS-RB-AUTH-FAILURES` | **`OPS-RB-AUTH-FAIL`** |
| `agent/knowledge/runbooks/order-worker-backlog.md` | `OPS-RB-WORKER-BACKLOG` | `OPS-RB-WORKER-BACKLOG` |
| `agent/knowledge/runbooks/ticket-analysis-guide.md` | `OPS-RB-TICKET-ANALYSIS` | **`OPS-OP-TICKET-ANALYSIS`**（分类改为 OPERATION_PROCESS） |

## 编写约定

完整规范见 [`STANDARDS.md`](STANDARDS.md)。摘要：

- 必填元数据：`doc_id` / `title` / `category` / `source_type` / `service` / `department` / `severity` / `created_at` / `visibility` / `status` / `version`（catalog 另需 `source_path` / `canonical` / `v1_ingest`）
- K1 起强制：`basis`（`code` \| `contract` \| `simulated`）、`related_docs`；未确认项见 [`PENDING_CONFIRMATIONS.md`](PENDING_CONFIRMATIONS.md)
- `service` 仅用 `CHECKOUT_API` / `AUTH_SERVICE` / `ORDER_WORKER` / `PLATFORM` / `MULTI`
- 工单 `priority` 仅 `low|medium|high|urgent`；文档 `severity: CRITICAL` ≠ 工单 priority
- Runbook（C3）必须含：触发条件 / 现象与证据 / 鉴别 / 分步（输入·预期·分支）/ 缓解与 Agent 不可执行声明 / 升级与恢复验证
- 复盘必须标模拟；虚构叙事号用 `OPS-IR-NARR-*`，Agent 查真单仍走 `search_tickets`
- 同源只保留一份 canonical；禁止 PDF 与 MD 双份矛盾正文同时可检索
- 不把工单全文或服务健康快照当知识资产；入库只走上面的 load / chunk / index
- **K0 不批量改写正文、不跑 index**；先过结构校验与人工确认 PENDING