# Studio(member-first / team-first 聚合)+ Scripting

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Studio.Application/`:`Studio/Contracts/`(Member/Role/Team/Workspace/Connector/Editor/Settings/Execution)、`Studio/Authoring/`、`Studio/Abstractions/`(ports:`IStudioMemberCommandPort`/`IStudioTeamService`/`IStudioWorkspaceCommandPort`)。
- `src/Aevatar.Studio.Domain/`:`Studio/Models/`(WorkflowDocument/RoleModel/StepModel)、`Studio/Services/WorkflowValidator.cs` + `WorkflowDocumentNormalizer.cs`。
- `src/Aevatar.Studio.Hosting/`:`Endpoints/`(StudioMember/Team/Studio/Explorer)、`Controllers/`(Editor/Connectors/Workspace/UserConfig)、`NyxId/`。
- `src/Aevatar.Studio.Infrastructure/`:`ActorBacked/`(actor-backed ports)、`Storage/`、`ScopeResolution/AppScopeResolver.cs`、`Serialization/YamlWorkflowDocumentService.cs`。
- `src/Aevatar.Studio.Projection/`:`ReadModels/`(StudioMember/Team/Workspace/UserConfig/UserMemory/ChatConversation/RoleCatalog/ConnectorCatalog/GAgentRegistry current-state documents + `studio_projection_readmodels.proto`)、`CommandServices/`、`Orchestration/`(materialization lease、`StudioActorBootstrap`)。
- `agents/Aevatar.GAgents.StudioMember/`(`StudioMemberGAgent.cs`)+ `agents/Aevatar.GAgents.StudioTeam/`(`StudioTeamGAgent.cs`)。
- `docs/adr/0016-studio-member-first-published-service.md`(accepted):member-first 生命周期(Create→Build→Bind→Invoke→Observe);Studio 主对象是 `member`(不再 leak scope-first)。
- `docs/adr/0017-studio-team-first-class-aggregate.md`(accepted):team 作为 first-class aggregate(member contract 之上定义 team identity/lifecycle/aggregate)。
- `src/Aevatar.Scripting.*`(6 项目):Abstractions/`script_host_messages.proto`、Core/`ScriptBehaviorGAgent.cs` + `ScriptEvolutionSessionGAgent.cs`、Application/`Runtime/ScriptBehaviorDispatcher.cs`、Infrastructure/`Compilation/RoslynScriptBehaviorCompiler.cs` + `ScriptSandboxPolicy.cs`、Hosting/`CapabilityApi/ScriptCapabilityEndpoints.cs`、Projection/`Materialization/`。
- `docs/canon/scripting.md`(active)。

---

## Studio:member-first / team-first

Studio 是 aevatar 的创作/管理面。六个项目按 DDD 分层(Application/Domain/Hosting/Infrastructure/Projection + authority actors)。

**member-first**(ADR-0016):Studio 的主对象是 `member`,生命周期 `Create member → Build → Bind → Invoke → Observe`。不再 leak scope-first 模型。

**team-first**(ADR-0017):team 作为 first-class aggregate,在 member contract 之上定义 team identity/lifecycle/aggregate 语义。

authority actors:`StudioMemberGAgent`(member 聚合权威)、`StudioTeamGAgent`(team 聚合权威)。

投影:`Studio.Projection` 持 StudioMember/Team/Workspace/UserConfig/UserMemory/ChatConversation/RoleCatalog/ConnectorCatalog/GAgentRegistry 当前态文档 + `studio_projection_readmodels.proto`。

---

## Scripting

六个项目(`src/Aevatar.Scripting.*`):
- **Abstractions**:`script_host_messages.proto` + query ports
- **Core**:`ScriptBehaviorGAgent` + `ScriptEvolutionSessionGAgent`(脚本行为/演进 actor)
- **Application**:`ScriptBehaviorDispatcher`(capability factory)
- **Infrastructure/Compilation**:`RoslynScriptBehaviorCompiler`(Roslyn 编译)+ `ScriptSandboxPolicy`(沙箱策略)
- **Hosting**:`ScriptCapabilityEndpoints`
- **Projection**:native document/graph/payload materializers

`docs/canon/scripting.md`(active)是架构文档。

---

## 验收

1. Studio 主对象是什么?(member,ADR-0016 member-first)
2. team 是什么?(first-class aggregate,ADR-0017)
3. Scripting 用什么编译?(Roslyn,RoslynScriptBehaviorCompiler + ScriptSandboxPolicy)

⟦AI:AUTO-LOOP⟧
