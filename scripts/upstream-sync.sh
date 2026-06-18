#!/usr/bin/env bash
# scripts/upstream-sync.sh
#
# 监听 aevatar 上游 feature/integrate 分支的新提交,为受影响的 aevatar-review 章节自动建 GitHub issue。
# 建出的 issue 零 crnd: label,由 consensus-loop 的 default-issue-intake(Path A)自动 claim。
#
# 设计与边界见 docs/upstream-sync.md 与 AGENTS.md。本脚本是 host 工具,不修改 ~/Code/aevatar,
# 不修改 consensus-loop skill 目录。所有运行时事实经 host.env 注入(FI-002)。
#
# 用法:
#   scripts/upstream-sync.sh             # 正常跑(默认)
#   scripts/upstream-sync.sh --dry-run   # 只打印会建什么 issue,不真建
#   scripts/upstream-sync.sh --init      # 首次跑:以当前上游 HEAD 为基线,不建任何 issue
#
# 退出码:0=成功(无论是否建了 issue);1=配置/环境错误;2=上游 git 错误。

set -euo pipefail

# ─── 路径与配置 ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$REPO_ROOT/.config/upstream-sync"
MAP_FILE="$CONFIG_DIR/chapter-source-map.json"
STATE_FILE="$CONFIG_DIR/state.json"
LABEL="upstream-sync"

# ─── 解析参数 ────────────────────────────────────────────────────────────────
DRY_RUN=0
INIT_MODE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --init)    INIT_MODE=1 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 1 ;;
  esac
done

# ─── 加载 host facts(必须经 CONSENSUS_RND_HOST_ENV,FI-002)────────────────
if [[ -z "${CONSENSUS_RND_HOST_ENV:-}" ]]; then
  echo "ERROR: CONSENSUS_RND_HOST_ENV 未设置。请先 'export CONSENSUS_RND_HOST_ENV=.config/consensus-rnd/host.env'" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$CONSENSUS_RND_HOST_ENV"

: "${AEVATAR_UPSTREAM_ROOT:?host.env 必须设置 AEVATAR_UPSTREAM_ROOT(指向 ~/Code/aevatar)}"
: "${GH_REPO_SLUG:?host.env 必须设置 GH_REPO_SLUG}"

if [[ ! -d "$AEVATAR_UPSTREAM_ROOT/.git" ]]; then
  echo "ERROR: AEVATAR_UPSTREAM_ROOT=$AEVATAR_UPSTREAM_ROOT 不是 git 仓库" >&2
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: 未找到 gh CLI" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 未找到 jq" >&2
  exit 1
fi

UPSTREAM_BRANCH="feature/integrate"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

# ─── 读 state ─────────────────────────────────────────────────────────────────
if [[ ! -f "$STATE_FILE" ]]; then
  INIT_MODE=1
fi

# ─── fetch 上游 ───────────────────────────────────────────────────────────────
log "fetch 上游 $UPSTREAM_BRANCH ..."
if ! git -C "$AEVATAR_UPSTREAM_ROOT" fetch origin "$UPSTREAM_BRANCH" --quiet 2>/dev/null; then
  echo "ERROR: git fetch origin $UPSTREAM_BRANCH 失败" >&2
  exit 2
fi
NEW_SHA="$(git -C "$AEVATAR_UPSTREAM_ROOT" rev-parse "origin/$UPSTREAM_BRANCH")"
log "上游 HEAD = ${NEW_SHA:0:12}"

# ─── INIT 模式:确立基线,不建 issue ──────────────────────────────────────────
if [[ "$INIT_MODE" -eq 1 ]]; then
  log "INIT 模式:以当前 HEAD ${NEW_SHA:0:12} 为基线,不建任何 issue。"
  jq -n \
    --arg sha "$NEW_SHA" \
    --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '{last_processed_sha: $sha, last_run_at: $ts, filed_issues: []}' \
    > "$STATE_FILE"
  log "state 已写入 ${STATE_FILE}。下次运行将从此 SHA 开始 diff。"
  exit 0
fi

# ─── 读 last_processed_sha ────────────────────────────────────────────────────
LAST_SHA="$(jq -r '.last_processed_sha' "$STATE_FILE")"
if [[ "$LAST_SHA" = "null" || -z "$LAST_SHA" ]]; then
  log "state 中 last_processed_sha 为空,转入 INIT 模式。"
  jq -n \
    --arg sha "$NEW_SHA" \
    --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '{last_processed_sha: $sha, last_run_at: $ts, filed_issues: []}' \
    > "$STATE_FILE"
  exit 0
fi

if [[ "$LAST_SHA" = "$NEW_SHA" ]]; then
  log "无新提交($LAST_SHA = $NEW_SHA)。退出。"
  jq --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" '.last_run_at = $ts' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
  exit 0
fi

log "检测到新提交区间: ${LAST_SHA:0:12}..${NEW_SHA:0:12}"

# ─── 取变更文件 + commit 列表 ──────────────────────────────────────────────────
# 只看这些顶层目录(章节映射表覆盖范围)
CHANGED_FILES="$(git -C "$AEVATAR_UPSTREAM_ROOT" diff --name-only "$LAST_SHA..$NEW_SHA" -- src/ docs/ agents/ apps/ workflows/ tools/ 2>/dev/null || true)"
if [[ -z "$CHANGED_FILES" ]]; then
  log "区间内无 src/docs/agents/apps/workflows/tools 变更。更新 state 后退出。"
  jq --arg sha "$NEW_SHA" --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '.last_processed_sha = $sha | .last_run_at = $ts' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
  exit 0
fi

# commit 列表(用于过滤噪音 + 写入 issue body)。格式: sha|subject|author|date
COMMITS_RAW="$(git -C "$AEVATAR_UPSTREAM_ROOT" log "$LAST_SHA..$NEW_SHA" --no-merges --format='%H|%s|%an|%ad' --date=short 2>/dev/null || true)"

# 过滤掉纯 chore/test/ci/style/docs:build 前缀的 commit(这些不改变设计语义)
# 注意:docs(canon/adr) 的设计变更不过滤,因为是事实源文档
FILTERED_COMMITS="$(echo "$COMMITS_RAW" | grep -vE '^[a-f0-9]+\|(chore|test|ci|style|revert|perf)\b' || true)"
if [[ -z "$FILTERED_COMMITS" ]]; then
  log "区间内 commit 全部为 chore/test/ci/style/revert/perf,过滤后无设计性变更。更新 state 后退出。"
  jq --arg sha "$NEW_SHA" --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '.last_processed_sha = $sha | .last_run_at = $ts' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
  exit 0
fi

log "设计性 commit 数: $(echo "$FILTERED_COMMITS" | wc -l | tr -d ' ')"

# ─── 构建反向索引(上游路径 → 章节列表)──────────────────────────────────────
# 用 jq 一次性展开映射表 + 别名,生成 "<matched_path_prefix>\t<chapter>" 行,再在 bash 里做前缀匹配。
# 这样避免在 bash 里反复调 jq(N² 问题),一次 jq 预处理 + bash 线性扫描。
build_inverted_index() {
  jq -r '
    .alias_expansion as $ae
    | .chapters
    | to_entries[]
    | select(.key | startswith("_doc") | not)
    | .key as $chapter
    | (
        # 条目可能是 array 或 {paths:[...]} 对象
        (.value | if type=="array" then . else (.paths // []) end)
      )[]
    | . as $entry
    # 展开别名:纯 NNNN-slug → docs/adr/NNNN-slug.md
    | (if ($entry | test("^[0-9]{4}-[a-z0-9-]+$")) then
         "docs/adr/\($entry).md"
       # canon 关键字(精确匹配 alias_expansion.canon 的 key)
       elif ($ae.canon // {}) | has($entry) then
         $ae.canon[$entry]
       else
         $entry
       end) as $expanded
    | "\($expanded)\t\($chapter)"
  ' "$MAP_FILE"
}

log "构建反向索引..."
INVERTED_INDEX="$(build_inverted_index)"
INDEX_LINES=$(echo "$INVERTED_INDEX" | wc -l | tr -d ' ')
log "反向索引条目数: $INDEX_LINES"

# ─── 对每个变更文件,找出受影响的章节 ──────────────────────────────────────────
# 匹配规则:
#   索引条目以 '/' 结尾 → 变更文件以此前缀开头即命中
#   否则 → 精确相等命中
# 输出: 临时文件 "<chapter>\t<changed_file>" 每行一个
AFFECTED_TMP="$(mktemp)"
trap 'rm -f "$AFFECTED_TMP"' EXIT

while IFS= read -r changed; do
  [[ -z "$changed" ]] && continue
  while IFS=$'\t' read -r entry chapter; do
    [[ -z "$entry" || -z "$chapter" ]] && continue
    if [[ "$entry" == */ ]]; then
      # 目录前缀匹配
      if [[ "$changed" == "$entry"* ]]; then
        printf '%s\t%s\n' "$chapter" "$changed" >> "$AFFECTED_TMP"
      fi
    else
      # 精确文件匹配
      if [[ "$changed" == "$entry" ]]; then
        printf '%s\t%s\n' "$chapter" "$changed" >> "$AFFECTED_TMP"
      fi
    fi
  done <<< "$INVERTED_INDEX"
done <<< "$CHANGED_FILES"

# 去重 + 按章节聚合
AFFECTED_CHAPTERS="$(awk -F'\t' '{print $1}' "$AFFECTED_TMP" | sort -u)"
CHAP_COUNT=$(echo "$AFFECTED_CHAPTERS" | grep -c . || true)

if [[ "$CHAP_COUNT" -eq 0 ]]; then
  log "变更文件未命中任何章节映射。可能命中未覆盖的目录。更新 state 后退出。"
  jq --arg sha "$NEW_SHA" --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '.last_processed_sha = $sha | .last_run_at = $ts' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
  exit 0
fi

log "受影响章节: $CHAP_COUNT 个"

# ─── 节流提示(consensus-loop 的 cooldown/cap 约束)─────────────────────────────
if [[ "$CHAP_COUNT" -gt 3 ]]; then
  log "提示: 受影响章节 > 3。consensus-loop 的 ACTIVE_DESIGN_CAP=3 + CLAIM_COOLDOWN=3600s,"
  log "      实际消化速度约 1 章/小时。其余 issue 会排队等待 claim,不会丢失。"
fi

# ─── 为每个章节建 issue ────────────────────────────────────────────────────────
SHORT_NEW="${NEW_SHA:0:12}"
SHORT_LAST="${LAST_SHA:0:12}"

# 取该章节对应的变更文件(聚合)
chapter_changed_files() {
  local chapter="$1"
  awk -F'\t' -v c="$chapter" '$1==c {print $2}' "$AFFECTED_TMP" | sort -u
}

# 取该章节对应的 commit(整个区间的,因为 commit 范围是全局的)
commits_block() {
  echo "$FILTERED_COMMITS" | while IFS='|' read -r sha subject author date; do
    printf -- '- `%s` %s — @%s %s\n' "$sha" "$subject" "$author" "$date"
  done
}

COMMITS_BLOCK="$(commits_block)"

# 变更规模评估
FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
COMMIT_COUNT=$(echo "$FILTERED_COMMITS" | wc -l | tr -d ' ')
if [[ "$FILE_COUNT" -gt 15 || "$COMMIT_COUNT" -gt 8 ]]; then
  SCALE="major"
else
  SCALE="minor"
fi

# 章节标题(从章节文件第一行 # 标题取)。永远返回非空字符串(兜底 basename)。
chapter_title() {
  local chapter="$1"
  local fpath="$REPO_ROOT/$chapter"
  local t=""
  if [[ -f "$fpath" ]]; then
    # grep 无匹配时返回非零,管道末尾 || true 防 pipefail;再测空。
    t="$(head -20 "$fpath" | grep -m1 '^# ' | sed 's/^# *//' || true)"
  fi
  if [[ -z "$t" ]]; then
    t="$(basename "$chapter" .md)"
  fi
  printf '%s' "$t"
}

# 已 filed 去重:检查 state.json.filed_issues 是否已有同 chapter + 同 sha 区间
already_filed_in_state() {
  local chapter="$1"
  jq -e --arg c "$chapter" --arg sha "$NEW_SHA" \
    '.filed_issues[] | select(.chapter==$c and .sha_end==$sha)' "$STATE_FILE" >/dev/null 2>&1
}

# GitHub 兜底去重:搜同 chapter 在 body 里且仍 open 的 issue
already_open_on_github() {
  local chapter="$1"
  gh issue list --repo "$GH_REPO_SLUG" --state open --search "$chapter in:body" --label "$LABEL" --limit 5 --json number,title 2>/dev/null \
    | jq -e '.[0]' >/dev/null 2>&1
}

CREATED_COUNT=0
SKIPPED_COUNT=0

while IFS= read -r chapter; do
  [[ -z "$chapter" ]] && continue
  title="$(chapter_title "$chapter")"
  changed_list="$(chapter_changed_files "$chapter")"
  files_block="$(echo "$changed_list" | sed 's/^/- `/; s/$/`/')"

  # 去重
  if already_filed_in_state "$chapter"; then
    log "SKIP(已 filed in state): $chapter"
    SKIPPED_COUNT=$((SKIPPED_COUNT+1))
    continue
  fi
  if already_open_on_github "$chapter"; then
    log "SKIP(已有 open issue on GitHub): $chapter"
    SKIPPED_COUNT=$((SKIPPED_COUNT+1))
    continue
  fi

  # 构建 body(变量全部显式 ${} 界定,避免全角字符干扰 bash 变量名解析)
  read -r -d '' BODY <<EOF || true
### 触发

上游 \`aelf:aevatarAI/aevatar\` \`${UPSTREAM_BRANCH}\` 新提交,可能影响本章节文档。

### 受影响章节

\`${chapter}\`(${title})

### 触发 commit

${COMMITS_BLOCK}

### 变更的上游源码(事实源)

${files_block}

### 任务

请 review 上述变更是否需要更新本章节文档:

- 若需更新:说明改什么(设计语义 / 图 / 示例),按 AGENTS.md v2 写作三原则执行(设计导向 / 每段有图 / 每段论证正当性)。
- 若无需更新:关闭本 issue 并说明理由(如:纯实现重构,设计语义未变)。

### 变更规模评估(供参考)

**${SCALE}** —— ${COMMIT_COUNT} 个设计性 commit / ${FILE_COUNT} 个变更文件 / 区间 \`${SHORT_LAST}..${SHORT_NEW}\`

> 本 issue 由 \`scripts/upstream-sync.sh\` 自动生成。label \`upstream-sync\` 仅供人审查询;consensus-loop 会通过 default-issue-intake 自动 claim。
EOF

  ISSUE_TITLE="【同步】${chapter} — ${SHORT_NEW} 上游 ${UPSTREAM_BRANCH} 变更可能影响「${title}」"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN 会建 issue: $chapter"
    echo "  标题: $ISSUE_TITLE"
    echo "  变更文件数: $(echo "$changed_list" | wc -l | tr -d ' ')"
    echo "  规模: $SCALE"
    CREATED_COUNT=$((CREATED_COUNT+1))
    continue
  fi

  # 确认 label 存在(幂等;失败不阻断)
  gh label create "$LABEL" --repo "$GH_REPO_SLUG" --description "upstream-sync 自动建的同步 issue" --color "5319E7" --force >/dev/null 2>&1 || true

  ISSUE_URL="$(gh issue create \
    --repo "$GH_REPO_SLUG" \
    --title "$ISSUE_TITLE" \
    --body "$BODY" \
    --label "$LABEL" 2>&1)" || {
      log "WARN: 建 issue 失败 ($chapter): $ISSUE_URL"
      continue
    }
  ISSUE_NUM="$(echo "$ISSUE_URL" | grep -oE '[0-9]+$' || echo "")"
  log "CREATED #$ISSUE_NUM  $chapter  ($SCALE)"
  CREATED_COUNT=$((CREATED_COUNT+1))

  # 记入 state
  jq --arg c "$chapter" --arg s "$NEW_SHA" --arg n "$ISSUE_NUM" --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '.filed_issues += [{chapter: $c, sha_end: $s, issue: $n, filed_at: $ts}]' \
    "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

done <<< "$AFFECTED_CHAPTERS"

# ─── 更新 state.last_processed_sha ───────────────────────────────────────────
if [[ "$DRY_RUN" -eq 0 ]]; then
  jq --arg sha "$NEW_SHA" --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '.last_processed_sha = $sha | .last_run_at = $ts' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
fi

log "完成。created=$CREATED_COUNT skipped=$SKIPPED_COUNT  (dry-run=$DRY_RUN)"
exit 0
