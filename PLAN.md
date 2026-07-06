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
08 附录 ──────────── 术语表 / 索引 / cookbook
09 方案区 ────────── 跨仓库设计与落地方案
10 已知问题 ──────── 运行态与环境已知缺陷
11 Skills 能力层 ─── 控制面与平台 fallback
12 问题复盘 ──────── 按周归档的问题复盘
```

---

## 章节清单

说明：反引号路径表示当前已经产出的章节，会被 `scripts/check-md.sh` 纳入校验。

### 00 · 序章

- ✅ `00/01-what-is-aevatar.md` — Aevatar 是什么、解决什么问题、与 LangGraph/AutoGen 等的区别定位
- ✅ `00/02-repo-map.md` — 仓库地图:`aevatar.slnx` + 当前 9 个 `aevatar.*.slnf` 怎么切、`src/` 下 98 个 `.csproj` 的分层归属(对照 `docs/canon/module-placement-map.md`)
- ✅ `00/03-quick-start.md` — 从零跑起来:配 Key → 起 Mainnet → `simple_qa` → 看 SSE + 看 `artifacts/` 报告
- ✅ `00/04-chat-request-lifecycle.md` — 主线全景图: 一次 `POST /api/chat` 请求的生命周期与全链路追踪
- ✅ 00/00-readme-and-plan.md — 即本 README + PLAN(已完成；不是独立章节文件)

### 01 · 宿主与入口

- ✅ `01/01-hosts-and-composition.md` — `Mainnet.Host.Api` vs `Workflow.Host.Api` 的边界;`AddAevatarMainnetHost` / `AddAevatarPlatform(EnableMakerExtensions)` 的组合过程
  - 关键代码:`src/Aevatar.Mainnet.Host.Api/Program.cs`、`src/Aevatar.Bootstrap/*`、`docs/canon/overview.md §3`
- ✅ `01/02-chat-api-and-sse.md` — `POST /api/chat` 协议、请求体(`prompt/workflow/agentId`)、SSE 帧类型(`RUN_STARTED`/步骤完成/消息片段/`RUN_FINISHED`)、`/v1/responses` 与软废弃的 `streaming-proxy` route
  - 关键代码:`docs/canon/chat-api.md`、`docs/canon/llm-streaming.md`、`README.md` 关于 Sunset 的说明
- ✅ `01/03-run-semantics.md` — Run 语义:`runId/sessionId` 服务端生成、不按 run 隔离事件流、终止事件收敛、`StartWorkflowEvent` 投影
  - 关键代码:README §"Run 语义"、`src/workflow/Aevatar.Workflow.Application/*`
- ✅ `01/04-platform-audit-trail.md` — 平台 Audit Trail:append-only governance artifact、`/api/audit/trail` 查询、actor resolution、endpoint/tool/projection 三采集面与自动告警边界
  - 事实源脊柱:`docs/canon/audit-trail.md`、`src/Aevatar.Audit.Hosting/AuditTrailEndpoints.cs`、`src/Aevatar.Audit.Abstractions/audit_messages.proto`

### 02 · 编排层(Workflow)★ 重点

- ✅ `02/01-yaml-grammar.md` — Workflow YAML 完整语法:`name/roles/steps/routes`、角色定义、`steps[].type` 取值全表(对照 README 表格 + canon)
  - 关键代码:`src/workflow/Aevatar.Workflow.Core/Primitives/*`、`docs/canon/workflow-primitives.md`
- ✅ `02/02-definition-and-run-actors.md` — `WorkflowGAgent`(definition actor,只持有 YAML + 编译结果)vs `WorkflowRunGAgent`(run actor,持有全部执行事实)的职责切分
  - 关键代码:`WorkflowGAgent.cs`、`WorkflowRunGAgent.cs`、`Aevatar.Workflow.Core/README.md`
- ✅ `02/03-execution-kernel.md` — `WorkflowExecutionKernel` 主循环:current step / variables / retry / timeout 全部在 actor-owned execution state;模块状态通过 `LoadState/SaveState` 落到 `WorkflowRunState.ExecutionStates`
- ✅ `02/04-step-modules-catalog.md` ★ — 30+ 步骤模块全图:每个配最小 YAML 片段
  - 关键代码:`src/workflow/Aevatar.Workflow.Core/Modules/*.cs`(逐文件)
- ✅ `02/05-workflows-walkthrough.md` — 逐个拆 `workflows/` 下 12 个示例(`simple_qa` / `resume_screening` / `invoice_ocr_approval` / `lark_approval_wait` / `petty_cash_approval` / `codex_long_running_handoff` / ...)
- ✅ `02/06-maker-plugin.md` — Maker 插件边界:`maker_recursive` + `maker_vote`,为什么从"独立 Host"降级成"Workflow 插件",`IWorkflowModulePack` 注册体系,架构门禁为什么禁止 Workflow→Maker 反向依赖
  - 关键代码:`src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/`、`demos/Aevatar.Demos.Maker/`、`docs/canon/overview.md §4`、`docs/adr/0006-multi-agent-evolution.md`
- ✅ `02/07-connectors.md` — Connector(HTTP/CLI/MCP)配置与 `connector_call` 执行;role connector allowlist
  - 关键代码:`docs/canon/connector.md`、`docs/canon/role-model.md`、`src/Aevatar.Configuration/README.md`
- ✅ `02/08-saga-durable-execution.md` — saga 补偿 + dead-letter + 持久挂起 = 长在 agent 编排上的 durable execution;两阶段账本 / `OutcomeUncertain` 跳过 / ADR-0034 漂移
  - 事实源脊柱:`src/workflow/Aevatar.Workflow.Core/workflow_state.proto`、`src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs`、`docs/adr/0034-workflow-saga-compensation-protocol.md`

### 03 · 运行内核(Foundation)★ 重点

- ✅ `03/01-agent-actor-runtime.md` — 核心概念辨析:Agent(业务逻辑)/ Actor(运行容器)/ Runtime(Stream 之上的 Actor 语义层)/ Stream(`EventEnvelope` 传输骨架)
  - 关键代码:`src/Aevatar.Foundation.Abstractions/*`、`docs/canon/architecture.md §核心概念`
- ✅ `03/02-event-envelope-vs-state-event.md` ★ — 最容易被混淆的边界:**`EventEnvelope` 是 runtime message envelope(命令/signal/reply/事件都装这里),`StateEvent` + `EventStore` 才是 Event Sourcing 的事实层**。两者关联但不是一回事。
- ✅ `03/03-gagent-base.md` — `GAgentBase` / `GAgentBase<TState>` / `GAgentBase<TState,TConfig>` 的统一事件 pipeline:静态 `[EventHandler]` + 动态 `IEventModule<IEventHandlerContext>` 按 Priority 合并、双 Hook 通道
  - 关键代码:`src/Aevatar.Foundation.Core/GAgentBase.cs`、`EventPipelineBuilder`、`docs/canon/architecture.md §Foundation.Core`
- ✅ `03/04-state-guard-and-event-sourcing.md` — `StateGuard`(`AsyncLocal` 限制状态只在事件处理期写)、`PersistDomainEventAsync`、`TransitionState` reducer、latest-wins `RunManager`
- ✅ `03/05-routing-and-topology.md` — 拓扑事实收口到 runtime actor 自身(Local 的 `LocalActor` / Orleans 的 `RuntimeActorGrainState`);`DirectRoute` vs `PublicationRoute.topology` vs `PublicationRoute.observer`(只给 projection/live sink)
- ✅ `03/06-local-runtime-deep-dive.md` — `LocalActorRuntime` / `LocalActor`(邮箱串行)/ `LocalActorPublisher` 的实现,为什么 InMemory 仅限开发测试
- ✅ `03/07-stream-actor-gagent-facts.md` — Stream × Actor × GAgent 三者关系与逐条事实清单:收口 03 块,纠正"事件都在 stream / stream 都包在 actor 里"两个常见说法
  - 事实源脊柱:`OrleansGrainEventPublisher.cs`(发布全部落 `ProduceAsync`)、`RuntimeActorGrain.cs`(订阅自身 stream)、`IRuntimeActorGrain.cs`(非事件 RPC 面)、`GAgentBase.cs`(turn 内同步处理)、`ScopeGAgentEndpoints.cs` + `ProjectionSessionEventHub.cs`(actor 外订阅 stream 的反例)
- ✅ `03/08-event-sourcing-dividends.md` — Event Sourcing 三重红利(唯一事实源 / 确定性重放 / 免费可观测性)+ `StateGuard` 写栅栏纪律
  - 事实源脊柱:`src/Aevatar.Foundation.Abstractions/Persistence/IEventStore.cs`、`src/Aevatar.Foundation.Core/StateGuard.cs`、`src/Aevatar.Foundation.Core/EventSourcing/StateEventApplierBase.cs`

### 04 · AI 能力层

- ✅ `04/01-role-gagent.md` — `RoleGAgent` 处理 `ChatRequestEvent`:流式调 LLM、发 AG-UI 事件(`TextMessageStart`→`Content*`→`ToolCall*`→`End`)、role identity 是 typed actor-owned fact
  - 关键代码:`src/Aevatar.AI.Core/RoleGAgent.cs`
- ✅ `04/02-llm-providers.md` — Provider 抽象与实现:MEAI / NyxId / Tornado,`ILLMProviderFactory`
- ✅ `04/03-tool-providers.md` ★ — 工具体系:ToolApprovalHandler(`YieldApprovalHandler` + 远程升级)、20+ ToolProvider(MCP / Skills / Lark / Web / Telegram / Ornn / Channel / Scripting ...),tool allowlist
  - 关键代码:`src/Aevatar.AI.ToolProviders.*`
- ✅ `04/04-chat-runtime-and-middleware.md` — `ChatRuntime` / ToolLoop / 中间件管线(`IAgentRunMiddleware` / `IToolCallMiddleware` / `ILLMCallMiddleware`)、可观测性

### 05 · CQRS 与读侧 ★ 重点

- ✅ `05/01-projection-overview.md` — 统一链路:`Command → EventEnvelope → Actor 决策 → 持久化领域事件 → Projection 消费 → ReadModel`;为什么 API 推送(SSE/WS/AGUI)和 CQRS 读模型共享同一条投影输入
- ✅ `05/02-two-projection-modes.md` ★ — 两条主链:**Durable Materialization**(scope actor,只消费 committed observation)+ **Session Observation**(发布 session event stream,不做生命周期事实);scope actor 是唯一运行态事实源,host 侧只留薄适配
  - 关键代码:`src/Aevatar.CQRS.Projection.Core/README.md`、`Orchestration/*`
- ✅ `05/03-readmodel-providers.md` — InMemory(默认)/ Elasticsearch / Neo4j / StateMirror 几种读模型存储,生产怎么换
- ✅ `05/04-workflow-projection.md` — Workflow 专属:`WorkflowExecutionCurrentStateProjector`(canonical)、`WorkflowRunInsightReport/Timeline/Graph ArtifactProjector`(derived durable)、AGUI 事件映射

### 06 · 分布式与生产态

- ✅ `06/01-current-vs-target.md` — 诚实对比表(README 那张表的展开):ActorRuntime Provider / Orleans Transport / Projection 并发 / LiveSink / ReadModel 存储的"当前实现 vs 目标态"
- ✅ `06/02-orleans-runtime.md` — `Aevatar.Foundation.Runtime.Implementations.Orleans*`,同一组原语(`IActorRuntime`/`IActorDispatchPort`/`IEventPublisher`)在分布式下的语义(同 actorId 全局单激活 + 邮箱串行)
- ✅ `06/03-kafka-transport.md` — 可选 `Transport=Kafka`(MassTransit/Kafka)插件,ADR-0003 的设计
- ✅ `06/04-garnet-clustering.md` — 生产聚类用共享 Garnet 成员资格(ADR-0032)、Garnet 持久化实现
- ✅ `06/05-architecture-guards.md` — `tools/ci/architecture_guards.sh` / `slow_test_guards.sh` 守卫什么、为什么"禁止 Workflow→Maker 反向依赖"这类规则是 CI 强制的
- ✅ `06/06-credentials-zero-standing-secrets.md` — 零长期密钥:grain state 只存不透明 `BindingId`、触发期换短期票、持久回调零凭证守卫、长效 key 作用域收敛
  - 事实源脊柱:`src/Aevatar.Foundation.Runtime.Implementations.Orleans/Grains/Callbacks/DurableCallbackEnvelopeCredentialGuard.cs`、`src/platform/Aevatar.GAgentService.Hosting/DependencyInjection/ServiceCollectionExtensions.cs`、`docs/adr/0018-per-user-nyxid-binding-via-oauth-broker.md`

### 07 · 周边

- ✅ `07/01-channels.md` — Channel Runtime(多通道适配:Lark/Telegram/...):多 token 凭证路由、凭证边界、统一入站骨干、交互回复抽象
- ✅ `07/02-a2a-interop.md` — `Aevatar.Interop.A2A.*`:Agent-to-Agent 互操作
- ✅ `07/03-chat-routing.md` — `ChatRoutePolicy`(配置 Actor + 边界解析器)、tool-first Ingress
- ✅ `07/04-voice-presence.md` — `Foundation.VoicePresence*`(MiniCPM / OpenAI)、语音路由
- ✅ `07/05-studio-and-scripting.md` — `Aevatar.Studio.*`(member-first / team-first 聚合)、`Aevatar.Scripting.*`
- ✅ `07/06-console-web.md` — 前端控制台 `apps/aevatar-console-web`:技术栈、与后端 SSE 的对接
- ✅ `07/07-observability.md` — OTel 语义约定 `aevatar.*`、两级 Inspector、`/status` 面板
- ✅ `07/08-lark-end-to-end.md` — Lark Bot 全链路走查: 消息入站、路由调度、Tool 执行与卡片回传
- ✅ `07/09-voice-presence-edge-brain.md` — voice-presence 边缘设备与 aevatar 大脑的双工交互与语音路由
- ✅ `07/10-input-ingress-unification.md` — Input 入站统一规范与归一化逻辑
- ✅ `07/11-file-handling-end-to-end.md` — 文件全链路走查: 字节不入 Actor 架构、Ingress、DocumentExtract 与 Submit 流程
- ✅ `07/12-scheduled-tasks.md` — 定时任务全链路走查: 定时调度、Sagas 挂起与可靠触发机制
- ✅ `07/13-lark-bot-registration.md` — Lark Bot 注册与对接：零凭证架构下的中继入站

### 08 · 附录

- ✅ `08/01-glossary.md` — 术语表(对照 `docs/canon/architecture-vocabulary.md`)
- ✅ `08/02-doc-index.md` — 把 aevatar 仓库 `docs/canon` + `docs/adr` 的索引搬过来并加导读(不复制全文)
- ✅ `08/03-demo-cookbook.md` — 可复现 demo 合集:Maker sample、CaseProjection、Workflow.Web、Cli、Inspector
- ✅ `08/04-todo-list.md` — 未来规划·战术 TODO 清单
- ✅ `08/05-crystallization-roadmap.md` — 未来规划·战略 结晶梯度路线图

### 09 · 方案区

- ✅ `09/01-workflow-as-nyxid-service/index.md` — 方案概览: 两头真、当中手工的 Workflow NyxID 服务发布
- ✅ `09/01-workflow-as-nyxid-service/01-mechanisms.md` — 机制总览: wire proxy 与 API 路由
- ✅ `09/01-workflow-as-nyxid-service/02-publish-path.md` — 发布路径与 member-first bind 关系
- ✅ `09/01-workflow-as-nyxid-service/03-register-and-discover.md` — 服务发现与 OpenAPI 穿透
- ✅ `09/01-workflow-as-nyxid-service/04-calling.md` — 三入口同源调用 (CLI/Tool/MCP)
- ✅ `09/01-workflow-as-nyxid-service/05-end-to-end-plan.md` — 端到端 12 跳与落地计划
- ✅ `09/01-workflow-as-nyxid-service/06-auto-registration-plan.md` — 自动注册流程与状态机
- ✅ `09/01-workflow-as-nyxid-service/07-auto-registration-adr.md` — 配套 ADR 草案 (Proposed)
- ✅ `09/02-ingress-tool-ownership/index.md` — 方案概览: 自有工具服务端执行与客户端隐形
- ✅ `09/02-ingress-tool-ownership/01-leak-and-asymmetric-rule.md` — 非对称工具所有权与泄漏分析
- ✅ `09/02-ingress-tool-ownership/02-fix-and-rollout.md` — 自有工具隔离两落点与修复计划
- ✅ `09/03-provision-and-observe-via-nyxid/index.md` — 方案概览: 一句话 provision 与实时观测
- ✅ `09/03-provision-and-observe-via-nyxid/01-end-to-end.md` — 四段全链路与 6 条 live 实测发现根因

### 10 · 已知问题

- ✅ `10/01-cli-lark-scope-isolation.md` — CLI 看不到 Lark Bot 创建的 Agent (Scope 隔离)
- ✅ `10/02-codex-shell-vs-aevatar-tools.md` — shell 工具 vs aevatar 自有工具冲突
- ✅ `10/03-ingress-own-tool-stream-leak.md` — 自有工具泄漏进客户端流的漏洞与修复
- ✅ `10/04-responses-llm-run-offactor-and-observation.md` — off-actor 模式下 LLM 执行与四层故障分析
- ✅ `10/05-lark-delivery-layer-failures.md` — Lark 投递层三类故障:回复错对象 / 截断残片 / 全哑 401
- ✅ `10/06-lark-identity-and-authorization.md` — Lark 身份与授权:owner-vs-sender 调用身份 / 资源授权降级
- ✅ `10/07-scheduled-task-not-firing.md` — 定时任务不触发:重激活跳拍 / Garnet 脑裂 / provision 凭证缺口
- ✅ `10/08-observatory-read-side.md` — 观测台读侧:排序缺失 / ES 1000 字段爆表 / 节点卡进行中
- ✅ `10/09-studio-console-three-traps.md` — Studio 控制台:binding 覆写致 500 / 对话失忆 / chip 溢出
- ✅ `10/10-voice-cancel-race-and-reconnect.md` — 语音:打断 cancel 竞态被当致命 / `/ws/voice` 重连缺失
- ✅ `10/11-nyxid-direct-llm-entry.md` — NyxID 直连 LLM 入口:chat/completions 收不到回复 / 不暴露服务工具

### 11 · Skills 能力层

- ✅ `11/01-aevatar-control-plane-skills.md` — 控制面 Skills 体系与 schedule 客户端 REST
- ✅ `11/02-aevatar-platform-and-probe-skills.md` — 平台 Skills 组合与 fallback 健康体检探针

### 12 · 问题复盘(按周)

- ✅ `12/index.md` — 问题复盘**章索引**:按周归档,逐周 append。
- ✅ `12/01-2026-06-22-to-06-26.md` — 2026-06-22 → 06-26 周复盘:按主题(Lark/定时/观测台/Studio/语音/直连入口)链到第 10 章各篇 + 横切教训 + 状态总表。

---

## 进度看板

| 大块 | 篇数 | 完成 | 状态 |
|---|---|---|---|
| 00 序章 | 4 | 4 | ✅ |
| 01 宿主与入口 | 4 | 4 | ✅ |
| 02 编排层 | 8 | 8 | ✅ |
| 03 内核 | 8 | 8 | ✅ |
| 04 AI 层 | 4 | 4 | ✅ |
| 05 CQRS 读侧 | 4 | 4 | ✅ |
| 06 分布式 | 6 | 6 | ✅ |
| 07 周边 | 13 | 13 | ✅ |
| 08 附录 | 5 | 5 | ✅ |
| 09 方案区 | 13 | 13 | ✅ |
| 10 已知问题 | 11 | 11 | ✅ |
| 11 Skills 能力层 | 2 | 2 | ✅ |
| 12 问题复盘 | 1 | 1 | ✅ |
| **合计** | **83** | **83** | ✅ |

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
