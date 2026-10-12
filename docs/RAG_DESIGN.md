# OpsPilot RAG 设计（Phase 10 历史 + V1 运行时）

> **V1 现行口径（Hardening H4）**  
> 北极星：AI 运维故障工单助手。  
> **现网 RAG**：`search_knowledge` → SiliconFlow `BAAI/bge-m3` → Milvus `knowledge_docs`；语料 `knowledge/ops`；入库 `load` / `chunk` / `index`（见 [`DEMO.md`](DEMO.md) §1.3）。  
> Tool 名与 hit 字段仍以 [`PHASE_A_V1_CONTRACT.md`](phases/PHASE_A_V1_CONTRACT.md) §5–§6 为准。  
> Memory 不在本文：Checkpointer + `thread_id`。  
> **下文 §1 / §1.5 / §2 / §3 是 Phase 10 与早期 V1 设想，不是现网。**  
> Legacy：关键词 top-k、本地 bge-small 文件、`python -m app.rag.ingest`。  
> 非目标：知识后台、OCR 平台、工单向量、第二套生产索引。

---

## 0. 现网检索（实现后）

```text
knowledge/ops（catalog 白名单）
  ↓ python -m app.rag.load / chunk / index
  ↓ SiliconFlow BAAI/bge-m3
  ↓ Milvus knowledge_docs
  ↓ search_knowledge hits（doc_id / title / path / section / snippet / score / confidence_level）
  ↓ Agent 只依据 snippet；无命中不编造
```

工单历史走 Go `GET /tickets?q=`，不进向量库。

---

## 1. 历史：Phase 10 关键词 RAG

当时为 **Local Knowledge Retrieval MVP**（制度 8 篇 + 关键词），用于验证「知识 → Agent」闭环。

```text
Markdown（knowledge/ 固定 8 篇）
  ↓ 按 ## 切块（Chunk）
  ↓ 关键词打分（Keyword Retrieval）
  ↓ Top-k（默认 3，最大 5）+ 分数阈值过滤
  ↓ hits：doc_id / title / section / snippet / score / confidence_level
```

---

## 1.5 历史：Phase A 曾冻结的本地 bge-small

```text
Markdown Runbook
  ↓ BAAI/bge-small-zh-v1.5
  ↓ 本地向量文件 agent/data/knowledge_index/
```

该路径在 `local_store.py` **遗留**；**禁止**接回 Tool。运行时已被 C-3（§0）替代。

`confidence_level` **仅辅助匹配强弱**，不得当作事实可信度。

---

## 2. 历史：为何 Phase 10 用关键词、A 稿不上 Milvus

当时结论是：关键词冒烟、V1 先本地文件、Milvus 作后续适配器。

**H4 现行结论**：关键词与「V1 禁止 Milvus」均已过时。现网 **就是** bge-m3 + Milvus；Phase 15 仍指知识 CMS / 异构平台，不是「从零再接 Milvus」。

---

## 3. 仍然明确不做（V1）

```text
- 无 Rerank（默认）
- 无知识管理后台 / HTTP CRUD
- 无 PG knowledge_documents
- 无工单向量 / ES
```

弱匹配与无命中：谨慎引用或拒答，禁止用常识编造公司内部规则。

---

## 4. 后续演进

**V1 已落地**：§0。  
**V2+ / Phase 15**：异构源、OCR、可见性平台、知识后台——延期，不改变 `search_knowledge` 契约与 Go 业务权威。
