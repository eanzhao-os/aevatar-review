# POST /api/chat 协议、SSE 帧类型、/v1/responses 与软废弃 streaming-proxy

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `docs/canon/chat-api.md` 第 19-39 行:端点清单;第 41-69 行:请求体字段 + 选择优先级;第 109-135 行:auto 编排路由;第 191-209 行:SSE 输出事件清单 + CUSTOM 子类型。
- `docs/canon/llm-streaming.md` 第 46-71 行:组件分层;第 163-170 行:SSE 路径代码锚点;第 199-205 行:WebSocket 锚点;第 280-297 行:会话语义表;第 314-361 行:事件模型;第 371-383 行:收敛与终止。
- `docs/canon/llm-streaming.md` 第 416-424 行:`WorkflowRunEventTypes` 是唯一共享常量源。
- `src/workflow/Aevatar.Workflow.Application.Abstractions/Runs/WorkflowRunEventTypes.cs` 第 3-19 行:14 个事件类型常量(SSOT);第 20-42 行:`GetEventType` 映射。
- `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/ChatEndpoints.cs` 第 44 行:`POST /api/chat` SSE 入口;第 152 行:WebSocket 入口。
- `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/ChatSseResponseWriter.cs` 第 45 行:SSE writer。
- `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/ChatWebSocketProtocol.cs` 第 16 行、`ChatWebSocketCommandParser.cs` 第 20 行、`ChatWebSocketRunCoordinator.cs` 第 22 行:WS 协议栈。
- `docs/2026-04-02-streaming-proxy-flow.md` 第 5 行、第 55 行、第 277-291 行:streaming-proxy 软废弃 + Sunset 日期 + 旧 SSE 帧。
- `agents/Aevatar.GAgents.StreamingProxy/StreamingProxyEndpoints.cs` 第 21-28 行:Sunset/Deprecation/Link 常量;第 37-41 行、第 72-77 行:废弃 header 注入。
- `src/Aevatar.Mainnet.Host.Api/Responses/ResponsesEndpoints.cs` 第 30 行、第 39-40 行、第 163/191/222/287/469 行:`/v1/responses` 端点 + 新 SSE 事件。

---

## POST /api/chat 协议

入口见 `docs/canon/chat-api.md` 第 19-39 行:

| 端点 | 传输 | 用途 |
|---|---|---|
| `POST /api/chat` | HTTP + SSE | 请求 + 运行事件 envelope 投影流 |
| `GET /api/ws/chat` | WebSocket | 同等能力,WS 版 |
| `POST /api/workflow-webhooks/{routeKey}` | HTTP | 外部 webhook → 新 run(`202 Accepted`) |
| `POST /api/workflows/resume` | HTTP | 恢复 `human_input` / `human_approval` |
| `POST /api/workflows/signal` | HTTP | 给 `wait_signal` 步骤发信号 |

### 请求体字段(`chat-api.md` 第 41-69 行)

```json
{
  "prompt": "必填",
  "workflow": "可选,已注册的 workflow 名",
  "source": {
    "kind": "definition_actor",
    "definitionActor": { "actorId": "..." }
  },
  "workflowYamls": ["可选,内联 YAML bundle"]
}
```

**选择优先级**(`chat-api.md` 第 55-61 行):`workflowYamls` > `workflow` > 全空时默认路由 `auto` > `source.definitionActor.actorId`(复用已绑定 actor)。

> 注意:canon 请求体**没有**顶层 `agentId` 字段。agent 身份只通过 typed `source.definitionActor.actorId` 或 `source.inlineBundle.actorId` 传递(`chat-api.md` 第 66 行)。

内置 workflow 路由(`chat-api.md` 第 109-135 行):`direct`(直连 actor)、`auto`(分类 → 校验 → human_approval → dynamic_workflow)、`auto_review`(同 auto 但只 finalize 不自动执行)。

---

## SSE 帧类型完整对照表

事件类型常量在 `src/workflow/Aevatar.Workflow.Application.Abstractions/Runs/WorkflowRunEventTypes.cs` 第 3-19 行,这是 SSOT。`GetEventType`(第 20-42 行)把 proto `WorkflowRunEventEnvelope.EventOneofCase` 一一映射。

| 帧名 | 常量行号 | 触发时机 | 关键 payload 字段 |
|---|---|---|---|
| `RUN_STARTED` | 第 5 行 | `StartWorkflowEvent` 投影生成(`llm-streaming.md` 第 421 行) | `runId`、`threadId`(=发布 actor 的 ActorId)、`workflowName` |
| `RUN_FINISHED` | 第 6 行 | `WorkflowCompletedEvent(success=true)` 投影(`llm-streaming.md` 第 465-523 行) | `runId`、`threadId`、`result.output` |
| `RUN_ERROR` | 第 7 行 | `WorkflowCompletedEvent(success=false)` 投影 | `runId`、code `"WORKFLOW_FAILED"` |
| `RUN_STOPPED` | 第 8 行 | `WorkflowStoppedEvent` 投影 | `runId` |
| `STEP_STARTED` | 第 9 行 | 步骤开始 | `stepId`、`stepType`、`role` |
| `STEP_FINISHED` | 第 10 行 | 步骤完成 | `stepId`、`stepType`、`success` |
| `TEXT_MESSAGE_START` | 第 11 行 | LLM 流式输出开始 | `role`、`messageId` |
| `TEXT_MESSAGE_CONTENT` | 第 12 行 | LLM 每个 token 片段 | `role`、`delta` |
| `TEXT_MESSAGE_END` | 第 13 行 | LLM 输出结束 | `role`、`messageId` |
| `STATE_SNAPSHOT` | 第 14 行 | run 收敛后由 `WorkflowRunFinalizeEmitter` 发出(`llm-streaming.md` 第 420 行) | `actorId`、`commandId`、`projectionCompletion*` |
| `TOOL_CALL_START` | 第 15 行 | 工具调用开始 | `toolName`、`callId` |
| `TOOL_CALL_END` | 第 16 行 | 工具调用结束 | `callId`、`result` |
| `USAGE` | 第 17 行 | `WorkflowCompletedEvent` 前发一次用量帧 | `promptTokens`/`completionTokens`/`totalTokens`/`model`/`cost`/`latencyMs` |
| `CUSTOM` | 第 18 行 | 扩展子类型载体 | `eventType`(见下) |

**CUSTOM 子类型**(`chat-api.md` 第 203-209 行):`aevatar.run.context`、`aevatar.step.request`、`aevatar.step.completed`、`aevatar.llm.reasoning`、`aevatar.media.chunk`(payload `MediaContentEvent`)、`aevatar.workflow.waiting_signal`。

> `chat-api.md` 第 198 行列了 `HUMAN_INPUT_REQUEST`,但它在 `WorkflowRunEventTypes` 里**没有**独立常量 —— 在统一事件模型里通过 `CUSTOM` 子类型(`aevatar.step.request` / `aevatar.workflow.waiting_signal`)表达。把它当投影流里的遗留/规范名称,不是 proto oneof case。

### WebSocket 帧协议(`chat-api.md` 第 211-239 行)

客户端发:`{ "type": "chat.command", "requestId": "...", "payload": { "inputParts": [...] } }`。
服务端依次回:`command.ack`(返回 `commandId` / `actorId` / `workflow`)→ 若干 `agui.event`(每帧一个 `WorkflowRunEventEnvelope` JSON)→ `command.error`(出错时)。文本帧和二进制帧都支持,回复帧类型匹配入站。

---

## streaming-proxy 软废弃 + /v1/responses 迁移

### Sunset 语义(`docs/2026-04-02-streaming-proxy-flow.md` 第 5、55 行)

streaming-proxy route 保留向后兼容,但已**软废弃**:

- **Sunset 日期**:`Wed, 25 Nov 2026 00:00:00 GMT`
- 每个 response 带:`Deprecation: true`、`Sunset: Wed, 25 Nov 2026 00:00:00 GMT`、`Link: </v1/responses>; rel="successive-version"`

代码常量在 `StreamingProxyEndpoints.cs` 第 21-28 行;`AddDeprecationHeaders`(第 72-77 行)对整个 route group 注入这三个 header(第 37-41 行的 filter)。

### 旧 streaming-proxy 帧(不等价于新接口)

`docs/2026-04-02-streaming-proxy-flow.md` 第 277-291 行的旧帧:`TOPIC_STARTED`、`AGENT_MESSAGE`、`PARTICIPANT_JOINED`、`PARTICIPANT_LEFT`、`RUN_FINISHED`、`RUN_ERROR`。这些是 room/fan-out/participant 语义,与新接口**没有一一对应**。

### /v1/responses(替代)

`src/Aevatar.Mainnet.Host.Api/Responses/ResponsesEndpoints.cs` 第 30 行 `MapResponsesApiEndpoints` 映射:
- `POST /responses`(第 39 行)、`POST /responses/{id}/cancel`(第 40 行)

新 SSE 事件类型:`response.created`(第 163 行)、`response.output_text.delta`(第 191 行)、`response.output_text.done`(第 222 行)、`response.completed`(第 287 行)、`response.failed`(第 469 行)。

### 迁移边界

| 语义 | streaming-proxy(旧) | /v1/responses(新) |
|---|---|---|
| 直接模型流式 / tool / continuation | 有 | **有**(直接迁移) |
| room CRUD / participant / fan-out | 有 | **无一一对应**(`docs/2026-04-02-streaming-proxy-flow.md` 第 5 行) |
| 帧类型 | `TOPIC_STARTED` / `AGENT_MESSAGE` / `PARTICIPANT_*` | `response.created` / `output_text.delta` / `output_text.done` / `response.completed` |

> `POST /api/chat`(workflow 框架层能力,见 `00/03-quick-start.md`)和 streaming-proxy 是两个不同的东西:`/api/chat` 是 workflow run 事件投影,streaming-proxy 是旧的 room-based 多端转发。别混淆。

---

## 验收

1. `POST /api/chat` 请求体有哪些字段?选择优先级?(`prompt`/`workflow`/`source`/`workflowYamls`,`chat-api.md` 第 41-69 行)
2. `TEXT_MESSAGE_CONTENT` 前后是什么帧?(`TEXT_MESSAGE_START` → `CONTENT`×N → `END`,`WorkflowRunEventTypes.cs` 第 11-13 行)
3. streaming-proxy 的 Sunset 日期?(2026-11-25,`StreamingProxyEndpoints.cs` 第 21-28 行)
4. streaming-proxy 的 room/participant 语义在新接口有一一对应吗?(没有,`docs/2026-04-02-streaming-proxy-flow.md` 第 5 行)

⟦AI:AUTO-LOOP⟧
