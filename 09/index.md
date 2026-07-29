---
status: index
---

# 09 Automation、调度与凭证

> 解释 Automation 资源、Schedule actor、durable callback、owner 授权、Agent Key、Vault reference 与版本化 canary。

## 阅读前提

- 先读 `05/02` 与 `06/01–04`，理解 owner、ACK 与 read model。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-automation-resource-api-and-readmodels.md) | `current` | Team Member Automation：资源 API、所有权与读模型 |
| 2 | [02](02-scheduled-actor-callback-and-fire.md) | `current` | Schedule Actor、Durable Callback 与 Fire：唤醒不是执行事实 |
| 3 | [03](03-owner-authorization-and-agent-key.md) | `current` | Owner 授权与 Agent Key：把无人值守权限固定成可重验计划 |
| 4 | [04](04-vault-reference-and-revocation-compensation.md) | `current` | Vault Reference 与撤销补偿：秘密不成为业务事实 |
| 5 | [05](05-production-canary-and-recovery.md) | `mixed` | Production Canary 与恢复：一次执行只能证明它绑定的版本 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [10 分布式与生产运行](../10/index.md)。
