# 路由与拓扑:DirectRoute / PublicationRoute.topology / PublicationRoute.observer

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Abstractions/agent_messages.proto` 第 53-60 行:`EnvelopeRoute`(publisher_actor_id + oneof direct/publication);第 62-64 行:`DirectRoute`;第 66-79 行:`PublicationRoute`(oneof topology/observer);第 29-40 行:`TopologyAudience`(SELF/PARENT/CHILDREN/PARENT_AND_CHILDREN)/`ObserverAudience`(COMMITTED_FACTS)。
- `src/Aevatar.Foundation.Abstractions/EnvelopeRouteSemantics.cs` 第 5-41 行:`CreateTopologyPublication`/`CreateDirect`/`CreateObserverPublication`;第 60-72 行:accessors。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActorPublisher.cs` 第 15 行:`IEventPublisher, ICommittedStateEventPublisher`;第 40-90 行:`PublishAsync`(topology);第 92-115 行:`SendToAsync`(direct);第 117-139 行:observer publish;第 141-149 行:`GetRouteTargetCount`。
- `src/Aevatar.Foundation.Core/EventSourcing/ICommittedStateEventPublisher.cs` 第 8-15 行:`internal interface`(`PublishAsync(CommittedStateEventPublished, ObserverAudience)`)。
- `docs/canon/architecture.md` 第 144-159 行:拓扑事实落点 + 三种路由行为。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActor.cs` 第 18/25/45-46/156-170 行:Local 拓扑字段。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Grains/RuntimeActorGrainState.cs` 第 16/19 行:Orleans 拓扑(`[Id(2)] ParentId`/`[Id(3)] Children`)。

---

## 三种路由

`docs/canon/architecture.md` 第 154-159 行明确三种路由行为:

| 路由 | proto | 行为 | 代码落点 |
|---|---|---|---|
| `DirectRoute` | 第 62-64 行 | runtime 直投目标 actor inbox | `architecture.md:155` |
| `PublicationRoute.topology` | 第 66-71 行 + `TopologyAudience` | stream forwarding / relay binding(Self/Parent/Children/ParentAndChildren) | `architecture.md:156` |
| `PublicationRoute.observer` | 第 66-71 行 + `ObserverAudience`(CommittedFacts) | 只给 projection/live sink/observer,**不进业务 actor inbox** | `architecture.md:157` |

---

## LocalActorPublisher:三种 publish

`LocalActorPublisher`(`LocalActorPublisher.cs` 第 15 行)实现 `IEventPublisher` + `ICommittedStateEventPublisher`:

**`PublishAsync`(topology,第 40-90 行)**:
- 构造 `CreateTopologyPublication(_actorId, audience)`(第 54 行)
- 按 audience 分发:`Self`→self stream(第 66-68 行);`Children`→self stream(第 69-71 行,经 relay);`Parent`→parent stream 或 self 回退(第 72-80 行);`ParentAndChildren`→self+parent streams(第 81-88 行)
- 实际 fan-out 到 children 通过 stream relay binding,不是直接 produce

**`SendToAsync`(direct,第 92-115 行)**:
- 构造 `CreateDirect(_actorId, targetActorId)`(第 105 行)
- `ProduceAsync` 到目标 stream(第 114 行)

**observer publish(第 117-139 行)**:
- 构造 `CreateObserverPublication(_actorId, audience)`(第 129 行)
- `routeTargetCount: 0`(第 136 行,observer audience 无业务目标)
- produce 到 self stream(第 138 行)

---

## ICommittedStateEventPublisher

`internal interface`(`ICommittedStateEventPublisher.cs` 第 8 行)—— `internal` 修饰符是为什么 `architecture.md:63` 说它"不进入业务 actor 公共能力面"。单方法 `PublishAsync(CommittedStateEventPublished, ObserverAudience=CommittedFacts)`。

被 `GAgentBase<TState>.PublishCommittedDomainEventsAsync`(`GAgentBase.TState.cs` 第 303-307 行)调用;`LocalActorPublisher` 显式实现(第 117 行);`NullCommittedStateEventPublisher` 存在于 `GAgentBase.cs` 第 542-551 行。

---

## 拓扑事实落点

`docs/canon/architecture.md` 第 144-159 行:

| Runtime | 拓扑持有者 | 字段 |
|---|---|---|
| Local | `LocalActor` | `_parentId`(`LocalActor.cs:25`/`:45`)、`_childrenIds`(`:18`/`:46`),`AddChild`/`RemoveChild`(`:156-157`)、`SubscribeToParentAsync`(`:159-170`) |
| Orleans | `RuntimeActorGrainState` | `[Id(2)] ParentId`(`:16`)、`[Id(3)] Children`(`:19`) |

`LocalActorRuntime.LinkAsync`(`LocalActorRuntime.cs` 第 231-251 行)同时更新拓扑 + stream relay:`parent.AddChild` + `child.SubscribeToParentAsync`(第 235-236 行),再 `UpsertRelayAsync` 建层级 binding(第 237-239 行)和 committed-observation binding child→parent(第 244-246 行)。

---

## 验收

1. 三种路由分别是什么?(DirectRoute 直投;topology 经 stream relay;observer 只给 projection 不进业务 inbox)
2. `PublicationRoute.observer` 的 audience 只有一个值?(CommittedFacts)
3. 拓扑事实在 Local 和 Orleans 各存哪?(LocalActor 字段 / RuntimeActorGrainState)

⟦AI:AUTO-LOOP⟧
