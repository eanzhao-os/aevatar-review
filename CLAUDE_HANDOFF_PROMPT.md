# Claude 执行提示词：完成 aevatar-review 全库文档重构

你现在是 `/Users/eanzhao/Code/aevatar-review` 的接手执行者。请直接在该仓库中继续并完成已经批准的全库文档重构。方案、信息架构和实施计划均已批准；不要重新做需求访谈，不要重新比较方案，不要逐 Task 等待用户说“继续”。除非遇到下文定义的真实阻塞，否则持续实施、验证、review、修复，直到完成。

## 1. 最终目标

以只读上游 `/Users/eanzhao/Code/aevatar` 的冻结提交
`f02aa690bbebb9cabeac30a553d737486b0eb661` 为唯一当前代码事实基线，结合：

- 2026-07-25 时点的 126 个 open issues；
- closed date 位于 2026-07-06 至 2026-07-25 的 154 个 closed issues；
- 当前 review 仓库的 85 篇旧章节和所有用户已有内容；

把本仓库重构为 `00–13` 共 14 个 block、72 篇实质章节和 14 个 block index 的结构化中文 Aevatar 解读。允许并且应当新增、删除、合并、拆分和重组章节；不得保留仅写“已迁移”的空壳章节。

最终文档必须让新读者能沿主线理解 Aevatar，也让维护者能核验职责边界、状态所有权、协议、ACK 强度、幂等、失败恢复、生产证据及当前缺口。

## 2. 开始前必须按顺序完整读取

1. `AGENTS.md`
2. `CLAUDE.md`
3. `docs/superpowers/specs/2026-07-25-aevatar-review-restructure-design.md`
4. `docs/superpowers/plans/2026-07-25-aevatar-review-restructure.md`
5. `docs/superpowers/specs/2026-07-25-chapter-navigation-layout-design.md`
6. `docs/superpowers/plans/2026-07-25-chapter-navigation-layout.md`
7. `.superpowers/sdd/progress.md`
8. `.superpowers/sdd/task-1-brief.md`

这些文件是已批准的设计和执行契约。若本提示词只概括了其中一部分，以这些文件中更具体、且与冻结基线一致的约束为准。不要改写设计或另起一套计划。

`CLAUDE_HANDOFF_PROMPT.md` 是用户要求生成的交接材料：不要修改、删除或混入任何 Task commit。若 Task 1 的 protected-worktree 规则要求登记所有未跟踪文件，将它作为 `user-existing` 受保护输入登记即可。

## 3. 已知现场状态：先核验，不要盲信

交接时已观察到：

- review 仓库 `HEAD == origin/main == da089e19be488caa02185a4af189207d57bc55d6`；
- `da089e1` 只改动了：
  - `09/03-provision-and-observe-via-nyxid/02-scheduled-agent-key-production-canary.md`
  - `09/03-provision-and-observe-via-nyxid/index.md`
- 这两个文件是受保护迁移输入，不属于 Task 1；
- Task 1 尚未产生治理文档、脚本实现、测试实现、Task 1 commit 或 72 个远端章节 issues；
- review 工作区已有 `.superpowers/*` 运行态文件；不得提交或破坏 `.superpowers/brainstorm/*`；
- 上游 live HEAD 已继续漂移，最近一次观察为
  `aba74805c6b40f3848a554b85e4192e7c06abfa2`，且上游存在多处用户未提交修改；
- 上游 live HEAD 和 dirty paths 都不是本轮事实基线，也不得被本任务修改；
- 最近一次 live GitHub 查询得到 open `128`、窗口内 closed `161`，与批准的 `126` / `154` 不同。

第一步重新运行只读检查：

```bash
pwd
git status --porcelain=v1
git rev-parse HEAD
git rev-parse origin/main
git -C /Users/eanzhao/Code/aevatar rev-parse HEAD
git -C /Users/eanzhao/Code/aevatar status --porcelain=v1
git -C /Users/eanzhao/Code/aevatar cat-file -e f02aa690bbebb9cabeac30a553d737486b0eb661^{commit}
```

把新出现的非任务改动一律当成用户资产；不得 reset、stash、checkout、clean、覆盖或顺手提交。

## 4. 绝对边界

### 上游只读

- `/Users/eanzhao/Code/aevatar` 只能读，禁止修改、格式化、生成、checkout、reset、stash、clean 或删除任何内容。
- 所有“当前实现”事实只能来自 Git object
  `f02aa690bbebb9cabeac30a553d737486b0eb661:<path>`，或由 Task 1 materializer 从该提交生成的 review 仓库 `.git/aevatar-frozen/<sha>` 快照。
- 不得使用上游 live working tree 来核验路径、行号、项目数量或行为。
- 每个 Task 和恢复后的新会话都重新运行：

```bash
export AEVATAR_FROZEN="$(bash scripts/materialize-frozen-upstream.sh \
  --repo /Users/eanzhao/Code/aevatar \
  --sha f02aa690bbebb9cabeac30a553d737486b0eb661)"
export AEVATAR_SRC="$AEVATAR_FROZEN"
```

### 事实诚实性

- current 论断必须有 E1：冻结提交中的 code、proto、config 或 test。
- canon / Accepted ADR 可说明设计治理，但代码与 canon 冲突时，以冻结代码描述当前行为，并登记 drift。
- closed issue 本身不证明已经落地；必须找到冻结基线中的实现、契约、测试或明确删除证据。
- open issue 只能描述 gap、risk、dispute 或 target state，不得写成 current capability。
- 生产 canary 只能证明绑定了 commit / image / date / environment 的版本化结论，不得外推成当前 HEAD 的普遍事实。
- NyxID、Chrono Sandbox、Ornn 只从 Aevatar adapter、authorization、typed reference、compensation 和 failure boundary 解释，不扩写外部产品内部。
- 找不到证据时删除论断，或诚实降级为 `historical` / `target`；禁止补全想象。

### Git 与工作区

- 每次写入前运行 `git status --porcelain=v1`。
- 只用精确 pathspec 暂存；禁止 `git add .` 和 `git add -A`，Task 19 已批准的原子切换路径数组除外。
- 每个 commit 使用 `git commit --only ... -- <exact paths>`，不得卷入用户已有 staged 内容。
- 不得 force push、rewrite history 或修改既有 commit。
- 用户已经批准按现有计划实施及在通过门槛后创建章节 issues；无需逐步重新询问。

## 5. 立即执行 Task 1，不重新规划

Task 1 的唯一详细 brief 是 `.superpowers/sdd/task-1-brief.md`。严格做真实 RED → GREEN，并且只允许修改以下十个任务路径：

```text
docs/migration/2026-07-25-target-chapters.md
docs/migration/2026-07-25-protected-worktree.md
docs/migration/2026-07-25-chapter-migration-ledger.md
docs/migration/2026-07-25-old-retire-paths.txt
docs/migration/2026-07-25-issue-evidence-ledger.md
docs/migration/2026-07-25-source-matrix.md
scripts/create_issues.py
scripts/snapshot-upstream-issues.py
scripts/materialize-frozen-upstream.sh
scripts/tests/test-doc-checks.sh
```

运行态报告写到 `.superpowers/sdd/task-1-report.md`，不要把 `.superpowers/*` 混入 Task commit。

Task 1 必须产出：

- 精确 72 行目标章节 manifest，不含 index；
- 每个现有旧 Markdown 文件的迁移账本骨架；
- 精确 85 行旧退役路径；
- 受保护工作区账本，只记录非敏感 fingerprint，不复制 secret、token、key、ciphertext 或完整 patch；
- 72 篇 source matrix 骨架；
- frozen-upstream materializer；
- issue snapshot CLI；
- 幂等 exact-scope chapter issue CLI；
- 以下三个测试的真实 RED 证据和最终 GREEN：

```bash
bash scripts/tests/test-doc-checks.sh frozen-upstream
bash scripts/tests/test-doc-checks.sh issue-snapshot
bash scripts/tests/test-doc-checks.sh issue-cli
```

Task 1 完整通过后，只提交上述十个路径：

```text
docs: establish review migration governance
```

Task 1 diff base 是 `da089e1`。提交前和提交后都核验 commit 只包含允许路径。

## 6. Issue cohort 漂移是远端写入硬门槛

批准的历史 cohort 是：

```text
snapshot date: 2026-07-25
open: 126
closed window: 2026-07-06..2026-07-25
closed: 154
total unique membership rows: 280
```

当前 live `128` / `161` 只能作为 drift telemetry，绝不能静默替代批准集合，也不能通过删掉“多出来的”issue 来凑数量。

在创建任何远端章节 issue、做 issue 分类或声称 Task 1 完成前，必须可审计地恢复严格的 126 + 154 membership：

1. 先搜索本仓库 Git 历史、workflow artifacts、本地缓存、临时输出和 GitHub 可获取的历史快照。
2. 若只能用 GitHub REST / GraphQL timeline 重建，必须按 issue 的完整状态事件重放到批准 cutoff，正确处理 `closed → reopened → closed`、边界日期和时区语义。
3. 为状态重放、边界日期、重复项、分页、标题中的 `|` 和 count mismatch 增加 fixture tests。
4. 在 ledger 中保存每个成员和恢复方法，使别人可以复核，不得只保存最终数字。
5. 只有严格得到 280 个唯一 membership rows 后，才允许分类及执行 `scripts/create_issues.py --create`。

如果穷尽安全的恢复方式后仍不能严格恢复批准 cohort：

- 完成 Task 1 中所有不依赖历史 membership 的本地脚本、RED/GREEN 测试、72-row manifest、85-row retire list、protected ledger 和其他安全骨架工作；
- 不创建任何远端 issue；
- 不伪造 issue ledger，不把 128/161 当成新批准基线；
- 不声称 Task 1 完成，也不执行其最终 canonical commit；
- 在 `.superpowers/sdd/task-1-report.md` 写明尝试过的恢复来源、证据和精确阻塞点；
- 最后向用户只报告这个真实 blocker，以及已经安全完成的本地工作。

不要因为这个远端写入门槛而在一开始停止所有本地工作。

## 7. 章节 issue 规则

恢复 cohort 并通过门槛后，幂等创建或复用 72 个章节 issues：

- 每篇实质章节一个独立 issue；
- issue body 必须含 `SCOPE_EXTEND`、完整 approved SHA、精确 target path；
- `scope_paths` 必须只含该一个目标 Markdown 路径；
- dry-run 默认不得产生 GitHub mutation；只有显式 `--create` 才能创建；
- 二次运行不得重复创建；
- 只有 existing issue 的 `scope_paths` 精确等于单个 target path 时才能复用；
- legacy issue `#147` 有六路径 scope，不能复用；必须为
  `09/05-production-canary-and-recovery.md` 新建 exact-scope issue，并在正文中交叉引用 `#147` 作为迁移证据；不得因此修改或关闭 `#147`。

## 8. 接着连续执行 Tasks 2–20

Task 1 完成后，严格按
`docs/superpowers/plans/2026-07-25-aevatar-review-restructure.md`
继续，不等待用户逐 Task 批准：

- Tasks 2–4：升级文档门禁，分类 154 closed + 126 open issues，补齐 migration/source/issue ledgers；
- Tasks 5–18：按依赖顺序重写 `00–13` 的 72 篇实质章节；
- Task 19：只有所有迁移证据通过后，原子更新 14 个 index、`PLAN.md`、`mkdocs.yml`、README、instructions、site/sync/CI，并删除 85 个已审阅旧路径；
- Task 20：全书 fresh verification、四个语义切片的独立 review、demo honesty audit 和最终验证报告。

不要提前改写 block index 或切换 `PLAN.md` / `mkdocs.yml`；在 Task 19 原子切换之前，当前 `00–12` 旧结构仍是 active book，`00–13` 是迁移目标。

## 9. 每章必须遵守的内容契约

每篇实质章节必须：

- 使用中文；路径、代码、标识符和协议词保留英文；
- frontmatter 含：

```yaml
---
status: current
upstream_commit: f02aa690bbebb9cabeac30a553d737486b0eb661
verified_at: 2026-07-25
---
```

- `status` 只能是 `current`、`mixed`、`historical`、`target`；index 使用 `index`；
- 开头列 1–3 个真正支撑整章的 frozen source 路径和有效行号锚点；
- 正文采用设计语言解释职责、边界、协议、状态、不变量和取舍，不堆文件名/行号；
- 至少有两张职责不同的图：一张静态边界/所有权图，一张动态时序/状态/失败恢复图；index 可豁免两图要求；
- 明确回答“为什么是它，不是替代方案”；不能论证时写
  `!!! warning "设计待论证"`，并在 `12/05-open-gaps-and-canon-drift.md` 登记精确位置、缺失证据、owner 和 exit criterion；
- 包含协议与状态深入、最小 demo、边界与演进、3–5 个验收问题；
- demo 状态只能是 `verified-static`、`verified-local`、`verified-production-versioned`；未实际运行不得写“已跑通”；
- 必要的细粒度论断—证据映射放在章末 `<details>`，不让源码引用成为正文骨架；
- 不得整篇复制上游 canon / ADR。

Mermaid 规则：

- 每个 Mermaid block 首行必须有 `%%{init: ...}%%`；
- `flowchart` 标签统一用双引号；
- `sequenceDiagram` 使用计划中的紧凑配置；
- sequence 消息文本禁止 ASCII `;`，改用 `、` 或中文 `；`；
- 必须用 Mermaid 11.15.0 真实解析，不能以 MkDocs build 代替。

## 10. 每章是独立工作单元

对 72 个 target，严格按 plan 的 `Per-chapter work-unit protocol`：

1. 核验 exact-scope issue 和 frozen SHA；
2. 重新枚举并保护非任务改动；
3. 只修改该一个 target 文件；
4. 运行该章的 Markdown、link、Mermaid、placeholder gates；
5. 做独立事实/设计 review，修复 Critical 和 Important findings 后复审；
6. 只提交该一个 target 文件；
7. 核验 commit 精确单路径，用户原 staged paths 保持原状。

共享 governance ledgers 只能由目录协调步骤更新，不能混入 chapter commit。每个目录完成后再做目录级术语、链接和边界 review，并以独立 coordinator commit 提交共享账本。

如果使用子任务或子代理，必须派发具体、非空、单路径 brief，并亲自检查结果。调度失败一次就自行继续，不得反复空派发、空等待或用“继续”消耗用户时间。没有可靠的独立 reviewer 时，执行 fresh-context 两遍 review，并在报告中诚实标注限制；不得省略 review 门槛。

## 11. 导航设计不可回退

Task 19 扩展到 `00–13` 时必须保留已批准的桌面双行导航设计：

- 桌面 tabs 允许换行，完整章名直接可见；
- `mkdocs.yml` 是唯一导航事实源；
- CSS、JavaScript、模板都不得硬编码章节清单；
- 不引入第二份 nav model；
- 窄屏继续使用 MkDocs Material drawer；
- 不为了容纳 14 个 block 而截断、隐藏或仅显示编号。

## 12. 已知迁移期红态

旧书当前 `bash scripts/check-md.sh` 有五个已知 stale-reference failures：

```text
02/05-workflows-walkthrough.md
10/02-codex-shell-vs-aevatar-tools.md
10/12-api-security-audit-and-hardening.md
10/09-studio-console-three-traps.md
07/11-file-handling-end-to-end.md
```

这些是即将退役旧章的已接受 migration red。不要为了临时全绿去篡改旧章；Task 19/20 完成后最终全库必须无豁免全绿。

## 13. Review 与完成声明

每个 Task 完成时：

- 对照设计、plan 和 task brief 做 spec compliance review；
- 做独立 quality / factual review；
- Critical / Important findings 必须修复并复审；
- 记录实际运行的命令、退出码和关键计数；
- 只在 fresh verification 之后提交和宣称通过。

最终至少 fresh-run：

```bash
bash scripts/tests/test-doc-checks.sh all
AEVATAR_SRC="$AEVATAR_FROZEN" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
git status --short --branch
```

同时机械核验：

- 72 篇实质章节；
- 14 个 block indexes；
- 85 个旧退役路径均有迁移证据后才删除；
- `PLAN.md`、target manifest、MkDocs nav、source map 数量和路径一致；
- 154 closed + 126 open issues 各精确分类一次；
- 所有 current/mixed 事实源路径和行号在 frozen SHA 有效；
- 普通章节每篇至少两张职责不同的图；
- 所有 Mermaid 由 11.15.0 真实解析；
- 每章 issue / exact scope / commit / review 一一对应；
- 所有 protected inputs 已无损迁移；
- `/Users/eanzhao/Code/aevatar` 没有任何可归因于本任务的变化。

只有这些 fresh gates、独立 review 和迁移账本全部满足，才能报告“全库重构完成”。不得通过缩小验证范围、隐藏 blocker、伪造 snapshot、保留过时空壳或把 target 写成 current 来换取完成。

## 14. 与用户沟通

- 直接工作，不要反复请求“继续”或重新请求已经给出的批准。
- 工具运行较久时，简短报告当前产物、验证结果和下一步，避免过程性长篇输出。
- 不要发送空计划、空派发或无结果状态更新。
- 真实需要用户决策时，只说明：已经完成什么、精确阻塞证据、为什么无法安全推断、需要用户决定什么。
- 最终回答以结果为主：完成范围、主要结构变化、验证证据、commit、仍存在的真实限制。

现在从核验现场和执行 `.superpowers/sdd/task-1-brief.md` 开始，持续完成整个批准计划。
