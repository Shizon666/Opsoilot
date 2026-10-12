# OpsPilot

企业内部 **AI 运维故障工单助手**（V1）。

| | 现行口径 |
|---|---|
| 北极星 | AI 运维故障工单助手 |
| RAG | SiliconFlow `BAAI/bge-m3` + Milvus `knowledge_docs`（`search_knowledge`） |
| Memory | LangGraph Checkpointer + `thread_id` |
| 主链 | Ticket / 服务健康 / Audit / HITL |
| Legacy | Permission / AccessRequest / Approval；本地 bge-small / 关键词 RAG（**不是实现目标**） |

**唯一 Demo 路径：[`docs/DEMO.md`](docs/DEMO.md) §1**（clone → 两套 Compose → `load`/`chunk`/`index` → 本机 Agent → Vite）。验收：[`docs/DEMO_CHECKLIST.md`](docs/DEMO_CHECKLIST.md)（先 P0）。

契约：[`docs/phases/PHASE_A_V1_CONTRACT.md`](docs/phases/PHASE_A_V1_CONTRACT.md)。路线：[`ROADMAP.md`](ROADMAP.md)。AI 开工：[`AI_CONTEXT.md`](AI_CONTEXT.md)。
