## 事实源

> 本篇汇总全书 ⚠️ 待决策项,详见 \#97 tech-debt。

# TODO List:设计待论证 / 已知缺口 / 已删组件

> 本篇汇总全书所有标 ⚠️ 的设计疑点、未实现项、已删组件。按 #97 tech-debt issue 组织。
> owner 逐条决策后,在此 ✅ 并回填结论。

## A. 已删组件(HEAD 里只剩空壳/已移除)

| # | 组件 | 状态 | 处理 | 上游/证据 |
|---|---|---|---|---|
| A1 | **A2A Interop**(3 项目) | 源码在 `8bfd8605c` 全删,空壳 | 标"历史设计" | 见 07/02 |
| A2 | **Inspector demo** | `40a36bbe2` 删,空壳 + tier guard 在 | 标"已删 demo" | 见 07/07 |
| A3 | **demos**(Workflow/Cli/Maker/CaseProjection) | `4a029981c`/`4ff5c2d1b` 删 | cookbook 只留 HEAD 可跑 | 见 08/03 |
| A4 | **StateMirror Projection** | `da7944cf2` 完全移除 | 文档删除该 provider | 见 05/03 |
| A5 | **MassTransit transport** | 零 csproj 消费,仅 props 残留 + guard | 标"历史路径" | 上游 [aevatar#2209](https://github.com/aevatarAI/aevatar/issues/2209) |

## B. 文档提到但代码未实现 / 状态不明

| # | 疑点 | 文档出处 | 实际 | 决策 |
|---|---|---|---|---|
| B1 | **RunManager / RunContextScope** | `architecture.md` | 只有 `AsyncLocalAgentContext` | ⚠️ 待 owner |
| B2 | **saga 补偿**(ADR-0034 proposed) | 02/03 | 实现程度不明 | ⚠️ 待 owner |
| B3 | **Timeline/Graph ArtifactProjector** | canon `architecture.md` | 已删,从 InsightReport 派生 | canon 需同步 |
| B4 | **streaming-proxy room/participant** | Sunset 2026-11-25 | `/v1/responses` 无对应 | ⚠️ 待 owner |
| B5 | **voice 静态 key 移除**(ADR-0033) | 07/04 | 落地不明 | ⚠️ 待 owner |

## C. 设计可疑(正当性未确认)

| # | 疑点 | 上下文 | 建议 | 上游 |
|---|---|---|---|---|
| C1 | kernel 隐式依赖展开(有 target_role 自动加 llm_call) | 02/04 | 显式模式? | — |
| C2 | `DefaultMaxToolRounds = int.MaxValue` | 04/04 | fallback 加固为有限值 | 上游 [aevatar#2210](https://github.com/aevatarAI/aevatar/issues/2210) |
| C3 | `ICommittedStateEventPublisher` 是 internal | 03/05 | 有意封装 vs 遗留 | — |
| C4 | NyxId/Tornado 都桥接 MEAI | 04/02 | 统一抽象 vs 适配遗留 | — |
| C5 | `CommittedStateProjectionActivationHook` 自激活幂等 | 05/02 | 重复抑制可靠性 | — |
| C6 | 9 个 `.slnf` 切分依据 | 00/02 | 有意设计 vs 演进遗留 | — |
| C7 | Telegram direct-callback 路径移除 | 07/01 | 有意收敛 vs 未完成 | — |
| C8 | 无独立 Orleans ADR | 06/02 | 是否补 ADR | — |

## 已确认结论

- **A5 MassTransit**:经源码核实**已完全不用**。当前 Kafka transport 是手写 Confluent.Kafka 客户端藏在 Orleans streaming 接口后。→ 文档标"历史路径"。上游 issue [#2209](https://github.com/aevatarAI/aevatar/issues/2209)。
- **C2 无限轮次**:经源码核实**不是 bug** —— 基类默认 40 轮(`AIGAgentBase.MaxToolRounds`)。但 `int.MaxValue` fallback 是隐患。上游 issue [#2210](https://github.com/aevatarAI/aevatar/issues/2210)。

⟦AI:AUTO-LOOP⟧
