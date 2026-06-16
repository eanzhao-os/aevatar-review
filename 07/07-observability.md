# 可观测性:OTel aevatar.* 语义约定 + 两级 Inspector + /status 面板

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.Abstractions/Observability/AevatarActivitySource.cs` 第 18-33 行:tag 常量(`aevatar.agent.id/.type/.parent`、`aevatar.event.id/.type/.direction/.publisher`、`aevatar.projection.name/.state.version/.last_event_id`、`aevatar.readmodel.name/.state.version/.id`、`aevatar.workflow.run_id/.name/.step`);第 35-38 行:activity 名(`aevatar.agent.spawn/.deactivate/.link/.unlink`)。
- `src/Aevatar.AI.Core/Observability/GenAIActivitySource.cs` + `GenAIObservabilityMiddleware.cs`:标准 OTel GenAI semconv(`gen_ai.client.token.usage` 等)。
- `src/Aevatar.Mainnet.Host.Api/Status/StatusEndpoints.cs` 第 23、27、40 行:`MapStatusEndpoints`;`GET /api/status`(JSON `StatusResponse{docs,counts,targets}` via `IHealthStatusQueryPort`,第 54-58 行);`GET /status`(HTML `StatusHtml.Page`)。
- `docs/canon/status-dashboard.md`(active,/status 面板架构)、`docs/canon/observability.md`(active,OTel 约定)。
- `docs/adr/0022-otel-aevatar-semantic-conventions.md`(proposed):aevatar.* activity 语义约定,引用 `AevatarActivitySource.cs` + `GenAIActivitySource.cs`。
- `docs/adr/0023-two-tier-inspector-architecture.md`(proposed):两级 Inspector(canonical readmodel vs observation OTel)。
- `tools/ci/inspector_tier_boundary_guard.sh`:ADR-0023 tier 边界守卫(L7-22 注释:Tier1=readmodel 查询;Tier2=OTel `ActivityListener`→`BoundedChannel<TelemetryFrame>`→SSE `/api/inspector/events` 仅此端点)。
- ⚠️ Inspector demo(`demos/Aevatar.Demos.Inspector/`)在 HEAD 只剩空壳(源码在 `40a36bbe2` 被删,可从 `git show 7b8b78dac:` 恢复)。

---

## OTel aevatar.* 语义约定(ADR-0022)

`AevatarActivitySource.cs`(第 18-33 行)定义 aevatar 专属 tag:
- agent:`aevatar.agent.id/.type/.parent`
- event:`aevatar.event.id/.type/.direction/.publisher`
- projection:`aevatar.projection.name/.state.version/.last_event_id`
- readmodel:`aevatar.readmodel.name/.state.version/.id`
- workflow:`aevatar.workflow.run_id/.name/.step`

activity 名(第 35-38 行):`aevatar.agent.spawn/.deactivate/.link/.unlink`。

GenAI 部分(`GenAIActivitySource.cs` + `GenAIObservabilityMiddleware`)用标准 OTel GenAI semconv(`gen_ai.client.token.usage`、`gen_ai.client.operation.duration`、`aevatar.tool.invocation.duration`)—— 见 `04/04`。

---

## /status 面板

`StatusEndpoints.cs` 第 23 行 `MapStatusEndpoints`:
- `GET /api/status`(第 27 行):JSON `StatusResponse{docs, counts, targets}`(第 54-58 行,经 `IHealthStatusQueryPort`)
- `GET /status`(第 40 行):HTML(`StatusHtml.Page`)

canon:`docs/canon/status-dashboard.md`(active)。

---

## 两级 Inspector(ADR-0023)

| Tier | 数据源 | 性质 |
|---|---|---|
| Tier 1 | canonical readmodel(经 query port) | **ground truth** |
| Tier 2 | OTel observation(`ActivityListener`→`BoundedChannel<TelemetryFrame>`→SSE) | **动画数据**,非查询源 |

`inspector_tier_boundary_guard.sh`(L7-22)强制:只有 `/api/inspector/events` 端点可引用 `TelemetryFrame`;禁止 collection-typed 返回(会暗示历史 replay)。

> ⚠️ Inspector demo 在 HEAD 已删(空壳),tier 守卫仍存活。demo 源码可从 `git show 7b8b78dac:` 恢复。

---

## 验收

1. aevatar.* 语义约定在哪定义?(`AevatarActivitySource.cs`,ADR-0022)
2. /status 返回什么?(JSON StatusResponse + HTML 面板)
3. 两级 Inspector 区别?(Tier1 canonical readmodel=ground truth;Tier2 OTel=动画)
4. Inspector demo 还在吗?(HEAD 已删,空壳)

⟦AI:AUTO-LOOP⟧
