# Run 语义:runId/sessionId 服务端生成、不按 run 隔离事件流、终止事件收敛

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `README.md` 第 89-105 行:「Run 语义(重要)」节,四条反直觉规则 + LiveSink/projection 上下文。
- `docs/canon/workflow-runtime.md` 第 56-82 行:`WorkflowRunGAgent`(一次 run 一个 actor)+ 事件链;第 272-308 行:run 链路(POST /api/chat → ExecuteAsync → resolver → lifecycle → dispatch → StartWorkflowEvent → kernel → WorkflowCompletedEvent → 投影 → SSE);第 393-398 行:和 CQRS 投影的关系。
- `docs/canon/llm-streaming.md` 第 280-297 行:会话语义表(actorId/runId/commandId/correlationId/sessionId/chatSessionId/messageId)。
- `src/Aevatar.CQRS.Core/Commands/DefaultCommandContextPolicy.cs` 第 16-21 行:`commandId = Guid.NewGuid()`,`correlationId` 默认等于 `commandId`。
- `src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs` 第 389-391 行:`runId` 从 actor `Id` 派生(`WorkflowRunIdNormalizer.Normalize`);第 404、418、422 行:写入事件并发布。
- `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowRunIdNormalizer.cs` 第 6-13 行:runId 规范化(空→`default`,否则 trim)。
- `src/workflow/Aevatar.Workflow.Application/Runs/WorkflowChatRequestEnvelopeFactory.cs` 第 15-17 行:`sessionId = command.SessionId ?? context.CorrelationId`。
- `src/workflow/Aevatar.Workflow.Application/Runs/WorkflowRunCompletionPolicy.cs` 第 11-35 行:`TryResolve` 把 `RUN_FINISHED`→Completed、`RUN_ERROR`→Failed、`RUN_STOPPED`→Stopped。
- `src/workflow/Aevatar.Workflow.Presentation.AGUIAdapter/EventEnvelopeToWorkflowRunEventMapper.cs` 第 122-150 行:`StartWorkflowEvent` → `RUN_STARTED`(threadId = 发布 actor 的 ActorId);第 465-523 行:`WorkflowCompletedEvent` → `USAGE` + `RUN_FINISHED`/`RUN_ERROR`;第 823-829 行:`ResolveThreadId` = `envelope.Route.PublisherActorId`。
- `src/workflow/Aevatar.Workflow.Application/Runs/WorkflowRunFinalizeEmitter.cs` 第 19-53 行:run 收敛后发终止 `STATE_SNAPSHOT`。

---

## 四条反直觉规则(`README.md` 第 89-94 行)

aevatar 的 run 语义有几个让习惯传统请求/响应模型的人踩坑的点:

1. **同一 Actor 多次运行,默认不按 run 隔离事件流**(第 91 行):客户端收到的是该 Actor 的全量事件,不是只收当前 run 的。
2. **单次请求只在"当前 runId 的终止事件"到达时结束**(第 92 行):终止事件是 `RUN_FINISHED` 或 `RUN_ERROR`。
3. **`RUN_STARTED` 由 `StartWorkflowEvent` 投影统一生成**(第 93 行):不是 actor 直接发的运行开始信号,而是投影层把领域事件映射出来的。`threadId` = 发布该 `StartWorkflowEvent` 的 ActorId。
4. **`runId` 与内部 `sessionId` 都由服务端生成**(第 94 行):客户端请求只需 `prompt` / `workflow` / `agentId`,不需要自己造 runId。

---

## runId / sessionId / commandId 从哪来

这三个标识都是服务端生成的,客户端不参与:

| 标识 | 生成位置 | 规则 |
|---|---|---|
| `commandId` | `DefaultCommandContextPolicy.cs` 第 16-21 行 | `Guid.NewGuid().ToString("N")`;写入 `EventEnvelope.Id`,是 session stream key 的一部分 |
| `correlationId` | 同上 | 默认 = `commandId` |
| `runId` | `WorkflowRunGAgent.cs` 第 389-391 行 | 从 actor `Id` 派生:`WorkflowRunIdNormalizer.Normalize(Id)`;空/whitespace 时返回 `"default"`(`WorkflowRunIdNormalizer.cs` 第 6-13 行) |
| `sessionId` | `WorkflowChatRequestEnvelopeFactory.cs` 第 15-17 行 | `command.SessionId ?? context.CorrelationId`(回退到 correlationId) |

`runId` 生成后写入 `WorkflowRunExecutionStartedEvent`(`WorkflowRunGAgent.cs` 第 404 行)、`StartWorkflowEvent.RunId`(第 418 行),再 publish 到 self(第 422 行)。kernel 的 `ResolveRunIdOrCurrent`(`WorkflowExecutionKernel.cs` 第 1490-1496 行)复用它。

> `llm-streaming.md` 第 280-297 行的会话语义表强调:`runId` 是 workflow run 绑定标识,**不是** actor 地址。actor 地址是 `actorId`。session stream key 是 `workflow-run:{actorId}:{commandId}`(第 286 行)。

---

## 为什么不按 run 隔离事件流?

这是最容易误解的一点。`README.md` 第 91 行说同一 Actor 多次运行默认**不按 run 隔离**。

**原因**:aevatar 的 actor 是有状态的业务实体(一个 `WorkflowRunGAgent` = 一次 run)。事件流是 actor 维度的(`workflow-run:{actorId}:{commandId}`),不是 run 维度的隔离管道。客户端订阅的是一个 actor 的事件投影,会收到该 actor 在该 commandId 生命周期内的全部 run 事件。

**那客户端怎么知道该停?** —— 靠终止事件收敛。`WorkflowRunCompletionPolicy.cs` 第 11-35 行的 `TryResolve`:

- `RUN_FINISHED` → `Completed`
- `RUN_ERROR` → `Failed`
- `RUN_STOPPED` → `Stopped`

这个 `ICommandCompletionPolicy`(注册在 `ServiceCollectionExtensions.cs` 第 85 行)决定 SSE/WS 流何时结束。单次请求只在**当前 runId 的终止事件**到达时结束(`README.md` 第 92 行)。

---

## 一次 run 的完整事件序列

以 `simple_qa` 为例,run 链路见 `docs/canon/workflow-runtime.md` 第 272-308 行:

```text
POST /api/chat
  → ICommandInteractionService.ExecuteAsync
  → WorkflowRunCommandTargetResolver(workflowYaml 优先,否则 registry,否则 default)
  → WorkflowRunObservationLifecycle(attach 到已有 projection session,无 pre-dispatch projection activation)
  → dispatch ChatRequestEvent envelope
  → WorkflowRunGAgent 收到,生成 runId,发 StartWorkflowEvent
  → WorkflowExecutionKernel 推进:StepRequestEvent → StepCompletedEvent → ...
  → WorkflowCompletedEvent
  → 投影(EventEnvelopeToWorkflowRunEventMapper)
  → SSE 流
```

投影层把领域事件映射成 run 事件(`EventEnvelopeToWorkflowRunEventMapper.cs`):

| 领域事件 | 映射到的 run 事件 | 代码行号 |
|---|---|---|
| `StartWorkflowEvent` | `RUN_STARTED`(`threadId` = 发布 actor 的 ActorId) | 第 122-150 行 |
| `WorkflowCompletedEvent(success=true)` | `USAGE` + `RUN_FINISHED` | 第 465-523 行 |
| `WorkflowCompletedEvent(success=false)` | `RUN_ERROR`(code `"WORKFLOW_FAILED"`) | 第 465-523 行 |
| `WorkflowStoppedEvent` | `RUN_FINISHED` / `RUN_ERROR` | 第 525+ 行 |

run 收敛后,`WorkflowRunFinalizeEmitter.cs` 第 19-53 行发一个终止 `STATE_SNAPSHOT`,携带 actorId / workflowName / commandId / projection completion + 可选 snapshot(`llm-streaming.md` 第 420-421 行)。

---

## threadId = 发布该事件的 ActorId

`RUN_STARTED` 和 `RUN_FINISHED` 的 `threadId` 由 `ResolveThreadId`(`EventEnvelopeToWorkflowRunEventMapper.cs` 第 823-829 行)决定:

```csharp
public static string ResolveThreadId(EventEnvelope envelope, string fallback)
{
    var publisherActorId = envelope.Route?.PublisherActorId;
    return string.IsNullOrWhiteSpace(publisherActorId) ? fallback : publisherActorId;
}
```

即 `threadId` = 发布 `StartWorkflowEvent` / `WorkflowCompletedEvent` 的那个 actor 的 ActorId(通常是 `WorkflowRunGAgent`),缺失时回退到 `evt.WorkflowName`。这解释了为什么 `RUN_STARTED` 的 `threadId` 不是客户端传的,而是服务端 actor 身份。

---

## LiveSink 绑定(`README.md` 第 96-105 行)

客户端订阅 run 事件靠 LiveSink,绑定方式是 `workflow-run:{actorId}:{commandId}` stream 的 subscribe/unsubscribe(`README.md` 第 96 行)。**没有**进程内 sink 列表 —— 这条约束(`docs/adr/0002-mainnet-architecture.md` 第 1054 行)禁止在中间层引入 `runId -> context` 进程内事实映射。投影并发通过 `projection:{rootActorId}` coordinator actor 协调(`README.md` 第 105 行)。

---

## 验收

用一次具体 run 回答:

1. runId 从哪来?(服务端从 actor Id 派生,`WorkflowRunGAgent.cs` 第 389-391 行;客户端不传)
2. 为什么不按 run 隔离事件流?(事件流是 actor 维度,客户端收该 actor 全量,`README.md` 第 91 行)
3. 客户端怎么知道该停?(当前 runId 的终止事件 `RUN_FINISHED`/`RUN_ERROR`,`WorkflowRunCompletionPolicy.cs` 第 11-35 行)
4. `RUN_STARTED` 怎么产生的?(投影层把 `StartWorkflowEvent` 映射出来,`EventEnvelopeToWorkflowRunEventMapper.cs` 第 122-150 行)
5. `threadId` 是什么?(发布该事件的 actor 的 ActorId,第 823-829 行)

⟦AI:AUTO-LOOP⟧
