# OpsPilot Demo 验收清单（V1 / Phase E）

> 讲解、账号与 **从 clone 到启动** 见 [`docs/DEMO.md`](DEMO.md)。  
> 真源：[`docs/phases/PHASE_A_V1_CONTRACT.md`](phases/PHASE_A_V1_CONTRACT.md) §8。  
> 完成定义以「页面/对话中看见什么」为准；analysis / Audit / Ownership 用 API 补验。  
> **先做 P0。P0 未过不要开始 A3（知识步）。**

---

## P0 启动前检查（环境，不是产品功能）

官方路径：主 compose **只起 postgres + backend**；Milvus 用独立 compose；Agent **本机 uvicorn**。命令见 DEMO.md §1。

| # | 检查项 | 怎么做 | 看见什么才算过 |
|---|---|---|---|
| P0.1 | Backend health | `curl.exe -s http://localhost:8080/health` | 服务已响应（非连接失败） |
| P0.2 | Milvus healthz | `curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:9091/healthz` | **200** |
| P0.3 | ingest 三步 | 在 `agent/`：`load` → `chunk` → `index --allow-drop-default-collection` | load `ok=33`；index 的 `chunks`/`embedded`/`inserted`/`count` 均为 **43** |
| P0.4 | collection | 看 `index` 打印的 JSON | `"collection": "knowledge_docs"`；`milvus_uri` 为 `http://127.0.0.1:19530` |
| P0.5 | Checkout 检索 smoke | 在 `agent/`：`python -m app.rag.retriever` | `"ok": true`；`checkout_502` 的 `passed` 为 true（命中 `OPS-RB-CHECKOUT*` 或 Checkout 标题）；`weather` 为空命中 |

P0.5 失败：先对 DEMO.md §1.6（Milvus / SiliconFlow / 是否误用 compose agent / 是否跑了遗留 `app.rag.ingest`），**不要改 Tool**。

---

## 环境前提（P0 通过后）

| 项 | 要求 |
|---|---|
| Compose | `postgres` + `backend`（**不要**用容器 Agent 做官方 Demo） |
| 知识 | 独立 Milvus + P0.3～P0.5 已过 |
| LLM | 本机 Agent 进程里已有 `LLM_API_KEY` |
| Embedding | 本机进程 / `.env` 已有 `SILICONFLOW_API_KEY` |
| 前端 | `http://localhost:5173` |
| Seed | backend 已应用 **`000015_seed_v1_demo`** |
| Employee | `demo@opspilot.local` / `password123` |
| Support | `support@opspilot.local` / `password123` |

---

## A. Employee（页面）

| # | 检查项 | 怎么做 | 看见什么才算过 |
|---|---|---|---|
| A1 | Chat 入口 | 登录张明 | **直接**进入 IT Agent（`/agent/chat`），不是工单表当首页 |
| A2 | 服务状态页 | 顶栏「服务状态」 | 表里有 `CHECKOUT_API`，`health_status=DEGRADED`（只读） |
| A3 | Checkout 知识 + 调查 | Chat 发送：「下单一直 502，checkout 付不了款，帮我创建工单」 | SSE 有逐字/过程；回复引用服务异常与知识要点；可读工具包含服务状态 / `search_knowledge` / `search_tickets` 一类调查（以回复与行为为准，不要求展开 tool 时间线） |
| A4 | 历史工单边界 | 同上轮回复 | 可提张明可见的 `OPS-V1-2001`；**不得**把李华 `OPS-V1-2003` 当成张明的历史单 |
| A5 | HITL 建单 | 出现确认框后点「确认提交」 | 确认的是 `create_ticket`；绑定 Checkout（UUID/名称/code 任一可辨）；**无** `success`/`ok:true` 当主文案 |
| A6 | `ticket_no` | 确认成功后的 Chat | 看到新工单编号（正文和/或 Ticket 卡片） |
| A7 | 我的工单 | 顶栏「我的工单」 | **同一张新单**出现在列表（禁止只看气泡） |

建议话术一次带「帮我创建工单」。只说 502、不说升级时，Agent 可以只分析、不出 HITL——那是产品行为，不要当成 A5 失败；应补一句升级后再测 HITL。

---

## B. Support（页面）

| # | 检查项 | 怎么做 | 看见什么才算过 |
|---|---|---|---|
| B1 | 登录入口 | 退出后登录王运维 | 进入 **工单工作台** `/support`；无 Chat 菜单 |
| B2 | 看见双人单据 | 列表 | 有张明刚建的新单；也能看到 `OPS-V1-2003`（李华） |
| B3 | 服务状态 | 顶栏「服务状态」 | 与员工侧一样能看 DEGRADED（只读） |
| B4 | 关闭工单 | 打开张明**新单**详情，点状态按钮直到关闭 | 最终状态为 **已关闭 / closed**（常见：认领 → 处理中 → 已解决 → 关闭） |

前端列表**没有** `q=checkout` 输入框：用标题/单号辨认即可，不算 B2 失败。

---

## C. 必要 API 验证（补 UI 缺口）

Support 页不能写 `analysis`、没有 Audit 页。下列用 **Support token**（Ownership 用 **Employee token**）。`BASE=http://localhost:8080`。

建单时的 `request_id`：看 Agent SSE `start`/`done` 的 `request_id`，或响应头 `X-Request-ID`。李华单 UUID（seed）：`44444444-4444-4444-4444-444444444503`。

### C1 写入 analysis（Support PATCH）

```bash
curl -s -X PATCH "$BASE/api/v1/tickets/<新单UUID>" \
  -H "Authorization: Bearer <SUPPORT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"analysis":"Checkout 依赖超时导致收银台 502；观察 5xx 后关闭"}'
```

期望：`code=0`；再 GET 该单，`data.analysis` 含刚写入的内容。

可与状态合并（以后端状态机为准），例如同时 `"status":"in_progress"`。非法跳转应失败，不算环境偶然 PASS。

### C2 按 request_id 查 Audit（Support GET）

```bash
curl -s -G "$BASE/api/v1/audit-logs" \
  -H "Authorization: Bearer <SUPPORT_TOKEN>" \
  --data-urlencode "request_id=<建单时的 request_id>"
```

期望：`code=0`；`data.items` 非空，含该次写操作（如 `ticket.create`）。缺 `request_id` → 400；Employee 调该接口 → 403。

### C3 Ownership（张明 GET 李华单）

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>" \
  "$BASE/api/v1/tickets/44444444-4444-4444-4444-444444444503"
```

期望：HTTP **403** 或 **404**（实现二选一，Go 层统一即可）。**不得** 200 且返回李华单据。

### C4 无 JWT（回归）

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"thread_demo","message":"hi"}'
```

期望：**401**。错误 Bearer 同样 401。

---

## D. 回复体验抽查

| 检查项 | 通过标准 |
|---|---|
| 非技术话术 | 主回复不是 `success` / `ok:true` / 裸 JSON |
| 不编造单号 | 未返回的 `ticket_no` 不出现在确认文案 |
| 中文可读 | 像运维助手，不像日志 |

---

## 明确不测 / 勿当失败

| 项 | 说明 |
|---|---|
| GitLab / VPN / 权限申请 Chat | 历史 Phase；V1 Agent **不**走 Permission Tools |
| Support 页写 analysis / 搜索框 / Audit 页 | 未做 UI；用本节 C |
| 多会话历史、Multi-Agent、监控图表 | 非 V1 Demo |
| 列表里出现旧 VPN 单 | `000012` 遗留，只要新 Checkout 单也在即可 |

---

## 签字栏（可选）

| 日期 | P0 预检 | A Chat/HITL/列表 | B Support 关单 | C API | 备注 |
|---|---|---|---|---|---|
|  | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |  |
