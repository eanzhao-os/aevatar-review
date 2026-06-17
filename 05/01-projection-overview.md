# Projection 总览:Command→EventEnvelope→Actor→持久化→Projection→ReadModel

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## 统一投影链路

`cqrs-projection` 的 mermaid 主链路:

```text
Host API → Application Service → Actor/GAgent → Actor Envelope Stream + EventStore → Projection Pipeline → ReadModel → Query API/SSE/WS
```

**关键口径**():EventEnvelope Stream 是**运行时消息流**,不是 ES 事实流;command → envelope → actor mailbox;只有显式持久化的领域事件进 EventStore;projection 消费 actor envelope stream。

> 这条链路解释了为什么 API 推送(SSE/WS/AGUI)和 CQRS 读模型共享同一投影输入 —— 它们都是这条链路的输出分支(`architecture.md` )。

---

## CQRS 统一命令骨架 7 步(`cqrs-projection.md` )

1. Normalize Command
2. Resolve Target
3. Create CommandContext
4. Build Envelope
5. Dispatch via `IActorDispatchPort`
6. Accepted Receipt
7. Observe Result

`DefaultCommandInteractionService`(`DefaultCommandInteractionService` )实现:Prepare → Observe → DispatchPrepared → Accepted callback → Pump → finalize → cleanup。**observation-before-dispatch**(重构注释):观察绑定必须在 dispatch 前完成,否则会丢事件。

---

## 投影约束(`cqrs-projection.md` )

1. CQRS/AGUI/SSE/WS 共享同一投影输入
2. EventTypeUrl 精确匹配
3. miss 时 no-op
4. lease/session 生命周期
5. one-to-many 全分支
6. `IProjectionStoreDispatcher` + Store Binding
7. committed-state 发布 hook 激活 durable scope
8. durable 激活由 committed-state publication owner hook 触发(非 command 路径)
9. host 侧只留薄适配

---

## 验收

1. 投影主链路?(Command→EventEnvelope→Actor→持久化→Projection→ReadModel)
2. 为什么 SSE 和 ReadModel 共享输入?(都是同一投影链路的输出分支)
3. 命令骨架第 5 步?(Dispatch via IActorDispatchPort)
4. observation 和 dispatch 的顺序?(observation-before-dispatch,否则丢事件)

⟦AI:AUTO-LOOP⟧
