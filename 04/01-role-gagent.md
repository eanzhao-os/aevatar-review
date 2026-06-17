# RoleGAgent:处理 ChatRequestEvent、流式调 LLM、发 AG-UI 事件

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## RoleGAgent 是什么

`RoleGAgent`(`RoleGAgent` )是 aevatar 的 AI 角色 actor,kind `ai.role-agent`,继承 `AIGAgentBase<RoleGAgentState>`。文件头注释()说明它的 3 步契约:

1. 经 `ChatStreamAsync` 流式调 LLM
2. 发 AG-UI 事件:`TextMessageStart → Content* → ToolCall* → End`
3. 记录稳定 id、长度、状态、脱敏标记

**Role 身份是 typed actor-owned fact**(重构注释):旧模式从 child actor id 前缀解析 role 身份;新模式把 `RoleId`/`RoleName` 作为持久化的 actor-owned fact。

---

## 处理 ChatRequestEvent()

```csharp
[EventHandler(AllowSelfHandling = true)]
public virtual async Task HandleChatRequest(ChatRequestEvent request)
```

`AllowSelfHandling = true` 允许 self-continuation(approval resume 后给自己发新 `ChatRequestEvent`)。

流程:
- :completed-session replay fast path
- :启动/恢复 session(新 SessionId 时持久化 `RoleChatSessionStartedEvent`)
- :per-request LLM timeout(`ResolveLlmTimeoutMs` + `CancellationTokenSource`)
- :**`TextMessageStartEvent`** 发给 `TopologyAudience.Parent`(流式开始前)
- :调 `ExecuteStreamingChatAsync`

---

## AG-UI 事件序列()

`ExecuteStreamingChatAsync`()迭代 `ChatStreamAsync`(继承自 `AIGAgentBase`,),逐 delta 发事件:

| delta 类型 | AG-UI 事件 | 行号 |
|---|---|---|
| content delta | `TextMessageContentEvent { Delta }` | |
| media delta | `MediaContentEvent` | |
| reasoning delta | `TextMessageReasoningEvent` | |
| tool-call delta | 累积 → `ToolCallEvent { CallId, ToolName, ArgumentsJson }` | |
| tool result | `ToolResultEvent`(带 `AgentToolReceipt`) | |

终端序列():`PersistSessionCompletionAsync`(先 commit)→ `PublishMissingDisplayContentAsync` → `PublishUsageAsync`(`ChatTokenUsageEvent`)→ `PublishCompletionAsync`(发 **`TextMessageEndEvent`**)。

---

## 工具审批与 self-continuation()

工具调用需要审批时():持久化 `PendingToolApprovalPersistedEvent`,发 `ToolApprovalRequestEvent`(mode `"yield"`),schedule timeout。默认 handler 是 `YieldApprovalHandler`()—— RoleGAgent 持有 pending-approval continuation(持久化 state + 远程升级 + timeout)。

审批通过后():清 pending approval → `BuildContinuationPrompt` → **self-continuation** —— 给自己 inbox 发新 `ChatRequestEvent`(`SendToAsync(Id, continuationRequest)`)开始新一轮。

---

## 验收

1. RoleGAgent 的 AG-UI 事件序列?(TextMessageStart → Content*/Media*/Reasoning* → ToolCall*/ToolResult* → End)
2. Role 身份存哪?(typed actor-owned fact,`RoleId`/`RoleName` 持久化在 state)
3. 工具审批后怎么继续?(self-continuation,给自己 inbox 发新 ChatRequestEvent)

⟦AI:AUTO-LOOP⟧
