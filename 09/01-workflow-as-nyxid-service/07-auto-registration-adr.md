# ADR(草案):已发布服务自动注册到 NyxID

> **状态** proposed(草案) · **owner** eanzhao · **关联** [09/01 方案](index.md)、落地方案见 [06](06-auto-registration-plan.md) · **目标落地** 接受后移植为 `~/Code/aevatar` 的 `docs/adr/` 下一个可用编号(当前下一个号 = 0035)。
>
> 本文件是 review 仓内的**决策草案**,不是 aevatar 的权威 ADR;aevatar 源码只读,落地时由 PR 携同实现一起进 `docs/adr/`。

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> 本 ADR 锁定"发布即自动被 NyxID 发现"的**决策与不变量**;详细落地步骤在 [06 落地方案](06-auto-registration-plan.md)。事实源脊柱:

- `src/Aevatar.Foundation.Abstractions/EventSourcing/ICommittedStatePublicationHook.cs` —— committed 事件 → 命令的写侧触发缝(先例 `src/platform/Aevatar.GAgentService.Infrastructure/Orchestration/ScriptingServiceRevisionRepublishHook.cs`)。
- `src/platform/Aevatar.GAgentService.Abstractions/Protos/service_definition.proto` —— `ExternalExposure` 契约,本 ADR 唯一演进的 proto。
- `src/platform/Aevatar.GAgentService.Core/GAgents/ServiceDefinitionGAgent.cs` —— `ExternalExposure` 唯一权威拥有者。
- `src/Aevatar.Capabilities/AevatarScopeAccessGuard.cs` —— invoke 端点 `scope_id` 鉴权门。
- NyxID(只读契约):`~/Code/NyxID/backend/src/handlers/services.rs`、`~/Code/NyxID/backend/src/handlers/proxy.rs`。

---

## Context

[03 注册与发现](03-register-and-discover.md) 确认:aevatar 没有任何代码会主动去 NyxID 注册自己;`ExternalExposure.nyxid_slug` 只是一个**本地指针**,可能悬空。"让 NyxID 发现 aevatar 服务"今天是一次**手工** `nyxid service add --custom` + 一份**手写** OpenAPI。这把"发布即被发现"卡成需要人介入的一跳,且留下三个缺口:protobuf↔OpenAPI 形状不匹配(G1)、注册桥缺失/本地悬空(G2)、`scope_id` 鉴权对不齐(G3)。

约束:**只能改 aevatar**(NyxID 只读其既有契约,不得新增/修改),且必须遵守主链路架构(actor 即业务实体、committed 事件驱动、读写分离、序列化 Protobuf、host 配置注入 FI-002)。

核心可行性事实(已对代码核实):

- **触发缝已存在**:`ICommittedStatePublicationHook` 在领域事件提交后、对外发布前被调用,`ScriptingServiceRevisionRepublishHook` 是"committed 事件 → 读 readmodel → 经命令端口派发"的活先例。注册无需新机制。
- **鉴权可 aevatar-only 闭环**:NyxID 代理对 `auth_method=bearer` 把存储凭证 **verbatim** 注入下游。于是 aevatar 可以**自签**一把带 `scope_id` claim 的 JWT 存进 NyxID,代理注入回来即自满足 `AevatarScopeAccessGuard`——NyxID 不必拥有 `scope_id` 概念。
- **身份边界已被路由限定**:NyxID `/api/v1/services` 拒绝 service-account 与 delegated token、无 admin 门 → 注册只能用 scope owner 的人类 token。

## Constraints(must honor)

- **Actor 即业务实体 / 事实源唯一**:回执是"已发布服务定义"的属性,必须由 `ServiceDefinitionGAgent` 单独拥有,**不新建注册协调 actor**。
- **committed 事件驱动 / 无 inline 副作用**:注册由 committed 激活事件经写侧钩子派发命令触发,**禁止**在发布请求/查询线程内同步调 NyxID。
- **self-continuation / 超时重试事件化**:出站调用完成只发自消息;退避 = `await → 发内部命令 → actor 消费`;回调线程不改 `State`。
- **读写分离**:"注册到哪一步 / 失败原因"由 readmodel 回答,不同步查 actor。
- **序列化 Protobuf**:新 state/command/event 一律 proto-first。
- **强类型内核**:`status` / `desired_spec_hash` / `credential_kid` 是核心控制流/轮转身份,建模为 typed proto field,不塞通用 bag。
- **FI-002**:NyxID 基址、签名密钥、base_url 由 host 配置注入,绝不硬编码;不出现具体 skill 名。
- **删除优先**:`ExternalExposure` 从被动指针**升级**为真回执,不保留双轨空壳。

## Decision

在已发布服务的生命周期里引入一条 **committed-事件驱动、actor 拥有的对账式自动注册**,把 `ExternalExposure` 从本地指针升级为**真注册回执**:

1. **触发**:`ServiceDeploymentActivatedEvent` 提交后,`ServiceExposureReconcileHook`(实现 `ICommittedStatePublicationHook`)按 opt-in 门控算出 `desired_spec_hash`,向 `ServiceDefinitionGAgent` 派发 `ReconcileExternalExposureCommand`;停用事件派 `RetireExternalExposureCommand`。
2. **状态机**:`ServiceDefinitionGAgent` 内 `Pending → Registering → Registered/Failed`,经 `INyxIdServiceRegistrationPort` 调 NyxID **既有** `POST/PUT/GET/DELETE /api/v1/services`;成功事件携带 NyxID **返回的** canonical slug + `service_id` 写回回执。
3. **G1 OpenAPI 自产**:新增匿名只读端点,把 `ServiceDefinitionSpec` 投影成 OpenAPI 3.1(带 `x-aevatar-tool`),作为 `openapi_spec_url` 传给 NyxID。
4. **G3 scope 凭证**:存进 NyxID 的 `credential` 是 aevatar **自签**的 scope-JWT(带 `scope_id` claim),注册体置 `forward_access_token=false`;invoke 端点接受 NyxID 与 aevatar-self 双 issuer。
5. **身份**:注册/轮转用 scope owner 的人类 NyxID token(瞬时、不入 grain state);存储凭证是自签 scope-JWT,两套凭证两条生命周期。

无 opt-in 的服务行为字节级不变(纯 opt-in 扩展)。

## Locked Rules

1. **单一拥有者**:`ServiceDefinitionGAgent` 是回执唯一权威;不引入注册协调 actor。
2. **committed 触发,非请求线程**:注册只由 committed 激活/停用事件经写侧钩子驱动。
3. **slug 只来自 NyxID 返回**:`nyxid_slug` 仅由 `ServiceRegistrationSucceededEvent` 写入;aevatar 绝不预占或猜测 slug ⇒ 悬空指针不可能。
4. **事件化退避**:重试/超时经自消息进 inbox;无 `Task.Run` 改状态、无 lock。
5. **显式对账**:重试命令带 `expected_attempt + desired_spec_hash`,与 `State` 不符即拒。
6. **幂等对账,不重复建**:`desired_spec_hash == registered_spec_hash` ⇒ no-op;漂移 ⇒ `PUT` 就地更新;半注册 409 ⇒ `GET` 解析既有 `service_id`。
7. **凭证不入持久态**:owner 人类 token 仅瞬时(AsyncLocal);proto/grain state 不落任何 secret;签名密钥仅以 host 配置/KMS 引用存在。
8. **读侧诚实**:注册 `status` + 失败详情只经 projection readmodel 暴露,携权威源版本;不同步查 actor、不 query-time replay。
9. **不静默吞失败**:永久失败落 `FAILED + last_error` 且 readmodel 可见;不 log-and-drop。

## Required Contract(`ExternalExposure` 演进)

> 仅摘录契约骨架(proto 是基本不变的核心抽象,折叠呈现)。完整命令/事件清单见 [06 §4](06-auto-registration-plan.md)。

<details>
<summary>service_definition.proto —— ExternalExposure 升级为状态机回执(additive、wire-safe)</summary>

```proto
enum ServiceRegistrationStatus {
  SERVICE_REGISTRATION_STATUS_UNSPECIFIED = 0;
  SERVICE_REGISTRATION_STATUS_PENDING     = 1;
  SERVICE_REGISTRATION_STATUS_REGISTERING = 2;
  SERVICE_REGISTRATION_STATUS_REGISTERED  = 3;
  SERVICE_REGISTRATION_STATUS_FAILED      = 4;
  SERVICE_REGISTRATION_STATUS_RETIRED     = 5;
}

message ExternalExposure {
  string nyxid_slug = 1;                        // 字段 1/2 保留,wire-safe
  google.protobuf.Timestamp registered_at = 2;
  ServiceRegistrationStatus status = 3;
  string nyxid_service_id = 4;                  // update/delete 的 key
  string desired_spec_hash = 5;                 // 想注册的(漂移探测)
  string registered_spec_hash = 6;             // 已注册的(== desired ⇒ no-op)
  string last_error = 7;                         // 脱敏,无 secret
  int32  attempt = 8;
  google.protobuf.Timestamp next_attempt_at = 9;
  string credential_kid = 10;                    // 存进 NyxID 的 scope-JWT 的 kid(轮转)
  bool   exposure_desired = 11;                  // 每服务 opt-in 结果
}
```

新增命令:`ReconcileExternalExposureCommand` / `RetireExternalExposureCommand` / `RunRegistrationAttemptCommand`(自消息)/ `RegistrationRetryDueCommand`(退避后自消息)。
新增 committed 事件:`ServiceRegistration{Requested,AttemptStarted,Succeeded,Failed,Retired}Event`。
</details>

## Consequences

- "发布即被发现"成为现实且**自动**:无手工 `nyxid service add`、无手写 OpenAPI;`external-exposure` 从悬空指针变成可验证回执。
- 信任边界正确:调用方只持 NyxID 凭证;aevatar 自签 scope-JWT 把"谁有权调这个 scope"收敛回 aevatar 自己的门。
- 新增成本诚实暴露:双 issuer / JWKS 是一个真子项目(Phase 2);OpenAPI URL 须公网可达;per-user 身份穿透仍不可 aevatar-only 解(见下)。
- 无 opt-in 的已发布服务零影响。

## Cutover Order

1. 接受本 ADR(proposed → accepted)。
2. **契约先行(Phase 0)**:`ExternalExposure` 升级 + 新命令/事件 + readmodel,build + proto 重生 + reducer/replay 测试。
3. **自动发现(Phase 1)**:OpenAPI 匿名端点 + `ServiceExposureReconcileHook` + `INyxIdServiceRegistrationPort`/适配器 + `NyxIdApiClient` 的 `/services` 方法,用 owner token 跑通上架/发现/回执/下架。
4. **凭证闭环(Phase 2)**:新认证项目 `Aevatar.Authentication.ScopeServiceTokens`(scope-JWT 铸币 + JWKS + 双 issuer + `credential_kid` 轮转)。
5. **硬化 + 文档(Phase 3)**:退避耗尽、`status` 可观测、opt-in 接进 bind 面;canon 更新回执模型;给 03/05 加 supersede 导读。

每步由 build + 定向测试 + 对应 `tools/ci/*guard*.sh` 门禁(见 [06 §11](06-auto-registration-plan.md))。

## Non-Goals

- 改 NyxID(任何形态)。
- per-user 身份穿透:代理调用在 scope 权威下跑,不是原始用户 NyxID subject;按人归属需 NyxID delegation token,**出界**,与 ADR-0018 边界一致。
- 无人值守注册/轮转(NyxID `/services` 拒 service-account + delegated token,须 owner 人类 token)。
- exactly-once:注册是 at-least-once + 幂等对账。

## Outcome

接受并实现后,一个 Studio 用户发布 workflow 即在 NyxID catalog 自动出现、带可拉取的 OpenAPI、`ExternalExposure` 是 NyxID 回执而非悬空指针,且(Phase 2 后)经 NyxID 代理的调用自满足 `AevatarScopeAccessGuard`——在 aevatar-only 边界内补齐 03/05 标红的"当中那一跳",并把无法 aevatar-only 解的 per-user 穿透诚实留给 ADR-0018 一族。
