# 核心概念辨析:Agent / Actor / Runtime / Stream

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Abstractions/IAgent.cs` 第 13-32 行:`IAgent`(Id/HandleEventAsync/GetSubscribedEventTypesAsync/Activate/Deactivate);第 38-42 行:`IAgent<TState>`(typed State)。
- `src/Aevatar.Foundation.Abstractions/IActor.cs` 第 11-33 行:`IActor`(运行容器,持 `IAgent Agent`,第 17 行;父子拓扑 GetParentIdAsync/GetChildrenIdsAsync)。
- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs` 第 11-43 行:`IActorRuntime`(Create/Destroy/Get/Exists/Link/Unlink)。
- `src/Aevatar.Foundation.Abstractions/IStream.cs` 第 14-36 行:`IStream`(StreamId/ProduceAsync/SubscribeAsync/UpsertRelayAsync);`IStreamProvider.cs` 第 11-15 行。
- `src/Aevatar.Foundation.Abstractions/IActorDispatchPort.cs` 第 68-76 行:外部 envelope admission(只承诺 accepted-for-dispatch)。
- `src/Aevatar.Foundation.Abstractions/IEventContext.cs` 第 6-33 行:inbound-envelope 视图;`IEventPublisher.cs` 第 15-29 行:outbound publish/send。
- `docs/canon/architecture.md` 第 21-29 行:五概念表;第 27 行:Runtime 构建"在 Stream 之上的 Actor 语义层"。
- `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActorRuntime.cs` 第 102-107 行:Runtime 用 IStreamProvider 构造 publisher。

---

## 五个核心概念

`docs/canon/architecture.md` 第 21-29 行把 Foundation 的核心拆成五个概念:

| 概念 | 抽象 | 它是什么 |
|---|---|---|
| **Agent** | `IAgent` / `IAgent<TState>` | 业务逻辑单元(`IAgent.cs:13-32`)。持 `Id`,处理 `EventEnvelope` |
| **Actor** | `IActor` | Agent 的**运行容器**(`IActor.cs:11-33`)。持 `IAgent Agent`(第 17 行)+ 父子拓扑 + 生命周期 |
| **Runtime** | `IActorRuntime` / `IActorDispatchPort` | Actor 语义层(`IActorRuntime.cs:11-43`)。创建/销毁/寻址/激活/链接 |
| **Event Context** | `IEventPublisher` / `IEventContext` | 当前 actor 执行中的 publish/send(`IEventPublisher.cs:15-29`)+ inbound envelope 视图(`IEventContext.cs:6-33`) |
| **Stream** | `IStream` / `IStreamProvider` | `EventEnvelope` 的传输骨架(`IStream.cs:14-36`) |

---

## 关系:Runtime 在 Stream 之上

`docs/canon/architecture.md` 第 27 行明确:Runtime 是"构建在 Stream 之上的 Actor 语义层"。

```mermaid
graph TB
    subgraph "Runtime 层 (Actor 语义)"
        RT["IActorRuntime<br/>(Create/Get/Link)"]
        DP["IActorDispatchPort<br/>(外部 admission)"]
        AC["IActor<br/>(容器 + 父子拓扑)"]
        AG["IAgent<br/>(业务逻辑)"]
        RT --> AC --> AG
        DP --> AC
    end
    subgraph "Stream 层 (传输骨架)"
        SP["IStreamProvider"]
        ST["IStream<br/>(Produce/Subscribe/Relay)"]
        SP --> ST
    end
    AC -.-"envelope 经 Stream 投递"-.- ST
```

具体落点(`LocalActorRuntime.cs` 第 102-107 行):Runtime 用 `IStreamProvider` 构造 `LocalActorPublisher`;publisher 解析目标 actor 的 `IStream` 并 `ProduceAsync` envelope(`LocalActorPublisher.cs:114`)。`LocalActor`(第 52-53 行)订阅自己的 self-stream 接收 envelope。

- **Runtime** 负责 Actor 身份/生命周期/拓扑/寻址
- **Stream** 是承载 `EventEnvelope` 在 actor stream 之间流动的"线"
- **Relay 绑定**(`IStream.UpsertRelayAsync`,第 29 行)做实际的 fan-out

---

## IActorDispatchPort:只承诺"已受理"

`IActorDispatchPort.DispatchAsync(actorId, envelope)` 返回 `DispatchAdmission`(`IActorDispatchPort.cs:75`)。注释(第 67、72-74 行)明确:完成只意味着 **accepted-for-dispatch**,不意味着已 handled/committed/observed。这与 `01/03-run-semantics.md` 的"终止事件收敛"呼应 —— 强保证要靠独立契约/异步观察。

---

## 验收

1. Agent 和 Actor 的关系?(Agent 是业务逻辑;Actor 是运行容器,持 Agent + 拓扑)
2. Runtime 在 Stream 之上是什么意思?(Stream 是传输骨架,Runtime 是其上的 Actor 语义层)
3. `DispatchAsync` 完成意味着什么?(只承诺 accepted-for-dispatch,不承诺已处理)

⟦AI:AUTO-LOOP⟧
