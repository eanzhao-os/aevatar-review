# Aevatar API 安全审计报告

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> **性质**:从 API 出发的安全审计 + OAuth2 加固。审计部分只读核对源码;加固部分**已实现并推送**到 aevatar `feature/integrate` @ `b7266fd08`(52 files,+3479/−168,build / test / guard 全绿)。
>
> **方法**:直读认证内核 + 多组并行 agent 覆盖端点授权 / 回调验签 / 密钥泄露 / 租户隔离 / 明文密钥打印;每条候选均打开源码确认,不凭 grep 下结论。
>
> 事实源脊柱(职责,非正文骨架):
>
> - `src/Aevatar.Authentication.Hosting/AevatarAuthenticationHostExtensions.cs` —— JWT Bearer + OIDC 装配、双 token 校验管道、fallback 授权策略。
> - `src/Aevatar.Authentication.ScopeServiceTokens/ScopeServiceTokenIssuer.cs` —— 本地自签 scope service token(HS256/RS256)签发。
> - `src/Aevatar.Mainnet.Host.Api/Responses/NyxIdIdentityAssertionValidator.cs` —— 教科书级 JWT 校验器(pin 算法 + require sub/jti),本次加固的推广样板。
> - `src/Aevatar.Authentication.Providers.NyxId/NyxIdClaimsTransformer.cs` —— `scope_id` 授权边界推导(waterfall + 已移除的泛化兜底)。
>
> **核对基线**:`feature/integrate`(审计基线 `b7266fd08` 之前;加固落在 `b7266fd08`)。

---

## 执行摘要

| 严重度 | 数量 | 是否阻塞 |
|---|---|---|
| CRITICAL | 0 | — |
| HIGH | 2 | 建议尽快修 |
| MEDIUM | 8 | 排期修 |
| LOW / 加固 | 6+ | 择机 |

**一句话结论**:主认证链路是合规的 OAuth2 资源服务器设计,**无致命漏洞**。真正的价值在两处"假防护/明文落库"的实打实问题(H1/H2),以及一个体系化的方向 —— 平台目前是**纯 bearer,没有任何持有证明(DPoP / mTLS / cnf 全仓为零)**,这是最贴合 OAuth2、也是收益最大的加固空间。代码里已有一个"把 token 绑定到请求体"的先例(`body_sha256`),可顺势推广成体系。

**明文密钥打印专项**:全库扫描结果为**零** —— 没有任何代码把我们持有的密钥值写进日志/控制台/异常。仅 6 处会记录上游 NyxID 的**错误响应体**(已截断、非 2xx 才记),属边缘项。

---

## 1. 当前安全设计全景(已核对)

### 1.1 认证主链路(mainnet = `Aevatar.Mainnet.Host.Api`)

- **JWT Bearer + OIDC discovery**,Authority = NyxID,`RequireHttpsMetadata=true` — `src/Aevatar.Authentication.Hosting/AevatarAuthenticationHostExtensions.cs:56`
- **Secure-by-default**:`FallbackPolicy` 要求已认证用户,公开端点须显式 `[AllowAnonymous]` — `:104`
- auth 只能在 **Development** 关闭,非 dev 强制开启 — `:144`
- 中间件:`UseAuthentication()` 只在注册了 scheme 时运行;共享 bootstrap 只 `AddAuthorization()`(无 fallback);`RedactingRequestLoggingMiddleware` 包整条管道 — `src/Aevatar.Bootstrap/Hosting/WebApplicationBuilderExtensions.cs:135,142,149`
- **两类 token 进同一校验管道**:① NyxID OIDC(RS256,JWKS 动态);② 本地自签 **ScopeServiceToken**。两套密钥并入同一 `IssuerSigningKeys`、两个 issuer 并入 `ValidIssuers` — `AevatarAuthenticationHostExtensions.cs:115` `ConfigureScopeServiceTokenValidation`
- `ScopeServiceProbeTokenProvider` 证明:宿主持签名密钥即可给**任意 `scope_id`** 铸 bearer(= 任意租户冒充)— `src/Aevatar.Mainnet.Host.Api/Status/ScopeServiceProbeTokenProvider.cs:38`

### 1.2 授权模型(设计得不错)

- **平台管理员**:`NyxIdPlatformAdminAuthorizer` 用调用方自己的 bearer 回查 NyxID `/users/me`,要求 role = admin/operator,fail-closed,只缓存放行不缓存拒绝 — `src/Aevatar.AI.ToolProviders.NyxId/NyxIdPlatformAdminAuthorizer.cs:44`
- **反 IDOR 原语**:`AevatarScopeAccessGuard` 把路由/请求体里的 `scopeId` 与 principal 上**唯一**的 `scope_id` claim 比对,不匹配 / 有歧义 / 缺失一律 403 — `src/Aevatar.Capabilities/AevatarScopeAccessGuard.cs:57`
- CQRS observatory / Workflow run observatory 的跨 scope 视图**确实**有 admin 门禁(fail-closed + 审计)

### 1.3 已具备的验签 / 防护能力(做得好 —— "对比签名"其实已有基础)

| 机制 | 位置 | 说明 |
|---|---|---|
| NyxID relay 回调全验签 | `NyxIdRelayAuthValidator.cs:171` | 手动 JWKS + RS256/ES256 + iss/aud/lifetime + **`body_sha256` 把 token 绑到具体请求体** + jti↔correlation |
| 设备回调 HMAC | `agents/Aevatar.GAgents.Device/DeviceEventEndpoints.cs:150` | HMAC-SHA256 + 常量时间比对 + 时间戳新鲜度 |
| Workflow webhook / 审批回调 HMAC | `WorkflowExternalApprovalCallbackEndpoints.cs:470`、`WorkflowWebhookIngressAuthenticator.cs:74` | 每绑定独立 secret + `FixedTimeEquals` + clock-skew |
| OAuth 回调 | `IdentityOAuthEndpoints.cs` | 签名 state-token(CSRF)+ PKCE |
| 身份断言校验器 | `src/Aevatar.Mainnet.Host.Api/Responses/NyxIdIdentityAssertionValidator.cs:96` | **pin `ValidAlgorithms=[RS256]`** + require sub/jti + 可选 service_id 匹配 —— 教科书级,应作为推广样板 |
| WS token 走子协议 | `src/Aevatar.Authentication.Hosting/WebSocketSubprotocolToken.cs` | token 不进 URL,镜像 k8s apiserver 模式 |
| CORS 生产 fail-closed | `WebApplicationBuilderExtensions.cs:216` | 从不 `AllowAnyOrigin + AllowCredentials` |
| 请求日志脱敏 | `RedactingRequestLoggingMiddleware` + `SensitiveQueryRedactor.cs:24` | 抹掉 query string 里的 16 个敏感 key |

---

## 2. 分级发现

### 2.1 🔴 HIGH

**H1 — Observatory readmodel 明文落密钥("脱敏"只是截断)**
`WorkflowArtifactFactBuilder.Redact()` 只按 2000 字符截断、不做任何掩码,≤2000 字符的 JWT/API key 原样写入 CQRS readmodel(`WorkflowRunInsightReportDocument`)并被 observatory UI 展示;`Content` / `ReasoningContent` **完全没有脱敏调用**。函数名与测试都自称"脱敏",实则不然。
- 证据:`src/workflow/Aevatar.Workflow.Core/WorkflowArtifactFactBuilder.cs:215`
- **修**:换成真正的密钥形态扫描(JWT / key 正则 + 关键字 JSON value 掩码),并在物化侧加纵深防御。

**H2 — ES ACL 护栏"自证清白",全租户共用一把 ES 凭证(含密钥索引)**
`AevatarOAuthClientEsAclStartupGuard` **根本不查 Elasticsearch**,只读一个 config 布尔 `GrantMatchesGrainEventStoreInternal`,而该布尔在代码里被**无条件写死为 `true`**。全仓无 `role_mapping` / document-level-security,租户隔离 100% 靠应用层 `scope_id` 查询过滤。更糟:ES 用**单一共享 Basic-auth**,存 OAuth client HMAC 密钥的 `aevatar-oauth-clients` 索引与普通租户索引**同一把凭证**。
- 证据:`agents/Aevatar.GAgents.Channel.Identity/Provisioning/AevatarOAuthClientEsAclStartupGuard.cs:28`;`src/Aevatar.Mainnet.Host.Api/Hosting/MainnetHostBuilderExtensions.cs:148`;`src/Aevatar.CQRS.Projection.Providers.Elasticsearch/Stores/ElasticsearchProjectionDocumentStore.cs:76`
- 影响:ES 凭证泄露或任一查询漏 scope 过滤 → 跨租户读 + 读到 OAuth 密钥索引,而"护栏"给出虚假安全感。
- **修**:让 guard 真查 ES `_security/role_mapping`,或至少把 OAuth 密钥索引拆到独立凭证 / DLS;应用层查询过滤加 CI 门禁。

### 2.2 🟡 MEDIUM

**M1 — 主 JWT 管道:audience 默认不校验 + 不 pin 算法 + 对称/非对称密钥同池**
`Audience` 默认空 ⇒ `ValidateAudience=false`;主管道无 `ValidAlgorithms`;HS256 scope 密钥与 RSA JWKS 并入同一 `IssuerSigningKeys` 且 `ValidIssuers` 合并。ScopeServiceToken 默认 HS256 意味着**校验方即可伪造**。信任边界被合并,一把 HS256 密钥泄露即可冒充任意 scope/issuer。
- 证据:`AevatarAuthenticationOptions.cs:22`、`AevatarAuthenticationHostExtensions.cs:63,115`、`ScopeServiceTokenOptions.cs:26`

**M2 — 纯 bearer,无持有证明**:全仓无 `DPoP` / `cnf` / `mTLS` / `ClientCertificate`。token 泄露后有效期内可任意重放。(详见第 4 节)

**M3 — `/rebuild` 运维端点用单一静态 token**:`POST /api/oauth/aevatar-client/rebuild` 重钉集群级 OAuth client,仅靠一个静态 `X-...RebuildToken`(常量时间比对但无轮换/过期/调用方审计身份)→ 单点。
- 证据:`agents/Aevatar.GAgents.Channel.Identity/Endpoints/IdentityOAuthEndpoints.cs:51`
- **修**:改走 `IPlatformAdminAuthorizer`。

**M4 — `/api/webhooks/nyxid-relay/diag` 是认证后的 token 中继 oracle**:任意已认证用户可用 `X-Test-Token` 让服务器转发到 NyxID LLM 网关并回显 500 字符。诊断端点被留在生产。
- 证据:`agents/Aevatar.GAgents.NyxidChat/NyxIdChatEndpoints.cs:48`
- **修**:admin 门禁或从生产构建移除。

**M5 — voice 第二条取 token 路径仍收 `?access_token=`**:`PolicyAwareVoiceEndpoints.ExtractCallerBearer` 没走子协议。日志泄露已被 redactor 兜住,但"token 不进 URL"的根因修复不完整。
- 证据:`src/Aevatar.Mainnet.Host.Api/Voice/PolicyAwareVoiceEndpoints.cs:350`

**M6 — connected-service 写操作 fail-open**:`IsDestructive` 默认 `false`,未标注的写操作在 `Auto` 模式下静默放行。
- 证据:`src/Aevatar.AI.ToolProviders.NyxId/ConnectedServices/ConnectedServiceProxyTool.cs:42`、`src/Aevatar.AI.Core/Middleware/ToolApprovalMiddleware.cs:77`
- 注:token 只发往 NyxID 固定 base URL,LLM 仅控制预注册 slug 内的子路径 → **无 confused-deputy**。

**M7 — `scope_id` 授权边界推导有兜底漏洞**:waterfall 末尾"任意 `*_id` claim"可成为租户边界。
- 证据:`src/Aevatar.Authentication.Providers.NyxId/NyxIdClaimsTransformer.cs:48`
- **修**:删掉泛化兜底,要求 issuer 明确背书的 scope claim。

**M8 — `jti` 要求存在但不查重放**:身份断言 require `jti` 却无 nonce 存储,重放保护名存实亡。
- 证据:`NyxIdIdentityAssertionValidator.cs:116`

### 2.3 🔵 LOW / 加固项

- **L1** 跨租户 channel-bot 状态可枚举泄露(`registrationId` 枚举出他人 bot 的 platform / 最近活跃)— `agents/channels/Aevatar.GAgents.Channel.NyxIdRelay/ChannelCallbackEndpoints.cs:220`
- **L2** 两处租户自服务端点带"Admin"命名却只做 own-scope 门禁(`ChatRoutePolicyAdminEndpoints` / `VoicePresenceCapabilityAdminEndpoints`)—— 今天正确,命名会诱发未来漂移
- **L3** Workflow webhook ingress 在 FallbackPolicy 后可达性语义不明确,应显式声明边界
- **L4** 两处对服务端内部 token 用 `==` 非常量时间比对(`NyxIdProxyTool.cs:280,343`,不可被外部精确探测,纵深防御项)

---

## 3. 明文密钥打印专项扫描

**扫描范围**:`src/`(含 `platform/`、`workflow/`)、`agents/`、`tools/`,排除 obj/bin,大小写不敏感。**技术**:1105 条 log/console 行 → 敏感标识过滤;插值密钥串 ∩ log/throw sink;多行检测器(密钥参数在下一行,读了 64 个候选);整对象 / `{@}` / header / serialize 日志;泛化占位符(`{Body}`/`{Response}`/`{Raw}`…)溯源到实际值;connection-string / `Authorization` header / PEM / signing-key 专项扫。**每条候选都打开源码确认**。

### 3.1 结论:零 HIGH/MEDIUM

**没有任何代码把我们持有的密钥值(JWT / access/refresh token / api-key / client-secret / password / HMAC 或签名密钥 / PEM / 连接串)写进日志、控制台、stdout/stderr 或被记录的异常。** 印证两个已部署修复(`7844b26cc` query 脱敏、`4d48f3947` WS 子协议 token)完好,且 auth/token/secret 代码路径只记录标识符 + 长度。

### 3.2 🔵 LOW / 边缘:上游 NyxID **错误体**回显进日志(非我方凭证)

以下记录的是上游 HTTP **错误**响应体(按契约是错误信封 / 描述);理论上一个行为异常的上游 4xx *可能*把提交值引回错误体。均已**截断**、均**仅非 2xx** 触发。

| `文件:行` | sink | 记录内容 | 严重度 |
|---|---|---|---|
| `agents/channels/Aevatar.GAgents.Channel.NyxIdRelay/NyxApiResponseHelper.cs:281`(`ExtractErrorDetail`)→ 抛于 `:23,:52`,由 `NyxLarkProvisioningService.cs:227` / `NyxTelegramProvisioningService.cs:140` 记录 | `LogWarning(ex)` | Nyx 错误信封 `body=` / `message=`(文档示例 `body=invalid app secret`) | LOW |
| `NyxApiResponseHelper.cs:326`(`TryRollbackAsync`) | `LogWarning {Response}` | 完整 Nyx rollback **错误**响应体 | LOW |
| `agents/Aevatar.GAgents.Channel.Identity/Broker/NyxIdRemoteCapabilityBroker.cs:207`(token-exchange)、`:146`(revoke)、`:308` | `LogError {Body}`(Truncate 256) | 仅上游**错误**体;成功体的 `access_token` 在 `:214` 解析,**从不记录** | LOW |
| `agents/Aevatar.GAgents.Channel.Identity/Provisioning/NyxIdDynamicClientRegistrationClient.cs:76` | `LogError {Body}`(Truncate 256) | DCR **错误**体;client 是 `token_endpoint_auth_method=none`(**不发 client_secret**),成功只记 `client_id` | LOW |
| `src/Aevatar.AI.LLMProviders.NyxId/NyxIdLLMProvider.cs:135` | `LogWarning(ex) {Body}` | 上游 LLM **错误**体 | LOW |
| `src/Aevatar.Studio.Hosting/NyxId/NyxIdLlmCatalogHttpClient.cs:109,132,167` | `LogWarning {Body}`(≤500) | NyxID catalog **错误**体(2xx 提前返回) | LOW |

**建议**(可选,纵深防御):对这些上游错误体记录前也过一层脱敏 / 只记状态码 + error code,避免上游 echo 提交值的边缘情形。

### 3.3 已验证安全的路径(抽样)

- **`RedactingRequestLoggingMiddleware` + `SensitiveQueryRedactor`**:替换 ASP.NET 原始请求日志,抹掉 query string 里 `access_token, token, id_token, refresh_token, api_key, key, client_secret, secret, password, code, sig, signature, bearer, authorization` 等值。**覆盖边界(设计使然,非 bug)**:只处理 **query string**,不碰 `Authorization` **header** 与 **body** —— 安全,因为(a)框架自身会打印 header/body 的请求日志已被压制,(b)无任何代码记录 Authorization header 或 body(已专项验证为空)。
- **Voice `/ws/voice` token**:从 `Sec-WebSocket-Protocol` 子协议取 bearer 进 `context.Token`,从不记录;legacy `?access_token=` 由 query redactor 兜。`VoiceConsolePage.cs` 里的 token 引用全是**客户端浏览器 JS**,非服务端日志。
- **ScopeServiceToken 签名密钥**:HS256 key / RS256 PEM 的每个 throw 都是校验消息("must be at least 32 bytes"、"requires Pem or PemPath"),**从不含密钥/PEM 值**。
- **OAuth HMAC 播种/轮换**(`AevatarOAuthClientGAgent.cs:169,298,689,703`):只记 "Seeded/Rotated HMAC key" 文本;`RandomNumberGenerator` 填充的密钥字节从不记录。
- **OAuth code/state**:authorization_code / state / code_verifier / id_token 被提取但从不记录;失败只记 `ErrorCode` / `CorrelationId` / `binding_id`。
- **NyxID token 遥测**(`NyxIdLLMProvider.cs:268`):只记 `tokenSource` + `accessToken.Length`。
- **启动期客户端接线**:connection-string / password / SASL 值到达任何 log/console/throw 的专项扫描**为空**。ES password → 仅 Base64 auth header;Garnet/Neo4j/Kafka 连接串传给 `Parse()`/config,从不记录;`ElasticsearchProjectionConfiguration.cs:82` `Console.Error.WriteLine` 只印"未配置"消息(store 名),无凭证。
- **无** `Authorization` header / 整个 `HttpRequestMessage` / `{@options}` / private-key / PEM / `SigningCredentials` 值到达任何 log sink(专项扫描均为空)。
- **无** `Console.Write` / `Debug.Write` / `Trace.Write` 打印密钥(page.cs 内嵌 HTML 之外仅 2 处 Console 写,均无凭证)。

---

## 4. 用 OAuth2 加强安全 —— 路线图

按"直接回应'对比签名' → 便宜高效 → 体系化"排序。

### 4.1 ① 发送者约束令牌 / 持有证明 —— "对比签名"的标准答案

**DPoP(RFC 9449)** —— 首选:
- 客户端持临时密钥对,每个请求带一个 **DPoP proof JWT**(header 放公钥 `jwk`,payload 放 `htm`=方法、`htu`=URL、`iat`、`jti`)
- access token 里带 `cnf.jkt` = 客户端公钥指纹
- aevatar 作为资源服务器校验四件事:proof 签名有效 → **proof 公钥指纹 == token 的 `cnf.jkt`**(这就是"对比签名")→ `htm/htu` 匹配真实请求 → `jti` 未重放
- 效果:token 被偷也没用,攻击者没有客户端私钥 → 直接消灭 M2 的重放面
- **切入点**:代码里已有雏形 —— `NyxIdRelayAuthValidator` 的 `body_sha256` 就是"把 token 绑到具体请求"的同一思路。可先复用 `NyxIdIdentityAssertionValidator` 的模式实现 DPoP proof 校验中间件;token 侧 `cnf` 需 NyxID 支持签发(平台级协作)。

**备选 mTLS 绑定令牌(RFC 8705)**:token 绑客户端 TLS 证书(`cnf.x5t#S256`),无需每请求签 proof,但要客户端证书基础设施。适合服务间调用。

### 4.2 ② 收紧 JWT 校验(便宜、当天可做)

- **打开 audience 校验**:给每个资源设 `Audience`,`ValidateAudience=true`(消 M1 一半)—— 别的 resource 的 NyxID token 无法拿到这里重放
- **pin `ValidAlgorithms`**:主管道显式限定(NyxID 走 `RS256`,scope token 走各自算法),照抄 `NyxIdIdentityAssertionValidator.cs:96`,防算法降级
- **按 issuer 绑定密钥**:用 `IssuerSigningKeyResolver` 让 NyxID token 只对 NyxID JWKS 验签、scope token 只对 scope 密钥验签,**拆开两个信任域**(消 M1 另一半)

### 4.3 ③ 自签 ScopeServiceToken:HS256 → RS256/ES256

改非对称后,校验方只持公钥、无法伪造;签名私钥只在签发方。代码已支持 RS256(`ConfiguredScopeServiceTokenKeyProvider.BuildRsaKey`),只是默认没用。

### 4.4 ④ 把已有的"验签"模式体系化

零散做对了很多(HMAC 常量时间、body 绑定、PKCE、state 签名)。抽一个**统一入站验签抽象**(`IInboundRequestSignatureValidator`),把 webhook HMAC + JWT + body_sha256 绑定收敛成一套,新入口默认接入,避免"某个新回调忘了验签"。

### 4.5 ⑤ 重放防护

给 `jti`(身份断言、未来 DPoP proof)加 TTL 内的 **seen-jti 缓存**(用现成 Garnet),拒绝重放(消 M8)。

### 4.6 ⑥ 顺手清理的授权项

`/rebuild` 换 `IPlatformAdminAuthorizer`(M3)、删/门禁 diag oracle(M4)、voice 第二路径走子协议(M5)、connected-service 写默认 fail-closed(M6)、`scope_id` 去掉泛化兜底(M7)。

---

## 5. 落地优先级(从便宜高价值开始)

1. **配置级(当天)**:设 `Audience` + `ValidateAudience=true`;pin `ValidAlgorithms`
2. **小改动(1–2 天)**:per-issuer 密钥绑定;ScopeServiceToken 默认 RS256;`jti` 重放缓存;`/rebuild` 换 admin 授权;diag oracle 下线
3. **中改动(1 周)**:修 `WorkflowArtifactFactBuilder` 真脱敏(H1);ES ACL guard 真查 ES / 密钥索引隔离(H2);统一入站验签抽象
4. **平台级(需与 NyxID 协作)**:DPoP 持有证明 —— 收益最大,消灭 bearer 重放面

---

## 附:覆盖范围与方法

- **分支**:`feature/integrate`,`git status` 干净(全程只读,无改动)。
- **认证内核**:直读 `Aevatar.Authentication.*`、`ScopeServiceTokens`、`NyxIdIdentityAssertionValidator`、bootstrap 管道、CORS、`grep DPoP/cnf/mTLS/ValidAlgorithms` 全仓。
- **端点授权**:枚举两 host 全部 `AllowAnonymous`、admin 授权模型、IDOR、自定义 token 校验。
- **回调验签**:NyxID relay / 设备 / Workflow webhook / OAuth callback,HMAC 常量时间比对与 JWT body 绑定。
- **密钥泄露 + 明文打印**:redactor 接线、readmodel 脱敏、下游 token 转发、secrets store、以及本报告第 3 节的全库明文密钥打印扫描。
- **租户隔离**:`scope_id` 强制、ES ACL guard、ES 凭证模型。
