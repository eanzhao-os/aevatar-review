# 解读计划与进度

> 自顶向下、以源码为准、配 demo。每篇对应一个可独立阅读的章节,落点明确到文件。
> 状态图例:⬜ 待写 / 🔄 进行中 / ✅ 已完成

---

## 写作原则

1. **自顶向下**:先讲"一次请求怎么流过去",再逐层下钻。读者可以随时停在任何一层。
2. **以源码为准**:每篇开头列「关键代码」清单(文件路径 + 行号锚点),论断都指向真实代码或 `docs/canon/*`。
3. **配 demo**:每个关键概念都给最小可读/可跑示例(优先用 `workflows/` 和 `demos/` 仓库自带的)。
4. **说清楚边界**:重点讲 aevatar 区别于"普通 Agent 框架"的设计取舍(Actor + ES + CQRS),而不只是 API 用法。
5. **诚实标注**:对仓库里标 "当前实现 vs 目标态" 的部分(见 README 表格),按代码事实描述,不脑补未来。

---

## 总览:5 大块 + 周边

```
00 序章 ─────────── 定位 / 主线 / 怎么跑
01 宿主与入口 ────── Host / API / SSE-WS
02 编排层(Workflow) ── YAML + 步骤模块 + Maker
03 运行内核(Foundation) Actor / Event / State
04 AI 能力层 ──────── RoleGAgent / LLM / Tool
05 CQRS 与读侧 ────── 投影 / ReadModel
06 分布式与生产态 ──── Orleans / Garnet / Kafka
07 周边 ──────────── Channel / A2A / Voice / 前端
```

---

## 章节清单

### 00 · 序章

- ⬜ `00/01-what-is-aevatar.md` — Aevatar 是什么、解决什么问题、与 LangGraph/AutoGen 等的区别定位
- ⬜ `00/02-repo-map.md` — 仓库地图:`aevatar.slnx` + 10 个 `*.slnf` 怎么切的、`src/` ~80 个项目的分层归属(对照 `docs/canon/module-placement-map.md`)
- ⬜ `00/03-quick-start.md` — 从零跑起来:配 Key → 起 Mainnet → `simple_qa` → 看 SSE + 看 `artifacts/` 报告
- ✅ `00/00-readme-and-plan.md` — 即本 README + PLAN(已完成)

### 01 · 宿主与入口

- ⬜ `01/01-hosts-and-composition.md` — `Mainnet.Host.Api` vs `Workflow.Host.Api` 的边界;`AddAevatarMainnetHost` / `AddAevatarPlatform(EnableMakerExtensions)` 的组合过程
  - 关键代码:`src/Aevatar.Mainnet.Host.Api/Program.cs`、`src/Aevatar.Bootstrap/*`、`docs/canon/overview.md §3`
- ⬜ `01/02-chat-api-and-sse.md` — `POST /api/chat` 协议、请求体(`prompt/workflow/agentId`)、SSE 帧类型(`RUN_STARTED`/步骤完成/消息片段/`RUN_FINISHED`)、`/v1/responses` 与软废弃的 `streaming-proxy` route
  - 关键代码:`docs/canon/chat-api.md`、`docs/canon/llm-streaming.md`、`README.md` 关于 Sunset 的说明
- ⬜ `01/03-run-semantics.md` — Run 语义:`runId/sessionId` 服务端生成、不按 run 隔离事件流、终止事件收敛、`StartWorkflowEvent` 投影
  - 关键代码:README §"Run 语义"、`src/workflow/Aevatar.Workflow.Application/*`

### 02 · 编排层(Workflow)★ 重点

- ⬜ `02/01-yaml-grammar.md` — Workflow YAML 完整语法:`name/roles/steps/routes`、角色定义、`steps[].type` 取值全表(对照 README 表格 + canon)
  - 关键代码:`src/workflow/Aevatar.Workflow.Core/Primitives/*`、`docs/canon/workflow-primitives.md`
- ⬜ `02/02-definition-and-run-actors.md` — `WorkflowGAgent`(definition actor,只持有 YAML + 编译结果)vs `WorkflowRunGAgent`(run actor,1779 行,持有全部执行事实)的职责切分
  - 关键代码:`WorkflowGAgent.cs`、`WorkflowRunGAgent.cs`、`Aevatar.Workflow.Core/README.md`
- ⬜ `02/03-execution-kernel.md` — `WorkflowExecutionKernel` 主循环:current step / variables / retry / timeout 全部在 actor-owned execution state;模块状态通过 `LoadState/SaveState` 落到 `WorkflowRunState.ExecutionStates`
- ⬜ `02/04-step-modules-catalog.md` ★ — 30+ 步骤模块全图:`workflow_loop`/`llm_call`/`tool_call`/`connector_call`/`parallel`/`switch`/`while`/`vote`/`human_approval`/`wait_signal`/`assign`/`transform`/`reflect`...,每个配最小 YAML 片段
  - 关键代码:`src/workflow/Aevatar.Workflow.Core/Modules/*.cs`(逐文件)
- ⬜ `02/05-workflows-walkthrough.md` — 逐个拆 `workflows/` 下 12 个示例(`simple_qa` / `resume_screening` / `invoice_ocr_approval` / `lark_approval_wait` / `petty_cash_approval` / `codex_long_running_handoff` / ...)
- ⬜ `02/06-maker-plugin.md` — Maker 插件边界:`maker_recursive` + `maker_vote`,为什么从"独立 Host"降级成"Workflow 插件",`IWorkflowModulePack` 注册体系,架构门禁为什么禁止 Workflow→Maker 反向依赖
  - 关键代码:`src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/`、`demos/Aevatar.Demos.Maker/`、`docs/canon/overview.md §4`、`docs/adr/0006-multi-agent-evolution.md`
- ⬜ `02/07-connectors.md` — Connector(HTTP/CLI/MCP)配置与 `connector_call` 执行;role connector allowlist
  - 关键代码:`docs/canon/connector.md`、`docs/canon/role-model.md`、`src/Aevatar.Configuration/README.md`

### 03 · 运行内核(Foundation)★ 重点

- ⬜ `03/01-agent-actor-runtime.md` — 核心概念辨析:Agent(业务逻辑)/ Actor(运行容器)/ Runtime(Stream 之上的 Actor 语义层)/ Stream(`EventEnvelope` 传输骨架)
  - 关键代码:`src/Aevatar.Foundation.Abstractions/*`、`docs/canon/architecture.md §核心概念`
- ⬜ `03/02-event-envelope-vs-state-event.md` ★ — 最容易被混淆的边界:**`EventEnvelope` 是 runtime message envelope(命令/signal/reply/事件都装这里),`StateEvent` + `EventStore` 才是 Event Sourcing 的事实层**。两者关联但不是一回事。
- ⬜ `03/03-gagent-base.md` — `GAgentBase` / `GAgentBase<TState>` / `GAgentBase<TState,TConfig>` 的统一事件 pipeline:静态 `[EventHandler]` + 动态 `IEventModule<IEventHandlerContext>` 按 Priority 合并、双 Hook 通道
  - 关键代码:`src/Aevatar.Foundation.Core/GAgentBase.cs`、`EventPipelineBuilder`、`docs/canon/architecture.md §Foundation.Core`
- ⬜ `03/04-state-guard-and-event-sourcing.md` — `StateGuard`(`AsyncLocal` 限制状态只在事件处理期写)、`PersistDomainEventAsync`、`TransitionState` reducer、latest-wins `RunManager`
- ⬜ `03/05-routing-and-topology.md` — 拓扑事实收口到 runtime actor 自身(Local 的 `LocalActor` / Orleans 的 `RuntimeActorGrainState`);`DirectRoute` vs `PublicationRoute.topology` vs `PublicationRoute.observer`(只给 projection/live sink)
- ⬜ `03/06-local-runtime-deep-dive.md` — `LocalActorRuntime` / `LocalActor`(邮箱串行)/ `LocalActorPublisher` 的实现,为什么 InMemory 仅限开发测试

### 04 · AI 能力层

- ⬜ `04/01-role-gagent.md` — `RoleGAgent` 处理 `ChatRequestEvent`:流式调 LLM、发 AG-UI 事件(`TextMessageStart`→`Content*`→`ToolCall*`→`End`)、role identity 是 typed actor-owned fact
  - 关键代码:`src/Aevatar.AI.Core/RoleGAgent.cs`
- ⬜ `04/02-llm-providers.md` — Provider 抽象与实现:MEAI / NyxId / Tornado,`ILLMProviderFactory`
- ⬜ `04/03-tool-providers.md` ★ — 工具体系:ToolApprovalHandler(`YieldApprovalHandler` + 远程升级)、20+ ToolProvider(MCP / Skills / Lark / Web / Telegram / Ornn / Channel / Scripting ...),tool allowlist
  - 关键代码:`src/Aevatar.AI.ToolProviders.*`
- ⬜ `04/04-chat-runtime-and-middleware.md` — `ChatRuntime` / ToolLoop / 中间件管线(`IAgentRunMiddleware` / `IToolCallMiddleware` / `ILLMCallMiddleware`)、可观测性

### 05 · CQRS 与读侧 ★ 重点

- ⬜ `05/01-projection-overview.md` — 统一链路:`Command → EventEnvelope → Actor 决策 → 持久化领域事件 → Projection 消费 → ReadModel`;为什么 API 推送(SSE/WS/AGUI)和 CQRS 读模型共享同一条投影输入
- ⬜ `05/02-two-projection-modes.md` ★ — 两条主链:**Durable Materialization**(scope actor,只消费 committed observation)+ **Session Observation**(发布 session event stream,不做生命周期事实);scope actor 是唯一运行态事实源,host 侧只留薄适配
  - 关键代码:`src/Aevatar.CQRS.Projection.Core/README.md`、`Orchestration/*`
- ⬜ `05/03-readmodel-providers.md` — InMemory(默认)/ Elasticsearch / Neo4j / StateMirror 几种读模型存储,生产怎么换
- ⬜ `05/04-workflow-projection.md` — Workflow 专属:`WorkflowExecutionCurrentStateProjector`(canonical)、`WorkflowRunInsightReport/Timeline/Graph ArtifactProjector`(derived durable)、AGUI 事件映射

### 06 · 分布式与生产态

- ⬜ `06/01-current-vs-target.md` — 诚实对比表(README 那张表的展开):ActorRuntime Provider / Orleans Transport / Projection 并发 / LiveSink / ReadModel 存储的"当前实现 vs 目标态"
- ⬜ `06/02-orleans-runtime.md` — `Aevatar.Foundation.Runtime.Implementations.Orleans*`,同一组原语(`IActorRuntime`/`IActorDispatchPort`/`IEventPublisher`)在分布式下的语义(同 actorId 全局单激活 + 邮箱串行)
- ⬜ `06/03-kafka-transport.md` — 可选 `Transport=Kafka`(MassTransit/Kafka)插件,ADR-0003 的设计
- ⬜ `06/04-garnet-clustering.md` — 生产聚类用共享 Garnet 成员资格(ADR-0032)、Garnet 持久化实现
- ⬜ `06/05-architecture-guards.md` — `tools/ci/architecture_guards.sh` / `slow_test_guards.sh` 守卫什么、为什么"禁止 Workflow→Maker 反向依赖"这类规则是 CI 强制的

### 07 · 周边

- ⬜ `07/01-channels.md` — Channel Runtime(多通道适配:Lark/Telegram/...):多 token 凭证路由(ADR-0008)、凭证边界(ADR-0012)、统一入站骨干(ADR-0013)、交互回复抽象(ADR-0014)
- ⬜ `07/02-a2a-interop.md` — `Aevatar.Interop.A2A.*`:Agent-to-Agent 互操作
- ⬜ `07/03-chat-routing.md` — `ChatRoutePolicy`(配置 Actor + 边界解析器,ADR-0024)、tool-first ingress(ADR-0026)
- ⬜ `07/04-voice-presence.md` — `Foundation.VoicePresence*`(MiniCPM / OpenAI)、语音路由(ADR-0025/0031/0033)
- ⬜ `07/05-studio-and-scripting.md` — `Aevatar.Studio.*`(member-first / team-first 聚合,ADR-0016/0017)、`Aevatar.Scripting.*`
- ⬜ `07/06-console-web.md` — 前端控制台 `apps/aevatar-console-web`:技术栈、与后端 SSE 的对接
- ⬜ `07/07-observability.md` — OTel 语义约定 `aevatar.*`(ADR-0022)、两级 Inspector(ADR-0023)、`/status` 面板

### 08 · 附录

- ⬜ `08/01-glossary.md` — 术语表(对照 `docs/canon/architecture-vocabulary.md`)
- ⬜ `08/02-doc-index.md` — 把 aevatar 仓库 `docs/canon` + `docs/adr` 的索引搬过来并加导读(不复制全文)
- ⬜ `08/03-demo-cookbook.md` — 可复现 demo 合集:Maker sample、CaseProjection、Workflow.Web、Cli、Inspector

---

## 进度看板

| 大块 | 篇数 | 完成 | 状态 |
|---|---|---|---|
| 00 序章 | 4 | 1 | 🔄 |
| 01 宿主与入口 | 3 | 0 | ⬜ |
| 02 编排层 | 7 | 0 | ⬜ |
| 03 内核 | 6 | 0 | ⬜ |
| 04 AI 层 | 4 | 0 | ⬜ |
| 05 CQRS 读侧 | 4 | 0 | ⬜ |
| 06 分布式 | 5 | 0 | ⬜ |
| 07 周边 | 7 | 0 | ⬜ |
| 08 附录 | 3 | 0 | ⬜ |
| **合计** | **43** | **1** | |

> 更新约定:每完成一篇,把对应行的 ⬜ 改成 ✅,并更新看板数字。

---

## 写作顺序建议

不严格按编号写,而是按"读者价值"优先级:

1. **第一批(立主线)**:`00/03-quick-start` → `01/02-chat-api-and-sse` → `03/02-event-envelope-vs-state-event` → `05/02-two-projection-modes`
   把"请求怎么流过去 + 两个最容易误解的概念"先讲清楚。
2. **第二批(讲编排)**:`02/01-yaml-grammar` → `02/04-step-modules-catalog` → `02/05-workflows-walkthrough` → `02/06-maker-plugin`
   这是 aevatar 最有特色、最实用的部分。
3. **第三批(下钻内核)**:`03/03-gagent-base` → `03/04-state-guard-and-event-sourcing` → `03/05-routing-and-topology`
4. **其余**:按需推进,AI 层 / 分布式 / 周边。
