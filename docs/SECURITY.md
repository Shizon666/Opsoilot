# SECURITY — OpsPilot MVP 安全设计

> 文档版本：v1.0  
> 项目名称：OpsPilot — AI 运维故障工单助手  
> 文档状态：MVP Security Design（V1 仍适用）  
> **V1**：Permission 为 Legacy，不是主链攻击面扩展对象。HITL 写确认保持。工单 Ownership：Employee 仅自己的单。  
> 约束：V1 HTTP 差集以 Phase A 契约为准；本文原则（JWT / 二次鉴权 / HITL≠Approval）不因产品收敛而放松。

---

# 1. Security Goals

MVP 安全目标是保护真实业务对象与 Agent 可控边界，而不是堆砌通用安全清单。

重点保护：

```text
用户身份
工单数据
权限申请
Agent Tool
多轮会话数据
```

核心原则：

```text
前端权限控制 ≠ 安全边界
LLM / Prompt ≠ 业务授权
Agent Tool Call ≠ 已授权执行
Go Service = 最终业务授权边界
```

---

# 2. Authentication

## 2.1 JWT

用户登录后由 Go Business API 签发 JWT。

后续受保护接口统一使用：

```text
Authorization: Bearer <JWT>
```

## 2.2 双端校验

| 服务 | 是否校验 JWT | 作用 |
|---|---|---|
| Go Business API | 是 | 业务接口认证；最终授权依据 |
| FastAPI Agent | 是 | Agent 对话接口认证；解析当前用户 |

说明：

- FastAPI Agent 与 Go Business API **都**校验 JWT
- `user_id` 必须从可信 JWT 中获取，不能信任客户端 body / query 自行传入的身份字段
- Agent 调用 Go 时携带当前用户认证上下文；Go 再次独立鉴权

---

# 3. Authorization

## 3.1 角色

MVP 角色：

```text
employee
it_support
admin
```

采用 RBAC：角色决定能力范围，再叠加资源归属与字段权限。

## 3.2 授权维度

| 维度 | 含义 | 示例 |
|---|---|---|
| RBAC | 角色能否做某类操作 | `employee` 不能审批 |
| Resource Ownership | 资源是否属于当前用户或其处理范围 | 员工只能看自己的工单 |
| Field-level Permission | 同一接口下不同角色可写字段不同 | 工单 PATCH：员工不可改 `status` / `assignee_id` |

## 3.3 最终边界

> **Service 层是最终业务授权边界。**

Frontend 的按钮隐藏、路由守卫、表单禁用只能改善体验，**不能作为安全边界**。

即使请求来自：

```text
React 页面
Agent Tool
内部脚本
```

Go Service 仍必须独立完成：

```text
认证上下文解析
RBAC
资源归属
字段级权限
业务规则 / 状态机校验
```

---

# 4. Agent Security

## 4.1 Prompt Injection

不要假设 Prompt 能“完全防住” Prompt Injection。

MVP 采用分层约束：

```text
System Prompt / Tool constraints
        ↓
Tool 参数校验
        ↓
Agent 不直接访问数据库
        ↓
Go Business API 最终鉴权
        ↓
敏感操作 HITL
```

即使 Agent 被诱导产生非法 Tool Call，也不能绕过 Go Service 的业务权限。

```text
LLM 判断 ≠ 业务权限
Tool 被调用 ≠ 操作已授权
```

## 4.2 Tool Security

| 控制点 | MVP 要求 |
|---|---|
| 参数校验 | Tool Schema + Go 侧最终参数校验 |
| Timeout | Tool 调用设置超时，避免长时间挂起 |
| Failure handling | 超时 / 异常 / 越权必须明确返回失败，禁止伪造成功 |
| HITL | 敏感操作进入人工确认后再执行 |
| Allowlist | 仅暴露当前任务真正需要的 Tool |

Agent **不得**直接访问 PostgreSQL。业务读写统一走：

```text
Tool → Business Client → Go Business API → Service → PostgreSQL
```

### HITL Confirmation ≠ Business Approval

HITL Confirmation 与业务 Approval 不属于同一层次：

```text
HITL：
用户确认是否提交 Agent 准备的高风险操作。

Approval：
具备审批权限的角色对业务申请进行审批。
```

典型权限申请链路：

```text
create_access_request
  ↓
HITL（用户确认“我确实要提交”）
  ↓
Go Backend 创建 AccessRequest
  ↓
Approval（审批人批准 / 拒绝）
```

> **用户完成 HITL 不等于业务申请已经 Approved。**

---

# 5. Identity Propagation

可信身份传递路径：

```text
User
  → JWT
  → FastAPI Agent
  → Business Client
  → Go Business API
  → Go Service
  → PostgreSQL
```

规则：

1. FastAPI Agent 先校验 JWT，并从 Token 解析 `user_id`
2. Business Client 调用 Go 时携带：`Authorization: Bearer <JWT>` 与 `X-Request-ID`
3. Go Business API 再次校验 JWT，并从可信 Token 解析 `user_id` / `role`
4. Go Service 根据该认证上下文完成最终授权
5. **Go Service 不能信任客户端或 Agent 请求体中自行传入的 `user_id` / `role`**

错误示范：

```text
Agent 在 body 中声明 role = admin
  → Go 直接相信并提权
```

正确做法：

```text
Authorization: Bearer <JWT>
X-Request-ID: <request_id>
  → Go 验证 JWT 签名
  → 从 JWT 解析 user_id / role
  → Service Authorization
```

---

# 6. Thread Isolation

多轮会话隔离属于安全边界，不是纯体验问题。

要求：

```text
thread_id ↔ user_id 绑定
用户只能访问自己的 thread
Checkpointer 读取前必须先完成 ownership validation
不能仅凭 thread_id 直接读取会话
```

流程：

```text
JWT
  → 解析 user_id
  → 校验 thread_id 归属
  → 通过后再加载 LangGraph Checkpointer
```

跨用户访问他人 `thread_id` 必须拒绝。

---

# 7. API Security

MVP API 安全最小集：

| 项 | 说明 |
|---|---|
| JWT validation | Go 与 Agent 均校验 |
| Request validation | 参数类型、必填、枚举、长度等 |
| Authorization | RBAC + Ownership + Field-level |
| Error information leakage | 错误信息面向用户可读，但不泄露内部细节 / 敏感数据 |
| Timeout | Agent / Tool / 下游调用设置合理超时 |
| Basic rate limiting | Nginx 基础限流；MVP 不引入复杂网关或 Redis 限流 |

不在 MVP 宣称已实现：

```text
WAF / 零信任完整体系
细粒度 ABAC 平台
专用密钥管理系统以外的复杂方案
分布式风控引擎
```

---

# 8. MVP Security Checklist

- [ ] JWT authentication（Go + Agent）
- [ ] RBAC（employee / it_support / admin）
- [ ] Resource ownership validation
- [ ] Field-level authorization
- [ ] Agent → Go re-authorization
- [ ] Tool input validation
- [ ] Tool timeout
- [ ] HITL for sensitive actions
- [ ] thread_id ownership validation
- [ ] Basic rate limiting（Nginx）
- [ ] Avoid sensitive information in error responses

---

# 9. 与其他文档的关系

| 文档 | 关系 |
|---|---|
| `API.md` | 唯一 API Contract；本文不新增 / 修改任何 endpoint |
| `ARCHITECTURE.md` | 安全分层与身份边界的架构依据 |
| `EVALUATION.md` | Prompt Injection / 越权 Tool / HITL 等安全相关 Agent Case 的验证方式 |

一句话：

> **OpsPilot MVP 安全靠“可信身份 + Service 最终授权 + Tool/HITL 约束 + thread 归属”，而不是靠 Prompt 或前端权限。**
