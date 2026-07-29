---
status: index
---

# 10 分布式与生产运行

> 覆盖生产拓扑、Orleans、Garnet、Kafka、安全授权、managed Codex、可观测性与架构门禁。

## 阅读前提

- 先读 `02`、`05`；涉及无人值守执行时补读 `09`。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-production-topology-and-configuration.md) | `current` | 生产拓扑与配置：先选择一致性档位，再组合能力 |
| 2 | [02](02-orleans-runtime.md) | `current` | Orleans Runtime：逻辑 Actor、Grain Turn 与可恢复投递 |
| 3 | [03](03-garnet-clustering-and-secret-storage.md) | `current` | Garnet 聚类与秘密存储：共享后端，不共享语义 |
| 4 | [04](04-streaming-transport-and-kafka.md) | `mixed` | Streaming Transport 与 Kafka：一个 Stream 身份，一套 Partition 所有权 |
| 5 | [05](05-authentication-scope-and-admin-authorization.md) | `current` | Authentication、Scope 与 Admin：四道门，不是一枚万能 Token |
| 6 | [06](06-managed-codex-sandbox-and-delegation.md) | `mixed` | Managed Codex：把执行、调用凭证与 Sandbox 委托拆成三层 |
| 7 | [07](07-observability-status-and-observatory.md) | `current` | Observability、Status 与 Observatory：观测事实，不接管业务事实 |
| 8 | [08](08-architecture-and-security-guards.md) | `current` | Architecture 与 Security Guards：把边界写成可失败的规则 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [11 场景教程与 Cookbook](../11/index.md)。
