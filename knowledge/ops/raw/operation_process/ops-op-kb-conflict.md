---
doc_id: OPS-OP-KB-CONFLICT
title: 知识冲突过期与选用规则
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: INFO
created_at: 2026-10-10
updated_at: 2026-10-10
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: CROSSCUT
basis:
  - contract
basis_notes: "选用规则对齐 STANDARDS 与 catalog canonical；Agent 仅 search_knowledge；废止 ID 见 STANDARDS；不自动改知识库。"
related_docs:
  - OPS-SM-SERVICE-CATALOG
  - OPS-OP-EVIDENCE-LEDGER
  - OPS-OP-DIAGNOSIS-STOP
  - OPS-SG-AGENT-TOOL-BOUNDARY
simulation_notice: true
---

# 知识冲突过期与选用规则

本文供 Agent 在 `search_knowledge` **命中多篇或疑似矛盾**时，决定如何引用、如何声明不确定，而不是随机拼接。

## 1. 独立价值

STANDARDS 写给人维护；本篇写给 **运行时选用**，进入可检索知识库。

## 2. 选用优先级（建议）

1. `status=active` 且 catalog `canonical` 的 V1 ops 文档  
2. 与当前服务/现象匹配的专用 Runbook 优先于宽泛 PLATFORM 文  
3. OPERATION_PROCESS / SECURITY 约束类优先于案例 IR 的根因叙事  
4. 模拟 IR 仅作案例，且必须标明非现状  
5. 废止 ID（如旧 AUTH-FAILURES）不得当现行依据  

## 3. 冲突处理分支

### A — 表面冲突实为场景不同

说明适用边界（例：入口 5xx vs 通道超时）；两篇都可引用并写清条件。

### B — 真冲突或版本不明

列出 `doc_id` 与分歧点；**不选边编造**；建议人工维护知识；对用户给保守结论（`OPS-OP-DIAGNOSIS-STOP`）。

### C — 命中过时口吻（如把文档 severity 误当成工单 priority）

以 Backend 合法工单 priority 枚举为准（`low|medium|high|urgent`），回答中只使用上述四档；可注明旧知识原文可能混用了文档紧急度标签。

## 4. 禁止

把 Phase 10 制度当 V1 故障主依据；静默合并矛盾根因；声称已更新知识库。

## 5. 关联

维护流程仍以仓库 `STANDARDS.md` 为准（非本检索集完整替代）。
