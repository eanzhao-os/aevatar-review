# GAgentBase 统一事件 pipeline:静态[EventHandler] + 动态 IEventModule + 双 Hook

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Core/GAgentBase.cs` 第 31 行:`GAgentBase : IAgent, IEventModuleContainer<IEventHandlerContext>`;第 121-190 行:`HandleEventAsync`;第 402-411 行:`GetOrBuildPipeline`(lazy + cache);第 192-234 行:双 Hook;第 376-397 行:`LoadHooksFromDI`/`RunHooksAsync`。
- `src/Aevatar.Foundation.Abstractions/Attributes/EventHandlerAttribute.cs` 第 13-36 行:`Priority`(第 18 行,lower=first)/`AllowSelfHandling`/`OnlySelfHandling`/`EndpointName`。
- `src/Aevatar.Foundation.Abstractions/EventModules/IEventModule.cs` 第 13-27 行:`Name`/`Priority`/`CanHandle`/`HandleAsync`。
- `src/Aevatar.Foundation.Core/Pipeline/EventPipelineBuilder.cs` 第 16-27 行:`Build`(静态 handler adapter + 动态 module,按 Priority 升序排序)。
- `src/Aevatar.Foundation.Core/Pipeline/StaticHandlerAdapter.cs` 第 12-101 行:编译 typed delegate(非反射)。
- `src/Aevatar.Foundation.Abstractions/Hooks/IGAgentExecutionHook.cs` 第 16-32 行:`OnEventHandlerStartAsync`/`OnEventHandlerEndAsync`/`OnErrorAsync`/`Priority`。
- `docs/canon/architecture.md` 第 73-107 行:§Foundation.Core。

---

## 统一 pipeline

`GAgentBase` 把两类处理器合并成一条 pipeline:

| 来源 | 机制 | 文件 |
|---|---|---|
| 静态 | `[EventHandler]` 特性标注的方法 | `EventHandlerAttribute.cs:13` |
| 动态 | `IEventModule<IEventHandlerContext>`(运行时注册) | `IEventModule.cs:13` |

`EventPipelineBuilder.Build`(`EventPipelineBuilder.cs` 第 16-27 行):
1. 每个静态 handler 经 `StaticHandlerAdapter` 适配成 `IEventModule`(第 19-20 行)
2. 与动态 module 拼接(第 22-24 行)
3. `Array.Sort(... Priority.CompareTo)` 升序排序(第 25 行)—— **Priority 小的先执行**

`StaticHandlerAdapter`(第 12-101 行)编译 typed delegate(`CompileHandler` 第 73-87 行)而非反射,提升性能。

pipeline lazy 构建并缓存(`GetOrBuildPipeline`,`GAgentBase.cs` 第 402-411 行),在 `RegisterModule`/`SetModules` 时失效(第 246、262 行)。

---

## HandleEventAsync 执行流程(第 121-190 行)

1. `StateGuard.BeginWriteScope()`(第 123 行)—— 开启状态写权限
2. external-link short-circuit(第 132-136 行)
3. `GetOrBuildPipeline()`(第 138 行)
4. 按 priority 顺序 `foreach` handler(第 140-184 行):
   - **双 Hook 通道**:virtual `OnEventHandlerStartAsync`(第 160 行)+ `RunHooksAsync(OnEventHandlerStart)`(第 161 行)
   - 执行 `handler.HandleAsync`(第 163 行)
   - 异常时 `RunHooksAsync(OnError)`(第 170 行)+ fail-fast(除非 `ShouldSuppressHandlerException`,第 172-173 行)
   - finally:hook-pipeline `OnEventHandlerEndAsync`(第 181 行)+ virtual `OnEventHandlerEndAsync`(第 182 行)

---

## 双 Hook 通道

两个并行扩展机制(`GAgentBase.cs` 第 192-234 行):

| 通道 | 机制 | 文件 |
|---|---|---|
| Virtual 方法 | 子类 override | 第 195-218 行 |
| `IGAgentExecutionHook` DI pipeline | DI 注册的 hook | `IGAgentExecutionHook.cs:16-32` |

DI hook 从 `LoadHooksFromDI`(第 376-384 行)加载,按 priority 排序,在 `RunHooksAsync`(第 387-397 行)best-effort 执行。这让横切关注点(日志/追踪/指标)可在不继承基类的情况下注入。

---

## 验收

1. 静态 `[EventHandler]` 和动态 `IEventModule` 怎么合并?(`EventPipelineBuilder.Build` 按 Priority 升序排序)
2. Priority 小的先还是后执行?(先,`EventPipelineBuilder.cs:25`)
3. 双 Hook 通道是什么?(virtual override + DI `IGAgentExecutionHook` pipeline)

⟦AI:AUTO-LOOP⟧
