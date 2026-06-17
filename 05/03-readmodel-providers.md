# ReadModel 存储实现:InMemory(默认) / Elasticsearch / Neo4j

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## Store 契约(并行 Document + Graph)

`Aevatar.CQRS.Projection.Stores.Abstractions/README.md` :无 router/fanout 逻辑,Document 与 Graph 两套并行契约:

| 契约 | 文件 | 操作 |
|---|---|---|
| `IProjectionDocumentWriter<TReadModel>` | `IProjectionDocumentWriter` | upsert/delete |
| `IProjectionDocumentReader<TReadModel,TKey>` | `IProjectionDocumentReader` | 读 |
| `IProjectionGraphStore` | `IProjectionGraphStore` | ReplaceOwnerGraph/UpsertNode/UpsertEdge/Delete/List/Neighbors/Subgraph |

`IProjectionStoreDispatcher`(`ProjectionStoreDispatcher`)是路由权威(`cqrs-projection.md`)。

---

## 三个 Provider

| Provider | 文件 | 类型 | 用途 |
|---|---|---|---|
| **InMemory** | `Providers.InMemory/` | Document + Graph | dev/test(`README.md`) |
| **Elasticsearch** | `Providers.Elasticsearch/` | Document only | 生产文档存储;schema-drift 权威 = augmented mapping fingerprint + alias 生命周期(`README.md`) |
| **Neo4j** | `Providers.Neo4j/` | Graph only | 生产图存储(Uri/Username/Password/Database/MaxTraversalDepth,`Neo4jProjectionGraphStoreOptions`) |

> ⚠️ **StateMirror 已移除**:目录 `Aevatar.CQRS.Projection.StateMirror/` 只剩 `bin/`/`obj/`(commit `da7944cf2` 移除)。不作为活跃 provider。

---

## 生产怎么换

`MainnetAgentProjectionDocumentStoresExtensions` :读 `ProjectionDocumentProviderConfiguration.Resolve(...)`,分支:
- `ElasticsearchEnabled` → `AddElasticsearchStores`()
- else → `AddInMemoryStores`()

per-model helper:`TryAddElasticsearchStore`()/`TryAddInMemoryStore`(),带 `EnsureCompatibleDocumentReaderProvider` 守卫()。

**禁止无条件并列注册**(`cqrs-projection.md`)。本地 ES + Neo4j 用 `docker-compose.projection-providers.yml`。

---

## 验收

1. 三个 ReadModel provider?(InMemory dev/test、Elasticsearch 文档、Neo4j 图)
2. StateMirror 还在吗?(已移除,只剩 build artifact)
3. 生产怎么换 ES?(MainnetAgentProjectionDocumentStoresExtensions.cs,ElasticsearchEnabled 分支)
4. Document 和 Graph 契约是合并的吗?(不是,并行两套)

⟦AI:AUTO-LOOP⟧
