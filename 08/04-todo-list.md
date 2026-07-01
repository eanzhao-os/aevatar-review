## 事实源

> 本篇是全书 ⚠️ 待决策项的**汇总 + 重审 + 未来规划**。每一条都已对照 `~/Code/aevatar`
> 当前源码核实(核对基线见文末「附:核对方法与基线」)。
> 高价值锚点(以源码为准,故意不贴行号):
> `docs/canon/architecture.md`、`docs/adr/0034-workflow-saga-compensation-protocol.md`、
> `src/workflow/Aevatar.Workflow.Core/Execution/WorkflowExecutionKernel.cs`、
> `src/Aevatar.AI.Core/Chat/ChatRuntime.cs`、
> `src/Aevatar.CQRS.Projection.Core/Orchestration/CommittedStateProjectionActivationHook.cs`。

# TODO List 与未来规划:设计缺口 / 待决策 / canon 漂移

> 本篇把散落在各章的 ⚠️ 标记**重新核对源码后归并成一份带优先级的未来规划**。
> 与上一版(纯 A/B/C 分类清单)的区别:每条都给出**最新核实结论**、**目标仓库**、
> **建议动作**,并按"先做什么"排序。owner 逐条拍板后,在此 ✅ 并回填结论。
>
> **两层未来规划**:本篇是**战术层**(修补现有实现的缺口 / 待决策 / canon 漂移);
> **战略层**(把"结晶梯度"做成一等可自迭代生命周期的产品方向)见
> [05 结晶梯度路线图](05-crystallization-roadmap.md)。两者交叉引用:战术里的 P1-1/P0-4/P2-2 是战略落地的前置 enabler。

**优先级图例**:🔴 P0(有硬期限 / 正确性 / 安全)· 🟠 P1(canon/事实源漂移)· 🟡 P2(设计决策待拍板)· ⚪ P3(文档准确性 & 死代码清理)
**目标仓库**:`[code]` aevatar 源码 · `[canon]` canon/ADR · `[doc]` 本解读仓库

---

## 0. 本次重审结论摘要

> 📝 **2026-06-18 review pass**:本表所有 `[doc]` 项已在解读仓库分支 `review/doc-revision-2026-06-18` 落地(strip-line-number debris 清理 + 事实订正 + 每章 ≥2 配图,全部经 `scripts/check-mermaid.py` 真引擎校验)。校核中发现并已修正的几处偏差:
> - **ToolSource 实际 26 个**(非本表旧写的 25),21 个在 src/Aevatar.AI.ToolProviders.*、5 个在 `src/workflow/`;`AgentWorkflowToolSource` / `LarkWorkflowFileSubmitToolSource` **不存在**(应为 `WorkflowAgentToolSource` / `WorkflowFileSubmitToolSource`)。
> - **P2-5** 生产其实 **fail-fast**(`EnforceInMemoryPolicy` 在 Production/DenyInMemory 时抛错),不是“静默退化成内存读模型”;05/03 已按此订正。
> - **P0-3** 准确字段名是 `AIAgentConfig.MaxToolRounds`(=40),不是 `AIGAgentBase.MaxToolRounds`。
> - saga 状态枚举是 `WorkflowSagaStatus.CompensationDeadLetter`(单数);`ToolApprovalMiddleware` 实际是链上第 2 位(`ToolCallCredentialPolicyMiddleware` 之后),非“最前”。

把上一版 18 条(A1–A5 / B1–B5 / C1–C8)逐条对源码复核,结论:

| 桶 | 结果 | 条目 |
|---|---|---|
| **已核实、可归档**(确认删除 / 收敛完成) | 6 | A1 A2 A3 A4 A5 · C7 |
| **结论翻转**(代码已落地,缺口转移到 canon/doc) | 2 | **B2 saga**(代码已全实现)· B3 timeline/graph |
| **仍开放**(真实缺口 / 待拍板) | 10 | B1 B4 B5 · C1 C2 C3 C4 C5 C6 C8 |
| **新发现**(本轮核对新增) | 见各 P 区 ★NEW | FailoverLLMProvider、隐式 `assistant` 角色、InMemory 生产兜底、OCC-retry 误解… |

> ⚠️ **核对基线漂移**:本书章节多写于 aevatar 旧 HEAD;实际当前源码已推进到
> `feature/integrate @ 803d1ab53`(2026-06-17 核对)。**最大的一处翻转**:saga 补偿
> 协议(B2 / ADR-0034)在文档里还是「proposed / 实现程度不明」,**但代码已经全量落地**。

---

## 1. 🔴 P0 — 有硬期限 / 正确性 / 安全风险(先做)

| # | 问题 | 最新核实(对源码) | 建议动作 | 目标 |
|---|---|---|---|---|
| **P0-1** | **streaming-proxy 的 room/participant 无替代**(原 B4) | `agents/Aevatar.GAgents.StreamingProxy/StreamingProxyEndpoints.cs` 仍提供 `rooms` / `participants` / `messages:stream` 路由,**Sunset 头 = 2026-11-25**;`src/Aevatar.Mainnet.Host.Api/Responses/ResponsesEndpoints.cs`(`/v1/responses`)全文无 room/participant 概念。缺口真实存在。注:首前端 console-web 已迁到 AG-UI `/api/chat`,**受影响的是外部 API/SDK 消费方**,不是自家 UI。 | owner 在 **2026-11-25 前**定 room/participant 去留:要么在 `/v1/responses` 补等价语义,要么显式声明该能力随 sunset 一并废弃并通知外部消费方。 | `[code]` |
| **P0-2** | **voice 静态 key 在 mainnet 未 fail-closed**(原 B5 + ★NEW) | ADR-0033 描述的 NyxID ephemeral broker **代码已落地**(`NyxIdRealtimeProviderCredentialResolver`,broker 默认开),但 `OpenAIRealtimeProvider` 在无 resolver 时**回退到静态 config key**,且这条回退**不按环境门禁** —— 部署只要设了 `OPENAI_API_KEY` env 就会激活静态路径,与 ADR-0018「零长期密钥」相悖。 | 给 mainnet 加 fail-closed 守卫:生产环境检测到静态 key 直接拒启/告警,只保留 dev 直连。顺带把 ADR-0033 提 accepted(见 P1)。 | `[code]` |
| **P0-3** | **`ChatRuntime` 工具轮次无封顶**(原 C2) | 复核仍在:`src/Aevatar.AI.Core/AIGAgentBase.cs` 基类默认 `MaxToolRounds = 40`(安全);但 `src/Aevatar.AI.Core/Chat/ChatRuntime.cs` 的 `DefaultMaxToolRounds = int.MaxValue`,且**无参 `ChatRuntime` 重载会把 `int.MaxValue` 直接透传**,非 `AIGAgentBase` 调用方可无限自旋。上游 [#2210](https://github.com/aevatarAI/aevatar/issues/2210) **代码未修**。 | 在 `ChatRuntime` 解析有效轮次处加合理硬上限(而非 `int.MaxValue`),让所有调用方都有兜底。 | `[code]` |
| **P0-4** | **投影激活 hook 的跨 commit 幂等是 best-effort**(原 C5 + ★NEW) | `CommittedStateProjectionActivationHook` 里的 `HashSet` **只在单次 `BeforePublishAsync` 内**去重;跨 commit 幂等实际落在 `ProjectionScopeActorRuntime.EnsureExistsAsync` 的 `ExistsAsync→CreateByKindAsync`(check-then-create,**无锁/lease,有 TOCTOU 窗口**,且异常被吞)。另有一条 stale actor-kind 时 destroy+recreate 的 self-heal 旁路。 | 审计首次并发 publish 竞态:确认 `CreateByKindAsync` 自身幂等,或给 ensure 路径加 lease/锁;把 self-heal 旁路的语义补进 05/02。 | `[code]` |

---

## 2. 🟠 P1 — canon / 事实源漂移(SSOT 可信度,优先于功能开发)

> 本仓库的第一原则是「以 `~/Code/aevatar` 为唯一事实源」。canon/ADR 与代码不一致,
> 会让所有信任 canon 的人被误导 —— 这是收益最高的一类修。

| # | 问题 | 最新核实 | 建议动作 | 目标 |
|---|---|---|---|---|
| **P1-1** ★ | **ADR-0034 saga 状态严重滞后**(原 B2 翻转) | saga 补偿**代码已全量落地**:`src/workflow/Aevatar.Workflow.Core/workflow_state.proto` 定义 `compensable_ledger`/`saga_status`/`dead_letter_*`(run actor 自持,无外部 coordinator);`WorkflowExecutionKernel` 反向串行发补偿;`WorkflowRunGAgent` 失败耗尽→`CompensationDeadLettered`。**但** `docs/adr/0034-workflow-saga-compensation-protocol.md` 仍 `status: proposed`,正文用将来时描述。ADR-0006/0017 等交叉引用还称其"rejected/未实现"。 | 把 ADR-0034 提 `accepted`,正文改成「已落地」事实口径;清理 0006/0017 里过期的"未实现"交叉引用;02/03 去掉 saga 的 proposed 框架。**全书最高优先文档修。** | `[canon]` |
| **P1-2** | **RunManager / RunContextScope 是 canon 幽灵**(原 B1) | 复核确认**代码里不存在**:全仓只有 `src/Aevatar.Foundation.Core/Context/AsyncLocalAgentContext.cs`;但 `docs/canon/architecture.md` 仍把 `IRunManager` / `RunManager` / `RunContextScope`(latest-wins)列成现役类型。 | owner 二选一:① 补实现 RunManager;② 在 `architecture.md` 把它降标为「目标态/设计意图」。本仓 03/04、01/03 已诚实标注,等 canon 口径统一后回指。 | `[canon]` |
| **P1-3** | **Timeline/Graph 已无独立 projector**(原 B3) | 复核确认:timeline/graph 现从单一 `WorkflowRunInsightReport` artifact **派生**(Materializer),旧 `*ArtifactProjector` 类已删;canon `architecture.md` 引用过期。 | canon 同步:删掉对已删 projector 类的引用,改述为「派生自 InsightReport」。本仓 05/04 已标注。 | `[canon]` |

---

## 3. 🟡 P2 — 设计决策待 owner 拍板(非 bug,是取舍)

| # | 问题 | 最新核实 | 建议动作 | 目标 |
|---|---|---|---|---|
| **P2-1** | **隐式依赖展开 + 隐式默认角色**(原 C1 + ★NEW) | 真实且无显式开关:`WorkflowStepTypeModuleDependencyExpander`(有 `target_role` 自动加 `llm_call`)+ 同目录 implicit expander 链。★更隐蔽的一处:`src/workflow/Aevatar.Workflow.Core/Primitives/WorkflowImplicitLlmRolePolicy.cs` 在需要 LLM 却没声明角色时**静默合成 `"assistant"` 角色**。两者在 YAML 里都不可见。 | 拍板要不要给一个「显式模式」(关掉隐式展开/默认角色);无论关不关,都得把 `WorkflowImplicitLlmRolePolicy` 的默认角色写进 02/04(目前文档只提了 `llm_call` 注入)。 | `[code]`/`[doc]` |
| **P2-2** | **Tornado provider 是降级旁路**(原 C4,文档需修正) | 核实**翻转 doc 口径**:并非「NyxId/Tornado 都桥接 MEAI」。只有 `NyxIdLLMProvider` 经 MEAI;`src/Aevatar.AI.LLMProviders.Tornado/TornadoLLMProvider.cs` 直接实现 `ILLMProvider`,**纯文本、多模态被静默丢弃、工具调用故意未实现**(注释指向「请用 MEAI provider」)。任何挂在 Tornado 上的 role 会**静默失去 tool use**。 | 决定:退役 Tornado,或补齐 tool/多模态;在落地前 04/02 必须改成「Tornado 是降级 chat-only 路径」并加 ⚠️。 | `[code]`/`[doc]` |
| **P2-3** | **`ICommittedStateEventPublisher` 为何 internal**(原 C3) | 核实倾向**有意封装**:`src/Aevatar.Foundation.Core/EventSourcing/ICommittedStateEventPublisher.cs` 是 framework-internal,公开面是 observer route(`ObserverPublication` + `CommittedStateEventPublished`),不是这个 publisher。 | 建议**直接关闭**该疑点,结论记为「committed-fact 发射是框架内部职责,公开面走 observer route」;若将来要扩展能力面,再引入受控 port。去掉 03/05 的"遗留?"措辞。 | `[doc]` |
| **P2-4** | **缺独立 Orleans runtime ADR**(原 C8) | 核实确认:`docs/adr/` 无 Orleans 专属 ADR(最近的是 0002 §8、0007、0020);而 Orleans runtime 代码量很大(Implementations.Orleans + Streaming + KafkaProvider 共 40+ 个 .cs)。 | 补一份合并性的「Orleans Runtime」ADR,收口同 actorId 全局单激活 + 邮箱串行 + stream-forward 的设计。 | `[canon]` |
| **P2-5** ★ | **ReadModel 生产默认是 InMemory 静默兜底** | ★NEW:`MainnetAgentProjectionDocumentStores` 逻辑是「ES 开了用 ES,否则**无条件回退 InMemory**」。ES(生产级,带 schema-drift 重建 + ACL 守卫)、Neo4j(真实 Cypher store)都已就绪,但默认兜底会让**误配的生产环境静默退化成内存读模型**。 | 生产改成 ES fail-fast(未配置直接拒启),InMemory 仅限 dev/test。 | `[code]` |
| **P2-6** | **9 个 `.slnf` 切分依据**(原 C6) | 本轮未深核(属设计意图问题,非代码缺口)。 | owner 用 1-2 句说明切分原则(按 host/层/可独立编译?),回填 00/02;说不清则标演进遗留。 | `[doc]` |

---

## 4. ⚪ P3 — 文档准确性修正 & 死代码清理(delete-first)

### 4.1 已删组件 —— 确认关闭,归档为「历史/已核实」

> 全部对源码复核:目录只剩未跟踪的 `obj/`/`bin/` 残留,git 已无源码。可在各章保留一条历史索引即可。

| # | 组件 | 核实结论 | 删除证据 |
|---|---|---|---|
| A1 | A2A Interop(3 项目) | ✅ 0 跟踪文件,仅 obj 残留 | `8bfd8605c`(见 07/02) |
| A2 | Inspector demo | ✅ 已删;ADR-0023 + tier guard 仍在;console-web inspector 面板是另一套现役实现 | `40a36bbe2`(见 07/07) |
| A3 | demos(Workflow/Cli/Maker/CaseProjection) | ✅ 全删;★**唯一存活 demo = `demos/lark-interaction-probe/`**(一个 YAML probe,非代码 demo) | `4a029981c`/`4ff5c2d1b`(见 08/03) |
| A4 | StateMirror Projection | ✅ 历史目录 **src/Aevatar.CQRS.Projection.StateMirror** 现为**空目录**(已在源码库中移除) | `da7944cf2`(见 05/03) |
| A5 | MassTransit transport | ✅ 三目录 0 .cs/.csproj,0 `PackageReference`;Kafka 是手写 `Confluent.Kafka` 藏在 Orleans `IQueueAdapter` 后 | 上游 [#2209](https://github.com/aevatarAI/aevatar/issues/2209) |
| C7 | Telegram direct-callback | ✅ 收敛完成,无残留/坏代码;ADR-0013 修正案已把 Telegram 并入 NyxID relay 骨干 | 见 07/01 |

### 4.2 死代码清理(FI-007 删除优先)

- [ ] 移除源码库中历史目录 **src/Aevatar.CQRS.Projection.StateMirror** 的残留。 `[code]`
- [ ] 清掉 `Directory.Packages.props` 里残留的 MassTransit `PackageVersion` 条目(已零消费,仅靠 guard 挡 v9)。 `[code]`

### 4.3 文档计数 / 术语 / 措辞修正(本仓)

- [x] **ToolSource 计数**(已修):04/03 旧写「22」。**实际 26 个** `*ToolSource`:21 个在 src/Aevatar.AI.ToolProviders.*,5 个在 `src/workflow/`(`WorkflowDocumentExtractToolSource` / `WorkflowSpreadsheetExtractToolSource` / `WorkflowFileSubmitToolSource` / `WorkflowConnectedServiceResourceFetchToolSource` / `HumanInteractionChannelToolSource`)。注:`AgentWorkflowToolSource`、`LarkWorkflowFileSubmitToolSource` **不存在**。 `[doc]`
- [ ] **补 FailoverLLMProvider**:`src/Aevatar.AI.Core/LLMProviders/FailoverLLMProviderFactory.cs`(primary→fallback,首个有效 chunk 前可中途切换)在 04/02 缺失,文档只讲了 Composite/Reloadable。 `[doc]`
- [ ] **LiveSink 术语**:并无 `LiveSink` 类型;真实抽象是 `IEventSinkProjectionLifecyclePort` + `ProjectionSessionEventHub`。05/02 / 06/01 统一术语,便于读者 grep。 `[doc]`
- [ ] **投影并发不是单线程**:实际是 OCC-retry(`EventStoreOptimisticConcurrencyException` 驱动重试),05/02 加一句避免误解。 `[doc]`
- [ ] **06/01 措辞**:`projection:{rootActorId}` / `workflow-run:{actorId}:{commandId}` 是示意名,不是字面常量;底层是 lease-based(`ReleaseProjectionAsync`/`ProjectionRuntimeScopeKey`)。软化为示意。 `[doc]`
- [ ] **SemaphoreSlim guard 作用域**:06/05 说「禁止进程内 SemaphoreSlim 仲裁投影」偏泛;`architecture_guards.sh` 实际只盯 `WorkflowExecutionProjectionPort.cs` 单文件。改成精确表述。 `[doc]`
- [ ] **MiniCPM 凭证不对称**:07/04 把 OpenAI/MiniCPM 并列,但 ADR-0033 broker 只覆盖 OpenAI,MiniCPM 无 NyxID broker 路径 —— voice provider 成熟度不对称,补一句。 `[doc]`

### 4.4 补文档:已实现但没写的机制

- [ ] **saga 两阶段 ledger**:`Provisional→Confirmed`(`CompensableLedgerEntryStatus`)对 replay 正确性有意义,02/03 未提。 `[doc]`
- [ ] **saga `OutcomeUncertain` 跳过**:终态 step 失败为 `OutcomeUncertain` 时**故意不补偿**(避免补偿半成功的 step),是合理但未文档化的边界。 `[doc]`

---

## 5. 已确认结论存档

- **A5 MassTransit**:已完全不用;Kafka 是手写 Confluent.Kafka 客户端藏在 Orleans streaming 接口后。文档标「历史路径」。上游 [#2209](https://github.com/aevatarAI/aevatar/issues/2209)。
- **C2 无限轮次**:不是 bug —— 基类默认 40 轮(`AIGAgentBase.MaxToolRounds`);但 `ChatRuntime` 的 `int.MaxValue` fallback 是隐患(见 P0-3)。上游 [#2210](https://github.com/aevatarAI/aevatar/issues/2210)。
- **B2 saga**(本轮新结论):**代码已全量落地**,缺口只在 ADR-0034 滞后(见 P1-1)。
- **C7 Telegram**(本轮新结论):有意收敛到 NyxID relay,已完成,无残留(见 4.1)。

---

## 附:核对方法与基线

- **事实源**:`~/Code/aevatar`,核对时 HEAD = `feature/integrate @ 803d1ab53`(2026-06-17)。本书章节多写于更早 HEAD,故本篇逐条以当前源码为准重判。
- **方法**:对每条 ⚠️,①读本仓章节论断 → ②到 aevatar 源码定位 → ③判定 仍开放 / 已解决 / 语义变化 / 部分,给出当前路径证据 → ④给前瞻建议。
- **路径口径**:遵循本仓 v2 原则(不贴行号);只保留高价值文件级锚点,且均已验证在当前源码存在。
- **复核日志**:本次重审把上一版 18 条全部复核 + 新增多条;下次源码大改后应重跑本流程并更新文末基线。

⟦AI:AUTO-LOOP⟧
