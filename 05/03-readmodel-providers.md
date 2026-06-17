# ReadModel 存储实现:InMemory(默认) / Elasticsearch / Neo4j

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.CQRS.Projection.Stores.Abstractions/README.md` 第 1-19 行:契约清单(无 router/fanout,Document vs Graph 并行)。
- `src/Aevatar.CQRS.Projection.Stores.Abstractions/Abstractions/Graphs/IProjectionGraphStore.cs` 第 3-38 行;`Abstractions/ReadModels/IProjectionDocumentWriter.cs` 第 3-9 行;`IProjectionDocumentReader.cs`。
- `src/Aevatar.CQRS.Projection.Runtime/Runtime/ProjectionStoreDispatcher.cs`:`IProjectionStoreDispatcher`(路由权威,`cqrs-projection.md:111`)。
- `src/Aevatar.CQRS.Projection.Providers.InMemory/README.md` 第 1-20 行:dev/test;`DependencyInjection/ServiceCollectionExtensions.cs` 第 9-40 行:`AddInMemoryDocumentProjectionStore`/`AddInMemoryGraphProjectionStore`。
- `src/Aevatar.CQRS.Projection.Providers.Elasticsearch/README.md` 第 1-43 行:document-only,schema-drift 权威(augmented mapping fingerprint + alias 生命周期);`DependencyInjection/ServiceCollectionExtensions.cs` 第 11-42 行:`AddElasticsearchDocumentProjectionStore`(+ `IProjectionIndexConsistencyProbe`)。
- `src/Aevatar.CQRS.Projection.Providers.Neo4j/DependencyInjection/ServiceCollectionExtensions.cs` 第 10-22 行:`AddNeo4jGraphProjectionStore`;`Configuration/Neo4jProjectionGraphStoreOptions.cs` 第 3-22 行(Uri/Username/Password/Database/MaxTraversalDepth/NodeLabel/EdgeType)。
- `src/Aevatar.Mainnet.Host.Api/Hosting/MainnetAgentProjectionDocumentStoresExtensions.cs` 第 25-48 行:生产装配(`ElasticsearchEnabled` → ES else InMemory;第 50-64/66-86 行);`EnsureCompatibleDocumentReaderProvider`(第 121 行)。
- `docs/canon/cqrs-projection.md` 第 112 行:禁止无条件并列注册。
- `docker-compose.projection-providers.yml` 第 1-24 行:本地 ES + Neo4j。

---

## Store 契约(并行 Document + Graph)

`Aevatar.CQRS.Projection.Stores.Abstractions/README.md` 第 1-19 行:无 router/fanout 逻辑,Document 与 Graph 两套并行契约:

| 契约 | 文件 | 操作 |
|---|---|---|
| `IProjectionDocumentWriter<TReadModel>` | `IProjectionDocumentWriter.cs` | upsert/delete |
| `IProjectionDocumentReader<TReadModel,TKey>` | `IProjectionDocumentReader.cs` | 读 |
| `IProjectionGraphStore` | `IProjectionGraphStore.cs` | ReplaceOwnerGraph/UpsertNode/UpsertEdge/Delete/List/Neighbors/Subgraph |

`IProjectionStoreDispatcher`(`ProjectionStoreDispatcher.cs`)是路由权威(`cqrs-projection.md:111`)。

---

## 三个 Provider

| Provider | 文件 | 类型 | 用途 |
|---|---|---|---|
| **InMemory** | `Providers.InMemory/` | Document + Graph | dev/test(`README.md:1-20`) |
| **Elasticsearch** | `Providers.Elasticsearch/` | Document only | 生产文档存储;schema-drift 权威 = augmented mapping fingerprint + alias 生命周期(`README.md:30-37`) |
| **Neo4j** | `Providers.Neo4j/` | Graph only | 生产图存储(Uri/Username/Password/Database/MaxTraversalDepth,`Neo4jProjectionGraphStoreOptions.cs`) |

> ⚠️ **StateMirror 已移除**:目录 `Aevatar.CQRS.Projection.StateMirror/` 只剩 `bin/`/`obj/`(commit `da7944cf2` 移除)。不作为活跃 provider。

---

## 生产怎么换

`MainnetAgentProjectionDocumentStoresExtensions.cs` 第 25-48 行:读 `ProjectionDocumentProviderConfiguration.Resolve(...)`,分支:
- `ElasticsearchEnabled` → `AddElasticsearchStores`(第 50-64 行)
- else → `AddInMemoryStores`(第 66-86 行)

per-model helper:`TryAddElasticsearchStore`(第 88-103 行)/`TryAddInMemoryStore`(第 105-119 行),带 `EnsureCompatibleDocumentReaderProvider` 守卫(第 121 行)。

**禁止无条件并列注册**(`cqrs-projection.md:112`)。本地 ES + Neo4j 用 `docker-compose.projection-providers.yml`。

---

## 验收

1. 三个 ReadModel provider?(InMemory dev/test、Elasticsearch 文档、Neo4j 图)
2. StateMirror 还在吗?(已移除,只剩 build artifact)
3. 生产怎么换 ES?(MainnetAgentProjectionDocumentStoresExtensions.cs,ElasticsearchEnabled 分支)
4. Document 和 Graph 契约是合并的吗?(不是,并行两套)

⟦AI:AUTO-LOOP⟧
