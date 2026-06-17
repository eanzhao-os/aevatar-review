# Aevatar 结构化中文解读

> 自顶向下读懂 Aevatar —— 一次请求的生命周期、Workflow YAML、Actor+Event 内核、CQRS 双投影、分布式目标态。

本书是 [aevatar](https://github.com/aelf/aevatarAI) 的中文技术解读,**43 篇章节全部锚定 `~/Code/aevatar` 事实源**。每篇用少量高价值路径作为入口,正文用流程图、状态图、示例和边界论证讲清模型,不脑补、不泛泛而谈。

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
| [01 宿主与入口](01/index.md) | 3 | Mainnet vs Workflow Host / chat API / Run 语义 |
| [02 编排层](02/index.md) | 7 | YAML 语法 / def-run actor / Kernel / 30+ 模块 / 示例 / Maker / Connector |
| [03 运行内核](03/index.md) | 6 | Agent/Actor/Runtime / EventEnvelope vs StateEvent / GAgentBase / StateGuard / 路由 / LocalRuntime |
| [04 AI 能力层](04/index.md) | 4 | RoleGAgent / LLM Providers / Tool 体系 / ChatRuntime |
| [05 CQRS 读侧](05/index.md) | 4 | Projection 总览 / 双投影链 / ReadModel 存储 / Workflow 投影 |
| [06 分布式](06/index.md) | 5 | 当前 vs 目标 / Orleans / Kafka / Garnet / 架构门禁 |
| [07 周边](07/index.md) | 7 | Channel / A2A / ChatRouting / Voice / Studio / 前端 / 可观测性 |
| [08 附录](08/index.md) | 3 | 术语表 / 文档索引 / Demo Cookbook |

!!! tip "进度:43/43 全部完成 ✅"

## 事实源入口约定

每篇章节开头都有「事实源/设计抽象(以 ~/Code/aevatar 为准)」清单,默认只列不超过 3 条高价值 `.cs` / `.yaml` / `docs/canon/*` / `docs/adr/*` 路径 + 行号锚点。所有论断都能回指事实源,但正文不以源码文件和行号索引代替解释。

!!! warning "外部仓库边界"
    `~/Code/aevatar`(上游 `aelf:aevatarAI/aevatar`)为**只读**事实源,本仓库不得修改其任何文件。

---

*本书由 consensus-loop 驱动 43 个 GitHub issue 逐篇产出,每篇经 design-consensus → implement → review 全链路。*
