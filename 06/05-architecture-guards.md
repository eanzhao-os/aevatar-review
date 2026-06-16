# 架构门禁:architecture_guards.sh / slow_test_guards.sh 守卫什么

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `tools/ci/architecture_guards.sh`(1998 行):单入口 bash,跑 `rg`/`awk`/`python3` + ~30 子 guard 脚本。
- `tools/ci/slow_test_guards.sh`(29 行):慢测试回归套件入口。
- `docs/canon/overview.md` 第 99-112 行:§7 架构门禁(必须通过)+ 四个 mandatory gate + guard 语义。

---

## 四个 mandatory gate(`overview.md` 第 101-104 行)

1. `bash tools/ci/architecture_guards.sh`(架构守卫)
2. `dotnet build aevatar.slnx --nologo`(构建)
3. `dotnet test aevatar.slnx --nologo`(快测试主路径)
4. `bash tools/ci/slow_test_guards.sh`(分钟级自演进回归)

---

## architecture_guards.sh 关键守卫(按行号)

| 守卫 | 行号 | 禁止/强制什么 |
|---|---|---|
| 禁止 legacy host 项目 | 第 32-35 行 | `Aevatar.Host.Api`/`Aevatar.Host.Gateway` |
| Directory.Build 版本 | 第 40-79 行 | 强制 `0.1.0-beta`/`0.1.0.0` |
| Channel 入站凭证 | 第 85-122 行 | `ChannelInboundEvent` 保留 field 9 + 名 `registration_token` |
| Workflow.Core 交互边界 | 第 124-177 行 | 只持 typed `InteractionSpec`,不持 channel 内容/原始 Lark card |
| **禁止 query-time replay** | 第 289-339 行 | QueryPort/QueryService/ApplicationService 不得在请求路径 replay 事件/重建 state/物化投影 |
| 禁止 provider 非流式 ChatAsync | 第 392-400 行 | 必须用 `ChatStreamAsync` |
| 禁止 legacy metadata bag | 第 402-416 行 | `CommandContext.Metadata`/`EventEnvelope.Metadata` 等不得在 core context |
| 禁止直投 `actor.HandleEventAsync` | 第 646-692 行 | 仅 allowlist(`LocalActor.cs`/`RuntimeActorGrain.cs`)外禁止 raw `SubscribeAsync<EventEnvelope>` |
| `DispatchAsync` 只返回 DispatchAdmission | 第 714-744 行 | dispatch port 不得调/await `HandleEventAsync` |
| 禁止端口 5000/5050 | 第 760-794 行 | 用 5100 |
| EventSourcing 事实纯度 | 第 1028-1078 行 | 禁止 `DefaultAutoPersistedStateEventFactory`、`StateStore.LoadAsync` in `GAgentBase<TState>` |
| **stateful GAgent 直改守卫** | 第 1080-1226 行 | AWK AST-walk 禁止 `GAgentBase` 派生类里 `State.X =` 直改(必须发领域事件) |
| MassTransit pin v8.x | 第 1335-1350 行 | v9 禁止 |
| **Workflow→Maker 反向依赖** | 第 1467-1475 行 | `src/workflow` 不得引用 `Aevatar.Maker.*.csproj` |
| 禁止 legacy Maker 项目 + AddMakerCapability + /api/maker | 第 1477-1498 行 | — |
| 强制 Mainnet 装配 Maker | 第 1500-1521 行 | 必须调 `AddAevatarPlatform(...EnableMakerExtensions=true...)` |
| 禁止进程内 SemaphoreSlim 仲裁投影 | 第 1594-1597 行 | — |
| 禁止中间层内存 ID 映射字典 | 第 1648-1695 行 | 必须 actor 化编排/lease handle/分布式状态 |
| 投影 provider 业务无关 | 第 1724-1765 行 | 不得 ref Workflow/AI;agents 不得 ref 具体 projection provider |

---

## 为什么"禁止 Workflow→Maker 反向依赖"是 CI 强制

`architecture_guards.sh` 第 1467-1475 行:扫描 `src/workflow` 的 `*.csproj`,任何引用 `Aevatar.Maker.*.csproj` 都 `exit 1`。

**原因**(`overview.md:108`):Maker 是 **workflow 扩展插件**,不是 foundation 依赖。依赖方向是 Maker→Workflow。禁止反向是为了让 Workflow(稳定核心)不能反向引用 Maker 插件(否则成环,破坏插件模型)。由第 1490-1493 行(`AddMakerCapability` 禁止)+ `0002-mainnet-architecture.md:141`("Maker 以插件方式装配到 Mainnet")共同强制。

---

## slow_test_guards.sh(`slow_test_guards.sh` 29 行)

- 第 10-16 行:构建 `dotnet test` args(`-m:1`/`UseSharedCompilation=false`/`NuGetAudit=false`)
- 第 18-24 行:`SLOW_TEST_NO_RESTORE`/`SLOW_TEST_NO_BUILD` opt-out
- 第 26 行:跑 `test/Aevatar.Integration.Slow.Tests` —— 分钟级自演进回归(从快测试主路径拆出)

---

## 验收

1. 四个 mandatory gate 是什么?(architecture_guards + build + test + slow_test_guards)
2. 为什么禁止 Workflow→Maker?(Maker 是 Workflow 插件,反向依赖成环破坏插件模型)
3. stateful GAgent 为什么禁止 `State.X=` 直改?(必须发领域事件,Event Sourcing 纯度)
4. 快测试和慢测试怎么分?(dotnet test aevatar.slnx 快;slow_test_guards 慢分钟级)

⟦AI:AUTO-LOOP⟧
