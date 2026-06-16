# 诚实对比:当前实现 vs 目标态(ActorRuntime/Transport/Projection/LiveSink/ReadModel)

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `README.md` 第 96-105 行:`### 当前实现与目标态(分布式 Runtime)` 完整对照表。
- `docs/canon/architecture.md` 第 126-129 行:InMemory 仅 dev/test,生产用 Garnet;第 131-138 行:§分布式目标态(生产)—— 单激活 + 邮箱串 + 同一组原语;第 144-159 行:路由细节。

---

## 对照表(`README.md` 第 96-105 行)

aevatar 对分布式 Runtime 的当前实现与目标态做了诚实对比。评分依据是**已落地代码**(第 105 行),不是承诺:

| 维度 | 当前实现 | 目标态 |
|---|---|---|
| **Actor Runtime**(`README.md:100`) | `ActorRuntime:Provider=InMemory`(dev/test) | 非 InMemory Provider(Redis/DB)+ 分布式 Actor Runtime |
| **Orleans Transport**(`:101`) | `Provider=Orleans` 默认内置 link;可选 `Transport=Kafka` 启用 KafkaProvider transport 插件 | 可插拔 transport,由 stream/queue 层承载跨节点转发 |
| **Projection 并发(Ensure/Release)**(`:102`) | 已由 `projection:{rootActorId}` projection-coordination Actor 串行化(不再进程内 `SemaphoreSlim`) | 继续依赖"同 actorId 单激活 + 邮箱串行" |
| **LiveSink(Attach/Detach)**(`:103`) | 已经 `workflow-run:{actorId}:{commandId}` event stream sub/unsub(不再 `ProjectionContext` 内存 sink 列表) | 分布式 stream provider 下原生跨节点 |
| **ReadModel storage**(`:104`) | 默认 `Aevatar.CQRS.Projection.Providers.InMemory`,可换 Provider | 换持久 read-model Provider 实现跨节点一致读 |
| **审计评分依据**(`:105`) | 当前 = 已落地代码 | 目标态落地后重新审计 |

---

## 关键澄清

`docs/canon/architecture.md` 第 131-138 行(§分布式目标态)补充:
- 第 133 行:生产语义是分布式 `IActorRuntime` 的**全局单激活 + 邮箱串行**
- 第 138 行:`AddAevatarFoundationRuntimeOrleans()` 和 `AddAevatarRuntime()` 暴露**同一组** `IActorRuntime`/`IActorDispatchPort`/`IEventPublisher` 原语 —— Local 和 Orleans 是同一抽象的两种实现
- 第 126-129 行:InMemory 仅 dev/test;生产用 `Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet`

---

## 验收

1. Actor Runtime 当前用什么?目标?(InMemory dev/test → 非 InMemory 分布式)
2. Projection 并发怎么做的?(projection:{rootActorId} Actor 串行,不再 SemaphoreSlim)
3. LiveSink 怎么 attach?(workflow-run:{actorId}:{commandId} stream sub/unsub)
4. Local 和 Orleans 是两套抽象吗?(不是,同一组原语的两种实现)

⟦AI:AUTO-LOOP⟧
