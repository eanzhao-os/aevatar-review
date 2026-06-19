# 方案 03 · CC/Codex 经 NyxID 一句话在 aevatar 上 provision 定时监控 workflow 并实时观测

> 这是 [09 方案区](../index.md) 下的**第三份方案**。前两份分别讲「把 workflow 发布成 NyxID 服务」([方案 01](../01-workflow-as-nyxid-service/index.md))和「自有工具所有权」([方案 02](../02-ingress-tool-ownership/index.md));本方案把它们落到一个**完整的人类操作场景**:一个 Claude Code / Codex 会话,只凭一句自然语言 + 一个 NyxID 凭证,就在 aevatar 上**开出一个定时监控 workflow**,并能**近实时地看着它跑**。本方案是一个独立单元(本概览 + 1 章全链路 `01-end-to-end.md`)。

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> 本方案回答一个端到端问题:**为什么 CC/Codex 不需要给 aevatar 写任何专用 MCP server / 任何专用 agent,就能 (a) 把 aevatar 当 LLM 大脑、(b) 调 aevatar 管理面 provision 一个 workflow、(c) 在浏览器里看它实时跑**。三件事各自复用 aevatar 一条已有主链,互不耦合。所有论断回指下面这条「大脑 → reach → provision → 观测」主线的事实源脊柱(≤3 高价值锚点,非正文骨架):

- **入站当大脑(无状态 LLM 网关)**:`src/Aevatar.Mainnet.Host.Api/Messages/MessagesEndpoints.cs`(`/v1/messages` 明确是 stateless facade,非 agent 工具循环)、默认路由/模型唯一真相源 `src/Aevatar.AI.Abstractions/LLMProviders/LlmDefaults.cs`。
- **C1 一次调用 provision**:`src/Aevatar.Studio.Hosting/Endpoints/StudioProvisioningEndpoints.cs`(`POST /api/scopes/{scopeId}/provision-workflow`,组合 member create + bind + invoke)、`src/Aevatar.Studio.Application/Studio/Services/StudioWorkflowProvisioningService.cs`(轮询绑定、容忍最终一致)。
- **C2 平台级只读观测**:`src/workflow/Aevatar.Workflow.Infrastructure/CapabilityApi/WorkflowRunObservatoryEndpoints.cs`(scope 隔离 + OIDC PKCE + host 自带内联单页)、`src/workflow/Aevatar.Workflow.Application/Observatory/WorkflowRunObservatoryQueryService.cs`(复用 timeline/graph/current-state)。

> **边界说明**:09 区域整体是 [SCOPE_EXTEND](../index.md)(不在仓库 `PLAN.md` 原始 00–08 清单内)。本方案所有论断**已于 2026-06-19 在 aevatar mainnet 上活体跑通**(C1 已上线 `c80c77929` + 修复 `c46824af1`,C2 已上线 `bd9975c8a`);第 5 节附录的每条「live 实测发现」都是 **mock 单测测不出、只有活体才暴露**的,逐条标注现象与根因。

---

## 一句话结论(先看这个,再读细节)

> **CC/Codex 既是 agent、又只是个调用方;aevatar 既是大脑、又是被调用的下游。** 整个链路没有任何「aevatar 专用客户端」,而是三条已有主链各被复用一次:
>
> 1. **大脑**:CC/Codex 把 aevatar 的 `/v1/messages`(及 `/v1/chat/completions`、`/v1/responses`)经 NyxID 配成自己的 LLM 后端。这条入站是**无状态 LLM 网关**——它不替你跑工具循环,真正的 agent 是 CC 自己,工具来自 **CC 侧**的 NyxID MCP。
> 2. **reach**:CC 用 NyxID MCP 的 `proxy request aevatar api/...` 调 aevatar 管理面。aevatar 是一个**已注册的 NyxID 下游服务**(`Auth:none` + `identity_propagation_mode=jwt`),NyxID 给每个请求签一份身份断言(`sub` = user.id),aevatar 把它映射成 `scope_id`。**不需要自建 aevatar MCP server**。
> 3. **provision + 观测**:CC 用一条 `POST /api/scopes/{scopeId}/provision-workflow`(C1)把 member create + bind + invoke 三步收成一次调用;再打开 host 自带的只读 Observatory 单页(C2),凭浏览器 OIDC 登录,近实时看着这次 run 一步步推进。

这三条之所以能拼成「一句话开监控」,关键在于**它们彼此独立、各自复用主干**:大脑链不知道有 provision、provision 链不知道有观测、观测链只读不操作。下面的章节按这条主线展开,并把第 5 节「live 实测发现」逐条交代——那是这套设计在真机上才暴露出来的边界。

## 本方案怎么读

| 章节 | 回答的问题 | 现状 |
|---|---|---|
| [01 全链路](01-end-to-end.md) | 四段主链(大脑 / reach / C1 provision / C2 观测)各复用了什么、怎么拼起来;附 6 条 live 实测发现 | C1/C2 均已上线;附录发现均为活体暴露,逐条标注 |

## 这条方案的设计正当性

为什么是「三条独立主链各复用一次」,而不是「给 aevatar 做一个专用 CC 集成层」?四点,都对应仓库不动点与 CLAUDE.md 架构约束:

- **读写分离**:观测面(Observatory)**只读**——它只查 readmodel(timeline / graph / current-state),GET-only、query-ports-only,由 host 的只读门禁强制;而 provision 面(Studio)**只操作**,走命令侧。两者物理隔离,观测永远不会变成事实源。
- **reach 复用 NyxID 下游,而非自建 MCP(单一主干)**:NyxID 的产品定位就是凭证经纪 + 通用反向代理 + 发现 + 审计。让 aevatar 暴露成普通 HTTP 下游、由 NyxID 一视同仁地代理,意味着 CC 只持 NyxID 凭证、永不接触 aevatar 真凭证;不需要 aevatar 长出「向某个客户端提供 MCP」的第二系统。
- **C1 异步化符合「actor 不长阻塞 / continuation 化」**:绑定是一条慢异步流水线(实测 ~3 分钟才 bound)。C1 同步阻塞等绑定会撞网关 ~60s 超时,因此它必须**异步化**——超时即返回 `202`(member 已建、会继续绑),而不是把请求挂死。这正是「跨 turn 等待要 continuation 化、不在当前调用里硬等」的体现(详见 [01 §5 附录①②](01-end-to-end.md))。
- **入站当大脑是无状态网关**:把 agent 工具循环留在 CC 侧、aevatar 入站只做 LLM 转发,避免「两个 agent 抢一个工具循环」的语义双轨(与 [方案 02](../02-ingress-tool-ownership/index.md) 的所有权问题同源——一旦入站越界去跑工具,就会泄漏)。

⟦AI:AUTO-LOOP⟧
