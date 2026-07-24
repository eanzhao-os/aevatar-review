# Aevatar 结构化中文解读

> 自顶向下读懂 Aevatar —— 一次请求的生命周期、Workflow YAML、Actor+Event 内核、CQRS 双投影、分布式目标态。

本书是 [aevatar](https://github.com/aelf/aevatarAI) 的中文技术解读,**当前 PLAN 的 85 篇章节全部锚定 `~/Code/aevatar` 事实源**。每篇用少量高价值路径作为入口,正文用流程图、状态图、示例和边界论证讲清模型,不脑补、不泛泛而谈。

## 这本书讲什么

Aevatar 不是一个普通的 Agent 框架。它用 **Actor + Event Sourcing + CQRS** 三件套构建了一套可持久化、可恢复、可观测的多角色 Agent 编排平台。本书帮你搞懂:

- 🎯 **一次 chat 请求怎么流过整个系统**(主线全景图)
- 📝 **怎么写 Workflow YAML**(31 种步骤模块 + 12 个实战示例)
- ⚙️ **Actor / Event / State 内核**怎么工作(EventEnvelope ≠ StateEvent 是最易踩的坑)
- 🔀 **CQRS 双投影链**(Durable Materialization vs Session Observation)
- 🌐 **分布式目标态**(Orleans + Kafka + Garnet 生产语义)

## 怎么读

| 你想 | 先看 |
|---|---|
| 跑起来看一遍 | [Quick Start](00/03-quick-start.md) |
| 理解全局 | [主线全景图](00/04-chat-request-lifecycle.md) |
| 写 workflow | [YAML 语法](02/01-yaml-grammar.md) → [步骤模块全图](02/04-step-modules-catalog.md) |
| 理解内核 | [EventEnvelope vs StateEvent ★](03/02-event-envelope-vs-state-event.md) |
| 理解读侧 | [两条投影主链 ★](05/02-two-projection-modes.md) |

## 全书结构

| 大块 | 篇数 | 内容 |
|---|---|---|
| [00 序章](00/index.md) | 4 | 定位 / 仓库地图 / Quick Start / 主线全景图 |
| [01 宿主与入口](01/index.md) | 4 | Mainnet vs Workflow Host / chat API / Run 语义 / Audit Trail |
| [02 编排层](02/index.md) | 8 | YAML 语法 / def-run actor / Kernel / 模块 / 示例 / Maker / Connector / saga |
| [03 运行内核](03/index.md) | 8 | Agent/Actor/Runtime / Envelope / GAgentBase / StateGuard / 路由 / LocalRuntime / 事实清单 |
| [04 AI 能力层](04/index.md) | 4 | RoleGAgent / LLM Providers / Tool 体系 / ChatRuntime |
| [05 CQRS 读侧](05/index.md) | 4 | Projection 总览 / 双投影链 / ReadModel 存储 / Workflow 投影 |
| [06 分布式](06/index.md) | 6 | 当前 vs 目标 / Orleans / Kafka / Garnet / 架构门禁 / 凭证 |
| [07 周边](07/index.md) | 13 | Channel / Lark / A2A / Voice / Studio / 文件 / 定时任务 / 前端 / 可观测性 |
| [08 附录](08/index.md) | 5 | 术语表 / 文档索引 / Demo Cookbook / 战术与战略路线图 |
| [09 方案区](09/index.md) | 14 | NyxID 服务发布 / 工具所有权 / provision 与 Agent Key 生产证据 |
| [10 已知问题](10/index.md) | 12 | 已确认故障、边界、根因与修复状态 |
| [11 Skills 能力层](11/index.md) | 2 | 控制面 skills / 平台与 probe skills |
| [12 问题复盘](12/index.md) | 1 | 按主题聚合的周度问题复盘 |

!!! tip "进度:85/85 全部完成"

## 事实源入口约定

每篇章节开头都有「事实源/设计抽象(以 ~/Code/aevatar 为准)」清单,默认只列不超过 3 条高价值 `.cs` / `.yaml` / `docs/canon/*` / `docs/adr/*` 路径 + 行号锚点。所有论断都能回指事实源,但正文不以源码文件和行号索引代替解释。

!!! warning "外部仓库边界"
    `~/Code/aevatar`(上游 `aelf:aevatarAI/aevatar`)为**只读**事实源,本仓库不得修改其任何文件。

---

*本书由 consensus-loop、逐章 issue 与 SCOPE_EXTEND 持续演进;当前 PLAN 记录 85/85。*
