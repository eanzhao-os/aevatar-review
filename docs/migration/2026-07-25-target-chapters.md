# 目标章节清单（2026-07-25 冻结）

> 上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`
>
> 批准来源：`docs/superpowers/specs/2026-07-25-aevatar-review-restructure-design.md` §5
>
> 实施顺序与逐行 `status`：`docs/superpowers/plans/2026-07-25-aevatar-review-restructure.md` Tasks 5–18 主题表
>
> 本清单只列 72 篇**实质章节**。14 个 block `index.md` 由 Task 19 统一改写，不计入本清单。

## 行格式

```text
- [ ] `<block>/<NN>-<slug>.md` — status:<current|mixed|historical|target> — issue:<url>
```

- `- [ ]` → 章节尚未完成；`- [x]` → 章节已有独立提交且已通过独立 review。
- `status` 取值只允许 `current` / `mixed` / `historical` / `target`，与该章 frontmatter 必须一致。
- `issue` 在 Task 1 Step 9 之后必须是精确单路径 issue 的 URL；`pending` 只允许出现在远端 issue 创建之前。

## `00` 导读与基线（3）

- [x] `00/01-reading-guide.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/167
- [x] `00/02-version-evidence-and-status.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/168
- [x] `00/03-repository-map.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/169

## `01` 启动与请求（4）

- [ ] `01/01-quick-start.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/170
- [ ] `01/02-hosts-and-composition.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/171
- [ ] `01/03-chat-conversation-turn-contract.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/172
- [ ] `01/04-request-streaming-lifecycle.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/173

## `02` Actor 运行内核（6）

- [ ] `02/01-agent-actor-runtime.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/174
- [ ] `02/02-envelope-command-event-query.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/175
- [ ] `02/03-gagent-event-pipeline.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/176
- [ ] `02/04-state-event-sourcing-and-guard.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/177
- [ ] `02/05-dispatch-routing-and-topology.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/178
- [ ] `02/06-local-runtime-and-lifecycle.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/179

## `03` Workflow 编排（7）

- [ ] `03/01-workflow-model-and-identities.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/180
- [ ] `03/02-yaml-schema-and-validation.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/181
- [ ] `03/03-execution-kernel-and-outcomes.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/182
- [ ] `03/04-primitives-catalog.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/183
- [ ] `03/05-pause-signal-approval-and-resume.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/184
- [ ] `03/06-saga-compensation-and-recovery.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/185
- [ ] `03/07-connectors-and-capability-admission.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/186

## `04` AI 执行与工具（5）

- [ ] `04/01-role-agent-and-streaming-run.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/187
- [ ] `04/02-llm-providers-and-route-selection.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/188
- [ ] `04/03-tool-loop-catalog-and-presentation.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/189
- [ ] `04/04-tool-approval-and-authorization.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/190
- [ ] `04/05-prompt-overlays-and-agent-context.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/191

## `05` CQRS、Projection 与 Audit（6）

- [ ] `05/01-command-event-projection-readmodel.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/192
- [ ] `05/02-committed-state-and-observation.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/193
- [ ] `05/03-projection-lifecycle-and-leases.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/194
- [ ] `05/04-readmodel-stores-versioning-and-rebuild.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/195
- [ ] `05/05-workflow-agui-and-live-observation.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/196
- [ ] `05/06-audit-trail-lifecycle-and-export.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/197

## `06` 产品资源与身份（5）

- [ ] `06/01-scope-team-member-resource-model.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/198
- [ ] `06/02-draft-revision-binding-and-published-service.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/199
- [ ] `06/03-catalog-visibility-and-scope-authorization.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/200
- [ ] `06/04-studio-commands-acks-and-readmodels.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/201
- [ ] `06/05-work-orders-and-durable-intent.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/202

## `07` Conversation、NyxIdChat 与 Agent Profile（4）

- [ ] `07/01-conversation-turn-and-chat-history.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/203
- [ ] `07/02-nyxid-chat-actor-model-and-progress.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/204
- [ ] `07/03-agent-profile-and-immutable-binding.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/205
- [ ] `07/04-turn-authority-tool-catalog-and-retry.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/206

## `08` Ingress、Channel、文件与语音（5）

- [ ] `08/01-ingress-normalization-and-routing.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/207
- [ ] `08/02-channel-runtime-and-credential-boundary.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/208
- [ ] `08/03-lark-delivery-interaction-and-repair.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/209
- [ ] `08/04-file-artifacts-and-attachments.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/210
- [ ] `08/05-voice-control-and-media-planes.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/211

## `09` Automation、调度与凭证（5）

- [ ] `09/01-automation-resource-api-and-readmodels.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/212
- [ ] `09/02-scheduled-actor-callback-and-fire.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/213
- [ ] `09/03-owner-authorization-and-agent-key.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/214
- [ ] `09/04-vault-reference-and-revocation-compensation.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/215
- [ ] `09/05-production-canary-and-recovery.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/216

## `10` 分布式与生产运行（8）

- [ ] `10/01-production-topology-and-configuration.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/217
- [ ] `10/02-orleans-runtime.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/218
- [ ] `10/03-garnet-clustering-and-secret-storage.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/219
- [ ] `10/04-streaming-transport-and-kafka.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/220
- [ ] `10/05-authentication-scope-and-admin-authorization.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/221
- [ ] `10/06-managed-codex-sandbox-and-delegation.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/222
- [ ] `10/07-observability-status-and-observatory.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/223
- [ ] `10/08-architecture-and-security-guards.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/224

## `11` 场景教程与 Cookbook（5）

- [ ] `11/01-run-a-simple-workflow.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/225
- [ ] `11/02-build-a-branching-tool-workflow.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/226
- [ ] `11/03-create-bind-and-invoke-a-team-member.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/227
- [ ] `11/04-connect-a-channel-and-handle-files.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/228
- [ ] `11/05-create-verify-and-troubleshoot-automation.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/229

## `12` 架构演进、案例与开放缺口（5）

- [ ] `12/01-evolution-method-and-timeline.md` — status:historical — issue:https://github.com/eanzhao-os/aevatar-review/issues/230
- [ ] `12/02-issue-decisions-by-theme.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/231
- [ ] `12/03-retired-and-superseded-components.md` — status:historical — issue:https://github.com/eanzhao-os/aevatar-review/issues/232
- [ ] `12/04-incident-case-studies.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/233
- [ ] `12/05-open-gaps-and-canon-drift.md` — status:target — issue:https://github.com/eanzhao-os/aevatar-review/issues/234

## `13` 术语与事实源索引（4）

- [ ] `13/01-glossary.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/235
- [ ] `13/02-canon-and-adr-index.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/236
- [ ] `13/03-chapter-source-matrix.md` — status:current — issue:https://github.com/eanzhao-os/aevatar-review/issues/237
- [ ] `13/04-issue-evolution-index.md` — status:mixed — issue:https://github.com/eanzhao-os/aevatar-review/issues/238
