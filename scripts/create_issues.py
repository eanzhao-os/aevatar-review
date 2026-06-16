#!/usr/bin/env python3
"""
为 aevatar-review 批量创建章节 issue。
做完这 43 个 issue = 整本书写完。

每条 issue:
  - title:  "【编号】标题"
  - milestone: 对应 8 大块之一 (number)
  - labels: [大块label, 优先级label, 章节]
  - body:   包含「本篇讲什么 / 关键代码 / 验收标准 / demo / 写作约束」
"""
import json, subprocess, sys

ISSUES = [
  # ───────────────── 00 序章 (ms #1) ─────────────────
  {
    "num": "00-01", "ms": 1, "block": "00-序章", "prio": "P0-主线",
    "title": "Aevatar 是什么、解决什么问题、定位对比",
    "what": "Aevatar 的定位:多 Agent 协作运行时 + Workflow YAML 编排层。讲清楚它和「把流程写死在代码里 / 单 Agent 串行 / 状态混在业务对象 / 难以分布式扩展」的传统 Agent 框架的差异。对比 LangGraph / AutoGen / MAF 等同类方案的取舍(可参考 docs/history/2026-03/maf-integration.md)。",
    "code": "README.md; docs/canon/overview.md; docs/history/2026-03/maf-integration.md; docs/history/2026-04/claude-code-architecture-learnings.md",
    "accept": "读者读完能回答:Aevatar 为什么用 Actor+Event 当内核?为什么用 YAML 而不是代码编排?它和 LangGraph 最本质的区别是什么?配一张『传统 vs Aevatar』对照表。",
  },
  {
    "num": "00-02", "ms": 1, "block": "00-序章", "prio": "P0-主线",
    "title": "仓库地图:slnx + 10 个 slnf 怎么切、src/ ~80 个项目的分层归属",
    "what": "把 aevatar.slnx 和 10 个 *.slnf (foundation/ai/cqrs/workflow/capabilities/agents/channels/platforms/distributed) 的切分逻辑讲透。src/ 下约 80 个项目按 Domain/Application/Infrastructure/Host 四层归类(对照 docs/canon/module-placement-map.md 的 feature→落点表)。",
    "code": "aevatar.slnx; *.slnf; docs/canon/module-placement-map.md; docs/canon/overview.md §2; README.md『代码组织与职责边界』",
    "accept": "输出一张完整的项目分层表(项目名 | 所属层 | 职责 | 依赖约束),并解释为什么用 slnf 按能力域拆分而不是单个 sln。",
  },
  {
    "num": "00-03", "ms": 1, "block": "00-序章", "prio": "P0-主线",
    "title": "Quick Start:从零跑起来 + simple_qa + 看 SSE/报告",
    "what": "可复现的端到端上手:配 LLM Key(环境变量 / ~/.aevatar/secrets.json) → dotnet run Mainnet → curl POST /api/chat simple_qa → 解读 SSE 流的每一帧 → 打开 artifacts/workflow-executions/ 下的 JSON+HTML 报告。每一步都给真实命令和预期输出。",
    "code": "README.md『快速开始』; src/Aevatar.Mainnet.Host.Api/Program.cs; workflows/simple_qa.yaml; src/Aevatar.Configuration/README.md",
    "accept": "读者照做能在本地看到 SSE 流并生成 run 报告;把 simple_qa 的完整 SSE 帧序列贴出来并逐帧注释。",
    "demo": "workflows/simple_qa.yaml",
  },
  {
    "num": "00-04", "ms": 1, "block": "00-序章", "prio": "P0-主线",
    "title": "主线全景图:一次 chat 请求怎么流过整个系统",
    "what": "README.md 主线时序图的完整展开版。从 POST /api/chat 到 SSE 返回,标注每一步落在哪个项目/类/方法。这是全书的『地图』,后续每篇都是对这张图某个局部的放大。要把『为什么这么分层』讲清楚:Command→EventEnvelope→Actor 决策→持久化领域事件→Projection→ReadModel。",
    "code": "README.md 主线时序图; docs/canon/architecture.md §核心主链路; docs/canon/cqrs-projection.md",
    "accept": "输出一张完整的端到端时序图 + 每个箭头对应的代码落点表;读者读完能定位『我要看 X 应该去哪个文件』。",
  },

  # ───────────────── 01 宿主与入口 (ms #2) ─────────────────
  {
    "num": "01-01", "ms": 2, "block": "01-宿主与入口", "prio": "P1-高频",
    "title": "Mainnet vs Workflow Host 边界 + AddAevatarPlatform 组合过程",
    "what": "为什么 Mainnet 是默认统一入口、Workflow.Host.Api 只做协议隔离?AddAevatarMainnetHost / AddAevatarPlatform(EnableMakerExtensions=true) 的 DI 组合顺序做了什么。Maker 为什么从『独立 Host』降级成『Mainnet 插件』。",
    "code": "src/Aevatar.Mainnet.Host.Api/Program.cs + Hosting/; src/Aevatar.Bootstrap/*; docs/canon/overview.md §3; docs/adr/0002-mainnet-architecture.md",
    "accept": "画出两个 Host 的 DI 注册对比图;说明『Host 只做协议适配与能力组合,不承载核心业务流程』这条边界如何被代码强制。",
  },
  {
    "num": "01-02", "ms": 2, "block": "01-宿主与入口", "prio": "P0-主线",
    "title": "POST /api/chat 协议、SSE 帧类型、/v1/responses 与软废弃 streaming-proxy",
    "what": "完整协议说明:请求体(prompt/workflow/agentId)、Accept: text/event-stream、SSE 帧类型全集(RUN_STARTED / 步骤完成 / 消息片段 / RUN_FINISHED / RUN_ERROR)。讲清楚 Sunset 语义:旧 /api/scopes/{scopeId}/streaming-proxy/* 已软废弃(Sunset: Wed, 25 Nov 2026),新客户端走 /v1/responses,两者 room/fan-out/participant 语义不等价。",
    "code": "docs/canon/chat-api.md; docs/canon/llm-streaming.md; docs/2026-04-02-streaming-proxy-flow.md; README.md Sunset 段落",
    "accept": "输出 SSE 帧类型完整对照表(帧名 | 触发时机 | payload 字段);明确新旧接口的迁移边界。",
  },
  {
    "num": "01-03", "ms": 2, "block": "01-宿主与入口", "prio": "P1-高频",
    "title": "Run 语义:runId/sessionId 服务端生成、不按 run 隔离事件流、终止事件收敛",
    "what": "Run 语义的几个反直觉点:同一 Actor 多次运行默认不按 run 隔离事件流(客户端收全量);单次请求只在当前 runId 的终止事件到达时结束;RUN_STARTED 由 StartWorkflowEvent 投影统一生成,threadId=发布该事件的 ActorId;runId/sessionId 都服务端生成,客户端只需 prompt/workflow/agentId。",
    "code": "README.md『Run 语义』; src/workflow/Aevatar.Workflow.Application/*; docs/canon/workflow-runtime.md",
    "accept": "用一次具体 run 的事件序列说明:为什么不按 run 隔离?客户端怎么知道该停?runId 从哪来?",
  },

  # ───────────────── 02 编排层 (ms #3) ─────────────────
  {
    "num": "02-01", "ms": 3, "block": "02-编排层", "prio": "P1-高频",
    "title": "Workflow YAML 完整语法:name/roles/steps/routes + steps[].type 取值全表",
    "what": "YAML 语法的权威说明:name/description/when_to_use/roles/steps/routes 四大块。steps[].type 的所有合法取值(workflow_loop/conditional/while/loop/workflow_call/assign/parallel/fan_out/vote_consensus/llm_call/tool_call/connector_call/transform/retrieve_facts...)及每个 type 必填/可选字段。区分 role vs target_role 的语义。",
    "code": "src/workflow/Aevatar.Workflow.Core/Primitives/*; docs/canon/workflow-primitives.md; docs/canon/role-model.md",
    "accept": "输出 steps[].type 完整字段表(type | 必填字段 | 可选字段 | next/routes 规则 | 示例片段)。",
  },
  {
    "num": "02-02", "ms": 3, "block": "02-编排层", "prio": "P1-高频",
    "title": "WorkflowGAgent(definition) vs WorkflowRunGAgent(run, 1779 行)职责切分",
    "what": "definition actor 只持有 YAML + 编译结果 + Version(只 bind/resolve),run actor 持有全部执行事实(WorkflowRunState: DefinitionActorId/RunId/Status/ExecutionStates/ExecutionContext/子工作流 binding)。为什么要把『定义』和『运行』拆成两个 actor?这样拆给 replay / 多 run / 子工作流带来什么好处?",
    "code": "src/workflow/Aevatar.Workflow.Core/WorkflowGAgent.cs; src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs; src/workflow/Aevatar.Workflow.Core/README.md",
    "accept": "输出两个 actor 的状态字段对照表 + 各自处理的事件列表;说明执行事实为什么不放在 definition actor。",
  },
  {
    "num": "02-03", "ms": 3, "block": "02-编排层", "prio": "P1-高频",
    "title": "WorkflowExecutionKernel 主循环:current step / variables / retry / timeout",
    "what": "run actor 内的执行内核怎么推进:主循环结构、current step 状态机、variables 作用域、retry/timeout 策略。重点讲『全部在 actor-owned execution state』—— 模块状态通过 LoadState/SaveState 落到 WorkflowRunState.ExecutionStates,callback 线程只能发内部事件不能直接推进业务状态。模块业务时间用 IWorkflowExecutionContext.UtcNow(不用 wall clock,见 iter89 refactor 注释)。",
    "code": "src/workflow/Aevatar.Workflow.Core/Execution/WorkflowExecutionKernel*; src/workflow/Aevatar.Workflow.Core/Execution/WorkflowExecutionBridgeModule.cs",
    "accept": "画出主循环状态机(推进/挂起等待/完成/失败收敛);说明 callback fired 事件怎么在 actor 内完成对账。",
  },
  {
    "num": "02-04", "ms": 3, "block": "02-编排层", "prio": "P0-主线",
    "title": "★ 步骤模块全图:30+ Module 逐个讲(配最小 YAML)",
    "what": "src/workflow/Aevatar.Workflow.Core/Modules/ 下全部模块逐文件讲:workflow_loop/llm_call/tool_call/connector_call/parallel_fan_out/switch/while/vote/wait_signal/human_approval/human_input/assign/transform/reflect/evaluate/emit/notify/guard/lease/delay/reflect/workflow_call/dynamic/... 每个给 type 名、作用、最小 YAML 片段、典型组合。这是全书最实用的一篇。",
    "code": "src/workflow/Aevatar.Workflow.Core/Modules/*.cs (30+ 文件); README.md『工作流里能写哪些步骤』表",
    "accept": "输出 30+ 模块的速查手册(每个 ≤10 行说明 + 最小示例),可作为日常写 YAML 的参考。",
  },
  {
    "num": "02-05", "ms": 3, "block": "02-编排层", "prio": "P1-高频",
    "title": "workflows/ 下 12 个示例逐个拆解",
    "what": "逐个拆 workflows/*.yaml:simple_qa / resume_screening / invoice_ocr_approval / petty_cash_approval / lark_approval_wait / lark_approval_wait_poll / cn_reimbursement_intake / employee_reimbursement_sg / codex_long_running_handoff / host-callback-budget-branch / probe_document_extract / probe_vision_describe。每个画 step 流转图,标注用到的模块和分支/降级策略。",
    "code": "workflows/*.yaml (12 个)",
    "accept": "12 个示例每个一段解读(流转图 + 设计要点);按复杂度递增排列,从 simple_qa 到 codex_long_running_handoff。",
  },
  {
    "num": "02-06", "ms": 3, "block": "02-编排层", "prio": "P0-主线",
    "title": "Maker 插件边界:maker_recursive + maker_vote、IWorkflowModulePack、架构门禁",
    "what": "Maker 的定位变迁:为什么从『独立 Host + /api/maker/*』降级成『Workflow 插件』。maker_recursive / maker_vote 模块的递归分解 + 并行 fan-out + 投票收敛机制(coordinator/worker roles)。IWorkflowModulePack 注册体系。为什么架构门禁强制禁止 Workflow→Maker 反向依赖、禁止残留独立 Maker 工程。",
    "code": "src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/; demos/Aevatar.Demos.Maker/; docs/canon/overview.md §4; docs/adr/0006-multi-agent-evolution.md; tools/ci/architecture_guards.sh",
    "accept": "画 Maker sample 的执行时序(coordinator→parallel fan-out→workers→vote→递归);列出架构门禁具体 grep 哪些模式。",
    "demo": "demos/Aevatar.Demos.Maker",
  },
  {
    "num": "02-07", "ms": 3, "block": "02-编排层", "prio": "P2-下钻",
    "title": "Connector(HTTP/CLI/MCP)配置与 connector_call 执行、role allowlist",
    "what": "Connector 配置格式(~/.aevatar/connectors.json)、三种类型(HTTP/CLI/MCP)、connector_call 步骤如何按名称解析并执行、role 的 connector allowlist 安全边界(connector_call 前检查 role 是否允许调用该 connector)。",
    "code": "docs/canon/connector.md; docs/canon/role-model.md; src/Aevatar.Configuration/README.md; src/workflow/Aevatar.Workflow.Core/Connectors/",
    "accept": "给一个 HTTP connector + 一个 MCP connector 的完整配置 + YAML 调用示例;说明 allowlist 怎么防越权。",
  },

  # ───────────────── 03 运行内核 (ms #4) ─────────────────
  {
    "num": "03-01", "ms": 4, "block": "03-运行内核", "prio": "P1-高频",
    "title": "核心概念辨析:Agent / Actor / Runtime / Stream",
    "what": "Foundation 的四个核心概念:Agent(业务逻辑单元)/ Actor(Agent 的运行容器,串行处理 + 层级关系)/ Runtime(Stream 之上的 Actor 语义层,负责生命周期/寻址/邮箱串行/拓扑)/ Stream(EventEnvelope 传输骨架)。对应关键接口 IAgent/IActor/IActorRuntime/IActorDispatchPort/IEventPublisher/IStream/IStreamProvider。",
    "code": "src/Aevatar.Foundation.Abstractions/*; docs/canon/architecture.md §核心概念",
    "accept": "输出四概念对照表(概念 | 职责 | 关键接口 | 一句话理解);说明 Runtime 和 Stream 是『语义层 vs 传输骨架』的关系,不是并列两条链路。",
  },
  {
    "num": "03-02", "ms": 4, "block": "03-运行内核", "prio": "P0-主线",
    "title": "★ 最易误解的边界:EventEnvelope(runtime message) vs StateEvent(事实源)",
    "what": "全书最容易踩坑的概念。EventEnvelope 名字叫 Event 但在 Foundation 语义上是 runtime message envelope —— payload 既可能是 command-like request/signal/reply/timeout fired,也可能是业务事件。Event Sourcing 的持久化事实是 StateEvent + EventStore,不是运行时消息流。两者有关联但不是一回事。只有显式 PersistDomainEventAsync 后领域事件才进入 EventStore。",
    "code": "src/Aevatar.Foundation.Abstractions (EventEnvelope, IStateStore, IEventStore); docs/canon/architecture.md §核心主链路 + 关键澄清; docs/canon/event-sourcing.md",
    "accept": "用一张图把『运行时消息流(EventEnvelope, on Stream)』和『事实层(StateEvent, in EventStore)』分开画;举一个具体事件说明它如何同时出现在两层但语义不同。",
  },
  {
    "num": "03-03", "ms": 4, "block": "03-运行内核", "prio": "P2-下钻",
    "title": "GAgentBase 统一事件 pipeline:静态[EventHandler] + 动态 IEventModule + 双 Hook",
    "what": "GAgentBase / GAgentBase<TState> / GAgentBase<TState,TConfig> 三层基类。统一事件分发:静态处理器(反射发现 [EventHandler])+ 动态模块(运行时注册 IEventModule<IEventHandlerContext>)按 Priority 升序合并执行(EventPipelineBuilder)。双 Hook 通道:virtual 方法 + IGAgentExecutionHook pipeline,默认 fail-fast,子类可 override ShouldSuppressHandlerException 改 best-effort。",
    "code": "src/Aevatar.Foundation.Core/GAgentBase.cs; EventPipelineBuilder; StateGuard; docs/canon/architecture.md §Foundation.Core",
    "accept": "画出『一条 EventEnvelope 进来后的 dispatch 流程』(找 handler→排序→Hook 前置→执行→Hook 后置→异常策略);给一个自定义 [EventHandler] + 一个 IEventModule 的最小代码示例。",
  },
  {
    "num": "03-04", "ms": 4, "block": "03-运行内核", "prio": "P2-下钻",
    "title": "StateGuard(AsyncLocal 写保护) + PersistDomainEventAsync + TransitionState reducer",
    "what": "StateGuard 通过 AsyncLocal 限制 State 只在事件处理或激活期的 write scope 可写,其他上下文抛 InvalidOperationException —— 保证状态修改与消息处理串行模型一致。有状态 Actor 只有显式 PersistDomainEventAsync/PersistDomainEventsAsync 后领域事件才进 EventStore。TransitionState 是纯函数 reducer(current, event)→next。latest-wins RunManager/RunContextScope。",
    "code": "src/Aevatar.Foundation.Core/ (StateGuard, GAgentBase<TState> PersistDomainEventAsync); docs/canon/event-sourcing.md",
    "accept": "说明『为什么状态不能在任意 await 后写』;给一个 PersistDomainEventAsync → TransitionState → committed observation 的完整代码追踪。",
  },
  {
    "num": "03-05", "ms": 4, "block": "03-运行内核", "prio": "P2-下钻",
    "title": "路由与拓扑:DirectRoute / PublicationRoute.topology / PublicationRoute.observer",
    "what": "拓扑事实已收口到 runtime actor 自身:Local 的 LocalActor 内存态持有 parent/children,Orleans 的 RuntimeActorGrainState 持久态持有 ParentId/Children。LinkAsync 同时更新拓扑状态和 stream relay binding。三种路由:DirectRoute(runtime 直接投递到 actor inbox)/ PublicationRoute.topology(stream forwarding 传播给父子)/ PublicationRoute.observer(只给 projection/live sink/observer,可见但不进业务 actor inbox)。",
    "code": "src/Aevatar.Foundation.Runtime.Implementations.Local/ (LocalActor, LocalActorPublisher); docs/canon/architecture.md §Routing 细节",
    "accept": "画出三种 route 的传播范围图;说明为什么 fan-out 不再用单独 EventRouter 对象而是 stream forwarding。",
  },
  {
    "num": "03-06", "ms": 4, "block": "03-运行内核", "prio": "P2-下钻",
    "title": "Local Runtime 深入:LocalActorRuntime / LocalActor(邮箱串行)/ LocalActorPublisher",
    "what": "本地实现的四个核心类:LocalActorRuntime(创建/销毁/查找/链接,按需激活)/ LocalActor(邮箱串行处理、父流订阅、子节点传播)/ LocalActorPublisher(按 EnvelopeRoute 的 direct/publication 变体发布)/ LocalActorTypeProbe。AddAevatarRuntime() 一键注册。为什么 InMemory* 组件仅限开发测试,不作为生产容量治理对象。",
    "code": "src/Aevatar.Foundation.Runtime.Implementations.Local/*; docs/canon/architecture.md §Local 实现",
    "accept": "给一个最小 demo:DI 注入 → 创建 parent/child → LinkAsync → PublishAsync(TopologyAudience.Children);说明邮箱串行是怎么实现的。",
    "demo": "docs/canon/architecture.md §快速上手 的三段代码",
  },

  # ───────────────── 04 AI 能力层 (ms #5) ─────────────────
  {
    "num": "04-01", "ms": 5, "block": "04-AI能力层", "prio": "P2-下钻",
    "title": "RoleGAgent:处理 ChatRequestEvent、流式调 LLM、发 AG-UI 事件",
    "what": "RoleGAgent(AI role actor)处理 ChatRequestEvent 的完整路径:通过 ChatStreamAsync 流式调 LLM,发布 AG-UI 事件序列 TextMessageStart → Content* → ToolCall* → End。role identity 是 typed actor-owned fact(不是解析 child actor id 前缀,见 iter15 refactor)。RoleGAgent 持有 pending-approval continuation(YieldApprovalHandler + 远程升级 + timeout)。",
    "code": "src/Aevatar.AI.Core/RoleGAgent.cs; src/Aevatar.AI.Abstractions/Agents/; docs/canon/role-model.md",
    "accept": "画出 ChatRequestEvent → LLM 流式 → AG-UI 事件序列的时序;说明 YieldApprovalHandler 在 tool 审批时怎么 yield。",
  },
  {
    "num": "04-02", "ms": 5, "block": "04-AI能力层", "prio": "P2-下钻",
    "title": "LLM Provider 抽象与实现:MEAI / NyxId / Tornado",
    "what": "ILLMProviderFactory 与各 Provider 实现的差异:Microsoft.Extensions.AI(MEAI,通用)/ NyxId(内部网关,见 nyxid-llm-integration.md)/ Tornado。Provider 怎么选配、流式 token 怎么回传。NyxId 的 per-user OAuth binding(ADR-0018)和 responses 直连(nyxid-responses-direct.md)。",
    "code": "src/Aevatar.AI.LLMProviders.* (MEAI/NyxId/Tornado); docs/canon/nyxid-llm-integration.md; docs/canon/nyxid-responses-direct.md; docs/adr/0018-per-user-nyxid-binding-via-oauth-broker.md",
    "accept": "输出 Provider 选择矩阵;给一个切换 Provider 的配置示例。",
  },
  {
    "num": "04-03", "ms": 5, "block": "04-AI能力层", "prio": "P1-高频",
    "title": "★ Tool 体系:ToolApprovalHandler + 20+ ToolProvider(MCP/Skills/Lark/Web/...)",
    "what": "工具体系全景:ToolApprovalHandler(YieldApprovalHandler 默认 + MissingApprovalHandler fail closed + IRemoteToolApprovalPort 远程升级)。20+ ToolProvider 逐个点:MCP / Skills / Lark / Web / Telegram / Ornn / Channel / ChannelAdmin / Scripting / ServiceInvoke / AgentCatalog / Binding / NyxId / ChronoStorage / Workflow / ToolSetRegistry / AevatarInvocation。tool allowlist 安全边界。",
    "code": "src/Aevatar.AI.ToolProviders.* (20+ 目录); docs/canon/role-model.md (tool allowlist)",
    "accept": "输出 20+ ToolProvider 速查表(provider | 提供什么工具 | 配置方式 | 安全边界);说明 MCP 和 Skills 两种 provider 的区别。",
  },
  {
    "num": "04-04", "ms": 5, "block": "04-AI能力层", "prio": "P2-下钻",
    "title": "ChatRuntime / ToolLoop / 中间件管线(IAgentRun/IToolCall/ILLMCall Middleware)",
    "what": "AI 执行管线:ChatRuntime 编排、ToolLoop 自动工具调用循环、三类中间件(IAgentRunMiddleware / IToolCallMiddleware / ILLMCallMiddleware)的插入点和优先级。可观测性中间件如何记录 stable ids / lengths / status / redaction markers。",
    "code": "src/Aevatar.AI.Core/Chat/*; src/Aevatar.AI.Core/Middleware/*; src/Aevatar.AI.Core/Hooks/*",
    "accept": "画出一次带工具调用的 ChatRuntime 完整执行流(model→tool_call→middleware→tool result→model);给一个自定义中间件的示例。",
  },

  # ───────────────── 05 CQRS 读侧 (ms #6) ─────────────────
  {
    "num": "05-01", "ms": 6, "block": "05-CQRS读侧", "prio": "P1-高频",
    "title": "Projection 总览:Command→EventEnvelope→Actor→持久化→Projection→ReadModel",
    "what": "CQRS 统一链路全景:Command 先进 Application,包装为 EventEnvelope 投递到 Actor;Actor 在串行邮箱决策并显式持久化领域事件;Projection 统一消费 Actor envelope 流更新 ReadModel;API 推送(SSE/WS/AGUI)和 CQRS 读模型共享同一条投影输入。关键:State 是写侧运行态,读侧由投影生成独立只读模型;实时输出主要是 workflow run-event 事件投影,不是直接把 State 映射到前端。",
    "code": "docs/canon/cqrs-projection.md; src/Aevatar.CQRS.Core*; src/Aevatar.CQRS.Projection.Core/README.md",
    "accept": "画出写侧(命令→事件→持久化)和读侧(投影→ReadModel→API)的分界;说明为什么 SSE 和 CQRS 共享同一投影输入(避免双轨)。",
  },
  {
    "num": "05-02", "ms": 6, "block": "05-CQRS读侧", "prio": "P0-主线",
    "title": "★ 两条投影主链:Durable Materialization vs Session Observation",
    "what": "全书 CQRS 部分核心。两条链都以 scope actor 为唯一运行态事实源,host 侧只留薄适配。Durable Materialization(scope actor,只消费 committed observation,ICurrentStateProjectionMaterializer vs IProjectionArtifactMaterializer 必须显式区分)。Session Observation(发布 session event stream,不做生命周期事实,live sink 不当事实)。scope actor 持有存在性/水位/失败/release 状态,host 不保留 actorId→runtime 注册表。",
    "code": "src/Aevatar.CQRS.Projection.Core/README.md; src/Aevatar.CQRS.Projection.Core/Orchestration/* (ProjectionScopeGAgentBase/Materialization/Session + ActivationService/ReleaseService)",
    "accept": "并列画出两条链的 actor 生命周期图;说明『durable 只吃 committed observation』『session 不持生命周期事实』这两条约束分别防什么 bug。",
  },
  {
    "num": "05-03", "ms": 6, "block": "05-CQRS读侧", "prio": "P2-下钻",
    "title": "ReadModel 存储实现:InMemory(默认) / Elasticsearch / Neo4j / StateMirror",
    "what": "四种读模型 Provider 的差异和适用场景:InMemory(开发测试默认,Providers.InMemory)/ Elasticsearch(全文检索)/ Neo4j(图关系)/ StateMirror(状态镜像)。生产怎么从 InMemory 切到持久化 Provider,实现跨节点一致读。",
    "code": "src/Aevatar.CQRS.Projection.Providers.InMemory/; src/Aevatar.CQRS.Projection.Providers.Elasticsearch/; src/Aevatar.CQRS.Projection.Providers.Neo4j/; src/Aevatar.CQRS.Projection.StateMirror/",
    "accept": "输出四种 Provider 对比表;给一个切换到 Elasticsearch 的配置示例。",
  },
  {
    "num": "05-04", "ms": 6, "block": "05-CQRS读侧", "prio": "P1-高频",
    "title": "Workflow 专属投影:CurrentState canonical + Insight/Timeline/Graph Artifact + AGUI 映射",
    "what": "Workflow 投影的几条输出分支:WorkflowExecutionCurrentStateProjector(canonical current-state store,只记 committed StateVersion/LastEventId)/ WorkflowRunInsightReport + Timeline + Graph ArtifactProjector(derived durable artifacts)/ WorkflowExecutionRunEventProjector(在 AGUIAdapter,通过 EventEnvelopeToWorkflowRunEventMapper 把同一 envelope 流转成 WorkflowRunEventEnvelope,经 ProjectionSessionEventHub 输出实时 SSE/WS)。订阅粒度 actor 级、分发粒度 command/correlation 级,按 workflow-run:{actorId}:{commandId} 路由。",
    "code": "src/workflow/Aevatar.Workflow.Projection/README.md; src/workflow/Aevatar.Workflow.Presentation.AGUIAdapter/; docs/canon/cqrs-projection.md",
    "accept": "画出同一 envelope 流如何 fan-out 到 canonical/artifact/SSE 三条分支;说明 command id 回退到 CorrelationId 的逻辑。",
  },

  # ───────────────── 06 分布式 (ms #7) ─────────────────
  {
    "num": "06-01", "ms": 7, "block": "06-分布式", "prio": "P1-高频",
    "title": "诚实对比:当前实现 vs 目标态(ActorRuntime/Transport/Projection/LiveSink/ReadModel)",
    "what": "README.md 那张『当前实现(2026-02-22) vs 目标态』表的逐行展开。诚实标注哪些是开发测试基线(InMemory/Local)、哪些是生产目标(分布式 Actor Runtime + 非 InMemory 持久化)。不脑补未来,按代码事实描述,对仓库标注的部分原样引用。审计评分口径:以当前已落地代码为准。",
    "code": "README.md『当前实现与目标态』表; docs/canon/overview.md §6; docs/audit-scorecard/*",
    "accept": "输出完整的当前/目标对比表,每行附『代码现状证据』(哪个 Provider 是默认)。",
  },
  {
    "num": "06-02", "ms": 7, "block": "06-分布式", "prio": "P2-下钻",
    "title": "Orleans Runtime:同一组原语在分布式下的语义",
    "what": "Aevatar.Foundation.Runtime.Implementations.Orleans*。AddAevatarFoundationRuntimeOrleans() 与本地 AddAevatarRuntime() 保持同一口径:都只暴露 IActorRuntime/IActorDispatchPort/IEventPublisher 这组基础原语。分布式下保证同一 actorId 全局单激活 + 邮箱串行。RuntimeActorGrainState 持久态持有 ParentId/Children。上层能力不依赖具体 runtime provider。",
    "code": "src/Aevatar.Foundation.Runtime.Implementations.Orleans/*; src/Aevatar.Foundation.Runtime.Implementations.Orleans.Streaming/*; docs/canon/architecture.md §分布式目标态",
    "accept": "说明『同一 actorId 全局单激活』在 Orleans 里怎么实现;对比 Local 与 Orleans 在拓扑/激活/路由上的接口一致性。",
  },
  {
    "num": "06-03", "ms": 7, "block": "06-分布式", "prio": "P2-下钻",
    "title": "Kafka Transport(MassTransit)插件 + ADR-0003 设计",
    "what": "可选 ActorRuntime:Transport=Kafka 启用 MassTransit/Kafka 传输插件。ADR-0003 的设计动机:为什么需要可插拔 transport、Kafka provider 的后端架构、与内置链路的切换点。生产按部署拓扑启用可插拔 transport,统一由 stream/queue 层承载跨节点转发。",
    "code": "src/Aevatar.Foundation.Runtime.Implementations.Orleans.Transport.KafkaProvider/; src/Aevatar.Foundation.Runtime.Transport.Implementations.MassTransitKafka/; docs/adr/0003-kafka-transport.md",
    "accept": "说明切换到 Kafka transport 的配置;画出跨节点 envelope 转发路径。",
  },
  {
    "num": "06-04", "ms": 7, "block": "06-分布式", "prio": "P2-下钻",
    "title": "Garnet 生产聚类 + 持久化实现",
    "what": "生产聚类用共享 Garnet 成员资格(ADR-0032),Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet 作为非 InMemory 持久化实现。Garnet 在 IStateStore/IEventStore 上的落点,内存增长与容量风险评估。",
    "code": "src/Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet/; docs/adr/0032-mainnet-garnet-clustering.md; docker-compose.mainnet-cluster.yml",
    "accept": "给一个 Garnet 集群的最小 docker-compose 配置解读;说明它怎么替换 InMemory。",
    "demo": "docker-compose.mainnet-cluster.yml",
  },
  {
    "num": "06-05", "ms": 7, "block": "06-分布式", "prio": "P1-高频",
    "title": "架构门禁:architecture_guards.sh / slow_test_guards.sh 守卫什么",
    "what": "tools/ci/ 下的守卫脚本具体检查什么:architecture_guards.sh 强制关键编排类保持轻量(行数 + 依赖数上限)、禁止 Workflow→Maker 反向依赖、禁止残留独立 Maker 工程、禁止 AddMakerCapability()/api/maker/* 回流、强制 Mainnet 通过 AddAevatarPlatform(EnableMakerExtensions) 装配。slow_test_guards.sh 承接分钟级自治演化回归。为什么这些规则必须是 CI 强制而不是靠约定。",
    "code": "tools/ci/architecture_guards.sh; tools/ci/slow_test_guards.sh; docs/canon/overview.md §7; docs/adr/0001-project-split-strategy.md",
    "accept": "列出 architecture_guards 的每条检查项 + 它防止什么架构腐化;给一个会触发门禁的反例。",
  },

  # ───────────────── 07 周边 (ms #8) ─────────────────
  {
    "num": "07-01", "ms": 8, "block": "07-周边", "prio": "P2-下钻",
    "title": "Channel Runtime:多通道适配(Lark/Telegram)+ 凭证路由/边界/入站骨干",
    "what": "多通道 IM 适配:Lark / Telegram 等。核心 ADR 链:多 token 凭证路由(0008)、凭证边界(0012)、统一入站骨干(0013)、交互回复抽象(0014)、bot 回调架构(0009)、Lark reply chain 完成语义(0021/0027)。Channel 怎么把外部 IM 消息转成内部 chat 请求、回复怎么可靠送回。",
    "code": "src/Aevatar.AI.ToolProviders.Channel/; src/Aevatar.AI.ToolProviders.ChannelAdmin/; src/Aevatar.AI.ToolProviders.Lark/; src/Aevatar.AI.ToolProviders.Telegram/; docs/canon/aevatar-channel-architecture.md; docs/canon/lark-reply-completion-semantics.md",
    "accept": "画一条 Lark 消息从收到到回复的完整路径(含凭证路由 + reply chain 完成保证)。",
  },
  {
    "num": "07-02", "ms": 8, "block": "07-周边", "prio": "P3-按需",
    "title": "A2A Interop:Agent-to-Agent 互操作",
    "what": "Aevatar.Interop.A2A.*(Abstraction/Application/Hosting)的定位:Aevatar agent 如何与外部 agent 系统互通。A2A 协议的接入点、身份映射、与内部 GAgent 的桥接。",
    "code": "src/Aevatar.Interop.A2A.Abstractions/; src/Aevatar.Interop.A2A.Application/; src/Aevatar.Interop.A2A.Hosting/",
    "accept": "说明 A2A 互操作的最小接入步骤;给一个把外部 agent 暴露给 Aevatar 的示例。",
  },
  {
    "num": "07-03", "ms": 8, "block": "07-周边", "prio": "P2-下钻",
    "title": "ChatRouting:ChatRoutePolicy(配置 Actor + 边界解析器)+ tool-first ingress",
    "what": "ChatRoutePolicy 机制:配置 Actor + 边界解析器(ADR-0024),ChatRouteResolver 如何把一条 chat 请求路由到正确的 agent/scope。tool-first ingress(ADR-0026):把 forward actions 收敛成 model + tools,而不是为每个 forward 写独立路径。",
    "code": "src/Aevatar.ChatRouting.Abstractions/; src/Aevatar.ChatRouting.Core/; docs/adr/0024-chat-route-policy.md; docs/adr/0026-tool-first-chat-ingress.md",
    "accept": "画一条 chat 请求的路由决策树;说明 tool-first 比 per-forward-action 好在哪。",
  },
  {
    "num": "07-04", "ms": 8, "block": "07-周边", "prio": "P3-按需",
    "title": "VoicePresence:语音在场(MiniCPM/OpenAI)+ 语音路由",
    "what": "语音能力:Foundation.VoicePresence(MiniCPM / OpenAI provider)。语音路由集成(ADR-0025 policy-aware WebSocket boundary)、voice edge local tools(ADR-0031)、voice provider NyxId ephemeral broker(ADR-0033)。RoleGAgent 实现 IVoicePresenceRuntimeStateOwner。",
    "code": "src/Aevatar.Foundation.VoicePresence*/; src/Aevatar.Foundation.VoicePresence.MiniCPM/; src/Aevatar.Foundation.VoicePresence.OpenAI/; docs/canon/voice-presence-integration.md; docs/adr/0025,0031,0033",
    "accept": "画语音会话的端到端路径(WebSocket edge → policy → RoleGAgent → voice provider);说明 ephemeral broker 的作用。",
  },
  {
    "num": "07-05", "ms": 8, "block": "07-周边", "prio": "P3-按需",
    "title": "Studio(member-first / team-first 聚合)+ Scripting",
    "what": "Aevatar.Studio.*:member-first published service 身份(ADR-0016)、team 作为 scope 下的一等聚合(ADR-0017)、team accepted receipt 语义(ADR-0028)、stable AgentKind identity(ADR-0019/0030)。Aevatar.Scripting.*:运行时脚本能力(canon/scripting.md),其 authority write path 的 CQRS 闭环。",
    "code": "src/Aevatar.Studio.*; src/Aevatar.Scripting.*; docs/adr/0016,0017,0019,0028,0030; docs/canon/scripting.md",
    "accept": "说明 member / team / scope / AgentKind 四个身份概念的关系;给 Scripting 一个 write path 的 CQRS 追踪。",
  },
  {
    "num": "07-06", "ms": 8, "block": "07-周边", "prio": "P3-按需",
    "title": "前端控制台 apps/aevatar-console-web:技术栈 + SSE 对接",
    "what": "前端控制台:React + Umi/Ant Design Pro + pnpm(biome.json / jest)。config/proxy/routes 结构,如何与后端 SSE/WebSocket 对接,AGUI 事件怎么在前端渲染(docs/canon/frontend-design.md)。",
    "code": "apps/aevatar-console-web/ (package.json, config/, src/); docs/canon/frontend-design.md",
    "accept": "说明前端如何订阅并渲染 AGUI 事件流;给一个 SSE handler 的关键代码片段。",
  },
  {
    "num": "07-07", "ms": 8, "block": "07-周边", "prio": "P2-下钻",
    "title": "可观测性:OTel aevatar.* 语义约定 + 两级 Inspector + /status 面板",
    "what": "OTel 语义约定 aevatar.* 的活动/spans(ADR-0022)。两级 Inspector 架构(ADR-0023:canonical readmodel vs observation OTel)。/status 状态面板架构(canon/status-dashboard.md)。scheduled skill runners(canon/scheduled-skill-runners.md)。",
    "code": "docs/adr/0022-otel-aevatar-semantic-conventions.md; docs/adr/0023-two-tier-inspector-architecture.md; docs/canon/observability.md; docs/canon/status-dashboard.md; docs/canon/scheduled-skill-runners.md",
    "accept": "列出 aevatar.* 的核心 activity 名;说明两级 Inspector 为什么要把 canonical readmodel 和 OTel observation 分开。",
  },

  # ───────────────── 08 附录 (ms #9) ─────────────────
  {
    "num": "08-01", "ms": 9, "block": "08-附录", "prio": "P3-按需",
    "title": "术语表(Glossary):对照 architecture-vocabulary.md",
    "what": "全书术语统一表,对照 docs/canon/architecture-vocabulary.md。收录所有高频术语:GAgent / Actor / Runtime / Stream / EventEnvelope / StateEvent / EventStore / Projection / ReadModel / Scope Actor / AgentKind / Role / Connector / Run / Command / AGUI / NyxId / Garnet 等,每个给中英对照 + 一句话定义 + 首次出现的章节链接。",
    "code": "docs/canon/architecture-vocabulary.md; 全书",
    "accept": "输出按字母/拼音排序的术语表,每个术语有定义 + 代码落点 + 关联术语。",
  },
  {
    "num": "08-02", "ms": 9, "block": "08-附录", "prio": "P3-按需",
    "title": "上游文档索引:canon + adr 导读(不复制全文,只加导读)",
    "what": "把 aevatar 仓库 docs/canon(26 篇)+ docs/adr(34 篇)的索引搬到本仓库,每篇加一句导读(这篇讲什么、什么时候该读、对应本书哪一章)。不复制全文,尊重上游版权;只做导航。",
    "code": "docs/README.md; docs/canon/*; docs/adr/*",
    "accept": "输出 canon + adr 完整索引表,每篇一行导读 + 关联本书章节号。",
  },
  {
    "num": "08-03", "ms": 9, "block": "08-附录", "prio": "P2-下钻",
    "title": "Demo Cookbook:Maker / CaseProjection / Workflow.Web / Cli / Inspector 可复现合集",
    "what": "demos/ 下所有 demo 的可复现合集:Aevatar.Demos.Maker(Maker sample)/ Aevatar.Demos.CaseProjection(+Host/+Extensions.Sla,案例投影)/ Aevatar.Demos.Workflow.Web / Aevatar.Demos.Cli / Aevatar.Demos.Inspector / lark-interaction-probe。每个给启动命令 + 预期输出 + 对应本书哪一章的实例。",
    "code": "demos/Aevatar.Demos.Maker/; demos/Aevatar.Demos.CaseProjection*/; demos/Aevatar.Demos.Workflow.Web/; demos/Aevatar.Demos.Cli/; demos/Aevatar.Demos.Inspector/; demos/lark-interaction-probe/",
    "accept": "每个 demo 一段可照做的 cookbook(环境前提 + 命令 + 看什么)。",
    "demo": "demos/* 全部",
  },
]

def create_issue(it):
    body = f"""### 本篇讲什么

{it["what"]}

### 关键代码(事实源,以 ~/Code/aevatar 为准)

`{it["code"]}`

### 验收标准(做到这些就算本 issue 完成)

{it["accept"]}
"""
    if it.get("demo"):
        body += f"\n### 配套 demo\n`{it['demo']}`\n"

    title = f"【{it['num']}】{it['title']}"
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
        "--label", f"{it['block']},{it['prio']},章节",
        "--milestone", it["ms_title"],
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL {it['num']}: {r.stderr.strip()}")
        return None
    print(f"OK   {it['num']}  {it['title']}  -> {r.stdout.strip()}")
    return r.stdout.strip()

MS = {
    1: "00-序章", 2: "01-宿主与入口", 3: "02-编排层", 4: "03-运行内核",
    5: "04-AI能力层", 6: "05-CQRS读侧", 7: "06-分布式", 8: "07-周边", 9: "08-附录",
}
for it in ISSUES:
    it["ms_title"] = MS[it["ms"]]

if __name__ == "__main__":
    print(f"共 {len(ISSUES)} 个 issue 待创建\n")
    urls = []
    for it in ISSUES:
        u = create_issue(it)
        if u:
            urls.append((it["num"], u))
    print(f"\n完成 {len(urls)}/{len(ISSUES)}")
