# 10 已知问题

> 诚实记录当前实现里**已确认、可复现**的问题与边界限制。每条都对照 `~/Code/aevatar` 源码核实根因(基线 `feature/integrate @ efaee423d`),给出**复现 → 根因 → 影响面 → 规避/修复方向**四段,并明确区分"按设计的限制"与"真正的 bug"。

| 篇 | 标题 | 一句话 | 性质 |
|---|---|---|---|
| [01](01-cli-lark-scope-isolation.md) | CLI 看不到 Lark bot 创建的 agent | NyxID token 里那一个 `scope_id` claim 把调用者钉死在单一 scope;Lark bot 跑在自己的 scope,个人 CLI 跨 scope 访问被 `AevatarScopeAccessGuard` 以 `403 SCOPE_ACCESS_DENIED` 拒绝 | 按设计的隔离 ⚠️ 缺可发现性 |
