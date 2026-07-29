---
status: index
---

# 02 Actor 运行内核

> 解释 Agent、Actor、Runtime、Envelope、StateEvent、路由与生命周期的不变量。

## 阅读前提

- 建议先读 `01/03`，区分请求身份与 actor 身份。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-agent-actor-runtime.md) | `current` | Agent / Actor / Runtime:三层分离与传输底座 |
| 2 | [02](02-envelope-command-event-query.md) | `current` | Envelope 消息语义 —— command / reply / signal / domain event / query 的分野 |
| 3 | [03](03-gagent-event-pipeline.md) | `current` | GAgent 事件处理管线：一条消息进入 actor 之后 |
| 4 | [04](04-state-event-sourcing-and-guard.md) | `current` | 状态与事件溯源：StateEvent、reducer 与 StateGuard |
| 5 | [05](05-dispatch-routing-and-topology.md) | `current` | Dispatch、路由与拓扑:消息怎么找到 Actor |
| 6 | [06](06-local-runtime-and-lifecycle.md) | `current` | Local Runtime 与 Actor 生命周期 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [03 Workflow 编排](../03/index.md)。
