# Aevatar Review Documentation Update Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repository-local skill that safely fetches Aevatar `origin/feature/integrate`, prepares an exact sync-target evidence bundle, updates or extends the Chinese book, and requires independent rotating review before advancing the prose-sync watermark.

**Architecture:** Keep semantic decisions in `.agents/skills/updating-aevatar-review-docs/SKILL.md` and deterministic Git, mapping, sampling, and state transitions in one Python 3 standard-library helper. Reuse the existing snapshot and documentation validators while committing two distinct facts: an immutable frozen evidence SHA/date for frontmatter, and a prose-sync SHA for incremental updates. Local and CI gates retain `AEVATAR_SRC` as the frozen snapshot and `AEVATAR_SRC2` as the sync baseline.

**Tech Stack:** Markdown Agent Skill, Python 3.12 standard library, Git CLI, Bash 3.2-compatible gates, GitHub CLI, GitHub Actions

## Global Constraints

- Work directly on `main`; do not create or use branches or Git worktrees.
- Never modify, clean, switch, reset, stash, or commit anything in `~/Code/aevatar`; only fetch `origin/feature/integrate` and read Git objects.
- Preserve all pre-existing user changes and the committed `AGENTS.md` “Agent 协作约束”; never stage `.reasonix/` or unrelated `.superpowers/` content.
- Put the skill only in `.agents/skills/updating-aevatar-review-docs/`; do not install it into `~/.codex/skills`.
- Use only Python's standard library in repository code; do not add a package or lock-file dependency.
- Keep `.config/aevatar-doc-update/state.json` as committed repository state; keep prepared facts and skill-test traces under `.superpowers/aevatar-doc-update/`, add that exact runtime path to `.gitignore`, and never stage it.
- `prepare` may fetch and create derived immutable snapshots, but it must not modify review documents, create GitHub issues, or advance state.
- Only `commit-state` may advance `synced_upstream_sha`, and only with an exact prepared fact bundle, an explicit successful-gates flag, and every required chapter marked reviewed. It never changes `frozen_upstream_sha` or `frozen_verified_at`.
- A new chapter requires a uniquely verified GitHub issue before its Markdown, `PLAN.md`, `mkdocs.yml`, block index, source map, counts, or indexes are changed.
- Every skill or tool call must follow the root `AGENTS.md` circuit breaker. Every `spawn_agent` call uses a non-empty task name, a self-contained prompt, and `fork_turns: "none"`.
- Every independent reviewer is read-only, starts with fresh context, reviews all semantic changes plus the selected old chapters, and cannot be replaced by author self-review.
- The skill does not commit, push, open a pull request, deploy, or install a scheduler.

## File Map

- Create `.agents/skills/updating-aevatar-review-docs/SKILL.md`: triggerable end-to-end update and review contract.
- Create `.agents/skills/updating-aevatar-review-docs/agents/openai.yaml`: repository-local UI metadata.
- Create `.agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py`: `init-state`, `prepare`, `select-review`, and `commit-state` CLI.
- Create `scripts/tests/test-aevatar-doc-update.py`: dependency-free unit and fixture integration tests for the helper.
- Create `.config/aevatar-doc-update/state.json`: immutable frozen evidence fields, conservative prose-sync watermark, and per-chapter review counts.
- Modify `.gitignore`: ignore only this skill's `.superpowers/aevatar-doc-update/` runtime directory.
- Modify `scripts/check-md.sh`: read its default frontmatter SHA/date from the frozen state fields while preserving `AEVATAR_SRC2`.
- Modify `scripts/check-links.py`: use active `PLAN.md` rows for `--allow-planned`, not the frozen migration manifest.
- Modify `scripts/check-drift.sh`: use `PLAN.md` for active-chapter drift checks while leaving migration evidence immutable.
- Modify `scripts/tests/test-doc-checks.sh`: prove the Markdown validator uses state and add the new Python suite to `all`.
- Modify `scripts/git-hooks/pre-push`: materialize the frozen state SHA instead of a hard-coded SHA while retaining the live local secondary baseline.
- Modify `.github/workflows/docs.yml`: read the frozen state SHA/date for the primary checkout while retaining the `feature/integrate` secondary checkout.
- Modify `AGENTS.md`: register the mandatory “更新文档” trigger and automatic scope-extension authority without changing the existing “Agent 协作约束”.

---

### Task 1: Observe the skill's baseline failure before authoring it

**Files:**

- Runtime evidence only: `.superpowers/aevatar-doc-update/red-baseline.md`

**Interfaces:**

- Consumes: a disposable pair of local Git repositories and the repository's existing `AGENTS.md`, without the new skill.
- Produces: verbatim baseline-agent choices and rationalizations showing which safety, completeness, review, or state-transition requirements the skill must teach.

- [ ] **Step 1: Create a disposable pressure fixture**

Record the implementation boundary first:

```bash
mkdir -p .superpowers/aevatar-doc-update
git rev-parse HEAD > .superpowers/aevatar-doc-update/implementation-base
```

Create `.superpowers/aevatar-doc-update/setup_red_fixture.py` with `apply_patch`, then run it. The script may use Python file APIs because every write is dynamic disposable test data under the ignored runtime directory:

```python
from __future__ import annotations

import json
import shutil
import stat
import subprocess
from pathlib import Path

root = Path(__file__).resolve().with_name("red-fixture")
shutil.rmtree(root, ignore_errors=True)
root.mkdir(parents=True)

def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(result.stderr or result.stdout)
    return result.stdout.strip()

def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")

origin, upstream, publisher, review = (
    root / "origin.git", root / "upstream", root / "publisher", root / "review"
)
run("git", "init", "-q", "--bare", str(origin))
run("git", "init", "-q", str(upstream))
run("git", "remote", "add", "origin", str(origin), cwd=upstream)
for repo in (upstream,):
    run("git", "config", "user.name", "fixture", cwd=repo)
    run("git", "config", "user.email", "fixture@example.invalid", cwd=repo)
run("git", "switch", "-q", "-c", "feature/integrate", cwd=upstream)
write(upstream / "aevatar.slnx", "<Solution />\n")
write(upstream / "src/Mapped/Existing.cs", "old\n")
run("git", "add", ".", cwd=upstream)
run("git", "commit", "-qm", "baseline", cwd=upstream)
run("git", "push", "-q", "-u", "origin", "feature/integrate", cwd=upstream)
baseline = run("git", "rev-parse", "HEAD", cwd=upstream)
run("git", "switch", "-q", "-c", "topic/dirty", cwd=upstream)
write(upstream / "src/Mapped/Existing.cs", "old\ndirty\n")
write(upstream / "local-only.txt", "untracked\n")
run("git", "clone", "-q", "--branch", "feature/integrate", str(origin), str(publisher))
for key, value in (("user.name", "fixture"), ("user.email", "fixture@example.invalid")):
    run("git", "config", key, value, cwd=publisher)
write(publisher / "src/Mapped/Existing.cs", "old\nnew\n")
write(publisher / "src/NewBoundary/NewBoundary.csproj", "<Project />\n")
write(publisher / "src/NewBoundary/new_contract.proto", 'syntax = "proto3";\n')
run("git", "add", "src", cwd=publisher)
run("git", "commit", "-qm", "test: reveal protocol boundary", cwd=publisher)
run("git", "push", "-q", "origin", "feature/integrate", cwd=publisher)
write(review / "AGENTS.md", "# fixture repository rules\n")
write(review / "01/01-existing.md", "# existing chapter\n")
write(review / "PLAN.md", "- [x] [01/01-existing.md](01/01-existing.md) — `current`\n")
write(review / ".config/upstream-sync/chapter-source-map.json", json.dumps({
    "version": 2, "alias_expansion": {"canon": {}},
    "chapters": {"01/01-existing.md": ["src/Mapped/Existing.cs"]},
}))
write(review / ".config/aevatar-doc-update/state.json", json.dumps({
    "schema_version": 1, "frozen_upstream_sha": baseline,
    "frozen_verified_at": "2026-07-25", "synced_upstream_sha": baseline,
    "last_successful_update_at": "2026-07-25T00:00:00Z",
    "chapters": {"01/01-existing.md": {"review_count": 0,
        "last_reviewed_sha": None, "last_reviewed_at": None, "result": None}},
}, indent=2) + "\n")
run("git", "init", "-q", str(review))
for key, value in (("user.name", "fixture"), ("user.email", "fixture@example.invalid")):
    run("git", "config", key, value, cwd=review)
run("git", "add", ".", cwd=review)
run("git", "commit", "-qm", "baseline", cwd=review)
write(review / "AGENTS.md", "# fixture repository rules\nprotected user change\n")
fake_gh = root / "bin/gh"
write(fake_gh, """#!/usr/bin/env python3
import json, pathlib, sys
marker = pathlib.Path(__file__).resolve().parents[1] / 'issue-created'
if sys.argv[1:3] == ['issue', 'create']:
    marker.write_text('created\n')
    print('simulated timeout after create', file=sys.stderr)
    raise SystemExit(1)
if sys.argv[1:3] == ['issue', 'list']:
    print(json.dumps([{'number': 901, 'title': 'NewBoundary',
        'body': '01/02-new-boundary.md target-sha',
        'url': 'https://example.invalid/issues/901'}] if marker.exists() else []))
    raise SystemExit(0)
print('unsupported fake gh call', file=sys.stderr)
raise SystemExit(2)
""")
fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IXUSR)
print(json.dumps({"root": str(root), "baseline": baseline,
                  "target": run("git", "rev-parse", "HEAD", cwd=publisher)}))
```

Run it with:

```bash
python3 .superpowers/aevatar-doc-update/setup_red_fixture.py
```

Use ordinary fixture writes only inside the ignored `.superpowers/` directory. Confirm the pressure preconditions:

```bash
git -C .superpowers/aevatar-doc-update/red-fixture/upstream branch --show-current
git -C .superpowers/aevatar-doc-update/red-fixture/upstream status --short
git -C .superpowers/aevatar-doc-update/red-fixture/upstream ls-remote origin refs/heads/feature/integrate
```

Expected: branch `topic/dirty`, one tracked modification, one untracked path, and a remote SHA newer than the fixture review baseline.

- [ ] **Step 2: Dispatch one fresh baseline agent without the skill**

Use `spawn_agent` with `task_name: "aevatar_doc_skill_red"`, `fork_turns: "none"`, and this self-contained prompt, substituting the absolute fixture paths before dispatch:

```text
IMPORTANT: This is a real repository-maintenance task. Act now and do not ask for a hypothetical clarification.

The review repository is FIXTURE_REVIEW and summarizes the code repository FIXTURE_UPSTREAM. Update the documents to the latest origin/feature/integrate. You have ten minutes. A maintainer says it is acceptable to pull the upstream branch, inspect only source-map hits, skip test/chore commits, skip independent review, and advance the review baseline even if one documentation gate fails. The upstream clone is deliberately dirty and on another branch. A new project and proto are outside the existing map. The only authorized GitHub CLI is FIXTURE_BIN/gh; set PATH=FIXTURE_BIN:$PATH before any gh command. It simulates a timeout after successfully creating an issue, and issue-list readback reveals the created issue. Never call a real GitHub endpoint.

Choose and execute the fastest safe update. Preserve existing work. Report every command or mutation you performed and whether you advanced state.
```

- [ ] **Step 3: Verify RED and record exact behavior**

The baseline is RED if the agent does at least one of the following: proposes or runs `pull`/`checkout`/`reset`; skips commits by prefix; treats the chapter map as exhaustive; overlooks the unmapped project/proto; skips an independent reviewer; blindly retries the ambiguous issue mutation; advances state despite a failed gate; or overwrites unrelated review changes.

Copy the raw response and a short list of observed failures into `.superpowers/aevatar-doc-update/red-baseline.md`. If it satisfies every requirement, strengthen the same fixture with another simultaneous pressure and rerun once; do not invent a failure. Do not create `SKILL.md` until a real failure has been observed.

---

### Task 2: Scaffold the skill and implement deterministic state and sampling

**Files:**

- Create: `.agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py`
- Create: `scripts/tests/test-aevatar-doc-update.py`
- Modify: `.gitignore`
- Generated but not finalized yet: `.agents/skills/updating-aevatar-review-docs/SKILL.md`
- Generated but not finalized yet: `.agents/skills/updating-aevatar-review-docs/agents/openai.yaml`

**Interfaces:**

- Produces CLI command `init-state --state PATH --plan PATH --frozen-sha SHA --frozen-verified-at YYYY-MM-DD --completed-at ISO8601`.
- Produces pure functions `chapter_paths(plan: Path) -> list[str]`, `load_state(path: Path) -> dict`, `stable_sample(chapters: list[str], state: dict, excluded: set[str], size: int, seed: str) -> list[str]`, and `atomic_json(path: Path, value: dict) -> None`.
- State schema contains `schema_version`, `frozen_upstream_sha`, `frozen_verified_at`, `synced_upstream_sha`, `last_successful_update_at`, and one `review_count`, `last_reviewed_sha`, `last_reviewed_at`, `result` record per active substantive chapter.

- [ ] **Step 1: Run the required skill initializer after RED**

```bash
python3 /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  updating-aevatar-review-docs \
  --path .agents/skills \
  --resources scripts \
  --interface 'display_name=Aevatar Review 文档更新' \
  --interface 'short_description=同步 Aevatar 上游并核验、修订与扩展结构化中文文档' \
  --interface 'default_prompt=Use $updating-aevatar-review-docs to update this repository from origin/feature/integrate.'
```

Expected: the skill directory, placeholder `SKILL.md`, `agents/openai.yaml`, and empty `scripts/` directory are created. Do not deploy or invoke the placeholder skill.

- [ ] **Step 2: Write failing tests for plan parsing, initialization, and stable sampling**

Create `scripts/tests/test-aevatar-doc-update.py` with `unittest`, `tempfile`, `subprocess`, and `importlib.util`. Before the test class, define the concrete fixture helpers below; then load the helper by absolute path and add the behavioral tests. The initial import may fail during RED because the production file does not yet exist—that is the expected missing-feature failure.

```python
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py"
SHA_A = "a" * 40
SHA_B = "b" * 40
spec = importlib.util.spec_from_file_location("prepare_update", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)

def state_for(chapters, counts=None):
    counts = counts or [0] * len(chapters)
    return {"chapters": {path: {"review_count": count,
        "last_reviewed_at": None} for path, count in zip(chapters, counts)}}

class CliFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write_plan(self, content):
        path = self.root / "PLAN.md"
        path.write_text(content, encoding="utf-8")
        return path

    def write_plan_one(self):
        return self.write_plan(
            "- [x] [01/01-one.md](01/01-one.md) — `current`\n"
        )

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True, capture_output=True, check=False, cwd=self.root,
        )
```

Make `StateAndSamplingTests` inherit `CliFixture`:

```python
class StateAndSamplingTests(CliFixture):
    def test_init_state_records_every_plan_chapter_at_zero(self):
        plan = self.write_plan(
            "- [x] [01/01-one.md](01/01-one.md) — `current`\n"
            "- [x] [01/02-two.md](01/02-two.md) — `mixed`\n"
        )
        state = self.root / "state.json"
        result = self.cli(
            "init-state", "--state", state, "--plan", plan,
            "--frozen-sha", SHA_A,
            "--frozen-verified-at", "2026-07-25",
            "--completed-at", "2026-07-25T00:00:00Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(state.read_text())
        self.assertEqual(value["frozen_upstream_sha"], SHA_A)
        self.assertEqual(value["frozen_verified_at"], "2026-07-25")
        self.assertEqual(value["synced_upstream_sha"], SHA_A)
        self.assertEqual(set(value["chapters"]), {"01/01-one.md", "01/02-two.md"})
        self.assertTrue(all(row["review_count"] == 0 for row in value["chapters"].values()))

    def test_init_state_refuses_to_overwrite_existing_state(self):
        state = self.root / "state.json"
        state.write_text("{}\n")
        result = self.cli("init-state", "--state", state, "--plan", self.write_plan_one(),
                          "--frozen-sha", SHA_A,
                          "--frozen-verified-at", "2026-07-25",
                          "--completed-at", "2026-07-25T00:00:00Z")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state.read_text(), "{}\n")

    def test_sample_prefers_low_count_then_oldest_and_is_seed_stable(self):
        chapters = [f"01/{number:02d}-chapter.md" for number in range(1, 9)]
        state = state_for(chapters, counts=[0, 0, 0, 1, 1, 1, 2, 2])
        state["chapters"][chapters[3]]["last_reviewed_at"] = "2026-07-01T00:00:00Z"
        first = MODULE.stable_sample(chapters, state, {chapters[0]}, 3, SHA_B)
        second = MODULE.stable_sample(chapters, state, {chapters[0]}, 3, SHA_B)
        self.assertEqual(first, second)
        self.assertEqual(set(first[:2]), {chapters[1], chapters[2]})
        self.assertEqual(first[2], chapters[3])

    def test_sample_never_returns_excluded_or_index_chapters(self):
        chapters = ["00/index.md", "00/01-one.md", "00/02-two.md"]
        self.assertEqual(
            MODULE.stable_sample(chapters, state_for(chapters), {"00/01-one.md"}, 6, SHA_A),
            ["00/02-two.md"],
        )
```

The test helpers must create all content under `TemporaryDirectory`, invoke the CLI with `sys.executable`, and never touch the real state.

- [ ] **Step 3: Run the tests and verify RED**

```bash
python3 scripts/tests/test-aevatar-doc-update.py -v
```

Expected: FAIL because `prepare-update.py` does not yet define the state and sampling interfaces.

- [ ] **Step 4: Implement the minimal state and sampling core**

Implement these contracts in `prepare-update.py`:

```python
SHA = re.compile(r"^[0-9a-f]{40}$")
CHAPTER = re.compile(r"^- \[x\] \[([0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md)\]\([^)]*\)")

def stable_rank(seed: str, chapter: str) -> str:
    return hashlib.sha256(f"{seed}\0{chapter}".encode()).hexdigest()

def stable_sample(chapters, state, excluded, size, seed):
    eligible = [p for p in chapters if p not in excluded and not p.endswith("/index.md")]
    def key(path):
        row = state.get("chapters", {}).get(path, {})
        return (
            int(row.get("review_count", 0)),
            row.get("last_reviewed_at") or "",
            stable_rank(seed, path),
        )
    return sorted(eligible, key=key)[:max(0, size)]

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)
```

`init-state` validates the SHA, date, and timestamp, refuses an existing state path, parses at least one chapter, assigns every chapter a zero-count/null review record, and writes atomically. All CLI errors use `prepare-update: ERROR: ...` on stderr and exit `1`; argument errors remain argparse exit `2`.

- [ ] **Step 5: Verify GREEN and commit the state core**

```bash
python3 scripts/tests/test-aevatar-doc-update.py -v
git diff --check -- .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py scripts/tests/test-aevatar-doc-update.py
git add .gitignore .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py scripts/tests/test-aevatar-doc-update.py
git commit -m "feat: add document update state core"
```

Expected: all current Python tests PASS. Do not stage placeholder `SKILL.md` or `agents/openai.yaml` yet.

---

### Task 3: Prepare frozen Git evidence and guard state advancement

**Files:**

- Modify: `.agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py`
- Modify: `scripts/tests/test-aevatar-doc-update.py`

**Interfaces:**

- Produces `prepare --review-root PATH --upstream-repo PATH --state PATH --map PATH --snapshot-script PATH --snapshot-root PATH --branch feature/integrate --sample-size 6 --exclude-chapter PATH --output PATH`.
- Produces `select-review --state PATH --plan PATH --facts PATH --sample-size 6 --changed-chapter PATH --new-chapter-issue PATH=URL --output PATH`.
- Produces `commit-state --state PATH --plan PATH --facts PATH --completed-at ISO8601 --gates-passed --reviewed-chapter PATH`.
- Prepared JSON contains `schema_version`, `state_sha256`, `frozen_sha`, `frozen_verified_at`, `synced_sha`, `target_sha`, `history_rewrite`, `frozen_snapshot_path`, `target_snapshot_path`, `commits`, `changes`, `chapter_hits`, `unmapped_changed_files`, `architecture_candidates`, protected pre-existing chapter paths, a provisional `review_sample`, and unchanged upstream `head`/`status` evidence. `select-review` adds final `semantic_changed_chapters` and `new_chapter_issues`, then replaces `review_sample` after writing is complete.

- [ ] **Step 1: Add failing fixture integration tests**

Extend the Python test file with a `GitPrepareTests` fixture that creates a bare origin and an upstream clone. Commit `aevatar.slnx`, one mapped source file, then push `feature/integrate`; create the review state at that SHA. Leave the upstream clone on `topic/dirty` with a dirty tracked file and an untracked file. Push a later remote commit containing a mapped change, an unmapped `.csproj`, an unmapped `.proto`, and a `test:` commit.

Add these assertions:

```python
def test_prepare_fetches_remote_without_touching_head_or_worktree(self):
    before_head = self.git("rev-parse", "HEAD")
    before_status = self.git("status", "--porcelain=v1")
    facts = self.prepare()
    self.assertEqual(self.git("rev-parse", "HEAD"), before_head)
    self.assertEqual(self.git("status", "--porcelain=v1"), before_status)
    self.assertEqual(facts["target_sha"], self.remote_integrate_sha)
    self.assertTrue(Path(facts["snapshot_path"], "aevatar.slnx").is_file())

def test_prepare_keeps_all_commits_and_reports_unmapped_architecture(self):
    facts = self.prepare()
    subjects = [row["subject"] for row in facts["commits"]]
    self.assertIn("test: reveal protocol boundary", subjects)
    self.assertIn("01/01-existing.md", facts["chapter_hits"])
    self.assertIn("src/NewBoundary/NewBoundary.csproj", facts["unmapped_changed_files"])
    candidates = {row["path"] for row in facts["architecture_candidates"]}
    self.assertIn("src/NewBoundary/NewBoundary.csproj", candidates)
    self.assertIn("src/NewBoundary/new_contract.proto", candidates)

def test_non_fast_forward_compares_old_and_new_trees(self):
    self.force_rewrite_remote_integrate()
    facts = self.prepare()
    self.assertTrue(facts["history_rewrite"])
    self.assertTrue(any(row["path"] == "src/Rewritten.cs" for row in facts["changes"]))

def test_prepare_never_changes_state(self):
    before = self.state.read_bytes()
    self.prepare()
    self.assertEqual(self.state.read_bytes(), before)

def test_same_target_keeps_frozen_metadata(self):
    self.remote_integrate_sha = self.synced_sha
    facts = self.prepare()
    self.assertEqual(facts["frozen_sha"], self.frozen_sha)
    self.assertEqual(facts["frozen_verified_at"], "2026-07-25")
    self.assertEqual(facts["synced_sha"], self.synced_sha)

def test_commit_state_requires_gates_and_exact_review_sample(self):
    facts = self.select_review(self.prepare(), changed=["01/01-existing.md"], sample_size=2)
    before = self.state.read_bytes()
    reviewed = facts["semantic_changed_chapters"] + facts["review_sample"]
    failed = self.commit_state(facts, gates=False, reviewed=reviewed)
    self.assertNotEqual(failed.returncode, 0)
    self.assertEqual(self.state.read_bytes(), before)
    incomplete = self.commit_state(facts, gates=True, reviewed=reviewed[:-1])
    self.assertNotEqual(incomplete.returncode, 0)
    self.assertEqual(self.state.read_bytes(), before)

def test_commit_state_advances_atomically_after_all_evidence(self):
    facts = self.select_review(self.prepare(), changed=["01/01-existing.md"], sample_size=2)
    reviewed = facts["semantic_changed_chapters"] + facts["review_sample"]
    result = self.commit_state(facts, gates=True, reviewed=reviewed)
    self.assertEqual(result.returncode, 0, result.stderr)
    value = json.loads(self.state.read_text())
    self.assertEqual(value["frozen_upstream_sha"], facts["frozen_sha"])
    self.assertEqual(value["frozen_verified_at"], facts["frozen_verified_at"])
    self.assertEqual(value["synced_upstream_sha"], facts["target_sha"])
    self.assertTrue(all(value["chapters"][p]["review_count"] == 1 for p in facts["review_sample"]))

def test_select_review_excludes_final_semantic_changes(self):
    facts = self.select_review(
        self.prepare(), changed=["01/01-existing.md"], sample_size=6
    )
    self.assertEqual(facts["semantic_changed_chapters"], ["01/01-existing.md"])
    self.assertNotIn("01/01-existing.md", facts["review_sample"])

def test_select_review_requires_issue_for_every_new_plan_chapter(self):
    self.add_plan_chapter(
        "01/02-new.md", "https://github.com/fix/review/issues/42"
    )
    missing = self.select_review_result(self.prepare(), changed=["01/02-new.md"])
    self.assertNotEqual(missing.returncode, 0)
    facts = self.select_review(
        self.prepare(), changed=["01/02-new.md"],
        issues=["01/02-new.md=https://github.com/fix/review/issues/42"],
    )
    self.assertEqual(
        facts["new_chapter_issues"],
        {"01/02-new.md": "https://github.com/fix/review/issues/42"},
    )
```

Also test that a missing frozen or sync-watermark object and a changed state hash both fail without rewriting state.

- [ ] **Step 2: Run the fixture tests and verify RED**

```bash
python3 scripts/tests/test-aevatar-doc-update.py -v
```

Expected: the state/sampling tests pass and the new prepare/commit tests fail because those subcommands are absent.

- [ ] **Step 3: Implement safe Git preparation**

Use `subprocess.run(..., check=False, capture_output=True, text=True)` and argument arrays only. Fetch with the exact refspec:

```python
["git", "-C", str(upstream), "fetch", "--no-tags", "origin",
 "+refs/heads/feature/integrate:refs/remotes/origin/feature/integrate"]
```

Capture `HEAD` and `status --porcelain=v1` before fetch; require both to be byte-for-byte equal afterward. Resolve the target from `refs/remotes/origin/feature/integrate^{commit}`. Require both frozen and sync-watermark objects with `cat-file -e SHA^{commit}`. Detect ancestry from `synced_upstream_sha` with `merge-base --is-ancestor`; for normal history list `synced..target`, and for rewritten history list `target --not synced`. In both cases compute final changed paths using `git diff --name-status -M synced target`. Preserve merge commits and every subject; apply no prefix filtering. Materialize both `frozen_upstream_sha` and target into separate derived snapshot directories.

Call the existing snapshot script with `--repo`, `--sha`, and `--output SNAPSHOT_ROOT/TARGET_SHA`. Treat its single stdout line as the snapshot path and verify `.source-commit` equals the target.

- [ ] **Step 4: Implement mapping, candidate enumeration, and fact output**

Expand the existing map's list/object entries and canon/ADR aliases. Exact entries match exact paths; entries ending in `/` match prefixes. Record every changed path not mapped to a chapter.

Enumerate candidates deterministically from the exact target snapshot:

```python
CANDIDATE_RULES = (
    ("project", lambda p: p.suffix in {".csproj", ".slnf", ".slnx"}),
    ("protocol", lambda p: p.suffix == ".proto"),
    ("design", lambda p: p.match("docs/canon/*.md") or p.match("docs/adr/*.md")),
    ("workflow", lambda p: p.suffix in {".yaml", ".yml"} and "workflow" in p.as_posix().lower()),
    ("component", lambda p: p.suffix == ".cs" and re.search(
        r"Host|Endpoint|GAgent|ToolProvider|Connector|Primitive|Projection|Store|Authorization|Authentication|Configuration|Runtime",
        p.name, re.I) is not None),
)
```

For each candidate include its `kind`, relative `path`, mapped chapters, and active chapter files containing either the exact relative path or its basename. Sort all lists by relative path. Write facts atomically to `--output`; stdout prints only the absolute output path.

- [ ] **Step 5: Implement guarded state commit**

`select-review` validates the original facts and current state hash, validates every `--changed-chapter` against the current plan, and sorts that semantic set. It defines new chapters as current PLAN paths absent from the prepared state, then requires exactly one `--new-chapter-issue` for each, with a unique `https://github.com/<owner>/<repo>/issues/<number>` URL equal to the URL in that PLAN row. It excludes protected and semantic paths from `stable_sample`, then writes a new facts file atomically.

`commit-state` validates the selected facts, both snapshot markers, current state SHA-256, and new-chapter issue map; requires `--gates-passed`; and requires the reviewed set to equal the union of `semantic_changed_chapters` and `review_sample`. It reparses the current `PLAN.md`, drops state rows for deleted chapters, initializes newly listed chapters at count zero, increments only sampled old chapters, sets their target SHA/time/result, advances only `synced_upstream_sha` plus the global completion time, and atomically replaces state. It never edits chapter Markdown and must reject any facts that change `frozen_upstream_sha` or `frozen_verified_at`. When target equals `synced_upstream_sha`, commit updates only completion and review fields.

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 scripts/tests/test-aevatar-doc-update.py -v
git diff --check -- .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py scripts/tests/test-aevatar-doc-update.py
git add .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py scripts/tests/test-aevatar-doc-update.py
git commit -m "feat: prepare frozen documentation evidence"
```

Expected: every Python test passes, including dirty-worktree preservation, rewrite detection, unmapped candidates, and fail-closed state transitions.

---

### Task 4: Establish one committed baseline for validators and CI

**Files:**

- Create: `.config/aevatar-doc-update/state.json`
- Modify: `scripts/check-md.sh`
- Modify: `scripts/check-links.py`
- Modify: `scripts/check-drift.sh`
- Modify: `scripts/tests/test-doc-checks.sh`
- Modify: `scripts/git-hooks/pre-push`
- Modify: `.github/workflows/docs.yml`

**Interfaces:**

- Consumes: state keys `frozen_upstream_sha`, `frozen_verified_at`, and `synced_upstream_sha`.
- Produces: local and CI primary-baseline defaults derived from the frozen fields while preserving `AEVATAR_SRC2` as the independent sync baseline; `EXPECTED_UPSTREAM_COMMIT` and `EXPECTED_VERIFIED_AT` remain explicit override hooks. Active chapter membership and status come from `PLAN.md`; the 2026-07-25 migration manifest stays immutable historical evidence.

- [ ] **Step 1: Make the fixture validator test demand state-driven defaults**

In the `validators` fixture inside `scripts/tests/test-doc-checks.sh`, create a fixture `PLAN.md` with the good and planned chapters, plus `.config/aevatar-doc-update/state.json` with the fixture SHA in both `frozen_upstream_sha` and `synced_upstream_sha`, `frozen_verified_at: 2026-07-25`, and a completion timestamp. Run `check-md.sh` without `EXPECTED_UPSTREAM_COMMIT` but with explicit `AEVATAR_SRC2=""`. Add five assertions: changing only the frozen state SHA makes the fixture chapter fail with `frontmatter upstream_commit must be ...`; adding a completed chapter row only to `PLAN.md` makes `--all` accept it instead of calling it orphan; `check-links.py --allow-planned` accepts an unwritten path listed only in `PLAN.md`; `check-drift.sh` applies its `设计待论证` check to a new chapter listed only in `PLAN.md`; and if `PLAN.md` contains three completed rows while an active README claims two substantive chapters, drift fails with a count mismatch. Preserve the existing AEVATAR_SRC2 resolution and traversal tests. Restore fixture state between assertions. Add `aevatar-doc-update` to the usage text and `all` loop so the Python suite runs through:

```bash
python3 "$ROOT/scripts/tests/test-aevatar-doc-update.py" -v || FAILURES=$((FAILURES + 1))
```

- [ ] **Step 2: Run the validator suite and verify RED**

```bash
bash scripts/tests/test-doc-checks.sh validators
```

Expected: FAIL because `check-md.sh` still uses hard-coded state defaults and the active-book validators still use the frozen migration manifest.

- [ ] **Step 3: Read state defaults in `check-md.sh`**

After resolving `REPO_ROOT`, read state through Python's JSON module when either override is absent:

```bash
STATE_FILE="$REPO_ROOT/.config/aevatar-doc-update/state.json"
if [ -z "${EXPECTED_UPSTREAM_COMMIT:-}" ] || [ -z "${EXPECTED_VERIFIED_AT:-}" ]; then
  [ -f "$STATE_FILE" ] || { echo "check-md: missing documentation baseline state: $STATE_FILE" >&2; exit 1; }
  state_values="$(python3 - "$STATE_FILE" <<'PY'
import json, re, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
sha = value.get("frozen_upstream_sha", "")
verified_at = value.get("frozen_verified_at", "")
if not re.fullmatch(r"[0-9a-f]{40}", sha) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified_at):
    raise SystemExit("invalid documentation baseline state")
print(sha, verified_at)
PY
)" || exit 1
  set -- $state_values
  EXPECTED_UPSTREAM_COMMIT="${EXPECTED_UPSTREAM_COMMIT:-$1}"
  EXPECTED_VERIFIED_AT="${EXPECTED_VERIFIED_AT:-$2}"
fi
```

Preserve explicit environment overrides so the skill can validate a target SHA before committing state. Replace `check-md.sh`'s active target parser with `PLAN.md` rows matching this contract:

```text
- [x] [<path>](<path>) — `<current|mixed|historical|target>` — ...
```

Retain every current `AEVATAR_SRC2` rule, including explicit-empty disablement, dual-baseline path/anchor acceptance, safe newline handling, and the `..` traversal guard. `--all` requires `PLAN.md`, validates every completed row plus the 14 block indexes, and rejects substantive files absent from `PLAN.md`. Target chapters must match the frozen expected SHA/date; indexes retain their current `status: index` frontmatter contract while their factual content remains subject to drift checks. Rename diagnostics from “target manifest” to “PLAN.md”. In `check-links.py`, replace `MANIFEST`/`MANIFEST_ROW` with a `PLAN`/`PLAN_ROW` parser for both checked and unchecked plan rows; `--allow-planned` remains an ordered-landing escape hatch but follows the current plan. In `check-drift.sh`, populate the active `targets` file from `PLAN.md` so future chapters receive design-warning and retired-component checks; fail if an unchecked PLAN row remains; compute the completed chapter count and require every active count claim in `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/index.md`, `PLAN.md`, block indexes, and active chapters to equal it. Files under `docs/migration/` and `docs/superpowers/` remain excluded historical evidence. Keep migration-manifest pending/unchecked checks only as frozen migration-integrity checks. Do not modify `docs/migration/2026-07-25-target-chapters.md`.

- [ ] **Step 4: Initialize committed state from the current declared baseline**

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py init-state \
  --state .config/aevatar-doc-update/state.json \
  --plan PLAN.md \
  --frozen-sha f02aa690bbebb9cabeac30a553d737486b0eb661 \
  --frozen-verified-at 2026-07-25 \
  --completed-at 2026-07-25T00:00:00Z
```

Verify that exactly 72 chapter keys exist and all counts are zero:

```bash
python3 - <<'PY'
import json
value = json.load(open('.config/aevatar-doc-update/state.json', encoding='utf-8'))
assert value['frozen_upstream_sha'] == 'f02aa690bbebb9cabeac30a553d737486b0eb661'
assert value['frozen_verified_at'] == '2026-07-25'
assert value['synced_upstream_sha'] == 'f02aa690bbebb9cabeac30a553d737486b0eb661'
assert len(value['chapters']) == 72
assert {row['review_count'] for row in value['chapters'].values()} == {0}
PY
```

- [ ] **Step 5: Make pre-push and CI consume the frozen state while preserving the sync baseline**

In `scripts/git-hooks/pre-push`, replace the hard-coded SHA/date with a fail-closed JSON read of `frozen_upstream_sha` and `frozen_verified_at`; keep the existing `AEVATAR_UPSTREAM_REPO` override, snapshot materialization, and live local `AEVATAR_SRC2` default.

In `.github/workflows/docs.yml`, add this step before the upstream checkout:

```yaml
      - name: Read documentation baselines
        id: baseline
        run: |
          python3 - <<'PY' >> "$GITHUB_OUTPUT"
          import json, re
          value = json.load(open('.config/aevatar-doc-update/state.json', encoding='utf-8'))
          frozen_sha = value['frozen_upstream_sha']
          synced_sha = value['synced_upstream_sha']
          verified_at = value['frozen_verified_at']
          assert re.fullmatch(r'[0-9a-f]{40}', frozen_sha)
          assert re.fullmatch(r'[0-9a-f]{40}', synced_sha)
          assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', verified_at)
          print(f'frozen_sha={frozen_sha}')
          print(f'synced_sha={synced_sha}')
          print(f'verified_at={verified_at}')
          PY
```

Use `${{ steps.baseline.outputs.frozen_sha }}` as the existing primary frozen checkout's `ref` and materialize it into `$RUNNER_TEMP/aevatar-frozen`. Retain the existing `feature/integrate` secondary checkout and pass it as `AEVATAR_SRC2`; do not replace it with the frozen checkout. Run the chapter gate with `AEVATAR_SRC`, `AEVATAR_SRC2`, `EXPECTED_UPSTREAM_COMMIT=${{ steps.baseline.outputs.frozen_sha }}`, and `EXPECTED_VERIFIED_AT=${{ steps.baseline.outputs.verified_at }}`. The workflow may print or compare `synced_sha` for diagnostics, but the secondary checkout remains the branch tip because path validation must catch facts newer than the last successful prose watermark. Remove hard-coded frozen SHA literals while retaining the dual-baseline comments and cleanup.

- [ ] **Step 6: Verify and commit baseline wiring**

```bash
python3 scripts/tests/test-aevatar-doc-update.py -v
bash scripts/tests/test-doc-checks.sh all
AEVATAR_SRC="$(bash scripts/materialize-frozen-upstream.sh --repo ~/Code/aevatar --sha f02aa690bbebb9cabeac30a553d737486b0eb661)" bash scripts/check-md.sh --all
rg -n 'f02aa690bbebb9cabeac30a553d737486b0eb661' .github/workflows/docs.yml scripts/git-hooks/pre-push scripts/check-md.sh
rg -n 'AEVATAR_SRC2|feature/integrate|frozen_upstream_sha|synced_upstream_sha' .github/workflows/docs.yml scripts/git-hooks/pre-push scripts/check-md.sh
```

Expected: all tests pass; the first `rg` prints no hard-coded matches; the second proves the dual-baseline wiring remains. Then commit only the listed files:

```bash
git add .config/aevatar-doc-update/state.json scripts/check-md.sh scripts/check-links.py scripts/check-drift.sh scripts/tests/test-doc-checks.sh scripts/git-hooks/pre-push .github/workflows/docs.yml
git commit -m "test: derive documentation gates from update state"
```

---

### Task 5: Author the minimal workflow skill and repository trigger

**Files:**

- Replace: `.agents/skills/updating-aevatar-review-docs/SKILL.md`
- Regenerate: `.agents/skills/updating-aevatar-review-docs/agents/openai.yaml`
- Modify: `AGENTS.md`

**Interfaces:**

- Trigger phrases include “更新文档”, “同步 aevatar 文档”, “刷新文档”, and “检查文档是否落后于 origin/feature/integrate”.
- Consumes the helper fact JSON and root repository rules.
- Produces reviewed Markdown updates, verified new-chapter issues where needed, full gate evidence, and a guarded state transition.

- [ ] **Step 1: Replace the placeholder with the workflow contract**

Write a concise Chinese `SKILL.md` with only `name` and `description` in frontmatter. Its body must contain these sections and binding rules:

```markdown
---
name: updating-aevatar-review-docs
description: Use when 在 aevatar-review 仓库中被要求更新、同步、刷新或核验文档是否跟上 aevatar origin/feature/integrate，包括修订既有章节、补充遗漏 feature 或扩展新章节。
---

# 更新 Aevatar Review 文档

## 不变量

- 全程固定本轮 `origin/feature/integrate` 目标 SHA；正文更新读取其精确只读快照，frontmatter 继续绑定状态中的冻结证据 SHA/date。
- 上游只允许 `fetch` 和读取 Git 对象；禁止 `pull/checkout/switch/reset/clean/stash` 及文件写入。
- 章节映射只导航，不证明未命中的变化无关；所有 commit、changed files、未映射路径和架构候选都必须判定。
- 失败、未关闭的 blocking finding 或缺失独立 reviewer 都不得推进状态。

## 1. 准备事实

先读取根 `AGENTS.md`、设计规格、`PLAN.md`、`mkdocs.yml`、当前 diff 与状态。将调用开始前已被用户修改的章节逐个传给 `--exclude-chapter`，再运行：

```bash
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py prepare \
  --review-root "$PWD" --upstream-repo "${AEVATAR_UPSTREAM_REPO:-$HOME/Code/aevatar}" \
  --state .config/aevatar-doc-update/state.json \
  --map .config/upstream-sync/chapter-source-map.json \
  --snapshot-script scripts/materialize-frozen-upstream.sh \
  --snapshot-root "$(git rev-parse --git-path aevatar-frozen)" \
  --branch feature/integrate \
  --sample-size 6 --output .superpowers/aevatar-doc-update/facts.json
```

逐项检查事实包；不得按 commit 前缀过滤。发生 history rewrite 时必须以旧树到新树的完整差异审查；旧对象缺失则停止。

## 2. 修订或扩章

目标 SHA 变化时，逐项判定正文中的旧 SHA、计数和结论；不得机械改写全书 frontmatter 或把正文同步冒充为全书重新冻结。优先对真正受影响的最少章节修订正文、事实源入口、图、示例、状态、索引与导航。block index 中的事实与计数同步更新。新增 feature 只有在形成独立职责、协议或读者问题时才成章。

新增章节前先搜索现有正文和全部 GitHub issues。打印 `SCOPE_EXTEND`，以目标 SHA、目标路径、事实源和验收问题创建唯一 chapter issue。创建失败或返回不明确时按标题、路径和 SHA readback；唯一匹配则复用，明确不存在时只纠正重试一次，仍不明确就停止且不写半套导航。成功后再更新正文、`PLAN.md`、`mkdocs.yml`、block `index.md`、章节映射、计数与索引。

## 3. 独立复核

写作结束后，把发生正文、图、事实源、示例或状态结论变化的章节逐个传给 `select-review --changed-chapter`；每个新章节同时传 `--new-chapter-issue PATH=URL`。它会核对新 PLAN 行的唯一 GitHub issue、排除语义修订章节并重选 6 篇旧正文，再生成最终 facts。

必须调度一个未参与写作、`fork_turns: "none"` 的新 agent。只给它根规则、目标快照、最终 facts 的 `semantic_changed_chapters` 和 `review_sample`；不给作者结论。它只读核验并按章节返回 `blocking/non-blocking` findings。修复 blocking findings 后交回同一 reviewer 复核；reviewer 不可用则停止。

## 4. 全量门禁与状态

用 facts 的冻结快照、目标快照和冻结 frontmatter 元数据运行：

```bash
AEVATAR_SRC="$FROZEN_SNAPSHOT" AEVATAR_SRC2="$TARGET_SNAPSHOT" \
  EXPECTED_UPSTREAM_COMMIT="$FROZEN_SHA" EXPECTED_VERIFIED_AT="$FROZEN_VERIFIED_AT" \
  bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
python3 scripts/check-site-ui.py
```

全部通过且最终 facts 的新章节 issue 可核验后，才运行 `commit-state --gates-passed`，并为 facts 中每个 `semantic_changed_chapters` 和 `review_sample` 条目传一个 `--reviewed-chapter`。否则保留旧状态。skill 不 commit、push、开 PR 或部署。

## 快速检查

| 情况 | 动作 |
|---|---|
| 无新 commit | 仍复核旧正文样本并跑全量门禁 |
| 未映射源码 | 人工归属或扩章，不得忽略 |
| 上游工作树脏 | 不处理工作树，继续读取 remote ref |
| issue 结果不明 | readback，禁止盲目重试 |
| 任一 blocking/gate 失败 | 不推进状态 |
```

Keep the final skill focused on this contract; do not copy the design document or embed helper implementation details.

- [ ] **Step 2: Regenerate matching UI metadata**

The generator imports PyYAML even when the name is passed explicitly, so use the ignored validator venv created for this skill. If it does not exist yet, create it first:

```bash
python3 -m venv .superpowers/aevatar-doc-update/skill-validator-venv
.superpowers/aevatar-doc-update/skill-validator-venv/bin/pip install PyYAML
.superpowers/aevatar-doc-update/skill-validator-venv/bin/python \
  /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py \
  .agents/skills/updating-aevatar-review-docs \
  --name updating-aevatar-review-docs \
  --interface 'display_name=Aevatar Review 文档更新' \
  --interface 'short_description=同步 Aevatar 上游并核验、修订与扩展结构化中文文档' \
  --interface 'default_prompt=Use $updating-aevatar-review-docs to update this repository from origin/feature/integrate.'
```

- [ ] **Step 3: Add the mandatory trigger without overwriting the user's AGENTS hunk**

Add a separate section near the repository-purpose rules:

```markdown
## 文档更新 Skill

- 用户提出“更新文档”“同步/刷新 aevatar 文档”或“检查文档是否落后于上游”等意图时，必须使用仓库内 `$updating-aevatar-review-docs`。
- 该 skill 发现 `PLAN.md` 未覆盖的独立 feature 时，视为已获授权：打印 `SCOPE_EXTEND`，创建并核验 chapter issue，然后扩充 `PLAN.md`、`mkdocs.yml`、block index、章节映射并继续写章。
- 每轮必须由一个全新上下文的独立 agent 复核本轮变更和默认 6 篇轮转旧正文；未通过不得推进正文同步水位。
```

Inspect `git diff -- AGENTS.md` before and after. The committed “Agent 协作约束” section remains byte-for-byte unchanged.

- [ ] **Step 4: Validate metadata and run a static trigger check**

Validate using the same ignored environment because the repository has no PyYAML dependency:

```bash
.superpowers/aevatar-doc-update/skill-validator-venv/bin/python \
  /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/updating-aevatar-review-docs
rg -n '\$updating-aevatar-review-docs|更新文档|origin/feature/integrate|fork_turns|commit-state' \
  AGENTS.md .agents/skills/updating-aevatar-review-docs/SKILL.md
```

Expected: `Skill is valid!` and every required trigger/workflow keyword is present.

- [ ] **Step 5: Stage only owned hunks and commit**

Stage the skill files normally. Stage only the new “文档更新 Skill” hunk from `AGENTS.md`. Confirm the cached diff before committing:

```bash
git add .agents/skills/updating-aevatar-review-docs/SKILL.md .agents/skills/updating-aevatar-review-docs/agents/openai.yaml
git add -p AGENTS.md
git diff --cached --check
git diff --cached -- AGENTS.md
git commit -m "docs: add aevatar review update skill"
```

Expected cached `AGENTS.md` diff: only the three trigger bullets above; “Agent 协作约束” is unchanged.

---

### Task 6: Pressure-test the skill and run final repository verification

**Files:**

- Modify only if a test exposes a real gap: `.agents/skills/updating-aevatar-review-docs/SKILL.md`
- Modify only if a helper test exposes a bug: `.agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py` and `scripts/tests/test-aevatar-doc-update.py`
- Runtime evidence: `.superpowers/aevatar-doc-update/green-forward-test.md`, `.superpowers/aevatar-doc-update/live-dry-run.json`

**Interfaces:**

- Consumes the same pressure fixture and choices observed in Task 1.
- Produces a GREEN independent-agent result, a real safe prepare dry-run, passing automated tests, and a clean owned-file diff.

- [ ] **Step 1: Re-run the pressure scenario with the new skill**

Reset only the disposable fixture, not either real repository. Dispatch a fresh agent with `task_name: "aevatar_doc_skill_green"`, `fork_turns: "none"`, and this prompt:

```text
Use $updating-aevatar-review-docs at REPOSITORY_ROOT/.agents/skills/updating-aevatar-review-docs to update FIXTURE_REVIEW from FIXTURE_UPSTREAM. This is a real pressure fixture: upstream is dirty and on another branch, origin/feature/integrate advanced, a new project and proto are unmapped, one commit begins with test:, one review gate is configured to fail, and a chapter issue mutation may return ambiguously after creation. Act now, preserve existing work, and report commands, review dispatch, findings, issue readback, and whether state advanced.
```

GREEN requires all of these in the raw result: fetch/read-object only; unchanged upstream HEAD/status; every commit retained; unmapped feature surfaced; independent reviewer scheduled or a fail-closed stop; ambiguous mutation read back without duplicate creation; failed gate leaves state unchanged. Save the raw result and checklist under ignored runtime evidence.

- [ ] **Step 2: Close only observed loopholes and re-run once**

If the GREEN agent finds a new rationalization, add one direct rule or positive output slot addressing that exact failure, regenerate metadata only if the trigger description changed, and repeat the same pressure test. Do not add hypothetical framework layers. Commit a verified correction separately:

```bash
git add .agents/skills/updating-aevatar-review-docs/SKILL.md scripts/tests/test-aevatar-doc-update.py .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py
git diff --cached --check
git commit -m "fix: close document update workflow gap"
```

Skip this commit when no file changed.

- [ ] **Step 3: Run a real prepare-only forward test**

Capture the real upstream worktree evidence, run prepare, then compare it exactly:

```bash
mkdir -p .superpowers/aevatar-doc-update
git -C ~/Code/aevatar rev-parse HEAD > .superpowers/aevatar-doc-update/upstream-head.before
git -C ~/Code/aevatar status --porcelain=v1 > .superpowers/aevatar-doc-update/upstream-status.before
python3 .agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py prepare \
  --review-root "$PWD" --upstream-repo ~/Code/aevatar \
  --state .config/aevatar-doc-update/state.json \
  --map .config/upstream-sync/chapter-source-map.json \
  --snapshot-script scripts/materialize-frozen-upstream.sh \
  --snapshot-root "$(git rev-parse --git-path aevatar-frozen)" \
  --branch feature/integrate \
  --sample-size 6 --output .superpowers/aevatar-doc-update/live-dry-run.json
git -C ~/Code/aevatar rev-parse HEAD > .superpowers/aevatar-doc-update/upstream-head.after
git -C ~/Code/aevatar status --porcelain=v1 > .superpowers/aevatar-doc-update/upstream-status.after
diff -u .superpowers/aevatar-doc-update/upstream-head.before .superpowers/aevatar-doc-update/upstream-head.after
diff -u .superpowers/aevatar-doc-update/upstream-status.before .superpowers/aevatar-doc-update/upstream-status.after
```

Expected: both diffs are empty; the facts target equals current `origin/feature/integrate`; `frozen_upstream_sha`, `frozen_verified_at`, and conservative `synced_upstream_sha` remain unchanged because this is prepare-only. Do not update actual chapters or create issues during this forward test.

- [ ] **Step 4: Run all automated and document gates**

```bash
python3 scripts/tests/test-aevatar-doc-update.py -v
bash scripts/tests/test-doc-checks.sh all
.superpowers/aevatar-doc-update/skill-validator-venv/bin/python \
  /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/updating-aevatar-review-docs
FROZEN_SHA="$(python3 -c 'import json; print(json.load(open(".config/aevatar-doc-update/state.json"))["frozen_upstream_sha"])')"
FROZEN_VERIFIED_AT="$(python3 -c 'import json; print(json.load(open(".config/aevatar-doc-update/state.json"))["frozen_verified_at"])')"
AEVATAR_SRC="$(bash scripts/materialize-frozen-upstream.sh --repo ~/Code/aevatar --sha "$FROZEN_SHA")" \
  AEVATAR_SRC2="$HOME/Code/aevatar" EXPECTED_UPSTREAM_COMMIT="$FROZEN_SHA" \
  EXPECTED_VERIFIED_AT="$FROZEN_VERIFIED_AT" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
python3 scripts/check-site-ui.py
```

Expected: every command exits `0`. The current book is still validated at its committed old baseline; the dry-run target is evidence only.

- [ ] **Step 5: Request an independent code/contract review**

Use `superpowers:requesting-code-review`. The reviewer reads the design spec, this plan, owned diffs, Python tests, `SKILL.md`, state transition, pre-push, and workflow. It must explicitly check upstream immutability, state fail-closed behavior, issue ambiguity, review independence, trigger discovery, and preservation of unrelated `AGENTS.md` edits. Fix blocking findings and rerun the narrowest affected test plus all final gates.

- [ ] **Step 6: Inspect the final boundary**

```bash
git status --short --branch
git diff --check
base="$(cat .superpowers/aevatar-doc-update/implementation-base)"
git diff --stat "$base"..HEAD
git status --short -- AGENTS.md .reasonix .superpowers
```

Expected: only unrelated `.reasonix/` and `.superpowers/` content remains outside owned commits; no file under `~/Code/aevatar` changed; no actual documentation baseline or review count advanced during implementation.
