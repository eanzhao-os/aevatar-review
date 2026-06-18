#!/usr/bin/env bash
# check-md.sh — aevatar-review 的 BUILD/TEST 校验脚本
#
# 校验目标(文档仓库无编译产物):
#   1. 若存在章节 Markdown 文件(XX/NN-*.md),每篇非空且含「事实源/设计抽象」入口。
#   2. 引用的 aevatar 源码路径(docs/ src/ workflows/ demos/ apps/ tools/)真实存在。
#   3. 02 编排层章节保持证据入口轻量,正文不退回源码文件/Name/行号表骨架。
#
# 作用域:增量友好。优先校验 git diff 中新增/修改的章节文件;若无 diff(干净 main),
# 则回退到校验仓库里已存在的全部章节文件。这样每篇章节 PR 只校验自己,不被其它未写
# 章节拖累;而干净 main 上跑则校验全书完整性。
#
# 环境变量:
#   REPO_ROOT     仓库根(默认脚本上级目录)
#   AEVATAR_SRC   aevatar 源码根(默认 ~/Code/aevatar)
#
# 退出码: 0 = 全部通过; 1 = 有失败项。POSIX/Bash 3.2 兼容(无 mapfile/数组)。
set -uo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_REPO_ROOT="${REPO_ROOT:-}"
if [ -n "$ENV_REPO_ROOT" ]; then
  script_top="$(git -C "$SCRIPT_ROOT" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$SCRIPT_ROOT")"
  env_top="$(git -C "$ENV_REPO_ROOT" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$ENV_REPO_ROOT")"
  if [ "$script_top" = "$env_top" ]; then
    REPO_ROOT="$ENV_REPO_ROOT"
  else
    REPO_ROOT="$SCRIPT_ROOT"
  fi
else
  REPO_ROOT="$SCRIPT_ROOT"
fi
AEVATAR_SRC="${AEVATAR_SRC:-$HOME/Code/aevatar}"

cd "$REPO_ROOT" || { echo "FATAL: cannot cd $REPO_ROOT" >&2; exit 1; }
[ -d "$AEVATAR_SRC" ] || { echo "FATAL: aevatar source not found at $AEVATAR_SRC" >&2; exit 1; }

fail=0
errors_file="$(mktemp)"
work_file="$(mktemp)"
trap 'rm -f "$errors_file" "$work_file"' EXIT

add_error() { printf '%s\n' "$1" >>"$errors_file"; }
error_count() { [ -s "$errors_file" ] && wc -l <"$errors_file" | tr -d ' ' || echo 0; }

# 确定要校验的章节文件集合。
# 增量优先:git diff(工作区 vs HEAD)中的章节 .md;若无 diff 则回退到全部已存在章节。
# 章节文件两种形态都纳入校验:
#   平铺   NN/NN-slug.md                 (00-08 各块)
#   方案子区 NN/NN-slug/NN-slug.md        (09 方案区:每份方案一个子目录)
CHAPTER_RE='^[0-9]{2}/([0-9]{2}-[a-z0-9-]+/)?[0-9]{2}-[a-z0-9-]+\.md$'
chapters_from_diff() {
  git diff --name-only --diff-filter=AM HEAD -- '??/*.md' '??/??-*.md' '??/*/*.md' 2>/dev/null \
    | grep -E "$CHAPTER_RE" || true
}

chapters_all() {
  # 仅收集仓库里真实存在的章节文件(PLAN.md 可能列了还没写的)。
  find . -path './.refactor-loop' -prune -o -path './.worktrees' -prune -o \
    -type f -name '[0-9][0-9]-*.md' -print 2>/dev/null \
    | sed 's|^\./||' \
    | grep -E "$CHAPTER_RE" || true
}

diff_out="$(chapters_from_diff)"
if [ -n "$diff_out" ]; then
  printf '%s\n' "$diff_out" >"$work_file"
  scope="git diff (changed/new chapters)"
else
  chapters_all >"$work_file"
  scope="all existing chapter files"
fi

count=$(wc -l <"$work_file" | tr -d ' ')
echo "check-md: scope=$scope, chapters=$count"

# 若没有章节文件可校验(全新空仓库),直接通过。
if [ "$count" -eq 0 ]; then
  echo "check-md: OK (no chapter files to verify)"
  exit 0
fi

while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  f="$REPO_ROOT/$rel"

  if [ ! -f "$f" ]; then
    add_error "missing chapter file: $rel"
    fail=1
    continue
  fi
  if [ ! -s "$f" ]; then
    add_error "empty chapter file: $rel"
    fail=1
    continue
  fi
  # 每篇应含事实源入口;旧章节的「关键代码」标题仍作为兼容写法通过。
  if ! grep -qiE '事实源|设计抽象|关键代码|关键文件|Key (code|files)|Evidence' "$f"; then
    add_error "$rel: missing 事实源/设计抽象 section"
    fail=1
  fi
  # 抽取引用的 aevatar 源码路径并校验存在(docs/ src/ workflows/ demos/ apps/ tools/)
  while IFS= read -r p; do
    p="${p#\`}"
    p="${p%\`}"
    case "$p" in
      *Code/aevatar/*) p="${p##*Code/aevatar/}";;
      ~/Code/aevatar/*) p="${p#~/Code/aevatar/}";;
    esac
    # strip trailing :line anchor (e.g. WorkflowRunGAgent.cs:36)
    p="${p%:[0-9]*}"
    case "$p" in
      docs/*|src/*|workflows/*|demos/*|apps/*|tools/*)
        if [ ! -e "$AEVATAR_SRC/$p" ]; then
          add_error "$rel: referenced source path does not exist: $p"
          fail=1
        fi
        ;;
    esac
  done < <(grep -oE '`[^`]*(docs|src|workflows|demos|apps)/[^`]+`' "$f")

  case "$rel" in
    02/0[1-7]-*.md)
      if grep -qE '文件 / Name 行|常量行号|\| 行号 \|' "$f"; then
        add_error "$rel: contains legacy file/name/line table wording"
        fail=1
      fi

      diagram_count=$(( $(grep -c '^```mermaid' "$f" || true) + $(grep -c '!\[' "$f" || true) ))
      if [ "$diagram_count" -lt 2 ]; then
        add_error "$rel: expected at least 2 mermaid/image diagrams, found $diagram_count"
        fail=1
      fi

      source_ref_count=$(grep -oE '`((~/Code/aevatar/)?(docs|src|workflows|demos|apps|tools)/[^`]+)`' "$f" | wc -l | tr -d ' ')
      if [ "$source_ref_count" -gt 3 ]; then
        add_error "$rel: expected at most 3 source fact anchors in 02 chapter, found $source_ref_count"
        fail=1
      fi
      ;;
  esac
done <"$work_file"

if [ "$fail" -ne 0 ]; then
  ec=$(error_count)
  echo "--- CHECK-MD FAILURES ($ec) ---"
  [ -s "$errors_file" ] && sed 's/^/  - /' "$errors_file" >&2
  exit 1
fi

echo "check-md: OK ($count chapters verified)"
exit 0
