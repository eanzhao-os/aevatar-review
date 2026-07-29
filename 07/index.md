---
status: index
---

# 07 Conversation、NyxIdChat 与 Agent Profile

> 解释多轮会话的 actor owner、ChatHistory、profile snapshot、turn authority 与工具目录。

## 阅读前提

- 先读 `02/01`、`05/02` 与 `06/01`。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-conversation-turn-and-chat-history.md) | `current` | Conversation、Turn 与耐久聊天历史 |
| 2 | [02](02-nyxid-chat-actor-model-and-progress.md) | `current` | NyxIdChat Actor 模型与已提交进度 |
| 3 | [03](03-agent-profile-and-immutable-binding.md) | `current` | Agent Profile 与不可变会话绑定 |
| 4 | [04](04-turn-authority-tool-catalog-and-retry.md) | `current` | Turn 权威、工具目录与重试 |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [08 Ingress、Channel、文件与语音](../08/index.md)。
