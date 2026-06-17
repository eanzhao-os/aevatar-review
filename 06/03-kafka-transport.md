# Kafka Transport(Orleans KafkaProvider)插件 + ADR-0003 设计

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## ⚠️ MassTransit 已退役

README 提到 MassTransit/Kafka,但 **MassTransit 是历史路径,已完全退役**:
- `src/Aevatar.Foundation.Runtime.Transport.Implementations.MassTransitKafka/` 和 `` 无 ``/`项目文件`(只剩 build artifact)
- 不在 `aevatar.slnx` 或任何 `.slnf`
- `architecture_guards` :CI 禁止 MassTransit v9,pin v8.x
- `0002-mainnet-architecture` :§8.1 明确标 MassTransit 为"历史路径"

**当前生产 transport = Orleans 原生 KafkaProvider backend**。

---

## KafkaProvider:Kafka partition 与 Orleans queue 收敛

`KafkaQueuePartitionMapper`(`KafkaQueuePartitionMapper`)的核心设计:让 Kafka partition 绑定和 Orleans queue 所有权**收敛到一个 runtime slot**。

映射规则(ADR-0003 ):
```
PartitionId = SHA256(StreamNamespace + "\n" + StreamId) % QueueCount
```

三层 ID 对齐(ADR-0003 ):业务 stream ↔ Kafka partition ↔ Orleans queue 一一对应。

**commit 边界**(ADR-0003 ):Kafka offset 仅在 Orleans `MessagesDeliveredAsync` 确认后提交 —— **at-least-once**。

**拓扑不变量**(ADR-0003 ):`QueueCount == TopicPartitionCount`;多 silo 要求共享持久 runtime state(非 InMemory pubsub)。

---

## 配置

`KafkaProviderTransportOptions`(`KafkaProviderTransportOptions`):

| 选项 | 默认 | 行号 |
|---|---|---|
| `BootstrapServers` | `localhost` | |
| `TopicName` | — | |
| `ConsumerGroup` | — | |
| `TopicPartitionCount` | 8 | |
| `ProducerMaxMessageBytes` | 10MB | |
| `ProducerCompressionType` | Gzip | |

启用:`AddAevatarFoundationRuntimeOrleansKafkaProviderTransport`(`ServiceCollectionExtensions`)。config key `OrleansStreamBackend=KafkaProvider`(`AevatarOrleansRuntimeOptions`)。

---

## ADR-0003 Non-Goals()

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
