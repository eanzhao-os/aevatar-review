#!/usr/bin/env bash
# check-md.sh — chapter contract gate for aevatar-review.
#
#   bash scripts/check-md.sh [--changed]                 incremental (default)
#   bash scripts/check-md.sh --paths PATH...             validate exactly these files
#   bash scripts/check-md.sh --all [--allow-retiring]    validate the whole book
#
# Options:
#   --repo-root PATH   review repository root (default: this script's parent)
#   --allow-retiring   migration mode: paths listed in the retire list and the
#                      block indexes are not yet held to the final contract.
#                      Forbidden in CI and in final verification.
#
# Environment:
#   AEVATAR_SRC                 frozen upstream snapshot root (see
#                               scripts/materialize-frozen-upstream.sh)
#   AEVATAR_SRC2                secondary sync baseline (default: live
#                               upstream working tree $HOME/Code/aevatar);
#                               a referenced path passes if it exists in
#                               either baseline, anchors pass if in range in
#                               at least one baseline; set AEVATAR_SRC2=""
#                               to disable the secondary baseline
#   EXPECTED_UPSTREAM_COMMIT    approved fact baseline (default below)
#   EXPECTED_VERIFIED_AT        approved verification date (default below)
#
# A file is classified before it is validated:
#   target    listed in the target manifest -> full chapter contract
#   index     NN/index.md                   -> index contract
#   retiring  listed in the retire list     -> legacy contract (being deleted)
#   orphan    none of the above             -> rejected by --all
#
# exit 0 = every selected file satisfies its contract; 1 = at least one failure.
# Bash 3.2 compatible: no mapfile, no associative arrays.

set -uo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$SCRIPT_ROOT}"
AEVATAR_SRC="${AEVATAR_SRC:-$HOME/Code/aevatar}"
if [ -z "${AEVATAR_SRC2+x}" ]; then AEVATAR_SRC2="$HOME/Code/aevatar"; fi
EXPECTED_UPSTREAM_COMMIT="${EXPECTED_UPSTREAM_COMMIT:-f02aa690bbebb9cabeac30a553d737486b0eb661}"
EXPECTED_VERIFIED_AT="${EXPECTED_VERIFIED_AT:-2026-07-25}"

MODE=changed
ALLOW_RETIRING=0
SELECTED=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --changed) MODE=changed; shift ;;
    --all) MODE=all; shift ;;
    --allow-retiring) ALLOW_RETIRING=1; shift ;;
    --repo-root)
      [ "$#" -ge 2 ] || { echo "check-md: --repo-root requires a value" >&2; exit 1; }
      REPO_ROOT="$2"; shift 2 ;;
    --paths)
      MODE=paths; shift
      while [ "$#" -gt 0 ]; do
        case "$1" in
          --*) break ;;
          *) SELECTED="$SELECTED$1
"; shift ;;
        esac
      done
      ;;
    *) echo "check-md: unknown argument: $1" >&2; exit 1 ;;
  esac
done

cd "$REPO_ROOT" || { echo "check-md: cannot cd $REPO_ROOT" >&2; exit 1; }
[ -d "$AEVATAR_SRC" ] || { echo "check-md: frozen upstream not found at $AEVATAR_SRC" >&2; exit 1; }

MANIFEST="docs/migration/2026-07-25-target-chapters.md"
RETIRE_LIST="docs/migration/2026-07-25-old-retire-paths.txt"

errors_file="$(mktemp)"
targets_file="$(mktemp)"
retire_file="$(mktemp)"
work_file="$(mktemp)"
trap 'rm -f "$errors_file" "$targets_file" "$retire_file" "$work_file"' EXIT

add_error() { printf '%s\n' "$1" >>"$errors_file"; }

if [ -f "$MANIFEST" ]; then
  grep -E '^- \[[ x]\] `[0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md` — status:' "$MANIFEST" \
    | sed -E 's/^- \[[ x]\] `([^`]+)` — status:([a-z]+) —.*/\1 \2/' > "$targets_file" || true
fi
[ -f "$RETIRE_LIST" ] && cp "$RETIRE_LIST" "$retire_file" || : > "$retire_file"

is_target() { grep -qx -- "$1 [a-z]*" "$targets_file" 2>/dev/null || grep -qE "^$(printf '%s' "$1" | sed 's/[.[\*^$]/\\&/g') " "$targets_file"; }
target_status() { grep -E "^$(printf '%s' "$1" | sed 's/[.[\*^$]/\\&/g') " "$targets_file" | awk 'NR==1{print $2}'; }
is_retiring() { grep -qxF -- "$1" "$retire_file"; }
is_block_index() { printf '%s' "$1" | grep -qE '^[0-9]{2}/index\.md$'; }

# ---------------------------------------------------------------- validators

frontmatter_value() {
  # frontmatter_value <file> <key>
  awk -v key="$2" '
    NR == 1 { if ($0 != "---") exit; next }
    /^---[[:space:]]*$/ { exit }
    { split($0, kv, ":"); k = kv[1];
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", k);
      if (k == key) { sub(/^[^:]*:[[:space:]]*/, ""); gsub(/[[:space:]]+$/, ""); print; exit } }
  ' "$1"
}

has_frontmatter() {
  [ "$(sed -n '1p' "$1")" = "---" ] || return 1
  sed -n '2,40p' "$1" | grep -qE '^---[[:space:]]*$' || return 1
  return 0
}

count_matches() {
  # grep -c prints 0 and exits 1 when nothing matches; never append a fallback.
  local n
  n=$(grep -c "$1" "$2" 2>/dev/null)
  printf '%s' "${n:-0}"
}

count_diagrams() {
  local mermaid images
  mermaid=$(count_matches '^```mermaid' "$1")
  images=$(count_matches '^!\[' "$1")
  printf '%s' "$(( mermaid + images ))"
}

# Emit every backticked upstream path reference in a file, one per line.
upstream_refs() {
  grep -oE '`[^`]+`' "$1" 2>/dev/null \
    | sed 's/^`//; s/`$//' \
    | sed 's|^~/Code/aevatar/||; s|.*Code/aevatar/||' \
    | grep -E '^(docs|src|workflows|demos|apps|tools|agents|test)/[^ ]+|^aevatar\.slnx|^[A-Za-z0-9_.-]+\.slnf' || true
}

check_upstream_refs() {
  local rel="$1" f="$2" ref path anchors candidate one total
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    path="$ref"
    anchors=""
    # Anchors come in two shapes: "path#L123" and "path:123" — the latter may
    # list several lines ("path:135,142,149") or a range ("path:12-20").
    case "$path" in
      *'#L'[0-9]*)
        candidate="${path##*#L}"
        if printf '%s' "$candidate" | grep -qE '^[0-9]+([,-][0-9]+)*$'; then
          anchors="$candidate"; path="${path%#L*}"
        fi
        ;;
    esac
    case "$path" in
      *:[0-9]*)
        candidate="${path##*:}"
        if printf '%s' "$candidate" | grep -qE '^[0-9]+([,-][0-9]+)*$'; then
          anchors="$candidate"; path="${path%:*}"
        fi
        ;;
    esac
    # Dual-baseline resolution: a path (and its line anchors) passes if it
    # exists in the primary frozen baseline ($AEVATAR_SRC) OR in the secondary
    # sync baseline ($AEVATAR_SRC2, default: the live upstream working tree).
    # Anchors are checked against every baseline where the file exists; the
    # reference is accepted if at least one baseline contains the full range.
    existing=""
    if [ -e "$AEVATAR_SRC/$path" ]; then existing="$AEVATAR_SRC"; fi
    if [ -n "$AEVATAR_SRC2" ] && [ -e "$AEVATAR_SRC2/$path" ]; then
      existing="${existing:+$existing
}$AEVATAR_SRC2"
    fi
    if [ -z "$existing" ]; then
      add_error "$rel: referenced source path does not exist at the frozen baseline or sync baseline: $path"
      return 1
    fi
    if [ -n "$anchors" ]; then
      ok=0
      sizes=""
      while IFS= read -r base; do
        [ -f "$base/$path" ] || continue
        total=$(wc -l < "$base/$path" | tr -d ' ')
        sizes="${sizes:+$sizes }$total"
        [ "$total" -lt 1 ] && continue
        in_range=1
        for one in $(printf '%s' "$anchors" | tr ',-' '  '); do
          if [ "$one" -lt 1 ] || [ "$one" -gt "$total" ]; then in_range=0; break; fi
        done
        [ "$in_range" -eq 1 ] && ok=1
      done <<EOF
$existing
EOF
      if [ "$ok" -eq 0 ]; then
        add_error "$rel: source line anchor out of range in every baseline: $path:$anchors (baseline line counts: ${sizes:-unknown})"
        return 1
      fi
    fi
  done <<EOF
$(upstream_refs "$f")
EOF
  return 0
}

validate_target() {
  local rel="$1" f="$REPO_ROOT/$1" bad=0 status expected value h1 spine
  if [ ! -s "$f" ]; then add_error "$rel: missing or empty chapter file"; return 1; fi

  if ! has_frontmatter "$f"; then
    add_error "$rel: missing or malformed frontmatter block"
    return 1
  fi

  status="$(frontmatter_value "$f" status)"
  case "$status" in
    current|mixed|historical|target) ;;
    *) add_error "$rel: invalid frontmatter status: '${status:-<empty>}'"; bad=1 ;;
  esac
  expected="$(target_status "$rel")"
  if [ -n "$expected" ] && [ -n "$status" ] && [ "$status" != "$expected" ]; then
    add_error "$rel: frontmatter status '$status' disagrees with the manifest status '$expected'"
    bad=1
  fi

  value="$(frontmatter_value "$f" upstream_commit)"
  if [ "$value" != "$EXPECTED_UPSTREAM_COMMIT" ]; then
    add_error "$rel: frontmatter upstream_commit must be $EXPECTED_UPSTREAM_COMMIT, found '${value:-<empty>}'"
    bad=1
  fi
  value="$(frontmatter_value "$f" verified_at)"
  if [ "$value" != "$EXPECTED_VERIFIED_AT" ]; then
    add_error "$rel: frontmatter verified_at must be $EXPECTED_VERIFIED_AT, found '${value:-<empty>}'"
    bad=1
  fi

  h1=$(count_matches '^# ' "$f")
  if [ "$h1" -ne 1 ]; then
    add_error "$rel: expected exactly one H1 heading, found $h1"
    bad=1
  fi

  for section in '版本与结论' '设计抽象与事实源' '为什么' '边界与演进' '读完应能回答'; do
    if ! grep -q -- "$section" "$f"; then
      add_error "$rel: missing required section: $section"
      bad=1
    fi
  done

  if ! grep -qE 'verified-static|verified-local|verified-production-versioned' "$f"; then
    add_error "$rel: missing an honest demo status marker"
    bad=1
  fi

  value=$(count_diagrams "$f")
  if [ "$value" -lt 2 ]; then
    add_error "$rel: expected at least 2 diagrams with different jobs, found $value"
    bad=1
  fi

  # The spine list is the block between the source heading and the next heading.
  spine=$(awk '
    /^## .*设计抽象与事实源/ { inside = 1; next }
    inside && /^## / { exit }
    inside && /^[-*] / && /`/ { n++ }
    END { print n + 0 }
  ' "$f")
  if [ "$spine" -lt 1 ] || [ "$spine" -gt 3 ]; then
    add_error "$rel: expected 1-3 source spine entries, found $spine"
    bad=1
  fi

  check_upstream_refs "$rel" "$f" || bad=1
  return "$bad"
}

validate_index() {
  local rel="$1" f="$REPO_ROOT/$1" bad=0 status h1
  if [ ! -s "$f" ]; then add_error "$rel: missing or empty index file"; return 1; fi
  if ! has_frontmatter "$f"; then
    add_error "$rel: missing or malformed frontmatter block"
    return 1
  fi
  status="$(frontmatter_value "$f" status)"
  if [ "$status" != "index" ]; then
    add_error "$rel: block index must declare frontmatter status: index, found '${status:-<empty>}'"
    bad=1
  fi
  h1=$(count_matches '^# ' "$f")
  if [ "$h1" -ne 1 ]; then
    add_error "$rel: expected exactly one H1 heading, found $h1"
    bad=1
  fi
  check_upstream_refs "$rel" "$f" || bad=1
  return "$bad"
}

validate_legacy() {
  # Retiring chapters keep the historical contract: they are evidence being
  # migrated, not content the final book ships.
  local rel="$1" f="$REPO_ROOT/$1" bad=0
  if [ ! -s "$f" ]; then add_error "$rel: missing or empty chapter file"; return 1; fi
  if ! grep -qiE '事实源|设计抽象|关键代码|关键文件|Key (code|files)|Evidence' "$f"; then
    add_error "$rel: missing 事实源/设计抽象 section"
    bad=1
  fi
  check_upstream_refs "$rel" "$f" || bad=1
  return "$bad"
}

validate_one() {
  local rel="$1"
  if is_block_index "$rel"; then
    if [ "$ALLOW_RETIRING" -eq 1 ]; then
      printf 'retiring-index %s\n' "$rel" >/dev/null
      return 0
    fi
    validate_index "$rel"
    return $?
  fi
  if grep -qE "^$(printf '%s' "$rel" | sed 's/[.[\*^$]/\\&/g') " "$targets_file"; then
    validate_target "$rel"
    return $?
  fi
  if is_retiring "$rel"; then
    # Retiring chapters are grandfathered: they are migration evidence on the
    # way out, not content the final book ships.
    [ "$ALLOW_RETIRING" -eq 1 ] && return 0
    validate_legacy "$rel"
    return $?
  fi
  # Anything else is new content and must meet the full contract.
  validate_target "$rel"
  return $?
}

# ------------------------------------------------------------------- selection

all_substantive() {
  find . -path './.git' -prune -o -path './.refactor-loop' -prune -o -path './.worktrees' -prune -o \
    -path './site' -prune -o -path './docs' -prune -o \
    -type f -name '*.md' -print 2>/dev/null \
    | sed 's|^\./||' \
    | grep -E '^[0-9]{2}/([0-9]{2}-[a-z0-9-]+/)?[0-9]{2}-[a-z0-9-]+\.md$' \
    | sort || true
}

case "$MODE" in
  paths)
    printf '%s' "$SELECTED" | grep -v '^$' > "$work_file" || true
    scope="explicit paths"
    ;;
  changed)
    git diff --name-only --diff-filter=AM HEAD -- '??/*.md' '??/*/*.md' 2>/dev/null \
      | grep -E '^[0-9]{2}/([0-9]{2}-[a-z0-9-]+/)?([0-9]{2}-[a-z0-9-]+|index)\.md$' > "$work_file" || true
    if [ ! -s "$work_file" ]; then
      all_substantive > "$work_file"
      scope="all existing chapters (no diff)"
    else
      scope="git diff"
    fi
    ;;
  all)
    if [ ! -s "$targets_file" ]; then
      echo "check-md: --all requires $MANIFEST" >&2
      exit 1
    fi
    awk '{print $1}' "$targets_file" > "$work_file"
    for block in 00 01 02 03 04 05 06 07 08 09 10 11 12 13; do
      printf '%s/index.md\n' "$block" >> "$work_file"
    done
    scope="full book"
    ;;
esac

count=$(count_matches . "$work_file")
echo "check-md: mode=$MODE scope=$scope files=$count allow-retiring=$ALLOW_RETIRING"

fail=0
while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  if [ ! -e "$REPO_ROOT/$rel" ]; then
    add_error "missing file: $rel"
    fail=1
    continue
  fi
  validate_one "$rel" || fail=1
done <"$work_file"

# --all additionally rejects substantive chapters nobody planned.
if [ "$MODE" = all ]; then
  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    grep -qE "^$(printf '%s' "$rel" | sed 's/[.[\*^$]/\\&/g') " "$targets_file" && continue
    if is_retiring "$rel"; then
      if [ "$ALLOW_RETIRING" -eq 1 ]; then
        continue
      fi
      add_error "orphan chapter still present (listed for retirement): $rel"
      fail=1
      continue
    fi
    add_error "orphan chapter not in the target manifest: $rel"
    fail=1
  done <<EOF
$(all_substantive)
EOF
fi

if [ "$fail" -ne 0 ]; then
  ec=$(count_matches . "$errors_file")
  echo "--- CHECK-MD FAILURES ($ec) ---"
  sed 's/^/  - /' "$errors_file" >&2
  exit 1
fi

echo "check-md: OK ($count files verified)"
exit 0
