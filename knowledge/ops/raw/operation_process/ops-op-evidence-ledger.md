---
doc_id: OPS-OP-EVIDENCE-LEDGER
title: 故障证据收集与缺口记录
category: OPERATION_PROCESS
source_type: markdown
service: PLATFORM
department: 运维部
severity: INFO
created_at: 2026-10-09
updated_at: 2026-10-09
visibility: INTERNAL
status: active
version: 1.0.0
knowledge_role: C8
basis:
  - code
  - contract
basis_notes: "可调用 Tool 以 agent/app/tools 白名单为准；健康字段为模拟快照（model/service.go）；报障最低字段见 OPS-OP-INCIDENT-MINSET；禁止编造未返回的 Tool 结果（Prompt）。"
related_docs:
  - OPS-OP-INCIDENT-MINSET
  - OPS-OP-TICKET-ANALYSIS
  - OPS-OP-IMPACT-ESCALATE
  - OPS-OP-RECOVERY-VERIFY
  - OPS-SM-OBSERVABILITY
  - OPS-SG-LOG-EXPORT
  - OPS-SG-AGENT-TOOL-BOUNDARY
simulation_notice: true
---

# 故障证据收集与缺口记录

本文用于 OpsPilot **模拟运维环境**。规范 Agent 在故障分析中**记什么、缺什么、不能假装查过什么**。  
有别于 `OPS-OP-INCIDENT-MINSET`（报障最低字段）：本篇面向**调查过程台账**，不是建单前的信息清单 alone。

## 1. 使用场景

- Context Gathering 后组织「当前状态 / 知识依据 / 历史参考」时。  
- 证据不足需澄清或建议升级时。  
- 防止把常识或空命中写成公司已证实结论。

## 2. 证据分类

| 类型 | 来源 | 记录要点 |
|------|------|----------|
| 用户陈述 | 对话 | 现象、时间窗、影响面；标注「用户所述，未独立验证」 |
| 服务快照 | `get_service_status` / `list_services` | `health_status`、`health_summary`；标明**模拟快照** |
| 知识片段 | `search_knowledge` | `doc_id` / title；依据 snippet，勿把 confidence 当事实 |
| 历史工单 | `search_tickets` / `get_ticket` | 可见范围内的单号与摘要；禁编造不可见单 |
| 缺口 | 无 Tool / 无命中 / 用户未提供 | 明确写出「未查到 / 无此 Tool / 待澄清」 |

## 3. 建议台账结构（写入分析或 analysis）

每次故障分析尽量覆盖：

1. **已收集：** 上表各类非空项。  
2. **缺口：** 缺时间窗/影响面/是否 5xx；知识无命中；无日志/监控 Tool 等。  
3. **禁止声称：** 未调用的 Tool 结果；生产 Prometheus/ELK；队列深度；通道成功率。  
4. **下一步：** 向用户澄清的问题，或建议人工核查的方向（非已执行）。

## 4. 分支

### 分支 A — 证据足够组织分析

- **触发：** 服务可定位或现象可对照 Runbook；关键缺口已说明。  
- **动作：** 按 Prompt 模板回复；缺口写在「未查到」类陈述中。  
- **停止：** 不因缺口编造根因。

### 分支 B — 关键缺口阻塞判断

- **触发：** 无法区分服务/故障类型，或影响面不明。  
- **动作：** 按 `OPS-OP-INCIDENT-MINSET` / `OPS-OP-IMPACT-ESCALATE` 澄清；必要时建议升级。  
- **停止：** 不绑定错误 `service_id`，不用 `GENERAL_IT`。

### 分支 C — 工具能力外的信息

- **触发：** 用户要求「查日志 / 看队列深度 / 看通道后台」。  
- **动作：** 说明 V1 Agent **无**对应 Tool（见 `OPS-SG-AGENT-TOOL-BOUNDARY`、`OPS-SG-LOG-EXPORT`）；建议人工。  
- **停止：** 禁止假装已查询。

## 5. 与可观测文档的关系

- 字段口径：`OPS-SM-OBSERVABILITY`。  
- 日志导出：`OPS-SG-LOG-EXPORT`（V1 无真实日志平台接入）。  
- 本篇不描述监控产品操作步骤。

## 6. 关联

见 `related_docs`。
