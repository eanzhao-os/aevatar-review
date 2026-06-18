# 端到端方案:从 Studio workflow 到 NyxID 可调用,逐跳 + 落地清单

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> 本篇把前四章合成一份**可执行方案**:一张端到端时序、一份逐步落地清单、一张"哪些是真的/手工的/缺口"的诚实矩阵、以及把缺口补成"一键打通"该做什么。事实源脊柱:

- `src/platform/Aevatar.GAgentService.Hosting/Endpoints/ScopeServiceEndpoints.cs` 与 `src/Aevatar.Studio.Hosting/Endpoints/StudioMemberEndpoints.cs`:aevatar 发布 + 调用前门(步骤 1–5、12)。
- `~/Code/NyxID/backend/src/handlers/proxy.rs` 与 `~/Code/NyxID/backend/src/handlers/services.rs`:NyxID 注册 + 代理(步骤 7–11)。
- `src/platform/Aevatar.GAgentService.Application/Services/ServiceCommandApplicationService.cs`:`external-exposure` 本地指针(步骤 6,⚠️ 不调 NyxID)。
- `src/Aevatar.AI.ToolProviders.NyxId/NyxIdApiClient.cs`:aevatar connected-service 工具与 CLI 命中同一 proxy 的证据。

---

## 1. 端到端时序(12 跳)

绿=已实现且端到端可跑;黄=手工/需人介入;红=缺口/假定。

```mermaid
%%{init: {"theme":"neutral"}}%%
sequenceDiagram
  autonumber
  participant U as Studio 用户
  participant AEV as aevatar API
  participant ADM as 管理员(手工)
  participant NYX as NyxID
  participant CLI as NyxID CLI / aevatar tool

  Note over U,AEV: 🟢 发布(aevatar 内部,真实)
  U->>AEV: 1. POST .../members 创建 member(铸 publishedServiceId)
  U->>AEV: 2. 在 Studio 编排 workflow YAML
  U->>AEV: 3. PUT .../members/{memberId}/binding → 202 bindingRunId
  AEV->>AEV: 4. 生命周期:Create→Prepare→Publish→Activate(Workflow 服务 + chat endpoint)
  AEV-->>U: 5. GET .../endpoints/{id}/contract:拿 InvokePath + SampleRequestJson

  Note over AEV,NYX: 🟡 接缝(手工,无自动桥)
  AEV->>AEV: 6. (可选) PUT .../external-exposure 记 nyxid_slug(⚠️ 纯本地,不调 NyxID)
  ADM->>NYX: 7. POST /api/v1/services 注册 base_url + 手写 OpenAPI(带 x-aevatar-tool)
  ADM->>NYX: 8. POST /api/v1/keys 连接凭证(nyxid service add --custom)→ canonical slug

  Note over NYX,CLI: 🟢 发现 + 调用(NyxID,真实,三入口同源)
  CLI->>NYX: 9. GET /proxy/services · /catalog/{slug}/endpoints(发现)
  CLI->>NYX: 10. POST /api/v1/proxy/s/{slug}/api/scopes/.../invoke/chat
  NYX->>AEV: 11. 注入凭证 + approval/审计 后转发(⚠️ 凭证须带 scope_id claim)
  AEV-->>CLI: 12. 202 + runId(或 :stream SSE);再 proxy .../runs/{runId} 观察
```

## 2. 落地清单(照着做就能跑通)

> 前提:你能拿到 aevatar 的 scope JWT、有 NyxID 账号(`nyxid login`)、且有人具备 NyxID 注册权限。

**A. 在 aevatar 发布(自助)**

1. `POST /api/scopes/{scopeId}/members`(若还没有 member)——拿到 `memberId` 与 `publishedServiceId`。
2. `PUT /api/scopes/{scopeId}/members/{memberId}/binding`,body `{ workflow: { workflowId, workflowYamls:[…] } }`——返回 `202 + bindingRunId`。
3. 轮询 `GET .../members/{memberId}/binding` 直到 `lastBinding` 出现。
4. `GET .../services/{serviceId}/endpoints/{endpointId}/contract`——记下 `InvokePath`、`Method=POST`、请求 `RequestTypeUrl`、`SampleRequestJson`。

**B. 把缝接到 NyxID(手工,一次性)**

5. **手写一份最小 OpenAPI**:`servers=[{url: https://<aevatar-host>}]`,一个 `POST {InvokePath}` operation,requestBody schema 用步骤 4 的样例,**给该 operation 标 `x-aevatar-tool: { enabled: true, name: invoke_chat }`**(否则 aevatar 的 connected-service 工具不会注册它)。把它 host 在一个 NyxID 能拉到的 URL。
6. 准备 NyxID 要注入给 aevatar 的**凭证**:见 §4 缺口 2——当前现实是**一把带目标 `scope_id` claim 的长期 JWT**(放进 `AEVATAR_SVC_TOKEN`)。
7. 注册 + 连接:
   ```bash
   nyxid service add aevatar --custom \
     --endpoint-url https://<aevatar-host> \
     --openapi-spec-url https://<spec-host>/openapi.json \
     --auth-method bearer --credential-env AEVATAR_SVC_TOKEN
   ```
   记下打印出来的 **canonical slug**(可能是 `aevatar-2`)。
8. (可选)`PUT /api/services/{serviceId}/external-exposure` 把 slug 写回 aevatar 作展示指针。

**C. 调用(自助,三入口任一)**

9. 发现:`nyxid proxy discover` / `nyxid catalog endpoints <slug>`。
10. 调用:`nyxid proxy request <slug> api/scopes/$SCOPE/members/$MEMBER/invoke/chat -m POST -d '{"payloadTypeUrl":"…","payloadJson":"{…}"}'`(`:stream` + `--stream` 看 SSE)。
11. 观察:`nyxid proxy request <slug> api/scopes/$SCOPE/services/$SERVICE/runs/$RUN -m GET`。
12. 或让 aevatar agent 调:在其 route policy 里开 `nyxid.connected_services` tool set,模型即可 tool-call `nyxid_<slug>__invoke_chat`(见 [04](04-calling.md))。

## 3. 诚实矩阵:哪些是真的 / 手工的 / 缺口

| 环节 | 状态 | 证据 / 说明 |
|---|---|---|
| 发布 workflow 为服务(步骤 1–4) | 🟢 真实,端到端 | `StudioMemberEndpoints` + `ScopeBinding…UpsertAsync` 生命周期 |
| 取调用契约(步骤 5) | 🟢 真实 | `.../endpoints/{id}/contract` 返回 InvokePath/Sample |
| aevatar 记 external-exposure(步骤 6) | 🟡 仅本地指针 | `ServiceCommandApplicationService` 不发 NyxID 调用;slug 可悬空 |
| **发布 → NyxID 自动注册/发现** | 🔴 不存在 | 无 aevatar→NyxID 注册代码;无 seeded "aevatar" 目录项 |
| 写 OpenAPI 让 operation 可发现(步骤 7) | 🟡 需手写 | aevatar 服务规格是 protobuf,不产出 OpenAPI |
| 注册 + 连接(步骤 7–8) | 🟢 真实但手工 | `POST /services` `/keys` 现役,但要人来做 |
| 发现(步骤 9) | 🟢 真实 | `/proxy/services`、`/catalog/{slug}/endpoints`、`nyx__discover_services` |
| 代理调用(步骤 10、CLI/tool/直连) | 🟢 真实,三入口同源 | 都命中 `/api/v1/proxy/s/{slug}/{path}` |
| 鉴权穿透(步骤 11) | 🔴 对不齐 | aevatar 要 `scope_id` claim;NyxID 只注入静态凭证、无 scope-JWT 签发;无 per-user 穿透 |
| 异步语义(步骤 12) | 🟢 真实(易误用) | 回 202+runId,需"提交+观察"两段式;NyxID 只透传 |

> 一句话总结:**两头是真的、当中那一跳是手工的**。如果(且仅当)有人按 §2-B 把 aevatar 注册成一个普通下游、连上一把带 `scope_id` claim 的凭证,则 CLI / aevatar tool / 直连三条调用立刻全可用——它们共享那条已完整实现的 NyxID proxy。但"我在 Studio 发布 → NyxID 自动认得它 → 任意用户用自己身份就能调"这句话,**逐字都未被代码支持**,不要这么对读者讲。

## 4. 把缺口补成"一键打通"该做什么(target-state)

登记到 [08/04 战术 TODO](../../08/04-todo-list.md) 性质的工作项:

1. **OpenAPI 自动产出**:让 aevatar 为已发布 scope service 暴露一份(proxy 友好的)OpenAPI(把 protobuf `ServiceDefinitionSpec` + endpoint type-url 投影成 OpenAPI operation,带 `x-aevatar-tool`)。补上后 §2-B 步骤 5 自动化、NyxID operation 发现非空。
2. **注册桥**:在 aevatar 发布生命周期里(或一个独立 reconciler)调用 NyxID `POST /api/v1/services` / `/keys` 完成注册,并把 NyxID 回吐的 slug 写进 `ExternalExposure`——让 `external-exposure` 从"本地指针"升级成"真实注册的回执"。⚠️ 须遵守 FI-002:NyxID base URL / 凭证策略由 host 配置注入,不硬编码。
3. **scope-aware 凭证签发**:设计 NyxID→aevatar 的身份穿透(例如 NyxID 用 RFC 8693 token-exchange 或 OAuth broker 为目标 scope 铸短期、带 `scope_id` claim 的 JWT 注入到 proxy 转发),替掉"一 scope 一把静态 JWT、无 per-user 身份"的现状。这是与 ADR-0018(per-user nyxid binding via oauth broker)同一族的问题,应在那条线里统一解。
4. **异步结果的 NyxID 侧约定**(可选):为"提交 + 轮询/SSE"两段式提供更顺手的封装,避免调用方误把 202 当成最终结果。

在 1–3 落地前,本方案的诚实形态就是 §2 那份"自助发布 + 一次手工注册 + 自助调用"的流程。

## 5. 这份方案为什么值得照它走(正当性)

- **它没有发明新协议**:复用 aevatar 既有的 published-service 发布链(member-first / ADR-0016)和 NyxID 既有的通用代理,缝只在"注册"一处,且那处用的是 NyxID 给所有下游的同一套 API。少一套专用集成,就少一处要长期维护的双轨。
- **它把信任边界放对了**:调用方(人或 aevatar agent)只持 NyxID 凭证,aevatar 的真凭证由 NyxID 注入;审计 / approval / node routing 在 NyxID 一处统一施加。一个**内网自托管的 aevatar host** 还能直接用 NyxID 的 **node proxy** 平面打穿防火墙(凭证留在你机器上)。
- **它对缺口诚实**:协议形状不匹配与鉴权穿透是真实的、当前未实现的缺口,本方案把它们显式标红并给出 target-state,而不是用"一键发布"掩盖。这正是仓库写作原则(诚实标注当前 vs 目标态、缺口登记 TODO)与不动点 FI-006(基于证据、显式暴露缺口)的要求。

## 验收

1. 完整路径是什么?**发布(aevatar member bind,真实)→ 手工注册(`nyxid service add --custom` + 手写带 `x-aevatar-tool` 的 OpenAPI,真实但需人)→ 发现/调用(NyxID proxy,真实,CLI/aevatar-tool/直连三入口同源)**。§2 是可照做的落地清单。
2. 哪些是真的、哪些是手工/缺口?见 §3 矩阵:两头(发布、代理调用)真实;当中注册一跳手工;"发布即自动被发现"与"scope_id 鉴权穿透"是缺口(🔴)。
3. 要做成"一键打通"还差什么?OpenAPI 自动产出、aevatar→NyxID 注册桥、scope-aware 短期凭证签发(并入 ADR-0018 一族)——见 §4,已按 target-state 登记。

⟦AI:AUTO-LOOP⟧
