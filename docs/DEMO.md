# OpsPilot Demo 指南

> **首次运行**：按下面 **§1 从 clone 到启动**，再打 [`DEMO_CHECKLIST.md`](DEMO_CHECKLIST.md)（先 P0 预检，再 A/B/C）。  
> **V1 手测真源**：[`docs/phases/PHASE_A_V1_CONTRACT.md`](phases/PHASE_A_V1_CONTRACT.md) §8。  
> 本页按现网代码写：**Checkout 故障 → Agent 调查 → HITL 建单 → Support 关单**。  
> Permission / VPN / GitLab 属于历史 Phase 能力，**不是**本 Demo 主路径。

---

## Demo 目标

用 5～8 分钟讲清：

```text
员工用自然语言报 Checkout 502
  → Chat（默认入口）SSE 流式回复
  → Agent 调 Tool：服务状态 + 知识 RAG + 历史工单
  → 用户确认 HITL 后 create_ticket 落库
  → 「我的工单」能看到 ticket_no
  → Support 在工作台推进并关闭
```

强调：**Agent 是入口与编排；Go Backend 是鉴权、状态机、Ownership、Audit 的权威。**

---

## 用户故事（V1）

| 角色 | 故事 | Demo 口径 |
|---|---|---|
| 员工（张明） | 收银台下单 502 / 付不了款 | 登录后**直接进 Chat**；Agent 查 CHECKOUT_API、Runbook、可见历史单 `OPS-V1-2001` |
| 员工 | 要升级成故障单 | 明确说「帮我建单/升级处理」→ HITL 确认 → 绑定 `CHECKOUT_API` |
| 员工 | 确认单据进系统 | 打开「我的工单」，不只看 Chat 气泡 |
| IT Support（王运维） | 处理现场单并关掉 | 工作台看到张明新单；也能看到李华历史单 `OPS-V1-2003`；UI 关到 CLOSED |
| 安全边界 | 张明不能看李华的单 | curl GET 李华单 → `40301` 或 `40401` |

咨询阶段默认**不建单**。要落库必须用户明确要求升级。

---

## 技术链路（现网）

```text
React 登录 → JWT
  → 默认路由 /agent/chat
  → POST /agent/chat/stream（SSE：token / confirmation / done）
  → LangGraph ReAct + HITL
       ├─ list_services / get_service_status
       ├─ search_knowledge（`knowledge/ops` / Milvus）
       ├─ search_tickets / get_ticket
       └─ create_ticket（写，必须 HITL）
  → Go /api/v1/*（JWT 透传）→ PostgreSQL
  → 前端气泡 + Ticket 卡片；确认按钮走 POST /agent/chat/resume
```

安全要点：业务路径无 Agent 系统账号后门；Tool 不接受冒充 `user_id`；Go 二次鉴权与 Ownership。

---

## 1. 从 clone 到启动（V1 Demo 官方路径）

第三方按本节做。打勾前先跑 [`DEMO_CHECKLIST.md`](DEMO_CHECKLIST.md) **P0 预检**。  
**不要**把主 compose 里的 `agent` 容器当作官方 Demo Agent（它与独立 Milvus 不在同一网络，容器内 `127.0.0.1:19530` 不是宿主机上的 Milvus）。

需要：Docker、Python 3.11+、Node 18+、可访问外网（LLM + SiliconFlow embedding）。Windows 可用 PowerShell；`curl` 若指向别名，改用 `curl.exe`。

### 1.1 配置 `.env`

在仓库根：

```text
cp .env.example .env
```

**必须填写（留空则 Demo 知识步或 Chat 失败，无 mock）：**

| 变量 | 用途 |
|---|---|
| `LLM_API_KEY` | Agent 对话 |
| `SILICONFLOW_API_KEY` | ingest 写向量 **以及** 运行时 query embedding |

保持 `JWT_SECRET` 与示例一致（或自己改一处，Go 与本机 Agent **必须相同**）。  
`MILVUS_URI` 保持 `http://127.0.0.1:19530`。  
不要提交 `.env`。

### 1.2 两套 Compose（顺序固定）

**第一套**（业务库 + Go）。只起 postgres 与 backend，让 entrypoint 跑完全部 `*.up.sql`（含 `000015_seed_v1_demo`）：

```text
docker compose up -d --build postgres backend
```

等到 `http://localhost:8080/health` 可用。若误把 `agent` 也起了：`docker compose stop agent`，避免占用 8000。

**第二套**（Milvus，独立项目，不加入主 compose 网络）：

```text
docker compose -f docker-compose.milvus.yml up -d
```

首次启动 healthcheck `start_period` 约 90s。等到：

```text
curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:9091/healthz
```

期望 **200**。过早跑 index 会连不上。

### 1.3 知识入库三步（唯一链路）

`processed/` 被 gitignore，clone 后必须自己跑。在 **`agent/`** 目录（会读仓库根 `.env`）：

```text
cd agent
python -m app.rag.load
python -m app.rag.chunk
python -m app.rag.index --allow-drop-default-collection
```

> 默认集合 `knowledge_docs` 受保护：`index` 会 drop 重建，必须显式 `--allow-drop-default-collection`。  
> 隔离语料请用 `MILVUS_COLLECTION=knowledge_docs_dayi`（或 `--collection`），**不要**对默认集合重建。

| 步 | 期望 |
|---|---|
| `load` | `ok=33`，`failed`/`skipped` 为空 |
| `chunk` | `documents=33`，`chunks>=33` |
| `index` | `chunks` / `embedded` / `inserted` / `count` 均为 **43**；`collection=knowledge_docs` |

**禁止** `python -m app.rag.ingest`（遗留本地 npy，不是现网 `search_knowledge`）。

### 1.4 本机启动 Agent

把 compose 主机名换成 localhost，再起 FastAPI（仓库根 `.env` 的 LLM/JWT/SiliconFlow 需进入进程环境；RAG 检索还会再读根目录 `.env`）：

```powershell
# 在仓库根；按你的 .env 填写两把 key
$env:JWT_SECRET = "change-me-in-local-dev"
$env:LLM_API_KEY = "<你的 LLM key>"
$env:SILICONFLOW_API_KEY = "<你的 SiliconFlow key>"
$env:BUSINESS_API_BASE_URL = "http://localhost:8080"
$env:CHECKPOINT_BACKEND = "postgres"
$env:CHECKPOINT_DATABASE_URL = "postgres://opspilot:opspilot@localhost:5432/opspilot_agent?sslmode=disable"
cd agent
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

依赖：`cd agent && pip install -r requirements.txt`（首次）。  
探针：`http://localhost:8000/internal/health` 应含 `"service":"agent"`。

### 1.5 前端

```text
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173/login`。Vite 会把 `/api` 转到 8080、`/agent` 转到 8000。

### 1.6 常见失败（先对表，再改 Agent）

| 现象 | 先查 |
|---|---|
| Chat 503 / 不走 Tool | `LLM_API_KEY` 未进 Agent 进程 |
| 登录 401、Chat 401 | Go 与 Agent `JWT_SECRET` 不一致 |
| Agent 连不上工单 API | 本机 Agent 仍用 `BUSINESS_API_BASE_URL=http://backend:8080` |
| Checkpoint / 多轮丢失 | `CHECKPOINT_DATABASE_URL` 仍指向主机名 `postgres` 而不是 `localhost` |
| 知识「暂无命中」 | Milvus 未 healthy；未跑完 load/chunk/index；缺 `SILICONFLOW_API_KEY`；用了 compose `agent` 容器 |
| `index` 立刻失败 | Milvus 还在启动；或误跑了 `app.rag.ingest` |
| 8000 端口占用 | 停掉 compose `agent` |
| 列表里有 VPN 旧单 | `000012` 噪音，不是启动失败 |

未 ingest / 未起 Milvus 时，checklist A3 知识步记 **环境 ❌**，不要改 Tool 凑 PASS。

---

## 2. 账号与预制数据（000015）

| 角色 | 登录标识 | 密码 | 说明 |
|---|---|---|---|
| Employee | `demo@opspilot.local` | `password123` | 张明 / 研发部；**本 Demo 登录主角** |
| IT Support | `support@opspilot.local` | `password123` | 王运维；第二角色 |
| 夹具 | `lihua@opspilot.local` | `password123` | 李华；**不要**作为演示登录 |

| 服务 `code` | health_status | 说明 |
|---|---|---|
| `CHECKOUT_API` | `DEGRADED` | 主故事；摘要含 5xx / 支付超时 |
| `AUTH_SERVICE` | `HEALTHY` | 对照 |
| `ORDER_WORKER` | `DOWN` | 对照，不要误绑成主单服务 |
| `GENERAL_IT` | （目录 **INACTIVE**） | **禁止**当建单默认 |

| ticket_no | 请求人 | 服务 | status | Demo 用途 |
|---|---|---|---|---|
| `OPS-V1-2001` | 张明 | CHECKOUT_API | RESOLVED | Agent 历史参考（可见） |
| `OPS-V1-2002` | 张明 | AUTH_SERVICE | CLOSED | 噪声单 |
| `OPS-V1-2003` | 李华 | CHECKOUT_API | RESOLVED | 王运维可见；**张明不可见** |

主路径 **OPEN Checkout 单由 Chat 现场创建**，不预置。

库中可能仍有历史 `000012` 的 VPN / 会议设备单。列表里看到了只说明旧 seed 还在，**不要当本 Demo 主故事**。

顶栏「服务状态」(`/services`) 应能看见 CHECKOUT `DEGRADED`（只读，不必在 Demo 里 PATCH 健康）。

---

## 3. Demo 流程（对齐契约 §8）

```text
1. CHECKOUT_API 已是 DEGRADED（seed）；或事先 Support PATCH 健康（本 Demo 不依赖 UI 改健康）

2. 打开 http://localhost:5173/login
   demo@opspilot.local / password123
   期望：登录后直接进入 /agent/chat（不必再找工单列表当首页）

3. 输入（建议一次说清升级意图）：
   「下单一直 502，checkout 付不了款，帮我创建工单」

4. 只读调查（SSE 过程可见 token）：
   服务状态（CHECKOUT DEGRADED）
   知识（Checkout 5xx Runbook）
   历史工单（张明可见 OPS-V1-2001；不得把 OPS-V1-2003 当自己的历史）

5. HITL：出现确认框 →「确认提交」
   create_ticket.service_id = CHECKOUT_API
   Chat 中看到新 ticket_no（气泡和/或 Ticket 卡片）

6. 顶栏「我的工单」刷新后也能看到同一张新单（禁止只看 Chat）

7. 退出。support@opspilot.local 登录 → /support
   工作台看到张明新单；列表里也能看到李华 OPS-V1-2003
   （前端无 q= 搜索框：翻页/标题识别即可）

8. 打开张明新单，按工作台按钮推进到 CLOSED
   （UI 常见路径：认领 → 开始处理 → 标记解决 → 关闭）
   写入 analysis、按 X-Request-ID 查 Audit：见 DEMO_CHECKLIST 的 API 步

9. 用张明 token GET 李华工单 UUID → 拒绝（40301 或 40401）
```

不要演示：申请 GitLab、查询权限申请、把 VPN 单当主路径。

---

## 4. 系统边界

| 层 | 负责 | 不负责 |
|---|---|---|
| **Agent** | 意图、追问、ReAct Tool、SSE、HITL 文案 | 最终鉴权、状态机、Ownership、Audit 权威 |
| **Go Backend** | JWT、Ownership、Ticket 状态机、`analysis`、Audit 读/写 | 自然语言理解 |
| **Knowledge** | 只读 Runbook 片段 | 代替 `get_service_status` / `search_tickets`；宣称已修复 |
| **Frontend** | Chat 第一入口、SSE 气泡、HITL 按钮、工单列表、服务状态只读页 | 监控大盘；analysis/Audit 表单（现网用手测 API） |

```text
Agent = 入口与编排
Backend = 权限 / 状态机 / Ownership / Audit
```

---

## 5. 当前限制（V1 Demo）

| 项 | 说明 |
|---|---|
| Support UI | 可改状态关单；**不能**在页面里写 `analysis`、不能按 `q` 搜、无 Audit 页 |
| Chat 卡片 | 建单结果可出 Ticket 卡；历史检索结果主要靠回复正文 |
| 会话 | 同一标签刷新复用 `sessionStorage.opspilot_thread_id`；气泡不持久（无历史库）；新标签新 thread；登录/退出会清 key |
| 列表噪音 | 可能混有 Phase 9.1 VPN 旧单 |
| 评测 | 自动化 eval 不是本 Demo 交付物 |

**本 Demo 明确不做：** Multi-Agent / MCP、新 Tool、新业务 API、知识库 2.0、用户画像、实时监控图表。

---

## 6. 历史 Phase 能力（降级，勿当 V1 主路径）

下列曾在 Phase 9.1 演示，**现网 Agent 白名单已不含 Permission Tools**；VPN 故事已被 Checkout 替换：

- 「回家 VPN 连不上」/ `OPS-DEMO-1001`
- 「我的权限申请有哪些」/ 申请 GitLab Developer
- 关键词 RAG + 制度 8 篇作为主知识源
- 登录后先进入工单列表再找 Chat

需要对照旧 HTTP 工单+权限闭环时，仓库里仍有历史脚本 `scripts/demo_phase7.ps1`，**不是 V1 Demo，本页不引用为验收。**
