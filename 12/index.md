---
status: index
---

# 12 架构演进、案例与开放缺口

> 用时间线、issue 主题、退役组件、事故案例与 canon drift 解释演进，不把目标态写成当前能力。

## 阅读前提

- 先读 `00/02`，再按案例回到负责 current 行为的主题章。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-evolution-method-and-timeline.md) | `historical` | 演进方法与时间线：先分清三套时钟，再解释“为什么变成现在这样” |
| 2 | [02](02-issue-decisions-by-theme.md) | `mixed` | Issue 决策主题图：把 280 个工作项还原成边界迁移 |
| 3 | [03](03-retired-and-superseded-components.md) | `historical` | 已退役与被替代组件：删除什么、由谁接管、留下什么约束 |
| 4 | [04](04-incident-case-studies.md) | `mixed` | 事故案例：症状相似时，先找到真正拥有事实的边界 |
| 5 | [05](05-open-gaps-and-canon-drift.md) | `target` | 开放缺口与 Canon Drift：只登记当前限制，不预支未来能力 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [13 术语与事实源索引](../13/index.md)。
