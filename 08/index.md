---
status: index
---

# 08 Ingress、Channel、文件与语音

> 沿外部入口说明身份规范化、Channel credential、Lark delivery、Artifact 引用与 Voice 控制/媒体分层。

## 阅读前提

- 先读 `06/01` 与 `07/01`，区分产品归属和会话归属。

## 按序阅读

| 顺序 | 章节 | 状态 | 阅读入口 |
|---:|---|---|---|
| 1 | [01](01-ingress-normalization-and-routing.md) | `current` | Ingress 规范化与路由：先固定身份，再选择执行意图 |
| 2 | [02](02-channel-runtime-and-credential-boundary.md) | `current` | Channel Runtime 与凭据边界：current durable write 不保存 raw secret material |
| 3 | [03](03-lark-delivery-interaction-and-repair.md) | `mixed` | Lark 投递、交互与修复：把意图、送达事实和平台故障分开 |
| 4 | [04](04-file-artifacts-and-attachments.md) | `current` | 文件工件与附件：让字节停在边界，让引用进入事实层 |
| 5 | [05](05-voice-control-and-media-planes.md) | `mixed` | Voice 控制面与媒体面：actor 记住语义，relay 搬运 PCM |

## 状态图例

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、生产版本证据或目标态。
- `historical`：只保留长期设计教训，不作为现行使用指南。
- `target`：尚未落地，只能作为缺口与退出条件阅读。

## 下一步

- 完成本块后进入 [09 Automation、调度与凭证](../09/index.md)。
