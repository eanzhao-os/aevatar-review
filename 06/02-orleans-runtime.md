# Orleans Runtime:同一组原语在分布式下的语义

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## 同一组原语,分布式实现

Foundation 三原语(`IActorRuntime`/`IActorDispatchPort`/`IEventPublisher`)在 Local 和 Orleans 是**同一抽象的两种实现**(`architecture.md`)。

**Orleans 实现**:
- `OrleansActorRuntime`(`OrleansActorRuntime`):`GetGrain<IRuntimeActorGrain>(actorId)`(第 50/67 行)—— **Orleans virtual actor 保证全局单激活**
- `OrleansActorDispatchPort`(`OrleansActorDispatchPort`):`DispatchAsync` → grain → `_streams.GetStream(actorId).ProduceAsync(envelope)`()→ 邮箱串行 admission → `DispatchAdmission`
- `OrleansGrainEventPublisher`:`IEventPublisher`(经 stream publish)

---

## RuntimeActorGrain:实际激活

`RuntimeActorGrain`(`RuntimeActorGrain`)是 string-keyed grain(`IGrainWithStringKey`,`IRuntimeActorGrain`)= 每 actorId 集群单激活。

- `[ImplicitStreamSubscription]`()+ `IPersistentState<RuntimeActorGrainState>`()
- `OnActivateAsync`():从持久化 kind 解析 identity,绑定 agent
- `HandleEnvelopeAsync`/`HandleEnvelopeAsyncCore`():**单线程 grain turn = 邮箱串行处理**;dedup()、routing()、`agent.HandleEventAsync`()
- self-stream 订阅():`SubscribeSelfStreamAsync`/`OnSelfStreamEventAsync` 喂 mailbox

`RuntimeActorGrainState`(`RuntimeActorGrainState`,`[GenerateSerializer]`):`AgentId`[Id 0]、`ParentId`[Id 2]、`Children`[Id 3]、`Identity`[Id 7]。

---

## 分布式拓扑存储

- `IStreamTopologyGrain`(`IStreamTopologyGrain`):分布式 Forward-topology grain(`IGrainWithStringKey`)
- `OrleansDistributedStreamForwardingRegistry`:分布式 `IStreamForwardingRegistry`
- `AddAevatarFoundationRuntimeOrleansStreaming()`(`ServiceCollectionExtensions`):替换为 Orleans 分布式实现

---

## ADR-0002 §8(`0002-mainnet-architecture.md` )

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
