# LLM Provider 抽象与实现:MEAI / NyxId / Tornado

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## Provider 契约

`ILLMProvider`(`ILLMProvider` )只暴露一个流式方法:

- `string Name`()
- `LLMProviderCapabilities Capabilities`(默认 `TextOnly`,)
- `IAsyncEnumerable<LLMStreamChunk> ChatStreamAsync(LLMRequest, CancellationToken)`()—— **唯一的调用方式**(非流式 `ChatAsync` 已移除,重构注释)

`ILLMProviderFactory`():`GetProvider(name)`/`GetDefault()`/`GetAvailableProviders()`。

---

## 三个 Provider 实现

| Provider | 文件 | 桥接 | 说明 |
|---|---|---|---|
| **MEAI** | `MEAILLMProvider` | `Microsoft.Extensions.AI` 的 `IChatClient` | 通用桥接;`MEAILLMProviderFactory` 持 `ImmutableDictionary` + `Register`/`SetDefault` |
| **NyxId** | `NyxIdLLMProvider` | 每路由构造 delegate MEAI provider(`CreateDelegateProvider` → `new MEAILLMProvider` ) | NyxId 网关路由 |
| **Tornado** | `TornadoLLMProvider` | `LlmTornado` 的 `TornadoApi` | 第三方 SDK 桥接 |

NyxId 和 Tornado 最终都桥接到 MEAI 形态,保证 `RoleGAgent` 只依赖 `ILLMProvider`。

---

## Composite + Reloadable 工厂

**CompositeLLMProviderFactory**(`CompositeLLMProviderFactory` ):包装 `_primaryFactory` + `_additionalProviders`;`GetProvider`()先查 additional 再回退 primary;`GetAvailableProviders`()合并去重。

**ReloadableLLMProviderFactory**(`ReloadableLLMProviderFactory` ):热重载。用 `Snapshot(Factory, Version, LastFailedVersion)` record()原子 swap。`GetCurrentFactory`():version 匹配走 fast path(无锁),否则 `RebuildFactory`(`Interlocked.CompareExchange` swap;异常时记 `LastFailedVersion` 抑制重复日志,保留旧 snapshot)。

---

## 验收

1. ILLMProvider 唯一调用方式?(ChatStreamAsync,流式)
2. NyxId/Tornado 和 MEAI 关系?(都桥接到 MEAI 形态)
3. ReloadableLLMProviderFactory 怎么热重载?(version-stamp + 原子 CompareExchange swap)

⟦AI:AUTO-LOOP⟧
