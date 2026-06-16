#!/usr/bin/env bash
# check-md.sh — aevatar-review 的 BUILD/TEST 校验脚本
#
# 校验目标(文档仓库无编译产物):
#   1. 若存在章节 Markdown 文件(XX/NN-*.md),每篇非空且含「关键代码」清单。
#   2. 引用的 aevatar 源码路径(docs/ src/ workflows/ demos/ apps/ tools/)真实存在。
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

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
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
chapters_from_diff() {
  git diff --name-only --diff-filter=AM HEAD -- '??/*.md' '??/??-*.md' 2>/dev/null \
    | grep -E '^[0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md$' || true
}

chapters_all() {
  # 仅收集仓库里真实存在的章节文件(PLAN.md 可能列了还没写的)。
  find . -path './.refactor-loop' -prune -o -path './.worktrees' -prune -o \
    -type f -name '[0-9][0-9]-*.md' -print 2>/dev/null \
    | sed 's|^\./||' \
    | grep -E '^[0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md$' || true
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
  # 每篇应含「关键代码」清单(中英任一写法均可)
  if ! grep -qiE '关键代码|关键文件|事实源|Key (code|files)' "$f"; then
    add_error "$rel: missing 关键代码/事实源 section"
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
done <"$work_file"

if [ "$fail" -ne 0 ]; then
  ec=$(error_count)
  echo "--- CHECK-MD FAILURES ($ec) ---"
  [ -s "$errors_file" ] && sed 's/^/  - /' "$errors_file" >&2
  exit 1
fi

echo "check-md: OK ($count chapters verified)"
exit 0
