# Aevatar 是什么

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

## 一句话定位

Aevatar 不是“给 LLM 包一层 API”的普通 Agent SDK。按源码首页的定义，它是一个多 Agent 协作系统：底层用 Actor + Event 承载运行时，默认用 `Workflow YAML` 声明角色、步骤、路由与策略，然后通过 HTTP Chat 接口触发，并用 SSE / WebSocket 观察运行过程。这个定位直接来自 `README.md` 、。

所以可以先这样记：

> Aevatar = 多 Agent 协作运行时 + Workflow YAML 编排层。

这句话里有两个重点：

1. **运行时**：Agent 不是临时函数调用，而是运行在 Actor 容器里的业务单元；Actor 提供寻址、生命周期、父子拓扑与串行处理。
2. **编排层**：协作流程不是散落在一堆 `if/else` 代码里，而是以 YAML 定义 `roles + steps + routes`，再由 workflow runtime 解析、校验、装配并执行。

## 它解决什么问题

普通 Agent 写法很直接：收到事件，写固定代码处理，再发下一个事件。但当流程开始出现顺序、分支、循环、并行、投票、人工审批、外部 Connector 时，硬编码流程会有两个明显问题：流程变更要改代码，控制逻辑也会在多个 Agent 里重复出现。`workflow-runtime` 把这个问题说得很清楚：硬编码 Agent 适合固定逻辑，workflow 适合可编排、可调整、可复用的流程逻辑。

Aevatar 的做法是把“怎么协作”拆到 Workflow YAML，把“怎么可靠地运行协作”交给 Actor + Event 内核，把“怎么观察结果”交给统一 Projection Pipeline。源码首页也明确说，API 推送结果和读模型共享同一投影输入链路，见 `README.md` 、。

## Actor + Event 内核

读 Aevatar 时，先别把 Agent 想成一个普通 class。Foundation 的词汇表把核心层次拆成五个概念：Agent 是业务逻辑单元，Actor 是 Agent 的运行容器，Runtime 在 Stream 之上提供 Actor 语义，Event Context 负责当前 Actor 执行中的 publish/send，Stream 是 `EventEnvelope` 的传输骨架。这个分层见 `architecture` 。

这里最容易混淆的是 “Event”。Aevatar 里有两层不同的东西：

| 名称 | 它是什么 | 不是啥 | 事实源位置 |
|---|---|---|---|
| `EventEnvelope` | Actor runtime 的消息信封，可以装 command、signal、reply、timeout 或业务事件 payload | 不是事件溯源的持久化事实 | `agent_messages` |
| `StateEvent` | Event Sourcing 写侧事实，带版本、事件类型、事件数据、actor id | 不是 runtime message transport | `agent_messages` |

换成人话：`EventEnvelope` 负责“消息怎么在 Actor 之间流动”，`StateEvent` 负责“什么业务事实已经被这个 Actor 明确提交”。`architecture` 和 `event-sourcing` 都在强调这条边界。

这也是 Aevatar 和很多轻量 Agent 编排写法的关键差异：它很在意事实归属。运行中的状态不能随便散在 Host、API 或中间层字典里；有状态 Actor 只有显式持久化领域事件后，事实才进入 `EventStore`。这条主线解释了为什么文档反复强调 Actor-owned state、CQRS、Projection 和 ReadModel。

## Workflow YAML 编排

Workflow YAML 是 Aevatar 的默认协作语言。它的最小结构是 `name`、`roles`、`steps`：`roles` 定义参与者，`steps` 定义每一步做什么，步骤通过 `role` 或 `target_role` 指向参与者。`workflow-primitives` 给了正式写法，`role-model` 说明 Role 会在运行时变成 role actor。

最小例子就是 `workflows/simple_qa.yaml`：

```yaml
name: simple_qa
roles:
  - id: assistant
    name: Assistant
    system_prompt: "You are a helpful assistant."
steps:
  - id: answer
    type: llm_call
    role: assistant
```

这段 YAML 不是配置装饰品。`WorkflowParser` 会把 YAML 解析成 `WorkflowDefinition`，其中包含角色和步骤列表，见 `WorkflowParser` 、`WorkflowDefinition` 。运行时会把职责拆给两个 Actor：

- `WorkflowGAgent` 是 definition actor，只持有 workflow YAML、编译结果、版本等 definition facts；它的类注释和绑定逻辑见 `WorkflowGAgent` 、。
- `WorkflowRunGAgent` 是 run actor，一次运行一个 actor，承载本次运行的全部事实；`src/workflow/README.md` 、给出了这条运行语义。

真正推进步骤的是 `WorkflowExecutionKernel`。它通过 `CanHandle` 识别 `StartWorkflowEvent`、`StepCompletedEvent`、timeout、retry、stop、compensation 等事件，再在 `HandleStartWorkflowAsync` 中初始化 run state、写入 input 变量、选择入口步骤并 dispatch 第一步。对应源码在 `WorkflowExecutionKernel` 、。

## 与 LangGraph / AutoGen / MAF 的定位差异

这里不做外部框架评测，也不替它们下结论；这张表只帮读者把常见心智模型切到 Aevatar 自己的源码事实上。

| 如果你带着这个心智模型来读 | 在 Aevatar 里要先看什么 | 为什么 |
|---|---|---|
| LangGraph 式“图节点怎么连” | 先看 `Workflow YAML` 的 `roles + steps + routes`，再看 `WorkflowExecutionKernel` 如何把 step 事件推进下去 | Aevatar 的流程图不是单独的应用层对象，而是落到 run actor 的事件管线和执行状态里 |
| AutoGen 式“Agent 之间怎么对话” | 先看 Role 如何在 YAML 中声明，再看 `WorkflowRunGAgent` 创建 run-scoped role actor | Role 不是随手 new 出来的聊天对象，而是 workflow 参与者、LLM 身份和外部能力授权的组合 |
| MAF 或通用 Agent Framework 式“Agent SDK 提供哪些抽象” | 先看 Foundation 的 Agent / Actor / Runtime / Stream / EventEnvelope 分层，再看 Host、Application、Projection 的职责边界 | Aevatar 的核心不是只暴露一组 Agent API，而是把命令、Actor 决策、领域事件、Projection、ReadModel 连成一条链路 |

一个更短的对照是：

| 常见写法 | Aevatar 的取舍 |
|---|---|
| 流程写在代码里，改步骤顺序要改实现 | 流程写在 YAML，`WorkflowParser` 解析，`WorkflowExecutionKernel` 推进 |
| Agent 会话状态容易变成框架或应用层临时状态 | run facts 归 `WorkflowRunGAgent`，definition facts 归 `WorkflowGAgent` |
| 实时输出和读模型可能是两条链路 | Projection 与 AGUI/SSE/WS 共享同一 Actor envelope 输入流 |
| 外部工具调用散在业务代码里 | Connector / tool / role allowlist 进入 workflow 与 role 语义 |

## 怎么读后面的章节

这篇序章只回答“它是什么”。后面可以按三条线继续读：

1. 想知道一次请求怎么跑：看 `01/02-chat-api-and-sse.md`、`03/02-event-envelope-vs-state-event.md`、`05/02-two-projection-modes.md`。
2. 想写 workflow：看 `02/01-yaml-grammar.md`、`02/04-step-modules-catalog.md`、`02/05-workflows-walkthrough.md`。
3. 想理解内核：看 `03/01-agent-actor-runtime.md`、`03/03-gagent-base.md`、`03/04-state-guard-and-event-sourcing.md`。

看完这一篇，至少应该能回答三个问题：

- Aevatar 为什么不是单纯的 LLM wrapper？
- 为什么它强调 Actor + Event，而不是只强调 Agent 对话？
- 为什么 Workflow YAML 是主入口，而不是 README 里的演示配置？
