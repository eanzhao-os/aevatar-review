# 10 已知问题

> 诚实记录当前实现里**已确认、可复现**的问题与边界限制。每条都对照 `~/Code/aevatar` 源码核实根因(基线 `feature/integrate @ efaee423d`),给出**复现 → 根因 → 影响面 → 规避/修复方向**四段,并明确区分"按设计的限制"与"真正的 bug"。

| 篇 | 标题 | 一句话 | 性质 |
|---|---|---|---|
| [01](01-cli-lark-scope-isolation.md) | CLI 看不到 Lark bot 创建的 agent | NyxID token 里那一个 `scope_id` claim 把调用者钉死在单一 scope;Lark bot 跑在自己的 scope,个人 CLI 跨 scope 访问被 `AevatarScopeAccessGuard` 以 `403 SCOPE_ACCESS_DENIED` 拒绝 | 按设计的隔离 ⚠️ 缺可发现性 |
| [02](02-codex-shell-vs-aevatar-tools.md) | 把 aevatar 当 model 套给 codex:shell 工具 vs 自有工具 | codex 是 shell-first 编码 agent;把 aevatar 当 model 时,LLM 在一次推理里可能 emit `shell` 调用让本机跑 `nyxid` CLI,而非用 aevatar 的 ornn 工具。入口原样透传 codex 的 system prompt、不替换 → aevatar 只有几行工具描述对抗,力量不对称 | 架构固有张力 ⚠️ 非 bug |
| [03](03-ingress-own-tool-stream-leak.md) | 自有工具调用被泄漏进客户端流(agentic 客户端当 model) | 即便 aevatar 在服务端选中并执行了自己的工具,`/v1/chat/completions` 仍把该 tool-call delta 无差别写进客户端 SSE;客户端没有该工具 → 回 `Tool not found`。泄漏在流式渲染层,与 forwarded/local 分桶无关。修复见 [09/02](../09/02-ingress-tool-ownership/index.md) | **真 bug,可修** ✅ |
| [04](04-responses-llm-run-offactor-and-observation.md) | `/v1/responses` off-actor LLM run 的执行与流式观察(四层故障复盘) | 同一个"60s 超时"症状叠了**四个独立根因**:① ingress 工具校验过严 → ② `#2271` off-actor 跑偏成 per-run 执行 grain 自死锁 → ③ executor sink 多此一举地 per-record 回读自己的事实(run 卡第 1 个 chunk)→ ④ dispatch 用 recordId 当 `CorrelationId` 致 committed 事实被观察投影器过滤、进不了客户端 hub。逐层修好(`f0408b9e`/`5ed080fa`/`b729e27c`/`82bd5d37`),线上 `你好` 4s 拿到完整响应 | **真 bug,四层修好 + 线上验证** ✅✅ |
| [05](05-lark-delivery-layer-failures.md) | Lark 机器人「收到却答不出」:投递层三类故障 | 回复错对象(NyxID 按 union_id 合并同人跨 app·非我方)/ 截断成残片(一次性 `reply_token` 被长回合拖过期)/ 全哑 401(`a2e9003ca` 删 scope 兜底·已 revert `105d95039`) | 混合:外部 / 真 bug 部分已修 / 已修 |
| [06](06-lark-identity-and-authorization.md) | Lark 机器人身份与授权 | 「sender 优先、owner 兜底」未绑定落 owner;授权侧 Bitable 默认精准授予请求者、Docx 故意组织可见 | 设计缺口 + 已修 ✅ |
| [07](07-scheduled-task-not-firing.md) | 定时任务为什么不触发 | 重激活从 now 重算跳过到期拍(`ac325cc70`)/ Orleans-Garnet 脑裂冻结(配置非代码)/ provision 塞两个凭证源违反「恰好一个」(`625e64c7e`) | 真 bug 已修 + 环境 |
| [08](08-observatory-read-side.md) | 观测台看不到我的 run / run 状态不对 | 查询没传排序退化 actor-id 序(`6c15d4685`)/ current-state 任意 map key 撑爆 ES 1000 字段(`f45025016`)/ 扇出父步骤被「收齐子节点」门控致节点永卡进行中 | 两修一开放 |
| [09](09-studio-console-three-traps.md) | Studio 控制台三坑 | run-bind 覆写 `workflow-definition:studio` 的 Definition doc 致 500(`fa2ff7223`)/ 对话失忆(前端 `c087df8cf`)/ chip 溢出(`a162d09e0`) | 真 bug 已修 + 前端 ✅ |
| [10](10-voice-cancel-race-and-reconnect.md) | 语音 `/voice` 与 `/ws/voice` | 打断时 server 自动 cancel 与显式 cancel 竞态、benign `response_cancel_not_active` 被当致命(`159586d23`)/ `/ws/voice` 无重连(#2159) | 已修 + 仍开放 |
| [11](11-nyxid-direct-llm-entry.md) | NyxID 直连 LLM 入口 | chat/completions 与 `/v1/responses` 共享 off-actor 底座(同 04)/ 直连入口双重断点不暴露 NyxID 服务工具 | 交叉引用 + 设计缺口 |

> 另见 [09/03 全链路附录(§5 live 实测发现)](../09/03-provision-and-observe-via-nyxid/01-end-to-end.md)——CC/Codex 经 NyxID provision + 观测 workflow 时活体暴露的 6 条发现(binding 读模型最终一致曾 `500`、绑定慢异步流水线撞网关 `499`、serving revision 未自动激活、`llm_call` 需注入 caller NyxID token、demo run 验证 C2、`WorkflowExecutionCurrentStateDocument` ES 字段超限),均为 mock 单测测不出、只有活体才暴露,逐条标注根因。
