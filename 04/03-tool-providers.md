# ★ Tool 体系:ToolApprovalHandler + 20+ ToolProvider(MCP/Skills/Lark/Web/...)

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.AI.Abstractions/ToolProviders/IToolApprovalHandler.cs` 第 12-19 行:`RequestApprovalAsync`;第 22-86 行:`ToolApprovalRequest`/`ToolApprovalResult`(Approved/Denied/TimedOut/Yielded)/`ToolApprovalDecision`。
- `src/Aevatar.AI.Core/Middleware/YieldApprovalHandler.cs` 第 16-22 行:立即 `Yielded`(actor 持 continuation);`MissingApprovalHandler.cs`:fail-closed 回退。
- `src/Aevatar.AI.Core/Middleware/ToolApprovalMiddleware.cs` 第 21-32 行:`IToolCallMiddleware`(必须插最前,第 16-17 行);第 36-97 行:grant 匹配/NeverRequire/Auto 分类(IsReadOnly/IsDestructive);第 88-97 行:denial 计数(≥3 `MaxConsecutiveDenials` 自动 block);第 129-191 行:Decision switch(Approved/Denied/Timeout/Yield→Terminate+PendingApproval)。
- `src/Aevatar.AI.Abstractions/ToolProviders/IAgentTool.cs` 第 18-39 行:`ApprovalMode`/`IsReadOnly`/`IsDestructive`/`RequiresApproval`。
- `src/Aevatar.AI.ToolProviders.ToolSetRegistry/ToolSetRegistry.cs` 第 7-94 行:`Resolve`/`AddSources`(set inclusion + cycle detection);`ToolSetNames.cs` 第 5-14 行:`workspace.default`/`lark.self_notify`/`nyxid.connected_services`。
- `src/Aevatar.Mainnet.Host.Api/Hosting/MainnetHostBuilderExtensions.cs` 第 266-301 行:`workspace.default`(16 sources)。
- 22 个 ToolSource 类(见下表)。

---

## 工具审批:ToolApprovalHandler

工具调用可能需要审批。`IToolApprovalHandler`(`IToolApprovalHandler.cs` 第 12-19 行)的 `RequestApprovalAsync` 返回 `ToolApprovalResult`:Approved/Denied/TimedOut/Yielded(第 50-70 行)。

**两个实现**:
- `YieldApprovalHandler`(`YieldApprovalHandler.cs` 第 16-22 行):立即 `Yielded` —— RoleGAgent 持有 pending-approval continuation(持久化 state + 远程升级 + timeout)
- `MissingApprovalHandler`:fail-closed 回退(不持 continuation 的 surface)

**`ToolApprovalMiddleware`**(`ToolApprovalMiddleware.cs` 第 21-32 行)是 `IToolCallMiddleware`,注释(第 16-17 行)要求插在 tool call middleware 链**最前面**(安全策略不可绕过)。逻辑:
- grant 匹配(replay grant 的 ToolName+ToolCallId 必须匹配,第 37-50 行)
- `NeverRequire` → 直接执行(第 53-57 行)
- `Auto` 分类:`IsReadOnly`/非 destructive → 跳过;`IsDestructive` → 审批(第 69-84 行)
- denial 计数:≥ `MaxConsecutiveDenials = 3`(第 23 行)→ 自动 block(第 88-97 行)
- Yield(第 169-190 行):Terminate + `TerminationKind = ApprovalPending` + `PendingApproval` context

---

## 22 个 ToolProvider / ToolSource

| # | 类 | 文件 | 领域 |
|---|---|---|---|
| 1 | `MCPAgentToolSource` | `Aevatar.AI.ToolProviders.MCP/MCPAgentToolSource.cs:11` | MCP servers |
| 2 | `SkillsAgentToolSource` | `…/Skills/SkillsAgentToolSource.cs:19` | Skills |
| 3 | `LarkAgentToolSource` | `…/Lark/LarkAgentToolSource.cs:9` | Lark |
| 4 | `LarkWorkflowFileSubmitToolSource` | `…/Lark/LarkWorkflowFileSubmitToolSource.cs:11` | Lark workflow 文件 |
| 5 | `WebAgentToolSource` | `…/Web/WebAgentToolSource.cs:11` | Web/搜索 |
| 6 | `TelegramAgentToolSource` | `…/Telegram/TelegramAgentToolSource.cs:9` | Telegram |
| 7 | `OrnnAgentToolSource` | `…/Ornn/OrnnAgentToolSource.cs:11` | Ornn |
| 8 | `ChannelInteractiveReplyToolSource` | `…/Channel/ChannelInteractiveReplyToolSource.cs:9` | Channel 交互回复 |
| 9 | `ChannelRegistrationToolSource` | `…/ChannelAdmin/ChannelRegistrationToolSource.cs:10` | Channel 注册 |
| 10 | `ScriptingAgentToolSource` | `…/Scripting/ScriptingAgentToolSource.cs:15` | Scripting |
| 11 | `ServiceInvokeAgentToolSource` | `…/ServiceInvoke/ServiceInvokeAgentToolSource.cs:10` | Service 调用 |
| 12 | `WorkflowAgentToolSource` | `…/Workflow/WorkflowAgentToolSource.cs:14` | Workflow |
| 13 | `BindingAgentToolSource` | `…/Binding/BindingAgentToolSource.cs:17` | Binding |
| 14 | `ChronoStorageAgentToolSource` | `…/ChronoStorage/ChronoStorageAgentToolSource.cs:12` | Chrono storage |
| 15 | `NyxIdAgentToolSource` | `…/NyxId/NyxIdAgentToolSource.cs:12` | NyxId |
| 16 | `NyxIdConnectedServiceToolSource` | `…/NyxId/NyxIdConnectedServiceToolSource.cs:21` | NyxId 连接服务(per-user opt-in) |
| 17 | `InvokeGAgentToolSource` | `…/AevatarInvocation/AevatarInvocationToolSources.cs:9` | 调 GAgent |
| 18 | `InvokeTeamToolSource` | 同上:22 | 调 team |
| 19 | `StartWorkflowToolSource` | 同上:35 | 启动 workflow |
| 20 | `ObserveRunToolSource` | 同上:48 | 观察 run |
| 21 | `ReadWorkflowRunArtifactToolSource` | 同上:61 | 读 run artifact |
| 22 | `AgentDeliveryTargetToolSource` | `…/AgentCatalog/AgentDeliveryTargetToolSource.cs:6` | Agent 投递目标 |

---

## ToolSetRegistry allowlist

`ToolSetRegistry`(`ToolSetRegistry.cs` 第 7-94 行)管理命名工具集:
- `Resolve(ChatRouteToolSetRef?)`(第 40-66 行):按名查 registration
- `AddSources`(第 68-94 行):支持 set inclusion(`IncludeToolSetNames`)+ cycle detection

三个命名集(`ToolSetNames.cs` 第 5-14 行):

| 集 | 内容 | 文件 |
|---|---|---|
| `workspace.default` | 16 sources(InvokeGAgent/Team/StartWorkflow/ObserveRun/ReadArtifact/ResponsesProvider/Channel×2/DeliveryTarget/NyxId/Lark/Telegram/ChronoStorage/Web/Skills/Ornn) | `MainnetHostBuilderExtensions.cs:268-288` |
| `lark.self_notify` | include `workspace.default` + Lark self-notify | 第 289-293 行 |
| `nyxid.connected_services` | opt-in only(`NyxIdConnectedServiceToolSource`) | 第 297-300 行 |

> connected-service 工具不进 `workspace.default`(第 9-13 行注释),只在 route policy 显式选择该 set 时注入。

---

## 验收

1. 工具审批的 Yield 模式怎么工作?(YieldApprovalHandler 立即 Yielded,actor 持 pending continuation)
2. ToolApprovalMiddleware 为什么插最前?(安全策略不可绕过,第 16-17 行)
3. `workspace.default` 含哪些?(16 个 source,MainnetHostBuilderExtensions.cs:268-288)
4. tool_call 和 connector_call 区别?(前者 agent 工具系统;后者 workflow connector,role-model.md:265-268)

⟦AI:AUTO-LOOP⟧
