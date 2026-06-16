# ChatRouting:ChatRoutePolicy(配置 Actor + 边界解析器)+ tool-first ingress

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.ChatRouting.Abstractions/`:`chat_route_policy.proto`、`buf.yaml`(proto-only 底层)。
- `src/Aevatar.ChatRouting.Core/ChatRouteResolver.cs` 第 10、26 行:无状态边界解析器(`Resolve(snapshot, input) → ChatRouteDecision`;解析顺序:rules by priority → default_target → env/options fallback);`EnvChatRouteFallbackProvider.cs`(冷启动 fallback = `ForwardToModel(env AEVATAR_DEFAULT_LLM_MODEL)`)。
- `agents/Aevatar.GAgents.ChatRouting/ChatRoutePolicyGAgent.cs`:per-scope **config-only** actor(处理 Upsert/RemoveRule,不 turn dispatch);`ChatRoutePolicyCurrentStateProjector.cs`、`ChatRoutePolicyCommittedStateProjectionActivationPlanProvider.cs`。
- `docs/adr/0024-chat-route-policy.md`(Accepted):L41-49 三段式(policy authority `ChatRoutePolicyGAgent` + 决策引擎 `ChatRouteResolver` 库函数 + 查询视图 `ChatRoutePolicyCurrentStateDocument`,热路径零新 actor hop);L62-68 `ChatRouteDecision` 不持久化;L135-144 `default_target` 必填 + 冷启动 fallback 标 `used_fallback=true`。
- `docs/adr/0026-tool-first-chat-ingress.md`(Accepted):L28-40 tool-calling backbone 已 load-bearing(`ToolCallLoop` + 30+ `IAgentToolSource`);L49-59 折叠到 `Reject` + `ForwardToModel`(`ForwardToGAgent`→tool `aevatar_invoke_gagent` 等);L62-72 `ForwardToModel` 增 `tool_set_ref` + `tool_choice_hint`。

---

## 两层切分

ChatRouting 分两层:

| 层 | 项目 | 职责 |
|---|---|---|
| 边界解析器 | `ChatRouting.Core/ChatRouteResolver.cs:10` | 无状态库函数,热路径零新 actor hop |
| 配置 Actor | `agents/…/ChatRoutePolicyGAgent.cs` | per-scope config-only(Upsert/RemoveRule,不 dispatch) |

`ChatRouteDecision`(ADR-0024 L62-68)**不持久化** —— 它是 per-request 决策,不是事实。

---

## 三段式设计(ADR-0024 第 41-49 行)

1. policy authority:`ChatRoutePolicyGAgent`(配置 actor)
2. 决策引擎:`ChatRouteResolver` 库函数
3. 查询视图:`ChatRoutePolicyCurrentStateDocument`

热路径**零新 actor hop** —— 解析是纯函数调用,不需要额外 actor 往返。

---

## Tool-first ingress(ADR-0026)

`docs/adr/0026`:tool-calling backbone 已是 load-bearing(`ToolCallLoop` + 30+ `IAgentToolSource`)。Forward actions 折叠到 `Reject` + `ForwardToModel`:
- `ForwardToGAgent` → tool `aevatar_invoke_gagent`
- `ForwardToTeam` → tool `aevatar_invoke_team`
- `ForwardToWorkflow` → tool `aevatar_start_workflow`

`ForwardToModel` 增 `tool_set_ref` + `tool_choice_hint`(含 `voice_attach_target` 子消息给 `/ws/voice` attach)。

---

## 验收

1. ChatRouteResolver 是 actor 吗?(不是,是无状态库函数,热路径零 actor hop)
2. ChatRouteDecision 持久化吗?(不,是 per-request 决策)
3. tool-first ingress 把 Forward 折叠成什么?(Reject + ForwardToModel,Forward 动作变 tool)
4. ChatRoutePolicyGAgent 做什么?(per-scope config-only,Upsert/RemoveRule)

⟦AI:AUTO-LOOP⟧
