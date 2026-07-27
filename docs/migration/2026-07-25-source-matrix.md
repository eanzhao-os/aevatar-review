# 章节事实源矩阵（2026-07-25）

> 上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`
>
> 核验日期：`2026-07-25`
>
> 每行对应 `docs/migration/2026-07-25-target-chapters.md` 的一个目标章节。

## 证据等级

| 等级 | 证据 | 可支持的表述 |
|---|---|---|
| E1 | 冻结基线中的 code / proto / config / test | 当前实现具有该行为 |
| E2 | 与代码一致的 canon、Accepted ADR、架构门禁 | 这是被声明并治理的设计边界 |
| E3 | 带 commit / 镜像 / 日期 / 环境的生产运行证据 | 该版本在该环境中被实际验证 |
| E4 | closed issue，且能定位到已落地代码或合并提交 | 为什么演进成当前设计 |
| E5 | open issue、Proposed ADR、未合并方案 | 缺口、风险或目标态 |
| E6 | 已删除代码、历史 commit、被替代 ADR | 历史与设计教训 |

`current` / `mixed` 章节的每条 current 论断必须有 E1；E2/E4 只能补充设计约束与演进原因。
E1 列写入的是**已批准的脊柱候选**（来自计划主题表），实施时必须解析为冻结 SHA 上有效的
1–3 条路径 + 有效行号锚点，并把最终值写回本表。

`verified` 列取值：`pending` → `resolved`（脊柱路径与行号已在冻结 SHA 核验）。

## 矩阵

| 目标章节 | status | E1 脊柱候选（冻结 SHA 上解析为 1–3 条 + 行号） | E2 canon/ADR | E3 生产证据 | E4 closed issues | E5 open issues | E6 历史 | verified |
|---|---|---|---|---|---|---|---|---|
| `00/01-reading-guide.md` | current | `README.md`; `docs/canon/overview.md`; `docs/canon/architecture.md` | — | — | — | — | — | pending |
| `00/02-version-evidence-and-status.md` | current | `AGENTS.md`; `docs/canon/architecture.md`; `docs/adr/` status headers | — | — | — | — | — | pending |
| `00/03-repository-map.md` | current | `aevatar.slnx`; `docs/canon/module-placement-map.md`; `AGENTS.md` | — | — | — | — | — | pending |
| `01/01-quick-start.md` | current | `src/Aevatar.Mainnet.Host.Api/README.md`; `src/workflow/Aevatar.Workflow.Host.Api/README.md`; `workflows/simple_qa.yaml` | — | — | — | — | — | pending |
| `01/02-hosts-and-composition.md` | current | `src/Aevatar.Mainnet.Host.Api/Hosting/MainnetHostBuilderExtensions.cs`; `src/Aevatar.Mainnet.Host.Api/Program.cs`; `docs/canon/overview.md` | — | — | — | — | — | pending |
| `01/03-chat-conversation-turn-contract.md` | current | `docs/canon/chat-api.md`; `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/ChatEndpoints.cs`; `agents/Aevatar.GAgents.ChatHistory/chat_history_messages.proto` | — | — | — | — | — | pending |
| `01/04-request-streaming-lifecycle.md` | mixed | `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/ChatSseResponseWriter.cs`; `src/Aevatar.AGUI.Contracts/agui_events.proto`; `docs/canon/llm-streaming.md` | — | — | — | — | — | pending |
| `02/01-agent-actor-runtime.md` | current | `src/Aevatar.Foundation.Abstractions/README.md`; `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs`; `src/Aevatar.Foundation.Abstractions/runtime_actor_identity.proto` | — | — | — | — | — | pending |
| `02/02-envelope-command-event-query.md` | current | `src/Aevatar.Foundation.Abstractions/agent_messages.proto`; `src/Aevatar.Foundation.Abstractions/EnvelopeRouteSemantics.cs`; `AGENTS.md` | — | — | — | — | — | pending |
| `02/03-gagent-event-pipeline.md` | current | `src/Aevatar.Foundation.Core/GAgentBase.cs`; `src/Aevatar.Foundation.Abstractions/EventModules/IEventModule.cs`; `src/Aevatar.Foundation.Abstractions/Attributes/EventHandlerAttribute.cs` | — | — | — | — | — | pending |
| `02/04-state-event-sourcing-and-guard.md` | current | `src/Aevatar.Foundation.Core/StateGuard.cs`; `src/Aevatar.Foundation.Abstractions/Persistence/IEventStore.cs`; `src/Aevatar.Foundation.Core/GAgentBase.TState.cs` | — | — | — | — | — | pending |
| `02/05-dispatch-routing-and-topology.md` | current | `src/Aevatar.Foundation.Abstractions/IActorDispatchPort.cs`; `src/Aevatar.Foundation.Abstractions/EventEnvelopePublishOptions.cs`; `src/Aevatar.Foundation.Abstractions/EnvelopeRouteSemantics.cs` | — | — | — | — | — | pending |
| `02/06-local-runtime-and-lifecycle.md` | current | `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActor.cs`; `src/Aevatar.Foundation.Runtime.Implementations.Local/README.md`; `src/Aevatar.Foundation.Runtime.Implementations.Local/Actors/LocalActorRuntime.cs` | — | — | — | — | — | pending |
| `03/01-workflow-model-and-identities.md` | current | `src/workflow/Aevatar.Workflow.Core/WorkflowGAgent.cs`; `src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs`; `src/workflow/Aevatar.Workflow.Core/workflow_state.proto` | — | — | — | — | — | pending |
| `03/02-yaml-schema-and-validation.md` | current | `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowParser.cs`; `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowYamlValidatorImpl.cs`; `docs/canon/workflow-primitives.md` | — | — | — | — | — | pending |
| `03/03-execution-kernel-and-outcomes.md` | current | `src/workflow/Aevatar.Workflow.Core/Execution/WorkflowExecutionKernel.cs`; `src/workflow/Aevatar.Workflow.Abstractions/workflow_execution_messages.proto`; `src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs` | — | — | — | — | — | pending |
| `03/04-primitives-catalog.md` | current | `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowPrimitiveCatalog.cs`; `src/workflow/Aevatar.Workflow.Core/Modules/`; `docs/canon/workflow-primitives.md` | — | — | — | — | — | pending |
| `03/05-pause-signal-approval-and-resume.md` | current | `src/workflow/Aevatar.Workflow.Core/Modules/WaitSignalModule.cs`; `src/workflow/Aevatar.Workflow.Core/Modules/HumanApprovalModule.cs`; `src/workflow/Aevatar.Workflow.Core/workflow_state.proto` | — | — | — | — | — | pending |
| `03/06-saga-compensation-and-recovery.md` | mixed | `src/workflow/Aevatar.Workflow.Core/workflow_state.proto`; `src/workflow/Aevatar.Workflow.Core/WorkflowRunGAgent.cs`; `docs/adr/0034-workflow-saga-compensation-protocol.md` | — | — | — | — | — | pending |
| `03/07-connectors-and-capability-admission.md` | current | `src/workflow/Aevatar.Workflow.Abstractions/workflow_capability_admission.proto`; `src/workflow/Aevatar.Workflow.Application/ExternalCapabilities/WorkflowExternalCapabilityAdmissionService.cs`; `docs/canon/connector.md` | — | — | — | — | — | pending |
| `04/01-role-agent-and-streaming-run.md` | current | `src/Aevatar.AI.Core/RoleGAgent.cs`; `src/Aevatar.AI.Abstractions/ai_messages.proto`; `src/Aevatar.AI.Core/Chat/ChatRuntime.cs` | — | — | — | — | — | pending |
| `04/02-llm-providers-and-route-selection.md` | current | `src/Aevatar.AI.Abstractions/LLMProviders/ILLMProvider.cs`; `src/Aevatar.AI.Core/LLMProviders/OwnerLlmConfigApplier.cs`; `src/Aevatar.Bootstrap.Extensions.AI/CompositeLLMProviderFactory.cs` | — | — | — | — | — | pending |
| `04/03-tool-loop-catalog-and-presentation.md` | current | `src/Aevatar.AI.Core/Tools/ToolCallLoop.cs`; `src/Aevatar.Foundation.Abstractions/Tools/tool_presentation.proto`; `src/Aevatar.AI.Abstractions/ToolProviders/IAgentToolSource.cs` | — | — | — | — | — | pending |
| `04/04-tool-approval-and-authorization.md` | current | `src/Aevatar.AI.Core/Middleware/ToolApprovalMiddleware.cs`; `src/Aevatar.AI.Core/Middleware/ToolCallCredentialPolicyMiddleware.cs`; `src/Aevatar.AI.Abstractions/ToolProviders/IRemoteToolApprovalPort.cs` | — | — | — | — | — | pending |
| `04/05-prompt-overlays-and-agent-context.md` | current | `src/Aevatar.AI.Abstractions/Prompting/SystemPromptLayers.cs`; `src/Aevatar.AI.Core/Prompting/SystemPromptLayerComposer.cs`; `docs/canon/system-skill-overlay-authoring-contract.md` | — | — | — | — | — | pending |
| `05/01-command-event-projection-readmodel.md` | current | `docs/canon/cqrs-projection.md`; `src/Aevatar.CQRS.Projection.Core/README.md`; `src/Aevatar.CQRS.Projection.Core.Abstractions/Abstractions/Orchestration/CommittedStateEventEnvelope.cs` | — | — | — | — | — | pending |
| `05/02-committed-state-and-observation.md` | current | `src/Aevatar.Foundation.Abstractions/agent_messages.proto`; `src/Aevatar.CQRS.Projection.Core/Orchestration/CommittedStateProjectionActivationHook.cs`; `src/Aevatar.CQRS.Projection.Core/Streaming/ProjectionSessionEventHub.cs` | — | — | — | — | — | pending |
| `05/03-projection-lifecycle-and-leases.md` | current | `src/Aevatar.CQRS.Projection.Core/Orchestration/ProjectionScopeGAgentBase.cs`; `src/Aevatar.CQRS.Projection.Core/Orchestration/ProjectionRuntimeLeaseBase.cs`; `src/Aevatar.CQRS.Projection.Core.Abstractions/Abstractions/Activation/ProjectionActivationPlan.cs` | — | — | — | — | — | pending |
| `05/04-readmodel-stores-versioning-and-rebuild.md` | mixed | `src/Aevatar.CQRS.Projection.Stores.Abstractions/Abstractions/ReadModels/ProjectionWriteResult.cs`; `src/Aevatar.CQRS.Projection.Providers.Elasticsearch/Stores/ElasticsearchIndexLifecycleManager.cs`; `docs/adr/0040-current-state-readmodel-dr-rebuild.md` | — | — | — | — | — | pending |
| `05/05-workflow-agui-and-live-observation.md` | current | `src/workflow/Aevatar.Workflow.Projection/README.md`; `src/workflow/Aevatar.Workflow.Presentation.AGUIAdapter/EventEnvelopeToWorkflowRunEventMapper.cs`; `src/Aevatar.AGUI.Contracts/agui_events.proto` | — | — | — | — | — | pending |
| `05/06-audit-trail-lifecycle-and-export.md` | current | `src/Aevatar.Audit.Abstractions/audit_messages.proto`; `src/Aevatar.Audit.Core/CommittedFacts/CommittedAuditArtifactMaterializer.cs`; `docs/canon/audit-trail.md` | — | — | — | — | — | pending |
| `06/01-scope-team-member-resource-model.md` | current | `agents/Aevatar.GAgents.StudioTeam/studio_team_messages.proto`; `agents/Aevatar.GAgents.StudioMember/studio_member_messages.proto`; `src/Aevatar.Studio.Hosting/Endpoints/StudioTeamEndpoints.cs` | — | — | — | — | — | pending |
| `06/02-draft-revision-binding-and-published-service.md` | current | `src/Aevatar.Studio.Application/Studio/Services/StudioMemberWorkflowBindingPort.cs`; `agents/Aevatar.GAgents.StudioMember/StudioMemberBindingRunGAgent.cs`; `src/platform/Aevatar.GAgentService.Abstractions/Protos/service_revision.proto` | — | — | — | — | — | pending |
| `06/03-catalog-visibility-and-scope-authorization.md` | current | `docs/canon/workflow-catalog-visibility.md`; `src/workflow/Aevatar.Workflow.Projection/Projectors/WorkflowCatalogCurrentStateProjector.cs`; `src/workflow/Aevatar.Workflow.Projection/Workflows/WorkflowCatalogReadModelQueryPort.cs` | — | — | — | — | — | pending |
| `06/04-studio-commands-acks-and-readmodels.md` | current | `src/Aevatar.Studio.Hosting/Endpoints/StudioMemberEndpoints.cs`; `src/Aevatar.Studio.Projection/CommandServices/ActorDispatchStudioMemberCommandService.cs`; `src/Aevatar.Studio.Projection/QueryPorts/ProjectionStudioMemberQueryPort.cs` | — | — | — | — | — | pending |
| `06/05-work-orders-and-durable-intent.md` | current | `agents/Aevatar.GAgents.WorkOrder/work_order_messages.proto`; `agents/Aevatar.GAgents.WorkOrder/WorkOrderGAgent.cs`; `docs/canon/work-orders.md` | — | — | — | — | — | pending |
| `07/01-conversation-turn-and-chat-history.md` | current | `agents/Aevatar.GAgents.ChatHistory/chat_history_messages.proto`; `agents/Aevatar.GAgents.ChatHistory/ChatConversationGAgent.cs`; `agents/Aevatar.GAgents.ChatHistory/ChatTurnHistoryDeliveryGAgent.cs` | — | — | — | — | — | pending |
| `07/02-nyxid-chat-actor-model-and-progress.md` | current | `agents/Aevatar.GAgents.NyxidChat/NyxIdChatGAgent.cs`; `agents/Aevatar.GAgents.NyxidChat/NyxIdChatProjectionSession.cs`; `docs/canon/nyxid-chat-api.md` | — | — | — | — | — | pending |
| `07/03-agent-profile-and-immutable-binding.md` | current | `docs/canon/nyxid-chat-agent-profile-binding.md`; `src/Aevatar.AI.Core/AgentProfiles/AgentProfileSnapshotCodec.cs`; `agents/Aevatar.GAgents.NyxidChat/AgentProfiles/AgentProfileTurnCatalogMaterializer.cs` | — | — | — | — | — | pending |
| `07/04-turn-authority-tool-catalog-and-retry.md` | current | `src/Aevatar.AI.Core/RoleGAgent.cs`; `src/Aevatar.AI.Core/AgentProfiles/AgentProfileTurnCatalog.cs`; `agents/Aevatar.GAgents.NyxidChat/AgentProfiles/AgentProfileTurnCatalogMaterializer.cs` | — | — | — | — | — | pending |
| `08/01-ingress-normalization-and-routing.md` | current | `agents/Aevatar.GAgents.Channel.Abstractions/protos/chat_activity.proto`; `agents/Aevatar.GAgents.Channel.Runtime/ConversationDispatchMiddleware.cs`; `src/Aevatar.ChatRouting.Core/ChatRouteResolver.cs` | — | — | — | — | — | pending |
| `08/02-channel-runtime-and-credential-boundary.md` | current | `agents/Aevatar.GAgents.Channel.Abstractions/protos/channel_contracts.proto`; `agents/Aevatar.GAgents.Channel.Runtime/Conversation/ConversationGAgent.cs`; `docs/adr/0012-channel-runtime-credential-boundary.md` | — | — | — | — | — | pending |
| `08/03-lark-delivery-interaction-and-repair.md` | mixed | `agents/channels/Aevatar.GAgents.Channel.NyxIdRelay/ChannelCallbackEndpoints.cs`; `agents/channels/Aevatar.GAgents.Channel.NyxIdRelay/ChannelWorkflowResultDeliveryRepairService.cs`; `docs/canon/lark-reply-completion-semantics.md` | — | — | — | — | — | pending |
| `08/04-file-artifacts-and-attachments.md` | current | `src/workflow/Aevatar.Workflow.Abstractions/workflow_execution_messages.proto`; `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/WorkflowMultipartFileInputParser.cs`; `agents/Aevatar.GAgents.Channel.Runtime/protos/conversation_state.proto` | — | — | — | — | — | pending |
| `08/05-voice-control-and-media-planes.md` | mixed | `src/Aevatar.Foundation.VoicePresence.Abstractions/Protos/voice_presence.proto`; `src/Aevatar.Foundation.VoicePresence.Abstractions/Sessions/IVoiceVolatileMediaStreamPort.cs`; `src/Aevatar.Mainnet.Host.Api/Voice/PolicyAwareVoiceEndpoints.cs` | — | — | — | — | — | pending |
| `09/01-automation-resource-api-and-readmodels.md` | current | `src/Aevatar.Studio.Hosting/Endpoints/StudioMemberAutomationEndpoints.cs`; `src/platform/Aevatar.GAgentService.Abstractions/Schedules/TeamAutomationOperationObservationContracts.cs`; `src/platform/Aevatar.GAgentService.Projection/Queries/ScheduledDispatchQueryPort.cs` | — | — | — | — | — | pending |
| `09/02-scheduled-actor-callback-and-fire.md` | current | `src/platform/Aevatar.GAgentService.Core/Schedules/ScheduledDispatchGAgent.cs`; `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Grains/Callbacks/RuntimeCallbackSchedulerGrain.cs`; `src/platform/Aevatar.GAgentService.Abstractions/Schedules/ScheduledDispatchCalculator.cs` | — | — | — | — | — | pending |
| `09/03-owner-authorization-and-agent-key.md` | current | `src/platform/Aevatar.GAgentService.Abstractions/Protos/scheduled_invocation_authorization_plan.proto`; `src/platform/Aevatar.GAgentService.Application/Schedules/Authorization/ScheduledInvocationAuthorizationPlanner.cs`; `docs/adr/0041-scheduled-invocation-agent-key-credential-reference.md` | — | — | — | — | — | pending |
| `09/04-vault-reference-and-revocation-compensation.md` | current | `src/platform/Aevatar.GAgentService.Core/Schedules/scheduled_dispatch_state.proto`; `src/Aevatar.Foundation.Abstractions/Credentials/credential_secret_references.proto`; `docs/adr/0043-scheduled-credential-lifecycle-compensation.md` | — | — | — | — | — | pending |
| `09/05-production-canary-and-recovery.md` | mixed | `docs/operations/2026-07-23-scheduled-agent-key-production-canary.md`; `docs/operations/2026-07-23-scheduled-agent-key-runtime-integrity-rollout.md`; protected `09/03/.../02-scheduled-agent-key-production-canary.md` | — | — | — | — | — | pending |
| `10/01-production-topology-and-configuration.md` | current | `src/Aevatar.Mainnet.Host.Api/Hosting/MainnetHostBuilderExtensions.cs`; `src/Aevatar.Mainnet.Host.Api/README.md`; `docs/canon/overview.md` | — | — | — | — | — | pending |
| `10/02-orleans-runtime.md` | current | `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Grains/RuntimeActorGrain.cs`; `src/Aevatar.Foundation.Runtime.Implementations.Orleans/Actors/OrleansActorRuntime.cs`; `src/Aevatar.Foundation.Runtime.Implementations.Orleans/README.md` | — | — | — | — | — | pending |
| `10/03-garnet-clustering-and-secret-storage.md` | current | `src/Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet/GarnetEventStore.cs`; `src/Aevatar.Foundation.Runtime.Persistence.Implementations.Garnet/GarnetBackedSecretVault.cs`; `docs/adr/0032-mainnet-garnet-clustering.md` | — | — | — | — | — | pending |
| `10/04-streaming-transport-and-kafka.md` | mixed | `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Streaming/Streaming/OrleansActorStream.cs`; `src/Aevatar.Foundation.Runtime.Implementations.Orleans.Transport.KafkaProvider/Streaming/KafkaProviderQueueAdapter.cs`; `docs/adr/0003-kafka-transport.md` | — | — | — | — | — | pending |
| `10/05-authentication-scope-and-admin-authorization.md` | current | `src/Aevatar.Authentication.Hosting/AevatarAuthenticationHostExtensions.cs`; `src/Aevatar.Authentication.Hosting/DPoPProofValidator.cs`; `src/Aevatar.Authentication.Abstractions/IPlatformAdminAuthorizer.cs` | — | — | — | — | — | pending |
| `10/06-managed-codex-sandbox-and-delegation.md` | mixed | `src/Aevatar.AI.Abstractions/CodexExecution/codex_execution.proto`; `src/Aevatar.AI.Infrastructure.ChronoSandbox/ChronoSandboxCodexExecutionAdapter.cs`; `docs/canon/managed-codex-execution.md` | — | — | — | — | — | pending |
| `10/07-observability-status-and-observatory.md` | current | `docs/canon/observability.md`; `src/Aevatar.Mainnet.Host.Api/Status/StatusEndpoints.cs`; `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/WorkflowRunObservatoryEndpoints.cs` | — | — | — | — | — | pending |
| `10/08-architecture-and-security-guards.md` | current | `tools/ci/architecture_guards.sh`; `tools/ci/README.md`; `tools/ci/audit_trail_guards.sh` | — | — | — | — | — | pending |
| `11/01-run-a-simple-workflow.md` | current | `workflows/simple_qa.yaml`; `src/workflow/Aevatar.Workflow.Host.Api/README.md`; `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/ChatEndpoints.cs` | — | — | — | — | — | pending |
| `11/02-build-a-branching-tool-workflow.md` | current | `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowPrimitiveCatalog.cs`; `src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowYamlValidatorImpl.cs`; `workflows/firecrawl_agent_async_poll.yaml` | — | — | — | — | — | pending |
| `11/03-create-bind-and-invoke-a-team-member.md` | current | `src/Aevatar.Studio.Hosting/Endpoints/StudioTeamEndpoints.cs`; `src/Aevatar.Studio.Hosting/Endpoints/StudioMemberEndpoints.cs`; `src/Aevatar.Studio.Application/Studio/Services/StudioMemberWorkflowBindingPort.cs` | — | — | — | — | — | pending |
| `11/04-connect-a-channel-and-handle-files.md` | current | `agents/Aevatar.GAgents.Channel.Abstractions/protos/channel_contracts.proto`; `agents/channels/Aevatar.GAgents.Channel.NyxIdRelay/ChannelCallbackEndpoints.cs`; `src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/WorkflowMultipartFileInputParser.cs` | — | — | — | — | — | pending |
| `11/05-create-verify-and-troubleshoot-automation.md` | current | `src/Aevatar.Studio.Hosting/Endpoints/StudioMemberAutomationEndpoints.cs`; `src/platform/Aevatar.GAgentService.Projection/Queries/ScheduledDispatchQueryPort.cs`; `docs/operations/2026-07-23-scheduled-agent-key-production-canary.md` | — | — | — | — | — | pending |
| `12/01-evolution-method-and-timeline.md` | historical | 演进层证据：issue ledger; git commits; ADR status history | — | — | — | — | — | pending |
| `12/02-issue-decisions-by-theme.md` | mixed | 演进层证据：280 classified issue rows; associated PR/commit/ADR | — | — | — | — | — | pending |
| `12/03-retired-and-superseded-components.md` | historical | 演进层证据：current deletion facts; historical commits/ADR | — | — | — | — | — | pending |
| `12/04-incident-case-studies.md` | mixed | 演进层证据：old `10/*`; canary; production operations docs; current fixes | — | — | — | — | — | pending |
| `12/05-open-gaps-and-canon-drift.md` | target | 演进层证据：open issue classes; Proposed ADR; code/canon conflicts | — | — | — | — | — | pending |
| `13/01-glossary.md` | current | 索引章：证据来自本表与 issue 账本，不单列代码脊柱 | — | — | — | — | — | pending |
| `13/02-canon-and-adr-index.md` | mixed | 索引章：证据来自本表与 issue 账本，不单列代码脊柱 | — | — | — | — | — | pending |
| `13/03-chapter-source-matrix.md` | current | 索引章：证据来自本表与 issue 账本，不单列代码脊柱 | — | — | — | — | — | pending |
| `13/04-issue-evolution-index.md` | mixed | 索引章：证据来自本表与 issue 账本，不单列代码脊柱 | — | — | — | — | — | pending |
