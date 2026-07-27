#!/usr/bin/env bash
# Fixture regression tests for the aevatar-review documentation tooling.
#
# Usage: bash scripts/tests/test-doc-checks.sh <suite>
#   frozen-upstream  materialize-frozen-upstream.sh snapshot isolation
#   issue-snapshot   snapshot-upstream-issues.py pagination/dedupe/escaping/count
#   issue-replay     snapshot-upstream-issues.py historical state replay + boundaries
#   issue-cli        create_issues.py manifest parsing and issue idempotency
#   validators       check-md.sh / check-links.py / check-drift.sh contracts
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
# validators
# --------------------------------------------------------------------------

make_chapter() {
  # make_chapter <file> <status> <sha> <spine-lines> <diagrams> [extra]
  local file="$1" status="$2" sha="$3" spine="$4" diagrams="$5"
  mkdir -p "$(dirname "$file")"
  {
    printf -- '---\n'
    printf 'status: %s\n' "$status"
    printf 'upstream_commit: %s\n' "$sha"
    printf 'verified_at: 2026-07-25\n'
    printf -- '---\n\n'
    printf '# 固定标题\n\n'
    printf '> 版本与结论：本章描述 %s。\n\n' "$status"
    printf '## 设计抽象与事实源\n\n'
    printf '%b' "$spine"
    printf '\n## 先建立模型\n\n'
    printf '```mermaid\n%%%%{init: {"maxTextSize": 100000}}%%%%\nflowchart LR\n    A["a"] --> B["b"]\n```\n\n'
    if [ "$diagrams" -ge 2 ]; then
      printf '## 沿一条链路走读\n\n'
      printf '```mermaid\n%%%%{init: {"maxTextSize": 100000}}%%%%\nsequenceDiagram\n    participant C as C\n    participant O as O\n    C->>O: cmd\n```\n\n'
    fi
    printf '## 为什么是它，不是别的\n\n说明取舍。\n\n'
    printf '## 协议与状态深入\n\n说明协议。\n\n'
    printf '## 最小示例\n\n> Demo status：`verified-static`\n\n'
    printf '## 边界与演进\n\n说明边界。\n\n'
    printf '## 读完应能回答\n\n1. 问题一？\n2. 问题二？\n3. 问题三？\n'
  } > "$file"
}

test_validators() {
  local tmp repo src
  tmp="$(mktemp -d)"
  repo="$tmp/repo"
  src="$tmp/src"
  mkdir -p "$repo/docs/migration" "$src/src/Aevatar.Foundation.Abstractions" "$src/docs/canon"
  printf 'line1\nline2\nline3\n' > "$src/src/Aevatar.Foundation.Abstractions/IActorRuntime.cs"
  printf 'canon\n' > "$src/docs/canon/overview.md"
  printf '<Solution />\n' > "$src/aevatar.slnx"

  local SHA=f02aa690bbebb9cabeac30a553d737486b0eb661
  local BAD=0000000000000000000000000000000000000000

  cat > "$repo/docs/migration/2026-07-25-target-chapters.md" <<MANIFEST
# fixture manifest

- [ ] \`00/01-good.md\` — status:current — issue:https://example.invalid/1
- [ ] \`00/02-planned.md\` — status:current — issue:https://example.invalid/2
MANIFEST
  printf '01/01-old.md\n' > "$repo/docs/migration/2026-07-25-old-retire-paths.txt"

  local GOOD_SPINE='- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs:2`：运行时查找与生命周期。\n'
  local run="AEVATAR_SRC=$src bash $ROOT/scripts/check-md.sh --repo-root $repo"

  # 1. a fully conforming chapter must pass
  make_chapter "$repo/00/01-good.md" current "$SHA" "$GOOD_SPINE" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths 00/01-good.md > "$tmp/ok.log" 2>&1
  assert_eq "0" "$?" "validators: conforming chapter must pass"

  # 2. missing frontmatter
  mkdir -p "$repo/probe"
  printf '# 无 frontmatter\n\n正文。\n' > "$repo/probe/00-nofm.md"
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/00-nofm.md > "$tmp/nofm.log" 2>&1
  assert_eq "1" "$?" "validators: missing frontmatter must fail"
  assert_contains "$tmp/nofm.log" "frontmatter" "validators: frontmatter failure must be named"

  # 3. invalid status
  make_chapter "$repo/probe/01-badstatus.md" draft "$SHA" "$GOOD_SPINE" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/01-badstatus.md > "$tmp/badstatus.log" 2>&1
  assert_eq "1" "$?" "validators: invalid status must fail"
  assert_contains "$tmp/badstatus.log" "status" "validators: status failure must be named"

  # 4. wrong upstream_commit
  make_chapter "$repo/probe/02-badsha.md" current "$BAD" "$GOOD_SPINE" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/02-badsha.md > "$tmp/badsha.log" 2>&1
  assert_eq "1" "$?" "validators: wrong upstream_commit must fail"
  assert_contains "$tmp/badsha.log" "upstream_commit" "validators: baseline failure must be named"

  # 5. only one diagram
  make_chapter "$repo/probe/03-onediagram.md" current "$SHA" "$GOOD_SPINE" 1
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/03-onediagram.md > "$tmp/onediagram.log" 2>&1
  assert_eq "1" "$?" "validators: single diagram must fail"
  assert_contains "$tmp/onediagram.log" "diagram" "validators: diagram failure must be named"

  # 6. four source-spine paths
  local FOUR='- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs:1`：a。\n- `docs/canon/overview.md:1`：b。\n- `aevatar.slnx:1`：c。\n- `docs/canon/overview.md:1`：d。\n'
  make_chapter "$repo/probe/04-fourspine.md" current "$SHA" "$FOUR" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/04-fourspine.md > "$tmp/four.log" 2>&1
  assert_eq "1" "$?" "validators: more than three spine paths must fail"
  assert_contains "$tmp/four.log" "spine" "validators: spine-count failure must be named"

  # 7. out-of-range source line anchor
  local OOR='- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs:900`：越界锚点。\n'
  make_chapter "$repo/probe/05-oorline.md" current "$SHA" "$OOR" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/05-oorline.md > "$tmp/oor.log" 2>&1
  assert_eq "1" "$?" "validators: out-of-range line anchor must fail"
  assert_contains "$tmp/oor.log" "line" "validators: line-anchor failure must be named"

  # 7b. multi-line and range anchors are validated element by element
  local MULTI='- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs:1,3`：多行锚点。\n'
  make_chapter "$repo/probe/05b-multiline.md" current "$SHA" "$MULTI" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/05b-multiline.md > "$tmp/multi.log" 2>&1
  assert_eq "0" "$?" "validators: valid multi-line anchor must pass"

  local MULTIBAD='- `src/Aevatar.Foundation.Abstractions/IActorRuntime.cs:1,900`：一个越界。\n'
  make_chapter "$repo/probe/05c-multibad.md" current "$SHA" "$MULTIBAD" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/05c-multibad.md > "$tmp/multibad.log" 2>&1
  assert_eq "1" "$?" "validators: one out-of-range element in a multi-line anchor must fail"
  assert_contains "$tmp/multibad.log" "900" "validators: the offending element must be named"

  # 8. nonexistent source path
  local MISS='- `src/Nope/Missing.cs:1`：不存在。\n'
  make_chapter "$repo/probe/06-misssrc.md" current "$SHA" "$MISS" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --paths probe/06-misssrc.md > "$tmp/misssrc.log" 2>&1
  assert_eq "1" "$?" "validators: nonexistent source path must fail"

  # 9. --all rejects a missing target chapter
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --all > "$tmp/all.log" 2>&1
  assert_eq "1" "$?" "validators: --all must fail while a target chapter is missing"
  assert_contains "$tmp/all.log" "00/02-planned.md" "validators: --all must name the missing target"

  # 10. --all rejects an orphan substantive chapter, --allow-retiring tolerates listed ones
  make_chapter "$repo/00/02-planned.md" current "$SHA" "$GOOD_SPINE" 2
  local b
  for b in 00 01 02 03 04 05 06 07 08 09 10 11 12 13; do
    mkdir -p "$repo/$b"
    printf -- '---\nstatus: index\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# %s 导读\n\n阅读顺序。\n' "$SHA" "$b" > "$repo/$b/index.md"
  done
  rm -rf "$repo/probe"
  make_chapter "$repo/01/01-old.md" current "$SHA" "$GOOD_SPINE" 2
  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --all > "$tmp/orphan.log" 2>&1
  assert_eq "1" "$?" "validators: --all must reject an orphan substantive chapter"
  assert_contains "$tmp/orphan.log" "01/01-old.md" "validators: orphan must be named"

  AEVATAR_SRC="$src" bash "$ROOT/scripts/check-md.sh" --repo-root "$repo" --all --allow-retiring > "$tmp/retiring.log" 2>&1
  assert_eq "0" "$?" "validators: --all --allow-retiring must tolerate listed retire paths"

  # ---------------- check-links ----------------
  printf -- '---\nstatus: current\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# 链接\n\n见 [good](../00/01-good.md) 与 [gone](../00/99-gone.md)。\n' "$SHA" > "$repo/01/02-links.md"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/02-links.md > "$tmp/links.log" 2>&1
  assert_eq "1" "$?" "validators: broken link must fail"
  assert_contains "$tmp/links.log" "00/99-gone.md" "validators: broken link target must be named"

  printf -- '---\nstatus: current\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# 计划\n\n见 [planned](../00/02-planned.md) 与 [frag](../00/01-good.md#不存在的小节)。\n' "$SHA" > "$repo/01/03-planned-link.md"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/03-planned-link.md --allow-planned > "$tmp/frag.log" 2>&1
  assert_eq "1" "$?" "validators: missing heading fragment must fail"
  assert_contains "$tmp/frag.log" "不存在的小节" "validators: missing fragment must be named"

  rm -f "$repo/00/02-planned.md"
  printf -- '---\nstatus: current\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# 计划\n\n见 [planned](../00/02-planned.md)。\n' "$SHA" > "$repo/01/04-planned-only.md"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/04-planned-only.md --allow-planned > "$tmp/planned.log" 2>&1
  assert_eq "0" "$?" "validators: --allow-planned must accept a manifest target that is not written yet"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/04-planned-only.md > "$tmp/planned2.log" 2>&1
  assert_eq "1" "$?" "validators: without --allow-planned an unwritten target is a broken link"

  # a link inside a fenced code block is not a link
  printf -- '---\nstatus: current\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# 代码\n\n```\n[gone](../00/99-gone.md)\n```\n\n`[also](../00/98-gone.md)`\n' "$SHA" > "$repo/01/05-fenced.md"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/05-fenced.md > "$tmp/fenced-link.log" 2>&1
  assert_eq "0" "$?" "validators: links inside code spans/fences must be ignored"

  # MkDocs exposes chapter blocks through docs/<block> symlinks, so a relative
  # asset link must resolve against the site view, not the raw tree.
  mkdir -p "$repo/docs/assets"
  printf 'png\n' > "$repo/docs/assets/demo.png"
  ( cd "$repo/docs" && ln -sf ../01 01 )
  printf -- '---\nstatus: current\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# 资产\n\n![demo](../assets/demo.png)\n' "$SHA" > "$repo/01/06-asset.md"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/06-asset.md > "$tmp/asset.log" 2>&1
  assert_eq "0" "$?" "validators: asset link must resolve through the docs symlink view"

  printf -- '---\nstatus: current\nupstream_commit: %s\nverified_at: 2026-07-25\n---\n\n# 资产\n\n![gone](../assets/missing.png)\n' "$SHA" > "$repo/01/07-asset-gone.md"
  python3 "$ROOT/scripts/check-links.py" --repo-root "$repo" --paths 01/07-asset-gone.md > "$tmp/asset2.log" 2>&1
  assert_eq "1" "$?" "validators: a genuinely missing asset must still fail"

  # ---------------- check-drift ----------------
  printf 'nav:\n  - 首页: index.md\n  - 01 旧: 01/01-old.md\n' > "$repo/mkdocs.yml"
  printf '# README\n\n本书共 43 篇章节。\n' > "$repo/README.md"
  bash "$ROOT/scripts/check-drift.sh" --repo-root "$repo" > "$tmp/drift.log" 2>&1
  assert_eq "1" "$?" "validators: drift scan must fail on a retired path in active navigation"
  assert_contains "$tmp/drift.log" "01/01-old.md" "validators: retired nav path must be named"
  assert_contains "$tmp/drift.log" "43" "validators: stale chapter-count claim must be named"

  rm -rf "$tmp"
}

# --------------------------------------------------------------------------

run_suite() {
  case "$1" in
    frozen-upstream) test_frozen_upstream ;;
    issue-snapshot)  test_issue_snapshot ;;
    issue-replay)    test_issue_replay ;;
    issue-cli)       test_issue_cli ;;
    validators)      test_validators ;;
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
    printf 'usage: %s <frozen-upstream|issue-snapshot|issue-replay|issue-cli|validators|all>\n' "$0" >&2
    exit 2
  fi
  if [ "$1" = "all" ]; then
    local rc=0
    for suite in frozen-upstream issue-snapshot issue-replay issue-cli validators; do
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
