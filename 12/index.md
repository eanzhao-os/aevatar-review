# 12 近 7 天问题复盘(2026-06-19 → 06-26)

> 这是从本周 **82 个 aevatar 会话**里收敛出的"我碰到的问题"**索引**:每条一句话根因 + 状态,详情指向第 10 章对应的深度复盘。**本页只做索引,不重复正文。**
>
> 核对基线:`feature/integrate`(部署线 origin @ `7d3c5a782`,2026-06-26)。⚠️ 本周一个反复踩的坑:**本地 checkout 落后部署线 21 个提交**,多条修复只在 origin、本地工作树没有 —— 下文"已修/仍开放"一律以 `origin/feature/integrate`(部署真相)为准。

---

## 索引(按主题)

### A · Lark/飞书机器人

| 问题 | 一句话根因 | 状态 | 详情 |
|---|---|---|---|
| 发给 Bot3 却 Bot2 回复 | NyxID 按 union_id 合并同人跨 app 私聊,回复走最早注册的 app;aevatar 入站/出站全程正确 | 非我方·外部 NyxID | [10/05 §1](../10/05-lark-delivery-layer-failures.md) |
| 回复截断成残片 | 一次性 `reply_token` 被长回合拖过期,最终 flush 拿不到票 | 真 bug·部分已修 | [10/05 §2](../10/05-lark-delivery-layer-failures.md) |
| bot 全程哑火 401 | `a2e9003ca` 删 scope 兜底,而回调 JWT 不带 scope_id → 100% `relay_scope_unresolved` | 已修(revert `105d95039`) | [10/05 §3](../10/05-lark-delivery-layer-failures.md) |
| 用 owner 身份而非 sender 调用 | "sender 优先、owner 兜底";未绑定 NyxID 的用户(≈全部)落 owner | 设计缺口·仍开放 | [10/06 §1](../10/06-lark-identity-and-authorization.md) |
| 资源授权降级 org-public | Bitable 默认精准授权请求者(拿不到才降级);Docx 故意组织可见 | Bitable 已修 / Docx by-design | [10/06 §2](../10/06-lark-identity-and-authorization.md) |

### B · 定时任务

| 问题 | 一句话根因 | 状态 | 详情 |
|---|---|---|---|
| 关灯定时漏一拍 | 重激活时 `OnActivate` 从 now 重算、跳过到期拍 | 已修(`ac325cc70`,含负向对照) | [10/07 §1](../10/07-scheduled-task-not-firing.md) |
| 大批 cron 冻结 | `#2224` Orleans/Garnet 脑裂:ConfigMap 漂移成 Localhost,reminder 投不出 | 环境/配置·门户修 | [10/07 §2](../10/07-scheduled-task-not-firing.md) |
| provision 注册失败 | 一次塞了两个凭证源,违反"恰好一个"校验 | 已修(`625e64c7e`) | [10/07 §3](../10/07-scheduled-task-not-firing.md) |

### C · 投影 / 观测台读侧

| 问题 | 一句话根因 | 状态 | 详情 |
|---|---|---|---|
| 全 scope 看不到自己的 run | 查询没传排序 → ES 退化 actor-id 序 + 先 Take | 已修(`6c15d4685`) | [10/08 §1](../10/08-observatory-read-side.md) |
| run success 却进不了观测台 | current-state document 任意 map key 撑爆 ES 1000 字段上限 | 已修(`f45025016`,#2321) | [10/08 §2](../10/08-observatory-read-side.md) |
| 节点一直"进行中" | 扇出父步骤被"收齐子节点"门控,缺一个子完成则永不收敛 | 真 bug·仍开放 | [10/08 §3](../10/08-observatory-read-side.md) |

### D · Studio 控制台

| 问题 | 一句话根因 | 状态 | 详情 |
|---|---|---|---|
| studio chat 全 500 | run-bind 覆写了 `workflow-definition:studio` 的 Definition binding doc | 已修(`fa2ff7223`,线上自愈) | [10/09 §1](../10/09-studio-console-three-traps.md) |
| 对话失忆 | `/api/chat` 无状态,记忆该由前端折叠注入 | 已修(`c087df8cf`) | [10/09 §2](../10/09-studio-console-three-traps.md) |
| 深链 chip 溢出 | observatory 筛选 chip 缺宽度上限/省略规则 | 已修(`a162d09e0`) | [10/09 §3](../10/09-studio-console-three-traps.md) |

### E · 语音

| 问题 | 一句话根因 | 状态 | 详情 |
|---|---|---|---|
| `/voice` 打断报"出错" | server 自动 cancel + aevatar 显式 cancel 竞态,benign 帧被当致命 | 已修(`159586d23`) | [10/10 §1](../10/10-voice-cancel-race-and-reconnect.md) |
| `/ws/voice` 断了不重连 | 单 socket 单生命周期,断即拆,无重连契约(issue #2159) | 仍开放 | [10/10 §2](../10/10-voice-cancel-race-and-reconnect.md) |

### F · NyxID 直连 LLM 入口

| 问题 | 一句话根因 | 状态 | 详情 |
|---|---|---|---|
| chat/completions 收不到回复 | 与 `/v1/responses` 共享 off-actor 底座,同根因 | 见 10/04 底座修复 | [10/11 §1](../10/11-nyxid-direct-llm-entry.md) · [10/04](../10/04-responses-llm-run-offactor-and-observation.md) |
| 入口不暴露我的 NyxID 服务 | 双重断点:facade 填 Empty + 工具集无路由引用 | 设计缺口·仍开放 | [10/11 §2](../10/11-nyxid-direct-llm-entry.md) |
| `/v1/responses` 四层 off-actor 故障 | ingress 校验 / grain 死锁 / sink 回环 / CorrelationId 路由 | 已修(四层) | [10/04](../10/04-responses-llm-run-offactor-and-observation.md) |
| 本地 agent 不认 aevatar 工具 / 自有工具泄漏进流 | 入口把自有 tool-call delta 透传进客户端流 | 见对应篇 | [10/02](../10/02-codex-shell-vs-aevatar-tools.md) · [10/03](../10/03-ingress-own-tool-stream-leak.md) |

### G · 周边工程(本轮未单独成篇)

| 问题 | 一句话根因 | 状态 |
|---|---|---|
| `.gitignore` 裸 `runs/` 吞掉源码目录 `Runs/` | 大小写不敏感盘(macOS)上 `runs/` 也匹配 `*/Runs/`,新源文件被静默 git-ignore,可提交出 build-breaking 缺文件 | 已知·待确认是否收窄为 `/runs/` 锚定 |
| `ornn_search_skills` 找不到组织共享 skills | 检索/发现口径未覆盖 ChronoAI 组织共享集(如 `sg-office-network`) | 优化请求·未深查 |

---

## 横切教训(本周反复踩)

1. **workflow 成功 ≠ 用户收到回复**。Lark 三例(10/05)workflow 全成功,坏在投递层;排查 channel bot 必须把"生成成功信号"与"投递成功信号"分开看。
2. **以部署线 origin 为准,别拿本地陈旧 checkout 当现状**。本地落后 origin 21 提交,多条修复文件本地不存在;判"已修/未修"用 `git merge-base --is-ancestor … origin/feature/integrate`,而非本地工作树。
3. **code 追出的根因是假设,跨外部边界更要 live trace 证实**。错投对象(10/05 A)、chat/completions 落点(10/11 §1)、Bitable 是否降级(10/06 §2)都需要一条线上 trace 才能从"机制成立"升到"该次实锤"。
4. **删冗余前先证明替代来源充分**。`a2e9003ca` 删 scope 镜像却假设"JWT 总带 scope_id",把 fail-closed 守卫退化成 100% 关闭(10/05 C)。
5. **边界归属要画清**。reply 目标选择属 NyxID(10/05)、reminder 身份确定性属配置(10/07)、会话记忆属前端(10/09)—— 把责任放对层,才知道"该不该在本仓库修"。

---

## 状态总表

| 性质 | 条目 |
|---|---|
| **已修复并部署** | Lark 全哑 401、关灯跳拍、provision 凭证、observatory 排序、ES 字段爆表、studio 500、对话失忆、chip 溢出、语音 cancel 竞态、`/v1/responses` 四层 |
| **仍开放(我方可修)** | reply_token 过期残片、observatory 节点卡进行中、`/ws/voice` 重连、直连入口不暴露 NyxID 服务工具 |
| **设计缺口 / by-design** | sender 未绑定落 owner 身份、Docx 默认组织可见、连接服务工具显式 opt-in |
| **非我方(外部 NyxID)** | 回复错投对象 |
| **环境/配置(非代码)** | `#2224` Orleans/Garnet 脑裂 |
