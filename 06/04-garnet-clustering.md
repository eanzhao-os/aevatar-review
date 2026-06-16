# Garnet 生产聚类 + 持久化实现

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet/GarnetEventStore.cs` 第 14 行:`IEventStore, IEventStoreMaintenance`;第 16-47 行:`AppendScript` Lua(OCC CAS on VersionKey + ZADD index + HSET data);第 90-148 行:`AppendAsync`(版本校验 + Lua + OCC 异常);第 150-198 行:`GetEventsAsync`;第 217-241 行:`DeleteEventsUpToAsync` 压缩;第 260-267 行:key layout `{prefix}:{agentId}:version|index|data`(hash-tagged `{agentId}` for Redis-cluster slot affinity)。
- `src/Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet/GarnetEventStoreOptions.cs`:`ConnectionString`/`KeyPrefix`/`Database`。
- `src/Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet/DependencyInjection/ServiceCollectionExtensions.cs` 第 13、24-32 行:`AddGarnetEventStore`(IConnectionMultiplexer + IEventStore + IEventStoreMaintenance)。
- `src/Aevatar.Mainnet.Host.Api/Hosting/MainnetDistributedHostBuilderExtensions.cs` 第 39、75-129 行:`ConfigureClustering`(Localhost/Development/Garnet);第 109-129 行:`ClusteringMode=Garnet`(需 `OrleansGarnetConnectionString`,`UseRedisClustering` over Garnet);第 121-125 行注释(membership + reminder + grain state 共享同一 store + ServiceId);第 135 行:`ConfigureGarnetClusterEndpoints`。
- `docs/adr/0032-mainnet-garnet-clustering.md` 第 9-24 行:Context(Localhost + 共享 Garnet grain-state/reminder → rolling deploy 双 owner → InconsistentStateException etag ping-pong + 双发 durable callback ~90s);第 30-47 行:Decision(`ClusteringMode=Garnet` via `Microsoft.Orleans.Clustering.Redis` over Garnet;membership+reminder+grain-state 共享一 store + 一 ClusterId/ServiceId → 单激活);第 49-68 行:Alternatives rejected;第 70-82 行:Consequences(pod 互通 silo port 11111;graceful shutdown 交环;Garnet 须支持 Orleans Redis providers 含 Lua)。
- `docker-compose.mainnet-cluster.yml`:Garnet `--lua true`。

---

## Garnet 的两个生产职责

Garnet(Redis 协议兼容)用于两件事:

### 1. IEventStore 持久化

`GarnetEventStore`(`GarnetEventStore.cs:14`)实现 `IEventStore`。核心是 Lua 脚本做 OCC CAS(`AppendScript`,第 16-47 行):
- CAS on `VersionKey`(乐观并发)
- `ZADD` 到 sorted-set index(版本排序)
- `HSET` 到 data hash(事件 payload)

key layout(第 260-267 行):`{prefix}:{agentId}:version|index|data`,hash-tag `{agentId}` 保证 Redis-cluster slot 亲和。`AppendAsync`(第 90-148 行)版本不连续或 OCC 冲突抛 `EventStoreOptimisticConcurrencyException`。`DeleteEventsUpToAsync`(第 217-241 行)做 snapshot 压缩。

DI:`AddGarnetEventStore`(`ServiceCollectionExtensions.cs:13`)注册 `IConnectionMultiplexer` + 替换 `IEventStore`。

### 2. Orleans 聚类/membership/grain-state/reminder

`MainnetDistributedHostBuilderExtensions.cs` 第 109-129 行:`ClusteringMode=Garnet`:
- 需 `OrleansGarnetConnectionString`(第 111-113 行)
- `UseRedisClustering(...)` over Garnet 连接串(第 126-127 行)
- 注释(第 121-125 行):membership + reminder table + grain state **共享同一 Garnet store + 同一 ServiceId** → rolling deploy 时新旧 pod 加入同一 cluster,reminder 环分区不重叠

---

## ADR-0032:为什么需要共享 Garnet membership

`docs/adr/0032-mainnet-garnet-clustering.md`:

**Context**(第 9-24 行):生产曾用 `ClusteringMode=Localhost` + 共享 Garnet grain-state/reminder table。每次 rolling deploy 新旧 pod 都 claim 完整 reminder 环 → `InconsistentStateException` etag ping-pong + durable callback 双发 ~90s。

**Decision**(第 30-47 行):加 `Orleans:ClusteringMode=Garnet`,经 `Microsoft.Orleans.Clustering.Redis` over 同一 Garnet 连接串。membership + reminder + grain-state 共享一 store + 一稳定 `ClusterId`/`ServiceId` → 每 grain 单激活。`Distributed` profile 默认 `Garnet`;`Localhost` 留 dev 默认。

**Consequences**(第 70-82 行):pod 须在 overlap 期互通 silo port 11111;graceful shutdown 把 reminder 环交给存活 silo;Garnet 须支持 Orleans Redis providers 的命令面(含 Lua,`RedisGrainStorage` etag 写已验证)。

---

## 验收

1. Garnet 做哪两件事?(IEventStore 持久化 + Orleans 聚类/membership/grain-state/reminder)
2. GarnetEventStore 怎么做 OCC?(Lua CAS on VersionKey + ZADD + HSET)
3. 为什么需要共享 Garnet membership?(否则 rolling deploy 双 owner 导致 etag ping-pong + callback 双发)
4. membership/reminder/grain-state 共享什么?(同一 Garnet store + 同一 ServiceId)

⟦AI:AUTO-LOOP⟧
