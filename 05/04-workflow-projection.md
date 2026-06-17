# Workflow 专属投影:CurrentState canonical + Insight/Timeline/Graph Artifact + AGUI 映射

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/workflow/Aevatar.Workflow.Projection/Projectors/WorkflowExecutionCurrentStateProjector.cs` 第 8-13 行:canonical current-state(`MappedCurrentStateProjectionMaterializer<…,WorkflowRunState,WorkflowExecutionCurrentStateDocument>`);`Map` 第 23-83 行;actor-scoped guard(第 32-33 行)。
- `src/workflow/Aevatar.Workflow.Projection/Projectors/WorkflowRunInsightReportArtifactProjector.cs` 第 9-11 行:derived artifact(`IProjectionArtifactMaterializer`);`ProjectAsync` 第 30-56 行(document + graph upsert);第 16-19 行重构注释(timeline/graph 从 report artifact 派生,删重复 shell)。
- `src/workflow/Aevatar.Workflow.Projection/Projectors/WorkflowCatalogCurrentStateProjector.cs` 第 10 行;`WorkflowActorBindingProjector.cs` 第 9 行。
- `src/workflow/Aevatar.Workflow.Projection/ReadModels/WorkflowRunGraphArtifactMaterializer.cs` 第 8、16-26 行:`Materialize(WorkflowRunInsightReportDocument)` 派生 graph;`WorkflowRunInsightReportGraphMaterializer.cs` 第 6-19 行(注册为 `IProjectionGraphMaterializer`)。
- `src/workflow/Aevatar.Workflow.Projection/DependencyInjection/ServiceCollectionExtensions.cs` 第 108-119 行:4 个 projector 注册;第 46-92 行:durable+session core + committed-state hook。
- `src/workflow/Aevatar.Workflow.Presentation.AGUIAdapter/EventEnvelopeToWorkflowRunEventMapper.cs` 第 22-101 行:AGUI 映射(ordered handlers);各 handler 第 103-864 行。
- `src/workflow/Aevatar.Workflow.Presentation.AGUIAdapter/WorkflowExecutionRunEventProjector.cs` 第 17-104 行:session projector(跑 mapper,pin stream 到 SessionId,fail-closed)。
- `src/Aevatar.CQRS.Projection.Core/Streaming/ProjectionSessionEventHub.cs` 第 17-121 行:fans out to live sinks(stream id `{channel}:{rootActorId}:{sessionId}`,第 119-120 行)。
- `docs/canon/llm-streaming.md` 第 13、27、48-52、82-97 行:projection 与 SSE 共享输入。

---

## canonical vs derived

workflow projection 有两类 projector(`ServiceCollectionExtensions.cs` 第 108-119 行):

| Projector | 类型 | 文件 | 说明 |
|---|---|---|---|
| `WorkflowExecutionCurrentStateProjector` | **canonical current-state** | `:8-13` | `WorkflowRunState → WorkflowExecutionCurrentStateDocument` 的权威当前态副本 |
| `WorkflowRunInsightReportArtifactProjector` | **derived artifact** | `:9-11` | upsert InsightReport document + graph |
| `WorkflowCatalogCurrentStateProjector` | current-state | `:10` | workflow binding 当前态 |
| `WorkflowActorBindingProjector` | artifact | `:9` | binding artifact |

> ⚠️ **Timeline/Graph 不再有独立 projector 类**。重构 `416108d7a` 删除了 `WorkflowRunTimelineArtifactProjector`/`WorkflowRunGraphArtifactProjector`(canon 文档引用已过期)。现在 timeline/graph 从单一 `WorkflowRunInsightReportDocument` artifact **派生**:`WorkflowRunGraphArtifactMaterializer.Materialize(report)`(`WorkflowRunGraphArtifactMaterializer.cs,16-26`)。

---

## AGUI 事件映射

`EventEnvelopeToWorkflowRunEventMapper`(`EventEnvelopeToWorkflowRunEventMapper.cs` 第 22-101 行)用 ordered handlers 把领域事件映射成 AGUI `WorkflowRunEventEnvelope`:

| Handler | 领域事件 → AGUI | 行号 |
|---|---|---|
| `StartWorkflowRunEventEnvelopeMappingHandler` | `StartWorkflowEvent` → `RunStarted` | 第 122-150 行 |
| `StepRequestRunEventEnvelopeMappingHandler` | → `StepStarted` + `aevatar.step.request` | 第 152-195 行 |
| `StepCompletedRunEventEnvelopeMappingHandler` | → `StepFinished` + `aevatar.step.completed` | 第 197-247 行 |
| `AITextStreamRunEventEnvelopeMappingHandler` | → `TextMessageStart/Content/End`、`MediaContent`、`ChatResponse`、`Usage` | 第 249-429 行 |
| `WorkflowCompletedRunEventEnvelopeMappingHandler` | → `RunFinished` / `RunError` | 第 465-523 行 |
| `ToolCallRunEventEnvelopeMappingHandler` | → `ToolCallStart` / `ToolCallEnd` | 第 575-626 行 |
| `WorkflowSuspendedRunEventEnvelopeMappingHandler` | → `aevatar.tool_approval.pending` / `aevatar.human_input.request` | 第 628-702 行 |

`WorkflowExecutionRunEventProjector`(`WorkflowExecutionRunEventProjector.cs` 第 17-104 行)是 session projector,跑这个 mapper 并 publish 到 `ProjectionSessionEventHub`(pin stream 到 `context.SessionId`,缺失时 fail-closed)。

---

## LiveSink fan-out

`ProjectionSessionEventHub`(`ProjectionSessionEventHub.cs` 第 17-121 行):按 `RootActorId + SessionId` key 的 stream fan-out 到 live sinks。stream id 格式 `{channel}:{rootActorId}:{sessionId}`(第 119-120 行)。`PublishAsync`(第 38-61 行)/`SubscribeAsync`(第 67-117 行)。

---

## 验收

1. canonical 和 derived projector 区别?(canonical = 权威当前态副本;derived = 派生非权威)
2. Timeline/Graph 还有独立 projector 吗?(没有,从 InsightReport artifact 派生)
3. AGUI 映射谁做?(`EventEnvelopeToWorkflowRunEventMapper`,ordered handlers)
4. LiveSink 怎么 fan-out?(ProjectionSessionEventHub,按 RootActorId+SessionId key)

⟦AI:AUTO-LOOP⟧
