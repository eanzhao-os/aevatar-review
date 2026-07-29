---
status: index
---

# 04 AI 执行与工具

> 解释 RoleGAgent、LLM 路由、ToolLoop、request-local catalog、审批授权与 prompt overlay。

## 阅读前提

- 先读 `03/01` 与 `03/03`，理解 workflow run 怎样驱动一步执行。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-role-agent-and-streaming-run.md) | `current` | RoleGAgent 与流式执行：actor turn、会话事实和终态重放 |
| 2 | [02](02-llm-providers-and-route-selection.md) | `current` | LLM Provider 与路由选择：四类身份、owner 覆盖和安全 failover |
| 3 | [03](03-tool-loop-catalog-and-presentation.md) | `current` | Tool loop、请求目录与展示事实：先冻结权力，再执行调用 |
| 4 | [04](04-tool-approval-and-authorization.md) | `current` | 工具审批与授权：先确定调用者，再等待可恢复的决定 |
| 5 | [05](05-prompt-overlays-and-agent-context.md) | `current` | Prompt overlay 与 Agent context：固定层序不是授权层级 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [05 CQRS、Projection 与 Audit](../05/index.md)。
