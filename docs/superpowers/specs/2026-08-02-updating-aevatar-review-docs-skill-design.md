# Aevatar Review 文档补充 Skill 设计

> 批准日期：2026-08-03
>
> 适用仓库：`~/Code/aevatar-review`
>
> 只读事实源：`~/Code/aevatar` 的 `origin/feature/integrate`

## 目标

用户只需说明要补充的 feature 或技术细节。仓库内 skill 自动寻找最合适的现有章节，以最新 `origin/feature/integrate` 的固定提交快照为依据完成中文文档更新；全部门禁通过后，只提交本轮文件并直接推送当前仓库的 `origin/main`。

本能力只处理用户明确点名的主题，不顺带扫描或重写全书。

## 方案

采用最小的 repo-local skill：

```text
.agents/skills/updating-aevatar-review-docs/
├── SKILL.md
└── agents/openai.yaml

AGENTS.md  # 登记自然语言触发规则
```

`SKILL.md` 只编排现有 Git 和仓库脚本，不新增状态台账、后台任务、通用工作流引擎或辅助程序。语义定位和写作需要 agent 判断；Git 快照及文档验证直接复用现有脚本。

未采用的方案：

- 只改 `AGENTS.md`：足以记录规则，但触发说明和完整执行契约会持续占用项目上下文。
- 新增自动生成程序：章节归属和设计论证不能可靠机械化，维护成本高于收益。

## 触发

在本仓库中，只要用户要求补充、更新、解释或同步某个 aevatar feature、模块、协议、流程或实现细节，就使用该 skill；用户无需显式点名 skill，也无需重复说明事实分支、验证或推送要求。

查询、审阅或仅要求建议时不触发写入和推送。

## 执行流程

### 1. 建立安全基线

1. 确认当前仓库是 `aevatar-review`，当前分支为 `main`，且不是 linked worktree。
2. 读取根 `AGENTS.md`、`PLAN.md` 和当前 `git status`。
3. `git fetch origin main`，记录 `origin/main` SHA。
4. 本地若含尚未存在于 `origin/main` 的既有提交，立即停止，避免将旧提交顺带推送。
5. 本地仅落后且工作树允许安全快进时，可执行 `git merge --ff-only origin/main`；发生分叉或无法快进时停止。

既有未提交改动归用户所有。它们可以留在工作树中，但一旦与本轮目标文件重叠，就停止并报告；不得 stash、覆盖或顺带提交。

### 2. 固定上游事实

1. 在 `~/Code/aevatar` 执行 `git fetch origin feature/integrate`。
2. 解析一次完整的 `origin/feature/integrate` SHA，并在本轮保持不变。
3. 调用 `scripts/materialize-frozen-upstream.sh` 生成本轮只读快照，并同时复用仓库既定的冻结基线快照。
4. 新增或更新的事实从本轮快照取得；普通章节 frontmatter 继续保留仓库既定的冻结 SHA/date，不顺手移动全书审查基线。

禁止对上游执行 `pull`、`checkout`、`switch`、`reset`、`clean`、`stash` 或文件写入；上游当前分支和工作树状态不影响读取远端提交对象。fetch 或快照失败时停止，不退回到可能陈旧的 live working tree。

### 3. 自动定位

综合搜索以下入口：

- 用户主题及源码标识符；
- `PLAN.md`、现有正文和 block `index.md`；
- `.config/upstream-sync/chapter-source-map.json`；
- 快照中的实现、contract、canon 与 ADR。

优先修改能够完整承接该读者问题的一个现有章节；只有跨越清晰的新职责边界、现有章节无法合理容纳时才扩章。扩章必须先按根 `AGENTS.md` 输出 `SCOPE_EXTEND` 并补 issue，再更新 `PLAN.md`、`mkdocs.yml`、block index 和必要索引。

### 4. 编写

文档遵守仓库写作原则：

- 用职责、边界、协议、状态和不变量解释设计，而不是堆实现清单；
- 开头保留不超过 3 条高价值事实源入口；事实论断必须能回指固定快照中的真实路径和行号；
- 说明“为什么采用当前设计，而不是其他方案”，无法论证时诚实登记 `设计待论证`；
- 流程、状态或分层关系用 Mermaid 表达，普通章节最终至少有两张图；每个 Mermaid 块包含规定的 init 行；
- 适用时补最小 YAML、协议或调用示例；
- 当前实现、目标态、历史或已移除组件必须明确区分。

修改范围只覆盖本主题及维持导航、索引和一致性所必需的文件。

### 5. 验证

按仓库既有“双基准”契约执行全部门禁：`AEVATAR_SRC` 指向 frontmatter 的冻结基线，`AEVATAR_SRC2` 指向本轮 `origin/feature/integrate` 快照。

```bash
AEVATAR_SRC="$FROZEN_SNAPSHOT" AEVATAR_SRC2="$TARGET_SNAPSHOT" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
```

任一门禁失败就停止，不 commit、不 push。只修复本轮造成或本轮目标范围内的失败；无关既有失败应报告，不能扩大范围掩盖。

### 6. 精确提交并推送

1. 仅用显式路径暂存本轮文件，禁止 `git add .` 或 `git add -A`。
2. 检查 cached diff，确认没有用户原有改动、临时文件或上游文件。
3. 创建一个 `docs:` 提交。
4. 再次 `git fetch origin main`；只有远端仍等于步骤 1 记录的 SHA，才执行 `git push origin HEAD:main`。
5. push 后读取 `refs/heads/main`，确认远端 SHA 等于本地 `HEAD`。

远端在本轮期间推进、push 被拒或本地历史分叉时，不自动 merge、rebase 或 force-push；保留本地提交并报告。push 结果不明确时先 readback，远端已是目标 SHA 即视为成功，明确未更新后才允许一次经诊断的重试。

## 完成条件

- 用户主题位于语义最合适的章节，且没有无关改动；
- 新增或更新的事实基于本轮固定的 `origin/feature/integrate` SHA，并与冻结 frontmatter 基线清楚区分；
- 仓库全部文档门禁通过；
- 本轮文件形成一个独立提交；
- `origin/main` 经 readback 确认指向该提交。

若任一条件未满足，结果必须明确标为未完成，并指出停在哪个安全边界。
