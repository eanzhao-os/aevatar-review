# OpenWiki 薄适配改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不生成第二套 wiki、不引入模型运行时的前提下，为现有上游同步增加严格只读预览，并为当前 72 章书目增加一次性本地 OpenWiki 关系图入口。

**Architecture:** 保留 `.config/upstream-sync/chapter-source-map.json`、`PLAN.md` 和 MkDocs 为唯一权威结构。`upstream-sync.sh --dry-run` 通过进程私有 state 副本隔离全部既有写入路径；`visualize-wiki.sh` 从 `PLAN.md` 物化 87 个 Markdown 页面到临时实目录，再仅调用固定版本 OpenWiki 的 `visualize` 子命令。

**Tech Stack:** Bash 3.2+、Git、jq、Node.js 22+、`npx openwiki@0.2.5 visualize`、现有 shell fixture tests、MkDocs Material。

## Global Constraints

- 所有工作直接在 `main` 分支完成；不得创建、切换或使用其他分支及 Git worktree。
- 当前工作树已有用户改动和未跟踪文件；每个任务开始先确认自己的目标路径没有既有改动，只用显式路径暂存，禁止 `git add .` 与 `git add -A`。
- `~/Code/aevatar` 只允许 `fetch` 和读取 Git 对象；不得修改其分支、索引或工作树文件。
- OpenWiki 固定为 npm `openwiki@0.2.5`，调研源码固定为 commit `0aa6ddcb57464b1541fe3457c4331418c3fdf28e`。
- 只允许调用 `openwiki visualize`；不得调用 `init`、`update`、agent chat、connector、telemetry 或定时生成。
- 不新增 `package.json`、lockfile、`.openwikiignore`、`.last-update.json`、仓库内 `openwiki/` 或任何 LLM/API key 配置。
- 不修改 `00`–`13`、`PLAN.md`、`mkdocs.yml`、章节 frontmatter 或冻结上游 SHA/date。
- 本地 visualizer 需要 Node.js major version `>=22`；自动测试必须 fake `node` / `npx`，不能访问 npm、GitHub 或真实上游。
- 图谱 Markdown 集合必须恰好是 `docs/index.md`、14 个 block `index.md` 和 `PLAN.md` 的 72 个完成章节，共 87 个节点；书目外 Markdown 不得进入镜像。
- 所有文件编辑使用 `apply_patch`；格式化或设置 executable bit 可使用对应原生命令。

## File Structure

| 文件 | 职责 |
|---|---|
| `scripts/upstream-sync.sh` | 保留现有影响映射与 issue 流程；将 dry-run 的 state 读写重定向到进程私有副本 |
| `scripts/visualize-wiki.sh` | 验证书目与 Node 环境，物化临时 wiki，前台启动固定版本 visualizer 并清理 |
| `scripts/tests/test-doc-checks.sh` | 提供无网络 `openwiki-adapter` fixture suite，覆盖同步预览、镜像范围、退出码和清理 |
| `.github/workflows/docs.yml` | 在部署前运行适配 suite；不安装或启动真实 OpenWiki |
| `README.md` | 暴露本地知识图入口、Node 下限和无 LLM 边界 |
| `docs/upstream-sync.md` | 明确 `--dry-run` 对 state 与 GitHub mutation 的零写入语义 |

---

### Task 1: 让 `upstream-sync --dry-run` 在所有路径零写入

**Files:**
- Modify: `scripts/tests/test-doc-checks.sh:4-10,642-678`
- Modify: `scripts/upstream-sync.sh:19-39,70-110,118-136,179-208`

**Interfaces:**
- Consumes: `CONSENSUS_RND_HOST_ENV` 指向的 host env；其中提供 `AEVATAR_UPSTREAM_ROOT` 和 `GH_REPO_SLUG`；现有 `chapter-source-map.json` 的 `chapters` / `alias_expansion` 结构。
- Produces: `bash scripts/upstream-sync.sh --dry-run` 和 `--init --dry-run`；允许 fetch 与 GitHub `issue list` 只读查询，但真实 `.config/upstream-sync/state.json` 字节不变且不调用 `gh label create` / `gh issue create`。
- Produces: `bash scripts/tests/test-doc-checks.sh openwiki-adapter` suite 名称，Task 2 和 Task 3 在同一 suite 中追加断言。

- [ ] **Step 1: 确认目标文件没有用户既有改动**

Run:

```bash
git branch --show-current
git status --short -- scripts/upstream-sync.sh scripts/tests/test-doc-checks.sh
```

Expected: 第一行是 `main`；两个目标路径没有输出。若任一路径已有改动，停止并先与用户确认归属。

- [ ] **Step 2: 在现有 shell test runner 中加入失败的 dry-run fixture**

用 `apply_patch` 在 `test_validators` 之后、`run_suite` 之前加入以下函数；同时把 usage、`run_suite` case 和 `all` 循环加入 `openwiki-adapter`：

```bash
test_openwiki_adapter() {
  local tmp review upstream remote fakebin base head
  tmp="$(mktemp -d)"
  review="$tmp/review"
  upstream="$tmp/upstream"
  remote="$tmp/upstream.git"
  fakebin="$tmp/bin"
  mkdir -p "$review/scripts" "$review/.config/upstream-sync" \
    "$review/.config/consensus-rnd" "$review/00" "$fakebin"
  cp "$ROOT/scripts/upstream-sync.sh" "$review/scripts/upstream-sync.sh"

  git init --bare -q "$remote"
  git clone -q "$remote" "$upstream"
  (
    cd "$upstream" || exit 1
    git config user.email fixture@example.invalid
    git config user.name fixture
    git switch -qc feature/integrate
    mkdir -p src
    printf 'initial\n' > src/demo.cs
    git add -- src/demo.cs
    git commit -qm 'feat: initial demo'
    git push -qu origin feature/integrate
  ) || { fail "openwiki-adapter: upstream fixture setup failed"; rm -rf "$tmp"; return; }
  base="$(git -C "$upstream" rev-parse HEAD)"
  (
    cd "$upstream" || exit 1
    printf 'changed\n' > src/demo.cs
    git add -- src/demo.cs
    git commit -qm 'feat: change demo'
    git push -q
  ) || { fail "openwiki-adapter: upstream fixture update failed"; rm -rf "$tmp"; return; }
  head="$(git -C "$upstream" rev-parse HEAD)"

  printf '%s\n' \
    '{"alias_expansion":{"canon":{}},"chapters":{"00/01-demo.md":["src/demo.cs"]}}' \
    > "$review/.config/upstream-sync/chapter-source-map.json"
  printf '# Demo chapter\n' > "$review/00/01-demo.md"
  printf 'AEVATAR_UPSTREAM_ROOT="%s"\nGH_REPO_SLUG="fixture/review"\n' "$upstream" \
    > "$review/.config/consensus-rnd/host.env"
  cat > "$fakebin/gh" <<'FAKE_GH'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$GH_CALL_LOG"
if [ "${1:-} ${2:-}" = "issue list" ]; then
  if [ "${GH_LIST_FAIL:-0}" = 1 ]; then
    printf 'fixture GitHub unavailable\n' >&2
    exit 91
  fi
  printf '[]\n'
  exit 0
fi
printf 'unexpected mutation: %s\n' "$*" >&2
exit 90
FAKE_GH
  chmod +x "$fakebin/gh"

  printf '{"last_processed_sha":"%s","last_run_at":"fixed","filed_issues":[]}\n' "$base" \
    > "$review/.config/upstream-sync/state.json"
  cp "$review/.config/upstream-sync/state.json" "$tmp/state.before"
  : > "$tmp/gh.log"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/hit.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: mapped dry-run exits zero"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: mapped dry-run changed state"
  assert_contains "$tmp/hit.log" "${base:0:12}..${head:0:12}" \
    "openwiki-adapter: dry-run names SHA range"
  assert_contains "$tmp/hit.log" "00/01-demo.md" "openwiki-adapter: dry-run names chapter"
  assert_contains "$tmp/hit.log" "src/demo.cs" "openwiki-adapter: dry-run names source"
  assert_contains "$tmp/hit.log" "规模: minor" "openwiki-adapter: dry-run names scale"
  if grep -Eq '(^| )(label|issue) create( |$)' "$tmp/gh.log"; then
    fail "openwiki-adapter: dry-run attempted GitHub mutation"
  fi

  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" GH_LIST_FAIL=1 \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/gh-fail.log" 2>&1
  assert_eq "1" "$?" "openwiki-adapter: GitHub lookup failure is explicit"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: failed GitHub lookup changed state"
  assert_contains "$tmp/gh-fail.log" "GitHub issue list 失败" \
    "openwiki-adapter: GitHub lookup failure is diagnosed"

  base="$head"
  (
    cd "$upstream" || exit 1
    printf 'outside mapped roots\n' > README.md
    git add -- README.md
    git commit -qm 'feat: update repository note'
    git push -q
  ) || { fail "openwiki-adapter: unrelated commit setup failed"; rm -rf "$tmp"; return; }
  head="$(git -C "$upstream" rev-parse HEAD)"
  printf '{"last_processed_sha":"%s","last_run_at":"fixed","filed_issues":[]}\n' "$base" \
    > "$review/.config/upstream-sync/state.json"
  cp "$review/.config/upstream-sync/state.json" "$tmp/state.before"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/unrelated.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: unrelated dry-run exits zero"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: unrelated dry-run changed state"

  base="$head"
  (
    cd "$upstream" || exit 1
    printf 'test-only change\n' > src/demo.cs
    git add -- src/demo.cs
    git commit -qm 'test: update demo fixture'
    git push -q
  ) || { fail "openwiki-adapter: filtered commit setup failed"; rm -rf "$tmp"; return; }
  head="$(git -C "$upstream" rev-parse HEAD)"
  printf '{"last_processed_sha":"%s","last_run_at":"fixed","filed_issues":[]}\n' "$base" \
    > "$review/.config/upstream-sync/state.json"
  cp "$review/.config/upstream-sync/state.json" "$tmp/state.before"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/filtered.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: filtered dry-run exits zero"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: filtered dry-run changed state"

  base="$head"
  (
    cd "$upstream" || exit 1
    printf 'unmapped\n' > src/unmapped.cs
    git add -- src/unmapped.cs
    git commit -qm 'feat: add unmapped source'
    git push -q
  ) || { fail "openwiki-adapter: unmapped commit setup failed"; rm -rf "$tmp"; return; }
  head="$(git -C "$upstream" rev-parse HEAD)"
  printf '{"last_processed_sha":"%s","last_run_at":"fixed","filed_issues":[]}\n' "$base" \
    > "$review/.config/upstream-sync/state.json"
  cp "$review/.config/upstream-sync/state.json" "$tmp/state.before"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/unmapped.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: unmapped dry-run exits zero"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: unmapped dry-run changed state"

  printf '{"last_processed_sha":null,"last_run_at":"fixed","filed_issues":[]}\n' \
    > "$review/.config/upstream-sync/state.json"
  cp "$review/.config/upstream-sync/state.json" "$tmp/state.before"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/null-sha.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: null-SHA dry-run exits zero"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: null-SHA dry-run changed state"

  printf '{"last_processed_sha":"%s","last_run_at":"fixed","filed_issues":[]}\n' "$head" \
    > "$review/.config/upstream-sync/state.json"
  cp "$review/.config/upstream-sync/state.json" "$tmp/state.before"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/no-change.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: no-change dry-run exits zero"
  cmp -s "$tmp/state.before" "$review/.config/upstream-sync/state.json" || \
    fail "openwiki-adapter: no-change dry-run changed state"

  rm -f "$review/.config/upstream-sync/state.json"
  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --init --dry-run > "$tmp/init.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: init dry-run exits zero"
  if [ -e "$review/.config/upstream-sync/state.json" ]; then
    fail "openwiki-adapter: init dry-run created state"
  fi
  assert_contains "$tmp/init.log" "state 保持不变" "openwiki-adapter: init explains no write"

  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --dry-run > "$tmp/implicit-init.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: missing-state dry-run exits zero"
  if [ -e "$review/.config/upstream-sync/state.json" ]; then
    fail "openwiki-adapter: missing-state dry-run created state"
  fi

  PATH="$fakebin:$PATH" GH_CALL_LOG="$tmp/gh.log" \
    CONSENSUS_RND_HOST_ENV="$review/.config/consensus-rnd/host.env" \
    bash "$review/scripts/upstream-sync.sh" --init > "$tmp/real-init.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: real init exits zero"
  assert_eq "$head" \
    "$(jq -r '.last_processed_sha' "$review/.config/upstream-sync/state.json")" \
    "openwiki-adapter: real init writes current upstream SHA"

  rm -rf "$tmp"
}
```

分发改为：

```bash
    openwiki-adapter) test_openwiki_adapter ;;
```

usage 与 `all` 列表分别加入 `openwiki-adapter`；`all` 循环最终为：

```bash
for suite in frozen-upstream issue-snapshot issue-replay issue-cli validators openwiki-adapter; do
```

- [ ] **Step 3: 运行新 suite，确认当前实现会失败**

Run:

```bash
bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

Expected: suite 非零退出，至少报告 GitHub 查询故障、无相关文件、纯过滤 commit、零映射命中、空 SHA、无变化和初始化等 dry-run 分支的失败；不得访问真实 GitHub。

- [ ] **Step 4: 用一个进程私有 state 副本隔离所有 dry-run 写入点**

用 `apply_patch` 在参数解析后、读取 state 前加入以下状态隔离；把原来的 `STATE_FILE` 定义改名为 `REAL_STATE_FILE`：

```bash
REAL_STATE_FILE="$CONFIG_DIR/state.json"
STATE_FILE="$REAL_STATE_FILE"
DRY_STATE_FILE=""
AFFECTED_TMP=""

cleanup() {
  [ -z "$AFFECTED_TMP" ] || rm -f "$AFFECTED_TMP"
  [ -z "$DRY_STATE_FILE" ] || rm -f "$DRY_STATE_FILE" "$DRY_STATE_FILE.tmp"
}
trap cleanup EXIT

if [[ "$DRY_RUN" -eq 1 ]]; then
  DRY_STATE_FILE="$(mktemp "${TMPDIR:-/tmp}/aevatar-review-upstream-sync.XXXXXX")"
  if [[ -f "$REAL_STATE_FILE" ]]; then
    cp "$REAL_STATE_FILE" "$DRY_STATE_FILE"
  else
    rm -f "$DRY_STATE_FILE"
  fi
  STATE_FILE="$DRY_STATE_FILE"
fi
```

删除后面会覆盖全局 cleanup 的这行：

```bash
trap 'rm -f "$AFFECTED_TMP"' EXIT
```

在 INIT 分支中，fetch 和解析 HEAD 后先给 dry-run 单独退出，真实模式才写基线：

```bash
if [[ "$INIT_MODE" -eq 1 ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN INIT 模式:将以当前 HEAD ${NEW_SHA:0:12} 为基线；state 保持不变。"
    exit 0
  fi
  log "INIT 模式:以当前 HEAD ${NEW_SHA:0:12} 为基线,不建任何 issue。"
  jq -n \
    --arg sha "$NEW_SHA" \
    --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '{last_processed_sha: $sha, last_run_at: $ts, filed_issues: []}' \
    > "$STATE_FILE"
  log "state 已写入 ${REAL_STATE_FILE}。下次运行将从此 SHA 开始 diff。"
  exit 0
fi
```

把 `LAST_SHA` 为空分支完整替换为：

```bash
if [[ "$LAST_SHA" = "null" || -z "$LAST_SHA" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN:state 中 last_processed_sha 为空；将采用当前 HEAD ${NEW_SHA:0:12}，state 保持不变。"
    exit 0
  fi
  log "state 中 last_processed_sha 为空,转入 INIT 模式。"
  jq -n \
    --arg sha "$NEW_SHA" \
    --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '{last_processed_sha: $sha, last_run_at: $ts, filed_issues: []}' \
    > "$STATE_FILE"
  exit 0
fi
```

紧接该分支定义一次退出文案：

```bash
STATE_RESULT="更新 state 后退出"
[[ "$DRY_RUN" -eq 1 ]] && STATE_RESULT="state 保持不变并退出"
```

其他 early-exit 的 jq 写入无需逐个加 guard，因为 dry-run 时它们只会写进 `DRY_STATE_FILE`。把四个日志分别改为：

```bash
log "无新提交($LAST_SHA = $NEW_SHA)。${STATE_RESULT}。"
log "区间内无 src/docs/agents/apps/workflows/tools 变更。${STATE_RESULT}。"
log "区间内 commit 全部为 chore/test/ci/style/revert/perf,过滤后无设计性变更。${STATE_RESULT}。"
log "变更文件未命中任何章节映射。可能命中未覆盖的目录。${STATE_RESULT}。"
```

保留每个日志后现有的 jq 更新和 `exit 0`。非 dry-run 的 state 路径和 issue 行为保持原样。

把 dry-run 命中输出补全为章节、规模和真实变更文件：

```bash
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN 会建 issue: $chapter"
    echo "  标题: $ISSUE_TITLE"
    echo "  变更文件:"
    echo "$changed_list" | sed 's/^/    - /'
    echo "  规模: $SCALE"
    CREATED_COUNT=$((CREATED_COUNT+1))
    continue
  fi
```

同时让 GitHub 去重查询区分“没有命中”和“查询失败”，避免在外部状态未知时继续进入 mutation 流程：

```bash
already_open_on_github() {
  local chapter="$1" response
  if ! response="$(gh issue list --repo "$GH_REPO_SLUG" --state open \
    --search "$chapter in:body" --label "$LABEL" --limit 5 \
    --json number,title 2>&1)"; then
    log "ERROR: GitHub issue list 失败 ($chapter): $response"
    return 2
  fi
  if ! jq -e 'type == "array"' <<< "$response" >/dev/null 2>&1; then
    log "ERROR: GitHub issue list 返回无效 JSON ($chapter)"
    return 2
  fi
  jq -e '.[0]' <<< "$response" >/dev/null 2>&1
}
```

调用点不能继续用一个裸 `if` 吞掉状态 `2`：

```bash
  if already_open_on_github "$chapter"; then
    log "SKIP(已有 open issue on GitHub): $chapter"
    SKIPPED_COUNT=$((SKIPPED_COUNT+1))
    continue
  else
    lookup_status=$?
    [[ "$lookup_status" -ne 2 ]] || exit 1
  fi
```

`lookup_status=1` 表示查询成功且没有重复 issue；`2` 表示外部状态未知，脚本以 `1` 退出且不推进真实 state。

- [ ] **Step 5: 运行语法检查和 adapter suite，确认变绿**

Run:

```bash
bash -n scripts/upstream-sync.sh scripts/tests/test-doc-checks.sh
bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

Expected: 两条命令退出 `0`；suite 输出 `openwiki-adapter: PASS`。

- [ ] **Step 6: 提交严格只读预览**

Run:

```bash
git diff --check -- scripts/upstream-sync.sh scripts/tests/test-doc-checks.sh
git add -- scripts/upstream-sync.sh scripts/tests/test-doc-checks.sh
git diff --cached --name-only
git commit -m "fix: make upstream sync dry-run read-only" -- scripts/upstream-sync.sh scripts/tests/test-doc-checks.sh
```

Expected: cached path 只有上述两个文件；commit 成功落在 `main`。

---

### Task 2: 增加临时书目镜像与 OpenWiki visualizer 入口

**Files:**
- Create: `scripts/visualize-wiki.sh`
- Modify: `scripts/tests/test-doc-checks.sh` 中的 `test_openwiki_adapter`

**Interfaces:**
- Consumes: `PLAN.md` 中 `- [x] [<block>/<file>.md](...)` 格式的 72 行；`docs/index.md`；`00/index.md`–`13/index.md`；可选的 `docs/assets` 与 `<block>/assets`。
- Produces: `bash scripts/visualize-wiki.sh [--port N] [--no-open]`；调用 `npx --yes openwiki@0.2.5 visualize <temp-root> ...`，并返回 `npx` 的退出码。固定在用户参数前的 `visualize <temp-root>` 不能被覆盖；`openwiki@0.2.5` 原生拒绝第二个 path 和非 visualizer 选项。
- Invariant: 只接受单层 `00`–`13` 章节路径，拒绝书目数量不是 72、缺文件、缺 block index、Node <22；无论成功、失败或信号退出都清理临时根。

- [ ] **Step 1: 确认 Task 2 目标路径没有用户既有改动**

Run:

```bash
git branch --show-current
git status --short -- scripts/visualize-wiki.sh scripts/tests/test-doc-checks.sh
```

Expected: 第一行是 `main`；`scripts/visualize-wiki.sh` 不存在，测试文件自 Task 1 提交后没有未提交改动。否则停止并确认归属。

- [ ] **Step 2: 扩展 fixture，先描述 87 节点镜像与失败边界**

用 `apply_patch` 在 `test_openwiki_adapter` 的最终 `rm -rf "$tmp"` 之前加入以下代码：

```bash
  cp "$ROOT/scripts/visualize-wiki.sh" "$review/scripts/visualize-wiki.sh" 2>/dev/null || true
  mkdir -p "$review/docs/assets"
  printf '# Fixture home\n' > "$review/docs/index.md"
  printf 'site asset\n' > "$review/docs/assets/site.png"
  : > "$review/PLAN.md"
  local block chapter_number chapter_limit rel wiki_root
  for block in 00 01 02 03 04 05 06 07 08 09 10 11 12 13; do
    mkdir -p "$review/$block"
    printf '# %s index\n' "$block" > "$review/$block/index.md"
    chapter_limit=5
    if [ "$block" = 00 ] || [ "$block" = 01 ]; then
      chapter_limit=6
    fi
    chapter_number=1
    while [ "$chapter_number" -le "$chapter_limit" ]; do
      rel="$block/$(printf '%02d' "$chapter_number")-fixture.md"
      printf '# %s\n\n[index](index.md)\n' "$rel" > "$review/$rel"
      printf -- '- [x] [%s](%s) — `current`\n' "$rel" "$rel" >> "$review/PLAN.md"
      chapter_number=$((chapter_number + 1))
    done
  done
  mkdir -p "$review/00/assets"
  printf 'block asset\n' > "$review/00/assets/block.png"
  printf '# Orphan\n' > "$review/00/99-orphan.md"
  printf '# Outside book\n' > "$review/README.md"

  cat > "$fakebin/node" <<'FAKE_NODE'
#!/usr/bin/env bash
printf '%s\n' "${FAKE_NODE_VERSION:-v22.0.0}"
FAKE_NODE
  cat > "$fakebin/npx" <<'FAKE_NPX'
#!/usr/bin/env bash
printf '%s\n' "$*" > "$FAKE_NPX_ARGS"
wiki_root="${4:-}"
printf '%s\n' "$wiki_root" > "$FAKE_WIKI_ROOT"
(cd "$wiki_root" && find . -type f | LC_ALL=C sort) > "$FAKE_WIKI_TREE"
if [ "${FAKE_NPX_SIGNAL_PARENT:-0}" = 1 ]; then
  kill -TERM "$PPID"
  exit 0
fi
exit "${FAKE_NPX_EXIT:-0}"
FAKE_NPX
  chmod +x "$fakebin/node" "$fakebin/npx"

  PATH="$fakebin:$PATH" FAKE_NPX_ARGS="$tmp/npx.args" \
    FAKE_WIKI_ROOT="$tmp/wiki.root" FAKE_WIKI_TREE="$tmp/wiki.tree" \
    bash "$review/scripts/visualize-wiki.sh" --port 4400 --no-open > "$tmp/visualize.log" 2>&1
  assert_eq "0" "$?" "openwiki-adapter: visualizer wrapper exits zero"
  assert_contains "$tmp/npx.args" "--yes openwiki@0.2.5 visualize" "openwiki-adapter: OpenWiki version is pinned"
  assert_contains "$tmp/npx.args" "--port 4400 --no-open" "openwiki-adapter: visualizer args pass through"
  assert_eq "87" "$(grep -c '\.md$' "$tmp/wiki.tree")" "openwiki-adapter: mirror node count"
  assert_contains "$tmp/wiki.tree" "./index.md" "openwiki-adapter: mirror contains home"
  assert_contains "$tmp/wiki.tree" "./00/index.md" "openwiki-adapter: mirror contains block index"
  assert_contains "$tmp/wiki.tree" "./assets/site.png" "openwiki-adapter: mirror contains site assets"
  assert_contains "$tmp/wiki.tree" "./00/assets/block.png" "openwiki-adapter: mirror contains block assets"
  assert_not_contains "$tmp/wiki.tree" "99-orphan.md" "openwiki-adapter: mirror excludes orphan Markdown"
  assert_not_contains "$tmp/wiki.tree" "README.md" "openwiki-adapter: mirror excludes repository README"
  assert_not_contains "$tmp/wiki.tree" "PLAN.md" "openwiki-adapter: mirror excludes PLAN"
  wiki_root="$(cat "$tmp/wiki.root")"
  if [ -e "$wiki_root" ]; then
    fail "openwiki-adapter: temporary wiki survived successful exit"
  fi
  if [ -e "$review/openwiki" ]; then
    fail "openwiki-adapter: wrapper created repository openwiki directory"
  fi

  mkdir -p "$tmp/no-node-bin"
  ln -s "$(command -v dirname)" "$tmp/no-node-bin/dirname"
  PATH="$tmp/no-node-bin" /bin/bash "$review/scripts/visualize-wiki.sh" \
    > "$tmp/no-node.log" 2>&1
  assert_eq "1" "$?" "openwiki-adapter: missing Node is rejected"
  assert_contains "$tmp/no-node.log" "Node.js 22+ is required" \
    "openwiki-adapter: missing Node is diagnosed"

  mkdir -p "$tmp/no-npx-bin"
  ln -s "$(command -v dirname)" "$tmp/no-npx-bin/dirname"
  ln -s "$fakebin/node" "$tmp/no-npx-bin/node"
  PATH="$tmp/no-npx-bin" /bin/bash "$review/scripts/visualize-wiki.sh" \
    > "$tmp/no-npx.log" 2>&1
  assert_eq "1" "$?" "openwiki-adapter: missing npx is rejected"
  assert_contains "$tmp/no-npx.log" "npx is required" \
    "openwiki-adapter: missing npx is diagnosed"

  : > "$tmp/npx.args"
  PATH="$fakebin:$PATH" FAKE_NODE_VERSION=v20.19.0 \
    FAKE_NPX_ARGS="$tmp/npx.args" FAKE_WIKI_ROOT="$tmp/wiki.root" \
    FAKE_WIKI_TREE="$tmp/wiki.tree" \
    bash "$review/scripts/visualize-wiki.sh" > "$tmp/node20.log" 2>&1
  assert_eq "1" "$?" "openwiki-adapter: Node 20 is rejected"
  assert_eq "" "$(cat "$tmp/npx.args")" "openwiki-adapter: rejected Node never calls npx"

  mv "$review/13/index.md" "$tmp/13-index.md"
  : > "$tmp/npx.args"
  PATH="$fakebin:$PATH" FAKE_NPX_ARGS="$tmp/npx.args" \
    FAKE_WIKI_ROOT="$tmp/wiki.root" FAKE_WIKI_TREE="$tmp/wiki.tree" \
    bash "$review/scripts/visualize-wiki.sh" > "$tmp/missing.log" 2>&1
  assert_eq "1" "$?" "openwiki-adapter: missing block index is rejected"
  assert_contains "$tmp/missing.log" "13/index.md" "openwiki-adapter: missing path is named"
  assert_eq "" "$(cat "$tmp/npx.args")" "openwiki-adapter: invalid book never calls npx"
  mv "$tmp/13-index.md" "$review/13/index.md"

  sed '$d' "$review/PLAN.md" > "$tmp/PLAN-71.md"
  mv "$review/PLAN.md" "$tmp/PLAN-72.md"
  mv "$tmp/PLAN-71.md" "$review/PLAN.md"
  : > "$tmp/npx.args"
  PATH="$fakebin:$PATH" FAKE_NPX_ARGS="$tmp/npx.args" \
    FAKE_WIKI_ROOT="$tmp/wiki.root" FAKE_WIKI_TREE="$tmp/wiki.tree" \
    bash "$review/scripts/visualize-wiki.sh" > "$tmp/count.log" 2>&1
  assert_eq "1" "$?" "openwiki-adapter: 71-chapter PLAN is rejected"
  assert_contains "$tmp/count.log" "must contain 72 completed chapters" \
    "openwiki-adapter: invalid chapter count is diagnosed"
  assert_eq "" "$(cat "$tmp/npx.args")" "openwiki-adapter: invalid count never calls npx"
  mv "$tmp/PLAN-72.md" "$review/PLAN.md"

  PATH="$fakebin:$PATH" FAKE_NPX_EXIT=23 FAKE_NPX_ARGS="$tmp/npx.args" \
    FAKE_WIKI_ROOT="$tmp/wiki.root" FAKE_WIKI_TREE="$tmp/wiki.tree" \
    bash "$review/scripts/visualize-wiki.sh" > "$tmp/npx-fail.log" 2>&1
  assert_eq "23" "$?" "openwiki-adapter: npx exit code is preserved"
  wiki_root="$(cat "$tmp/wiki.root")"
  if [ -e "$wiki_root" ]; then
    fail "openwiki-adapter: temporary wiki survived failed npx"
  fi

  PATH="$fakebin:$PATH" FAKE_NPX_SIGNAL_PARENT=1 \
    FAKE_NPX_ARGS="$tmp/npx.args" FAKE_WIKI_ROOT="$tmp/wiki.root" \
    FAKE_WIKI_TREE="$tmp/wiki.tree" \
    bash "$review/scripts/visualize-wiki.sh" > "$tmp/signal.log" 2>&1
  assert_eq "143" "$?" "openwiki-adapter: TERM exit code is conventional"
  wiki_root="$(cat "$tmp/wiki.root")"
  if [ -e "$wiki_root" ]; then
    fail "openwiki-adapter: temporary wiki survived TERM"
  fi
```

- [ ] **Step 3: 运行 suite，确认入口尚不存在时失败**

Run:

```bash
bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

Expected: 非零退出；visualizer 相关断言失败，首个根因是 `scripts/visualize-wiki.sh` 尚不存在。Task 1 的 dry-run 断言仍通过。

- [ ] **Step 4: 写最小 visualizer wrapper**

用 `apply_patch` 新建 `scripts/visualize-wiki.sh`，内容如下：

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLAN="$REPO_ROOT/PLAN.md"
HOME_PAGE="$REPO_ROOT/docs/index.md"
OPENWIKI_VERSION="0.2.5"
BLOCKS=(00 01 02 03 04 05 06 07 08 09 10 11 12 13)
WIKI_ROOT=""

die() {
  printf 'visualize-wiki: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  [ -z "$WIKI_ROOT" ] || rm -rf "$WIKI_ROOT"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

command -v node >/dev/null 2>&1 || die "Node.js 22+ is required"
command -v npx >/dev/null 2>&1 || die "npx is required"
NODE_VERSION="$(node --version 2>/dev/null || true)"
NODE_MAJOR="$(printf '%s' "$NODE_VERSION" | sed -E 's/^v([0-9]+).*/\1/')"
[[ "$NODE_MAJOR" =~ ^[0-9]+$ ]] || die "cannot parse Node.js version: $NODE_VERSION"
(( NODE_MAJOR >= 22 )) || die "Node.js 22+ is required; found $NODE_VERSION"

[[ -f "$PLAN" ]] || die "missing PLAN.md"
[[ -f "$HOME_PAGE" ]] || die "missing docs/index.md"
[[ ! -L "$PLAN" ]] || die "PLAN.md must be a regular file"
[[ ! -L "$HOME_PAGE" ]] || die "docs/index.md must be a regular file"
for block in "${BLOCKS[@]}"; do
  [[ -f "$REPO_ROOT/$block/index.md" ]] || die "missing $block/index.md"
  [[ ! -L "$REPO_ROOT/$block/index.md" ]] || die "$block/index.md must be a regular file"
done

CHAPTERS=()
while IFS= read -r chapter; do
  [[ "$chapter" =~ ^(0[0-9]|1[0-3])/[^/]+\.md$ ]] || \
    die "invalid completed chapter path in PLAN.md: $chapter"
  [[ "$chapter" != */index.md ]] || die "block index cannot be a completed chapter: $chapter"
  [[ -f "$REPO_ROOT/$chapter" ]] || die "missing completed chapter: $chapter"
  [[ ! -L "$REPO_ROOT/$chapter" ]] || die "completed chapter must be a regular file: $chapter"
  CHAPTERS+=("$chapter")
done < <(sed -n 's/^- \[x\] \[\([^]]*\.md\)\](.*$/\1/p' "$PLAN")
[[ "${#CHAPTERS[@]}" -eq 72 ]] || \
  die "PLAN.md must contain 72 completed chapters; found ${#CHAPTERS[@]}"
UNIQUE_CHAPTER_COUNT="$(printf '%s\n' "${CHAPTERS[@]}" | LC_ALL=C sort -u | wc -l | tr -d ' ')"
[[ "$UNIQUE_CHAPTER_COUNT" -eq 72 ]] || \
  die "PLAN.md completed chapter paths must be unique; found $UNIQUE_CHAPTER_COUNT unique paths"

WIKI_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/aevatar-review-openwiki.XXXXXX")"
cp "$HOME_PAGE" "$WIKI_ROOT/index.md"
for block in "${BLOCKS[@]}"; do
  mkdir -p "$WIKI_ROOT/$block"
  cp "$REPO_ROOT/$block/index.md" "$WIKI_ROOT/$block/index.md"
  if [[ -d "$REPO_ROOT/$block/assets" ]]; then
    cp -R "$REPO_ROOT/$block/assets" "$WIKI_ROOT/$block/assets"
  fi
done
for chapter in "${CHAPTERS[@]}"; do
  cp "$REPO_ROOT/$chapter" "$WIKI_ROOT/$chapter"
done
if [[ -d "$REPO_ROOT/docs/assets" ]]; then
  cp -R "$REPO_ROOT/docs/assets" "$WIKI_ROOT/assets"
fi
MIRROR_NODE_COUNT="$(find "$WIKI_ROOT" -type f -name '*.md' | wc -l | tr -d ' ')"
[[ "$MIRROR_NODE_COUNT" -eq 87 ]] || \
  die "temporary wiki must contain 87 Markdown nodes; found $MIRROR_NODE_COUNT"

npx --yes "openwiki@$OPENWIKI_VERSION" visualize "$WIKI_ROOT" "$@"
```

设置 executable bit：

```bash
chmod +x scripts/visualize-wiki.sh
```

- [ ] **Step 5: 运行语法检查与 adapter suite**

Run:

```bash
bash -n scripts/visualize-wiki.sh scripts/tests/test-doc-checks.sh
bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

Expected: 两条命令退出 `0`；suite 输出 `openwiki-adapter: PASS`，没有网络访问。

- [ ] **Step 6: 提交本地知识图入口**

Run:

```bash
git diff --check -- scripts/visualize-wiki.sh scripts/tests/test-doc-checks.sh
git add -- scripts/visualize-wiki.sh scripts/tests/test-doc-checks.sh
git diff --cached --name-only
git commit -m "feat: add local OpenWiki visualizer" -- scripts/visualize-wiki.sh scripts/tests/test-doc-checks.sh
```

Expected: cached path 只有上述两个文件；新脚本 mode 为 executable；commit 成功落在 `main`。

---

### Task 3: 接入文档、CI 与全量门禁

**Files:**
- Modify: `scripts/tests/test-doc-checks.sh` 中的 `test_openwiki_adapter`
- Modify: `.github/workflows/docs.yml:20-39`
- Modify: `README.md:14-35`
- Modify: `docs/upstream-sync.md:56-84,130-148`

**Interfaces:**
- Consumes: Task 1 的 `openwiki-adapter` suite 和严格 dry-run；Task 2 的 `scripts/visualize-wiki.sh`。
- Produces: README 用户命令、同步 runbook 的零写入承诺、部署前 CI source contract。
- CI contract: 只运行 fake-backed adapter suite，不安装 `openwiki`，不启动浏览器，不变更现有 Node 20 Mermaid 构建环境。

- [ ] **Step 1: 确认 Task 3 目标路径没有用户既有改动**

Run:

```bash
git branch --show-current
git status --short -- scripts/tests/test-doc-checks.sh .github/workflows/docs.yml README.md docs/upstream-sync.md
```

Expected: 第一行是 `main`；四个路径自 Task 2 提交后没有未提交改动。否则停止并确认归属。

- [ ] **Step 2: 先给文档和 CI 加失败的 source-contract 断言**

在 `test_openwiki_adapter` 清理临时目录之前追加：

```bash
  assert_contains "$ROOT/README.md" "bash scripts/visualize-wiki.sh" \
    "openwiki-adapter: README exposes visualizer"
  assert_contains "$ROOT/README.md" "Node.js 22+" \
    "openwiki-adapter: README names Node floor"
  assert_contains "$ROOT/docs/upstream-sync.md" "state.json 保持不变" \
    "openwiki-adapter: runbook promises dry-run state isolation"
  assert_contains "$ROOT/.github/workflows/docs.yml" \
    "bash scripts/tests/test-doc-checks.sh openwiki-adapter" \
    "openwiki-adapter: CI runs adapter suite"
```

- [ ] **Step 3: 运行 suite，确认文档与 CI 契约尚未满足**

Run:

```bash
bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

Expected: 非零退出，仅新增的 README、runbook、CI source-contract 断言失败；Task 1–2 行为断言继续通过。

- [ ] **Step 4: 更新 README 的本地知识图入口**

用 `apply_patch` 在“当前书目”之后加入：

````markdown
## 本地知识图

Node.js 22+ 环境可以把当前首页、14 个 block index 和 `PLAN.md` 中的 72 篇完成章节临时投影为 OpenWiki 关系图：

```bash
bash scripts/visualize-wiki.sh
# 只启动服务，不自动打开浏览器
bash scripts/visualize-wiki.sh --port 4400 --no-open
```

脚本固定调用 `openwiki@0.2.5 visualize`，不运行文档生成 agent，不需要 LLM/API key，也不会在仓库内创建第二套 wiki。首次运行需要 npm 网络，浏览器页面还会从公共 CDN 加载前端库；进程退出后临时镜像自动删除。
````

在 README 的验证代码块首行加入：

```bash
bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

- [ ] **Step 5: 收紧 upstream-sync runbook 的 dry-run 描述**

将“先看会建什么”小节改为：

````markdown
### 严格只读预览

```bash
bash scripts/upstream-sync.sh --dry-run
bash scripts/upstream-sync.sh --init --dry-run
```

两种 dry-run 都可以 fetch 和执行 GitHub `issue list` 只读查询，但不会创建 label/issue，且 `.config/upstream-sync/state.json 保持不变`；没有 state 时也不会创建。只有去掉 `--dry-run` 后，脚本才推进基线或记录已建 issue。
````

并在“边界”列表补一条：

```markdown
- **dry-run 零写入**：允许更新本地 remote-tracking Git 对象和执行 GitHub 只读查询；不写 state，不创建 GitHub 资源。
```

- [ ] **Step 6: 在 docs workflow 中运行 fake-backed adapter suite**

用 `apply_patch` 在 checkout 之后、安装 Python 之前加入：

```yaml
      - name: Validate OpenWiki adapter contracts
        run: bash scripts/tests/test-doc-checks.sh openwiki-adapter
```

不要改变现有 `actions/setup-node` 的 Node 20；真实 visualizer 的 Node 22 下限由 wrapper 和 fake-backed suite 验证，站点 Mermaid 构建继续使用当前版本。

- [ ] **Step 7: 运行 adapter suite 和全部 fixture suites**

Run:

```bash
bash scripts/tests/test-doc-checks.sh openwiki-adapter
bash scripts/tests/test-doc-checks.sh all
```

Expected: 两条命令退出 `0`；每个 suite 均输出 `PASS`。

- [ ] **Step 8: 运行仓库完整文档门禁**

Run:

```bash
FROZEN="$(bash scripts/materialize-frozen-upstream.sh \
  --repo "$HOME/Code/aevatar" \
  --sha f02aa690bbebb9cabeac30a553d737486b0eb661)"
AEVATAR_SRC="$FROZEN" AEVATAR_SRC2="$HOME/Code/aevatar" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  export PUPPETEER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
fi
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
python3 scripts/check-site-ui.py
```

Expected: 每条命令退出 `0`；Markdown、链接、漂移、Mermaid、MkDocs 和站点 UI 全部报告成功。若失败来自本轮范围外的既有问题，保留失败证据并停止，不扩大改动范围掩盖它。

- [ ] **Step 9: 检查范围并提交文档与 CI**

Run:

```bash
git diff --check -- scripts/tests/test-doc-checks.sh .github/workflows/docs.yml README.md docs/upstream-sync.md
git status --short
git diff -- scripts/tests/test-doc-checks.sh .github/workflows/docs.yml README.md docs/upstream-sync.md
git add -- scripts/tests/test-doc-checks.sh .github/workflows/docs.yml README.md docs/upstream-sync.md
git diff --cached --name-only
git commit -m "docs: document OpenWiki adapter workflow" -- \
  scripts/tests/test-doc-checks.sh .github/workflows/docs.yml README.md docs/upstream-sync.md
```

Expected: cached path 只有四个显式文件；用户原有改动和未跟踪文件仍未暂存；commit 成功落在 `main`。

- [ ] **Step 10: 提交后重新验证最终树而非提交前状态**

Run:

```bash
bash scripts/tests/test-doc-checks.sh all
git log -3 --oneline
git status --short --branch
```

Expected: suites 再次全部通过；最近三个实现提交依次覆盖 dry-run、visualizer、文档/CI；工作树只显示任务开始前已有的无关改动或未跟踪文件。不要 push，除非用户另行明确要求。
