# WorkflowGAgent(definition) vs WorkflowRunGAgent(run) 职责切分

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/workflow/Aevatar.Workflow.Core/WorkflowGAgent.cs` 第 16-17 行:`[GAgent("workflow.definition")]`,`WorkflowGAgent : GAgentBase<WorkflowState>`;第 21 行:`BindWorkflowDefinitionAsync`;第 46-99 行:`ApplyBindWorkflowDefinition`;第 101 行:`EvaluateWorkflowCompilation`;第 128 行:`EnsureWorkflowNameCanBind`;第 150 行:`SubWorkflowDefinitionResolveRequestedEvent` handler;第 224 行:`WorkflowDefinitionSnapshot`。
- `src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs` 第 35-38 行:`[GAgent("workflow.run")]`,`WorkflowRunGAgent : GAgentBase<WorkflowRunState>, IWorkflowExecutionStateHost`(1779 行);第 40-43 行:`WorkflowRunState.Status`;第 93-103 行:`SubWorkflowOrchestrator`;第 112-168 行:`IWorkflowExecutionStateHost` 实现;第 935-983 行:模块装配;第 996 行:`TransitionState`;第 1202-1213 行:`ApplyWorkflowExecutionStateUpserted/Cleared`。
- `docs/canon/workflow-runtime.md` 第 56-82 行:两个 actor 的职责定义。

---

## 两个 actor,两种职责

aevatar 把 workflow 的"定义"和"运行"拆成两个 actor:

| | `WorkflowGAgent`(definition) | `WorkflowRunGAgent`(run) |
|---|---|---|
| GAgent kind | `workflow.definition`(`WorkflowGAgent.cs:16`) | `workflow.run`(`WorkflowRunGAgent.cs:35`) |
| 行数 | ~260 行 | **1779 行** |
| 持有 | YAML + 编译结果 + 版本(definition facts) | 全部执行事实(run facts) |
| 职责 | 解析/编译/版本管理 + 子 workflow 快照服务 | 生命周期 + 模块装配 + 步骤派发宿主 + 执行上下文 + 模块状态持久化 + 补偿 |

这是"Actor 即业务实体"原则的体现:一个 actor = 一个业务实体。definition actor 是 workflow 定义实体,run actor 是单次运行实体。

---

## WorkflowGAgent(definition actor)—— 只持有 YAML + 编译结果

`WorkflowGAgent`(`WorkflowGAgent.cs`)持有 **definition-only** 状态(`WorkflowState`):`WorkflowYaml`、`WorkflowName`、`InlineWorkflowYamls`、`ScopeId`、`SourceKind`、`Version`、`Compiled`、`CompilationError`(`ApplyBindWorkflowDefinition`,第 66-99 行)。

**关键行为**:
- `BindWorkflowDefinitionAsync`(第 21 行):持久化 `BindWorkflowDefinitionEvent`;拒绝重绑到不同 workflow 名(`EnsureWorkflowNameCanBind`,第 128 行)。
- 每次 bind 都编译:`_parser.Parse` + `WorkflowValidator.Validate`(`EvaluateWorkflowCompilation`,第 101 行)。
- 处理的事件:`BindWorkflowDefinitionEvent`(第 46/63 行)和 `SubWorkflowDefinitionResolveRequestedEvent`(第 50/150 行)—— 后者为父 run 提供子 workflow 定义快照(第 224 行构造 `WorkflowDefinitionSnapshot`,回复 `SubWorkflowDefinitionResolvedEvent` / `…ResolveFailedEvent`)。

**它不执行步骤**。只拥有 YAML + 编译后的 `WorkflowDefinition`。

---

## WorkflowRunGAgent(run actor)—— 持有全部执行事实

`WorkflowRunGAgent`(`WorkflowRunGAgent.cs`,**1779 行**)实现 `GAgentBase<WorkflowRunState>, IWorkflowExecutionStateHost`。

**执行状态**(`WorkflowRunState`):
- `RunId`、`ScopeId`、`Status`(`running`/`completed`/`failed`/`stopped`,第 40-43 行)
- `ExecutionContext`(typed `WorkflowRunExecutionContextState`)
- **`ExecutionStates`**(`scopeKey → Any` protobuf 状态 map)—— 模块状态存这里
- `WorkflowName` + 补偿/saga 事实

`TransitionState` reducer 在第 996 行;`ApplyWorkflowExecutionStateUpserted`(第 1202 行,`next.ExecutionStates[scopeKey] = evt.State`)/ `ApplyWorkflowExecutionStateCleared`(第 1213 行)。

**模块装配**(第 935-983 行):构造 `WorkflowExecutionKernel(_compiledWorkflow, this)` + `WorkflowExecutionBridgeModule(executors, this)`(第 977-980 行)。`executors` 来自每个展开后的模块名 `_stepExecutorFactory.TryCreate(name)`(第 961-973 行)。terminal 状态不装模块(第 940 行)。

**`IWorkflowExecutionStateHost` 实现**(第 112-168 行)—— 这是 run actor 作为"状态宿主"的核心接口:

| 方法 | 行号 | 作用 |
|---|---|---|
| `RuntimeContext` | 第 112 行 | 运行时上下文 |
| `ExecutionContextSnapshot` | 第 118 行 | 只读快照 |
| `UpdateExecutionContextAsync` | 第 121 行 | 持久化 `WorkflowRunExecutionContextUpdatedEvent` |
| `GetExecutionState` | 第 143 行 | 读 `State.ExecutionStates` |
| `UpsertExecutionStateAsync` | 第 154 行 | 持久化 `WorkflowExecutionStateUpsertedEvent` |
| `ClearExecutionStateAsync` | 第 170 行 | 清除模块状态 |
| 补偿宿主方法 | 第 183/214 行 | saga 补偿 |

---

## 模块状态怎么落到 WorkflowRunState

步骤模块通过 `ctx.LoadState/SaveState` → `WorkflowExecutionContextAdapter` → 宿主的 `UpsertExecutionStateAsync` → 存到 `State.ExecutionStates`。kernel 自己的状态在 key `"workflow_execution_kernel"` 下(见 `02/03-execution-kernel.md`)。

子 workflow 编排委托给 `SubWorkflowOrchestrator`(第 93-103 行构造)。

---

## 为什么这么切分

1. **definition 可复用**:同一个 workflow 定义可以被多次 run 复用,definition actor 只编译一次。
2. **run 隔离**:每次运行一个 run actor,执行事实互不干扰。
3. **状态权威唯一**:run actor 是本次运行的唯一事实源(`WorkflowRunState`),中间层不持有 `runId → context` 进程内映射(`docs/adr/0002-mainnet-architecture.md` 第 1054 行)。

---

## 验收

1. 两个 actor 各自持有什么?(definition:YAML + 编译结果;run:全部执行事实)
2. 为什么 definition actor 不执行步骤?(职责单一:只管定义;执行是 run actor 的事)
3. 模块状态存哪?(`WorkflowRunState.ExecutionStates[scopeKey]`,第 1202 行)

⟦AI:AUTO-LOOP⟧
