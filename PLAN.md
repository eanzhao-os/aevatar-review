# 解读计划与进度

> 当前权威书目：`00–13` 共 14 个 block、72 篇实质章节；全部章节已完成。
>
> `07/05` 为 milestone 40 专题登记（`target`，未落地），不计入上述 72 篇。
>
> 上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`；核验日期：`2026-07-25`。

## 实施原则

1. 自顶向下：先建立请求与身份主线，再下钻 Actor、Workflow、CQRS 和生产边界。
2. 以冻结事实为准：current 论断必须回到 E1；canon、ADR、issue 和生产观察不能替代代码事实。
3. 设计导向：正文解释职责、协议、状态所有权、不变量和取舍，不把文件名/行号表当作文章。
4. 示例诚实：只使用 `verified-static`、`verified-local`、`verified-production-versioned`。
5. 边界清楚：`current`、`mixed`、`historical`、`target` 不混写。

## 章节清单（72/72）

### `00` 导读与版本基线（3）

- [x] [00/01-reading-guide.md](00/01-reading-guide.md) — `current` — 全书阅读指南：三条路线与证据纪律 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/167)
- [x] [00/02-version-evidence-and-status.md](00/02-version-evidence-and-status.md) — `current` — 版本基线与证据等级：全书论断的可信度规则 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/168)
- [x] [00/03-repository-map.md](00/03-repository-map.md) — `current` — 仓库地图：100+ 项目面前如何选阅读面 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/169)

### `01` 启动与请求全景（4）

- [x] [01/01-quick-start.md](01/01-quick-start.md) — `current` — 快速上手:本地启动 Host 并完成第一次请求 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/170)
- [x] [01/02-hosts-and-composition.md](01/02-hosts-and-composition.md) — `current` — Host 与组合：协议终结与能力装配的边界 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/171)
- [x] [01/03-chat-conversation-turn-contract.md](01/03-chat-conversation-turn-contract.md) — `current` — Chat / Conversation / Turn 服务端身份契约 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/172)
- [x] [01/04-request-streaming-lifecycle.md](01/04-request-streaming-lifecycle.md) — `mixed` — 请求与流式生命周期：从 POST/WS 到终态观测 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/173)

### `02` Actor 运行内核（6）

- [x] [02/01-agent-actor-runtime.md](02/01-agent-actor-runtime.md) — `current` — Agent / Actor / Runtime:三层分离与传输底座 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/174)
- [x] [02/02-envelope-command-event-query.md](02/02-envelope-command-event-query.md) — `current` — Envelope 消息语义 —— command / reply / signal / domain event / query 的分野 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/175)
- [x] [02/03-gagent-event-pipeline.md](02/03-gagent-event-pipeline.md) — `current` — GAgent 事件处理管线：一条消息进入 actor 之后 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/176)
- [x] [02/04-state-event-sourcing-and-guard.md](02/04-state-event-sourcing-and-guard.md) — `current` — 状态与事件溯源：StateEvent、reducer 与 StateGuard — [issue](https://github.com/eanzhao-os/aevatar-review/issues/177)
- [x] [02/05-dispatch-routing-and-topology.md](02/05-dispatch-routing-and-topology.md) — `current` — Dispatch、路由与拓扑:消息怎么找到 Actor — [issue](https://github.com/eanzhao-os/aevatar-review/issues/178)
- [x] [02/06-local-runtime-and-lifecycle.md](02/06-local-runtime-and-lifecycle.md) — `current` — Local Runtime 与 Actor 生命周期 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/179)

### `03` Workflow 编排（7）

- [x] [03/01-workflow-model-and-identities.md](03/01-workflow-model-and-identities.md) — `current` — Workflow 模型与身份：定义、运行、草稿与发布物不是同一个对象 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/180)
- [x] [03/02-yaml-schema-and-validation.md](03/02-yaml-schema-and-validation.md) — `current` — Workflow YAML：一个根模式，四道不同的关 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/181)
- [x] [03/03-execution-kernel-and-outcomes.md](03/03-execution-kernel-and-outcomes.md) — `current` — Workflow 执行内核：把异步步骤收敛成一个 run 终态 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/182)
- [x] [03/04-primitives-catalog.md](03/04-primitives-catalog.md) — `current` — Workflow 原语目录：canonical type、模块与输出契约 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/183)
- [x] [03/05-pause-signal-approval-and-resume.md](03/05-pause-signal-approval-and-resume.md) — `current` — Workflow 暂停与恢复：signal、人工审批和 delivery 边界 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/184)
- [x] [03/06-saga-compensation-and-recovery.md](03/06-saga-compensation-and-recovery.md) — `mixed` — Workflow Saga：反向补偿、OutcomeUncertain 与恢复 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/185)
- [x] [03/07-connectors-and-capability-admission.md](03/07-connectors-and-capability-admission.md) — `current` — Connector 与外部能力准入：所有权、readiness 和证据时效 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/186)

### `04` AI 执行与工具（5）

- [x] [04/01-role-agent-and-streaming-run.md](04/01-role-agent-and-streaming-run.md) — `current` — RoleGAgent 与流式执行：actor turn、会话事实和终态重放 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/187)
- [x] [04/02-llm-providers-and-route-selection.md](04/02-llm-providers-and-route-selection.md) — `current` — LLM Provider 与路由选择：四类身份、owner 覆盖和安全 failover — [issue](https://github.com/eanzhao-os/aevatar-review/issues/188)
- [x] [04/03-tool-loop-catalog-and-presentation.md](04/03-tool-loop-catalog-and-presentation.md) — `current` — Tool loop、请求目录与展示事实：先冻结权力，再执行调用 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/189)
- [x] [04/04-tool-approval-and-authorization.md](04/04-tool-approval-and-authorization.md) — `current` — 工具审批与授权：先确定调用者，再等待可恢复的决定 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/190)
- [x] [04/05-prompt-overlays-and-agent-context.md](04/05-prompt-overlays-and-agent-context.md) — `current` — Prompt overlay 与 Agent context：固定层序不是授权层级 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/191)

### `05` CQRS、Projection 与 Audit（6）

- [x] [05/01-command-event-projection-readmodel.md](05/01-command-event-projection-readmodel.md) — `current` — Command、committed fact、Projection 与 ReadModel：把写入结果和查询视图分开 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/192)
- [x] [05/02-committed-state-and-observation.md](05/02-committed-state-and-observation.md) — `current` — Committed state 与 observation：持久事实和实时可见性不是一回事 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/193)
- [x] [05/03-projection-lifecycle-and-leases.md](05/03-projection-lifecycle-and-leases.md) — `current` — Projection lifecycle 与 lease：scope actor 拥有状态，handle 只负责清理 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/194)
- [x] [05/04-readmodel-stores-versioning-and-rebuild.md](05/04-readmodel-stores-versioning-and-rebuild.md) — `mixed` — ReadModel store、versioning 与 rebuild：副本可覆盖，修复必须显式 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/195)
- [x] [05/05-workflow-agui-and-live-observation.md](05/05-workflow-agui-and-live-observation.md) — `current` — Workflow AGUI 与 live observation：同源映射，不同持久性 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/196)
- [x] [05/06-audit-trail-lifecycle-and-export.md](05/06-audit-trail-lifecycle-and-export.md) — `current` — Audit Trail：生命周期、追加语义与 CloudEvents 导出 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/197)

### `06` 产品资源与身份（5）

- [x] [06/01-scope-team-member-resource-model.md](06/01-scope-team-member-resource-model.md) — `current` — Scope、Team 与 Member：产品资源、归属权威与派生 roster — [issue](https://github.com/eanzhao-os/aevatar-review/issues/198)
- [x] [06/02-draft-revision-binding-and-published-service.md](06/02-draft-revision-binding-and-published-service.md) — `current` — Draft、Revision、Binding Run 与 Published Service：五种身份，三层完成语义 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/199)
- [x] [06/03-catalog-visibility-and-scope-authorization.md](06/03-catalog-visibility-and-scope-authorization.md) — `current` — Workflow Catalog 可见性与 Scope 授权：公共模板不是私有可运行资源 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/200)
- [x] [06/04-studio-commands-acks-and-readmodels.md](06/04-studio-commands-acks-and-readmodels.md) — `current` — Studio Command、ACK 与 Read Model：受理不是提交，查询不是修复 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/201)
- [x] [06/05-work-orders-and-durable-intent.md](06/05-work-orders-and-durable-intent.md) — `current` — WorkOrder：耐久授权意图，不是通用任务队列 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/202)

### `07` Conversation、NyxIdChat 与 Agent Profile（4）

- [x] [07/01-conversation-turn-and-chat-history.md](07/01-conversation-turn-and-chat-history.md) — `current` — Conversation、Turn 与耐久聊天历史 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/203)
- [x] [07/02-nyxid-chat-actor-model-and-progress.md](07/02-nyxid-chat-actor-model-and-progress.md) — `current` — NyxIdChat Actor 模型与已提交进度 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/204)
- [x] [07/03-agent-profile-and-immutable-binding.md](07/03-agent-profile-and-immutable-binding.md) — `current` — Agent Profile 与不可变会话绑定 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/205)
- [x] [07/04-turn-authority-tool-catalog-and-retry.md](07/04-turn-authority-tool-catalog-and-retry.md) — `current` — Turn 权威、工具目录与重试 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/206)
- [x] [07/05-milestone-40-nyxid-assistant-support-contract.md](07/05-milestone-40-nyxid-assistant-support-contract.md) — `target` — M-40 专题：NyxID Assistant Support Contract v1（未落地登记，不计入冻结书目） — [issue](https://github.com/aevatarAI/aevatar/milestone/40)

### `08` Ingress、Channel、文件与语音（5）

- [x] [08/01-ingress-normalization-and-routing.md](08/01-ingress-normalization-and-routing.md) — `current` — Ingress 规范化与路由：先固定身份，再选择执行意图 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/207)
- [x] [08/02-channel-runtime-and-credential-boundary.md](08/02-channel-runtime-and-credential-boundary.md) — `current` — Channel Runtime 与凭据边界：current durable write 不保存 raw secret material — [issue](https://github.com/eanzhao-os/aevatar-review/issues/208)
- [x] [08/03-lark-delivery-interaction-and-repair.md](08/03-lark-delivery-interaction-and-repair.md) — `mixed` — Lark 投递、交互与修复：把意图、送达事实和平台故障分开 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/209)
- [x] [08/04-file-artifacts-and-attachments.md](08/04-file-artifacts-and-attachments.md) — `current` — 文件工件与附件：让字节停在边界，让引用进入事实层 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/210)
- [x] [08/05-voice-control-and-media-planes.md](08/05-voice-control-and-media-planes.md) — `mixed` — Voice 控制面与媒体面：actor 记住语义，relay 搬运 PCM — [issue](https://github.com/eanzhao-os/aevatar-review/issues/211)

### `09` Automation、调度与凭证（5）

- [x] [09/01-automation-resource-api-and-readmodels.md](09/01-automation-resource-api-and-readmodels.md) — `current` — Team Member Automation：资源 API、所有权与读模型 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/212)
- [x] [09/02-scheduled-actor-callback-and-fire.md](09/02-scheduled-actor-callback-and-fire.md) — `current` — Schedule Actor、Durable Callback 与 Fire：唤醒不是执行事实 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/213)
- [x] [09/03-owner-authorization-and-agent-key.md](09/03-owner-authorization-and-agent-key.md) — `current` — Owner 授权与 Agent Key：把无人值守权限固定成可重验计划 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/214)
- [x] [09/04-vault-reference-and-revocation-compensation.md](09/04-vault-reference-and-revocation-compensation.md) — `current` — Vault Reference 与撤销补偿：秘密不成为业务事实 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/215)
- [x] [09/05-production-canary-and-recovery.md](09/05-production-canary-and-recovery.md) — `mixed` — Production Canary 与恢复：一次执行只能证明它绑定的版本 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/216)

### `10` 分布式与生产运行（8）

- [x] [10/01-production-topology-and-configuration.md](10/01-production-topology-and-configuration.md) — `current` — 生产拓扑与配置：先选择一致性档位，再组合能力 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/217)
- [x] [10/02-orleans-runtime.md](10/02-orleans-runtime.md) — `current` — Orleans Runtime：逻辑 Actor、Grain Turn 与可恢复投递 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/218)
- [x] [10/03-garnet-clustering-and-secret-storage.md](10/03-garnet-clustering-and-secret-storage.md) — `current` — Garnet 聚类与秘密存储：共享后端，不共享语义 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/219)
- [x] [10/04-streaming-transport-and-kafka.md](10/04-streaming-transport-and-kafka.md) — `mixed` — Streaming Transport 与 Kafka：一个 Stream 身份，一套 Partition 所有权 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/220)
- [x] [10/05-authentication-scope-and-admin-authorization.md](10/05-authentication-scope-and-admin-authorization.md) — `current` — Authentication、Scope 与 Admin：四道门，不是一枚万能 Token — [issue](https://github.com/eanzhao-os/aevatar-review/issues/221)
- [x] [10/06-managed-codex-sandbox-and-delegation.md](10/06-managed-codex-sandbox-and-delegation.md) — `mixed` — Managed Codex：把执行、调用凭证与 Sandbox 委托拆成三层 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/222)
- [x] [10/07-observability-status-and-observatory.md](10/07-observability-status-and-observatory.md) — `current` — Observability、Status 与 Observatory：观测事实，不接管业务事实 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/223)
- [x] [10/08-architecture-and-security-guards.md](10/08-architecture-and-security-guards.md) — `current` — Architecture 与 Security Guards：把边界写成可失败的规则 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/224)

### `11` 场景教程与 Cookbook（5）

- [x] [11/01-run-a-simple-workflow.md](11/01-run-a-simple-workflow.md) — `current` — 运行最小 Workflow：先证明定义，再观察一次运行 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/225)
- [x] [11/02-build-a-branching-tool-workflow.md](11/02-build-a-branching-tool-workflow.md) — `current` — 编写分支 Tool Workflow：把结果、路由与副作用分开 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/226)
- [x] [11/03-create-bind-and-invoke-a-team-member.md](11/03-create-bind-and-invoke-a-team-member.md) — `current` — 创建、绑定并调用 Team Member：沿响应句柄逐层观察 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/227)
- [x] [11/04-connect-a-channel-and-handle-files.md](11/04-connect-a-channel-and-handle-files.md) — `current` — 连接 Channel 并处理文件：注册、入站、Artifact 与 Delivery 分层验证 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/228)
- [x] [11/05-create-verify-and-troubleshoot-automation.md](11/05-create-verify-and-troubleshoot-automation.md) — `current` — 创建、验证与排障 Automation：不要把 `202` 当成已经执行 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/229)

### `12` 架构演进、案例与开放缺口（5）

- [x] [12/01-evolution-method-and-timeline.md](12/01-evolution-method-and-timeline.md) — `historical` — 演进方法与时间线：先分清三套时钟，再解释“为什么变成现在这样” — [issue](https://github.com/eanzhao-os/aevatar-review/issues/230)
- [x] [12/02-issue-decisions-by-theme.md](12/02-issue-decisions-by-theme.md) — `mixed` — Issue 决策主题图：把 280 个工作项还原成边界迁移 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/231)
- [x] [12/03-retired-and-superseded-components.md](12/03-retired-and-superseded-components.md) — `historical` — 已退役与被替代组件：删除什么、由谁接管、留下什么约束 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/232)
- [x] [12/04-incident-case-studies.md](12/04-incident-case-studies.md) — `mixed` — 事故案例：症状相似时，先找到真正拥有事实的边界 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/233)
- [x] [12/05-open-gaps-and-canon-drift.md](12/05-open-gaps-and-canon-drift.md) — `target` — 开放缺口与 Canon Drift：只登记当前限制，不预支未来能力 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/234)

### `13` 术语与事实源索引（4）

- [x] [13/01-glossary.md](13/01-glossary.md) — `current` — 术语表：先找事实 owner，再区分名字相近的协议角色 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/235)
- [x] [13/02-canon-and-adr-index.md](13/02-canon-and-adr-index.md) — `mixed` — Canon 与 ADR 索引：状态原样保留，current 结论仍回到冻结 E1 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/236)
- [x] [13/03-chapter-source-matrix.md](13/03-chapter-source-matrix.md) — `current` — 章节—事实源矩阵：72 个阅读入口怎样回到冻结证据 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/237)
- [x] [13/04-issue-evolution-index.md](13/04-issue-evolution-index.md) — `mixed` — Issue 演进索引：280 个冻结成员，一个都不靠状态猜实现 — [issue](https://github.com/eanzhao-os/aevatar-review/issues/238)

## 完成定义

- 72 篇实质章节与 14 个 block index 同时存在，路径与 `mkdocs.yml` 一致。
- 每篇 current/mixed 章节的事实源在冻结 SHA 中可解析；历史和目标态不冒充 current。
- 154 个 frozen-closed 与 126 个 frozen-open issue 无损分类并可反向查证。
- 结构、链接、漂移、Mermaid 与 MkDocs 全量门禁通过。
- 85 个旧路径只在迁移证据完成后删除，不保留“已迁移”空壳。
