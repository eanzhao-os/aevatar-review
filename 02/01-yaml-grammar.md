# Workflow YAML 完整语法:name/roles/steps + steps[].type 取值全表

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowDefinition.cs` 第 11-51 行:`WorkflowDefinition`(Name/Roles/Steps/Configuration/OnFailure);第 73-88 行:`GetNextStep` 分支解析顺序;第 95-112 行:`WorkflowRuntimeConfiguration.ClosedWorldMode` + `WorkflowRunFailurePolicy`。
- `src/workflow/Aevatar.Workflow.Core/Primitives/StepDefinition.cs` 第 6-78 行:`StepDefinition`(Id/Type/TargetRole/Parameters/Next/Branches/Retry/OnError/TimeoutMs/Compensation);第 84-109 行:`StepRetryPolicy` + `StepErrorPolicy`。
- `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowDefinition.cs` 第 118-186 行:`RoleDefinition`(Id/Name/AgentKind/SystemPrompt/Provider/Model/Temperature/MaxTokens/Connectors allowlist)。
- `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowParser.cs` 第 19-21 行:YamlDotNet snake_case;第 83-99 行:`Parse`;第 143-164 行:`MapStep`(默认 type=`llm_call`,canonical 化);第 835 行:`ApplyErgonomicDefaults`;第 23-75 行:`RootParameterMappings`(~50 个根字段提升)。
- `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowPrimitiveCatalog.cs` 第 12-57 行:canonical 别名表 + `IdentityPrimitives` + `CapabilityPrimitives`;第 71 行:`ToCanonicalType`。
- `src/workflow/Aevatar.Workflow.Core/WorkflowCoreModulePack.cs` 第 9-41 行:31 个模块注册(canonical step type 注册表)。
- `docs/canon/workflow-primitives.md` 第 41-73 行:role schema;第 74-102 行:saga compensation;第 104-784 行:primitive 分组(Data/Control/AI/Composition/Integration/Human/Engine-internal)。

---

## 顶层结构

一个 workflow YAML 的最小骨架(综合 `WorkflowDefinition.cs` + `workflow-primitives.md`):

```yaml
name: my_workflow              # 必填,WorkflowDefinition.cs:16
description: "..."             # 可选,:21
when_to_use: "..."             # 可选,:26
roles:                          # 必填,List<RoleDefinition>,:31
  - id: assistant
    name: Assistant
    system_prompt: "..."
    provider: openai
    model: gpt-4o
    connectors: [github_router] # role connector allowlist,:186
steps:                          # 必填,List<StepDefinition>,:36
  - id: answer
    type: llm_call              # 默认 type,:145
    role: assistant
    next: done                  # 显式后继
    retry:                      # StepDefinition.cs:63
      max_attempts: 3
      backoff: exponential
      delay_ms: 1000
    on_error:                   # :73
      strategy: fallback
      fallback_step: handle_error
    timeout_ms: 30000           # :78
configuration:                  # 可选,:41
  closed_world_mode: true       # :95-101
on_failure:                     # 可选,:46
  action: fork_from_failed_step # :112
  max_attempts: 2
```

> **注意**:aevatar **没有** `RouteDefinition` 类型。路由通过 `StepDefinition.Branches`(dict)+ `Next` + `on_error`/`retry`/`compensation` 表达(`StepDefinition.cs` 第 43-78 行)。

---

## roles:角色定义(`RoleDefinition`,`WorkflowDefinition.cs` 第 118-186 行)

| 字段 | 行号 | 含义 |
|---|---|---|
| `id` | 第 123 行 | 角色标识,step 通过 `role`/`target_role` 引用 |
| `name` | 第 128 行 | 显示名 |
| `agent_kind` | 第 133 行 | 默认 `workflow.role-agent` |
| `system_prompt` | 第 138 行 | 系统提示词 |
| `provider` / `model` / `temperature` / `max_tokens` | 第 143-168 行 | LLM 配置 |
| `max_tool_rounds` / `max_history_messages` | 第 168 行 | 工具轮次/历史上限 |
| `event_modules` / `event_routes` | 第 173-178 行 | 动态事件模块 |
| `agent_tool_scope` | 第 180 行 | 工具作用域 |
| `connectors` | 第 186 行 | **connector allowlist**(授权,不是连接定义) |

`connectors` 是授权清单:`connector_call` 步骤运行时检查 role 的 `connectors` 是否包含该 connector(`src/Aevatar.Configuration/README.md` 第 44-50 行)。省略 `role` 则跳过 allowlist(向后兼容,第 50 行)。

---

## steps:步骤定义 + 分支解析

`StepDefinition`(`StepDefinition.cs` 第 6-78 行):

| 字段 | 行号 | 含义 |
|---|---|---|
| `id` | 第 11 行 | 步骤标识 |
| `type` | 第 16 行 | 步骤类型(默认 `llm_call`,第 145 行) |
| `target_role` / `role` | 第 21 行 | 目标角色 |
| `parameters` | 第 26 行 | `Dictionary<string,string>` 参数 |
| `next` | 第 43 行 | 显式后继 |
| `branches` | 第 58 行 | `Dictionary<string,string>?` 条件分支 |
| `retry` | 第 63 行 | `StepRetryPolicy`(max_attempts 1-10,backoff fixed/exponential) |
| `on_error` | 第 73 行 | `StepErrorPolicy`(fail/skip/fallback) |
| `timeout_ms` | 第 78 行 | 超时 |
| `compensation` | 第 48 行 | saga 补偿 |

**分支解析顺序**(`WorkflowDefinition.GetNextStep`,第 73-88 行):
`Branches[branchKey]` → `Branches["_default"]` → `step.Next` → next-by-index。

**重试**(`StepRetryPolicy`,第 84-94 行):`max_attempts` 默认 3,范围 1-10;`backoff` = `fixed`/`exponential`;`delay_ms` 默认 1000。

**错误策略**(`StepErrorPolicy`,第 99-109 行):`strategy` = `fail`/`skip`/`fallback`;可选 `fallback_step`、`default_output`。

---

## steps[].type 取值全表

canonical 类型注册在 `WorkflowPrimitiveCatalog.cs`(第 12-57 行)和 `WorkflowCoreModulePack.cs`(第 9-41 行,31 个模块)。别名通过 `ToCanonicalType`(第 71 行)归一化。

### 别名归一化表(`WorkflowPrimitiveCatalog.cs` 第 12-41 行)

| 别名 | canonical |
|---|---|
| `loop` | `while` |
| `sub_workflow` | `workflow_call` |
| `for_each` / `foreach_llm` | `foreach` |
| `parallel_fanout` / `fan_out` | `parallel` |
| `mapreduce` / `map_reduce_llm` | `map_reduce` |
| `judge` | `evaluate` |
| `select` | `race` |
| `assert` | `guard` |
| `sleep` | `delay` |
| `publish` | `emit` |
| `wait` | `wait_signal` |
| `bridge_call` / `cli_call` / `mcp_call` / `http_get` / `http_post` / `http_put` / `http_delete` | `connector_call` |
| `secure_connector` | `secure_connector_call` |
| `secret_input` | `secure_input` |
| `vote_consensus` | `vote` |
| `mutex` | `lease` |
| `schedule_workflow` | `self_reschedule` |

### canonical 类型全集(31 个,`WorkflowCoreModulePack.cs` 第 9-41 行)

| 分组 | 类型 | 最小 YAML 片段 |
|---|---|---|
| **Data** | `transform` | `type: transform` + `operation` |
| | `assign` | `type: assign` + `target`/`value` |
| | `retrieve_facts` | `type: retrieve_facts` |
| | `cache` | `type: cache` + `key`/`ttl_ms` |
| **Control** | `conditional` | `type: conditional` → `true`/`false` 分支 |
| | `switch` | `type: switch` + `on` + `branch.*` |
| | `while` | `type: while` + `condition`/`max_iterations` |
| | `foreach` | `type: foreach` + `delimiter`/`sub_step_type` |
| | `parallel` | `type: parallel` + `workers`/`vote_step_type` |
| | `race` | `type: race` → 首个完成者胜 |
| | `map_reduce` | `type: map_reduce` + map/reduce 子步 |
| | `workflow_call` | `type: workflow_call` + `workflow` |
| | `dynamic_workflow` | `type: dynamic_workflow` |
| | `delay` | `type: delay` + `duration_ms` |
| | `wait_signal` | `type: wait_signal` + `signal_name` |
| | `checkpoint` | `type: checkpoint` |
| | `lease` | `type: lease` + acquire/renew/release |
| | `guard` | `type: guard` + 校验 |
| **AI** | `llm_call` | `type: llm_call` + `role`/`prompt_prefix` |
| | `tool_call` | `type: tool_call` + `tool`/`operation` |
| | `evaluate` | `type: evaluate` + threshold 分支 |
| | `reflect` | `type: reflect` + `max_rounds` |
| **Integration** | `connector_call` | `type: connector_call` + `connector`/`operation` |
| | `emit` | `type: emit` + `event_type`/`payload` |
| | `notify` | `type: notify` |
| | `actor_send` | `type: actor_send` |
| **Human** | `human_input` | `type: human_input` |
| | `human_approval` | `type: human_approval` + `on_reject` |
| | `secure_input` | `type: secure_input` |
| **Engine-internal** | `workflow_loop` | 自动注入,用户不写(= `WorkflowExecutionKernel`) |
| | `workflow_yaml_validate` | `type: workflow_yaml_validate` |

> 每个 step type 的详细语义、参数、最小 YAML 见 `02/04-step-modules-catalog.md`。

---

## 语法糖:`RootParameterMappings` + `ApplyErgonomicDefaults`

`WorkflowParser` 对 LLM 生成的 YAML 做了大量容错(`WorkflowParser.cs`):

- **`RootParameterMappings`**(第 23-75 行):~50 个根字段(`prompt`、`workers`、`vote_step_type`、`signal_name`、`timeout`、`quorum_count`、`key`、`ttl_ms`…)自动提升进 `parameters`,允许把参数写在 step 根级。
- **`ApplyErgonomicDefaults`**(第 835 行):`http_get/post/put/delete` → 自动补 `method`;`mcp_call` → `operation=<tool>`;`foreach_llm` → `sub_step_type=llm_call`;`map_reduce_llm` → map+reduce llm_call。

这让手写和 LLM 生成都能用更自然的写法,parser 统一归一化。

---

## 最小示例(simple_qa)

`workflows/simple_qa.yaml`(第 1-9 行):

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

这是最小合法 workflow:1 个 role + 1 个 `llm_call` step,无路由。`WorkflowParser.Parse`(第 83 行)把它解析成 `WorkflowDefinition`,`EntryStepId` = `Steps[0].Id`(第 51 行)。

---

## 验收

1. workflow YAML 的必填顶层字段?(`name`、`roles`、`steps`,`WorkflowDefinition.cs` 第 16/31/36 行)
2. `switch` 步骤的分支怎么解析?(`Branches[key]` → `_default` → `Next` → next-by-index,第 73-88 行)
3. `http_get` 是 canonical 类型吗?(不是,归一化成 `connector_call`,`WorkflowPrimitiveCatalog.cs` 第 12-41 行)
4. role 的 `connectors` 是什么?(授权 allowlist,不是连接定义,第 186 行)

⟦AI:AUTO-LOOP⟧
