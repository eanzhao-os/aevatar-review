---
name: updating-aevatar-review-docs
description: Use when a user requests an aevatar-review documentation change, a full upstream sync, or a check that Aevatar feature coverage is current.
---

# 更新 Aevatar Review 文档

准确是完成门槛；用增量事实、最小写作范围和并行旧文复核提速。

## 1. 选择模式并守住发布基线

- 未限定主题而要求补充、更新、解释或同步文档，或检查覆盖时，使用 `full`。
- 点名一个 feature、模块、协议、流程或实现细节并要求补充、更新、解释或同步时，使用 `topic` 并保留原始主题文本。
- 查询、审阅或建议只读：不建 issue、不推进状态、不提交、不推送。

读取根 `AGENTS.md`、批准设计、`PLAN.md`、`mkdocs.yml`、状态和完整 `git status`。确认当前仓库为 `aevatar-review`、分支为 `main`、不是 linked worktree 且 index 为空。执行：

```bash
git fetch origin main
BASE_SHA="$(git rev-parse origin/main)"
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py \
  verify-publication --review-root "$PWD" --base-sha "$BASE_SHA" --phase base
```

该检查要求本地 `HEAD == BASE_SHA == origin/main`；失败即停止。既有修改归用户所有；目标文件重叠时停止，非重叠文件永不暂存。

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

先按计划语义路径构造 `SELECT_ARGS+=(--changed-chapter "$path")`；新章再构造 `ISSUE_ARGS+=(--new-chapter-issue "$path=$url")`。从实际 Git diff 中逐个选择非章节的结构语义路径（导航、source map、索引或资源），构造 `STRUCTURAL_ARGS+=(--structural-path "$path")`。运行：

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py select-review \
  --state .config/aevatar-doc-update/state.json --plan PLAN.md \
  --facts .superpowers/aevatar-doc-update/prepared.json --sample-size 6 \
  "${SELECT_ARGS[@]}" "${ISSUE_ARGS[@]}" "${STRUCTURAL_ARGS[@]}" \
  --output .superpowers/aevatar-doc-update/provisional.json
```

立即调度恰好一个未参与写作、无继承作者上下文的只读 reviewer，使旧文复核与写作并行。先检查实际调度工具 schema，只发送它支持的字段：

1. 标准 `spawn_agent` 支持时，传非空 `task_name`、自包含非空 `message`、`fork_turns: "none"` 和显式可用的 reviewer model；
2. 等价 API 用 `fork_context` 表示上下文继承时，传 `fork_context: false` 和显式可用的 reviewer model，并在自包含 `message` 中写入非空 task identifier。

消息只提供根规则、固定目标快照、`provisional.json`、最多 6 篇 `review_sample` 和只读边界；不给作者结论。Reviewer 不修改文件、不建 issue、不推进状态。无法保证 fresh、无上下文继承、只读且独立时停止。

## 4. 写作与最终复核

以固定目标快照为当前事实，保留冻结 frontmatter。正文解释职责、边界、协议、状态、不变量和取舍；事实源入口不超过 3 条高价值路径与锚点。普通章节至少两张合规 Mermaid 图，适用时补最小示例，并区分 current、target、historical/removed。无法证明正当性时标记“设计待论证”并登记 TODO。

写作后从实际 diff 重建 `SELECT_ARGS`、`ISSUE_ARGS` 和 `STRUCTURAL_ARGS`，再次以 `prepared.json` 为输入运行 `select-review`，输出 `final.json`。`final.json.sealed_files` 必须覆盖全部语义章节、轮转 sample 和结构语义路径的当前 SHA-256。若范围扩大或 sample 改变，把新增范围交给同一 reviewer。随后让它核验全部 sealed path，并按路径返回 `pass` 或 findings。修复 blocking finding 后必须重新生成 `final.json` 并交回同一 reviewer 复核；reviewer 不可用就停止。作者自审不能替代独立复核。

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

任一命令失败即停止，不推进状态。把事实写入仓库内忽略目录下两个 JSON；它们只记录可验证的工作流事实，不证明 reviewer 的密码学身份。两者的 `facts_sha256` 都必须等于 `final.json.facts_sha256`。

Reviewer evidence 最小 schema（`results` 必须与 `sealed_files` 路径集合完全相等且全部为 `pass`）：

```json
{
  "schema_version": 1,
  "facts_sha256": "<final facts SHA-256>",
  "reviewer": {
    "task_id": "<non-empty task id>",
    "model": "<explicit model>",
    "fresh_context": true,
    "read_only": true,
    "independent": true
  },
  "results": {"01/01-example.md": "pass"},
  "blocking_findings": []
}
```

Gate evidence 最小 schema；五个必需 gate 不得缺失或重名，所有必需或附加 gate 的 `exit_code` 都必须是整数 `0`：

```json
{
  "schema_version": 1,
  "facts_sha256": "<final facts SHA-256>",
  "gates": [
    {"name": "check-md", "exit_code": 0},
    {"name": "check-links", "exit_code": 0},
    {"name": "check-drift", "exit_code": 0},
    {"name": "check-mermaid", "exit_code": 0},
    {"name": "mkdocs", "exit_code": 0}
  ]
}
```

证据保存为 `.superpowers/aevatar-doc-update/reviewer-evidence.json` 和 `gate-evidence.json` 后运行：

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py commit-state \
  --state .config/aevatar-doc-update/state.json --plan PLAN.md \
  --facts .superpowers/aevatar-doc-update/final.json \
  --completed-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --review-evidence .superpowers/aevatar-doc-update/reviewer-evidence.json \
  --gate-evidence .superpowers/aevatar-doc-update/gate-evidence.json
```

`commit-state` 在稳定的仓库内 lock 上持有 `flock`，重验状态、证据和每个 sealed file 后才原子替换状态。任何文件在 final review 后变化都必须重新选择、复核并运行门禁。只有 `full` 能推进 `synced_upstream_sha`；`topic` 只更新旧文轮转覆盖。任何失败都保留旧状态。

把本轮文档、导航、source map 和状态逐个加入 `OWNED_ARGS+=(--owned-path "$path")`。只用这些显式路径暂存并检查 cached diff。紧邻提交前再次运行 `--phase base`，然后创建一个 `docs:` 提交。提交后和 push 前分别运行：

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py \
  verify-publication --review-root "$PWD" --base-sha "$BASE_SHA" \
  --phase commit "${OWNED_ARGS[@]}"
DOC_SHA="$(python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py \
  verify-publication --review-root "$PWD" --base-sha "$BASE_SHA" \
  --phase push "${OWNED_ARGS[@]}")"
git push origin "$DOC_SHA:main"
```

`commit`/`push` 检查要求 `HEAD^ == BASE_SHA`、只有一个 parent，且完整 `BASE_SHA..HEAD` changed-file 集合与 owned path 集合完全相等；`push` 还要求远端 main 仍为 `BASE_SHA`，并返回已验证的固定 `DOC_SHA`。只 push 该 SHA，不能再次读取可能已推进的 `HEAD`。push 后用 `git ls-remote origin refs/heads/main` 确认远端 SHA 等于 `DOC_SHA`。结果不明先 readback；远端已是目标即成功，明确未更新才允许一次诊断后的重试。禁止自动 merge、rebase、force-push 或顺带提交用户文件。

## 快速检查

| 情况 | 动作 |
|---|---|
| 无新 commit | 仍轮转复核旧正文并跑全量门禁 |
| 未映射路径 | 人工归属或扩章，不得忽略 |
| 上游工作树脏 | 不整理，继续读取 remote ref |
| issue 结果不明 | readback，禁止盲目重试 |
| reviewer 或 gate 失败 | 不推进状态、不提交、不推送 |
| final review 后文件变化 | 重建 final facts、复核并重跑门禁 |
| 本地 HEAD 在发布期间推进 | 保留结果，停止发布 |
| 远端 main 推进 | 保留本地结果，停止发布 |
