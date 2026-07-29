---
status: index
---

# 05 CQRS、Projection 与 Audit

> 区分 command receipt、committed fact、projection、read model、live observation 与 audit。

## 阅读前提

- 先读 `02/02–04`；Workflow 读者可补 `03/03`。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-command-event-projection-readmodel.md) | `current` | Command、committed fact、Projection 与 ReadModel：把写入结果和查询视图分开 |
| 2 | [02](02-committed-state-and-observation.md) | `current` | Committed state 与 observation：持久事实和实时可见性不是一回事 |
| 3 | [03](03-projection-lifecycle-and-leases.md) | `current` | Projection lifecycle 与 lease：scope actor 拥有状态，handle 只负责清理 |
| 4 | [04](04-readmodel-stores-versioning-and-rebuild.md) | `mixed` | ReadModel store、versioning 与 rebuild：副本可覆盖，修复必须显式 |
| 5 | [05](05-workflow-agui-and-live-observation.md) | `current` | Workflow AGUI 与 live observation：同源映射，不同持久性 |
| 6 | [06](06-audit-trail-lifecycle-and-export.md) | `current` | Audit Trail：生命周期、追加语义与 CloudEvents 导出 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [06 产品资源与身份](../06/index.md)。
