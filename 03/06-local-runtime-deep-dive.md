# Local Runtime 深入:LocalActorRuntime / LocalActor(邮箱串行)/ LocalActorPublisher

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActorRuntime.cs` 第 23-331 行:`IActorRuntime` 实现;第 25 行:`ConcurrentDictionary<string,LocalActor> _actors`;第 231-251 行:`LinkAsync`(拓扑 + relay)。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActor.cs` 第 11-242 行:`IActor` 实现(邮箱串行);第 13-17 行:`Channel<MailboxWorkItem> _mailbox`(`SingleReader=true`);第 50 行:`ActivateAsync` 启 pump;第 52-109 行:self-stream 订阅 + route 分类;第 174-181 行:`EnqueueAsync`;第 183-187 行:`ProcessMailboxAsync`;第 189-228 行:`ProcessMailboxItemAsync`。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActorPublisher.cs` 第 15-151 行:`IEventPublisher` + `ICommittedStateEventPublisher`(见 `03/05`)。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActorDispatchPort.cs` 第 5-26 行:`DispatchAsync` → `AcceptDispatchedEnvelope`。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/DependencyInjection/ServiceCollectionExtensions.cs` 第 37-106 行:`AddAevatarRuntime()` 装配。
- `src/Aevatar.Foundation.Runtime/Streams/InMemoryStream.cs` 第 14 行:`// DEV/TEST ONLY` 注释;第 52-62 行:双 channel(ingress bounded + dispatch unbounded);第 169-220 行:`PumpLoopAsync`/`DispatchLoopAsync`(顺序 subscriber)。
- `docs/canon/architecture.md` 第 128-138 行:InMemory 仅 dev/test;生产用 Orleans/Garnet。

---

## LocalActorRuntime

`LocalActorRuntime`(`LocalActorRuntime.cs` 第 23-331 行)是 `IActorRuntime` 的本地实现:
- `ConcurrentDictionary<string,LocalActor> _actors`(第 25 行)—— 所有 actor 存内存字典
- Create/Get/Destroy/Link/Unlink
- `LinkAsync`(第 231-251 行):同时更新拓扑(parent.AddChild + child.SubscribeToParent)+ stream relay binding

---

## LocalActor:邮箱串行

`LocalActor`(`LocalActor.cs` 第 11-242 行)的核心是**邮箱串行处理**:

- `Channel<MailboxWorkItem> _mailbox`(第 13-17 行):`CreateUnbounded`,`SingleReader=true, SingleWriter=false` —— **single reader 保证串行**
- `EnqueueAsync`(第 174-181 行):写 `MailboxWorkItem(envelope, propagateFailure, TaskCompletionSource)`,返回 `completion.Task` 让调用方 await(per-envelope 背压)
- `ActivateAsync`(第 50 行)启动 `_mailboxPump = ProcessMailboxAsync()`
- `ProcessMailboxAsync`(第 183-187 行):`await foreach` 读 mailbox,**严格 one-at-a-time**(单消费者 await 每个 item 后才读下一个)
- `ProcessMailboxItemAsync`(第 189-228 行):可选 dedup(第 195-206 行)→ `EventHandleScope`(第 208 行)→ `Agent.HandleEventAsync(envelope)`(第 210 行)→ `SetResult`/`SetException`

**入站路径**(两个入口进 mailbox):
1. self-stream 订阅回调(`ActivateAsync` 第 52-109 行):订阅自己的 `IStream`,按 route(observer/direct/self/up-from-child/forwarded-down)分类,匹配的 `EnqueueAsync`(第 67/74/81/94/104 行)
2. `LocalActorDispatchPort.DispatchAsync` → `AcceptDispatchedEnvelope`(第 127 行)→ `EnqueueAsync`

---

## 为什么 InMemory 仅限开发测试

- `InMemoryStream.cs` 第 14 行注释:`// DEV/TEST ONLY transport - production must use a durable Orleans/Kafka stream provider.`
- `docs/canon/architecture.md` 第 128-129 行:InMemory 组件仅用于开发/测试;生产用 `Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet`
- 第 136 行:InMemory 仅保留本地开发与自动化测试

生产目标(第 131-138 行):分布式 `IActorRuntime` 实现**全局单激活 + 邮箱串行**;非 InMemory store;`AddAevatarFoundationRuntimeOrleans()` 暴露同一组原语(`IActorRuntime`/`IActorDispatchPort`/`IEventPublisher`)。

---

## Stream 层串行机制

`InMemoryStream`(`InMemoryStream.cs`):
- 双 channel:bounded `_ingressChannel`(第 52-57 行,容量 4096,`SingleReader=true`)+ unbounded `_dispatchChannel`(第 58-62 行,`SingleReader=SingleWriter=true`)
- `PumpLoopAsync`(第 169-184 行):ingress → dispatch(串行交接)
- `DispatchLoopAsync`(第 186-220 行):`await foreach` dispatch,**顺序**调每个 subscriber(`await sub(envelope)` 第 197 行)—— 无 fire-and-forget(重构注释第 16-17 行明确移除了并发 fire-and-forget)

---

## AddAevatarRuntime DI 装配

`ServiceCollectionExtensions.cs` 第 37-106 行(`AddAevatarRuntime()`):
- `IStreamProvider → InMemoryStreamProvider`(第 47-51 行)
- `IActorRuntime → LocalActorRuntime`(第 63-70 行)
- `IActorDispatchPort → LocalActorDispatchPort`(第 71 行)
- `IEventStore → InMemoryEventStore`(第 81 行)、`IStateStore<> → InMemoryStateStore<>`(第 78 行)
- `IEventDeduplicator → MemoryCacheDeduplicator`(第 90 行)
- kind registry(第 103 行)
- 可切换 file persistence:`AddFileEventStore`(第 111-125 行)

---

## 验收

1. LocalActor 怎么保证串行?(`SingleReader=true` channel + `await foreach` one-at-a-time)
2. 为什么 InMemory 不能用于生产?(进程内,无持久化,无分布式单激活)
3. 生产用什么?(Orleans + Garnet,同一组 IActorRuntime 原语)

⟦AI:AUTO-LOOP⟧
