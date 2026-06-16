#!/usr/bin/env bash
# check-md.sh — aevatar-review 的 BUILD/TEST 校验脚本
#
# 校验:
#   1. PLAN.md 列出的所有章节 Markdown 文件存在且非空。
#   2. 每篇章节含「关键代码」清单(指向 ~/Code/aevatar 的真实路径)。
#   3. 引用的源码文件真实存在于 AEVATAR_SRC(默认 ~/Code/aevatar)。
#
# 退出码: 0 = 全部通过; 1 = 有失败项。
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
AEVATAR_SRC="${AEVATAR_SRC:-$HOME/Code/aevatar}"
PLAN="$REPO_ROOT/PLAN.md"

fail=0
errors=()

if [ ! -f "$PLAN" ]; then
  echo "FATAL: PLAN.md not found at $PLAN" >&2
  exit 1
fi

if [ ! -d "$AEVATAR_SRC" ]; then
  echo "FATAL: aevatar source not found at $AEVATAR_SRC" >&2
  exit 1
fi

# Collect chapter files referenced in PLAN.md as `NN/NN-slug.md`.
mapfile -t CHAPTER_FILES < <(
  grep -oE '`[0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md`' "$PLAN" \
    | tr -d '`' | sort -u
)

echo "Found ${#CHAPTER_FILES[@]} chapter paths in PLAN.md"

for rel in "${CHAPTER_FILES[@]}"; do
  f="$REPO_ROOT/$rel"
  if [ ! -f "$f" ]; then
    errors+=("missing chapter file: $rel")
    fail=1
    continue
  fi
  if [ ! -s "$f" ]; then
    errors+=("empty chapter file: $rel")
    fail=1
    continue
  fi
  # 每篇应含「关键代码」清单(中英任一写法均可)
  if ! grep -qiE '关键代码|关键文件|事实源|Key (code|files)' "$f"; then
    errors+=("$rel: missing 关键代码/事实源 section")
    fail=1
  fi
  # 抽取引用的 aevatar 源码路径并校验存在(只校验 docs/ src/ workflows/ demos/ apps/ 前缀)
  while IFS= read -r p; do
    # 去掉常见包裹符
    p="${p#\`}"
    p="${p%\`}"
    # 规范化 ~/Code/aevatar/ 前缀
    case "$p" in
      *Code/aevatar/*) p="${p##*Code/aevatar/}";;
      ~/Code/aevatar/*) p="${p#~/Code/aevatar/}";;
    esac
    case "$p" in
      docs/*|src/*|workflows/*|demos/*|apps/*|tools/*)
        if [ ! -e "$AEVATAR_SRC/$p" ]; then
          errors+=("$rel: referenced source path does not exist: $p")
          fail=1
        fi
        ;;
    esac
  done < <(grep -oE '`[^`]*(docs|src|workflows|demos|apps)/[^`]+`' "$f")
done

if [ "$fail" -ne 0 ]; then
  echo "--- CHECK-MD FAILURES (${#errors[@]}) ---"
  printf '  - %s\n' "${errors[@]}" >&2
  exit 1
fi

echo "check-md: OK (${#CHAPTER_FILES[@]} chapters verified)"
exit 0
