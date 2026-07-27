#!/usr/bin/env bash
# Materialize a read-only snapshot of one upstream commit inside this review
# repository's Git directory.
#
#   bash scripts/materialize-frozen-upstream.sh --repo PATH --sha FULL_SHA [--output PATH]
#
# stdout: exactly one absolute snapshot directory path
# stderr: diagnostics
# exit 0: the requested commit exists and the snapshot marker/tree match FULL_SHA
# exit 1: malformed SHA, missing commit, archive/extract failure, or marker mismatch
#
# The snapshot exists so that path-existence and line-anchor validation always
# read the frozen fact baseline instead of a drifting upstream working tree.
# This script never runs checkout/reset/stash/clean and never writes anything
# under the upstream repository. The cache is derived state: it is rebuildable,
# ignored by Git, and is never a fact source or host configuration.

set -uo pipefail

die() {
  printf 'materialize-frozen-upstream: %s\n' "$1" >&2
  exit 1
}

UPSTREAM_REPO=""
SHA=""
OUTPUT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      [ "$#" -ge 2 ] || die "--repo requires a value"
      UPSTREAM_REPO="$2"
      shift 2
      ;;
    --sha)
      [ "$#" -ge 2 ] || die "--sha requires a value"
      SHA="$2"
      shift 2
      ;;
    --output)
      [ "$#" -ge 2 ] || die "--output requires a value"
      OUTPUT="$2"
      shift 2
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[ -n "$UPSTREAM_REPO" ] || die "--repo is required"
[ -n "$SHA" ] || die "--sha is required"

case "$SHA" in
  *[!0-9a-f]* | "") die "malformed SHA (expected 40 lowercase hex chars): $SHA" ;;
esac
[ "${#SHA}" -eq 40 ] || die "malformed SHA (expected 40 lowercase hex chars): $SHA"

# Expand a leading ~ so callers may pass the documented ~/Code/aevatar form.
case "$UPSTREAM_REPO" in
  "~"/*) UPSTREAM_REPO="$HOME/${UPSTREAM_REPO#~/}" ;;
  "~") UPSTREAM_REPO="$HOME" ;;
esac

[ -d "$UPSTREAM_REPO" ] || die "upstream repository not found: $UPSTREAM_REPO"

git -C "$UPSTREAM_REPO" rev-parse --git-dir >/dev/null 2>&1 ||
  die "not a Git repository: $UPSTREAM_REPO"

git -C "$UPSTREAM_REPO" cat-file -e "$SHA^{commit}" 2>/dev/null ||
  die "commit object not present in $UPSTREAM_REPO: $SHA"

if [ -z "$OUTPUT" ]; then
  REVIEW_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" ||
    die "cannot resolve the review repository root"
  GIT_PATH="$(git -C "$REVIEW_ROOT" rev-parse --git-path aevatar-frozen 2>/dev/null)" ||
    die "cannot resolve the review repository Git directory"
  case "$GIT_PATH" in
    /*) ;;
    *) GIT_PATH="$REVIEW_ROOT/$GIT_PATH" ;;
  esac
  OUTPUT="$GIT_PATH/$SHA"
fi

case "$OUTPUT" in
  /*) ;;
  *) OUTPUT="$(pwd)/$OUTPUT" ;;
esac

marker_matches() {
  # A cache entry is trustworthy only when its marker names the requested commit
  # and the extracted tree still looks like a real checkout.
  [ -d "$1" ] || return 1
  [ -f "$1/.source-commit" ] || return 1
  [ "$(sed -n '1p' "$1/.source-commit" 2>/dev/null)" = "$SHA" ] || return 1
  [ -e "$1/aevatar.slnx" ] || return 1
  return 0
}

if marker_matches "$OUTPUT"; then
  printf '%s\n' "$OUTPUT"
  exit 0
fi

PARENT="$(dirname "$OUTPUT")"
mkdir -p "$PARENT" || die "cannot create snapshot parent directory: $PARENT"

STAGING="$(mktemp -d "$PARENT/.tmp-$SHA.XXXXXX")" ||
  die "cannot create staging directory under $PARENT"

cleanup() {
  [ -n "${STAGING:-}" ] && [ -d "$STAGING" ] && rm -rf "$STAGING"
}
trap cleanup EXIT

git -C "$UPSTREAM_REPO" archive --format=tar "$SHA" 2>/dev/null | tar -x -C "$STAGING" 2>/dev/null ||
  die "failed to archive/extract $SHA from $UPSTREAM_REPO"

[ -e "$STAGING/aevatar.slnx" ] ||
  die "extracted tree for $SHA has no aevatar.slnx; refusing to publish an unrecognized snapshot"

printf '%s\n' "$SHA" > "$STAGING/.source-commit" ||
  die "cannot write the .source-commit marker"

if [ -e "$OUTPUT" ]; then
  # A stale or partial cache entry is replaced, never silently reused.
  rm -rf "$OUTPUT" || die "cannot replace the stale snapshot at $OUTPUT"
fi

if mv "$STAGING" "$OUTPUT" 2>/dev/null; then
  STAGING=""
else
  # Lost an atomic rename race: accept the winner only if it validates.
  if marker_matches "$OUTPUT"; then
    printf '%s\n' "$OUTPUT" >&2
    printf 'materialize-frozen-upstream: reused a concurrently created snapshot\n' >&2
    printf '%s\n' "$OUTPUT"
    exit 0
  fi
  die "cannot publish the snapshot at $OUTPUT"
fi

marker_matches "$OUTPUT" || die "published snapshot failed marker validation: $OUTPUT"

printf '%s\n' "$OUTPUT"
exit 0
