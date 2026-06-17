# GAgentBase 统一事件 pipeline:静态[EventHandler] + 动态 IEventModule + 双 Hook

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Core/GAgentBase.cs` 第 31 行:`GAgentBase` 同时是 `IAgent` 与 `IEventModuleContainer<IEventHandlerContext>`;第 121-190 行:统一 dispatch 主路径;第 192-234 行:virtual hook;第 376-411 行:DI hook 与 pipeline cache。
- `src/Aevatar.Foundation.Abstractions/Attributes/EventHandlerAttribute.cs` 第 13-36 行:静态 handler 标注与 priority。
- `src/Aevatar.Foundation.Abstractions/EventModules/IEventModule.cs` 第 13-27 行:动态模块契约。
- `src/Aevatar.Foundation.Core/Pipeline/EventPipelineBuilder.cs` 第 16-27 行:静态 handler adapter 与动态 module 合并,按 priority 升序排序。
- `src/Aevatar.Foundation.Core/Pipeline/StaticHandlerAdapter.cs` 第 12-101 行:静态 handler 适配为 pipeline module。
- `src/Aevatar.Foundation.Abstractions/Hooks/IGAgentExecutionHook.cs` 第 16-32 行:DI hook 的 start/end/error 观测点。
- `docs/canon/architecture.md` 第 73-107 行:Foundation.Core 职责。

---

## GAgentBase 解决的问题

Actor runtime 只负责把 envelope 交给 Agent。到了 Agent 内部,还需要一个稳定规则回答三个问题:哪些 handler 参与处理?动态能力怎么插进来?日志、追踪、指标这类横切逻辑放在哪里?

`GAgentBase` 的答案是一条统一 pipeline。开发者写在类上的 `[EventHandler]` 是静态处理器;运行期注册的 `IEventModule<IEventHandlerContext>` 是动态处理器。二者都会被适配成同一种 pipeline entry,再按 priority 合并执行。

---

## 为什么静态和动态要合并

如果静态 handler 和动态 module 各跑一套链路,优先级、错误处理和观测点就会分叉。Aevatar 把它们合并后,一个 envelope 进入 Agent 时只有一套顺序、一套 fail-fast 策略、一套 hook 观测面。

这里的设计收益不是“少写几行反射代码”,而是把 Agent 的可扩展性变成可推理的顺序语义:priority 小的先执行;handler 是否能处理由 `CanHandle` 决定;异常默认中断,除非子类明确选择 suppress。

---

## 双 Hook 的位置

GAgentBase 留了两条 hook 通道。第一条是子类 override 的 virtual hook,适合 agent 自己的局部扩展。第二条是 DI 注入的 `IGAgentExecutionHook`,适合 tracing、metrics、审计这类跨 agent 的横切能力。

这两条通道共享同一个 handler 生命周期,所以观察到的是同一条 pipeline,不会出现“静态 handler 有日志、动态 module 没日志”这类分裂。

---

## 和状态写保护的关系

`HandleEventAsync` 进入时会打开 StateGuard 的 writable scope。也就是说,pipeline 不是任意业务代码的集合,而是 actor 串行 mailbox 内、被框架允许修改状态的执行区。下一篇会专门讲这个 AsyncLocal 闸门为什么存在。

---

## 验收

1. 静态 `[EventHandler]` 和动态 `IEventModule` 怎么合并?(适配成同一种 pipeline entry 后按 priority 升序排序)
2. Priority 小的先还是后执行?(先执行)
3. 双 Hook 通道是什么?(子类 virtual hook + DI `IGAgentExecutionHook` pipeline)

⟦AI:AUTO-LOOP⟧
