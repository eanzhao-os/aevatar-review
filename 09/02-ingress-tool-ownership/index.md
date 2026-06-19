# 方案 02 · Ingress 工具所有权:自有工具服务端执行、永不上线

> 这是 [09 方案区](../index.md) 下的**第二份方案**。针对 [10/03 已知问题](../../10/03-ingress-own-tool-stream-leak.md)(GitHub `aevatarAI/aevatar#2269`)给出可落地的修复设计。本方案是一个独立单元(本概览 + 2 章)。

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> 本方案回答:把 aevatar 当 model 套进 agentic 客户端时,怎么让 aevatar 的**自有工具**在服务端执行、对客户端完全隐形(「伪装成模型返回」),同时仍把**客户端自己声明的**工具转发回客户端执行。所有论断回指下面这条「分类 → 路由 → 渲染」主线的事实源脊柱:
>
> - **分类(谁是自有 / 谁该转发)**:`src/platform/Aevatar.GAgentService.Application/Responses/ResponsesToolClassificationService.cs`(`forwarded = 客户端声明工具 ∖ substitute`;additive 名当前未被排除 —— R3 缺口的源头)。
> - **执行与路由**:`src/platform/Aevatar.GAgentService.Core/GAgents/LlmSessionGAgent.cs`(`RunLlmLoopAsync` 的 forwarded/local 分桶、`BuildEffectiveToolsAsync` 的实时发现、`MaxToolRounds` 循环)。
> - **流式渲染(泄漏点)**:`src/platform/Aevatar.GAgentService.Application/Responses/LlmSessionRunObservationAccumulator.cs` + `src/Aevatar.Mainnet.Host.Api/ChatCompletions/ChatCompletionsEndpoints.cs`。
>
> 核对基线:`feature/integrate`(本次会话核对于 HEAD `82e957bc8` 附近)。本方案已经 **codex 设计评审**,审出 6 个实现缺口并已并入(见 02 章)。下文工具名为占位语义。

---

## 一句话结论(先看这个,再读细节)

这条链路的修复是**非对称、按所有权**判定的,落在**两个**点上,缺一不可:

> **aevatar 自有工具 ⇒ 服务端执行、永不上线**(客户端只看到文字);**客户端声明的工具 ⇒ 转发给客户端执行**(只有它能跑本机 shell / 改文件)。判定依据是工具的**所有权**,不是哪次实时发现先到、也不是谁先声明了同名。

- **落点一(流式渲染)**:客户端流里只允许出现「转发类」tool-call;aevatar 自有工具的 tool-call delta 一律不写给客户端。当前 `/v1/chat/completions` 把每个 delta 无差别透出,这是 [10/03](../../10/03-ingress-own-tool-stream-leak.md) 的直接症状。
- **落点二(所有权 typed 分类)**:把「aevatar 自有工具名」做成 typed 事实(`owned_tool_names`),分类时永不把它放进 forwarded 桶;撞名时所有权优先;发现抖动不改变所有权。

**决策(2026-06-19,用户拍板)**:采「非对称转发」而非「纯服务端永不转发」(后者会让 codex 的本地 shell / 文件工具无法通过 aevatar 使用)。Part 1 + Part 2 **一起 ship**(只上 Part 1 只能止住 CC 当前症状,撞名 + 完成阶段泄漏仍在)。

## 本方案怎么读

| 章节 | 回答的问题 | 现状 |
|---|---|---|
| [01 泄漏链路与非对称所有权不变量](01-leak-and-asymmetric-rule.md) | 泄漏到底在哪一层?为什么是 additive 工具?该立什么不变量?为什么不是「纯服务端」 | 根因坐实;不变量明确 |
| [02 两个落点、codex 审出的 6 缺口、落地](02-fix-and-rollout.md) | 两个落点具体怎么改?codex 审出哪些坑?里程碑/issue/验收/诚实缺口 | 设计已评审;⚠️ 未实现 |

## 这条方案的设计正当性

为什么是「按所有权非对称转发」,而不是「aevatar 永不向客户端转发任何工具(纯服务端 agent)」?因为 agentic 客户端(codex/zcode)的本地工具(`shell`、改文件)只能在**客户端机器**上执行,aevatar 根本跑不了;若一律不转发,这些客户端的本地能力就废了。反过来,aevatar 自有工具(ornn / skills 等)只有 aevatar 能执行,客户端拿到也没用。所以正确的边界是**按所有权双向收口**:自有的留在服务端、对客户端隐形;客户端的转发回去。这也正好把 [10/02](../../10/02-codex-shell-vs-aevatar-tools.md) 那条「选择之争」的下游清干净 —— 即便 LLM 选了 aevatar 自有工具(10/02 想要的结果),本方案保证这次执行对客户端**完全不可见**,不会再触发客户端的二次执行失败。
