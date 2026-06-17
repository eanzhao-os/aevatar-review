# Kafka Transport(Orleans KafkaProvider)插件 + ADR-0003 设计

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Transport.KafkaProvider/Streaming/KafkaQueuePartitionMapper.cs` 第 10 行:`IStreamQueueMapper, IConsistentRingStreamQueueMapper`;第 39-48 行:`GetPartitionId = SHA256(StreamNamespace + "\n" + StreamId) % queueCount`;第 26-32 行:`GetQueueForStream`。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Transport.KafkaProvider/Streaming/KafkaProviderQueueAdapterReceiver.cs` 第 11 行:`IQueueAdapterReceiver`;第 44-48 行:每 queue 绑一个 Kafka partition;第 23-24 行:inflight/acked offset;commit 仅在 Orleans `MessagesDeliveredAsync` 后。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Transport.KafkaProvider/Transport/KafkaProviderTransportOptions.cs` 第 5-31 行:`BootstrapServers`/`TopicName`/`ConsumerGroup`/`TopicPartitionCount=8`/`ProducerMaxMessageBytes=10MB`/`ProducerCompressionType=Gzip`。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Transport.KafkaProvider/DependencyInjection/ServiceCollectionExtensions.cs` 第 12、20、44 行:`AddAevatarFoundationRuntimeOrleansKafkaProviderTransport`。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Streaming/AevatarOrleansRuntimeOptions.cs` 第 5-6 行:`StreamBackendInMemory="InMemory"`/`StreamBackendKafkaProvider="KafkaProvider"`。
- `docs/adr/0003-kafka-transport.md` 第 9-18 行:Status(Provider=Orleans + OrleansStreamBackend=KafkaProvider);第 82-88 行:映射规则;第 100-113 行:三层 ID 对齐;第 142-155 行:commit 边界(at-least-once);第 158-165 行:拓扑不变量(QueueCount==TopicPartitionCount);第 209-215 行:Non-Goals(无 exactly-once/无自由分区扩展/无 InMemory 多 silo)。
- `src/Aevatar.Foundation.Runtime.Implementations.Orleans/README.md` 第 59-86 行:KafkaProvider 启用片段 + "不依赖 MassTransit"。

---

## ⚠️ MassTransit 已退役

README 第 101 行提到 MassTransit/Kafka,但 **MassTransit 是历史路径,已完全退役**:
- `src/Aevatar.Foundation.Runtime.Transport.Implementations.MassTransitKafka/` 和 `…/Streaming.Implementations.MassTransit/` 无 `.cs`/`.csproj`(只剩 build artifact)
- 不在 `aevatar.slnx` 或任何 `.slnf`
- `architecture_guards.sh` 第 1335-1350 行:CI 禁止 MassTransit v9,pin v8.x
- `docs/adr/0002-mainnet-architecture.md` 第 636 行:§8.1 明确标 MassTransit 为"历史路径"

**当前生产 transport = Orleans 原生 KafkaProvider backend**。

---

## KafkaProvider:Kafka partition 与 Orleans queue 收敛

`KafkaQueuePartitionMapper`(`KafkaQueuePartitionMapper.cs`)的核心设计:让 Kafka partition 绑定和 Orleans queue 所有权**收敛到一个 runtime slot**。

映射规则(第 39-48 行,ADR-0003 第 82-88 行):
```
PartitionId = SHA256(StreamNamespace + "\n" + StreamId) % QueueCount
```

三层 ID 对齐(ADR-0003 第 100-113 行):业务 stream ↔ Kafka partition ↔ Orleans queue 一一对应。

**commit 边界**(ADR-0003 第 142-155 行):Kafka offset 仅在 Orleans `MessagesDeliveredAsync` 确认后提交 —— **at-least-once**。

**拓扑不变量**(ADR-0003 第 158-165 行):`QueueCount == TopicPartitionCount`;多 silo 要求共享持久 runtime state(非 InMemory pubsub)。

---

## 配置

`KafkaProviderTransportOptions`(`KafkaProviderTransportOptions.cs`):

| 选项 | 默认 | 行号 |
|---|---|---|
| `BootstrapServers` | `localhost:9092` | 第 7 行 |
| `TopicName` | — | 第 9 行 |
| `ConsumerGroup` | — | 第 11 行 |
| `TopicPartitionCount` | 8 | 第 13 行 |
| `ProducerMaxMessageBytes` | 10MB | 第 24 行 |
| `ProducerCompressionType` | Gzip | 第 31 行 |

启用:`AddAevatarFoundationRuntimeOrleansKafkaProviderTransport`(`ServiceCollectionExtensions.cs`)。config key `OrleansStreamBackend=KafkaProvider`(`AevatarOrleansRuntimeOptions.cs`)。

---

## ADR-0003 Non-Goals(第 209-215 行)

- 不做 exactly-once(at-least-once)
- 不支持自由分区扩展
- 不兼容 InMemory 多 silo

---

## 验收

1. 当前 Kafka transport 是 MassTransit 吗?(不是,是 Orleans KafkaProvider;MassTransit 已退役)
2. Kafka partition 和 Orleans queue 关系?(收敛到一个 slot,SHA256 % QueueCount)
3. commit 语义?(at-least-once,Orleans 确认后才提交 offset)
4. QueueCount 和 TopicPartitionCount 关系?(必须相等,拓扑不变量)

⟦AI:AUTO-LOOP⟧
