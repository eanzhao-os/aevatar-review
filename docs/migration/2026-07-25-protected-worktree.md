# 受保护工作区与迁移输入账本（2026-07-25 冻结基线）

> 上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`（只读）
>
> 本仓库 Task 1 diff base：`da089e19be488caa02185a4af189207d57bc55d6`
>
> 首次枚举时间：Task 1 Step 3（执行会话开始时）

## 1. 规则

- 任务开始时**已经存在**的一切工作区改动（staged / unstaged / untracked），无论是否属于本次重构计划，
  一律标记 `owner = user-existing` 并成为受保护输入。
- 受保护输入**不得**被 `reset` / `stash` / `checkout` / `clean` / 整文件覆盖，也不得被顺手提交进任务提交。
- 本账本只记录**非敏感指纹**：porcelain XY 状态、HEAD blob、index blob、worktree SHA-256、
  staged/unstaged patch SHA-256。**禁止**把 patch 正文、secret、bearer 值、原始 key、密文或完整外部清单写入本文件。
- 对本身就承载凭据的 skill-private 运行态文件，连指纹也不记录（列为 `withheld-sensitive-runtime`），
  因为它们既不进入文档，也不需要迁移比对；记录哈希只会平白扩大暴露面。
- 每个受保护输入必须有 `migration_status`：

| `migration_status` | 含义 |
|---|---|
| `pending` | 尚未确定落点；Task 19 结构切换前必须清零 |
| `unreviewed` | 已有落点但未经逐节比对；Task 19 结构切换前必须清零 |
| `migrated-reviewed` | 已逐节比对并确认无损迁入新落点 |
| `retained-as-is` | 文件本身继续存在于新结构，不需要迁移 |
| `no-migration-runtime` | skill-private 运行态产物，不属于文档内容，不迁移也不提交 |

## 2. 快照 A：Task 1 起始时的工作区改动

命令来源：`git diff --cached --name-only -z`、`git diff --name-only -z`、
`git ls-files --others --exclude-standard -z` 的并集（NUL 安全）。

| 路径 | XY | owner | HEAD blob | index blob | worktree SHA-256 | staged patch SHA-256 | unstaged patch SHA-256 | 迁移落点 | migration_status |
|---|---|---|---|---|---|---|---|---|---|
| `CLAUDE_HANDOFF_PROMPT.md` | `??` | user-existing | absent | absent | `1a35dff2a425e7bd3e49a9b8bab1dfb491b72566278086498b08c3d71a9e28a7` | `e3b0c442…7852b855`（空） | `e3b0c442…7852b855`（空） | 不迁移；用户要求生成的交接材料，保持未跟踪原样 | `retained-as-is` |
| `.superpowers/brainstorm/91971-1784922164/content/navigation-layout-options.html` | `??` | user-existing | absent | absent | `fe45c6df46864eda445567af0325dc22b3285d782969bd1c89d9114fefd03bc4` | 空 | 空 | 不迁移；导航方案的可视化对比稿，结论已固化进已批准设计 | `no-migration-runtime` |
| `.superpowers/brainstorm/91971-1784922164/content/waiting-for-spec-review.html` | `??` | user-existing | absent | absent | `452e3c8412552fbdc7c1807bacbe8316317d6acb60bb25c266a0efbdd825d6fc` | 空 | 空 | 不迁移；brainstorm 会话页面 | `no-migration-runtime` |
| `.superpowers/brainstorm/91971-1784922164/state/server-instance-id` | `??` | user-existing | absent | absent | `3fc6a6dfdc04eff30acb2b4bdcb19a60fd89e93428be32e20a720c9d18a578f2` | 空 | 空 | 不迁移；本地服务运行态 | `no-migration-runtime` |
| `.superpowers/brainstorm/91971-1784922164/state/server-stopped` | `??` | user-existing | absent | absent | `009bab728df0d4fbdaeff438d4521bb68bbecefb86f0129497aa572377aea568` | 空 | 空 | 不迁移；本地服务运行态 | `no-migration-runtime` |
| `.superpowers/brainstorm/91971-1784922164/state/server.pid` | `??` | user-existing | absent | absent | `765b3e5d0e6c98cdaf27e80c32f4e11d20f12fa9ef926641491b36df77599ad9` | 空 | 空 | 不迁移；本地服务运行态 | `no-migration-runtime` |
| `.superpowers/brainstorm/.last-port` | `??` | user-existing | absent | absent | `withheld-sensitive-runtime` | 空 | 空 | 不迁移；skill-private 运行态 | `no-migration-runtime` |
| `.superpowers/brainstorm/.last-token` | `??` | user-existing | absent | absent | `withheld-sensitive-runtime` | 空 | 空 | 不迁移；skill-private 会话令牌，禁止进入任何文档或提交 | `no-migration-runtime` |

### 快照 A2：Task 2 期间新出现的工作区改动

标准义务要求每个 Task 开始时重新枚举。下列改动在 Task 1 起始枚举时**不存在**，在 Task 2 执行期间出现，
因此自动成为受保护输入：

| 路径 | XY | owner | HEAD blob（前 12） | worktree SHA-256 | 迁移落点 | migration_status |
|---|---|---|---|---|---|---|
| `10/07-scheduled-task-not-firing.md` | ` M` | user-existing | `3d6a5f95ee31` | `c9cf3458f5b8d8c0b9c9f8b1f6a7c758470e7fcb09ddb1839780cdaba23e7192` | `09/02`、`12/04`（新增的第四类"reminder 收尾丢上下文"必须与既有三类根因分层保留，不得合并成一句） | `unreviewed` |

该文件的未提交改动新增了第四类"定时任务不触发"根因（一次性回调触发后收尾注销失败，tick 被 Orleans
记为投递错误、物理 reminder 行不删除）。它是**尚未提交的用户内容**，不得被本任务提交、还原或覆盖；
Task 14 与 Task 17 迁移 `09/02` 与 `12/04` 时必须重新取哈希并按节比对，确认这一类根因无损进入新结构。

`.superpowers/sdd/` 由其自带的 `.gitignore`（内容为 `*`）完全忽略，因此不出现在 `git ls-files --others --exclude-standard`
的输出中。它承载本轮 SDD 运行态（`progress.md`、`task-1-brief.md`、`task-1-report.md`），同样属于 `no-migration-runtime`：
不进入任何 Task 提交，也不作为任何事实源。

### 快照 A3：Task 7 恢复时新出现的目标章节

下列未跟踪文件在本次恢复会话开始时已经存在，因此先按 `user-existing` 保护。它们恰好位于 Task 7
的精确目标路径，但“路径正确”不等于“章节已完成”：只有逐章通过事实审计、四项门禁与独立复核后，
才能提交并把状态改为 `migrated-reviewed`。

| 路径 | XY | owner | HEAD blob | worktree SHA-256 | 迁移落点 | migration_status |
|---|---|---|---|---|---|---|
| `02/01-agent-actor-runtime.md` | `??` | user-existing | absent | `29573a0ca236164930b1cb8f613d4dc143cb90c6357c6cd6278b55ed40219d88` | 原路径保留并按 Task 7 验收 | `migrated-reviewed` |
| `02/02-envelope-command-event-query.md` | `??` | user-existing | absent | `d4108f40dbcea03bac21a4c9462b958dc8e7cc656e673738a11d6f4402ab32aa` | 原路径保留并按 Task 7 验收 | `migrated-reviewed` |
| `02/03-gagent-event-pipeline.md` | `??` | user-existing | absent | `67ce6b4a10ec1fb891541564934d7248e86fa028d9b6252dc3bb6dc1ca7f4b98` | 原路径保留并按 Task 7 验收 | `migrated-reviewed` |
| `02/04-state-event-sourcing-and-guard.md` | `??` | user-existing | absent | `8943fbe9b11929a609a84a77b5ece1d92668c6592dc968e32ecdc6c2457c56b0` | 原路径保留并按 Task 7 验收 | `migrated-reviewed` |
| `02/05-dispatch-routing-and-topology.md` | `??` | user-existing | absent | `2ef758322587dbf1aed0f657f6bb91f97f3f84cc0ea7e4c99e9d8e27fb3e75f5` | 原路径保留并按 Task 7 验收 | `migrated-reviewed` |
| `02/06-local-runtime-and-lifecycle.md` | `??` | user-existing | absent | `686fc165baac0fb88dd718f804a4db206cb51d7076eb80c0581db2ac429dfabe` | 原路径保留并按 Task 7 验收 | `migrated-reviewed` |

## 3. 快照 B：设计期已识别、当前已进入 HEAD 的受保护迁移输入

设计 §9.3 列出的受保护文件在 `bab63e8` / `da089e1` 两个用户提交中已进入 HEAD，因此在本次执行基线上
不再表现为 dirty 工作区条目，但它们**仍然是受保护迁移输入**：其事实、措辞意图与生产证据必须无损进入新结构，
之后才允许由 Task 19 按退役清单删除。

| 路径 | owner | HEAD blob（前 12） | 最近提交 | 迁移落点 | migration_status |
|---|---|---|---|---|---|
| `07/12-scheduled-tasks.md` | user-existing | `6dc6cf120add` | `bab63e8` | `09/01`、`09/02`、`09/03`、`09/04`、`12/04` | `unreviewed` |
| `09/03-provision-and-observe-via-nyxid/02-scheduled-agent-key-production-canary.md` | user-existing | `114817a9698d` | `da089e1` | `09/05`、`12/04` | `unreviewed` |
| `09/03-provision-and-observe-via-nyxid/index.md` | user-existing | `71dcf0ae50e1` | `da089e1` | `09/index.md`（Task 19 原位改写）、`09/05` | `unreviewed` |
| `07/index.md` | user-existing | `f24150cc40c0` | `bab63e8` | `07/index.md`、`08/index.md`、`09/index.md`（Task 19 原位改写） | `pending` |
| `10/index.md` | user-existing | `05b07bbd30f6` | `bab63e8` | `10/index.md`、`12/index.md`（Task 19 原位改写） | `pending` |
| `PLAN.md` | user-existing | `953b6241a587` | `bab63e8` | `PLAN.md`（Task 19 合并改写为 72 行清单，不整文件覆盖） | `pending` |
| `mkdocs.yml` | user-existing | `8436e3b7ebe8` | `bab63e8` | `mkdocs.yml`（Task 19 原子替换 nav，保留站点/主题设置与已批准双行导航设计） | `pending` |

## 4. 快照 C：并行用户分支

| 引用 | 内容 | 处置 |
|---|---|---|
| `fix/chapter-navigation` @ `9bdf078` | 已批准双行导航布局的实现（`scripts/check-site-ui.py`、`docs/stylesheets/extra.css`、`mkdocs.yml`、`.github/workflows/docs.yml`） | 用户于 2026-07-28 明确要求捞取其他分支成品并只在 `main` 续写；原分支 source contract 通过后，于 `e751fe8` 合入 `main`。Task 19 扩展导航到 `00–13` 时必须保留该设计契约，并把 `CURRENT_TOP_LEVEL_COUNT` 从 14 更新为 15。 |
| `codex/fix-pages-owner` @ `56e2a57` | 仓库迁移后的 Pages、repository 与 social URL 修正 | 原提交 `git show --check` 通过后，经 `b39578c` 合入 `main`；Task 19 改写 `mkdocs.yml` 时必须保留 `eanzhao-os` 地址。 |

## 5. 外部只读仓库漂移记录

| 项 | 值 |
|---|---|
| 冻结事实基线 | `f02aa690bbebb9cabeac30a553d737486b0eb661`（本轮唯一当前实现事实源） |
| Task 1 起始时上游 live HEAD | `aba74805c6b40f3848a554b85e4192e7c06abfa2` |
| 上游 live 工作区 | 存在他人未提交修改（10 个 `M` 路径 + 未跟踪项） |
| 处置 | 只记录为外部漂移。不移动基线、不读取 live working tree 作为事实、不对上游做任何写操作 |

## 6. 重新枚举义务

每个 Task 与每次恢复后的 turn 都必须重新运行第 2 节的并集命令。当时存在且不属于该 Task 的任何新改动
自动成为受保护输入，必须在派发或写入前追加到快照 A。设计期文件清单不是封闭清单。

## 7. Task 14 调度输入复核与逐节落点

Task 14 协调前重新枚举只发现既有 `.superpowers/` 与 `CLAUDE_HANDOFF_PROMPT.md` 两项未跟踪受保护资产；
没有新的任务外改动。下列指纹取自 2026-07-29 当前工作树，正文迁移采用该最新内容：

| 路径 | 当前 blob（前 12） | 当前 SHA-256 | 已迁入落点 | 尚待落点 | migration_status |
|---|---|---|---|---|---|
| `07/12-scheduled-tasks.md` | `6dc6cf120add` | `1eb1dc5c6b559347b881117a8136c47770e9de6d001ca3dd560d7dc3a09673a1` | §0–1 资源/API→`09/01`；§2 callback/fire→`09/02`；§3 Agent Key/Vault→`09/03–04`；§4–5 ACK/补偿→`09/01`、`09/04`；§6–8 current surface与验证层级→`09/01–05` | §6 fire-time exchange历史与事故教训→`12/04` | `unreviewed` |
| `10/07-scheduled-task-not-firing.md` | `7718b7ad24a0` | `c9cf3458f5b8d8c0b9c9f8b1f6a7c758470e7fcb09ddb1839780cdaba23e7192` | §0、§4 的current callback ownership、one-shot grain-context修复→`09/02` | §1–4 四类根因各自的症状/根因/修复/余限→`12/04` | `unreviewed` |
| `09/03/provision-and-observe-via-nyxid/02-scheduled-agent-key-production-canary.md` | `85f5b61ac091` | `cb2ae417ad2d3bf7796b91a7a5f6a3620bb6623dc574312f58efb02d6dbb5d8e` | §0、§2–5、§6四次证据、§6.1前置失败、§7–9恢复/检查单/结论→`09/05`，其中授权与Vault边界分别回指`09/03–04` | 版本化生产缺口、projection repair与第四次前置事故→`12/04` | `unreviewed` |
| `09/03/provision-and-observe-via-nyxid/index.md` | `71dcf0ae50e1` | `c2551412e7ac21fb639751d3a57af9a776e080cf2a30ddb50dfb1e278d67c9e0` | production evidence导读意图→`09/05` | 目录导航→Task 19 的`09/index.md`、`12/index.md` | `unreviewed` |

这里的 `unreviewed` 是有意保留的中间态：`09` 已逐节承接 current model 与四次证据强度，但`12/04`尚未写作，
因此不能提前宣称受保护输入已经完成全落点复核。Task 17 必须再次按上述 SHA-256 比对并把四类 schedule 事故、
canary audit/provenance 缺口无损收拢后，才能把对应行推进为 `migrated-reviewed`。
