# Projection 总览:Command→EventEnvelope→Actor→持久化→Projection→ReadModel

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `docs/canon/cqrs-projection.md` 第 36-46 行:mermaid 主链路;第 48-53 行:投影口径澄清;第 55-78 行:CQRS Core 统一命令骨架 7 步;第 104-114 行:投影约束 1-9。
- `docs/canon/architecture.md` 第 161-184 行:§CQRS 与 Projection 落点;第 198-201 行:输出分支。
- `src/Aevatar.CQRS.Core.Abstractions/Interactions/ICommandInteractionService.cs` 第 6-14 行:交互接口。
- `src/Aevatar.CQRS.Core/Interactions/DefaultCommandInteractionService.cs` 第 10-13 行:默认实现(Prepare→Observe→Dispatch→Pump→finalize);第 56-58 行:observation-before-dispatch 重构注释;第 125 行:dispatch。
- `src/Aevatar.CQRS.Core/Commands/DefaultCommandDispatchPipeline.cs`:标准命令骨架。
- `src/Aevatar.CQRS.Core/Commands/ActorCommandTargetDispatcher.cs`:经 `IActorDispatchPort` 落地。
- `src/Aevatar.CQRS.Projection.Core/DependencyInjection/EventSinkProjectionRuntimeRegistration.cs` 第 54-85 行:session pipeline 注册;`ProjectionMaterializationRuntimeRegistration.cs` 第 44-79 行:durable pipeline 注册。

---

## 统一投影链路

`docs/canon/cqrs-projection.md` 第 36-46 行的 mermaid 主链路:

```text
Host API → Application Service → Actor/GAgent → Actor Envelope Stream + EventStore → Projection Pipeline → ReadModel → Query API/SSE/WS
```

**关键口径**(第 48-53 行):EventEnvelope Stream 是**运行时消息流**,不是 ES 事实流;command → envelope → actor mailbox;只有显式持久化的领域事件进 EventStore;projection 消费 actor envelope stream。

> 这条链路解释了为什么 API 推送(SSE/WS/AGUI)和 CQRS 读模型共享同一投影输入 —— 它们都是这条链路的输出分支(`architecture.md` 第 198-201 行)。

---

## CQRS 统一命令骨架 7 步(`cqrs-projection.md` 第 55-78 行)

1. Normalize Command
2. Resolve Target
3. Create CommandContext
4. Build Envelope
5. Dispatch via `IActorDispatchPort`
6. Accepted Receipt
7. Observe Result

`DefaultCommandInteractionService`(`DefaultCommandInteractionService.cs` 第 10-13 行)实现:Prepare → Observe → DispatchPrepared → Accepted callback → Pump → finalize → cleanup。**observation-before-dispatch**(第 56-58 行重构注释):观察绑定必须在 dispatch 前完成,否则会丢事件。

---

## 投影约束(`cqrs-projection.md` 第 104-114 行)

1. CQRS/AGUI/SSE/WS 共享同一投影输入
2. EventTypeUrl 精确匹配
3. miss 时 no-op
4. lease/session 生命周期
5. one-to-many 全分支
6. `IProjectionStoreDispatcher` + Store Binding
7. committed-state 发布 hook 激活 durable scope
8. durable 激活由 committed-state publication owner hook 触发(非 command 路径)
9. host 侧只留薄适配

---

## 验收

1. 投影主链路?(Command→EventEnvelope→Actor→持久化→Projection→ReadModel)
2. 为什么 SSE 和 ReadModel 共享输入?(都是同一投影链路的输出分支)
3. 命令骨架第 5 步?(Dispatch via IActorDispatchPort)
4. observation 和 dispatch 的顺序?(observation-before-dispatch,否则丢事件)

⟦AI:AUTO-LOOP⟧
