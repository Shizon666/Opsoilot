# V1 运维知识库 — 待确认事项清单（K0）

> **用途：** 阻止把未证实内容写入 `basis: code` 或冒充生产事实。  
> **状态：** 开放（Open）项须在写入对应正文前由人工确认或明确批准为 `simulated`。  
> **规范真源：** [`STANDARDS.md`](STANDARDS.md)  

图例：`Open` = 未确认；关闭时填写确认人/日期与结论（`adopt_as_simulated` / `reject` / `promote_to_code`）。

---

## PENDING-DEP-01 — 三服务依赖顺序与超时阈值

| 项 | 内容 |
|----|------|
| 待确认内容 | `CHECKOUT_API`、`AUTH_SERVICE`、`ORDER_WORKER` 与支付通道之间的调用顺序、超时/重试阈值 |
| 影响文档 | C1/C2：`OPS-SM-SERVICE-CATALOG`、`OPS-SM-CHECKOUT`、`OPS-SM-AUTH`、`OPS-SM-ORDER-WORKER`；相关 Runbook 依赖节 |
| 缺失依据 | Backend 无服务依赖注册表；现有 SM 仅为叙事 |
| 风险 | 写成「已验证架构」会误导面试/演示；错误超时会被当成 SLA |
| 建议处理 | 人工给出**模拟依赖图**后标 `basis: simulated`；或 K1 仅写定性依赖、不写毫秒级超时 |
| 状态 | Open |

---

## PENDING-ACT-01 — 切流 / 扩容 / 杀连接 / 回滚的步骤与授权

| 项 | 内容 |
|----|------|
| 待确认内容 | 支付切备、扩容依赖、杀连接、发布回滚的具体操作步骤、执行角色与审批 |
| 影响文档 | `OPS-RB-PAY-TIMEOUT`、`OPS-RB-RELEASE-ROLLBACK`、`OPS-RB-DEP-TIMEOUT`、`OPS-OP-CHANGE-ROLLBACK` 等 |
| 缺失依据 | Agent 无对应 Tool；仓库无变更执行 API |
| 风险 | 读者以为 Agent 可执行变更；步骤若过细且无授权说明像假生产权限 |
| 建议处理 | 正文固定句式：「以下为**人工**缓解建议（模拟设定），Agent **不能**执行」；细节待确认前保持原则级 |
| 状态 | Open |

---

## PENDING-PLT-01 — 证书轮转、缓存预热、发布窗口规则

| 项 | 内容 |
|----|------|
| 待确认内容 | 证书轮转流程、缓存预热门槛、变更窗口定义与例外 |
| 影响文档 | `OPS-RB-CERT-EXPIRY`、`OPS-RB-CACHE-STAMP`、`OPS-RB-RELEASE-ROLLBACK`、`OPS-IR-CERT-ROTATION`、`OPS-IR-CACHE-WARMUP`、`OPS-IR-OFFWINDOW-RELEASE`、`OPS-OP-CHANGE-ROLLBACK` |
| 缺失依据 | 无平台组件真实配置；均为 gen_ops_kb / 叙事 |
| 风险 | 平台面过细却无业务锚点；与三服务主故事抢注意力 |
| 建议处理 | 确认「演示保留广度」后统一标 `simulated`；或 K3 合并删减弱篇 |
| 状态 | Open |

---

## PENDING-SLA-01 — 错误码、SLA、成功率门禁、恢复时间目标

| 项 | 内容 |
|----|------|
| 待确认内容 | 业务错误码表；可用性/恢复 SLA；登录成功率等发布门禁；RTO/RPO 类目标 |
| 影响文档 | 各 SM「错误码」节、升级时限（如「超过 N 分钟」）、复盘门禁表述、C6 时限 |
| 缺失依据 | `backend/**/*.go` 无 SLA/error_code 定义；现有分钟数为叙事 |
| 风险 | 简历/演示宣称生产级 SLA；与 API 行为不一致 |
| 建议处理 | **默认不写具体 SLA 表**；若演示需要时限，必须 `basis: simulated` + 本 PENDING 关闭为 `adopt_as_simulated` |
| 状态 | Open |

---

## PENDING-IR-01 — 模拟事故的根因、时间线与影响范围

| 项 | 内容 |
|----|------|
| 待确认内容 | 各 `OPS-IR-*` 的根因叙事、分钟级时间线、影响面表述是否作为**官方模拟 canon** |
| 影响文档 | 全部 `INCIDENT_REPORT`（含 PDF） |
| 缺失依据 | 非真实事故；虚构 `OPS-IR-NARR-*` |
| 风险 | 被口述成「公司真实事故」；与 seed 工单 `OPS-V1-20xx` 混淆 |
| 建议处理 | 确认后保留并强制 §5 模拟声明 + `narrative_ids`；或精简为 3 篇（每 ACTIVE 服务一篇） |
| 状态 | Open |

---

## 已可用代码/契约（勿再标 PENDING）

以下**不是**待确认项，编写时应标 `basis: code` 或 `contract`：

| 主题 | 依据位置 |
|------|----------|
| 三 ACTIVE 服务 code 与模拟健康枚举 | `migrations/000015_seed_v1_demo.up.sql`、`model/service.go` |
| 工单状态机与 priority 四档 | `ticket_state_machine.go`、`model/ticket.go`、`normalizePriority` |
| Agent 工具白名单与 HITL 写工具 | `agent/app/tools/__init__.py`、`agent_prompt.py`、`WRITE_TOOLS` |
| V1 仅索引 `knowledge/ops` | `agent/app/rag/catalog.py` `FORBIDDEN_PREFIXES` |
| 无真实日志/Prometheus Tool | Tool 列表 + `OPS-SM-OBSERVABILITY` / `OPS-SG-LOG-EXPORT` 既有表述 |

---

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-10-09 | K0 建立五类 Open PENDING |
