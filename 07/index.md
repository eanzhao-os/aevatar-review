# 07 周边

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

- `docs/canon/architecture.md`:Foundation 主链路,Actor + Event Sourcing + CQRS/Projection 的基本口径。
- `docs/canon/architecture-vocabulary.md`:Router、Port、ReadModel、Projection 等词汇边界。
- `docs/canon/aevatar-channel-architecture.md`:Channel Runtime 与外部通道接入的长文 RFC。

---

07 章不把周边组件当项目树清单讲,而是回答一个问题:外部能力怎样接入 aevatar 主干。

| 面 | 章节 | 主干接入职责 | 当前状态 |
|---|---|---|---|
| 入口面 | [01 Channel](01-channels.md) | Lark/Telegram 经 NyxID relay 规范化成 `ChatActivity`,进入 `ConversationGAgent` 与 turn runner | 现役;Telegram direct-callback/local credential 已出支持契约,见 01 的 ⚠️ |
| 入口面 | [03 ChatRouting](03-chat-routing.md) | `ChatRoutePolicyGAgent` 持配置,入口同步调用无状态 resolver,再进入模型/tool 执行 | 现役;不是 router actor |
| 历史/待决策 | [02 A2A](02-a2a-interop.md) | 历史设计是在 Host boundary 把 A2A task 映射到框架消息 | ⚠️ 源码已删/空壳,不按当前能力使用 |
| 能力面 | [04 Voice](04-voice-presence.md) | Voice 是挂到已有 actor 生命周期的 EventModule capability | 现役;ADR-0033 仍是 proposed,凭证落地状态见 04 的 ⚠️ |
| 能力面 | [05 Studio + Scripting](05-studio-and-scripting.md) | Studio 以 member/team 聚合组织产品事实;Scripting 挂成可发布能力 | 现役;旧 demos 只按历史素材处理,见 05 的 ⚠️ |
| 观察面 | [06 Console](06-console-web.md) | 前端只消费 API/SSE/readmodel,把运行事件归一化成 UI 事件 | 现役;不把前端文件行号当架构主体 |
| 观察面 | [07 Observability](07-observability.md) | Tier1 查询 readmodel,Tier2 只消费 OTel live SSE 做动画 | 设计有效;Inspector demo 源码已删/空壳,见 07 的 ⚠️ |

这一组章节的读法是从外到内:入口先把外部 payload 变成 actor 可处理的强类型消息;能力挂在已有 actor 生命周期或产品聚合上;观察面只读 readmodel 或 SSE,不反向成为事实源。

⟦AI:AUTO-LOOP⟧
