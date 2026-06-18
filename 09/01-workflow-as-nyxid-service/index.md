# 方案 01 · 把 Studio workflow 发布成 NyxID 可调用服务

> 这是 [09 方案区](../index.md) 下的**第一份方案**。09 是一个收录跨 aevatar × NyxID 设计方案的区域,本方案是其中一份独立单元(自带 5 章 + 本概览)。

## 事实源/设计抽象(以 ~/Code/aevatar 为准)

> 本方案不是又一篇组件解读,而是一份**可落地的方案**:回答「我在 Studio 建了一个 workflow,怎么把它发布成外部能调用的服务,怎么让 NyxID 发现它,NyxID CLI / aevatar 自己的 nyxid tools 怎么调用它」。所有论断回指下面这条「发布—注册—发现—调用」主线的事实源脊柱(非正文骨架):

- `src/platform/Aevatar.GAgentService.Hosting/Endpoints/ScopeServiceEndpoints.cs`:scope service 的发布(`PUT .../binding`)、发现(`GET .../services`)、调用(`POST .../invoke/{endpointId}`)的统一前门。
- `src/platform/Aevatar.GAgentService.Abstractions/Protos/service_definition.proto`:`ServiceDefinitionSpec` 与 `ExternalExposure { nyxid_slug, registered_at }`——published service 与 NyxID 的**唯一**结构性耦合点。
- `docs/canon/nyxid-connected-service-tools.md`:aevatar 反向把一个 NyxID service 的 endpoint 动态注册成 LLM 工具、经 NyxID proxy 下发的权威口径。
- `~/Code/NyxID/backend/src/handlers/proxy.rs`:NyxID `POST /api/v1/proxy/s/{slug}/{*path}`——CLI 与 aevatar tools 最终命中的**同一个** wire 契约。

---

> **边界说明**:09 区域整体是 [SCOPE_EXTEND](../index.md) 新增(不在 [PLAN.md](../../PLAN.md) 原始 00–08 清单内)。本方案事实源跨两个只读仓库(`~/Code/aevatar` 与 `~/Code/NyxID`),NyxID 侧路径一律以 `~/Code/NyxID/` 前缀标注以示边界。

## 一句话结论(先看这个,再读细节)

这条链路**两头是真的、当中那一跳是手工的**:

- **aevatar 这半截是真的**:Studio workflow → member bind → 一个 `Workflow` 实现的 published service(带一个 `chat` endpoint)→ `POST /api/scopes/{scopeId}/members/{memberId}/invoke/{endpointId}` 可调用。整条发布生命周期在 aevatar 内部端到端跑通。
- **NyxID 这半截是真的**:任何 HTTP 下游服务都能被注册成 `DownstreamService`、被发现、被 `POST /api/v1/proxy/s/{slug}/{path}` 代理调用(凭证服务端注入,调用方永远看不到真 key)。
- **当中「发布即被 NyxID 自动发现」这一跳不存在**:没有任何 aevatar 代码会去 NyxID 注册自己;aevatar 侧的 `ExternalExposure.nyxid_slug` 只是**本地记下一个 slug 指针**,不发出任何对 NyxID 的调用。把已发布的 workflow 接到 NyxID 上,是一个**管理员手工动作**(`nyxid service add --custom` / `POST /api/v1/services`),再把 NyxID 回吐的 slug 写回 aevatar。

所以这份方案的正确读法是:**aevatar 负责"做出一个可调用的 HTTP 服务",NyxID 把它当成"又一个普通下游"代理出去**;两者之间没有专用集成,靠一次手工注册和一份手写 OpenAPI 把缝补上。后面每一章都按这个诚实口径展开,并把 ⚠️ 缺口显式标出来,不写"一键打通"的幻觉。

## 本方案怎么读

| 章节 | 回答的问题 | 现状 |
|---|---|---|
| [01 机制总览](01-mechanisms.md) | 当前可用的机制有哪些?两半各自是什么,在哪条线上相遇 | 两半现役;相遇点单一且真实 |
| [02 发布路径](02-publish-path.md) | aevatar 用哪个 API 把 Studio workflow 发布成可调用服务 | 现役;member-first bind → workflow 服务 |
| [03 注册与发现](03-register-and-discover.md) | 怎么让 NyxID 发现这个服务 | ⚠️ 手工注册;协议形状不匹配 + 鉴权缺口 |
| [04 三个调用入口](04-calling.md) | NyxID CLI / aevatar 自身 nyxid tools / 直连 REST·MCP 怎么调 | proxy 入口现役且三者同源 |
| [05 端到端方案](05-end-to-end-plan.md) | 完整时序 + 落地清单 + 哪些是真的/手工的/缺口 | 落地步骤可执行;缺口登记到 TODO |

## 这条方案的设计正当性

为什么是「aevatar 发布 HTTP 服务 + NyxID 当通用代理」,而不是「aevatar 和 NyxID 做一套点对点的服务注册协议」?因为 NyxID 的产品定位就是**凭证经纪 + 通用反向代理 + 发现 + 审计 + approval 通道**(见 `docs/canon/approval-quota-ledger.md`:NyxID 是 credential/proxy/approval/audit/service-discovery channel)。让 aevatar 暴露成普通 HTTP、让 NyxID 把它和 OpenAI/GitHub 一视同仁,意味着:调用方只持 NyxID 凭证、永不接触 aevatar 的真凭证;审计、approval、node routing 自动适用;aevatar 不需要长出一条「向某个特定身份提供商注册」的专用链。代价是:发布与注册是两个动作、要靠人接起来——这正是本方案反复强调的缺口。

⟦AI:AUTO-LOOP⟧
