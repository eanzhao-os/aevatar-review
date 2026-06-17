# ★ 最易误解的边界:EventEnvelope(runtime message) vs StateEvent(事实源)

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Abstractions/agent_messages.proto` 第 44-51 行:`EventEnvelope`;第 142-149 行:`StateEvent`;第 151-160 行:commit result 与 committed-state publication payload。
- `src/Aevatar.Foundation.Abstractions/Persistence/IEventStore.cs` 第 11-41 行:Event Sourcing append log,包含 OCC append、range query 与压缩。
- `src/Aevatar.Foundation.Abstractions/Persistence/IStateStore.cs` 第 11-21 行:snapshot store,不是写侧事实源。
- `src/Aevatar.Foundation.Core/GAgentBase.TState.cs` 第 205-230 行:领域事件 commit + state fold;第 276-309 行:committed state event 发布给 observer。
- `docs/canon/architecture.md` 第 51-55 行、第 71 行:EventEnvelope 与 StateEvent 的边界。
- `docs/canon/event-sourcing.md` 第 13 行、第 23-27 行:Runtime envelope 流不是 Event Sourcing 事实源。

---

## 两层先分开

`EventEnvelope` 的名字很容易误导人。它虽然叫 Event,但它在 Foundation 里首先是 runtime message envelope:外部 command、内部 signal、reply、timeout,甚至业务事件 payload,都可以先装进这个信封,经 Stream 进入 actor。

Event Sourcing 的权威事实在另一层。只有 actor 在处理消息后显式持久化领域事件,它才会变成 `StateEvent` 并进入 `EventStore`。所以这两层有关联,但权威性完全不同。

![EventEnvelope 与 StateEvent 是两层](../assets/03-two-layers.png)

---

## 为什么不能把消息流当事实源

运行时消息的目标是“送达并触发处理”。它可能是请求、控制信号、回包或转发出来的观察消息。这样的流适合驱动 actor,但不适合作为业务事实源:它没有天然表达“这个领域决定已经被提交”,也不能直接承担 OCC、版本递增和可重放 reducer 的责任。

`EventStore` 的价值就在这里。它把 actor 已经确认的领域事件追加成带版本的事实流,让恢复、投影和一致性观察有同一个锚点。`IStateStore` 只适合 snapshot/恢复优化,不能替代这个事实层。

---

## 从消息层进入事实层

典型路径是:actor 收到一个 runtime envelope,业务 handler 做判断,然后调用持久化领域事件的 API。提交成功后,框架把 committed events fold 回当前 state,再发布 committed-state observation,让 projection/live sink 看到“事实已经发生”。

这也是 Aevatar 和普通“消息总线 + mutable object”写法的关键区别。消息本身不等于事实;actor 的领域决定经过 `EventStore` 提交后,才成为可恢复、可投影、可审计的事实。

<details>
<summary>proto 字段证据</summary>

- `EventEnvelope` 位于 `agent_messages.proto` 第 44-51 行,包含 `id`、`timestamp`、`payload`、`route`、`propagation`、`runtime`。
- `StateEvent` 位于第 142-149 行,包含 `event_id`、`timestamp`、`version`、`event_type`、`event_data`、`agent_id`。
- route 细节位于第 53-79 行,包含 direct、topology publication、observer publication。
- `EventStoreCommitResult` 与 `CommittedStateEventPublished` 位于第 151-160 行。

</details>

---

## 一个判断口诀

看到 `EventEnvelope`,先问:它是不是只是 actor runtime 正在传的一封消息?多数情况下答案是“是”。看到 `StateEvent`,再问:它是不是已经通过 EventStore append 成功、带版本、可重放的领域事实?这个答案才决定它能不能作为写侧权威。

---

## 验收

1. EventEnvelope 是 Event Sourcing 的事实吗?(不是,它是 runtime message envelope)
2. 什么才是写侧事实源?(`StateEvent` + `EventStore`)
3. 一个业务事件怎么从消息层进入事实层?(actor 显式持久化领域事件,提交成功后成为 StateEvent)
4. proto 字段在哪里看?(正文不贴字段表;字段细节在本篇 `<details>` 和关键代码清单里)

⟦AI:AUTO-LOOP⟧
