---
status: index
---

# 01 启动与请求全景

> 从本地启动进入 Host、Chat / Conversation / Turn 身份，以及 HTTP / WebSocket 流式终态。

## 阅读前提

- 先读 `00/02`，理解 current / mixed 与冻结证据规则。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-quick-start.md) | `current` | 快速上手:本地启动 Host 并完成第一次请求 |
| 2 | [02](02-hosts-and-composition.md) | `current` | Host 与组合：协议终结与能力装配的边界 |
| 3 | [03](03-chat-conversation-turn-contract.md) | `current` | Chat / Conversation / Turn 服务端身份契约 |
| 4 | [04](04-request-streaming-lifecycle.md) | `mixed` | 请求与流式生命周期：从 POST/WS 到终态观测 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [02 Actor 运行内核](../02/index.md)。
