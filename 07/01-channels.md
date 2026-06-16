# Channel Runtime:多通道适配(Lark/Telegram)+ 凭证路由/边界/入站骨干

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `agents/Aevatar.GAgents.Channel.Runtime/`:`ChannelBotRegistrationGAgent.cs`、`ConversationPipelineTurnContext.cs`、`ConversationDispatchMiddleware.cs`、`Conversation/`、`Middleware/`、`ShardLeader/`、`UserBinding/`。
- `agents/channels/Aevatar.GAgents.Channel.NyxIdRelay/`:`NyxIdRelayTransport.cs`、`ChannelCallbackEndpoints.cs`、`NyxIdRelayScopeResolver.cs`、`NyxLarkProvisioningService.cs`、`NyxTelegramProvisioningService.cs`、`NyxIdRelayConversationTypeMap.cs`。
- `agents/platforms/Aevatar.GAgents.Platform.Lark/`:`LarkMessageComposer.cs`、`LarkChannelNativeMessageProducer.cs`、`LarkStreamingCardShell.cs`、`LarkPayloadRedactor.cs`;`agents/platforms/Aevatar.GAgents.Platform.Telegram/`:`TelegramMessageComposer.cs` 等(渲染/组合 only)。
- `docs/adr/0008-channel-runtime-multi-token-routing.md`(superseded)、`docs/adr/0012-channel-runtime-credential-boundary.md`(accepted,L33 "ChannelRuntime is not a channel credential authority")、`docs/adr/0013-unified-channel-inbound-backbone.md`(accepted,L27-29 单一入站骨干)、`docs/adr/0014-interactive-reply-abstraction.md`(accepted,L34-39 per-turn collector)。
- `docs/canon/aevatar-channel-architecture.md`(236KB RFC,active)。

---

## 架构分层

Channel Runtime 分三棵树(`agents/` 下,非 `src/`):

| 树 | 职责 |
|---|---|
| `Channel.Runtime` | per-scope 配置 + 会话 pipeline GAgent |
| `Channel.NyxIdRelay` | 平台中立的 transport adapter(NyxId 中继) |
| `Platform.Lark` / `Platform.Telegram` | **渲染/组合 only**(不持凭证、不做路由) |

`aevatar.channels.slnf`(transport)+ `aevatar.platforms.slnf`(rendering)编码了这个分层切分。

---

## 凭证边界(ADR-0012)

`docs/adr/0012` 第 33 行明确:"ChannelRuntime is not a channel credential authority." 生产路径:`Lark → NyxID → Aevatar`(第 47 行)。direct-callback + Telegram-local-credential 路径已从支持契约移除(第 56-60 行)。

> **不变量**:零长期 secret material + NyxID 是唯一凭证经纪。所有凭证(channel token、voice key、LLM key)经 per-request caller NyxID token,不走本地静态 secret。

---

## 统一入站骨干(ADR-0013)

`docs/adr/0013` 第 27-29 行:单一入站 trunk `transport adapter → ChatActivity → ConversationGAgent → ChannelConversationTurnRunner`。Telegram 修正案(第 55-101 行):同 NyxIdRelay transport,`platform="telegram"`,`NyxIdRelayConversationTypeMap`(`private`→`DirectMessage`、`group`/`supergroup`→`Group`、`channel`→`Channel`)。

---

## 交互回复抽象(ADR-0014)

`docs/adr/0014` 第 34-39 行:per-turn `IInteractiveReplyCollector`(AsyncLocal)→ registry → composer → relay dispatcher。加一个平台的 card 支持是**加法**(composer + producer + register)。

---

## 验收

1. Channel Runtime 分几棵树?(Runtime/NyxIdRelay/Platform.Lark/Telegram)
2. ChannelRuntime 是凭证权威吗?(不是,ADR-0012,凭证经 NyxID)
3. 入站骨干是几条?(一条,trunk:adapter→ChatActivity→ConversationGAgent→TurnRunner)
4. 加平台的 card 支持是加法还是改法?(加法,ADR-0014)

⟦AI:AUTO-LOOP⟧
