# ChatRuntime / ToolLoop / 中间件管线(IAgentRun/IToolCall/ILLMCall Middleware)

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## ChatRuntime:流式 chat 执行

`ChatRuntime`(`ChatRuntime` )是流式 chat 执行核心。`DefaultMaxToolRounds = int.MaxValue`()—— 循环跑到 LLM 不再调工具(注释匹配 Claude Code 行为)。

`ChatStreamAsync` core():
1. 构建 `AgentRunContext`()
2. 经 `MiddlewarePipeline.RunAgentAsync` + `AgentRunMiddlewareBridge` 跑 agent-run middleware()
3. 迭代 `RunChatStreamCoreAsync`(:上下文压缩 → AfterCompression)

`RunChatStreamCoreAfterCompressionAsync`():主 `for (round)` 循环(),per-round `StreamingToolExecutor`(),per-round LLMRequest + `ComposeRoundCallId`(),skill-recovery + length-truncation recovery。

---

## ToolCallLoop:LLM → tool → result → LLM

`ToolCallLoop`(`ToolCallLoop` )持 `ToolManager` + hooks + middleware。`ExecuteCoreAsync`():

```text
for (round = 0; round < maxRounds; round++):
    InvokeLlmAsync ()
    Post-Sampling hook gate (可 block_tool_calls, )
    DSML/XML 文本工具调用 fallback (TextToolCallParser.Parse, )
    length-truncation recovery ()
    ExecuteToolCallsCoreAsync ()
maxRounds 耗尽 → 无工具 final call (ComposeFinalCallId, )
```

`MaxLengthRecoveries = 3`(),超长时用 `LengthRecoveryNudge` continuation prompt。

---

## 三层中间件管线(ASP.NET Core 风格)

`MiddlewarePipeline`(`MiddlewarePipeline` )用递归 `Execute<TMiddleware,TContext>`()实现 `next` 链:

| 中间件 | 接口 | Context 关键字段 |
|---|---|---|
| AgentRun | `IAgentRunMiddleware` | UserMessage/AgentId/Result/Terminate/Items |
| ToolCall | `IToolCallMiddleware` | Tool/ArgumentsJson/Result/Receipt/PendingApproval/Terminate/TerminationKind(None/ApprovalDenied/ApprovalTimedOut/ApprovalPending/MiddlewareTerminated) |
| LLMCall | `ILLMCallMiddleware` | Request(可变)/Provider/Response/Terminate/IsStreaming |

每个 `InvokeAsync(context, Func<Task> next)` —— 标准 middleware 链。

---

## 可观测性:OTel GenAI 语义约定

`GenAIActivitySource`(`GenAIActivitySource` ):
- `ActivitySource = new("Aevatar.GenAI", "1.0.0")`()
- Metrics:`gen_ai.client.token.usage`()、`gen_ai.client.operation.duration`()、`aevatar.tool.invocation.duration`()
- Spans:`StartInvokeAgent`(op `invoke_agent`,)、`StartChat`(op `chat`,)、`StartExecuteTool`()

`GenAIObservabilityMiddleware`(`GenAIObservabilityMiddleware` )实现全部三个 middleware,自动埋点(含 `EnableSensitiveData` 开关,控制是否记 input)。

---


!!! warning "设计待论证 / 已知缺口"
    DefaultMaxToolRounds = int.MaxValue 是无熔断 fallback(实际默认 40,见上游 aevatar#2210)。详见附录 TODO List(08/04)。

## 验收

1. ChatRuntime 的 tool loop 跑到什么时候?(LLM 不再调工具,DefaultMaxToolRounds=int.MaxValue)
2. 三层 middleware 是什么?(AgentRun/ToolCall/LLMCall,标准 next 链)
3. 可观测性用什么语义约定?(OTel GenAI,Aevatar.GenAI ActivitySource)

⟦AI:AUTO-LOOP⟧
