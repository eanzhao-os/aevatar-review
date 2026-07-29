# 旧章节迁移账本（2026-07-25）
> 上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`
>
> 本账本覆盖执行基线 `da089e1` 上**全部** 98 个旧 Markdown 文件：85 个进入退役清单 `docs/migration/2026-07-25-old-retire-paths.txt`，13 个块级 `index.md` 由 Task 19 原位改写。

## 处置状态

| 处置 | 含义 |
|---|---|
| `retain-rewrite` | 主题边界仍正确，在新目录重写并重新核验 |
| `merge` | 多篇围绕同一状态所有者或协议链路，合成一篇 |
| `split` | 一篇同时解释多个独立资源或协议，拆成边界清楚的多篇 |
| `promote-current` | 原方案或故障修复已成为正式设计，去掉方案口吻 |
| `move-evolution` | 有长期价值但不是当前使用路径，迁入 `12` |
| `delete` | 已失效、重复且无独立教训，由 Git 历史归档 |
| `rewrite-in-place` | 块级索引，Task 19 原位改写，不进入退役清单 |

`status` 列取值：`pending` → `migrated` → `migrated-reviewed`。Task 19 结构切换前，退役清单里的每一行都必须是 `migrated-reviewed`。

`owner` 列的 `protected` 表示该文件是受保护迁移输入，见 `docs/migration/2026-07-25-protected-worktree.md`。

## 逐文件处置

| 旧路径 | owner | 处置 | 新落点 | status | 说明 |
|---|---|---|---|---|---|
| `00/01-what-is-aevatar.md` | tracked | merge | `00/01`、`00/02` | migrated | 定位与对比重写为阅读路线与证据等级，不再作为独立「是什么」章 |
| `00/02-repo-map.md` | tracked | retain-rewrite | `00/03` | migrated | 项目数量必须从冻结基线重新生成，不沿用旧计数 |
| `00/03-quick-start.md` | tracked | retain-rewrite | `01/01` | migrated | 上手路径迁入启动目录，端口与字段按冻结 Host 配置重新核验 |
| `00/04-chat-request-lifecycle.md` | tracked | split | `01/03`、`01/04` | migrated | 会话身份契约与流式生命周期拆成两章，避免 conversation/turn/run 混用 |
| `00/index.md` | tracked | rewrite-in-place | `00/index.md` | n/a | Task 19 原位改写为块导读，不进入退役清单 |
| `01/01-hosts-and-composition.md` | tracked | retain-rewrite | `01/02` | migrated | Host 只承担协议与组装，业务编排不下沉到 Host |
| `01/02-chat-api-and-sse.md` | tracked | split | `01/03`、`01/04` | migrated | API 契约与 SSE/AGUI 帧分层，dispatch receipt 与终态观察分开 |
| `01/03-run-semantics.md` | tracked | merge | `01/04`、`12/05` | migrated | 已落地流式生命周期进入`01/04`；未落地reconnect cursor/retention/gap contract已在`12/05`登记owner与exit criterion |
| `01/04-platform-audit-trail.md` | tracked | promote-current | `05/06` | migrated-reviewed | Audit 生命周期、三采集面、追加语义、查询 coverage 与 CloudEvents 导出已提升为正式读侧章节 |
| `01/index.md` | tracked | rewrite-in-place | `01/index.md` | n/a | Task 19 原位改写 |
| `02/01-yaml-grammar.md` | tracked | retain-rewrite | `03/02` | migrated-reviewed | 以冻结 parser/validator 为准重述 schema 与准入阶段 |
| `02/02-definition-and-run-actors.md` | tracked | retain-rewrite | `03/01` | migrated-reviewed | definition/run/draft/published 身份必须显式区分 |
| `02/03-execution-kernel.md` | tracked | retain-rewrite | `03/03` | migrated-reviewed | 补齐终态收敛与 typed tool error |
| `02/04-step-modules-catalog.md` | tracked | retain-rewrite | `03/04` | migrated-reviewed | primitive 清单以 catalog 为权威，冻结 SHA 计数，不写「30+」永恒口径 |
| `02/05-workflows-walkthrough.md` | tracked | split | `11/01`、`11/02` | migrated-reviewed | 已拆为最小运行与分支Tool Workflow两篇verified-static教程，并复核definition/admission/run与副作用边界 |
| `02/06-maker-plugin.md` | tracked | move-evolution | `12/03` | migrated | 独立Maker capability/Host已退役，current能力是Workflow extension module pack；替代边界与教训已迁入`12/03` |
| `02/07-connectors.md` | tracked | retain-rewrite | `03/07` | migrated-reviewed | 补 capability admission 与 bind/startup 准入，不写查询期刷新 |
| `02/08-saga-durable-execution.md` | tracked | split | `03/05`、`03/06` | migrated-reviewed | 挂起/信号/审批与补偿恢复分离；ADR 状态漂移与代码事实分开 |
| `02/index.md` | tracked | rewrite-in-place | `02/index.md` | n/a | Task 19 原位改写 |
| `03/01-agent-actor-runtime.md` | tracked | retain-rewrite | `02/01` | migrated-reviewed | Agent/Actor/Runtime/Stream 四层边界 |
| `03/02-event-envelope-vs-state-event.md` | tracked | split | `02/02`、`02/04` | migrated-reviewed | 消息语义与状态事实分成两章，杜绝 envelope 冒充事实源 |
| `03/03-gagent-base.md` | tracked | retain-rewrite | `02/03` | migrated-reviewed | handler/优先级/hook/turn 边界 |
| `03/04-state-guard-and-event-sourcing.md` | tracked | retain-rewrite | `02/04`、`12/05` | migrated | event-first、StateGuard与OCC主链已迁入`02/04`；RunManager/latest-wins现役声明缺类型的canon drift已迁入`12/05` |
| `03/05-routing-and-topology.md` | tracked | retain-rewrite | `02/05` | migrated-reviewed | publish 即投递到 inbox，无 inline self 捷径 |
| `03/06-local-runtime-deep-dive.md` | tracked | retain-rewrite | `02/06` | migrated-reviewed | 本地 runtime 局限与向 Orleans 迁移不改业务协议 |
| `03/07-stream-actor-gagent-facts.md` | tracked | merge | `02/01`、`02/05` | migrated-reviewed | 辨析并入运行内核与路由章，不单列「事实澄清」章 |
| `03/08-event-sourcing-dividends.md` | tracked | merge | `02/04`、`05/01`、`05/02` | migrated-reviewed | Actor 侧收益与 CQRS committed/read-side 边界均已迁移并复核 |
| `03/index.md` | tracked | rewrite-in-place | `03/index.md` | n/a | Task 19 原位改写 |
| `04/01-role-gagent.md` | tracked | retain-rewrite | `04/01` | migrated-reviewed | ChatStreamAsync 唯一面向用户路径；off-turn 执行折叠为 actor 信号 |
| `04/02-llm-providers.md` | tracked | retain-rewrite | `04/02` | migrated-reviewed | NyxID 是 adapter，不是通用后端 |
| `04/03-tool-providers.md` | tracked | split | `04/03`、`04/04` | migrated-reviewed | 工具目录/呈现与审批/授权拆开 |
| `04/04-chat-runtime-and-middleware.md` | tracked | split | `04/01`、`04/04`、`07/04` | migrated | AI runtime 与审批边界已迁入 `04`；conversation turn authority 待 `07/04` 完成后复核 |
| `04/index.md` | tracked | rewrite-in-place | `04/index.md` | n/a | Task 19 原位改写 |
| `05/01-projection-overview.md` | tracked | split | `05/01`、`05/02` | migrated-reviewed | 写侧事实、committed observation、durable read side 与 session observation 已分层复核 |
| `05/02-two-projection-modes.md` | tracked | retain-rewrite | `05/03` | migrated-reviewed | 生命周期、actor-owned scope、lease 与 exact subscription handle 已复核 |
| `05/03-readmodel-providers.md` | tracked | retain-rewrite | `05/04` | migrated-reviewed | StateVersion 权威、幂等覆盖、索引生命周期与有限 DR repair 已复核 |
| `05/04-workflow-projection.md` | tracked | retain-rewrite | `05/05` | migrated-reviewed | current-state、artifact、session event 与 Workflow/AGUI 方言边界已复核 |
| `05/index.md` | tracked | rewrite-in-place | `05/index.md` | n/a | Task 19 原位改写 |
| `06/01-current-vs-target.md` | tracked | retain-rewrite | `10/01` | migrated-reviewed | 已删除无代码支撑的「当前 vs 目标」表，按冻结基线重写拓扑、配置档位与故障边界并复核 |
| `06/02-orleans-runtime.md` | tracked | retain-rewrite | `10/02` | migrated-reviewed | 单一激活、grain inbox turn、持久恢复与 runtime-neutral dispatch 已迁移并复核 |
| `06/03-kafka-transport.md` | tracked | retain-rewrite | `10/04`、`12/03` | migrated | 当前KafkaProvider语义已迁入`10/04`；MassTransit runtime退役、历史删除与未清residue已迁入`12/03` |
| `06/04-garnet-clustering.md` | tracked | retain-rewrite | `10/03` | migrated-reviewed | Garnet 共享后端下的 EventStore、SecretVault、membership 与 state 职责已分层迁移并复核 |
| `06/05-architecture-guards.md` | tracked | retain-rewrite | `10/08` | migrated-reviewed | 56 个顶层 guard 已按治理不变量重写，并明确其不是完整正确性证明 |
| `06/06-credentials-zero-standing-secrets.md` | tracked | split | `09/03`、`09/04`、`10/05` | migrated-reviewed | 调度 Agent Key、Vault locator/双轨撤销与通用认证授权均已迁移并复核 |
| `06/index.md` | tracked | rewrite-in-place | `06/index.md` | n/a | Task 19 原位改写 |
| `07/01-channels.md` | tracked | retain-rewrite | `08/02` | migrated-reviewed | bot registration/conversation事实owner与raw credential边界已迁入并复核 |
| `07/02-a2a-interop.md` | tracked | move-evolution | `12/03` | migrated | A2A runtime删除事实、Host-boundary替代原则与不再提供恢复教程的边界已迁入`12/03` |
| `07/03-chat-routing.md` | tracked | retain-rewrite | `08/01` | migrated-reviewed | 入站规范化、owner scope与route policy边界已迁入并复核 |
| `07/04-voice-presence.md` | tracked | retain-rewrite | `08/05` | migrated-reviewed | actor control/realtime observation/volatile PCM与lease fencing已迁入并复核 |
| `07/05-studio-and-scripting.md` | tracked | split | `06/01`、`06/04` | migrated-reviewed | Team/Member资源模型、identity边界与命令/ACK/读模型已拆分迁移并复核 |
| `07/06-console-web.md` | tracked | merge | `06/03`、`06/04`、`10/07` | migrated-reviewed | catalog/授权、Studio命令/readmodel与只读Observatory查询面均已迁移并复核 |
| `07/07-observability.md` | tracked | retain-rewrite | `10/07` | migrated-reviewed | OTel实时信号、Status probe事实、权威读模型与Observatory边界已分层迁移并复核 |
| `07/08-lark-end-to-end.md` | tracked | split | `08/03`、`11/04` | migrated-reviewed | Lark adapter/delivery/repair与registration→relay→conversation→delivery教程已迁移并复核 |
| `07/09-voice-presence-edge-brain.md` | tracked | merge | `08/05`、`12/05` | migrated | 当前control/media/credential/restart边界已迁入`08/05`；zero-config、resume与transcript owner/exit criterion已迁入`12/05` |
| `07/10-input-ingress-unification.md` | tracked | retain-rewrite | `08/01` | migrated-reviewed | 统一入站骨干、canonical identity与执行意图分层已迁入并复核 |
| `07/11-file-handling-end-to-end.md` | tracked | retain-rewrite | `08/04` | migrated-reviewed | durable ref、bytes窄边界、ownership与cleanup已迁入并复核；旧章stale reference属已接受迁移红态 |
| `07/12-scheduled-tasks.md` | protected | promote-current+split | `09/01`、`09/02`、`09/03`、`09/04`、`12/04` | migrated | canonical资源、callback、Agent Key与Vault生命周期已迁入`09/01–04`；fire-time凭证、callback与canary证据边界已逐节迁入`12/04` |
| `07/13-lark-bot-registration.md` | tracked | merge | `08/03`、`11/04` | migrated-reviewed | registration/repair事实与webhook、callback、status分层教程已迁移并复核 |
| `07/index.md` | protected | rewrite-in-place | `07/index.md`、`08/index.md`、`09/index.md` | n/a | 受保护索引；Task 19 原位改写并把导航拆到三个新块 |
| `08/01-glossary.md` | tracked | retain-rewrite | `13/01-glossary.md` | migrated-reviewed | 42 个唯一术语已迁入，必需词、owner/boundary、章节落点与易混对象均已复核 |
| `08/02-doc-index.md` | tracked | retain-rewrite | `13/02-canon-and-adr-index.md` | migrated-reviewed | 冻结快照的 39 篇 canon + 43 篇 ADR 已完整重建索引，raw status、导读、落点与 drift/lifecycle 标记均已复核 |
| `08/03-demo-cookbook.md` | tracked | split | `11/01`、`11/02`、`11/03`、`11/04`、`11/05` | migrated-reviewed | cookbook已拆成五篇verified-static教程，统一区分receipt、projected state、run/fire与外部副作用证据 |
| `08/04-todo-list.md` | tracked | move-evolution | `12/05` | migrated | 旧TODO已重审为带owner、current limit、evidence与exit criterion的开放缺口/canon drift登记 |
| `08/05-crystallization-roadmap.md` | tracked | move-evolution | `12/01`、`12/05` | migrated | 路线口吻已拆为`12/01`的历史方法与`12/05`的target缺口，不再伪装current能力 |
| `08/index.md` | tracked | rewrite-in-place | `08/index.md` | n/a | Task 19 原位改写 |
| `09/01-workflow-as-nyxid-service/01-mechanisms.md` | tracked | promote-current | `06/02`、`03/07` | migrated-reviewed | draft/revision/member/binding/service身份与准入机制已迁入当前模型并复核 |
| `09/01-workflow-as-nyxid-service/02-publish-path.md` | tracked | promote-current | `06/02`、`11/03` | migrated-reviewed | 发布身份、binding链与authority-returned service/revision观察教程均已迁移并复核 |
| `09/01-workflow-as-nyxid-service/03-register-and-discover.md` | tracked | split | `06/03`、`12/05` | migrated | catalog可见性与scope授权已迁入`06/03`；未落地NyxID registration/headless binding合同已作为target迁入`12/05` |
| `09/01-workflow-as-nyxid-service/04-calling.md` | tracked | promote-current | `11/03` | migrated-reviewed | member-first调用已迁入教程并区分invoke 202、statusUrl与terminal run |
| `09/01-workflow-as-nyxid-service/05-end-to-end-plan.md` | tracked | merge | `11/03`、`12/05` | migrated | 已落地create/bind/invoke观察进入`11/03`；未落地registration/version/access-review切片进入`12/05` |
| `09/01-workflow-as-nyxid-service/06-auto-registration-plan.md` | tracked | move-evolution | `12/05` | migrated | 自动注册未落地事实已降级为`12/05` target registry，不再保留执行计划口吻 |
| `09/01-workflow-as-nyxid-service/07-auto-registration-adr.md` | tracked | move-evolution | `12/05` | migrated | Proposed identity/registration治理状态与局部E1差异已迁入`12/05`，没有晋级current |
| `09/01-workflow-as-nyxid-service/index.md` | tracked | delete | `06/index.md`、`12/index.md` | pending | 方案区嵌套索引取消，导航由新块索引承担 |
| `09/02-ingress-tool-ownership/01-leak-and-asymmetric-rule.md` | tracked | promote-current | `04/03`、`04/04` | migrated-reviewed | 工具归属规则转当前设计 |
| `09/02-ingress-tool-ownership/02-fix-and-rollout.md` | tracked | split | `04/04`、`12/04` | migrated | current审批/授权与tool ownership修复进入`04/04`；symptom→root boundary→fix→remaining limit进入`12/04` |
| `09/02-ingress-tool-ownership/index.md` | tracked | delete | `04/index.md`、`12/index.md` | pending | 方案区嵌套索引取消 |
| `09/03-provision-and-observe-via-nyxid/01-end-to-end.md` | tracked | split | `09/05`、`11/03`、`11/05` | migrated-reviewed | 版本化生产证据、Member调用与automation preflight/create/run-or-cron/revocation恢复均已迁移并复核 |
| `09/03-provision-and-observe-via-nyxid/02-scheduled-agent-key-production-canary.md` | protected | promote-current+split | `09/05`、`12/04` | migrated | 四次证据的commit/image/date/environment、`last_used_at`、6201/6202、provenance、cleanup与第四次前置失败已逐节迁入`09/05`和`12/04` |
| `09/03-provision-and-observe-via-nyxid/index.md` | protected | delete | `09/index.md`、`12/index.md` | migrated | 内容意图与生产证据导读已进入`09/05`；块级导航仍待Task 19原子切换 |
| `09/index.md` | tracked | rewrite-in-place | `09/index.md` | n/a | Task 19 原位改写为 Automation 与调度块导读 |
| `10/01-cli-lark-scope-isolation.md` | tracked | split | `06/03`、`12/04` | migrated | scope catalog/Workflow授权进入`06/03`；真实泄漏与合法隔离不可混同的事故边界进入`12/04` |
| `10/02-codex-shell-vs-aevatar-tools.md` | tracked | split | `04/03`、`10/06`、`12/04` | migrated | 工具归属与managed sandbox/delegation进入`04/03`、`10/06`；server/client tool事故与余限进入`12/04` |
| `10/03-ingress-own-tool-stream-leak.md` | tracked | split | `04/03`、`08/01`、`12/04` | migrated | tool ownership与ingress/route边界进入`04/03`、`08/01`；分类前泄漏根因与修复进入`12/04` |
| `10/04-responses-llm-run-offactor-and-observation.md` | tracked | split | `04/01`、`05/02`、`12/04` | migrated | off-actor AI执行与committed/session observation进入`04/01`、`05/02`；跨边界推断教训进入`12/04` |
| `10/05-lark-delivery-layer-failures.md` | tracked | split | `08/03`、`12/04` | migrated | delivery语义、current drift与原位repair进入`08/03`；generation/delivery分层事故进入`12/04` |
| `10/06-lark-identity-and-authorization.md` | tracked | split | `08/02`、`10/05`、`12/04` | migrated | Channel credential/current durable边界与通用auth进入`08/02`、`10/05`；身份授权事故进入`12/04` |
| `10/07-scheduled-task-not-firing.md` | tracked | split | `09/02`、`12/04` | migrated | callback/lease/stale拒绝与one-shot grain-context修复进入`09/02`；四类不同根因已在`12/04`逐类复盘 |
| `10/08-observatory-read-side.md` | tracked | split | `05/04`、`10/07`、`12/04` | migrated | 索引versioning、显式repair与只读Observatory进入`05/04`、`10/07`；projection/index drift事故进入`12/04` |
| `10/09-studio-console-three-traps.md` | tracked | split | `06/04`、`07/01`、`12/04` | migrated | 命令/ACK/readmodel与conversation/turn/history进入`06/04`、`07/01`；UI假成功事故边界进入`12/04` |
| `10/10-voice-cancel-race-and-reconnect.md` | tracked | split | `08/05`、`12/04`、`12/05` | migrated | cancel/drain/restart进入`08/05`；竞态事故进入`12/04`，真正resume/current-state缺口进入`12/05` |
| `10/11-nyxid-direct-llm-entry.md` | tracked | split | `04/02`、`07/02`、`12/04` | migrated | LLM provider/route与NyxIdChat actor/progress进入`04/02`、`07/02`；外部故障证据边界进入`12/04` |
| `10/12-api-security-audit-and-hardening.md` | tracked | split | `10/05`、`10/08`、`12/05` | migrated | 已落地认证授权与security guards进入`10/05`、`10/08`；未闭合security debt/contract进入`12/05` |
| `10/index.md` | protected | rewrite-in-place | `10/index.md`、`12/index.md` | n/a | 受保护索引；Task 19 原位改写 |
| `11/01-aevatar-control-plane-skills.md` | tracked | merge | `04/03`、`11/03`、`12/03` | migrated | current tool catalog与Team Member教程进入`04/03`、`11/03`；旧SkillRunner/Maker等退役边界进入`12/03` |
| `11/02-aevatar-platform-and-probe-skills.md` | tracked | merge | `04/05`、`11/05`、`12/03` | migrated | prompt/skill overlay与automation排障证据梯度进入`04/05`、`11/05`；旧runtime/探针不再作为current入口并入`12/03` |
| `11/index.md` | tracked | rewrite-in-place | `11/index.md` | n/a | Task 19 原位改写为教程块导读 |
| `12/01-2026-06-22-to-06-26.md` | tracked | merge | `12/01`、`12/02`、`12/04` | migrated | 周报已拆为三套时钟/主题决策/事故边界；日期与issue仍可追溯，但不再把周次当功能完成状态 |
| `12/index.md` | tracked | rewrite-in-place | `12/index.md` | n/a | Task 19 原位改写为演进块导读 |
