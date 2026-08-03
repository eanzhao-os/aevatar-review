---
name: updating-aevatar-review-docs
description: Use when a user requests an aevatar-review documentation change, a full upstream sync, or a check that Aevatar feature coverage is current.
---

# 更新 Aevatar Review 文档

准确是完成门槛；用增量事实、最小写作范围和并行旧文复核提速。

## 1. 选择模式并守住发布基线

- 未限定主题而要求“更新、同步、刷新文档”或检查覆盖时，使用 `full`。
- 点名 feature、模块、协议、流程或实现细节时，使用 `topic` 并保留原始主题文本。
- 查询、审阅或建议只读：不建 issue、不推进状态、不提交、不推送。

读取根 `AGENTS.md`、批准设计、`PLAN.md`、`mkdocs.yml`、状态和完整 `git status`。确认当前仓库为 `aevatar-review`、分支为 `main`、不是 linked worktree 且 index 为空。执行 `git fetch origin main`；本地含未在 `origin/main` 的既有提交或双方分叉时停止。记录 `BASE_SHA=$(git rev-parse origin/main)`。既有修改归用户所有；目标文件重叠时停止，非重叠文件永不暂存。

上游只允许 fetch 和读取 Git 对象。禁止 `pull/checkout/switch/reset/clean/stash` 及文件写入；其当前分支、detached HEAD 和脏工作树不阻塞 remote-ref 读取。

## 2. 固定事实

为完整同步设置 `MODE_ARGS=(--mode full)`；为点题更新设置 `MODE_ARGS=(--mode topic --topic "$TOPIC")`。把调用开始前已被用户修改的章节逐个加入 `EXCLUDE_ARGS+=(--exclude-chapter "$path")`，然后运行：

```bash
mkdir -p .superpowers/aevatar-doc-update
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py prepare \
  "${MODE_ARGS[@]}" "${EXCLUDE_ARGS[@]}" \
  --review-root "$PWD" \
  --upstream-repo "${AEVATAR_UPSTREAM_REPO:-$HOME/Code/aevatar}" \
  --state .config/aevatar-doc-update/state.json \
  --map .config/upstream-sync/chapter-source-map.json \
  --snapshot-script scripts/materialize-frozen-upstream.sh \
  --snapshot-root "$(git rev-parse --git-path aevatar-frozen)" \
  --branch feature/integrate \
  --output .superpowers/aevatar-doc-update/prepared.json
```

逐项判断 `commits`、`changes`、`chapter_hits`、`unmapped_changed_files` 和 `architecture_candidates`。禁止按 subject 过滤，也不得把 source map 当作完整性证明。history rewrite 只能报告和人工裁决，不能自动推进；同步对象缺失则停止。

`full` 处理同步水位之后所有真正影响设计的变化。`topic` 只写原始主题和一致性所需文件，不能宣称全书同步，也不能推进同步水位。

## 3. 定位、扩章和启动旧文复核

优先修改能够完整回答读者问题的最少现有章节。独立职责、协议或读者问题确实无处容纳时：

1. 打印 `SCOPE_EXTEND`；
2. 搜索现有正文、`PLAN.md` 和全部 GitHub issues；
3. 选定 block、编号、slug 和目标路径；
4. 创建包含目标 SHA、目标路径、高价值事实源和读者验收问题的 chapter issue；
5. 创建失败或结果不明时按标题、路径和 SHA readback：唯一命中则复用，明确不存在才允许一次纠正后的创建，仍不明则停止；
6. 唯一 issue 确认后，才写新章并更新 `PLAN.md`、`mkdocs.yml`、block index、source map、计数和必要索引。

先按计划语义路径构造 `SELECT_ARGS+=(--changed-chapter "$path")`；新章再构造 `ISSUE_ARGS+=(--new-chapter-issue "$path=$url")`。运行：

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py select-review \
  --state .config/aevatar-doc-update/state.json --plan PLAN.md \
  --facts .superpowers/aevatar-doc-update/prepared.json --sample-size 6 \
  "${SELECT_ARGS[@]}" "${ISSUE_ARGS[@]}" \
  --output .superpowers/aevatar-doc-update/provisional.json
```

立即调度一个未参与写作的新 reviewer，使旧文复核与写作并行。调用必须有非空 `task_name`、自包含非空 `message`、显式 `fork_turns: "none"`，以及当前可用的 reviewer model。消息只提供根规则、固定目标快照、`provisional.json`、最多 6 篇 `review_sample` 和只读边界；不给作者结论。Reviewer 不修改文件、不建 issue、不推进状态。

## 4. 写作与最终复核

以固定目标快照为当前事实，保留冻结 frontmatter。正文解释职责、边界、协议、状态、不变量和取舍；事实源入口不超过 3 条高价值路径与锚点。普通章节至少两张合规 Mermaid 图，适用时补最小示例，并区分 current、target、historical/removed。无法证明正当性时标记“设计待论证”并登记 TODO。

写作后从实际 diff 重建 `SELECT_ARGS` 和 `ISSUE_ARGS`，再次以 `prepared.json` 为输入运行 `select-review`，输出 `final.json`。若语义范围扩大或 sample 改变，把新增范围交给同一 reviewer。随后让它核验全部 `semantic_changed_chapters`，并按章节返回 `blocking/non-blocking` findings。修复 blocking finding 后必须交回同一 reviewer 复核；reviewer 不可用就停止。作者自审不能替代独立复核。

## 5. 门禁、状态和发布

从 `final.json` 读取冻结/目标快照和冻结元数据，设置对应 shell 变量后运行：

```bash
AEVATAR_SRC="$FROZEN_SNAPSHOT" \
  AEVATAR_SRC2="$TARGET_SNAPSHOT" \
  EXPECTED_UPSTREAM_COMMIT="$FROZEN_SHA" \
  EXPECTED_VERIFIED_AT="$FROZEN_VERIFIED_AT" \
  bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
```

任一命令失败即停止，不推进状态。全部通过且 reviewer 对 final facts 中每个语义章节和 sample 都为 pass 后，逐个构造 `REVIEW_ARGS+=(--reviewed-chapter "$path")`，运行：

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py commit-state \
  --state .config/aevatar-doc-update/state.json --plan PLAN.md \
  --facts .superpowers/aevatar-doc-update/final.json \
  --completed-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --gates-passed "${REVIEW_ARGS[@]}"
```

只有 `full` 能推进 `synced_upstream_sha`；`topic` 只更新旧文轮转覆盖。任何失败都保留旧状态。

只用显式路径暂存本轮文档、导航、source map 和状态；检查 cached diff 后创建一个 `docs:` 提交。再次 `git fetch origin main`，只有 `origin/main` 仍等于 `BASE_SHA` 才执行 `git push origin HEAD:main`。随后用 `git ls-remote origin refs/heads/main` 确认远端 SHA 等于本地 HEAD。结果不明先 readback；远端已是目标即成功，明确未更新才允许一次诊断后的重试。禁止自动 merge、rebase、force-push 或顺带提交用户文件。

## 快速检查

| 情况 | 动作 |
|---|---|
| 无新 commit | 仍轮转复核旧正文并跑全量门禁 |
| 未映射路径 | 人工归属或扩章，不得忽略 |
| 上游工作树脏 | 不整理，继续读取 remote ref |
| issue 结果不明 | readback，禁止盲目重试 |
| reviewer 或 gate 失败 | 不推进状态、不提交、不推送 |
| 远端 main 推进 | 保留本地结果，停止发布 |
