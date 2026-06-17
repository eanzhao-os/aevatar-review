# Orleans Runtime:同一组原语在分布式下的语义

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs` 第 11 行;`IActorDispatchPort.cs` 第 68 行;`IEventPublisher.cs` 第 15 行:三原语(共享,不重复)。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Actors/OrleansActorRuntime.cs` 第 12 行:`IActorRuntime` 实现;第 50/67 行:`GetGrain<IRuntimeActorGrain>`(全局单激活);第 129-140 行:`LinkAsync`(拓扑 + relay)。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Actors/OrleansActorDispatchPort.cs` 第 7、20、30 行:`DispatchAsync` → grain → stream ProduceAsync。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Grains/IRuntimeActorGrain.cs` 第 5 行:`IGrainWithStringKey`(string-keyed = 每 actorId 集群单激活);`RuntimeActorGrain.cs` 第 25 行:`[ImplicitStreamSubscription]`;第 27 行:`IPersistentState<RuntimeActorGrainState>`;第 170-292 行:`HandleEnvelopeAsync`(单线程 grain turn = 邮箱串行;dedup 第 208-213 行;routing 第 219-268 行;`agent.HandleEventAsync` 第 274 行)。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Grains/RuntimeActorGrainState.cs` 第 6-35 行:`[GenerateSerializer]`(AgentId [Id 0]/ParentId [Id 2]/Children [Id 3]/Identity [Id 7])。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Streaming/Streaming/Topology/IStreamTopologyGrain.cs` 第 5 行:分布式 Forward-topology 存储;`OrleansDistributedStreamForwardingRegistry.cs`;`Streaming/DependencyInjection/ServiceCollectionExtensions.cs` 第 11-15 行:`AddAevatarFoundationRuntimeOrleansStreaming()`。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/README.md` 第 3 行:Orleans 提供 IActorRuntime+IActorDispatchPort 平行实现;第 38 行:默认 stream backend InMemory。
- `docs/adr/0002-mainnet-architecture.md` 第 627-699 行:§8.1 三模式表(InMemory/MassTransit-historical/Orleans)+ §8.2 Orleans 分布式拓扑 + §8.3 config keys(`ActorRuntime:Provider=Orleans`/`OrleansStreamBackend`/`OrleansPersistenceBackend`)。

---

## 同一组原语,分布式实现

Foundation 三原语(`IActorRuntime`/`IActorDispatchPort`/`IEventPublisher`)在 Local 和 Orleans 是**同一抽象的两种实现**(`architecture.md:138`)。

**Orleans 实现**:
- `OrleansActorRuntime`(`OrleansActorRuntime.cs`):`GetGrain<IRuntimeActorGrain>(actorId)`(第 50/67 行)—— **Orleans virtual actor 保证全局单激活**
- `OrleansActorDispatchPort`(`OrleansActorDispatchPort.cs`):`DispatchAsync` → grain → `_streams.GetStream(actorId).ProduceAsync(envelope)`(第 30 行)→ 邮箱串行 admission → `DispatchAdmission`
- `OrleansGrainEventPublisher`:`IEventPublisher`(经 stream publish)

---

## RuntimeActorGrain:实际激活

`RuntimeActorGrain`(`RuntimeActorGrain.cs`)是 string-keyed grain(`IGrainWithStringKey`,`IRuntimeActorGrain.cs`)= 每 actorId 集群单激活。

- `[ImplicitStreamSubscription]`(第 25 行)+ `IPersistentState<RuntimeActorGrainState>`(第 27 行)
- `OnActivateAsync`(第 55-77 行):从持久化 kind 解析 identity,绑定 agent
- `HandleEnvelopeAsync`/`HandleEnvelopeAsyncCore`(第 170-292 行):**单线程 grain turn = 邮箱串行处理**;dedup(第 208-213 行)、routing(第 219-268 行)、`agent.HandleEventAsync`(第 274 行)
- self-stream 订阅(第 477-501 行):`SubscribeSelfStreamAsync`/`OnSelfStreamEventAsync` 喂 mailbox

`RuntimeActorGrainState`(`RuntimeActorGrainState.cs`,`[GenerateSerializer]`):`AgentId`[Id 0]、`ParentId`[Id 2]、`Children`[Id 3]、`Identity`[Id 7]。

---

## 分布式拓扑存储

- `IStreamTopologyGrain`(`IStreamTopologyGrain.cs`):分布式 Forward-topology grain(`IGrainWithStringKey`)
- `OrleansDistributedStreamForwardingRegistry`:分布式 `IStreamForwardingRegistry`
- `AddAevatarFoundationRuntimeOrleansStreaming()`(`ServiceCollectionExtensions.cs`):替换为 Orleans 分布式实现

---

## ADR-0002 §8(`0002-mainnet-architecture.md` 第 627-699 行)

- §8.1 三模式:InMemory / MassTransit(历史)/ Orleans
- §8.2 Orleans 分布式拓扑:virtual actor + Kafka + Garnet
- §8.3 config keys:`ActorRuntime:Provider=Orleans`、`OrleansStreamBackend=KafkaProvider`、`OrleansPersistenceBackend=InMemory|Garnet`

> 无独立 Orleans ADR;分布式 Runtime 架构记录在 ADR-0002 §8。

---

## 验收

1. Orleans 怎么保证全局单激活?(string-keyed grain,每 actorId 一个激活)
2. grain turn 和邮箱串行关系?(单线程 grain turn = 邮箱串行)
3. Local 和 Orleans 是同一抽象吗?(是,同一组三原语的两种实现)
4. 分布式拓扑存哪?(IStreamTopologyGrain,分布式 Forward-topology grain)

⟦AI:AUTO-LOOP⟧
