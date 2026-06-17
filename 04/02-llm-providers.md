# LLM Provider 抽象与实现:MEAI / NyxId / Tornado

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.AI.Abstractions/LLMProviders/ILLMProvider.cs` 第 9-24 行:`ILLMProvider`(`Name`/`Capabilities`/`ChatStreamAsync`,第 18-20 行重构注释:只暴露 ChatStreamAsync)。
- `src/Aevatar.AI.Abstractions/LLMProviders/ILLMProviderFactory.cs` 第 9-22 行:`ILLMProviderFactory`(`GetProvider`/`GetDefault`/`GetAvailableProviders`)。
- `src/Aevatar.AI.LLMProviders.MEAI/MEAILLMProvider.cs` 第 26 行:桥接 MEAI `IChatClient`;`MEAILLMProviderFactory.cs` 第 21 行:`IMEAILLMProviderRegistry`。
- `src/Aevatar.AI.LLMProviders.NyxId/NyxIdLLMProvider.cs` 第 16 行:每路由构造 delegate MEAI provider(第 284、302 行);`NyxIdLLMProviderFactory.cs` 第 7 行。
- `src/Aevatar.AI.LLMProviders.Tornado/TornadoLLMProvider.cs` 第 26 行:桥接 LlmTornado;`TornadoLLMProviderFactory.cs` 第 20 行。
- `src/Aevatar.Bootstrap.Extensions.AI/CompositeLLMProviderFactory.cs` 第 6-46 行:primary + additional 合并。
- `src/Aevatar.Bootstrap.Extensions.AI/ReloadableLLMProviderFactory.cs` 第 12-98 行:version-stamp 热重载(`Interlocked.CompareExchange` 原子 swap)。

---

## Provider 契约

`ILLMProvider`(`ILLMProvider.cs` 第 9-24 行)只暴露一个流式方法:

- `string Name`(第 12 行)
- `LLMProviderCapabilities Capabilities`(默认 `TextOnly`,第 15 行)
- `IAsyncEnumerable<LLMStreamChunk> ChatStreamAsync(LLMRequest, CancellationToken)`(第 24 行)—— **唯一的调用方式**(非流式 `ChatAsync` 已移除,第 18-20 行重构注释)

`ILLMProviderFactory`(第 9-22 行):`GetProvider(name)`/`GetDefault()`/`GetAvailableProviders()`。

---

## 三个 Provider 实现

| Provider | 文件 | 桥接 | 说明 |
|---|---|---|---|
| **MEAI** | `MEAILLMProvider.cs` | `Microsoft.Extensions.AI` 的 `IChatClient` | 通用桥接;`MEAILLMProviderFactory` 持 `ImmutableDictionary` + `Register`/`SetDefault` |
| **NyxId** | `NyxIdLLMProvider.cs` | 每路由构造 delegate MEAI provider(`CreateDelegateProvider` 第 284 行 → `new MEAILLMProvider` 第 302 行) | NyxId 网关路由 |
| **Tornado** | `TornadoLLMProvider.cs` | `LlmTornado` 的 `TornadoApi` | 第三方 SDK 桥接 |

NyxId 和 Tornado 最终都桥接到 MEAI 形态,保证 `RoleGAgent` 只依赖 `ILLMProvider`。

---

## Composite + Reloadable 工厂

**CompositeLLMProviderFactory**(`CompositeLLMProviderFactory.cs` 第 6-46 行):包装 `_primaryFactory` + `_additionalProviders`;`GetProvider`(第 31-37 行)先查 additional 再回退 primary;`GetAvailableProviders`(第 41-46 行)合并去重。

**ReloadableLLMProviderFactory**(`ReloadableLLMProviderFactory.cs` 第 12-98 行):热重载。用 `Snapshot(Factory, Version, LastFailedVersion)` record(第 14 行)原子 swap。`GetCurrentFactory`(第 49-60 行):version 匹配走 fast path(无锁),否则 `RebuildFactory`(第 62-98 行,`Interlocked.CompareExchange` swap;异常时记 `LastFailedVersion` 抑制重复日志,保留旧 snapshot)。

---

## 验收

1. ILLMProvider 唯一调用方式?(ChatStreamAsync,流式)
2. NyxId/Tornado 和 MEAI 关系?(都桥接到 MEAI 形态)
3. ReloadableLLMProviderFactory 怎么热重载?(version-stamp + 原子 CompareExchange swap)

⟦AI:AUTO-LOOP⟧
