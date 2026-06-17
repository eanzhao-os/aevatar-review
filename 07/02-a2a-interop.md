# A2A Interop:历史设计与当前删除状态

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

- `history/2026-03/maf-integration`:A2A v0.3.3-preview 的历史适配设计,位于 Host boundary。
- `src/Aevatar.Interop.A2A.Abstractions/`:当前目录只剩空壳/构建残留。
- `src/Aevatar.Interop.A2A.Hosting/`:当前目录只剩空壳/构建残留。

---

A2A 的历史设计目标是让外部 Agent-to-Agent task 在 Host boundary 被翻译成 aevatar 的运行时消息,而不是让 A2A task state 成为新的事实源。正确方向是:

| A2A 侧 | aevatar 侧 | 边界 |
|---|---|---|
| Agent card | Host 暴露能力说明 | 可发布信息,不是 actor state |
| task send/get/cancel | EventEnvelope/actor command | 进入主干后由 actor/event store 承认事实 |
| task state | actor state + event store/readmodel | A2A 本地 task store 不做权威 |
| subscribe | SSE 观察 | 观察结果不能反推事实 |

⚠️ 当前 HEAD 不提供可用 A2A 运行时。三个 A2A 项目源码已在 8bfd8605c 删除,目录只剩空壳或构建残留;本章不再把 IA2AAdapterService、JSON-RPC endpoints 或 in-memory task store 写成当前能力。

## 决策框

维护者后续需要在三种路径里选一种,本 issue 不替它拍板:

| 选项 | 含义 | 文档影响 |
|---|---|---|
| 删除本篇 | A2A 不再是目标态 | 07 章只保留一条历史索引 |
| 标为历史已放弃 | 保留设计教训 | 本篇留在 07,但明确不可运行 |
| 重新实现 | A2A 仍是产品目标 | 需要新的设计 issue,并重新证明 task state 不绕过 Actor + ES |

在没有新授权前,读者应把 A2A 看成"历史方案和待决策项",不是集成教程。

## 验收

1. A2A adapter 应该在哪一层?Host boundary。
2. A2A task state 是事实源吗?不是,actor state + event store/readmodel 才是。
3. 当前 HEAD 有可运行 A2A 源码吗?没有,只剩空壳/构建残留。

⟦AI:AUTO-LOOP⟧
