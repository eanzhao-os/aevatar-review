# ★ Tool 体系:ToolApprovalHandler + 20+ ToolProvider(MCP/Skills/Lark/Web/...)

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## 工具审批:ToolApprovalHandler

工具调用可能需要审批。`IToolApprovalHandler`(`IToolApprovalHandler` )的 `RequestApprovalAsync` 返回 `ToolApprovalResult`:Approved/Denied/TimedOut/Yielded()。

**两个实现**:
- `YieldApprovalHandler`(`YieldApprovalHandler` ):立即 `Yielded` —— RoleGAgent 持有 pending-approval continuation(持久化 state + 远程升级 + timeout)
- `MissingApprovalHandler`:fail-closed 回退(不持 continuation 的 surface)

**`ToolApprovalMiddleware`**(`ToolApprovalMiddleware` )是 `IToolCallMiddleware`,注释()要求插在 tool call middleware 链**最前面**(安全策略不可绕过)。逻辑:
- grant 匹配(replay grant 的 ToolName+ToolCallId 必须匹配,)
- `NeverRequire` → 直接执行()
- `Auto` 分类:`IsReadOnly`/非 destructive → 跳过;`IsDestructive` → 审批()
- denial 计数:≥ `MaxConsecutiveDenials = 3`()→ 自动 block()
- Yield():Terminate + `TerminationKind = ApprovalPending` + `PendingApproval` context

---

## 22 个 ToolProvider / ToolSource

| # | 类 | 文件 | 领域 |
|---|---|---|---|
| 1 | `MCPAgentToolSource` | MCP servers |
| 2 | `SkillsAgentToolSource` | `SkillsAgentToolSource` | Skills |
| 3 | `LarkAgentToolSource` | `LarkAgentToolSource` | Lark |
| 4 | `LarkWorkflowFileSubmitToolSource` | `LarkWorkflowFileSubmitToolSource` | Lark workflow 文件 |
| 5 | `WebAgentToolSource` | `WebAgentToolSource` | Web/搜索 |
| 6 | `TelegramAgentToolSource` | `TelegramAgentToolSource` | Telegram |
| 7 | `OrnnAgentToolSource` | `OrnnAgentToolSource` | Ornn |
| 8 | `ChannelInteractiveReplyToolSource` | `ChannelInteractiveReplyToolSource` | Channel 交互回复 |
| 9 | `ChannelRegistrationToolSource` | `ChannelRegistrationToolSource` | Channel 注册 |
| 10 | `ScriptingAgentToolSource` | `ScriptingAgentToolSource` | Scripting |
| 11 | `ServiceInvokeAgentToolSource` | `ServiceInvokeAgentToolSource` | Service 调用 |
| 12 | `WorkflowAgentToolSource` | `WorkflowAgentToolSource` | Workflow |
| 13 | `BindingAgentToolSource` | `BindingAgentToolSource` | Binding |
| 14 | `ChronoStorageAgentToolSource` | `ChronoStorageAgentToolSource` | Chrono storage |
| 15 | `NyxIdAgentToolSource` | `NyxIdAgentToolSource` | NyxId |
| 16 | `NyxIdConnectedServiceToolSource` | `NyxIdConnectedServiceToolSource` | NyxId 连接服务(per-user opt-in) |
| 17 | `InvokeGAgentToolSource` | `AevatarInvocationToolSources` | 调 GAgent |
| 18 | `InvokeTeamToolSource` | 同上 | 调 team |
| 19 | `StartWorkflowToolSource` | 同上 | 启动 workflow |
| 20 | `ObserveRunToolSource` | 同上 | 观察 run |
| 21 | `ReadWorkflowRunArtifactToolSource` | 同上 | 读 run artifact |
| 22 | `AgentDeliveryTargetToolSource` | `AgentDeliveryTargetToolSource` | Agent 投递目标 |

---

## ToolSetRegistry allowlist

`ToolSetRegistry`(`ToolSetRegistry` )管理命名工具集:
- `Resolve(ChatRouteToolSetRef?)`():按名查 registration
- `AddSources`():支持 set inclusion(`IncludeToolSetNames`)+ cycle detection

三个命名集(`ToolSetNames` ):

| 集 | 内容 | 文件 |
|---|---|---|
| `workspace.default` | 16 sources(InvokeGAgent/Team/StartWorkflow/ObserveRun/ReadArtifact/ResponsesProvider/Channel×2/DeliveryTarget/NyxId/Lark/Telegram/ChronoStorage/Web/Skills/Ornn) | `MainnetHostBuilderExtensions` |
| `lark.self_notify` | include `workspace.default` + Lark self-notify | |
| `nyxid.connected_services` | opt-in only(`NyxIdConnectedServiceToolSource`) | |

> connected-service 工具不进 `workspace.default`(注释),只在 route policy 显式选择该 set 时注入。

---

## 验收

1. 工具审批的 Yield 模式怎么工作?(YieldApprovalHandler 立即 Yielded,actor 持 pending continuation)
2. ToolApprovalMiddleware 为什么插最前?(安全策略不可绕过,)
3. `workspace.default` 含哪些?(16 个 source,MainnetHostBuilderExtensions.cs)
4. tool_call 和 connector_call 区别?(前者 agent 工具系统;后者 workflow connector,role-model.md)

⟦AI:AUTO-LOOP⟧
