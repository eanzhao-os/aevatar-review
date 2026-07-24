# 07 周边

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

- `docs/canon/architecture.md`:Foundation 主链路,Actor + Event Sourcing + CQRS/Projection 的基本口径。
- `docs/canon/architecture-vocabulary.md`:Router、Port、ReadModel、Projection 等词汇边界。
- `docs/canon/aevatar-channel-architecture.md`:Channel Runtime 与外部通道接入的长文 RFC。

---

07 章不把周边组件当项目树清单讲,而是回答一个问题:外部能力怎样接入 aevatar 主干。

> 想先看「所有 input 入口是否统一」的横切总览,直接读 [10 Input 入口统一](10-input-ingress-unification.md):它把模型 API / 直聊 / 通道 / 语音 / Studio / Workflow 等入口列全,并按路由策略、动作词汇、工具骨干、命令骨架、投影链五层给出统一矩阵与剩余缺口。

| 面 | 章节 | 主干接入职责 | 当前状态 |
|---|---|---|---|
| 横切总览 | [10 Input 入口统一](10-input-ingress-unification.md) | 全部 input 入口清单 + 五层统一矩阵 + 彻底统一还差什么 | 现役;语音工具循环 / Workflow chat 第二前门为主要缺口 |
| 入口面 | [01 Channel](01-channels.md) | Lark/Telegram 经 NyxID relay 规范化成 `ChatActivity`,进入 `ConversationGAgent` 与 turn runner | 现役;Telegram direct-callback/local credential 已出支持契约,见 01 的 ⚠️ |
| 入口面 | [08 Lark 全链路](08-lark-end-to-end.md) | 沿一条 Lark 消息走完 relay → `ChatActivity` → `ConversationGAgent` → run actor → `ToolCallLoop` → relay 回复 | 现役;run actor = `AgentRunGAgent`,`RoleGAgent` 不在此热路径 |
| 入口面 | [03 ChatRouting](03-chat-routing.md) | `ChatRoutePolicyGAgent` 持配置,入口同步调用无状态 resolver,再进入模型/tool 执行 | 现役;不是 router actor |
| 历史/待决策 | [02 A2A](02-a2a-interop.md) | 历史设计是在 Host boundary 把 A2A task 映射到框架消息 | ⚠️ 源码已删/空壳,不按当前能力使用 |
| 能力面 | [04 Voice](04-voice-presence.md) | Voice 是挂到已有 actor 生命周期的 EventModule capability | 现役;ADR-0033 仍是 proposed,凭证落地状态见 04 的 ⚠️ |
| 能力面 | [09 边缘×大脑全链路](09-voice-presence-edge-brain.md) | `voice-presence` 边缘把 provider/persona/工具/回合外包给 aevatar+NyxID,沿一次语音问答走完每一跳 | 现役;broker 代码已落 mainnet、prod 端到端可用,ADR-0033 头仍 proposed |
| 能力面 | [05 Studio + Scripting](05-studio-and-scripting.md) | Studio 以 member/team 聚合组织产品事实;Scripting 挂成可发布能力 | 现役;旧 demos 只按历史素材处理,见 05 的 ⚠️ |
| 数据面 | [11 文件全链路](11-file-handling-end-to-end.md) | 一个文件经 ingress 落进 `workflow-file://` artifact store 换成 `WorkflowFileRef`;主链路只流 ref,字节只在归一化/`document_extract`/多模态/`workflow_file_submit` 四个边界出现 | 现役;默认单机文件系统 store + 后台清理;无对象存储/独立 OCR |
| 调度面 | [12 定时任务](12-scheduled-tasks.md) | `ScheduledDispatchGAgent` 持有 schedule/credential facts,durable callback 只负责唤醒,workflow/team service 承担执行 | 现役;canonical Member Automation 用 Agent Key;C1 每 fire exchange 一张短票;旧 SkillRunner 已退役 |
| 观察面 | [06 Console](06-console-web.md) | 前端只消费命令 ACK、API/readmodel 与 SSE/ExecutionTrace,把运行事件归一化成 UI 展示 | 现役;不把前端文件行号当架构主体 |
| 观察面 | [07 Observability](07-observability.md) | Tier1 查询 readmodel,Tier2 只消费 OTel live SSE 做动画 | 设计有效;Inspector demo 源码已删/空壳,见 07 的 ⚠️ |

这一组章节的读法是从外到内:入口先把外部 payload 变成 actor 可处理的强类型消息;能力挂在已有 actor 生命周期或产品聚合上;观察面只读 readmodel 或 SSE,不反向成为事实源。

本 block 只重写文档契约,不恢复 A2A、Inspector demo 或旧 demos 的已删源码。

⟦AI:AUTO-LOOP⟧
