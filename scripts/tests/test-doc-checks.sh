#!/usr/bin/env bash
# Fixture regression tests for the aevatar-review documentation tooling.
#
# Usage: bash scripts/tests/test-doc-checks.sh <suite>
#   frozen-upstream  materialize-frozen-upstream.sh snapshot isolation
#   issue-snapshot   snapshot-upstream-issues.py pagination/dedupe/escaping/count
#   issue-replay     snapshot-upstream-issues.py historical state replay + boundaries
#   issue-cli        create_issues.py manifest parsing and issue idempotency
#   all              every suite above
#
# Every suite builds its own throwaway fixtures under a temporary directory and
# never touches the read-only upstream repository or the live GitHub API.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAILURES=0

fail() {
  printf 'ASSERT FAIL: %s\n' "$1" >&2
  FAILURES=$((FAILURES + 1))
}

assert_eq() {
  # assert_eq <expected> <actual> <label>
  if [ "$1" != "$2" ]; then
    fail "$3: expected [$1] got [$2]"
  fi
}

assert_contains() {
  # assert_contains <haystack-file> <needle> <label>
  if ! grep -Fq -- "$2" "$1"; then
    fail "$3: missing [$2]"
  fi
}

assert_not_contains() {
  if grep -Fq -- "$2" "$1"; then
    fail "$3: unexpected [$2]"
  fi
}

# --------------------------------------------------------------------------
# frozen-upstream
# --------------------------------------------------------------------------

test_frozen_upstream() {
  local tmp upstream out first second
  tmp="$(mktemp -d)"
  upstream="$tmp/upstream"
  mkdir -p "$upstream"
  (
    cd "$upstream" || exit 1
    git init -q .
    git config user.email fixture@example.invalid
    git config user.name fixture
    printf 'first\n' > tracked.txt
    printf '<Solution />\n' > aevatar.slnx
    git add -- tracked.txt aevatar.slnx
    git commit -qm first
    printf 'second\n' > later.txt
    git add -- later.txt
    git commit -qm second
    printf 'dirty\n' >> tracked.txt
    printf 'untracked\n' > untracked.txt
  ) || { fail "frozen-upstream: fixture repo setup failed"; rm -rf "$tmp"; return; }

  first="$(git -C "$upstream" rev-parse HEAD~1)"
  second="$(git -C "$upstream" rev-parse HEAD)"

  out="$(bash "$ROOT/scripts/materialize-frozen-upstream.sh" --repo "$upstream" --sha "$first" --output "$tmp/snap" 2>"$tmp/err")"
  assert_eq "0" "$?" "frozen-upstream: exit code for a valid commit"
  assert_eq "$tmp/snap" "$out" "frozen-upstream: stdout must be exactly the snapshot path"

  if [ ! -f "$out/tracked.txt" ]; then
    fail "frozen-upstream: requested commit content missing"
  fi
  if [ -f "$out/later.txt" ]; then
    fail "frozen-upstream: snapshot leaked content from a later commit"
  fi
  if [ -f "$out/untracked.txt" ]; then
    fail "frozen-upstream: snapshot leaked untracked working-tree content"
  fi
  assert_eq "first" "$(cat "$out/tracked.txt" 2>/dev/null)" "frozen-upstream: snapshot leaked dirty working-tree content"
  assert_eq "$first" "$(sed -n '1p' "$out/.source-commit" 2>/dev/null)" "frozen-upstream: .source-commit marker"

  # Reuse must be idempotent and must not rewrite the marker.
  local out2
  out2="$(bash "$ROOT/scripts/materialize-frozen-upstream.sh" --repo "$upstream" --sha "$first" --output "$tmp/snap" 2>>"$tmp/err")"
  assert_eq "$out" "$out2" "frozen-upstream: reuse returns the same path"
  assert_eq "first" "$(cat "$out2/tracked.txt" 2>/dev/null)" "frozen-upstream: reuse kept frozen content"

  # A stale marker must be repaired rather than silently reused.
  printf '%s\n' "$second" > "$out/.source-commit"
  bash "$ROOT/scripts/materialize-frozen-upstream.sh" --repo "$upstream" --sha "$first" --output "$tmp/snap" >/dev/null 2>>"$tmp/err"
  assert_eq "$first" "$(sed -n '1p' "$out/.source-commit" 2>/dev/null)" "frozen-upstream: stale marker must be repaired"

  # Missing commit and malformed SHA must fail loudly.
  bash "$ROOT/scripts/materialize-frozen-upstream.sh" --repo "$upstream" --sha 0000000000000000000000000000000000000000 --output "$tmp/miss" >/dev/null 2>>"$tmp/err"
  assert_eq "1" "$?" "frozen-upstream: missing commit must exit 1"
  bash "$ROOT/scripts/materialize-frozen-upstream.sh" --repo "$upstream" --sha not-a-sha --output "$tmp/bad" >/dev/null 2>>"$tmp/err"
  assert_eq "1" "$?" "frozen-upstream: malformed SHA must exit 1"

  # The upstream repository must be untouched.
  assert_eq "$second" "$(git -C "$upstream" rev-parse HEAD)" "frozen-upstream: upstream HEAD moved"
  assert_eq " M tracked.txt
?? untracked.txt" "$(git -C "$upstream" status --porcelain=v1)" "frozen-upstream: upstream working tree mutated"

  rm -rf "$tmp"
}

# --------------------------------------------------------------------------
# shared fake gh helper
# --------------------------------------------------------------------------

write_fake_gh() {
  # write_fake_gh <bindir> <fixturedir>
  # The fake resolves an endpoint to <fixturedir>/<slug>.json where slug is the
  # endpoint with non-alphanumerics collapsed to '-'.
  local bindir="$1" fixtures="$2"
  mkdir -p "$bindir"
  cat > "$bindir/gh" <<FAKE
#!/usr/bin/env bash
set -uo pipefail
FIXTURES="$fixtures"
endpoint=""
for arg in "\$@"; do
  case "\$arg" in
    api|--paginate|--method|GET) continue ;;
    -*) continue ;;
    *) if [ -z "\$endpoint" ]; then endpoint="\$arg"; fi ;;
  esac
done
slug="\$(printf '%s' "\$endpoint" | tr -c 'A-Za-z0-9' '-' )"
if [ -f "\$FIXTURES/\$slug.json" ]; then
  cat "\$FIXTURES/\$slug.json"
  exit 0
fi
printf 'fake gh: no fixture for endpoint [%s] slug [%s]\n' "\$endpoint" "\$slug" >&2
exit 1
FAKE
  chmod +x "$bindir/gh"
}

fixture_slug() {
  printf '%s' "$1" | tr -c 'A-Za-z0-9' '-'
}

# --------------------------------------------------------------------------
# issue-snapshot
# --------------------------------------------------------------------------

test_issue_snapshot() {
  local tmp bin fixtures out endpoint slug
  tmp="$(mktemp -d)"
  bin="$tmp/bin"
  fixtures="$tmp/fixtures"
  mkdir -p "$fixtures"
  write_fake_gh "$bin" "$fixtures"

  endpoint='search/issues?q=repo%3Afix%2Frepo+is%3Aissue+is%3Aclosed+closed%3A2026-07-06..2026-07-25&per_page=100'
  slug="$(fixture_slug "$endpoint")"
  # Two concatenated pages; #11 is duplicated across pages; #10 has a pipe in its title.
  cat > "$fixtures/$slug.json" <<'JSON'
{"total_count":3,"items":[
 {"number":12,"title":"later issue","state":"closed","created_at":"2026-07-07T00:00:00Z","closed_at":"2026-07-08T00:00:00Z","html_url":"https://example.invalid/12","labels":[{"name":"bug"}]},
 {"number":10,"title":"pipe | inside | title","state":"closed","created_at":"2026-07-06T00:00:00Z","closed_at":"2026-07-06T01:00:00Z","html_url":"https://example.invalid/10","labels":[]}
]}
{"total_count":3,"items":[
 {"number":11,"title":"dup issue","state":"closed","created_at":"2026-07-07T00:00:00Z","closed_at":"2026-07-09T00:00:00Z","html_url":"https://example.invalid/11","labels":[{"name":"a"},{"name":"b"}]},
 {"number":11,"title":"dup issue","state":"closed","created_at":"2026-07-07T00:00:00Z","closed_at":"2026-07-09T00:00:00Z","html_url":"https://example.invalid/11","labels":[{"name":"a"},{"name":"b"}]}
]}
JSON

  out="$tmp/out.md"
  PATH="$bin:$PATH" python3 "$ROOT/scripts/snapshot-upstream-issues.py" \
    --repo fix/repo --state closed --from 2026-07-06 --through 2026-07-25 \
    --expect-count 3 --format markdown > "$out" 2>"$tmp/err"
  assert_eq "0" "$?" "issue-snapshot: exact expected count must exit 0"

  assert_eq "3" "$(grep -c '^| closed | #' "$out" 2>/dev/null | tr -d ' ')" "issue-snapshot: duplicate issue must collapse to one row"
  assert_eq "10
11
12" "$(sed -n 's/^| closed | #\([0-9]*\) |.*/\1/p' "$out")" "issue-snapshot: rows must sort numerically"
  assert_contains "$out" 'pipe \| inside \| title' "issue-snapshot: pipe in title must be escaped"
  assert_contains "$out" '| unclassified |' "issue-snapshot: classification column defaults to unclassified"
  assert_contains "$out" 'a; b' "issue-snapshot: labels must be rendered without raw pipes"

  # Count drift must fail loudly rather than emit a short cohort.
  PATH="$bin:$PATH" python3 "$ROOT/scripts/snapshot-upstream-issues.py" \
    --repo fix/repo --state closed --from 2026-07-06 --through 2026-07-25 \
    --expect-count 4 --format markdown > "$tmp/out2.md" 2>"$tmp/err2"
  assert_eq "1" "$?" "issue-snapshot: count mismatch must exit 1"
  assert_contains "$tmp/err2" "expected 4" "issue-snapshot: count mismatch must name the expectation"

  # Malformed arguments must fail before any network call.
  PATH="$bin:$PATH" python3 "$ROOT/scripts/snapshot-upstream-issues.py" \
    --repo fix/repo --state closed --expect-count 3 --format markdown > /dev/null 2>&1
  assert_eq "1" "$?" "issue-snapshot: closed state without a window must exit 1"

  rm -rf "$tmp"
}

# --------------------------------------------------------------------------
# issue-replay
# --------------------------------------------------------------------------

test_issue_replay() {
  local tmp bin fixtures out slug
  tmp="$(mktemp -d)"
  bin="$tmp/bin"
  fixtures="$tmp/fixtures"
  mkdir -p "$fixtures"
  write_fake_gh "$bin" "$fixtures"

  # Cutoff for the fixture cohort.
  local cutoff='2026-07-24T15:23:48Z'

  slug="$(fixture_slug '/repos/fix/repo/issues?state=all&per_page=100')"
  cat > "$fixtures/$slug.json" <<'JSON'
[
 {"number":1,"title":"closed inside window before cutoff","state":"closed","created_at":"2026-07-01T00:00:00Z","closed_at":"2026-07-10T00:00:00Z","updated_at":"2026-07-10T00:00:00Z","html_url":"https://example.invalid/1","labels":[]},
 {"number":2,"title":"closed exactly on window lower bound","state":"closed","created_at":"2026-07-01T00:00:00Z","closed_at":"2026-07-06T00:00:00Z","updated_at":"2026-07-06T00:00:00Z","html_url":"https://example.invalid/2","labels":[]},
 {"number":3,"title":"closed before window","state":"closed","created_at":"2026-06-01T00:00:00Z","closed_at":"2026-07-05T23:59:59Z","updated_at":"2026-07-05T23:59:59Z","html_url":"https://example.invalid/3","labels":[]},
 {"number":4,"title":"closed after cutoff so open at cutoff","state":"closed","created_at":"2026-07-02T00:00:00Z","closed_at":"2026-07-25T15:17:16Z","updated_at":"2026-07-25T15:17:16Z","html_url":"https://example.invalid/4","labels":[]},
 {"number":5,"title":"closed then reopened before cutoff","state":"closed","created_at":"2026-07-02T00:00:00Z","closed_at":"2026-07-26T00:00:00Z","updated_at":"2026-07-26T00:00:00Z","html_url":"https://example.invalid/5","labels":[]},
 {"number":6,"title":"still open and quiet","state":"open","created_at":"2026-07-03T00:00:00Z","closed_at":null,"updated_at":"2026-07-03T00:00:00Z","html_url":"https://example.invalid/6","labels":[]},
 {"number":7,"title":"created after cutoff","state":"open","created_at":"2026-07-25T18:36:42Z","closed_at":null,"updated_at":"2026-07-25T18:36:42Z","html_url":"https://example.invalid/7","labels":[]},
 {"number":8,"title":"pull request must be excluded","state":"closed","created_at":"2026-07-02T00:00:00Z","closed_at":"2026-07-10T00:00:00Z","updated_at":"2026-07-10T00:00:00Z","html_url":"https://example.invalid/8","labels":[],"pull_request":{"url":"https://example.invalid/pull/8"}},
 {"number":9,"title":"closed exactly at cutoff instant","state":"closed","created_at":"2026-07-02T00:00:00Z","closed_at":"2026-07-24T15:23:48Z","updated_at":"2026-07-24T15:23:48Z","html_url":"https://example.invalid/9","labels":[]}
]
JSON

  # Only issues touched at/after the cutoff need timeline replay.
  cat > "$fixtures/$(fixture_slug '/repos/fix/repo/issues/4/events?per_page=100').json" <<'JSON'
[{"event":"closed","created_at":"2026-07-25T15:17:16Z"}]
JSON
  cat > "$fixtures/$(fixture_slug '/repos/fix/repo/issues/5/events?per_page=100').json" <<'JSON'
[{"event":"closed","created_at":"2026-07-08T00:00:00Z"},
 {"event":"reopened","created_at":"2026-07-09T00:00:00Z"},
 {"event":"closed","created_at":"2026-07-26T00:00:00Z"}]
JSON

  out="$tmp/open.md"
  PATH="$bin:$PATH" python3 "$ROOT/scripts/snapshot-upstream-issues.py" \
    --repo fix/repo --state open --reconstruct-at "$cutoff" \
    --expect-count 3 --format markdown > "$out" 2>"$tmp/err"
  assert_eq "0" "$?" "issue-replay: open cohort count"
  assert_eq "4
5
6" "$(sed -n 's/^| open | #\([0-9]*\) |.*/\1/p' "$out")" "issue-replay: open-at-cutoff membership"
  assert_not_contains "$out" "| open | #7 |" "issue-replay: issues created after the cutoff must be excluded"

  out="$tmp/closed.md"
  PATH="$bin:$PATH" python3 "$ROOT/scripts/snapshot-upstream-issues.py" \
    --repo fix/repo --state closed --from 2026-07-06 --through 2026-07-25 --reconstruct-at "$cutoff" \
    --expect-count 3 --format markdown > "$out" 2>"$tmp/err"
  assert_eq "0" "$?" "issue-replay: closed cohort count"
  assert_eq "1
2
9" "$(sed -n 's/^| closed | #\([0-9]*\) |.*/\1/p' "$out")" "issue-replay: closed-in-window membership at cutoff"
  assert_not_contains "$out" "| closed | #8 |" "issue-replay: pull requests must be excluded"
  assert_not_contains "$out" "| closed | #3 |" "issue-replay: issues closed before the window must be excluded"
  assert_not_contains "$out" "| closed | #4 |" "issue-replay: issues closed after the cutoff must not be in the closed cohort"
  assert_not_contains "$out" "| closed | #5 |" "issue-replay: reopened-before-cutoff issues must not be in the closed cohort"

  rm -rf "$tmp"
}

# --------------------------------------------------------------------------
# issue-cli
# --------------------------------------------------------------------------

test_issue_cli() {
  local tmp bin manifest log
  tmp="$(mktemp -d)"
  bin="$tmp/bin"
  mkdir -p "$bin"
  log="$tmp/gh-calls.log"

  # Fake gh records every mutating call and answers searches from a state file.
  cat > "$bin/gh" <<FAKE
#!/usr/bin/env bash
set -uo pipefail
LOG="$log"
STATE="$tmp/created.txt"
touch "\$STATE"
printf '%s\n' "\$*" >> "\$LOG"
case "\$1" in
  issue)
    case "\${2:-}" in
      create)
        title=""
        next=""
        for arg in "\$@"; do
          if [ "\$next" = "title" ]; then title="\$arg"; next=""; continue; fi
          case "\$arg" in --title) next=title ;; esac
        done
        n=\$(( \$(wc -l < "\$STATE" | tr -d ' ') + 900 ))
        printf '%s\n' "\$title" >> "\$STATE"
        printf 'https://github.com/fix/repo/issues/%s\n' "\$n"
        exit 0
        ;;
      list)
        printf '[]\n'
        exit 0
        ;;
    esac
    ;;
  api)
    printf '{"total_count":0,"items":[]}\n'
    exit 0
    ;;
esac
printf 'fake gh: unhandled %s\n' "\$*" >&2
exit 1
FAKE
  chmod +x "$bin/gh"

  manifest="$tmp/manifest.md"
  cat > "$manifest" <<'MD'
# fixture manifest

- [ ] `00/01-alpha.md` — status:current — issue:pending
- [ ] `00/02-beta.md` — status:mixed — issue:pending
MD

  PATH="$bin:$PATH" python3 "$ROOT/scripts/create_issues.py" --manifest "$manifest" --repo fix/repo > "$tmp/dry.log" 2>"$tmp/dry.err"
  assert_eq "0" "$?" "issue-cli: dry-run must exit 0"
  assert_eq "0" "$(grep -c 'issue create' "$log" 2>/dev/null | tr -d ' ')" "issue-cli: dry-run must not create issues"
  assert_eq "2" "$(grep -c '^CREATE ' "$tmp/dry.log" 2>/dev/null | tr -d ' ')" "issue-cli: dry-run must report planned creates"

  PATH="$bin:$PATH" python3 "$ROOT/scripts/create_issues.py" --manifest "$manifest" --repo fix/repo --create > "$tmp/create1.log" 2>"$tmp/create1.err"
  assert_eq "0" "$?" "issue-cli: first --create must exit 0"
  assert_eq "2" "$(grep -c 'issue create' "$log" 2>/dev/null | tr -d ' ')" "issue-cli: first --create must create each row once"
  assert_eq "2" "$(grep -c '^CREATE ' "$tmp/create1.log" 2>/dev/null | tr -d ' ')" "issue-cli: first --create must report two creates"
  assert_eq "0" "$(grep -c 'issue:pending' "$manifest" 2>/dev/null | tr -d ' ')" "issue-cli: manifest must record resolved issue URLs"
  assert_contains "$manifest" "https://github.com/fix/repo/issues/" "issue-cli: manifest must contain issue URLs"

  PATH="$bin:$PATH" python3 "$ROOT/scripts/create_issues.py" --manifest "$manifest" --repo fix/repo --create > "$tmp/create2.log" 2>"$tmp/create2.err"
  assert_eq "0" "$?" "issue-cli: second --create must exit 0"
  assert_eq "2" "$(grep -c 'issue create' "$log" 2>/dev/null | tr -d ' ')" "issue-cli: second --create must be idempotent"
  assert_eq "2" "$(grep -c '^RECORDED ' "$tmp/create2.log" 2>/dev/null | tr -d ' ')" "issue-cli: second run must report RECORDED rows"

  # The issue body contract must be enforced.
  local bodies
  bodies="$(grep -c 'SCOPE_EXTEND' "$log" 2>/dev/null | tr -d ' ')"
  if [ "$bodies" -lt 2 ]; then
    fail "issue-cli: every created issue body must carry SCOPE_EXTEND"
  fi

  # A fenced example row is documentation, not a target row.
  cat > "$tmp/fenced.md" <<'MD'
# fixture manifest with a documented row format

```text
- [ ] `<block>/<NN>-<slug>.md` — status:<current|mixed|historical|target> — issue:<url>
```

- [ ] `00/01-alpha.md` — status:current — issue:pending
MD
  PATH="$bin:$PATH" python3 "$ROOT/scripts/create_issues.py" --manifest "$tmp/fenced.md" --repo fix/repo > "$tmp/fenced.log" 2>"$tmp/fenced.err"
  assert_eq "0" "$?" "issue-cli: fenced format example must not be parsed as a row"
  assert_eq "1" "$(grep -c '^CREATE ' "$tmp/fenced.log" 2>/dev/null | tr -d ' ')" "issue-cli: only the real row counts"

  # A broad legacy scope is migration evidence, never an adoptable work unit.
  local legacybin="$tmp/legacybin"
  mkdir -p "$legacybin"
  cat > "$legacybin/gh" <<'LEGACY'
#!/usr/bin/env bash
set -uo pipefail
if [ "${1:-}" = "issue" ] && [ "${2:-}" = "list" ]; then
  cat <<'JSON'
[{"number":147,"title":"legacy","url":"https://github.com/fix/repo/issues/147","body":"## Scope paths\n\n- 09/05-production-canary-and-recovery.md\n- 09/03-provision-and-observe-via-nyxid/index.md\n- PLAN.md\n"},
 {"number":148,"title":"exact","url":"https://github.com/fix/repo/issues/148","body":"scope_paths:\n- 00/02-beta.md\n"}]
JSON
  exit 0
fi
printf 'legacy fake gh: refused mutation %s\\n' "$*" >&2
exit 1
LEGACY
  chmod +x "$legacybin/gh"
  cat > "$tmp/legacy.md" <<'MD'
- [ ] `09/05-production-canary-and-recovery.md` — status:mixed — issue:pending
- [ ] `00/02-beta.md` — status:mixed — issue:pending
MD
  PATH="$legacybin:$PATH" python3 "$ROOT/scripts/create_issues.py" --manifest "$tmp/legacy.md" --repo fix/repo > "$tmp/legacy.log" 2>"$tmp/legacy.err"
  assert_eq "0" "$?" "issue-cli: legacy-scope dry-run must exit 0"
  assert_contains "$tmp/legacy.log" "CREATE 09/05-production-canary-and-recovery.md" "issue-cli: multi-path legacy scope must not be reused"
  assert_contains "$tmp/legacy.log" "REUSE 00/02-beta.md https://github.com/fix/repo/issues/148" "issue-cli: exact single-path scope must be reused"

  # A duplicate target path is a manifest defect, not something to silently merge.
  cat > "$tmp/dup.md" <<'MD'
- [ ] `00/01-alpha.md` — status:current — issue:pending
- [ ] `00/01-alpha.md` — status:current — issue:pending
MD
  PATH="$bin:$PATH" python3 "$ROOT/scripts/create_issues.py" --manifest "$tmp/dup.md" --repo fix/repo > /dev/null 2>&1
  assert_eq "1" "$?" "issue-cli: duplicate target path must exit 1"

  rm -rf "$tmp"
}

# --------------------------------------------------------------------------

run_suite() {
  case "$1" in
    frozen-upstream) test_frozen_upstream ;;
    issue-snapshot)  test_issue_snapshot ;;
    issue-replay)    test_issue_replay ;;
    issue-cli)       test_issue_cli ;;
    *) printf 'unknown suite: %s\n' "$1" >&2; exit 2 ;;
  esac
  if [ "$FAILURES" -eq 0 ]; then
    printf '%s: PASS\n' "$1"
  else
    printf '%s: FAIL (%d assertions)\n' "$1" "$FAILURES"
  fi
}

main() {
  if [ "$#" -ne 1 ]; then
    printf 'usage: %s <frozen-upstream|issue-snapshot|issue-replay|issue-cli|all>\n' "$0" >&2
    exit 2
  fi
  if [ "$1" = "all" ]; then
    local rc=0
    for suite in frozen-upstream issue-snapshot issue-replay issue-cli; do
      FAILURES=0
      run_suite "$suite"
      [ "$FAILURES" -eq 0 ] || rc=1
    done
    exit "$rc"
  fi
  run_suite "$1"
  [ "$FAILURES" -eq 0 ]
}

main "$@"
