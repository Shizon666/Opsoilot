# 北京小小医信息科技有限公司 — 内部 IT 知识库

> **C-2 V1 运维知识资产**（33 篇清单与 raw 样本）在 [`ops/README.md`](ops/README.md)，**不**把本目录 Phase 10 制度扫进 C-2。  
>
> **V1（Phase C）**：检索集改为运维 Runbook（路径见 Phase A 契约 §6）；本清单的 8 篇制度语料**保留文件，退出 V1 索引**。  
> 本 Phase A **不创建** `knowledge/runbooks/` 正文。当前代码仍只索引下表 8 篇（关键词）。
>
> OpsPilot 知识资产。目标：模拟信息技术部**最小真实知识库**，支撑 Agent 判断 `answer` / `ticket` / `permission` / `human`。  
> **不是** Demo FAQ 注水文库。  
> 程序消费以 YAML front matter 英文字段为准；路径以本 README 为权威清单（**直至 Phase C 切换名单**）。

## Phase 10 第一批 RAG 语料（Employee，`search_knowledge` 仅索引下列 8 篇）

| 路径 | doc_id | 状态 |
|------|--------|------|
| `服务目录/IT服务目录与入口指引.md` | XXY-IT-CAT-001 | active |
| `制度规范/IT服务请求工单规范.md` | XXY-IT-POL-TKT-001 | active |
| `制度规范/信息系统访问与权限管理规范.md` | XXY-IT-POL-ACL-001 | active |
| `权限管理/GitLab权限申请指南.md` | XXY-IT-ACC-GL-001 | active |
| `VPN与远程办公/VPN与远程办公接入指南.md` | XXY-IT-HOW-VPN-001 | active |
| `办公与直播设备/办公与直播设备报修指引.md` | XXY-IT-HOW-EQP-001 | active |
| `软件安装/标准软件安装与例外申请指南.md` | XXY-IT-HOW-SW-001 | active |
| `账号登录/账号与登录处理指南.md` | XXY-IT-HOW-ACC-001 | active |

> 其余 knowledge 文档本阶段**不入库**。检索实现：Agent 进程内关键词 top-k（无 Milvus / 无 rerank）。

## 资产总表

### 既有（保留，未删未迁）

| 路径 | category | visibility | related_intent | Employee RAG | 状态 |
|------|----------|------------|----------------|--------------|------|
| `服务目录/IT服务目录与入口指引.md` | catalog | PUBLIC | answer, ticket, permission, human | 是 | active |
| `制度规范/IT服务请求工单规范.md` | policies | PUBLIC | ticket, answer | 是 | active |
| `制度规范/信息系统访问与权限管理规范.md` | policies | PUBLIC | permission, human, answer | 是 | active |
| `权限管理/GitLab权限申请指南.md` | access | PUBLIC | permission, answer, human | 是 | active |
| `权限管理/数据库访问权限申请指南.md` | access | PUBLIC | permission, human, answer | 是 | outline |
| `权限管理/开发环境权限申请指南.md` | access | PUBLIC | permission, answer | 是 | outline |
| `常见问题/常见IT问题处理指南.md` | howto | PUBLIC | answer, ticket, human | 是 | outline（过渡索引，专篇优先） |
| `作业手册/IT-Support内部处理规范.md` | runbooks | INTERNAL | human, ticket, permission | **否** | outline |
| `权限管理/权限与审批关系矩阵.xlsx` | access | INTERNAL | permission, human | **否** | outline（非 RAG 主数据） |

旁路元数据：`权限管理/权限与审批关系矩阵.meta.yaml`  
`README.md` 本身不入 RAG。

### 员工高频自助域

| 路径 | category | visibility | related_intent | Employee RAG | 状态 |
|------|----------|------------|----------------|--------------|------|
| `账号登录/账号与登录处理指南.md` | howto | PUBLIC | answer, ticket, human | 是 | active（Phase 10 语料） |
| `VPN与远程办公/VPN与远程办公接入指南.md` | howto | PUBLIC | answer, ticket, human | 是 | active（Phase 10 语料） |
| `办公与直播设备/办公与直播设备报修指引.md` | howto | PUBLIC | answer, ticket, human | 是 | active（Phase 10 语料） |
| `软件安装/标准软件安装与例外申请指南.md` | howto | PUBLIC | answer, ticket, human | 是 | active（Phase 10 语料） |
| `数据安全/数据安全与敏感信息处理须知.md` | policies | PUBLIC | answer, ticket, permission, human | 是 | outline（**未**入 Phase 10 语料） |

> Phase 10 语料见上文 8 篇表。数据安全 / DB / DEV_ENV / Support 手册等本阶段不检索。

## 目录映射（category → 中文目录）

| category（英，front matter） | 知识库目录 |
|------------------------------|------------|
| `catalog` | `knowledge/服务目录/` |
| `policies` | `knowledge/制度规范/`、`knowledge/数据安全/` |
| `access` | `knowledge/权限管理/` |
| `howto` | `knowledge/常见问题/`、`knowledge/账号登录/`、`knowledge/VPN与远程办公/`、`knowledge/办公与直播设备/`、`knowledge/软件安装/` |
| `runbooks` | `knowledge/作业手册/` |
| （规范文档，非业务 category） | `knowledge/元数据/` |

> 入库扫描：遍历 `knowledge/**/*.md` 读 front matter；**不要**写死单一中文子目录。以 `doc_id` + `rag.*` 为准。

## 与 V0 业务闭环

```text
Employee 咨询
    ├─ 服务目录（总路由）
    ├─ 工单规范 + 账号/VPN/设备/软件（自助与建单）
    ├─ 权限总规 + 三份 access 指南（Permission）
    ├─ 数据安全须知（底线 / 事件升级）
    └─ Support 作业手册（INTERNAL，仅 Support RAG）
         ↓
Ticket / Permission → Approval → Audit
```

## 元数据规范

见 [`元数据/文档元数据规范.md`](元数据/文档元数据规范.md)。  
所有业务 Markdown 必须使用 **英文字段名** 的 YAML front matter；缺字段视为未就绪。

## 编写约定（正文阶段生效）

- 语气：企业内部正式通知 / 制度口径
- 必备章节：适用范围、**意图判断表**、流程、限制条件、示例问题（含预期意图）
- 禁止：虚假法律合规、技术教程堆砌、无判断价值的 FAQ 注水
- PDF/DOCX 正式发布版：后置
- 稳定标识优先用 `doc_id`，勿依赖文件名
