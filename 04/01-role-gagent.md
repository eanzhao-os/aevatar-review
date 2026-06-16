# RoleGAgent:处理 ChatRequestEvent、流式调 LLM、发 AG-UI 事件

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.AI.Core/RoleGAgent.cs` 第 1-8 行:文件头注释(3 步契约:ChatStreamAsync 流式 → AG-UI 事件 → 日志);第 32-33 行:`[GAgent("ai.role-agent")] RoleGAgent : AIGAgentBase<RoleGAgentState>, IRoleAgent, IVoicePresenceRuntimeStateOwner`;第 68-74 行:`RoleName`/`RoleId`(typed actor-owned fact);第 58-62 行:默认 `YieldApprovalHandler`;第 777-778 行:`[EventHandler(AllowSelfHandling=true)] HandleChatRequest`;第 823-828 行:`TextMessageStartEvent`;第 911、930 行:`ExecuteStreamingChatAsync`/`ChatStreamAsync`;第 935-1008 行:content/media/reasoning/tool delta → AG-UI 事件;第 1237-1244 行:`TextMessageEndEvent`;第 206-223 行:self-continuation(approval resume)。
- `src/Aevatar.AI.Core/AIGAgentBase.cs`:基类(持 `ChatStreamAsync` 机制 + `Tools`/`History`)。
- `docs/canon/role-model.md` 第 7-15 行:Role 定义;第 42 行:provider;第 57 行:llm_call 派发;第 265-268 行:tool_call vs connector_call。

---

## RoleGAgent 是什么

`RoleGAgent`(`RoleGAgent.cs` 第 32-33 行)是 aevatar 的 AI 角色 actor,kind `ai.role-agent`,继承 `AIGAgentBase<RoleGAgentState>`。文件头注释(第 1-8 行)说明它的 3 步契约:

1. 经 `ChatStreamAsync` 流式调 LLM
2. 发 AG-UI 事件:`TextMessageStart → Content* → ToolCall* → End`
3. 记录稳定 id、长度、状态、脱敏标记

**Role 身份是 typed actor-owned fact**(第 71-74 行重构注释):旧模式从 child actor id 前缀解析 role 身份;新模式把 `RoleId`/`RoleName` 作为持久化的 actor-owned fact。

---

## 处理 ChatRequestEvent(第 777-778 行)

```csharp
[EventHandler(AllowSelfHandling = true)]
public virtual async Task HandleChatRequest(ChatRequestEvent request)
```

`AllowSelfHandling = true` 允许 self-continuation(approval resume 后给自己发新 `ChatRequestEvent`)。

流程:
- 第 780-789 行:completed-session replay fast path
- 第 791-806 行:启动/恢复 session(新 SessionId 时持久化 `RoleChatSessionStartedEvent`)
- 第 818-821 行:per-request LLM timeout(`ResolveLlmTimeoutMs` + `CancellationTokenSource`)
- 第 823-828 行:**`TextMessageStartEvent`** 发给 `TopologyAudience.Parent`(流式开始前)
- 第 833 行:调 `ExecuteStreamingChatAsync`

---

## AG-UI 事件序列(第 911-1244 行)

`ExecuteStreamingChatAsync`(第 911 行)迭代 `ChatStreamAsync`(继承自 `AIGAgentBase`,第 930 行),逐 delta 发事件:

| delta 类型 | AG-UI 事件 | 行号 |
|---|---|---|
| content delta | `TextMessageContentEvent { Delta }` | 第 935-943 行 |
| media delta | `MediaContentEvent` | 第 945-954 行 |
| reasoning delta | `TextMessageReasoningEvent` | 第 956-964 行 |
| tool-call delta | 累积 → `ToolCallEvent { CallId, ToolName, ArgumentsJson }` | 第 966-985 行 |
| tool result | `ToolResultEvent`(带 `AgentToolReceipt`) | 第 987-1008 行 |

终端序列(第 891-894 行):`PersistSessionCompletionAsync`(先 commit)→ `PublishMissingDisplayContentAsync` → `PublishUsageAsync`(`ChatTokenUsageEvent`)→ `PublishCompletionAsync`(第 1237-1244 行发 **`TextMessageEndEvent`**)。

---

## 工具审批与 self-continuation(第 206-223 行)

工具调用需要审批时(第 863-885 行):持久化 `PendingToolApprovalPersistedEvent`,发 `ToolApprovalRequestEvent`(mode `"yield"`),schedule timeout。默认 handler 是 `YieldApprovalHandler`(第 58-62 行)—— RoleGAgent 持有 pending-approval continuation(持久化 state + 远程升级 + timeout)。

审批通过后(第 206-223 行):清 pending approval → `BuildContinuationPrompt` → **self-continuation** —— 给自己 inbox 发新 `ChatRequestEvent`(第 215-223 行,`SendToAsync(Id, continuationRequest)`)开始新一轮。

---

## 验收

1. RoleGAgent 的 AG-UI 事件序列?(TextMessageStart → Content*/Media*/Reasoning* → ToolCall*/ToolResult* → End)
2. Role 身份存哪?(typed actor-owned fact,`RoleId`/`RoleName` 持久化在 state)
3. 工具审批后怎么继续?(self-continuation,给自己 inbox 发新 ChatRequestEvent)

⟦AI:AUTO-LOOP⟧
