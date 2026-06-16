# ★ 步骤模块全图:30+ Module 逐个讲(配最小 YAML)

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/workflow/Aevatar.Workflow.Core/WorkflowCoreModulePack.cs` 第 9-41 行:31 个模块注册(canonical step type → module 注册表)。
- `src/workflow/Aevatar.Workflow.Core/Modules/*.cs`:每个模块的实现(下表逐个给出文件 + `Name` 行号)。
- `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowPrimitiveCatalog.cs` 第 12-57 行:别名归一化表 + canonical 类型集。
- `src/workflow/Aevatar.Workflow.Core/WorkflowModuleFactory.cs` 第 1-57 行:`IEventModuleFactory` 构建 name→module map,拒绝重复名。
- `src/workflow/Aevatar.Workflow.Core/Composition/WorkflowStepTypeModuleDependencyExpander.cs` 第 1-49 行:依赖展开(有 `target_role` 自动加 `llm_call`)。
- `docs/canon/workflow-primitives.md` 第 104-784 行:primitive 分组(Data/Control/AI/Composition/Integration/Human/Engine-internal)。
- 扩展包:`src/workflow/extensions/Aevatar.Workflow.Extensions.Schedules/WorkflowScheduleModulePack.cs` 第 9-12 行(`self_reschedule`);`src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/MakerModulePack.cs` 第 12-16 行(`maker_vote`/`maker_recursive`)。

---

## 模块注册机制

`WorkflowCoreModulePack`(`WorkflowCoreModulePack.cs` 第 9-41 行)注册 31 个 `IWorkflowModule`。`WorkflowModuleFactory`(`WorkflowModuleFactory.cs` 第 29-52 行)从所有注册的 `IWorkflowModulePack` 构建 case-insensitive name→module map,拒绝重复名(第 40 行)。`WorkflowStepTypeModuleDependencyExpander`(`第 1-49 行`)在编译期展开依赖:有 `target_role` 的 step 自动加 `llm_call`(第 26-27 行)。

canonical 类型集来自 `WorkflowPrimitiveCatalog`(`第 50-57 行` 的 `CapabilityPrimitives`)+ `IdentityPrimitives`(`第 43-48 行`)。

---

## 全图(31 + 扩展)

### Control / 流程控制

| 类型 | 文件 / Name 行 | 最小 YAML | 说明 |
|---|---|---|---|
| `conditional` | `ConditionalModule.cs:16` | `type: conditional`<br>`condition: "{{steps.x.output == 'ok'}}"` | 二分支,emit `true`/`false` branch key |
| `switch` | `SwitchModule.cs:17` | `type: switch`<br>`on: "{{steps.x.output}}"`<br>`branch.a: step_a`<br>`branch.b: step_b` | 多路分支,按 `on` + `branch.*` |
| `while` (alias `loop`) | `WhileModule.cs:21` | `type: while`<br>`condition: "..."`<br>`max_iterations: "10"`<br>`step: {id: ..., type: ...}` | 循环子步直到条件 false / max |
| `foreach` (alias `for_each`) | `ForEachModule.cs:30` | `type: foreach`<br>`input: "{{steps.x.output}}"`<br>`delimiter: "\n"`<br>`sub_step_type: llm_call` | 按分隔符拆分,fan out 子步 |
| `parallel` (alias `parallel_fanout`) | `ParallelFanOutModule.cs:27` | `type: parallel`<br>`workers: 3`<br>`vote_step_type: vote` | fan out N 个 worker,converge,可选 vote |
| `race` (alias `select`) | `RaceModule.cs:18` | `type: race`<br>`candidates: [...]` | fan out,首个完成者胜 |
| `map_reduce` (alias `mapreduce`) | `MapReduceModule.cs:19` | `type: map_reduce`<br>`map: {...}`<br>`reduce: {...}` | 并行 map 分片,再 reduce |
| `workflow_call` (alias `sub_workflow`) | `WorkflowCallModule.cs:17` | `type: workflow_call`<br>`workflow: sub_wf_name` | 调用子 workflow |
| `dynamic_workflow` | `DynamicWorkflowModule.cs:23` | `type: dynamic_workflow` | 从前序输出提取 YAML 块,重配 run actor |
| `delay` (alias `sleep`) | `DelayModule.cs:18` | `type: delay`<br>`duration_ms: 5000` | 暂停 |
| `wait_signal` (alias `wait`) | `WaitSignalModule.cs:23` | `type: wait_signal`<br>`signal_name: user_reply` | 挂起等外部 `SignalReceivedEvent`(≤90 min) |
| `checkpoint` | `CheckpointModule.cs:16` | `type: checkpoint`<br>`name: after_extract` | 写命名 checkpoint,resume/audit |
| `lease` (alias `mutex`) | `LeaseModule.cs:21` | `type: lease`<br>`action: acquire`<br>`key: resource_x` | 跨 run 单例资源协调(acquire/renew/release) |
| `guard` (alias `assert`) | `GuardModule.cs:17` | `type: guard`<br>`condition: "..."`<br>`on_fail: fail` | 输入校验门(fail/skip/branch) |

### Data / 数据

| 类型 | 文件 / Name 行 | 最小 YAML | 说明 |
|---|---|---|---|
| `transform` | `TransformModule.cs:29` | `type: transform`<br>`operation: uppercase`<br>`input: "{{steps.x.output}}"` | 确定性文本/json/数值变换(trim/uppercase/json_extract/group_by/sum/…) |
| `assign` | `AssignModule.cs:16` | `type: assign`<br>`target: result`<br>`value: "done"` | 写 workflow 变量 |
| `retrieve_facts` | `RetrieveFactsModule.cs:18` | `type: retrieve_facts`<br>`query: "..."`<br>`top_k: 5` | 关键词检索 top-k 片段 |
| `cache` | `CacheModule.cs:18` | `type: cache`<br>`key: "..."`<br>`ttl_ms: 60000` | 按 key+TTL 缓存子步结果 |

### AI / 人工智能

| 类型 | 文件 / Name 行 | 最小 YAML | 说明 |
|---|---|---|---|
| `llm_call` | `LLMCallModule.cs:32` | `type: llm_call`<br>`role: assistant`<br>`prompt_prefix: "..."` | 调目标 role 的 LLM |
| `tool_call` | `ToolCallModule.cs:31` | `type: tool_call`<br>`tool: search_web`<br>`operation: search` | 调注册的 tool/function/MCP tool(approval-aware) |
| `evaluate` (alias `judge`) | `EvaluateModule.cs:25` | `type: evaluate`<br>`role: judge`<br>`threshold: 0.8` | LLM 打分 + 阈值分支 |
| `reflect` | `ReflectModule.cs:25` | `type: reflect`<br>`role: critic`<br>`max_rounds: 3` | 自反思改进循环 |

### Integration / 集成

| 类型 | 文件 / Name 行 | 最小 YAML | 说明 |
|---|---|---|---|
| `connector_call` (alias `bridge_call`/`cli_call`/`mcp_call`/`http_*`) | `ConnectorCallModule.cs:31` | `type: connector_call`<br>`connector: github_router`<br>`operation: list_repos` | 调 HTTP/CLI/MCP/host_callback connector |
| `emit` (alias `publish`) | `EmitModule.cs:15` | `type: emit`<br>`event_type: job_done`<br>`payload: "..."` | 发布事件 |
| `notify` | `NotifyModule.cs:12` | `type: notify`<br>`target: lark`<br>`card: "..."` | 渲染交互卡片/通知 |
| `actor_send` | `ActorSendModule.cs:13` | `type: actor_send`<br>`target_actor: "..."`<br>`message: "..."` | 给目标 actor 发 typed message |

### Human / 人工

| 类型 | 文件 / Name 行 | 最小 YAML | 说明 |
|---|---|---|---|
| `human_input` | `HumanInputModule.cs:23` | `type: human_input`<br>`prompt: "请补充信息"` | 挂起等自由文本人工输入 |
| `human_approval` | `HumanApprovalModule.cs:23` | `type: human_approval`<br>`prompt: "是否批准?"`<br>`on_reject: fail` | 挂起等 approve/reject |
| `secure_input` (alias `secret_input`) | `SecureInputModule.cs:18` | `type: secure_input`<br>`credential: "..."` | 凭据绑定的安全输入采集 |

### Engine-internal / 引擎内部

| 类型 | 文件 | 说明 |
|---|---|---|
| `workflow_loop` | `Execution/WorkflowExecutionKernel.cs:36` | 主循环调度器,**自动注入**,用户不写(见 `02/03-execution-kernel.md`) |
| `workflow_yaml_validate` | `WorkflowYamlValidateModule.cs:12` | 校验 YAML body 是否符合 workflow grammar |

### 扩展包(非 Core)

| 类型 | 包 / 文件 | 说明 |
|---|---|---|
| `self_reschedule` (alias `schedule_workflow`) | `Aevatar.Workflow.Extensions.Schedules` / `WorkflowSelfRescheduleModule.cs` | 自我重调度 |
| `maker_vote` | `Aevatar.Workflow.Extensions.Maker` / `MakerVoteModule.cs:15` | first-to-ahead-by-k 投票 |
| `maker_recursive` | `Aevatar.Workflow.Extensions.Maker` / `MakerRecursiveModule.cs:21` | 递归 MAKER 求解(见 `02/06-maker-plugin.md`) |

---

## 依赖展开(`WorkflowStepTypeModuleDependencyExpander.cs`)

编译期自动展开依赖(第 1-49 行):
- 有 `target_role` 的 step 自动加 `llm_call`(第 26-27 行)
- 解析 `*_step_type` 参数键(第 29-37 行)
- `foreach` 无 `sub_step_type` 时自动加 `parallel`(第 39-43 行)

这让你写更简洁的 YAML,编译期补全隐含依赖。

---

## 验收

1. `workflow_loop` 是用户写的吗?(不是,自动注入的 `WorkflowExecutionKernel`)
2. `http_get` 归一化成什么?(`connector_call`)
3. `parallel` 和 `race` 的区别?(parallel 等全部 converge;race 取首个完成者)
4. 有 `target_role` 的 step 自动加什么依赖?(`llm_call`)

⟦AI:AUTO-LOOP⟧
