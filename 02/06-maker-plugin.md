# Maker 插件边界:maker_recursive + maker_vote、IWorkflowModulePack、架构门禁

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/MakerModulePack.cs` 第 10-25 行:`IWorkflowModulePack` named `workflow.extensions.maker`(第 18 行),注册 `maker_vote`(第 14 行)+ `maker_recursive`/`maker_recursive_solve`(第 15 行)。
- `src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/Modules/MakerVoteModule.cs` 第 15-16 行:`Name => "maker_vote"`,`Priority => 6`;第 28-29 行:`k` 默认 1、`max_response_length` 默认 2200。
- `src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/Modules/MakerRecursiveModule.cs` 第 19-22 行:state key `"maker_recursive"`、`Name => "maker_recursive"`、`Priority => 3`。
- `src/workflow/extensions/Aevatar.Workflow.Extensions.Maker/ServiceCollectionExtensions.cs` 第 6-12 行:`AddWorkflowMakerExtensions()` → `AddWorkflowModulePack<MakerModulePack>()`。
- `src/workflow/Aevatar.Workflow.Core/WorkflowModuleFactory.cs` 第 29-52 行:`IWorkflowModuleFactory` 从所有 pack 构建 name→module map。
- `docs/canon/overview.md` 第 2/7/15 行:Maker 定位;第 51-65 行:§4 Maker 插件边界;第 106-112 行:架构门禁。
- `docs/adr/0006-multi-agent-evolution.md` 第 4 行(status superseded)、第 7 行(title)、第 227-258 行(Phase 2-A worker actor-ization)、第 299 行(superseded note → ADR-0034)。

---

## Maker 是什么

Maker 是 aevatar 的**多 Agent 协作求解插件**,提供两个 workflow 步骤模块:

| 模块 | 文件 / Name 行 | 说明 |
|---|---|---|
| `maker_vote` | `MakerVoteModule.cs:15` | first-to-ahead-by-k 投票,带响应长度红旗过滤(`k` 默认 1,`max_response_length` 默认 2200) |
| `maker_recursive` | `MakerRecursiveModule.cs:21` | 递归 MAKER 求解:原子性决策 + 递归分解 + 每阶段投票;state 存 key `"maker_recursive"` |

它不是独立系统,而是通过 `IWorkflowModulePack` 机制挂进 workflow 的两个步骤模块。

---

## IWorkflowModulePack 注册体系

workflow 的模块注册通过 `IWorkflowModulePack` 接口。每个 pack 贡献一组模块:

- `WorkflowCoreModulePack`(Core,31 个模块)
- `MakerModulePack`(`workflow.extensions.maker`,2 个模块)
- `WorkflowScheduleModulePack`(`workflow.extensions.schedules`,1 个)

`WorkflowModuleFactory`(`WorkflowModuleFactory.cs` 第 29-52 行)从所有注册的 pack 构建 case-insensitive name→module map,拒绝重复名(第 40 行)。

Maker 的注册入口:`AddWorkflowMakerExtensions()`(`ServiceCollectionExtensions.cs` 第 6-12 行)→ `AddWorkflowModulePack<MakerModulePack>()`。这个入口只在 Mainnet Host 的 `AddAevatarPlatform(options => EnableMakerExtensions = true)` 时被调用(见 `01/01-hosts-and-composition.md`)。

---

## 为什么从"独立 Host"降级成"Workflow 插件"

`docs/canon/overview.md` §4(第 51-65 行)明确 Maker 插件边界:

**Maker 的定位**(`overview.md` 第 15 行):"Workflow 插件扩展,不是独立能力系统"。

**职责**(第 57-59 行):
- 提供 `maker_recursive`/`maker_vote` 模块
- `AddWorkflowMakerExtensions()` 入口(platform 启用 Maker 时调用)
- 通过 `IWorkflowModulePack` 贡献

**依赖约束**(第 61-65 行):
- ✅ 允许:plugin → `Workflow.Core`/`Workflow.Abstractions` + Foundation abstractions
- ❌ 禁止:`Workflow` 反向依赖 plugin 实现(第 64 行)
- ❌ 禁止:独立 CQRS/Projection pipeline(第 65 行)

**架构门禁**(`overview.md` 第 106-112 行)CI 强制:
- 禁止 `Workflow → Maker` 反向依赖(第 108 行)
- 禁止残留独立 Maker 项目(第 109 行)
- 禁止 `AddMakerCapability()`/`/api/maker/*`(第 110 行)
- 强制 Mainnet 通过 `AddAevatarPlatform(...EnableMakerExtensions=true...)` 装配(第 111 行)

**为什么这么做**:Maker 本质是两个 workflow 步骤模块。让它成为插件而非独立 Host,消除了平行"第二系统",符合 "单一主干,插件扩展" 的架构哲学。

---

## ADR-0006 历史背景

`docs/adr/0006-multi-agent-evolution.md`(status: **superseded**,第 4 行)是"Workflow 调度 Actor 化 & 多智能体协作演进方案"RFC(第 7 行)。关键内容:

- 单个 `WorkflowRunGAgent` 串行化步骤执行,即使 `ParallelFanOutModule`/`ForEachModule`/`MapReduceModule` 也是(第 27-29 行)
- Phase 2-A 提出 worker actor-ization,保持 run-actor 为唯一状态权威(第 227-258 行)
- 背压(默认 `max_concurrent_workers_per_run = 20`,第 191 行)和幂等 `execution_id`(第 200-219 行)在此提出,现已实现(见 `02/03-execution-kernel.md`)
- 原可选补偿草案(§Phase 2-B,第 262-297 行)被 ADR-0034 的 saga 补偿取代(第 299 行 note)
- Foundation MultiAgent 生产面(`TaskBoardGAgent`/`TeamManagerGAgent`)已退役(第 15-19 行)

---

## 验收

1. Maker 提供哪两个模块?(`maker_vote` + `maker_recursive`)
2. Maker 通过什么机制注册?(`IWorkflowModulePack`,MakerModulePack)
3. 为什么禁止 `Workflow → Maker` 反向依赖?(Maker 是 Workflow 的插件,反向依赖违反分层,overview.md 第 64 行)
4. 架构门禁禁止什么?(独立 Maker 项目、`/api/maker/*`、`AddMakerCapability()`,第 108-110 行)

⟦AI:AUTO-LOOP⟧
