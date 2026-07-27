# Issue 演进账本（2026-07-25 冻结成员）

> 上游仓库：`aevatarAI/aevatar`
>
> 上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`
>
> 批准成员：2026-07-25 快照的 **126** 个 open issues，以及关闭日期落在
> 2026-07-06 至 2026-07-25 的 **154** 个 closed issues，共 **280** 行唯一成员。

## 1. 成员是冻结的，不随 live GitHub 改变

本账本第 4、5 节的成员行是**本轮唯一的 issue 事实源**。Tasks 3–4 只对这些行做分类；
执行期间 live GitHub 的新增、关闭、重开只作为 drift telemetry 记录，**不得**增删任何成员行。
一个在快照后才关闭的 issue 仍然属于本快照的 `open` 队列；它之后的状态变化是演进证据，不是成员变更。

Issue 的 open / closed 状态**本身不证明实现状态**。分类必须回到冻结基线找实现、契约、测试或明确删除证据。

## 2. 成员恢复方法（可复核）

### 2.1 为什么需要恢复

设计批准发生在 2026-07-25（用户本地时区 `+08:00`）。执行开始于 2026-07-27，此时 live GitHub 搜索已经漂移：

| 观测时间 | `is:issue is:open` | `is:issue is:closed closed:2026-07-06..2026-07-25` |
|---|---|---|
| 批准快照 | `126` | `154` |
| 2026-07-27（progress.md 记录） | `128` | `161` |
| 2026-07-27（Task 1 执行时实测） | `138` | `161` |

计数漂移意味着**无法用计数直接重放批准集合**。先检索了可用的不可变原始快照来源：本仓库 Git 历史
（含所有分支与 `git log --all --diff-filter=A`）、workflow artifacts、`.superpowers/` 运行态、
本地临时输出与既有脚本产物 —— 均**没有**保存 2026-07-25 的原始 issue 成员列表。因此走 REST timeline 重建。

### 2.2 重建算法

`scripts/snapshot-upstream-issues.py --reconstruct-at <instant>` 实现：

1. 通过 `/repos/aevatarAI/aevatar/issues?state=all&per_page=100` 分页枚举**全部** issue（1535 条），
   按 `pull_request` 字段排除 PR（`is:issue` 语义）。
2. 对每个 issue 判定 cutoff 时刻的状态：
   - `created_at > cutoff` → 当时不存在，两个队列都不属于；
   - `updated_at <= cutoff` → cutoff 之后没有任何活动，当前状态即当时状态；
   - 否则拉取 `/issues/{n}/events` 并按时间重放 `closed` / `reopened`，取 cutoff 之前最后一个状态事件。
     末事件为 `reopened` 或无状态事件 → 当时为 open；末事件为 `closed` → 当时为 closed，
     且 `closed_at` 取该事件时间（而非可能被后续重开重关覆盖的当前 `closed_at` 字段）。
3. closed 队列再按窗口过滤：`2026-07-06T00:00:00Z <= closed_at <= min(2026-07-25T23:59:59Z, cutoff)`。

窗口语义（下界含当日 `00:00:00Z`、上界含当日 `23:59:59Z`）经过独立校准：以 `cutoff = 2026-07-25T23:59:59Z`
运行同一算法得到 `161`，与同日 live 搜索 `closed:2026-07-06..2026-07-25 = 161` **完全一致**，
说明重建使用的边界与 GitHub 搜索一致，不是自定义口径。

### 2.3 cutoff 是如何被唯一确定的

把 open 与 closed 两个计数都写成 cutoff 的函数，在 2026-07-23 至 2026-07-25 的**全部**状态事件边界上求值。
只有一个区间同时满足两个批准计数：

```text
[2026-07-24T15:23:48Z, 2026-07-24T19:23:10Z)   ->  open = 126, closed-in-window = 154
```

- 区间下界 `2026-07-24T15:23:48Z` 是 `#2961` 的创建时刻（open 从 125 变成 126）。
- 区间上界 `2026-07-24T19:23:10Z` 是下一个 issue 的创建时刻（open 变成 127）。
- 区间内**没有任何**状态事件，因此区间内任意时刻的**成员集合完全相同** —— 成员是唯一确定的，
  不依赖于在区间内如何取点。
- 相邻区间都不满足：`19:23:10Z` 之后 open = 127；`2026-07-24T20:10:04Z` 之后 closed = 155；
  2026-07-25 全天 closed >= 155。

本账本取区间内的 `2026-07-24T16:58:27Z` 作为 canonical cutoff。它不是任选值，而是本仓库提交
`5f6ed80 docs: design aevatar review restructure`（`2026-07-25 00:58:27 +0800`）的作者时刻 ——
即**批准设计被写下的那一刻**，落在唯一匹配区间内。它同时解释了"2026-07-25 快照"的日期口径：
批准日期是用户本地 `+08:00` 日期，对应的 UTC 时刻在 2026-07-24。

### 2.4 独立交叉校验

| 校验 | 期望 | 结果 |
|---|---|---|
| 计划 Task 4 断言 `#2954–#2957` 属于 open 队列（E5，只进 `12/05`） | 4 个都在 open | 通过（这 4 个在 `2026-07-25T15:17:16Z` 才被关闭，晚于 cutoff） |
| 计划 Task 12 引用的 ChatHistory / NyxIdChat / Profile 已落地 issues | 属于 closed 队列 | 18/18 通过；`#2847` 不在任一队列，经核实它是 **pull request**，本就被 `is:issue` 排除 |
| 计划 Task 8 引用的 Workflow issues `#2451`、`#2678`、`#2769`、`#2895` | 属于 closed 队列 | 4/4 通过 |
| 两队列交集 | `0` | 通过 |
| 唯一成员行总数 | `280` | 通过 |

### 2.5 复核方式

```bash
python3 scripts/snapshot-upstream-issues.py --repo aevatarAI/aevatar --state closed \
  --from 2026-07-06 --through 2026-07-25 --reconstruct-at 2026-07-24T16:58:27Z \
  --expect-count 154 --format markdown

python3 scripts/snapshot-upstream-issues.py --repo aevatarAI/aevatar --state open \
  --snapshot-date 2026-07-25 --reconstruct-at 2026-07-24T16:58:27Z \
  --expect-count 126 --format markdown
```

两条命令都必须以 exit 0 结束；任何计数偏离都会使脚本失败退出，而不是输出一个短少的队列。
重放逻辑、窗口边界、重复项、分页与标题中的 `|` 由 `bash scripts/tests/test-doc-checks.sh issue-snapshot`
与 `issue-replay` 两个 fixture 套件覆盖。

## 3. 分类口径

closed issue 分类（Task 3）：

| 分类 | 判定 |
|---|---|
| `landed-current` | 冻结基线存在对应实现且语义仍成立（必须给出 E1 路径） |
| `landed-superseded` | 曾经落地但当前已被替换或删除 |
| `design-only` | 只形成设计 / 共识，实现未进入冻结基线 |
| `ops-verified` | 关闭依据是部署 / canary / 恢复（E3，必须绑定 commit、镜像、日期、环境） |
| `duplicate/replaced` | 被另一 issue、PR 或契约替代 |
| `failed/abandoned` | 无落地证据或主动放弃 |
| `administrative` | 看板 / 自动 fork / 跟踪，无设计语义 |

open issue 分类（Task 4）：

| 分类 | 判定 |
|---|---|
| `confirmed-bug` | 可复现，当前行为与契约矛盾 |
| `security-debt` | 已被承认的临时安全妥协 |
| `missing-contract` | 当前模型缺少必要协议 / 读模型 / API |
| `proposal/dispute` | 架构提案或未决选择，永不进入 current 正文 |
| `ops-ux-test` | 运维、前端体验或测试稳定性 |
| `blocked/duplicate/tracking` | 依赖、看板、bot fork、重复 |

`classification` 列的初始值统一是 `unclassified`；`implementation_evidence` 与 `destinations` 初始为 `—`。
Tasks 3–4 负责把它们填满，并且不得新增或删除任何成员行。

## 4. 冻结成员：closed（154）

窗口：`closed_at ∈ [2026-07-06T00:00:00Z, 2026-07-24T16:58:27Z]`（窗口上界与 cutoff 取小）。

| snapshot_state | issue | title | created_at | closed_at | labels | url | classification | implementation_evidence | destinations |
|---|---|---|---|---|---|---|---|---|---|
| closed | #1948 | Fix local demo service serving activation | 2026-06-10T08:02:25Z | 2026-07-16T11:41:08Z | fkst-dev:enabled; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/1948 | unclassified | — | — |
| closed | #1969 | Support physical deletion of Studio members | 2026-06-10T12:04:48Z | 2026-07-09T09:42:56Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/1969 | unclassified | — | — |
| closed | #2006 | Fix scoped workflow first-edit draft identity merge | 2026-06-11T11:00:49Z | 2026-07-16T03:02:42Z | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2006 | unclassified | — | — |
| closed | #2082 | feat(frontend): Platform 导航 P0 任务化入口与概览 | 2026-06-15T04:12:23Z | 2026-07-14T02:20:50Z | 🚀 phase:pr-open; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2082 | unclassified | — | — |
| closed | #2091 | feat(frontend): Platform Overview 智能下一步入口 | 2026-06-15T07:18:42Z | 2026-07-14T02:20:41Z | crnd:human:auto; crnd:triage:resume-requested; crnd:phase:blocked; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2091 | unclassified | — | — |
| closed | #2103 | feat(studio/workflow-debug): show manual and scheduled member workflow run history | 2026-06-15T11:06:31Z | 2026-07-09T06:15:13Z | enhancement; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2103 | unclassified | — | — |
| closed | #2244 | Clarify Studio member bind async ACK and observable admission result | 2026-06-17T14:42:33Z | 2026-07-10T04:48:52Z | fkst-dev:enabled; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2244 | unclassified | — | — |
| closed | #2303 | Align Console NyxID login client with backend finalization | 2026-06-22T06:27:46Z | 2026-07-16T03:00:27Z | fkst-dev:enabled; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2303 | unclassified | — | — |
| closed | #2315 | Treat Ornn workflow YAML as templates with explicit mount/import into scope workflows | 2026-06-23T02:36:02Z | 2026-07-16T02:59:25Z | fkst-dev:enabled; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2315 | unclassified | — | — |
| closed | #2350 | Expose Lark-created scheduled agents in team automations UI | 2026-06-24T04:45:03Z | 2026-07-21T09:33:11Z | fkst-dev:enabled; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2350 | unclassified | — | — |
| closed | #2355 | Inbound Lark bot relay does not run the bound workflow/skill (routes to generic agent; use_skill tool-call leaks as text; message not passed) | 2026-06-24T08:22:35Z | 2026-07-13T09:00:17Z | — | https://github.com/aevatarAI/aevatar/issues/2355 | unclassified | — | — |
| closed | #2368 | Update Studio workflow publish flow to use save-and-bind API | 2026-06-25T03:10:35Z | 2026-07-09T12:55:53Z | fkst-dev:thinking; fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2368 | unclassified | — | — |
| closed | #2377 | NyxID proxy: all services return HTTP 402 'billing_not_configured (11301): billing wallet is missing' mid-session (worked minutes earlier; how to configure the wallet?) | 2026-06-25T10:10:47Z | 2026-07-13T07:14:13Z | — | https://github.com/aevatarAI/aevatar/issues/2377 | unclassified | — | — |
| closed | #2405 | 定时调用凭证：proto 收敛为 oneof + role（契约先行） | 2026-06-29T05:46:11Z | 2026-07-10T16:44:35Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2405 | unclassified | — | — |
| closed | #2406 | 定时调用凭证：校验下沉 application/domain 并对齐各入口 | 2026-06-29T05:46:13Z | 2026-07-11T00:10:39Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2406 | unclassified | — | — |
| closed | #2407 | 定时调用凭证：durable 降级为 reference，关闭通用 API raw token 入口 | 2026-06-29T05:46:15Z | 2026-07-11T00:59:26Z | crnd:lifecycle:managed; crnd:phase:closed; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2407 | unclassified | — | — |
| closed | #2408 | 定时调用凭证：fire 注入按 role 收敛，清理双轨与 legacy | 2026-06-29T05:46:17Z | 2026-07-13T08:07:21Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2408 | unclassified | — | — |
| closed | #2409 | 定时调用凭证：required-credential policy 与测试矩阵硬化 | 2026-06-29T05:46:19Z | 2026-07-13T04:35:55Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2409 | unclassified | — | — |
| closed | #2412 | Lark relay: message attachments not passed to skill agent as input_parts; replies truncated to first token | 2026-06-29T07:17:44Z | 2026-07-14T02:17:25Z | — | https://github.com/aevatarAI/aevatar/issues/2412 | unclassified | — | — |
| closed | #2451 | Workflow engine: tool_call reports success when its tool result carries an error (non-2xx / {"error":true}) — silent false-success across all workflows | 2026-06-30T04:59:16Z | 2026-07-21T09:56:48Z | — | https://github.com/aevatarAI/aevatar/issues/2451 | unclassified | — | — |
| closed | #2472 | Backend: Add Mission Wall scope/team latest workflow run feed | 2026-06-30T09:54:32Z | 2026-07-07T08:19:26Z | enhancement; backend-backlog; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2472 | unclassified | — | — |
| closed | #2475 | Backend: Add Mission Wall top status summary contract | 2026-06-30T10:21:28Z | 2026-07-07T08:19:18Z | enhancement; backend-backlog; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2475 | unclassified | — | — |
| closed | #2500 | Fix 404 return action SPA navigation | 2026-07-01T03:12:22Z | 2026-07-08T10:33:27Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:pr-open | https://github.com/aevatarAI/aevatar/issues/2500 | unclassified | — | — |
| closed | #2573 | Implement Chat MVP session creation and local history | 2026-07-01T07:41:06Z | 2026-07-07T08:14:02Z | fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2573 | unclassified | — | — |
| closed | #2589 | Design unified audit log for sensitive operations | 2026-07-02T06:39:06Z | 2026-07-06T02:27:27Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2589 | unclassified | — | — |
| closed | #2609 | Unify channel relay abstraction for AI-facing message I/O | 2026-07-06T06:02:52Z | 2026-07-07T02:47:05Z | fkst-dev:enabled; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2609 | unclassified | — | — |
| closed | #2611 | Backend console: split the 313KB single-file /admin asset, unify console page organization, inject host facts | 2026-07-06T07:48:27Z | 2026-07-06T14:15:46Z | enhancement; architecture; crnd:lifecycle:managed; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2611 | unclassified | — | — |
| closed | #2612 | Admin authorization: config-backed aevatar admin allowlist as the single source of truth | 2026-07-06T07:48:48Z | 2026-07-06T13:14:33Z | enhancement; crnd:lifecycle:managed; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2612 | unclassified | — | — |
| closed | #2617 | Refactor Nyx relay notification delivery to channel sender plugins | 2026-07-07T02:22:16Z | 2026-07-07T12:23:27Z | fkst-dev:enabled; fkst-class:background; fkst-dev:merged; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2617 | unclassified | — | — |
| closed | #2620 | code_execute returns HTTP 500 internal_error (1006) for every call after service recovery; same-run nyxid_proxy calls all succeed | 2026-07-07T08:07:10Z | 2026-07-13T06:18:40Z | — | https://github.com/aevatarAI/aevatar/issues/2620 | unclassified | — | — |
| closed | #2627 | Keep channel native delivery target free of platform-specific fields | 2026-07-08T02:46:01Z | 2026-07-08T07:24:53Z | fkst-dev:enabled; fkst-class:background; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2627 | unclassified | — | — |
| closed | #2629 | Fork of #2500: Fix 404 return action SPA navigation | 2026-07-08T03:18:03Z | 2026-07-08T03:21:26Z | — | https://github.com/aevatarAI/aevatar/issues/2629 | unclassified | — | — |
| closed | #2630 | Redirect missing Team member published-runs routes home | 2026-07-08T03:39:38Z | 2026-07-08T07:19:39Z | — | https://github.com/aevatarAI/aevatar/issues/2630 | unclassified | — | — |
| closed | #2632 | Refactor Lark outbound delivery behind platform boundary | 2026-07-08T03:50:39Z | 2026-07-16T11:40:30Z | fkst-dev:enabled; fkst-class:background; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2632 | unclassified | — | — |
| closed | #2633 | Fork of #2580: Harden channel-relay credential trust boundary (aevatar-side): strip persisted per-step credentials + gate human-only NyxID tools in relay turns | 2026-07-08T04:09:16Z | 2026-07-08T04:33:43Z | fkst-dev:enabled; fkst-class:expedite; fkst-dev:fixing | https://github.com/aevatarAI/aevatar/issues/2633 | unclassified | — | — |
| closed | #2638 | Mission Wall: 新增 workflow 首次执行出现在左侧列表后，右侧拓扑图未自动展示 | 2026-07-08T04:11:17Z | 2026-07-08T09:20:28Z | fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2638 | unclassified | — | — |
| closed | #2645 | FKST fix loop cannot parse review-result dedup with review loop suffix | 2026-07-08T06:28:22Z | 2026-07-08T06:29:21Z | — | https://github.com/aevatarAI/aevatar/issues/2645 | unclassified | — | — |
| closed | #2646 | Add Team Overview run actions and recent execution history | 2026-07-08T06:28:31Z | 2026-07-09T06:49:55Z | fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2646 | unclassified | — | — |
| closed | #2653 | 让 Lark workflow 附件下载使用入站 channel bot 的 provider slug | 2026-07-08T08:29:17Z | 2026-07-08T12:23:33Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2653 | unclassified | — | — |
| closed | #2663 | Trim explanatory copy from Team overview | 2026-07-08T10:01:24Z | 2026-07-09T06:45:30Z | fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2663 | unclassified | — | — |
| closed | #2666 | Allow Team Test entry selection before prompt entry | 2026-07-09T06:30:38Z | 2026-07-14T02:20:11Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2666 | unclassified | — | — |
| closed | #2667 | Fix long-running workflow NyxID token refresh | 2026-07-09T06:53:13Z | 2026-07-14T15:26:16Z | blocker; architecture; crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current; fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2667 | unclassified | — | — |
| closed | #2670 | Prevent repeated NyxID DCR from redirect URI drift | 2026-07-09T07:32:10Z | 2026-07-09T12:41:21Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2670 | unclassified | — | — |
| closed | #2673 | AgentRun 将图片 base64 持久化到 durable state，导致 projection 消息可能超过 Kafka 大小限制 | 2026-07-09T08:16:09Z | 2026-07-09T15:32:15Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2673 | unclassified | — | — |
| closed | #2675 | Lark skill-triggered workflow defaults to wait=stream and fails on missing durable reply credential | 2026-07-09T09:27:18Z | 2026-07-15T02:59:41Z | bug | https://github.com/aevatarAI/aevatar/issues/2675 | unclassified | — | — |
| closed | #2676 | Frontend: 定时任务创建前显式授权 dedicated Agent Key（Milestone 33 follow-up） | 2026-07-09T10:36:38Z | 2026-07-16T16:25:10Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:merged; crnd:milestone:current; fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2676 | unclassified | — | — |
| closed | #2678 | Studio workflow generator emits YAML rejected by platform parser | 2026-07-09T12:49:50Z | 2026-07-15T11:19:27Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2678 | unclassified | — | — |
| closed | #2682 | fkst-dev board | 2026-07-10T02:50:15Z | 2026-07-10T07:15:57Z | fkst-dashboard | https://github.com/aevatarAI/aevatar/issues/2682 | unclassified | — | — |
| closed | #2683 | Decouple SkillRunner outbound delivery from Lark transport | 2026-07-10T03:50:37Z | 2026-07-10T12:38:28Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2683 | unclassified | — | — |
| closed | #2684 | Replace Lark-specific delivery target fields with generic channel address model | 2026-07-10T03:50:39Z | 2026-07-14T06:18:46Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2684 | unclassified | — | — |
| closed | #2685 | Move Lark routed target details out of generic channel target resolver | 2026-07-10T03:50:41Z | 2026-07-10T11:24:50Z | fkst-dev:enabled; fkst-class:background; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2685 | unclassified | — | — |
| closed | #2686 | Generalize channel registration tool beyond register_lark_via_nyx | 2026-07-10T03:50:43Z | 2026-07-10T06:01:44Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2686 | unclassified | — | — |
| closed | #2688 | 定时调用凭证：修订 ADR-0037——durable 语义更正为 vault 引用（硬前置） | 2026-07-10T04:27:40Z | 2026-07-10T23:14:08Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2688 | unclassified | — | — |
| closed | #2689 | 定时调用凭证：vault 撤销/轮换基建（Garnet CAS Revoke + NyxID 撤销 outbox） | 2026-07-10T04:27:43Z | 2026-07-10T21:57:33Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2689 | unclassified | — | — |
| closed | #2690 | 定时调用凭证：agent key provisioning 与 issuer 最小权限收紧 + gagent 类 fire 注入 | 2026-07-10T04:27:47Z | 2026-07-10T21:04:06Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2690 | unclassified | — | — |
| closed | #2691 | 定时调用凭证：workflow handle 传递与逐步 vault 解析 + 泄漏守卫（>5min 主场景） | 2026-07-10T04:27:50Z | 2026-07-10T20:02:34Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2691 | unclassified | — | — |
| closed | #2692 | 定时调用凭证：secret 基础设施硬化（keyring 强制 fingerprintKey / 工具链 / runbook / canon） | 2026-07-10T04:27:53Z | 2026-07-10T16:30:55Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2692 | unclassified | — | — |
| closed | #2695 | Fix loading indicators missing animation | 2026-07-10T04:48:59Z | 2026-07-10T07:02:55Z | fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2695 | unclassified | — | — |
| closed | #2703 | Publish gate：修复 LocalSecretProtectionOptions NoKeychain 语义导致的 TEST_CMD 红 | 2026-07-10T07:30:10Z | 2026-07-10T10:58:58Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2703 | unclassified | — | — |
| closed | #2723 | fkst-dev board | 2026-07-13T08:19:40Z | 2026-07-21T02:49:16Z | fkst-class:background; fkst-dashboard; fkst-dev:tracking | https://github.com/aevatarAI/aevatar/issues/2723 | unclassified | — | — |
| closed | #2725 | Fix responsive clipping across Team console surfaces | 2026-07-13T09:11:23Z | 2026-07-13T20:38:02Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2725 | unclassified | — | — |
| closed | #2728 | 定时调用凭证：补齐 agent key 双轨撤销、失败补偿与 allowlist fail-closed | 2026-07-13T09:49:13Z | 2026-07-14T10:23:10Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2728 | unclassified | — | — |
| closed | #2731 | Remove SkillRunner lifecycle surfaces from scheduled automation | 2026-07-14T06:14:26Z | 2026-07-16T04:05:11Z | fkst-dev:enabled; fkst-class:background; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2731 | unclassified | — | — |
| closed | #2732 | Move external trigger admission off SkillRunnerGAgent | 2026-07-14T06:14:29Z | 2026-07-16T08:24:44Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merge-ready | https://github.com/aevatarAI/aevatar/issues/2732 | unclassified | — | — |
| closed | #2733 | Delete SkillRunnerGAgent runtime and legacy scheduled runner model | 2026-07-14T06:14:31Z | 2026-07-16T11:27:29Z | fkst-dev:enabled; fkst-class:background; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2733 | unclassified | — | — |
| closed | #2734 | Move GAgent auth flows onto generic identity and credential contracts | 2026-07-14T06:15:36Z | 2026-07-15T08:18:15Z | — | https://github.com/aevatarAI/aevatar/issues/2734 | unclassified | — | — |
| closed | #2735 | Remove standalone Lark authoring package | 2026-07-14T06:15:38Z | 2026-07-15T04:09:24Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2735 | unclassified | — | — |
| closed | #2736 | 定时调用凭证：修复 workflow Agent Key 的 DurableCallerCredentialRef 不变量 | 2026-07-14T07:19:37Z | 2026-07-14T11:39:30Z | bug; blocker; architecture; crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2736 | unclassified | — | — |
| closed | #2738 | Team Automation：将 scheduled credential lifecycle 扩展到 schedule actor | 2026-07-14T07:22:14Z | 2026-07-16T16:25:11Z | enhancement; architecture; crnd:lifecycle:managed; crnd:human:auto; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2738 | unclassified | — | — |
| closed | #2739 | Team Automation：提供 canonical command API 与 credential health current-state read model | 2026-07-14T07:23:47Z | 2026-07-16T16:25:08Z | enhancement; architecture; crnd:lifecycle:managed; crnd:human:auto; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2739 | unclassified | — | — |
| closed | #2742 | Frontend: Team Automations AgentKey consent UI 与 mock contract（可先做） | 2026-07-14T09:56:15Z | 2026-07-14T14:37:47Z | enhancement; crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2742 | unclassified | — | — |
| closed | #2743 | Frontend: Team Automations scoped AgentKey API 接入（blocked on backend contract） | 2026-07-14T09:56:56Z | 2026-07-16T16:25:10Z | enhancement; crnd:lifecycle:managed; crnd:human:auto; crnd:phase:merged; crnd:milestone:current; fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2743 | unclassified | — | — |
| closed | #2745 | Escalate blocked output obligation: state-output-obligation-timeout for #2732 | 2026-07-14T10:36:54Z | 2026-07-14T15:07:48Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2745 | unclassified | — | — |
| closed | #2747 | [Studio] Add transactional YAML editing to the Team member workflow editor | 2026-07-14T10:56:33Z | 2026-07-21T02:48:38Z | enhancement; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2747 | unclassified | — | — |
| closed | #2753 | [fkst-stability] 持续失败: identity.login.finalize (fp:7f51706b) | 2026-07-14T17:23:00Z | 2026-07-15T14:06:17Z | fkst-dev:enabled; fkst-dev:blocked; fkst-stability; signal:recurring-failure; severity:high | https://github.com/aevatarAI/aevatar/issues/2753 | unclassified | — | — |
| closed | #2755 | Fork of #2447: [channel][lark] No working path to run a workflow on an uploaded file: /workflow run needs the file on the command message (Lark sends files separately); skill/aevatar_invoke_team path drops attachments | 2026-07-15T05:18:14Z | 2026-07-15T05:27:15Z | — | https://github.com/aevatarAI/aevatar/issues/2755 | unclassified | — | — |
| closed | #2756 | Fork of #2592: [Epic] Platform audit trail: unified recording of security-relevant operations | 2026-07-15T05:18:44Z | 2026-07-15T05:27:18Z | — | https://github.com/aevatarAI/aevatar/issues/2756 | unclassified | — | — |
| closed | #2757 | Fork of #2699: foreach fan-out → aggregate is unusable: downstream code_execute can't read a foreach's aggregated output (+ broker size limit, no code_execute concurrency/~60s cold-start, undocumented output shape) | 2026-07-15T05:19:53Z | 2026-07-15T05:27:23Z | — | https://github.com/aevatarAI/aevatar/issues/2757 | unclassified | — | — |
| closed | #2758 | Fork of #2462: [Epic] Layered context architecture for agent system prompts: minimal stable kernel + host-extensible forced overlay | 2026-07-15T05:20:01Z | 2026-07-15T05:27:26Z | — | https://github.com/aevatarAI/aevatar/issues/2758 | unclassified | — | — |
| closed | #2759 | Fork of #2738: Team Automation：将 scheduled credential lifecycle 扩展到 schedule actor | 2026-07-15T05:20:27Z | 2026-07-15T05:27:30Z | — | https://github.com/aevatarAI/aevatar/issues/2759 | unclassified | — | — |
| closed | #2760 | Fork of #2580: Harden channel-relay credential trust boundary (aevatar-side): strip persisted per-step credentials + gate human-only NyxID tools in relay turns | 2026-07-15T05:20:33Z | 2026-07-15T05:27:34Z | — | https://github.com/aevatarAI/aevatar/issues/2760 | unclassified | — | — |
| closed | #2761 | Fork of #2386: [PQL][Aevatar][Workflow] Published workflow member cannot run because no draft steps are linked | 2026-07-15T05:21:00Z | 2026-07-15T05:27:38Z | — | https://github.com/aevatarAI/aevatar/issues/2761 | unclassified | — | — |
| closed | #2762 | Fork of #2358: /whatsapp-reply-draft <multi-line message>: only the first line is passed to the workflow (remaining lines dropped) | 2026-07-15T05:21:06Z | 2026-07-15T05:27:41Z | — | https://github.com/aevatarAI/aevatar/issues/2762 | unclassified | — | — |
| closed | #2763 | Fork of #2178: 接入外部系统的请求定义：固化交互契约（definition id + 字段映射 + 事件订阅方） | 2026-07-15T05:21:14Z | 2026-07-15T05:27:45Z | — | https://github.com/aevatarAI/aevatar/issues/2763 | unclassified | — | — |
| closed | #2766 | Remove Lark-specific semantics from GAgent-facing contracts | 2026-07-15T08:19:05Z | 2026-07-15T13:00:13Z | fkst-dev:enabled; fkst-class:background; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2766 | unclassified | — | — |
| closed | #2769 | Unify workflow YAML root schema ownership between parser and Studio | 2026-07-15T11:17:52Z | 2026-07-16T03:11:26Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2769 | unclassified | — | — |
| closed | #2772 | 物化 owner-scoped NyxID 授权事实 | 2026-07-15T17:00:59Z | 2026-07-16T06:37:07Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2772 | unclassified | — | — |
| closed | #2773 | 单一 plan、digest 与写侧重验证 | 2026-07-15T17:01:03Z | 2026-07-16T04:08:58Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2773 | unclassified | — | — |
| closed | #2774 | 原子迁移 issuer、Studio 与 Team UI | 2026-07-15T17:01:06Z | 2026-07-16T04:09:05Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2774 | unclassified | — | — |
| closed | #2776 | 单一 plan、digest 与写侧重验证 | 2026-07-15T17:09:14Z | 2026-07-16T16:25:08Z | crnd:human:auto; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2776 | unclassified | — | — |
| closed | #2777 | 原子迁移 issuer、Studio 与 Team UI | 2026-07-15T17:09:18Z | 2026-07-16T16:25:08Z | crnd:human:auto; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2777 | unclassified | — | — |
| closed | #2778 | Refactor Studio actor-backed ChatHistory to backend terminal append writes | 2026-07-16T03:03:18Z | 2026-07-16T04:39:57Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2778 | unclassified | — | — |
| closed | #2781 | Add managed_sandbox target and runtime-neutral Codex execution port | 2026-07-16T03:44:11Z | 2026-07-16T11:10:46Z | enhancement; architecture; fkst-class:expedite | https://github.com/aevatarAI/aevatar/issues/2781 | unclassified | — | — |
| closed | #2783 | Publish managed-sandbox codex_exec readiness workflow and setup skill | 2026-07-16T03:44:16Z | 2026-07-21T03:07:10Z | documentation; enhancement; fkst-class:expedite | https://github.com/aevatarAI/aevatar/issues/2783 | unclassified | — | — |
| closed | #2787 | Add explicit audit lifecycle, terminal outcomes, and CloudEvents-compatible export semantics | 2026-07-16T04:10:39Z | 2026-07-16T22:52:28Z | enhancement; architecture; fkst-dev:enabled; fkst-class:standard; fkst-dev:implementing | https://github.com/aevatarAI/aevatar/issues/2787 | unclassified | — | — |
| closed | #2789 | Add a first-class WorkOrder resource for authorized Team execution | 2026-07-16T04:11:59Z | 2026-07-23T17:13:53Z | enhancement; architecture; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2789 | unclassified | — | — |
| closed | #2791 | Add a registered extension model for Team detail tabs | 2026-07-16T04:13:17Z | 2026-07-16T18:52:40Z | enhancement; architecture; fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2791 | unclassified | — | — |
| closed | #2792 | Refactor Studio actor-backed ChatHistory to backend terminal append writes (clean reissue) | 2026-07-16T04:32:34Z | 2026-07-17T03:06:17Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2792 | unclassified | — | — |
| closed | #2797 | Remove workflow debug shortcuts from team cards | 2026-07-16T08:05:22Z | 2026-07-16T10:57:43Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2797 | unclassified | — | — |
| closed | #2804 | feat(nyxid-chat): add a server-owned agent profile and deterministic Ornn skill routing | 2026-07-16T09:26:44Z | 2026-07-22T19:02:20Z | enhancement; architecture; crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2804 | unclassified | — | — |
| closed | #2806 | Frontend: add NyxID service access review flow on dev | 2026-07-16T10:13:37Z | 2026-07-17T02:48:56Z | enhancement; fkst-dev:enabled; fkst-class:standard; fkst-dev:merged; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2806 | unclassified | — | — |
| closed | #2810 | scheduled_agent_creator one-shot outbound slug is not configurable via required_service_slugs | 2026-07-16T13:10:10Z | 2026-07-17T05:57:48Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2810 | unclassified | — | — |
| closed | #2811 | 外部依赖：NyxID 缺少 owner-scoped UserService 节点拓扑读取契约 | 2026-07-16T16:50:35Z | 2026-07-17T02:38:17Z | enhancement; blocker | https://github.com/aevatarAI/aevatar/issues/2811 | unclassified | — | — |
| closed | #2813 | Add immutable exact Ornn references | 2026-07-16T17:29:21Z | 2026-07-18T05:36:48Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2813 | unclassified | — | — |
| closed | #2814 | Compose fixed ordered prompt overlays | 2026-07-16T17:29:27Z | 2026-07-17T06:33:47Z | crnd:lifecycle:managed; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2814 | unclassified | — | — |
| closed | #2815 | Bind immutable profiles to conversations | 2026-07-16T17:29:33Z | 2026-07-18T06:19:28Z | crnd:lifecycle:managed; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2815 | unclassified | — | — |
| closed | #2816 | Enforce deterministic routing and tool policy | 2026-07-16T17:29:40Z | 2026-07-18T12:42:58Z | crnd:lifecycle:managed; crnd:human:auto; crnd:triage:resume-requested; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2816 | unclassified | — | — |
| closed | #2817 | Resume typed authorization handoffs safely | 2026-07-16T17:29:46Z | 2026-07-17T00:15:59Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2817 | unclassified | — | — |
| closed | #2818 | Provision and evaluate profile rollout | 2026-07-16T17:29:53Z | 2026-07-22T19:02:05Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2818 | unclassified | — | — |
| closed | #2824 | Unify API login and Lark data ownership scope | 2026-07-17T03:43:04Z | 2026-07-17T08:55:04Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2824 | unclassified | — | — |
| closed | #2828 | Add Studio query tools for teams, members, workflows, and schedules | 2026-07-17T06:35:48Z | 2026-07-20T08:55:39Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2828 | unclassified | — | — |
| closed | #2829 | 修复 Garnet SecretStore CAS 集成测试的稳定失败 | 2026-07-17T07:16:42Z | 2026-07-18T02:30:54Z | crnd:lifecycle:managed; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2829 | unclassified | — | — |
| closed | #2834 | 重构 `POST /api/chat` Conversation 契约：由后端拥有 `conversationId` 和 `turnId` | 2026-07-17T08:57:11Z | 2026-07-20T02:23:18Z | fkst-class:standard; fkst-dev:merge-ready | https://github.com/aevatarAI/aevatar/issues/2834 | unclassified | — | — |
| closed | #2839 | Close the Team-scoped connector authoring-to-runtime resolution loop | 2026-07-17T11:11:23Z | 2026-07-20T01:34:35Z | enhancement; architecture; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2839 | unclassified | — | — |
| closed | #2841 | Define the minimal actor-owned authorization handoff and resume contract | 2026-07-18T08:35:32Z | 2026-07-22T13:25:45Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2841 | unclassified | — | — |
| closed | #2842 | 落地单一 actor-owned profile turn catalog 与执行准入链 | 2026-07-18T12:52:11Z | 2026-07-18T22:52:06Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2842 | unclassified | — | — |
| closed | #2843 | 把窄 NyxID service tools 接入 route-owned catalog | 2026-07-18T12:53:28Z | 2026-07-21T00:36:56Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2843 | unclassified | — | — |
| closed | #2844 | 落地 turn-local profile catalog 与统一执行准入 | 2026-07-18T22:59:44Z | 2026-07-19T06:49:27Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2844 | unclassified | — | — |
| closed | #2845 | 把 profile turn authority 作为 actor-owned 单调 retry 事实 | 2026-07-18T23:01:40Z | 2026-07-21T00:44:05Z | crnd:lifecycle:managed; crnd:human:auto; crnd:phase:closed | https://github.com/aevatarAI/aevatar/issues/2845 | unclassified | — | — |
| closed | #2846 | 实施冻结的 turn-local catalog 39-path vertical slice | 2026-07-19T06:57:42Z | 2026-07-20T19:22:42Z | crnd:lifecycle:managed; crnd:phase:merged | https://github.com/aevatarAI/aevatar/issues/2846 | unclassified | — | — |
| closed | #2848 | Add a first-class HTTP Request workflow primitive with secret-backed authentication | 2026-07-20T01:50:13Z | 2026-07-21T02:22:50Z | enhancement; architecture; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2848 | unclassified | — | — |
| closed | #2850 | Lark tool context does not receive canonical owner_scope_id after PR 2826 | 2026-07-20T02:56:55Z | 2026-07-20T07:28:54Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merge-ready | https://github.com/aevatarAI/aevatar/issues/2850 | unclassified | — | — |
| closed | #2851 | 优化 AGENTS.md 中 NyxID 外部仓库检查规则的适用边界 | 2026-07-20T03:08:24Z | 2026-07-20T05:31:54Z | — | https://github.com/aevatarAI/aevatar/issues/2851 | unclassified | — | — |
| closed | #2855 | Frontend: disable Apply to draft after YAML apply | 2026-07-20T06:29:09Z | 2026-07-20T09:11:56Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2855 | unclassified | — | — |
| closed | #2856 | Chat 创建 workflow 前应确认所属 Team，禁止生成不可发现的独立 workflow | 2026-07-20T06:36:16Z | 2026-07-21T05:05:45Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2856 | unclassified | — | — |
| closed | #2861 | [bug][studio/backend] Studio 拒绝 Runtime 已支持的 roles[].allowed_tools | 2026-07-20T09:22:22Z | 2026-07-20T11:49:04Z | fkst-dev:enabled; fkst-class:expedite; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2861 | unclassified | — | — |
| closed | #2862 | Fix Lark sender scope fallback after NyxID rebinding | 2026-07-20T09:42:39Z | 2026-07-20T12:50:33Z | — | https://github.com/aevatarAI/aevatar/issues/2862 | unclassified | — | — |
| closed | #2866 | Improve YAML editor opening feedback | 2026-07-20T12:46:00Z | 2026-07-21T02:12:19Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2866 | unclassified | — | — |
| closed | #2869 | Fork of #2639: Fix Mission Wall workflow graph disappearing | 2026-07-20T13:43:10Z | 2026-07-21T02:11:54Z | — | https://github.com/aevatarAI/aevatar/issues/2869 | unclassified | — | — |
| closed | #2871 | feat(nyxid-chat): freeze actor-owned turn authority | 2026-07-21T00:55:32Z | 2026-07-21T18:24:26Z | crnd:lifecycle:managed; crnd:phase:merged; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2871 | unclassified | — | — |
| closed | #2872 | feat(nyxid-chat): freeze request-local NyxID service tools | 2026-07-21T00:55:50Z | 2026-07-22T19:01:52Z | crnd:lifecycle:managed; crnd:phase:closed; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2872 | unclassified | — | — |
| closed | #2873 | feat(studio): allow bound member runs to start without input | 2026-07-21T02:22:04Z | 2026-07-21T06:00:58Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2873 | unclassified | — | — |
| closed | #2874 | [backend][chat-history] Harden ownership, pagination, and idempotent create recovery | 2026-07-21T02:42:11Z | 2026-07-21T04:58:00Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:impl-failed | https://github.com/aevatarAI/aevatar/issues/2874 | unclassified | — | — |
| closed | #2876 | [backend][chat-history] Harden ownership, pagination, and idempotent create recovery | 2026-07-21T03:05:53Z | 2026-07-21T09:11:25Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2876 | unclassified | — | — |
| closed | #2885 | fix(console): 正确渲染 Chat 消息中的 Markdown 表格 | 2026-07-21T03:58:32Z | 2026-07-22T08:11:49Z | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2885 | unclassified | — | — |
| closed | #2888 | [backend][chat-history] Harden ownership, pagination, and idempotent create recovery | 2026-07-21T04:52:25Z | 2026-07-21T07:05:36Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:implementing; fkst-dev:blocked-on-dependency | https://github.com/aevatarAI/aevatar/issues/2888 | unclassified | — | — |
| closed | #2890 | 支持 Lark Channel 按会话和发送者路由到不同 Studio Member / 已发布 Workflow | 2026-07-21T06:14:19Z | 2026-07-21T07:31:47Z | fkst-dev:enabled; fkst-dev:hold; fkst-class:standard; fkst-dev:implementing | https://github.com/aevatarAI/aevatar/issues/2890 | unclassified | — | — |
| closed | #2891 | Chat 创建外部服务 Workflow 时应识别鉴权需求，并引导通过 NyxID Service 与 Tool call 接入 | 2026-07-21T07:54:36Z | 2026-07-22T03:02:29Z | — | https://github.com/aevatarAI/aevatar/issues/2891 | unclassified | — | — |
| closed | #2892 | Improve Workflow Studio canvas readability and editor polish | 2026-07-21T08:44:36Z | 2026-07-22T09:22:04Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2892 | unclassified | — | — |
| closed | #2893 | Stream committed NyxIdChat progress and type tool-card identity | 2026-07-21T09:52:45Z | 2026-07-21T15:31:29Z | — | https://github.com/aevatarAI/aevatar/issues/2893 | unclassified | — | — |
| closed | #2895 | [chat][workflow] 引入 typed External Capability Readiness，按 authority owner 选择 Connector/NyxID 并做 bind admission | 2026-07-21T09:55:48Z | 2026-07-22T03:02:32Z | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2895 | unclassified | — | — |
| closed | #2896 | [P0] Provision vault-backed per-user NyxID agent keys for internal managed codex_exec | 2026-07-21T10:00:01Z | 2026-07-22T05:40:12Z | enhancement; Target p0; security-debt | https://github.com/aevatarAI/aevatar/issues/2896 | unclassified | — | — |
| closed | #2897 | [P0] Run codex-runner through chrono-sandbox with NyxID-injected delegation | 2026-07-21T10:00:32Z | 2026-07-22T05:40:11Z | enhancement; Target p0; infrastructure; security-debt | https://github.com/aevatarAI/aevatar/issues/2897 | unclassified | — | — |
| closed | #2900 | Fix scheduled workflow NyxID catalog refresh for agent-key provisioning | 2026-07-21T10:42:14Z | 2026-07-22T02:10:46Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2900 | unclassified | — | — |
| closed | #2907 | Resolve owner LLM exact service identity from binding for schedules | 2026-07-22T02:53:59Z | 2026-07-22T03:03:43Z | — | https://github.com/aevatarAI/aevatar/issues/2907 | unclassified | — | — |
| closed | #2909 | Unify workflow schedule authorization through Studio member path | 2026-07-22T03:18:04Z | 2026-07-24T07:39:05Z | — | https://github.com/aevatarAI/aevatar/issues/2909 | unclassified | — | — |
| closed | #2913 | [Security][Chat] Scope 内可枚举全局 workflow，疑似越权可见 | 2026-07-22T05:53:04Z | 2026-07-22T18:05:18Z | bug; fkst-dev:enabled; fkst-class:expedite; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2913 | unclassified | — | — |
| closed | #2915 | [Backend][Chat] Workflow LLM chunks are not projected to SSE text deltas | 2026-07-22T06:12:26Z | 2026-07-23T02:37:27Z | bug; fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2915 | unclassified | — | — |
| closed | #2920 | [Backend][Chat History] 续聊只归档消息，未把历史上下文注入 Workflow 执行 | 2026-07-22T08:01:11Z | 2026-07-23T02:37:27Z | fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2920 | unclassified | — | — |
| closed | #2925 | fix(workflow): scope-owned workflow definitions leak into the global runnable catalog | 2026-07-22T08:44:29Z | 2026-07-22T18:05:15Z | bug; architecture | https://github.com/aevatarAI/aevatar/issues/2925 | unclassified | — | — |
| closed | #2926 | fix(console): Invoke 跳转 Workflow Studio 后丢失已发布 member 的 workflow draft | 2026-07-22T09:17:00Z | 2026-07-23T03:11:27Z | bug; fkst-dev:enabled; fkst-class:standard; fkst-dev:merged | https://github.com/aevatarAI/aevatar/issues/2926 | unclassified | — | — |
| closed | #2929 | Clarify Workflow Studio header action semantics | 2026-07-23T02:49:21Z | 2026-07-23T03:04:33Z | fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2929 | unclassified | — | — |
| closed | #2931 | Decouple Lark-specific relay prompt and channel context | 2026-07-23T08:24:07Z | 2026-07-24T07:39:37Z | — | https://github.com/aevatarAI/aevatar/issues/2931 | unclassified | — | — |
| closed | #2942 | Update console schedule queries to pass scope context | 2026-07-23T10:44:54Z | 2026-07-24T05:48:38Z | — | https://github.com/aevatarAI/aevatar/issues/2942 | unclassified | — | — |

## 5. 冻结成员：open（126）

状态：`2026-07-24T16:58:27Z`（即批准的 2026-07-25 `+08:00` 快照时刻）为 open。

| snapshot_state | issue | title | created_at | closed_at | labels | url | classification | implementation_evidence | destinations |
|---|---|---|---|---|---|---|---|---|---|
| open | #114 | feat: workflow primitives enhancement — learnings from Kestra orchestration model | 2026-04-06T05:08:48Z | — | backlog | https://github.com/aevatarAI/aevatar/issues/114 | unclassified | — | — |
| open | #192 | refactor(ai): migrate all IAgentTool implementations to AgentToolBase<TParams> | 2026-04-14T09:41:42Z | — | enhancement | https://github.com/aevatarAI/aevatar/issues/192 | unclassified | — | — |
| open | #198 | [Test] #146《前端产品重构 — AI Teams + Studio》QA 执行 Checklist | 2026-04-14T14:51:40Z | — | — | https://github.com/aevatarAI/aevatar/issues/198 | unclassified | — | — |
| open | #199 | [Test] #150《A0 测试网稳定 / Testnet Stable》QA CheckList | 2026-04-14T15:46:38Z | — | — | https://github.com/aevatarAI/aevatar/issues/199 | unclassified | — | — |
| open | #212 | [Risk][Studio] 多层 `overflow: hidden` 与固定高度叠加，页面在小窗口下存在滚动归属和内容可达性风险 | 2026-04-15T09:08:29Z | — | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/212 | unclassified | — | — |
| open | #219 | [Bug][Studio] Settings 中点击 `Add provider` 后无可见效果，新增 provider 被本地状态重置覆盖 | 2026-04-15T11:33:37Z | — | — | https://github.com/aevatarAI/aevatar/issues/219 | unclassified | — | — |
| open | #220 | [Bug][Studio] `脚本行为` 页面加载时请求 `/api/scopes/{scopeId}/scripts?includeSource=true` 返回 `400 Bad Request`，工作台无法正常获取 scope scripts | 2026-04-16T03:25:09Z | — | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/220 | unclassified | — | — |
| open | #221 | [Bug][Studio] 左侧导航与工作区切换不流畅，页面切换过程中存在阻塞感、目标不清和状态跳转不一致 | 2026-04-16T03:46:52Z | — | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/221 | unclassified | — | — |
| open | #222 | [Bug][Studio] Settings 中点击 `Add provider` 后无可见效果，新增 provider 被本地状态重置覆盖 | 2026-04-16T04:11:38Z | — | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/222 | unclassified | — | — |
| open | #225 | [Bug][Studio] 脚本行为页缺少显式的新建草稿与编辑入口，用户无法从当前页面完整创建并编辑 script draft | 2026-04-16T06:56:05Z | — | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/225 | unclassified | — | — |
| open | #227 | [Bug][Studio] 测试运行页按钮状态判断不一致：未开始时“停止”可点击但无效果，“重新运行”因提示词为空被提前禁用 | 2026-04-16T07:22:56Z | — | fkst-dev:enabled; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/227 | unclassified | — | — |
| open | #244 | [Feature][Bindings] BindingDto 补 invokeUrl/env/rate-limit/streaming 等字段，新增 :rotate | 2026-04-19T11:37:55Z | — | enhancement; backlog | https://github.com/aevatarAI/aevatar/issues/244 | unclassified | — | — |
| open | #250 | [Test Plan] Aevatar API — v1 API 集成测试覆盖 | 2026-04-20T08:37:56Z | — | — | https://github.com/aevatarAI/aevatar/issues/250 | unclassified | — | — |
| open | #251 | [Bug] API 设计待确认问题 — 8 项需后端团队答复 | 2026-04-20T09:29:03Z | — | question | https://github.com/aevatarAI/aevatar/issues/251 | unclassified | — | — |
| open | #285 | Add descriptor compatibility guard for legacy protobuf aliases | 2026-04-21T08:19:33Z | — | — | https://github.com/aevatarAI/aevatar/issues/285 | unclassified | — | — |
| open | #286 | Detect duplicate legacy TypeUrl aliases in ProtobufContractCompatibility | 2026-04-21T08:19:34Z | — | — | https://github.com/aevatarAI/aevatar/issues/286 | unclassified | — | — |
| open | #375 | [RFC] Aevatar 线上零 secret material — 从 Day One 演化到 capability-broker 边界 | 2026-04-24T06:10:27Z | — | auto-loop; phase9-auto-solve; 🔍 phase:design-solving; 🤖 human:auto-推进 | https://github.com/aevatarAI/aevatar/issues/375 | unclassified | — | — |
| open | #435 | [Blocker] Missing member contract and roster APIs block final Studio de-serviceId cleanup | 2026-04-27T06:44:23Z | — | phase11-not-eligible | https://github.com/aevatarAI/aevatar/issues/435 | unclassified | — | — |
| open | #481 | [Bug] [Aevatar] 自然语言请求“帮我查最近 24 小时 Lark 里提到我的消息”后无回复、无进度、无错误提示 | 2026-04-28T07:06:35Z | — | — | https://github.com/aevatarAI/aevatar/issues/481 | unclassified | — | — |
| open | #1016 | Studio Team-First Console 支持 Static GAgent 协作 | 2026-05-25T07:17:57Z | — | fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/1016 | unclassified | — | — |
| open | #1665 | [refactor-design][visible-supervisor] Studio member lifecycle recovery guidance | 2026-06-02T03:25:36Z | — | auto-loop; phase9-auto-solve; 👀 phase:reviewing; 🤖 human:auto-推进; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/1665 | unclassified | — | — |
| open | #1667 | [refactor-design][visible-supervisor] Governance exposure and retired-state affordance clarity | 2026-06-02T05:01:09Z | — | auto-loop; phase9-auto-solve; 🚀 phase:pr-open; 👀 phase:reviewing; 🤖 human:auto-推进 | https://github.com/aevatarAI/aevatar/issues/1667 | unclassified | — | — |
| open | #1676 | [refactor-design][visible-supervisor] Deployments release action handoff clarity | 2026-06-02T05:44:01Z | — | auto-loop; phase9-auto-solve; 🚀 phase:pr-open; 👀 phase:reviewing; 🤖 human:auto-推进; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/1676 | unclassified | — | — |
| open | #1696 | [refactor-design][visible-supervisor] Services and Scopes runtime affordance clarity | 2026-06-02T12:19:44Z | — | auto-loop; phase9-auto-solve; ⏸️ phase:blocked; 🤖 human:auto-推进; fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/1696 | unclassified | — | — |
| open | #1899 | Clarify draft-run vs member invoke semantics and simplify workflow run contracts | 2026-06-09T07:45:58Z | — | question; backlog; architecture; fkst-dev:hold; fkst-class:background | https://github.com/aevatarAI/aevatar/issues/1899 | unclassified | — | — |
| open | #2058 | cleanup(test): 测试套件质量整改——*CoverageTests 按覆盖率组织 / 超大测试文件 / setup 里的 GetAwaiter().GetResult() | 2026-06-13T16:42:48Z | — | cleanup; crnd:phase:implementing | https://github.com/aevatarAI/aevatar/issues/2058 | unclassified | — | — |
| open | #2080 | Studio member binding run can remain in progress after readiness timeout | 2026-06-15T03:55:41Z | — | fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2080 | unclassified | — | — |
| open | #2104 | feat(studio/connectors): add typed connector operation schemas for app operation forms | 2026-06-15T11:07:00Z | — | enhancement; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2104 | unclassified | — | — |
| open | #2105 | feat(studio/workflow-debug): add Step IO panel for selected workflow steps | 2026-06-15T11:07:00Z | — | enhancement; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2105 | unclassified | — | — |
| open | #2106 | feat(studio/workflow-debug): debug workflow drafts from historical runs | 2026-06-15T11:07:38Z | — | enhancement; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2106 | unclassified | — | — |
| open | #2107 | feat(studio/workflow-debug): support draft-only pinned step artifacts | 2026-06-15T11:07:38Z | — | enhancement; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2107 | unclassified | — | — |
| open | #2108 | feat(studio/artifacts): add workflow artifact and file port for uploads and step outputs | 2026-06-15T11:07:39Z | — | enhancement; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2108 | unclassified | — | — |
| open | #2112 | [arch] Remove dead reverse ProjectReferences: Studio.Application → Scripting.{Infrastructure,Hosting} | 2026-06-15T14:47:29Z | — | architecture; cleanup | https://github.com/aevatarAI/aevatar/issues/2112 | unclassified | — | — |
| open | #2113 | [arch] Relocate Workflow.Infrastructure AGUI-adapter DI wiring to the composition root (Infra→Presentation reverse edge) | 2026-06-15T14:47:31Z | — | architecture | https://github.com/aevatarAI/aevatar/issues/2113 | unclassified | — | — |
| open | #2114 | [arch] Architecture hygiene (Brooks 06-15): NyxidChat fan-out, Foundation.Runtime naming taxonomy, zero-fan-in assemblies | 2026-06-15T14:47:33Z | — | architecture; cleanup | https://github.com/aevatarAI/aevatar/issues/2114 | unclassified | — | — |
| open | #2167 | feat(schedule): expose execution history and full detail payload | 2026-06-16T08:18:13Z | — | enhancement; backend-backlog; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2167 | unclassified | — | — |
| open | #2178 | 接入外部系统的请求定义：固化交互契约（definition id + 字段映射 + 事件订阅方） | 2026-06-16T09:42:17Z | — | crnd:human:auto; crnd:phase:blocked | https://github.com/aevatarAI/aevatar/issues/2178 | unclassified | — | — |
| open | #2182 | [Epic] 外部门控的资源变更闭环：请求 → 前置校验 → 外部确认 → 幂等提交/回滚 → 回写通知 | 2026-06-16T09:42:53Z | — | crnd:human:auto; crnd:phase:blocked | https://github.com/aevatarAI/aevatar/issues/2182 | unclassified | — | — |
| open | #2209 | MassTransit 残留清理:props/guard/ADR-0007 均漂移,无活跃 csproj 消费 | 2026-06-17T05:31:00Z | — | question; architecture | https://github.com/aevatarAI/aevatar/issues/2209 | unclassified | — | — |
| open | #2210 | ChatRuntime.DefaultMaxToolRounds = int.MaxValue 是无熔断 fallback(实际默认 40,但 fallback 路径无保护) | 2026-06-17T05:31:33Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2210 | unclassified | — | — |
| open | #2224 | Prevent Orleans/Garnet split-brain from production config drift | 2026-06-17T08:41:09Z | — | bug; architecture; infrastructure | https://github.com/aevatarAI/aevatar/issues/2224 | unclassified | — | — |
| open | #2266 | Support multipart uploads for scope workflow draft-run | 2026-06-18T09:02:01Z | — | fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2266 | unclassified | — | — |
| open | #2299 | Epic: 已发布服务自动注册为 NyxID downstream（发布即被发现） | 2026-06-22T05:14:48Z | — | — | https://github.com/aevatarAI/aevatar/issues/2299 | unclassified | — | — |
| open | #2319 | Zero-config voice: /ws/voice should auto-provision a session/actor (drop per-account chat-route + voice-enable setup) | 2026-06-23T03:18:53Z | — | — | https://github.com/aevatarAI/aevatar/issues/2319 | unclassified | — | — |
| open | #2333 | Add low-interaction workflow execution display board | 2026-06-23T09:11:37Z | — | enhancement; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2333 | unclassified | — | — |
| open | #2357 | Lark bot: after /whatsapp-reply-draft loads the skill and asks for input, providing the message does not run the workflow (agent polishes/rephrases instead) | 2026-06-24T08:47:58Z | — | — | https://github.com/aevatarAI/aevatar/issues/2357 | unclassified | — | — |
| open | #2358 | /whatsapp-reply-draft <multi-line message>: only the first line is passed to the workflow (remaining lines dropped) | 2026-06-24T09:13:22Z | — | — | https://github.com/aevatarAI/aevatar/issues/2358 | unclassified | — | — |
| open | #2359 | Relay truncates the reply sent to Lark — workflow output is complete in the observatory but the Lark message is cut off mid-output (3rd draft dropped) | 2026-06-24T09:19:05Z | — | fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2359 | unclassified | — | — |
| open | #2369 | Scope-owner schedule: create returns 202 but every fire errors 'NyxID binding does not grant the requested schedule scope' (broker_binding+proxy binding insufficient, no self-serve fix) | 2026-06-25T03:38:23Z | — | — | https://github.com/aevatarAI/aevatar/issues/2369 | unclassified | — | — |
| open | #2386 | [PQL][Aevatar][Workflow] Published workflow member cannot run because no draft steps are linked | 2026-06-26T08:11:42Z | — | bug | https://github.com/aevatarAI/aevatar/issues/2386 | unclassified | — | — |
| open | #2389 | [PQL][Aevatar][Console] Services API returns 403 because service identity claims are missing | 2026-06-26T10:25:27Z | — | bug | https://github.com/aevatarAI/aevatar/issues/2389 | unclassified | — | — |
| open | #2404 | 定时调用凭证：收敛为单一权威来源模型（ADR-0037 / disc#2402） | 2026-06-29T05:43:48Z | — | — | https://github.com/aevatarAI/aevatar/issues/2404 | unclassified | — | — |
| open | #2418 | Expose scheduled dispatch prompt in backend schedule summaries | 2026-06-29T08:29:41Z | — | fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2418 | unclassified | — | — |
| open | #2424 | 支持外部 learned-routing orchestrator 作为 OpenAI 兼容 provider 接入 | 2026-06-29T11:04:52Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2424 | unclassified | — | — |
| open | #2425 | fkst-dev board | 2026-06-29T12:03:33Z | — | fkst-class:background; fkst-dashboard; fkst-dev:tracking | https://github.com/aevatarAI/aevatar/issues/2425 | unclassified | — | — |
| open | #2447 | [channel][lark] No working path to run a workflow on an uploaded file: /workflow run needs the file on the command message (Lark sends files separately); skill/aevatar_invoke_team path drops attachments | 2026-06-30T02:52:26Z | — | — | https://github.com/aevatarAI/aevatar/issues/2447 | unclassified | — | — |
| open | #2450 | Scheduled (scopeOwnerNyxId) fire of a ~7-8min workflow fails mid-run with token_expired (2001); identical direct invoke completes | 2026-06-30T04:49:19Z | — | bug; blocker; crnd:lifecycle:managed; crnd:human:auto; crnd:phase:blocked; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2450 | unclassified | — | — |
| open | #2459 | [Request] Enable external exposure / NyxID registration for HR email-approval service (scope e56cc992…) | 2026-06-30T08:33:09Z | — | — | https://github.com/aevatarAI/aevatar/issues/2459 | unclassified | — | — |
| open | #2461 | Lark relay bot: Ornn skill fails with `credential_denied` — relayed turn can't resolve the bot user's NyxID-connected datasource (post-/init) | 2026-06-30T08:36:56Z | — | — | https://github.com/aevatarAI/aevatar/issues/2461 | unclassified | — | — |
| open | #2462 | [Epic] Layered context architecture for agent system prompts: minimal stable kernel + host-extensible forced overlay | 2026-06-30T08:47:43Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2462 | unclassified | — | — |
| open | #2491 | [aevatar] Feature: a non-console (CLI / REST / device-code) path to establish the scope-owner NyxID broker binding — headless/agent operators currently can't create `scopeOwnerNyxId` schedules | 2026-06-30T15:24:01Z | — | — | https://github.com/aevatarAI/aevatar/issues/2491 | unclassified | — | — |
| open | #2578 | 定时调度静默漏拍复发（#2366 根因未修）：ScheduledDispatchGAgent fire handler 幂等去重仍会误吞合法 occurrence，系统性影响 5+ 条排程 | 2026-07-01T11:50:43Z | — | — | https://github.com/aevatarAI/aevatar/issues/2578 | unclassified | — | — |
| open | #2580 | Harden channel-relay credential trust boundary (aevatar-side): strip persisted per-step credentials + gate human-only NyxID tools in relay turns | 2026-07-01T12:54:30Z | — | — | https://github.com/aevatarAI/aevatar/issues/2580 | unclassified | — | — |
| open | #2584 | fkst-dev board | 2026-07-01T15:47:43Z | — | fkst-class:background; fkst-dashboard; fkst-dev:tracking | https://github.com/aevatarAI/aevatar/issues/2584 | unclassified | — | — |
| open | #2591 | 为 workflow readmodel/artifact 查询工具补 scope 授权校验 | 2026-07-02T10:09:58Z | — | — | https://github.com/aevatarAI/aevatar/issues/2591 | unclassified | — | — |
| open | #2592 | [Epic] Platform audit trail: unified recording of security-relevant operations | 2026-07-03T07:57:51Z | — | infrastructure | https://github.com/aevatarAI/aevatar/issues/2592 | unclassified | — | — |
| open | #2621 | [studio] Backend version contract for editor/server/runtime state consistency | 2026-07-07T08:27:22Z | — | fkst-dev:hold; fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2621 | unclassified | — | — |
| open | #2639 | Fix Mission Wall workflow graph disappearing | 2026-07-08T04:17:06Z | — | fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2639 | unclassified | — | — |
| open | #2654 | [frontend] Add Workflow Studio Step IO panel | 2026-07-08T08:41:43Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2654 | unclassified | — | — |
| open | #2655 | [frontend] Add member workflow run history in Studio | 2026-07-08T08:42:23Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2655 | unclassified | — | — |
| open | #2656 | [frontend] Render schema-driven connector operation forms | 2026-07-08T08:42:48Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2656 | unclassified | — | — |
| open | #2657 | [frontend] Add Debug from run flow for Workflow Studio | 2026-07-08T08:43:10Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2657 | unclassified | — | — |
| open | #2658 | [frontend] Add draft-only pinned step artifact controls | 2026-07-08T08:43:33Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2658 | unclassified | — | — |
| open | #2659 | [frontend] Add workflow artifact upload and preview UI | 2026-07-08T08:43:57Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2659 | unclassified | — | — |
| open | #2660 | [frontend] Consume Studio workflow version and provenance contract | 2026-07-08T08:44:23Z | — | enhancement; fkst-dev:hold; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2660 | unclassified | — | — |
| open | #2661 | Backend: expose run event resume stream for frontend reconnect recovery | 2026-07-08T08:52:47Z | — | fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2661 | unclassified | — | — |
| open | #2679 | Studio workflow provisioning reports accepted while failed binds leave enabled schedules and duplicate resources | 2026-07-09T12:50:07Z | — | fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2679 | unclassified | — | — |
| open | #2699 | foreach fan-out → aggregate is unusable: downstream code_execute can't read a foreach's aggregated output (+ broker size limit, no code_execute concurrency/~60s cold-start, undocumented output shape) | 2026-07-10T06:10:46Z | — | — | https://github.com/aevatarAI/aevatar/issues/2699 | unclassified | — | — |
| open | #2700 | Frontend: make Chat workflow run state and next actions explicit | 2026-07-10T06:36:37Z | — | fkst-dev:enabled; fkst-class:standard; fkst:generated | https://github.com/aevatarAI/aevatar/issues/2700 | unclassified | — | — |
| open | #2717 | Add schedule-filtered run history for Team member automations | 2026-07-13T06:45:33Z | — | enhancement; fkst-class:background; fkst-dev:tracking | https://github.com/aevatarAI/aevatar/issues/2717 | unclassified | — | — |
| open | #2718 | Backend: expose schedule-filtered member run history | 2026-07-13T06:46:00Z | — | enhancement; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2718 | unclassified | — | — |
| open | #2719 | Frontend: add schedule-filtered automation run history | 2026-07-13T06:46:22Z | — | enhancement; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2719 | unclassified | — | — |
| open | #2737 | 定时调用凭证：统一强类型授权计划与 exact NyxID service/node grants | 2026-07-14T07:20:59Z | — | enhancement; blocker; architecture; crnd:human:auto; crnd:phase:blocked; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2737 | unclassified | — | — |
| open | #2754 | Make NyxID service grants configurable and reviewable from Lark /init | 2026-07-15T03:33:44Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2754 | unclassified | — | — |
| open | #2765 | [fkst-stability] 错误率飙升: identity.login.finalize (fp:01452398) | 2026-07-15T06:52:49Z | — | fkst-dev:enabled; fkst-dev:blocked; fkst-stability; severity:high; signal:error-spike | https://github.com/aevatarAI/aevatar/issues/2765 | unclassified | — | — |
| open | #2775 | 物化 owner-scoped NyxID 授权事实 | 2026-07-15T17:09:09Z | — | blocker; crnd:human:auto; crnd:phase:blocked; crnd:milestone:current | https://github.com/aevatarAI/aevatar/issues/2775 | unclassified | — | — |
| open | #2779 | 支持 Aevatar 直连 OpenSandbox 执行 managed codex_exec | 2026-07-16T03:29:16Z | — | implementation-deferred; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2779 | unclassified | — | — |
| open | #2782 | Enable user-scoped managed Codex execution through NyxID | 2026-07-16T03:44:14Z | — | enhancement; architecture; implementation-deferred; fkst-dev:hold; fkst-class:background; fkst-dev:tracking | https://github.com/aevatarAI/aevatar/issues/2782 | unclassified | — | — |
| open | #2784 | Prove allowlisted NyxID account can run managed-sandbox codex_exec end to end | 2026-07-16T03:44:19Z | — | enhancement; infrastructure; implementation-deferred; fkst-dev:hold; fkst-class:expedite | https://github.com/aevatarAI/aevatar/issues/2784 | unclassified | — | — |
| open | #2785 | [OpenSandbox] Provide Codex runner image and validate direct execution | 2026-07-16T03:44:22Z | — | infrastructure; implementation-deferred; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2785 | unclassified | — | — |
| open | #2786 | [Ops] Enable isolated direct OpenSandbox access for managed codex_exec | 2026-07-16T03:44:23Z | — | infrastructure; implementation-deferred; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2786 | unclassified | — | — |
| open | #2788 | Add durable approval coordination for deterministic connector calls | 2026-07-16T04:11:22Z | — | enhancement; architecture; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2788 | unclassified | — | — |
| open | #2790 | Add revisioned content artifacts with provenance and citation support | 2026-07-16T04:12:37Z | — | enhancement; fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2790 | unclassified | — | — |
| open | #2800 | Frontend: 从 Studio 发起 NyxID service access review | 2026-07-16T08:56:33Z | — | enhancement | https://github.com/aevatarAI/aevatar/issues/2800 | unclassified | — | — |
| open | #2803 | fkst-dev board | 2026-07-16T09:25:24Z | — | fkst-dashboard | https://github.com/aevatarAI/aevatar/issues/2803 | unclassified | — | — |
| open | #2808 | Escalate blocked output obligation: state-output-obligation-timeout for #2765 | 2026-07-16T10:54:11Z | — | — | https://github.com/aevatarAI/aevatar/issues/2808 | unclassified | — | — |
| open | #2812 | Lark channel provisioning is not idempotent and leaks relay Agent Keys | 2026-07-16T17:20:59Z | — | bug; architecture | https://github.com/aevatarAI/aevatar/issues/2812 | unclassified | — | — |
| open | #2838 | Close the Team-scoped connector authoring-to-runtime resolution loop | 2026-07-17T11:10:39Z | — | — | https://github.com/aevatarAI/aevatar/issues/2838 | unclassified | — | — |
| open | #2853 | fix(console): disable Apply to draft after YAML is successfully applied | 2026-07-20T04:12:07Z | — | — | https://github.com/aevatarAI/aevatar/issues/2853 | unclassified | — | — |
| open | #2854 | [Bug] Workflow schedule provisioning fails with nyxid_catalog_snapshot_not_found | 2026-07-20T04:35:28Z | — | fkst-dev:enabled; fkst-class:standard; fkst-dev:blocked | https://github.com/aevatarAI/aevatar/issues/2854 | unclassified | — | — |
| open | #2877 | fkst-dev board | 2026-07-21T03:10:55Z | — | fkst-class:background; fkst-dashboard; fkst-dev:tracking | https://github.com/aevatarAI/aevatar/issues/2877 | unclassified | — | — |
| open | #2881 | Enable managed codex_exec for all eligible workflow users | 2026-07-21T03:41:34Z | — | enhancement; architecture; implementation-deferred; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2881 | unclassified | — | — |
| open | #2883 | fix(console): 正确渲染 Chat 消息中的 Markdown 表格 | 2026-07-21T03:57:33Z | — | — | https://github.com/aevatarAI/aevatar/issues/2883 | unclassified | — | — |
| open | #2898 | [Ops] Deploy and canary internal managed codex_exec through chrono-sandbox | 2026-07-21T10:00:55Z | — | Target p0; infrastructure; security-debt | https://github.com/aevatarAI/aevatar/issues/2898 | unclassified | — | — |
| open | #2899 | [Security debt] Replace managed Codex agent keys and broad proxy delegation | 2026-07-21T10:01:51Z | — | backlog; architecture; implementation-deferred; security-debt | https://github.com/aevatarAI/aevatar/issues/2899 | unclassified | — | — |
| open | #2921 | [Proposal] Simplify managed codex_exec to gVisor + direct short-lived token (drop runc/Landlock/Vault) | 2026-07-22T08:12:48Z | — | — | https://github.com/aevatarAI/aevatar/issues/2921 | unclassified | — | — |
| open | #2922 | [codex-runner] Update image + contract for gVisor model (option B of #2921) | 2026-07-22T08:22:27Z | — | — | https://github.com/aevatarAI/aevatar/issues/2922 | unclassified | — | — |
| open | #2932 | Extract Lark resource and identity handling behind channel ports | 2026-07-23T08:24:10Z | — | — | https://github.com/aevatarAI/aevatar/issues/2932 | unclassified | — | — |
| open | #2933 | Generalize channel runtime metadata and delivery targets | 2026-07-23T08:24:12Z | — | — | https://github.com/aevatarAI/aevatar/issues/2933 | unclassified | — | — |
| open | #2934 | Generalize Lark card delivery state and operation events | 2026-07-23T08:24:14Z | — | — | https://github.com/aevatarAI/aevatar/issues/2934 | unclassified | — | — |
| open | #2935 | [fkst-stability] 持续失败: nyxid_proxy (fp:76379b1a) | 2026-07-23T08:33:35Z | — | fkst-dev:enabled; fkst-dev:blocked; fkst-stability; signal:recurring-failure; severity:high | https://github.com/aevatarAI/aevatar/issues/2935 | unclassified | — | — |
| open | #2936 | [Backend][Workflow/Chat] Step 失败后仍继续执行并返回成功终态 | 2026-07-23T08:57:18Z | — | bug; fkst-dev:enabled; fkst-class:standard; fkst-dev:awaiting-pr | https://github.com/aevatarAI/aevatar/issues/2936 | unclassified | — | — |
| open | #2944 | [workflow] #2895 bind admission 已上线，但 Lark bot 服务无已发布 OpenAPI spec —— operation_id 无法满足，存量 nyxid_proxy workflow 全部无法 rebind，求迁移路径 | 2026-07-24T01:49:41Z | — | — | https://github.com/aevatarAI/aevatar/issues/2944 | unclassified | — | — |
| open | #2946 | Escalate blocked output obligation: state-output-obligation-timeout for #2788 | 2026-07-24T03:10:24Z | — | — | https://github.com/aevatarAI/aevatar/issues/2946 | unclassified | — | — |
| open | #2947 | Escalate blocked output obligation: state-output-obligation-timeout for #2790 | 2026-07-24T03:10:33Z | — | — | https://github.com/aevatarAI/aevatar/issues/2947 | unclassified | — | — |
| open | #2949 | [Epic][Smart Home] 自然语言连接 Xiaomi Home 并生成可执行 Workflow | 2026-07-24T03:14:57Z | — | enhancement; architecture; fkst-dev:hold | https://github.com/aevatarAI/aevatar/issues/2949 | unclassified | — | — |
| open | #2951 | Escalate blocked output obligation: state-output-obligation-timeout for #2935 | 2026-07-24T07:35:18Z | — | — | https://github.com/aevatarAI/aevatar/issues/2951 | unclassified | — | — |
| open | #2952 | Unify API chat and channel bot history ownership | 2026-07-24T08:05:39Z | — | — | https://github.com/aevatarAI/aevatar/issues/2952 | unclassified | — | — |
| open | #2953 | Make /api/schedules the single owner-aware schedule API | 2026-07-24T08:30:13Z | — | — | https://github.com/aevatarAI/aevatar/issues/2953 | unclassified | — | — |
| open | #2954 | Add actor-owned stop semantics to NyxIdChat turns | 2026-07-24T08:55:59Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2954 | unclassified | — | — |
| open | #2955 | Expose durable NyxIdChat conversation state and reconnect observation | 2026-07-24T08:56:00Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2955 | unclassified | — | — |
| open | #2956 | Add typed mid-run steering for NyxIdChat conversations | 2026-07-24T08:56:00Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2956 | unclassified | — | — |
| open | #2957 | Expose typed NyxIdChat task plan and step lifecycle | 2026-07-24T08:56:03Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2957 | unclassified | — | — |
| open | #2958 | [scheduler] 07-22 前创建的排程 actor 全部停止触发且不自愈：nextFireAt 冻结、零报错；新建排程正常 fire | 2026-07-24T10:20:19Z | — | — | https://github.com/aevatarAI/aevatar/issues/2958 | unclassified | — | — |
| open | #2959 | Fork of #2838: [fkst:blocked-github-content:v1 field="title" existed="true" author_login="abigail940404" why="non-whitelisted-author"] | 2026-07-24T11:14:08Z | — | fkst-class:standard | https://github.com/aevatarAI/aevatar/issues/2959 | unclassified | — | — |
| open | #2961 | Define NyxID browser action handoff for NyxIdChat | 2026-07-24T15:23:48Z | — | enhancement; architecture | https://github.com/aevatarAI/aevatar/issues/2961 | unclassified | — | — |
