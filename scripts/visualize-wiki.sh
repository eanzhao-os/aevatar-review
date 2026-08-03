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
  [[ -z "$WIKI_ROOT" ]] || rm -rf "$WIKI_ROOT"
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
