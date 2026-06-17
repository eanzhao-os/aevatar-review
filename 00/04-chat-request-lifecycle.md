# 主线全景图:一次 chat 请求怎么流过整个系统

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## 这张图解决什么

这是全书的「地图」。读者读完应该能回答一个问题:**「我想看 X,应该去哪个文件?」**。

aevatar 把一次 chat 请求的生命周期切成了清晰的层:Host(API 协议出口)→ Application(编排)→ Core(definition/run actor + 执行内核)→ AI(role actor + LLM)→ CQRS Projection(读侧)。每一层的职责、为什么这么分、代码落在哪,都在下面这张图和表里。

> **为什么这么分层** —— 这是这张图最该讲清楚的。`architecture` 把核心主链路总结成五步,这张图就是那五步在一个具体请求上的实例化。

---

## 端到端时序图

```mermaid
sequenceDiagram
    participant User
    participant API as ChatAPI<br/>(Mainnet/Workflow Host)
    participant App as WorkflowChatRunInteractionService<br/>(Application 层)
    participant WF as WorkflowGAgent<br/>(definition actor)
    participant Run as WorkflowRunGAgent<br/>(run actor)
    participant Kernel as WorkflowExecutionKernel<br/>(run actor 内主循环)
    participant Role as RoleGAgent<br/>(AI role actor)
    participant LLM
    participant Store as EventStore<br/>(StateEvent 事实层)
    participant Proj as Projection<br/>(CQRS 读侧)

    User->>API: POST /api/chat {prompt, workflow}
    API->>App: ExecuteAsync(request)
    App->>App: WorkflowChatRequestEnvelopeFactory 组装 envelope
    App->>WF: 解析 YAML / 复用 definition actor(按 workflow 名寻址)
    WF-->>App: definition 就绪(已编译)
    App->>Run: 派生 run actor(一次 run 一个,runId 服务端生成)
    Run->>Role: 按 roles 创建 run-scoped 子 actor
    App->>Run: ChatRequestEvent(进 actor inbox)

    Note over Run,Kernel: WorkflowExecutionKernel 主循环
    Run->>Kernel: StartWorkflowEvent 初始化 run state
    Kernel->>Kernel: 选入口 step → dispatch

    rect rgb(240, 248, 255)
        Note over Kernel,Role: 逐 step(llm_call / tool_call / parallel / vote / ...)
        Kernel->>Role: llm_call → ChatRequestEvent
        Role->>LLM: ChatStreamAsync(流式)
        LLM-->>Role: tokens
        Role-->>Kernel: StepCompletedEvent
        Kernel->>Store: PersistDomainEventAsync(显式持久化领域事件)
        Kernel->>Kernel: Apply reducer 更新 run state(TransitionState)
        Kernel->>Proj: 同一 envelope 流投影(CommittedFacts observer)
    end

    Run-->>App: WorkflowCompletedEvent
    App->>Proj: 投影同一 envelope 流 → ReadModel + 实时 SSE
    Proj-->>User: SSE 流(RUN_STARTED → STEP_* → TEXT_MESSAGE_* → USAGE → RUN_FINISHED)
```

---

## 每个箭头:发生了什么 / 业务含义 / 代码落点 / 继续阅读

| 箭头 | 发生了什么 / 业务含义 | 代码落点 | 继续阅读 |
|---|---|---|---|
| `User → API: POST /api/chat` | HTTP SSE 入口;协议见 canon | `01/02-chat-api-and-sse.md` |
| `API → App: ExecuteAsync` | HTTP 层只做协议出口,把请求交给 Application 编排 | `WorkflowChatRunInteractionService` | `01/03-run-semantics.md` |
| `App 组装 envelope` | 把 prompt/workflow/source 组装成发给 actor 的 `EventEnvelope` | `WorkflowChatRequestEnvelopeFactory` | `03/02-event-envelope-vs-state-event.md` |
| `App → WF: definition` | 按 workflow 名寻址/创建 definition actor,复用已编译的 YAML | `02/02-definition-and-run-actors.md` |
| `App → Run: 派生 run actor` | 一次运行一个 run actor,`runId` 服务端生成 | `01/03-run-semantics.md` |
| `Run → Role: 创建子 actor` | 按 `roles` 创建 run-scoped role actor(AI 身份 + 能力授权) | `04/01-role-gagent.md` |
| `App → Run: ChatRequestEvent` | 请求进入 run actor 的 inbox(Actor 邮箱串行) | `WorkflowRunGAgent`(ChatRequestEvent handler) | `03/01-agent-actor-runtime.md` |
| `Run → Kernel: StartWorkflow` | 执行内核初始化 run state、写 input 变量、选入口 step | `02/03-execution-kernel.md` |
| `Kernel → Role: llm_call` | 把 `llm_call` 步骤派给 role actor,包成 `ChatRequestEvent` | `RoleGAgent`(ChatRequestEvent handler) | `02/04-step-modules-catalog.md` |
| `Role → LLM: ChatStreamAsync` | role actor 流式调 LLM Provider(MEAI/NyxId/Tornado) | `RoleGAgent`(ChatStreamAsync) | `04/02-llm-providers.md` |
| `LLM → Role: tokens` | LLM 流式回 token;role 发 `TextMessageStart → Content* → End` | `RoleGAgent`(注释说明 AG-UI 事件序列) | `04/01-role-gagent.md` |
| `Role → Kernel: StepCompletedEvent` | 步骤完成事件回到 run actor;内核推进到下一步 | `WorkflowRunGAgent`(`On<StepCompletedEvent>`)、`(`ApplyStepCompleted` reducer) | `02/03-execution-kernel.md` |
| `Kernel → Store: PersistDomainEventAsync` | **只有显式持久化后**,领域事件才进 EventStore 成为事实 | `GAgentBase`(PersistDomainEventAsync);`architecture` | `03/04-state-guard-and-event-sourcing.md` |
| `Kernel → Proj: 投影` | 同一条 committed envelope 流被投影为多个分支(SSE/报告/ReadModel) | `architecture`、` | `05/01-projection-overview.md` |
| `Run → App: WorkflowCompletedEvent` | run 收敛,通知 Application | `WorkflowRunGAgent` | `01/03-run-semantics.md` |
| `Proj → User: SSE 流` | 投影产出实时 SSE 帧 + 物化 ReadModel | `ChatSseResponseWriter`;`WorkflowRunEventTypes` | `00/03-quick-start.md`、`05/02-two-projection-modes.md` |

---

## 为什么这么分层(对应核心主链路五步)

`architecture` 把框架主线总结成五步,这张图是它的实例化:

1. **统一消息传输契约**(`architecture.md`):外部 command、内部 signal、reply、业务事件,都以 `EventEnvelope.payload` 形式进入 Actor 消息流。图里 `ChatRequestEvent`、`StepCompletedEvent`、`WorkflowCompletedEvent` 都是 envelope payload。
2. **Runtime 赋予 Actor 语义**(`architecture.md`):`IActorRuntime` / `IActor` 在 Stream 之上提供创建、寻址、激活、邮箱串行、父子拓扑;`IActorDispatchPort` 负责定向投递。图里 run actor → role actor 是父子拓扑。
3. **统一路由执行**(`architecture.md`):`PublishAsync` / `SendToAsync` 构造 `PublicationRoute.topology` 或 `DirectRoute`;`GAgentBase` 合并静态 `[EventHandler]` 与动态 `IEventModule`。图里 Kernel 推进步骤就是这条。
4. **领域事实显式持久化**(`architecture.md`):有状态 Actor **只有**调用 `PersistDomainEventAsync(...)` 后,领域事件才进 `EventStore`。这是 EventEnvelope(运行时消息)和 StateEvent(事实层)的分界 —— `03/02-event-envelope-vs-state-event.md` 专门讲这条最容易踩的边界。
5. **统一读侧投影**(`architecture.md`):同一条 Actor envelope 流被投影成多个输出分支。图里 SSE 流、运行报告、ReadModel 共享同一投影输入 —— 这是 aevatar 区别于普通 Agent 框架的关键设计,`05/02-two-projection-modes.md` 展开。

---

## 最容易误解的两个边界(后续专门讲)

读这张图时,这两个地方最容易踩坑,先标记出来:

1. **EventEnvelope ≠ StateEvent**(`architecture.md`):图里 actor 之间流动的 `ChatRequestEvent` / `StepCompletedEvent` 是运行时消息(envelope),不是事件溯源的事实。事实层是 `StateEvent` + `EventStore`,只有 `PersistDomainEventAsync` 后才进入。→ `03/02-event-envelope-vs-state-event.md`

2. **SSE 流是投影,不是 State 直射**(`architecture.md`):`Proj → User: SSE 流` 这条线是 workflow run-event 事件投影,不是把写侧 `State` 直接映射到前端。写侧 State 是运行态;读侧建议由投影生成独立只读模型(CQRS)。→ `05/02-two-projection-modes.md`

---

## 怎么用这张图

- **想跑起来看一遍** → `00/03-quick-start.md`
- **想看 API 协议细节** → `01/02-chat-api-and-sse.md`
- **想写 workflow** → `02/01-yaml-grammar.md` → `02/03-execution-kernel.md`
- **想理解 Actor/Event 内核** → `03/01-agent-actor-runtime.md` → `03/02-event-envelope-vs-state-event.md`
- **想理解读侧投影** → `05/01-projection-overview.md` → `05/02-two-projection-modes.md`

⟦AI:AUTO-LOOP⟧
