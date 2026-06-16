# StateGuard(AsyncLocal 写保护) + PersistDomainEventAsync + TransitionState reducer

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Core/StateGuard.cs` 第 14 行:`AsyncLocal<bool> Writable`;第 20 行:`BeginWriteScope`(返回 WriteScope);第 23-28 行:`EnsureWritable`(非 writable 抛异常)。
- `src/Aevatar.Foundation.Core/GAgentBase.TState.cs` 第 31-34 行:`State.set` 调 `StateGuard.EnsureWritable()`;第 205-230 行:`PersistDomainEventsAsync`;第 109-118 行:`TransitionState` reducer;第 276-309 行:`PublishCommittedDomainEventsAsync`。
- `src/Aevatar.Foundation.Core/EventSourcing/EventSourcingBehavior.cs` 第 292-293 行:`TransitionState` virtual;第 243 行:replay fold。
- `src/Aevatar.Foundation.Core/EventSourcing/StateTransitionMatcher.cs`:避免 `Any+switch` 样板的 helper。
- 写 scope 开启位置:`GAgentBase.cs:87`(Activate)、`:123`(HandleEvent);`GAgentBase.TState.cs:49`(post-replay)、`:189`(OCC replay fold)、`:224`(commit fold)。
- `src/Aevatar.Foundation.Abstractions/Persistence/IEventStore.cs` 第 17-21 行:`AppendAsync`(OCC → EventStoreCommitResult)。

---

## StateGuard:状态只在事件处理期可写

`StateGuard`(`StateGuard.cs`,37 行,`internal static`)用 `AsyncLocal<bool>`(第 14 行)限制状态写:

- `BeginWriteScope()`(第 20 行)返回 `WriteScope` struct(第 31-36 行),设 `Writable.Value=true`,Dispose 时恢复
- `EnsureWritable()`(第 23-28 行):非 writable 抛 `InvalidOperationException("State can only be modified inside EventHandler / EventModule / OnActivateAsync scopes.")`

**强制点**:`State.set`(`GAgentBase.TState.cs` 第 31-34 行)调 `StateGuard.EnsureWritable()` —— 任何 scope 外的 `_state =` 都会抛异常。

**写 scope 只在这些地方开启**:
- `HandleEventAsync`(`GAgentBase.cs:123`,事件处理)
- `ActivateAsync`(`GAgentBase.cs:87`,激活)
- post-replay(`GAgentBase.TState.cs:49`)
- commit fold(`GAgentBase.TState.cs:224`)
- OCC replay fold(`GAgentBase.TState.cs:189`)

这保证 actor 的串行邮箱模型和状态变更一致 —— 状态只能在处理事件时改,不能在任意代码路径改。

---

## PersistDomainEventAsync:核心 commit 路径

`PersistDomainEventsAsync`(`GAgentBase.TState.cs` 第 205-230 行):

1. `eventSourcing.RaiseEvent(evt)` 缓冲到 `_pending`(第 220 行)
2. `eventSourcing.ConfirmEventsAsync(ct)` 原子 append `StateEvent` 到 `IEventStore`(OCC,第 222 行)—— 冲突抛 `EventStoreOptimisticConcurrencyException`
3. 在 `StateGuard.BeginWriteScope()`(第 224 行)内,`eventSourcing.TransitionState(_state, evt)` fold(第 226 行)
4. `OnStateChangedAsync` hook(第 228 行)
5. `PublishCommittedDomainEventsAsync`(第 229 行)—— 把 committed 事实发布给 observer

OCC 冲突有吸收重载(第 153-163 行):调方提供 `Func<EventStoreOptimisticConcurrencyException, Task<bool>>` 回调决定是否重试。

---

## TransitionState reducer

`GAgentBase<TState>.TransitionState(current, evt)`(`GAgentBase.TState.cs` 第 109-118 行):
- 默认遍历 DI 注册的 `IStateEventApplier<TState>`(按 `Order`,第 257-274 行),返回首个 `TryApply` 成功
- 回退返回 `current` 不变(第 117 行)

agent 可 override 这个方法自定义 fold 逻辑。它被绑进 `EventSourcingBehaviorFactory.Create`(`GAgentBase.TState.cs` 第 239 行),在 replay(`EventSourcingBehavior.cs` 第 243 行)和 live commit(`GAgentBase.TState.cs` 第 226 行)时都执行。

`StateTransitionMatcher`(`StateTransitionMatcher.cs`)是推荐的 helper,避免 `Any+switch` 样板。

---

## RunManager:设计意图,尚未落地

`docs/canon/architecture.md` 第 82 行和 `src/Aevatar.Foundation.Core/README.md` 第 19 行提到 `RunManager`/`RunContextScope`(latest-wins 运行管理),但 `src/` 里**没有**对应类型定义。当前上下文传播机制是 `AsyncLocalAgentContext`/`IAgentContextAccessor`(`src/Aevatar.Foundation.Core/Context/AsyncLocalAgentContext.cs`,在 `Local/DependencyInjection/ServiceCollectionExtensions.cs:93` 注册)。

> 本章把 RunManager 描述为"文档记录的设计意图,尚未实现;当前上下文传播是 `AsyncLocalAgentContext`"。

---

## 验收

1. 状态为什么只能在事件处理期写?(StateGuard 的 AsyncLocal 限制,scope 外抛异常)
2. PersistDomainEventsAsync 的步骤?(RaiseEvent → ConfirmEventsAsync OCC → TransitionState fold → OnStateChangedAsync → PublishCommitted)
3. RunManager 存在吗?(设计意图,未实现;当前是 AsyncLocalAgentContext)

⟦AI:AUTO-LOOP⟧
