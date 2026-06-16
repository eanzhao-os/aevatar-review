# ChatRuntime / ToolLoop / 中间件管线(IAgentRun/IToolCall/ILLMCall Middleware)

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.AI.Core/Chat/ChatRuntime.cs` 第 34-80 行:`ChatRuntime`(持 `_providerFactory`/`_history`/`_toolLoop`/`_hooks`/三 middleware 只读列表);第 40 行:`DefaultMaxToolRounds = int.MaxValue`(注释第 37-39 行:跑到 LLM 不再调工具);第 184-256 行:`ChatStreamAsync` core(AgentRunContext + MiddlewarePipeline.RunAgentAsync);第 291-404 行:`RunChatStreamCoreAfterCompressionAsync`(per-round for 循环 + StreamingToolExecutor)。
- `src/Aevatar.AI.Core/Chat/ChatRuntimeStepExecutor.cs` 第 9-32 行:可组合 step(BuildLlmStepRequest/ExecuteLlmStepAsync/ExecuteToolStepAsync)。
- `src/Aevatar.AI.Core/Tools/ToolCallLoop.cs` 第 20-40 行:`ToolCallLoop`(持 ToolManager/hooks/middleware);第 53-63 行:`ExecuteAsync`;第 73-209 行:`ExecuteCoreAsync`(per-round LLM→tool→result→LLM);第 121-163 行:DSML/XML 文本工具调用 fallback(`TextToolCallParser.Parse`);第 211-260 行:maxRounds 耗尽后无工具 final call。
- `src/Aevatar.AI.Core/Middleware/MiddlewarePipeline.cs` 第 9-53 行:`RunAgentAsync`/`RunToolCallAsync`/`RunLLMCallAsync`(递归 `Execute<TMiddleware,TContext>`,第 41-52 行)。
- `src/Aevatar.AI.Abstractions/Middleware/IAgentRunMiddleware.cs` 第 7-10 行;`IToolCallMiddleware.cs` 第 10-13 行(Context 第 40-80 行:Tool/ArgumentsJson/Result/Receipt/PendingApproval/Terminate/TerminationKind);`ILLMCallMiddleware.cs` 第 9-12 行。
- `src/Aevatar.AI.Core/Observability/GenAIActivitySource.cs` 第 15-68 行:`Aevatar.GenAI` ActivitySource + Meter(`gen_ai.client.token.usage`/`gen_ai.client.operation.duration`/`aevatar.tool.invocation.duration`);`GenAIObservabilityMiddleware.cs` 第 17-18 行:实现全部三个 middleware。
- `src/Aevatar.AI.Core/Tools/ToolManager.cs` 第 13-73 行:工具注册 + 执行。

---

## ChatRuntime:流式 chat 执行

`ChatRuntime`(`ChatRuntime.cs` 第 34-80 行)是流式 chat 执行核心。`DefaultMaxToolRounds = int.MaxValue`(第 40 行)—— 循环跑到 LLM 不再调工具(注释第 37-39 行,匹配 Claude Code 行为)。

`ChatStreamAsync` core(第 184-256 行):
1. 构建 `AgentRunContext`(第 197-203 行)
2. 经 `MiddlewarePipeline.RunAgentAsync` + `AgentRunMiddlewareBridge` 跑 agent-run middleware(第 205-214 行)
3. 迭代 `RunChatStreamCoreAsync`(第 258-289 行:上下文压缩 → AfterCompression)

`RunChatStreamCoreAfterCompressionAsync`(第 291-404 行):主 `for (round)` 循环(第 330 行),per-round `StreamingToolExecutor`(第 338-341 行),per-round LLMRequest + `ComposeRoundCallId`(第 351-353 行),skill-recovery + length-truncation recovery。

---

## ToolCallLoop:LLM → tool → result → LLM

`ToolCallLoop`(`ToolCallLoop.cs` 第 20-40 行)持 `ToolManager` + hooks + middleware。`ExecuteCoreAsync`(第 73-209 行):

```text
for (round = 0; round < maxRounds; round++):
    InvokeLlmAsync (第 99 行)
    Post-Sampling hook gate (可 block_tool_calls, 第 101-119 行)
    DSML/XML 文本工具调用 fallback (TextToolCallParser.Parse, 第 121-163 行)
    length-truncation recovery (第 165-180 行)
    ExecuteToolCallsCoreAsync (第 200-208 行)
maxRounds 耗尽 → 无工具 final call (ComposeFinalCallId, 第 211-260 行)
```

`MaxLengthRecoveries = 3`(第 65 行),超长时用 `LengthRecoveryNudge` continuation prompt。

---

## 三层中间件管线(ASP.NET Core 风格)

`MiddlewarePipeline`(`MiddlewarePipeline.cs` 第 9-53 行)用递归 `Execute<TMiddleware,TContext>`(第 41-52 行)实现 `next` 链:

| 中间件 | 接口 | Context 关键字段 |
|---|---|---|
| AgentRun | `IAgentRunMiddleware.cs:7-10` | UserMessage/AgentId/Result/Terminate/Items |
| ToolCall | `IToolCallMiddleware.cs:10-13` | Tool/ArgumentsJson/Result/Receipt/PendingApproval/Terminate/TerminationKind(None/ApprovalDenied/ApprovalTimedOut/ApprovalPending/MiddlewareTerminated) |
| LLMCall | `ILLMCallMiddleware.cs:9-12` | Request(可变)/Provider/Response/Terminate/IsStreaming |

每个 `InvokeAsync(context, Func<Task> next)` —— 标准 middleware 链。

---

## 可观测性:OTel GenAI 语义约定

`GenAIActivitySource`(`GenAIActivitySource.cs` 第 15-68 行):
- `ActivitySource = new("Aevatar.GenAI", "1.0.0")`(第 17 行)
- Metrics:`gen_ai.client.token.usage`(第 26 行)、`gen_ai.client.operation.duration`(第 30 行)、`aevatar.tool.invocation.duration`(第 34 行)
- Spans:`StartInvokeAgent`(op `invoke_agent`,第 39-47 行)、`StartChat`(op `chat`,第 49-56 行)、`StartExecuteTool`(第 58-67 行)

`GenAIObservabilityMiddleware`(`GenAIObservabilityMiddleware.cs` 第 17-18 行)实现全部三个 middleware,自动埋点(含 `EnableSensitiveData` 开关,第 21 行控制是否记 input)。

---

## 验收

1. ChatRuntime 的 tool loop 跑到什么时候?(LLM 不再调工具,DefaultMaxToolRounds=int.MaxValue)
2. 三层 middleware 是什么?(AgentRun/ToolCall/LLMCall,标准 next 链)
3. 可观测性用什么语义约定?(OTel GenAI,Aevatar.GenAI ActivitySource)

⟦AI:AUTO-LOOP⟧
