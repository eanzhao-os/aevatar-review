---
status: index
---

# 03 Workflow 编排

> 把 YAML、定义/运行身份、执行内核、原语、挂起恢复、补偿与 Connector 准入串成一条链。

## 阅读前提

- 先读 `02/01–05`，掌握 actor、event 与 dispatch。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-workflow-model-and-identities.md) | `current` | Workflow 模型与身份：定义、运行、草稿与发布物不是同一个对象 |
| 2 | [02](02-yaml-schema-and-validation.md) | `current` | Workflow YAML：一个根模式，四道不同的关 |
| 3 | [03](03-execution-kernel-and-outcomes.md) | `current` | Workflow 执行内核：把异步步骤收敛成一个 run 终态 |
| 4 | [04](04-primitives-catalog.md) | `current` | Workflow 原语目录：canonical type、模块与输出契约 |
| 5 | [05](05-pause-signal-approval-and-resume.md) | `current` | Workflow 暂停与恢复：signal、人工审批和 delivery 边界 |
| 6 | [06](06-saga-compensation-and-recovery.md) | `mixed` | Workflow Saga：反向补偿、OutcomeUncertain 与恢复 |
| 7 | [07](07-connectors-and-capability-admission.md) | `current` | Connector 与外部能力准入：所有权、readiness 和证据时效 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [04 AI 执行与工具](../04/index.md)。
