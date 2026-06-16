# VoicePresence:语音在场(MiniCPM/OpenAI)+ 语音路由

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `src/Aevatar.Foundation.VoicePresence.Abstractions/`:`IVoiceTransport.cs`、`IRealtimeVoiceProvider.cs`、`IVoiceSessionCredentialStore.cs`、`IVoiceToolCatalog.cs`、`IVoiceToolInvoker.cs`、`IVoicePresenceRuntimeStateOwner.cs`、`Protos/voice_presence.proto`、`Sessions/`(lease/attachment/media-stream/capability-query ports)。
- `src/Aevatar.Foundation.VoicePresence/`:`Transport/WebSocketVoiceTransport.cs`、`Transport/WebRtcVoiceTransport.cs`、`Modules/VoicePresenceModule.cs`(EventModule capability)、`Hosting/VoicePresenceEndpoints.cs`(`MapVoicePresenceWebSocket` L19/27、`MapVoicePresenceWhip` L114/124、fail-closed `503` L186/247/256/273/281)、`Hosting/ActorOwnedVoiceRealtimeSession.cs`。
- `src/Aevatar.Foundation.VoicePresence.OpenAI/OpenAIRealtimeProvider.cs` 第 22 行:`IRealtimeVoiceProvider`(嵌套 `OpenAIRealtimeProviderSession` 第 339 行)。
- `src/Aevatar.Foundation.VoicePresence.MiniCPM/MiniCPMRealtimeProvider.cs` 第 21 行:`IRealtimeVoiceProvider`(MiniCPM-o demo-protocol adapter);`Internal/MiniCPMWaveCodec.cs`、`MiniCPMSsePayloadReader.cs`。
- `docs/canon/voice-presence-integration.md` 第 1-23 行:aevatar 作为 `/ws/voice` Brain;voice-presence 是外部 edge server,aevatar 持有全部 brain-side(realtime provider/persona/tools/turn lifecycle/NyxID-brokered creds)。
- `docs/adr/0025-voice-router-integration.md`(Accepted):policy-aware WS 边界;attach target 经 `ForwardToModel.tool_choice_hint.voice_attach_target`(被 ADR-0026 取代 target 编码);Voice 是 `VoicePresence` EventModule capability,挂到已有 actor —— 无独立 `VoiceSessionGAgent`。
- `docs/adr/0031-voice-edge-local-tools.md`(Accepted):cloud voice session 执行 LAN-only tool(Home Assistant/Frigate/ESP32);`VoiceFunctionCallRequested` → `VoicePresenceModule.ExecuteToolCallAsync` → `IVoiceToolInvoker` → `AgentToolVoiceInvoker` → `IAgentToolSource` → `IRealtimeVoiceProvider.SendToolResultAsync`。
- `docs/adr/0033-voice-provider-nyxid-ephemeral-broker.md`(proposed):移除静态 `OPENAI_API_KEY` 依赖,凭证经 NyxID ephemeral broker;无静态 key 时 `/ws/voice` fail-closed `503 voice_not_configured`。

---

## VoicePresence 是什么

aevatar 作为 `/ws/voice` 的 Brain(`docs/canon/voice-presence-integration.md`)。voice-presence 是外部 edge server,aevatar 持有全部 brain-side:realtime provider、persona、tools、turn lifecycle、NyxID-brokered creds。

四个项目:
- **Abstractions**:transport/provider/credential/tool/runtime-state ports + proto
- **VoicePresence**(runtime/host):WebSocket/WebRtc transport、`VoicePresenceModule`(EventModule capability)、fail-closed endpoints
- **OpenAI**:`OpenAIRealtimeProvider`(`:22`)
- **MiniCPM**:`MiniCPMRealtimeProvider`(MiniCPM-o demo-protocol,`:21`)

---

## 关键设计

**Voice 是 capability,不是独立 actor**(ADR-0025):`VoicePresence` 是 EventModule,挂到已有 actor —— 无独立 `VoiceSessionGAgent`。attach target 经 `ForwardToModel.tool_choice_hint.voice_attach_target`(ADR-0026 取代了旧 target 编码)。

**Edge local tools**(ADR-0031):cloud voice session 可执行 LAN-only tool(`VoiceFunctionCallRequested` → `IVoiceToolInvoker` → `IAgentToolSource` → `SendToolResultAsync`)。

**凭证经 NyxID**(ADR-0033 proposed):移除静态 `OPENAI_API_KEY`,经 NyxID ephemeral broker;无 key 时 `/ws/voice` fail-closed `503`。

**fail-closed**:所有端点在配置缺失时返回 `503`(`VoicePresenceEndpoints.cs` L186/247/256/273/281)。

---

## 验收

1. Voice 是独立 actor 吗?(不是,是 EventModule capability,挂到已有 actor)
2. voice 凭证从哪来?(NyxID ephemeral broker,非静态 key)
3. cloud voice 怎么执行 LAN tool?(ADR-0031,经 IVoiceToolInvoker→IAgentToolSource)
4. 配置缺失时端点返回什么?(503 fail-closed)

⟦AI:AUTO-LOOP⟧
