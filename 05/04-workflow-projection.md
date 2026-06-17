# Workflow 专属投影:CurrentState canonical + Insight/Timeline/Graph Artifact + AGUI 映射

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## canonical vs derived

workflow projection 有两类 projector(`ServiceCollectionExtensions` ):

| Projector | 类型 | 文件 | 说明 |
|---|---|---|---|
| `WorkflowExecutionCurrentStateProjector` | **canonical current-state** | ` | `WorkflowRunState → WorkflowExecutionCurrentStateDocument` 的权威当前态副本 |
| `WorkflowRunInsightReportArtifactProjector` | **derived artifact** | ` | upsert InsightReport document + graph |
| `WorkflowCatalogCurrentStateProjector` | current-state | ` | workflow binding 当前态 |
| `WorkflowActorBindingProjector` | artifact | ` | binding artifact |

> ⚠️ **Timeline/Graph 不再有独立 projector 类**。重构 `416108d7a` 删除了 `WorkflowRunTimelineArtifactProjector`/`WorkflowRunGraphArtifactProjector`(canon 文档引用已过期)。现在 timeline/graph 从单一 `WorkflowRunInsightReportDocument` artifact **派生**:`WorkflowRunGraphArtifactMaterializer.Materialize(report)`(`WorkflowRunGraphArtifactMaterializer.cs,16-26`)。

---

## AGUI 事件映射

`EventEnvelopeToWorkflowRunEventMapper`(`EventEnvelopeToWorkflowRunEventMapper` )用 ordered handlers 把领域事件映射成 AGUI `WorkflowRunEventEnvelope`:

| Handler | 领域事件 → AGUI | 行号 |
|---|---|---|
| `StartWorkflowRunEventEnvelopeMappingHandler` | `StartWorkflowEvent` → `RunStarted` | |
| `StepRequestRunEventEnvelopeMappingHandler` | → `StepStarted` + `aevatar.step.request` | |
| `StepCompletedRunEventEnvelopeMappingHandler` | → `StepFinished` + `aevatar.step.completed` | |
| `AITextStreamRunEventEnvelopeMappingHandler` | → `TextMessageStart/Content/End`、`MediaContent`、`ChatResponse`、`Usage` | |
| `WorkflowCompletedRunEventEnvelopeMappingHandler` | → `RunFinished` / `RunError` | |
| `ToolCallRunEventEnvelopeMappingHandler` | → `ToolCallStart` / `ToolCallEnd` | |
| `WorkflowSuspendedRunEventEnvelopeMappingHandler` | → `aevatar.tool_approval.pending` / `aevatar.human_input.request` | |

`WorkflowExecutionRunEventProjector`(`WorkflowExecutionRunEventProjector` )是 session projector,跑这个 mapper 并 publish 到 `ProjectionSessionEventHub`(pin stream 到 `context.SessionId`,缺失时 fail-closed)。

---

## LiveSink fan-out

`ProjectionSessionEventHub`(`ProjectionSessionEventHub` ):按 `RootActorId + SessionId` key 的 stream fan-out 到 live sinks。stream id 格式 `{channel}:{rootActorId}:{sessionId}`()。`PublishAsync`()/`SubscribeAsync`()。

---

## 验收

1. canonical 和 derived projector 区别?(canonical = 权威当前态副本;derived = 派生非权威)
2. Timeline/Graph 还有独立 projector 吗?(没有,从 InsightReport artifact 派生)
3. AGUI 映射谁做?(`EventEnvelopeToWorkflowRunEventMapper`,ordered handlers)
4. LiveSink 怎么 fan-out?(ProjectionSessionEventHub,按 RootActorId+SessionId key)

⟦AI:AUTO-LOOP⟧
