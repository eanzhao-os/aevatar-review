# 上游文档索引:canon + adr 导读(不复制全文,只加导读)

## 关键代码(事实源,以 ~/Code/aevatar 为准)

本篇是 `~/Code/aevatar/docs/canon/`(26 篇)+ `docs/adr/`(36 篇)的导读索引,不复制全文。

---

## docs/canon/(26 篇,全 active)

| 文件 | 标题 | 本 review 对应章节 |
|---|---|---|
| `overview.md` | Aevatar 项目架构(Maker 插件化基线) | 01/01、02/06、06/05 |
| `architecture.md` | Aevatar Foundation | 03/01-06、05/01 |
| `architecture-vocabulary.md` | Architecture Vocabulary | 08/01 |
| `cqrs-projection.md` | Aevatar CQRS 架构 | 05/01-02 |
| `event-sourcing.md` | Event Sourcing 基线 | 03/02、03/04 |
| `llm-streaming.md` | Workflow LLM 流式链路 | 01/02、05/04 |
| `chat-api.md` | Workflow Chat API(框架层) | 01/02 |
| `workflow-primitives.md` | Workflow Primitives 参考手册 | 02/01、02/04 |
| `workflow-runtime.md` | 工作流引擎设计与实践 | 01/03、02/02-03 |
| `role-model.md` | Role 与工作流、Connector 配置指南 | 04/01、04/03、02/07 |
| `connector.md` | Connector 配置与执行逻辑 | 02/07 |
| `module-placement-map.md` | Module Placement Map | 00/02 |
| `sdk-dotnet.md` | .NET Workflow SDK Quick Start | — |
| `scripting.md` | Aevatar.Scripting 架构文档 | 07/05 |
| `observability.md` | Aevatar Observability — OTel 约定 | 07/07 |
| `status-dashboard.md` | /status 状态面板架构 | 07/07 |
| `voice-presence-integration.md` | Voice Presence Integration | 07/04 |
| `actor-evolution.md` | Actor Evolution Canon Matrix | 03/* |
| `gagent-registry-ownership.md` | GAgent Registry Ownership | — |
| `scheduled-skill-runners.md` | Scheduled Skill Runners | — |
| `nyxid-llm-integration.md` | NyxID LLM Provider 集成指南 | 04/02 |
| `nyxid-responses-direct.md` | NyxID Responses 直连 | 01/02 |
| `nyxid-connected-service-tools.md` | NyxID Connected-Service LLM Tools | 04/03 |
| `lark-reply-completion-semantics.md` | Lark Reply Chain Completion Semantics | 07/01 |
| `frontend-design.md` | Aevatar 前端设计基线 | 07/06 |
| `aevatar-channel-architecture.md` | [RFC] Multi-Channel Adapter Architecture(236KB) | 07/01 |

---

## docs/adr/(36 篇,按主题导读)

### 架构 / 拆分 / 运行时
- `0001-project-split-strategy`(active):项目拆分策略
- `0002-mainnet-architecture`(active):Mainnet 架构(§8 Orleans/Kafka/Garnet)→ 01/01、06/02-04
- `0007-stream-forward`(active):Stream Forward 架构 → 03/05
- `0019-stable-agent-kind-identity`(accepted):AgentKind 替代 CLR-name 身份
- `0020-actor-state-version-placement`(accepted):state schema version 在 runtime envelope
- `0030-gagent-registry-agent-kind-key`(accepted):Registry 用 AgentKind 作业务 key

### Kafka / 分布式 / 持久化
- `0003-kafka-transport`(active):Orleans KafkaProvider Backend → 06/03
- `0032-mainnet-garnet-clustering`(accepted):Garnet 共享 membership → 06/04

### Workflow / Maker
- `0006-multi-agent-evolution`(superseded):Actor 化 & 多智能体演进 → 02/06
- `0034-workflow-saga-compensation-protocol`(proposed):Saga/补偿协议 → 02/03
- `0015-agui-sse-projection-session-pipeline`(active):AGUI/SSE 投影 session → 05/04

### Channel / 平台
- `0008`(superseded)/`0009`(accepted)/`0010`(accepted)/`0011`(superseded)/`0012`(accepted)/`0013`(accepted)/`0014`(accepted):Channel Runtime 演进 → 07/01

### Chat / Voice
- `0024-chat-route-policy`(Accepted)→ 07/03
- `0025-voice-router-integration`(Accepted)/`0031-voice-edge-local-tools`(Accepted)/`0033-voice-provider-nyxid-ephemeral-broker`(proposed)→ 07/04
- `0026-tool-first-chat-ingress`(Accepted)→ 07/03
- `0021-lark-reply-chain-completion-semantics`(Proposed)/`0027-lark-reply-run-dispatcher-plain-task-handoff`(Accepted)→ 07/01

### Studio / 身份
- `0016-studio-member-first`(accepted)/`0017-studio-team-first`(accepted)→ 07/05
- `0018-per-user-nyxid-binding-via-oauth-broker`(accepted)/`0028-studio-team-accepted-receipt`(accepted)/`0029-identity-oauth-accepted-ack`(accepted)→ 07/05

### 可观测性
- `0022-otel-aevatar-semantic-conventions`(proposed)/`0023-two-tier-inspector`(proposed)→ 07/07

> 0004/0005 不存在(序号空缺)。状态大小写不一致(accepted/Accepted/active/proposed),按 front matter 原样。

⟦AI:AUTO-LOOP⟧
