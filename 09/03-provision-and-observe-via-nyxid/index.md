# 方案 03 · NyxID 下的 C1 Provision、C2 观测与 Team Member Automation Agent Key 验证

> 这是 [09 方案区](../index.md) 下的**第三份方案**。前两份分别讲「把 workflow 发布成 NyxID 服务」([方案 01](../01-workflow-as-nyxid-service/index.md))和「自有工具所有权」([方案 02](../02-ingress-tool-ownership/index.md))。本目录收拢两个相关但身份与凭证 contract 独立的验证单元:CC/Codex 经 NyxID 完成 C1 provision + C2 观测,以及 canonical Team Member Automation 的 scheduled Agent Key 生产闭环。

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> 本方案回答一个端到端问题:**为什么 CC/Codex 不需要给 aevatar 写任何专用 MCP server / 任何专用 agent,就能 (a) 把 aevatar 当 LLM 大脑、(b) 调 aevatar 管理面 provision 一个 workflow、(c) 在浏览器里看它实时跑**。三件事各自复用 aevatar 一条已有主链,互不耦合。所有论断回指下面这条「大脑 → reach → provision → 观测」主线的事实源脊柱(≤3 高价值锚点,非正文骨架):

- **入站当大脑(无状态 LLM 网关)**:`src/Aevatar.Mainnet.Host.Api/Messages/MessagesEndpoints.cs`(`/v1/messages` 明确是 stateless facade,非 agent 工具循环)、默认路由/模型唯一真相源 `src/Aevatar.AI.Abstractions/LLMProviders/LlmDefaults.cs`。
- **C1 一次调用 provision**:`src/Aevatar.Studio.Hosting/Endpoints/StudioProvisioningEndpoints.cs`(`POST /api/scopes/{scopeId}/provision-workflow`,成功统一 `202`)、`src/Aevatar.Studio.Application/Studio/Services/StudioWorkflowProvisioningService.cs`(admit → resolve/create member → accept bind → optional ensure schedule,不 poll、不 direct invoke)。
- **C2 平台级只读观测**:`src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/WorkflowRunObservatoryEndpoints.cs`(默认 scope 隔离 + OIDC PKCE + host 自带内联单页;`45c1bd208` 起平台管理员可经 `IPlatformAdminAuthorizer` 显式跨 scope)、`src/workflow/Aevatar.Workflow.Application/Observatory/WorkflowRunObservatoryQueryService.cs`(复用 timeline/graph/current-state)。

> **边界说明**:09 区域整体是 [SCOPE_EXTEND](../index.md)(不在仓库 `PLAN.md` 原始 00–08 清单内)。2026-06-19 的 mainnet 活体执行验证了当时的 C1/C2 链并暴露 6 条问题;当前 C1 已演进为 `4e0def2` 的 non-blocking contract,本次只按源码重核,没有借 Agent Key canary 冒充 C1 复测。2026-07-24 完成的是独立 canonical Team Member Automation Agent Key audited canary(带一次性 provenance exception)与 operator-attested functional repeat;2026-07-26 又在 code-owned projection repair 后完成真实 wall-clock cron canary,见 [02](02-scheduled-agent-key-production-canary.md)。

!!! warning "两条 schedule surface 不可混同"
    [02](02-scheduled-agent-key-production-canary.md)验证的是 canonical Team Member Automation `/members/{memberId}/automations`。C1 `/provision-workflow` 是独立入口,当前只保存 `SenderNyxId`;每次 fire 由 dispatch 换一张短票,写入临时 Vault reference 后交给 workflow run 复用。02 的 dedicated Agent Key 结论不覆盖 C1。

---

## 一句话结论(先看这个,再读细节)

> **CC/Codex 既是 agent、又只是个调用方;aevatar 既是大脑、又是被调用的下游。** 整个链路没有任何「aevatar 专用客户端」,而是三条已有主链各被复用一次:
>
> 1. **大脑**:CC/Codex 把 aevatar 的 `/v1/messages`(及 `/v1/chat/completions`、`/v1/responses`)经 NyxID 配成自己的 LLM 后端。这条入站是**无状态 LLM 网关**——它不替你跑工具循环,真正的 agent 是 CC 自己,工具来自 **CC 侧**的 NyxID MCP。
> 2. **reach**:CC 用 NyxID MCP 的 `proxy request aevatar api/...` 调 aevatar 管理面。aevatar 是一个**已注册的 NyxID 下游服务**(`Auth:none` + `identity_propagation_mode=jwt`),NyxID 给每个请求签一份身份断言(`sub` = user.id),aevatar 把它映射成 `scope_id`。**不需要自建 aevatar MCP server**。
> 3. **provision + 观测**:CC 用一条 `POST /api/scopes/{scopeId}/provision-workflow`(C1)完成 capability admission、member resolve/create、异步 bind 与可选 schedule ensure;端点统一返回 `202`。随后打开 host 自带的只读 Observatory 单页(C2),凭浏览器 OIDC 登录,近实时观察 schedule 产生的 run。

这三条之所以能拼成「一句话开监控」,关键在于**它们彼此独立、各自复用主干**:大脑链不知道有 provision、provision 链不知道有观测、观测链只读不操作。[01](01-end-to-end.md) 按这条主线展开;[02](02-scheduled-agent-key-production-canary.md) 是同目录下另一个独立验证单元,验证 canonical Member Automation,不是 C1 credential 升级。

## 本方案怎么读

| 章节 | 回答的问题 | 现状 |
|---|---|---|
| [01 全链路](01-end-to-end.md) | 四段主链(大脑 / reach / C1 provision / C2 观测)各复用了什么、怎么拼起来;附录区分 2026-06-19 live 现象与当前凭证重核 | 当前 C1 contract 按 `4e0def2` 重核;历史 live 证据不冒充当前 C1 canary |
| [02 Scheduled Agent Key](02-scheduled-agent-key-production-canary.md) | 独立 canonical Member Automation 的 NyxID scope-plan、dedicated key、`last_used_at`、真实 cron、双轨吊销与恢复 | 首次功能/audit 闭环但 provenance 有 exception;第三次真实 cron `manual=false` 与 Agent Key transition 已验证,`6202` 仍有 observability gap |

## 这条方案的设计正当性

为什么是「三条独立主链各复用一次」,而不是「给 aevatar 做一个专用 CC 集成层」?四点,都对应仓库不动点与 CLAUDE.md 架构约束:

- **读写分离**:观测面(Observatory)**只读**——它只查 readmodel(timeline / graph / current-state),GET-only、query-ports-only,由 host 的只读门禁强制;而 provision 面(Studio)**只操作**,走命令侧。两者物理隔离,观测永远不会变成事实源。
- **reach 复用 NyxID 下游,而非自建 MCP(单一主干)**:NyxID 的产品定位就是凭证经纪 + 通用反向代理 + 发现 + 审计。让 aevatar 暴露成普通 HTTP 下游、由 NyxID 一视同仁地代理,意味着 CC 只持 NyxID 凭证、永不接触 aevatar 真凭证;不需要 aevatar 长出「向某个客户端提供 MCP」的第二系统。
- **C1 异步化符合「actor 不长阻塞 / continuation 化」**:绑定是一条慢异步流水线(历史活体曾约 3 分钟才 bound)。当前 C1 不再 poll 或 direct invoke,成功统一返回 `202`;可选 schedule 按 cron 到点尝试 dispatch,不会等待 binding readiness。调用方因此必须观察 binding/schedule/run,不能把 `202` 或 `RunImmediately` 当成功保证(详见 [01 §3 与 §5 历史附录](01-end-to-end.md))。
- **入站当大脑是无状态网关**:把 agent 工具循环留在 CC 侧、aevatar 入站只做 LLM 转发,避免「两个 agent 抢一个工具循环」的语义双轨(与 [方案 02](../02-ingress-tool-ownership/index.md) 的所有权问题同源——一旦入站越界去跑工具,就会泄漏)。

⟦AI:AUTO-LOOP⟧
