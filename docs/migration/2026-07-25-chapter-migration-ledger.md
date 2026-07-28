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
| `01/03-run-semantics.md` | tracked | merge | `01/04`、`12/05` | migrated | 已落地语义并入生命周期章；未落地 reconnect 保证只进 12/05 |
| `01/04-platform-audit-trail.md` | tracked | promote-current | `05/06` | migrated-reviewed | Audit 生命周期、三采集面、追加语义、查询 coverage 与 CloudEvents 导出已提升为正式读侧章节 |
| `01/index.md` | tracked | rewrite-in-place | `01/index.md` | n/a | Task 19 原位改写 |
| `02/01-yaml-grammar.md` | tracked | retain-rewrite | `03/02` | migrated-reviewed | 以冻结 parser/validator 为准重述 schema 与准入阶段 |
| `02/02-definition-and-run-actors.md` | tracked | retain-rewrite | `03/01` | migrated-reviewed | definition/run/draft/published 身份必须显式区分 |
| `02/03-execution-kernel.md` | tracked | retain-rewrite | `03/03` | migrated-reviewed | 补齐终态收敛与 typed tool error |
| `02/04-step-modules-catalog.md` | tracked | retain-rewrite | `03/04` | migrated-reviewed | primitive 清单以 catalog 为权威，冻结 SHA 计数，不写「30+」永恒口径 |
| `02/05-workflows-walkthrough.md` | tracked | split | `11/01`、`11/02` | pending | 走读改为两篇可复现教程；旧章现存 stale reference 属已接受迁移红态 |
| `02/06-maker-plugin.md` | tracked | move-evolution | `12/03` | pending | Maker 若非当前路径则只保留历史与教训 |
| `02/07-connectors.md` | tracked | retain-rewrite | `03/07` | migrated-reviewed | 补 capability admission 与 bind/startup 准入，不写查询期刷新 |
| `02/08-saga-durable-execution.md` | tracked | split | `03/05`、`03/06` | migrated-reviewed | 挂起/信号/审批与补偿恢复分离；ADR 状态漂移与代码事实分开 |
| `02/index.md` | tracked | rewrite-in-place | `02/index.md` | n/a | Task 19 原位改写 |
| `03/01-agent-actor-runtime.md` | tracked | retain-rewrite | `02/01` | migrated-reviewed | Agent/Actor/Runtime/Stream 四层边界 |
| `03/02-event-envelope-vs-state-event.md` | tracked | split | `02/02`、`02/04` | migrated-reviewed | 消息语义与状态事实分成两章，杜绝 envelope 冒充事实源 |
| `03/03-gagent-base.md` | tracked | retain-rewrite | `02/03` | migrated-reviewed | handler/优先级/hook/turn 边界 |
| `03/04-state-guard-and-event-sourcing.md` | tracked | retain-rewrite | `02/04`、`12/05` | migrated | 主链已迁入 `02/04`；RunManager/latest-wins canon drift 已在旧 `08/04` 登记，待 Task 17 迁入 `12/05` 后复核 |
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
| `06/01-current-vs-target.md` | tracked | retain-rewrite | `10/01` | pending | 删除无代码支撑的「当前 vs 目标」表，改为冻结基线拓扑与配置 |
| `06/02-orleans-runtime.md` | tracked | retain-rewrite | `10/02` | pending | 单一激活、grain inbox turn 语义与 runtime-neutral dispatch |
| `06/03-kafka-transport.md` | tracked | retain-rewrite | `10/04`、`12/03` | pending | 当前 KafkaProvider 为准；MassTransit 明确历史 |
| `06/04-garnet-clustering.md` | tracked | retain-rewrite | `10/03` | pending | EventStore 与 SecretVault 职责必须分开 |
| `06/05-architecture-guards.md` | tracked | retain-rewrite | `10/08` | pending | 门禁是可执行治理，不是正确性证明 |
| `06/06-credentials-zero-standing-secrets.md` | tracked | split | `09/03`、`09/04`、`10/05` | pending | 调度专用 Agent Key 与通用认证授权分层 |
| `06/index.md` | tracked | rewrite-in-place | `06/index.md` | n/a | Task 19 原位改写 |
| `07/01-channels.md` | tracked | retain-rewrite | `08/02` | migrated-reviewed | bot registration/conversation事实owner与raw credential边界已迁入并复核 |
| `07/02-a2a-interop.md` | tracked | move-evolution | `12/03` | pending | A2A 已退役，只保留架构教训，不与现役能力等权展示 |
| `07/03-chat-routing.md` | tracked | retain-rewrite | `08/01` | migrated-reviewed | 入站规范化、owner scope与route policy边界已迁入并复核 |
| `07/04-voice-presence.md` | tracked | retain-rewrite | `08/05` | migrated-reviewed | actor control/realtime observation/volatile PCM与lease fencing已迁入并复核 |
| `07/05-studio-and-scripting.md` | tracked | split | `06/01`、`06/04` | migrated-reviewed | Team/Member资源模型、identity边界与命令/ACK/读模型已拆分迁移并复核 |
| `07/06-console-web.md` | tracked | merge | `06/03`、`06/04`、`10/07` | migrated | catalog/授权与Studio命令/readmodel已迁入`06`；Console观测面待`10/07`完成 |
| `07/07-observability.md` | tracked | retain-rewrite | `10/07` | pending | OTel 实时信号 vs 权威读模型 |
| `07/08-lark-end-to-end.md` | tracked | split | `08/03`、`11/04` | migrated | Lark adapter/delivery/repair边界已迁入`08/03`；可复现教程待`11/04` |
| `07/09-voice-presence-edge-brain.md` | tracked | merge | `08/05`、`12/05` | migrated | 当前control/media/credential/restart边界已迁入`08/05`；剩余zero-config、resume与transcript缺口待`12/05` |
| `07/10-input-ingress-unification.md` | tracked | retain-rewrite | `08/01` | migrated-reviewed | 统一入站骨干、canonical identity与执行意图分层已迁入并复核 |
| `07/11-file-handling-end-to-end.md` | tracked | retain-rewrite | `08/04` | migrated-reviewed | durable ref、bytes窄边界、ownership与cleanup已迁入并复核；旧章stale reference属已接受迁移红态 |
| `07/12-scheduled-tasks.md` | protected | promote-current+split | `09/01`、`09/02`、`09/03`、`09/04`、`12/04` | pending | Agent Key 当前模型与 fire-time 换票历史必须分开 |
| `07/13-lark-bot-registration.md` | tracked | merge | `08/03`、`11/04` | migrated | registration/repair事实已迁入`08/03`；操作教程待`11/04` |
| `07/index.md` | protected | rewrite-in-place | `07/index.md`、`08/index.md`、`09/index.md` | n/a | 受保护索引；Task 19 原位改写并把导航拆到三个新块 |
| `08/01-glossary.md` | tracked | retain-rewrite | `13/01` | pending | 术语表补齐易混对，每词一个定义 |
| `08/02-doc-index.md` | tracked | retain-rewrite | `13/02` | pending | canon/ADR 索引从冻结快照重新生成，状态从正文解析 |
| `08/03-demo-cookbook.md` | tracked | split | `11/01`、`11/02`、`11/03`、`11/04`、`11/05` | pending | cookbook 拆成五篇诚实标注的教程 |
| `08/04-todo-list.md` | tracked | move-evolution | `12/05` | pending | TODO 变成带 owner/exit criterion 的开放缺口登记 |
| `08/05-crystallization-roadmap.md` | tracked | move-evolution | `12/01`、`12/05` | pending | 路线图不得写成当前能力 |
| `08/index.md` | tracked | rewrite-in-place | `08/index.md` | n/a | Task 19 原位改写 |
| `09/01-workflow-as-nyxid-service/01-mechanisms.md` | tracked | promote-current | `06/02`、`03/07` | migrated-reviewed | draft/revision/member/binding/service身份与准入机制已迁入当前模型并复核 |
| `09/01-workflow-as-nyxid-service/02-publish-path.md` | tracked | promote-current | `06/02`、`11/03` | migrated | 发布身份与binding链已迁入`06/02`；端到端教程待`11/03` |
| `09/01-workflow-as-nyxid-service/03-register-and-discover.md` | tracked | split | `06/03`、`12/05` | migrated | catalog可见性与scope授权已迁入`06/03`；未落地注册语义待`12/05` |
| `09/01-workflow-as-nyxid-service/04-calling.md` | tracked | promote-current | `11/03` | pending | 调用路径进入教程，区分 202 与观察到的完成 |
| `09/01-workflow-as-nyxid-service/05-end-to-end-plan.md` | tracked | merge | `11/03`、`12/05` | pending | 计划口吻去掉；未落地部分留 12/05 |
| `09/01-workflow-as-nyxid-service/06-auto-registration-plan.md` | tracked | move-evolution | `12/05` | pending | 自动注册未落地，只能是 target |
| `09/01-workflow-as-nyxid-service/07-auto-registration-adr.md` | tracked | move-evolution | `12/05` | pending | Proposed ADR 不进 current 正文 |
| `09/01-workflow-as-nyxid-service/index.md` | tracked | delete | `06/index.md`、`12/index.md` | pending | 方案区嵌套索引取消，导航由新块索引承担 |
| `09/02-ingress-tool-ownership/01-leak-and-asymmetric-rule.md` | tracked | promote-current | `04/03`、`04/04` | migrated-reviewed | 工具归属规则转当前设计 |
| `09/02-ingress-tool-ownership/02-fix-and-rollout.md` | tracked | split | `04/04`、`12/04` | migrated | 修复语义已迁入 `04/04`；事故过程待 `12/04` 完成后复核 |
| `09/02-ingress-tool-ownership/index.md` | tracked | delete | `04/index.md`、`12/index.md` | pending | 方案区嵌套索引取消 |
| `09/03-provision-and-observe-via-nyxid/01-end-to-end.md` | tracked | split | `09/05`、`11/03`、`11/05` | pending | 端到端过程拆成生产证据与两篇教程 |
| `09/03-provision-and-observe-via-nyxid/02-scheduled-agent-key-production-canary.md` | protected | promote-current+split | `09/05`、`12/04` | pending | 受保护生产证据：commit/镜像/日期/环境绑定，严格 canary 与功能性重跑强度不同，不得混同 |
| `09/03-provision-and-observe-via-nyxid/index.md` | protected | delete | `09/index.md`、`12/index.md` | pending | 受保护嵌套索引；内容意图迁入新块索引与 09/05 |
| `09/index.md` | tracked | rewrite-in-place | `09/index.md` | n/a | Task 19 原位改写为 Automation 与调度块导读 |
| `10/01-cli-lark-scope-isolation.md` | tracked | split | `06/03`、`12/04` | migrated | scope catalog/Workflow授权边界已迁入`06/03`；事故叙事待`12/04` |
| `10/02-codex-shell-vs-aevatar-tools.md` | tracked | split | `04/03`、`10/06`、`12/04` | migrated | 工具归属已迁入 `04/03`；sandbox 与事故落点待后续章节完成；旧章 stale reference 属已接受迁移红态 |
| `10/03-ingress-own-tool-stream-leak.md` | tracked | split | `04/03`、`08/01`、`12/04` | migrated | tool ownership与ingress/route边界已迁入`04/03`、`08/01`；事故落点待`12/04` |
| `10/04-responses-llm-run-offactor-and-observation.md` | tracked | split | `04/01`、`05/02`、`12/04` | migrated | off-actor AI 执行与 committed/session observation 边界已迁入 `04/01`、`05/02`；事故落点待 `12/04` |
| `10/05-lark-delivery-layer-failures.md` | tracked | split | `08/03`、`12/04` | migrated | delivery语义、当前drift与原位repair已迁入`08/03`；事故过程待`12/04` |
| `10/06-lark-identity-and-authorization.md` | tracked | split | `08/02`、`10/05`、`12/04` | migrated | Channel credential/current durable边界已迁入`08/02`；通用auth与事故落点待`10/05`、`12/04` |
| `10/07-scheduled-task-not-firing.md` | tracked | split | `09/02`、`12/04` | pending | callback 只唤醒 actor；stale callback 拒绝 |
| `10/08-observatory-read-side.md` | tracked | split | `05/04`、`10/07`、`12/04` | migrated | 索引漂移、versioning 与显式 repair 边界已迁入 `05/04`；观测运维与事故落点待后续章节 |
| `10/09-studio-console-three-traps.md` | tracked | split | `06/04`、`07/01`、`12/04` | migrated | 命令/ACK/读模型与identity resolution已迁入`06/04`，conversation/turn/history边界已迁入`07/01`；事故落点待`12/04` |
| `10/10-voice-cancel-race-and-reconnect.md` | tracked | split | `08/05`、`12/04`、`12/05` | migrated | cancel/drain/restart当前边界已迁入`08/05`；事故与真正resume缺口待`12/04–05` |
| `10/11-nyxid-direct-llm-entry.md` | tracked | split | `04/02`、`07/02`、`12/04` | migrated | LLM provider/route边界已迁入`04/02`，NyxIdChat actor/progress边界已迁入`07/02`；事故落点待`12/04` |
| `10/12-api-security-audit-and-hardening.md` | tracked | split | `10/05`、`10/08`、`12/05` | pending | 已落地加固转当前，未闭合项留 12/05；旧章 stale reference 属已接受迁移红态 |
| `10/index.md` | protected | rewrite-in-place | `10/index.md`、`12/index.md` | n/a | 受保护索引；Task 19 原位改写 |
| `11/01-aevatar-control-plane-skills.md` | tracked | merge | `04/03`、`11/03`、`12/03` | migrated | tool catalog 边界已迁入 `04/03`；教程与退役落点待后续章节完成 |
| `11/02-aevatar-platform-and-probe-skills.md` | tracked | merge | `04/05`、`11/05`、`12/03` | migrated | prompt/skill overlay 边界已迁入 `04/05`；排障教程与退役落点待后续章节完成 |
| `11/index.md` | tracked | rewrite-in-place | `11/index.md` | n/a | Task 19 原位改写为教程块导读 |
| `12/01-2026-06-22-to-06-26.md` | tracked | merge | `12/01`、`12/02`、`12/04` | pending | 按周复盘改为按主题聚合的决策记录 + 日期/issue 索引 |
| `12/index.md` | tracked | rewrite-in-place | `12/index.md` | n/a | Task 19 原位改写为演进块导读 |
