#!/usr/bin/env bash
# check-drift.sh — final-state drift scan for aevatar-review.
#
#   bash scripts/check-drift.sh [--repo-root PATH]
#
# It answers one question: does the *active* book still advertise a structure,
# a chapter count, or a component that no longer exists?
#
# Scope: reader-facing chapters, site entry points, instructions and navigation.
# Explicitly excluded: docs/superpowers/specs/, docs/superpowers/plans/ and
# docs/migration/. Those are immutable migration evidence — they are supposed to
# record the old counts and the old paths, and rewriting them would destroy the
# audit trail.
#
# Failures:
#   1. a retired path still referenced from active navigation or reader surfaces
#   2. a stale chapter-count claim (43 / 83 / 85 substantive chapters)
#   3. an unresolved `issue:pending` row in the target manifest
#   4. an unchecked target row while the switch is presented as complete
#   5. a `设计待论证` warning that is not registered in 12/05
#   6. a current chapter presenting a retired component as a default
#
# exit 0 = no drift; 1 = at least one finding.

set -uo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$SCRIPT_ROOT}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo-root)
      [ "$#" -ge 2 ] || { echo "check-drift: --repo-root requires a value" >&2; exit 1; }
      REPO_ROOT="$2"; shift 2 ;;
    *) echo "check-drift: unknown argument: $1" >&2; exit 1 ;;
  esac
done

cd "$REPO_ROOT" || { echo "check-drift: cannot cd $REPO_ROOT" >&2; exit 1; }

MANIFEST="docs/migration/2026-07-25-target-chapters.md"
RETIRE_LIST="docs/migration/2026-07-25-old-retire-paths.txt"
GAPS="12/05-open-gaps-and-canon-drift.md"

findings="$(mktemp)"
active="$(mktemp)"
trap 'rm -f "$findings" "$active"' EXIT

add() { printf '%s\n' "$1" >>"$findings"; }

# The active surface: every reader-facing Markdown plus the site/instruction
# files, minus the immutable migration evidence.
{
  find . -path './.git' -prune -o -path './site' -prune -o \
       -path './.refactor-loop' -prune -o -path './.worktrees' -prune -o \
       -path './docs/superpowers' -prune -o -path './docs/migration' -prune -o \
       -type f -name '*.md' -print 2>/dev/null | sed 's|^\./||'
  for extra in mkdocs.yml .config/upstream-sync/chapter-source-map.json; do
    [ -f "$extra" ] && printf '%s\n' "$extra"
  done
} | sort -u > "$active"

# 1. retired paths still referenced from an active surface
if [ -f "$RETIRE_LIST" ]; then
  while IFS= read -r retired; do
    [ -z "$retired" ] && continue
    [ -e "$retired" ] && continue   # not deleted yet: Task 19 handles the switch
    while IFS= read -r surface; do
      [ -z "$surface" ] && continue
      [ -f "$surface" ] || continue
      if grep -qF -- "$retired" "$surface"; then
        add "retired path still referenced: $surface -> $retired"
      fi
    done < "$active"
  done < "$RETIRE_LIST"
fi

# A retired path that still exists but is wired into navigation is also drift:
# the switch is incomplete.
if [ -f mkdocs.yml ] && [ -f "$RETIRE_LIST" ]; then
  while IFS= read -r retired; do
    [ -z "$retired" ] && continue
    if grep -qF -- "$retired" mkdocs.yml; then
      add "retired path still in active navigation: mkdocs.yml -> $retired"
    fi
  done < "$RETIRE_LIST"
fi

# 2. stale chapter-count claims
while IFS= read -r surface; do
  [ -z "$surface" ] && continue
  [ -f "$surface" ] || continue
  if grep -nE '(共|计)?[^0-9](43|83|85)[[:space:]]*(篇|个)(章节|实质章节)?' "$surface" >/dev/null 2>&1; then
    while IFS= read -r hit; do
      add "stale chapter-count claim: $surface:$hit"
    done <<EOF
$(grep -nE '(共|计)?[^0-9](43|83|85)[[:space:]]*(篇|个)(章节|实质章节)?' "$surface" | head -3)
EOF
  fi
done < "$active"

# 3/4. manifest completeness
if [ -f "$MANIFEST" ]; then
  pending=$(grep -c 'issue:pending' "$MANIFEST" 2>/dev/null); pending=${pending:-0}
  [ "$pending" -gt 0 ] && add "target manifest still has $pending unresolved issue:pending row(s)"
  unchecked=$(grep -cE '^- \[ \] `[0-9]{2}/' "$MANIFEST" 2>/dev/null); unchecked=${unchecked:-0}
  [ "$unchecked" -gt 0 ] && add "target manifest still has $unchecked unchecked target row(s)"
else
  add "missing target manifest: $MANIFEST"
fi

# 5. unregistered design-justification warnings
while IFS= read -r surface; do
  [ -z "$surface" ] && continue
  [ -f "$surface" ] || continue
  case "$surface" in "$GAPS") continue ;; esac
  grep -q '设计待论证' "$surface" || continue
  if [ ! -f "$GAPS" ] || ! grep -qF -- "$surface" "$GAPS"; then
    add "unregistered 设计待论证 warning: $surface is not recorded in $GAPS"
  fi
done < "$active"

# 6. retired components presented as current defaults
RETIRED_COMPONENTS='A2A|MassTransit|StateMirror|SkillRunnerGAgent'
while IFS= read -r surface; do
  [ -z "$surface" ] && continue
  [ -f "$surface" ] || continue
  case "$surface" in
    12/*|*/index.md|mkdocs.yml|*.json) continue ;;
  esac
  grep -qE "$RETIRED_COMPONENTS" "$surface" || continue
  status="$(awk 'NR==1 && $0 != "---" { exit } NR>1 && /^---/ { exit } /^status:/ { sub(/^status:[[:space:]]*/, ""); print; exit }' "$surface")"
  case "$status" in
    historical|target) continue ;;
  esac
  # A current chapter may still name a retired component, but only in a
  # paragraph that marks it retired.
  while IFS= read -r hit; do
    line_no="${hit%%:*}"
    text="${hit#*:}"
    case "$text" in
      *历史*|*已移除*|*已退役*|*已删除*|*superseded*|*retired*|*removed*) continue ;;
    esac
    add "retired component presented without a retired marker: $surface:$line_no"
  done <<EOF
$(grep -nE "$RETIRED_COMPONENTS" "$surface" | head -5)
EOF
done < "$active"

if [ -s "$findings" ]; then
  count=$(grep -c . "$findings")
  echo "check-drift: FAIL ($count finding(s))"
  sed 's/^/  - /' "$findings" >&2
  exit 1
fi

echo "check-drift: OK"
exit 0
