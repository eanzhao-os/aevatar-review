from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from threading import BrokenBarrierError

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py"
spec = importlib.util.spec_from_file_location("prepare_update", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)


def concurrent_commit_worker(barrier, queue, args: tuple[object, ...]) -> None:
    real_atomic_json = MODULE.atomic_json

    def synchronized_atomic_json(path: Path, value: dict) -> None:
        try:
            barrier.wait(timeout=1)
        except BrokenBarrierError:
            pass
        real_atomic_json(path, value)

    MODULE.atomic_json = synchronized_atomic_json
    try:
        MODULE.commit_state(*args)
    except Exception as error:  # subprocess result is asserted by the parent
        queue.put(type(error).__name__)
    else:
        queue.put("ok")


def state_for(chapters: list[str], counts: list[int] | None = None) -> dict:
    counts = counts or [0] * len(chapters)
    return {"chapters": {
        path: {"review_count": count, "last_reviewed_at": None}
        for path, count in zip(chapters, counts)
    }}


class CliFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state = self.root / "state.json"
        self.plan = self.root / "PLAN.md"
        self.plan.write_text(
            "- [x] [01/01-one.md](01/01-one.md) — `current` — One — "
            "[issue](https://github.com/fix/review/issues/1)\n"
            "- [x] [01/02-two.md](01/02-two.md) — `mixed` — Two — "
            "[issue](https://github.com/fix/review/issues/2)\n",
            encoding="utf-8",
        )
        self.plan_with_mismatched_link = self.root / "bad-plan.md"
        self.plan_with_mismatched_link.write_text(
            self.plan.read_text().replace(
                "[01/02-two.md](01/02-two.md)",
                "[01/02-two.md](01/99-wrong.md)",
            ),
            encoding="utf-8",
        )
        self.chapters = [f"01/{number:02d}-chapter.md" for number in range(1, 9)]
        self.coverage_state = state_for(self.chapters, [0, 0, 0, 1, 1, 1, 2, 2])
        for index, date in zip((3, 4, 5), ("2026-07-01", "2026-07-02", "2026-07-03")):
            self.coverage_state["chapters"][self.chapters[index]]["last_reviewed_at"] = date
        self.excluded = {self.chapters[0]}

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def cli(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True, capture_output=True, cwd=self.root, check=False,
        )


class StateAndSamplingTests(CliFixture):
    def test_init_state_records_every_plan_chapter_at_zero(self):
        result = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", "a" * 40,
            "--frozen-verified-at", "2026-07-25",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(self.state.read_text())
        self.assertEqual(value["frozen_upstream_sha"], "a" * 40)
        self.assertEqual(value["synced_upstream_sha"], "a" * 40)
        self.assertIsNone(value["last_successful_update_at"])
        self.assertEqual(set(value["chapters"]), {"01/01-one.md", "01/02-two.md"})
        self.assertEqual({r["review_count"] for r in value["chapters"].values()}, {0})

    def test_init_state_refuses_existing_state(self):
        self.state.write_text("{}\n", encoding="utf-8")
        result = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", "a" * 40,
            "--frozen-verified-at", "2026-07-25",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.state.read_text(), "{}\n")

    def test_plan_rows_require_matching_paths_and_unique_issues(self):
        rows = MODULE.chapter_rows(self.plan)
        self.assertEqual(rows["01/01-one.md"], "https://github.com/fix/review/issues/1")
        with self.assertRaises(ValueError):
            MODULE.chapter_rows(self.plan_with_mismatched_link)

    def test_plan_rejects_row_with_multiple_github_issue_urls(self):
        path = self.root / "multiple-issues.md"
        path.write_text(
            self.plan.read_text(encoding="utf-8").replace(
                "One — [issue](https://github.com/fix/review/issues/1)",
                "One — [issue](https://github.com/fix/review/issues/2) — "
                "[issue](https://github.com/fix/review/issues/1)",
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            MODULE.chapter_rows(path)

    def test_sample_prefers_low_count_then_oldest_then_stable_hash(self):
        first = MODULE.stable_sample(self.chapters, self.coverage_state, self.excluded, 3, "b" * 40)
        second = MODULE.stable_sample(self.chapters, self.coverage_state, self.excluded, 3, "b" * 40)
        self.assertEqual(first, second)
        self.assertEqual(set(first[:2]), {self.chapters[1], self.chapters[2]})
        self.assertEqual(first[2], self.chapters[3])

    def test_sample_excludes_owned_and_index_paths(self):
        result = MODULE.stable_sample(
            ["00/index.md", "00/01-one.md", "00/02-two.md"],
            state_for(["00/index.md", "00/01-one.md", "00/02-two.md"]),
            {"00/01-one.md"}, 6, "a" * 40,
        )
        self.assertEqual(result, ["00/02-two.md"])

    def test_plan_rejects_empty_duplicate_path_and_duplicate_issue(self):
        rows = self.plan.read_text(encoding="utf-8")
        first = rows.splitlines(keepends=True)[0]
        cases = {
            "empty.md": "",
            "duplicate-path.md": rows + first,
            "duplicate-issue.md": rows.replace("issues/2", "issues/1"),
        }
        for name, content in cases.items():
            with self.subTest(name=name):
                path = self.root / name
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    MODULE.chapter_rows(path)

    def test_init_state_rejects_bad_sha_and_date_without_writing(self):
        for index, (sha, date) in enumerate((
            ("abc", "2026-07-25"),
            ("a" * 40, "2026-7-25"),
        )):
            state = self.root / f"invalid-{index}.json"
            result = self.cli(
                "init-state", "--state", state, "--plan", self.plan,
                "--frozen-sha", sha, "--frozen-verified-at", date,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(state.exists())

    def test_init_state_rejects_state_outside_plan_root(self):
        outside = Path(f"{self.root}-outside-state.json")
        try:
            result = self.cli(
                "init-state", "--state", outside, "--plan", self.plan,
                "--frozen-sha", "a" * 40,
                "--frozen-verified-at", "2026-07-25",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(outside.exists())
            self.assertFalse(outside.with_name(f".{outside.name}.lock").exists())
        finally:
            outside.unlink(missing_ok=True)
            outside.with_name(f".{outside.name}.lock").unlink(missing_ok=True)

    def test_load_state_rejects_malformed_chapter_record(self):
        result = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", "a" * 40,
            "--frozen-verified-at", "2026-07-25",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(self.state.read_text())
        value["chapters"]["01/01-one.md"]["review_count"] = -1
        self.state.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.load_state(self.state)

    def test_load_state_enforces_review_count_evidence_relationships(self):
        result = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", "a" * 40,
            "--frozen-verified-at", "2026-07-25",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        baseline = json.loads(self.state.read_text(encoding="utf-8"))
        invalid_records = [
            {
                "review_count": 999,
                "last_reviewed_sha": None,
                "last_reviewed_at": None,
                "result": None,
            },
            {
                "review_count": 0,
                "last_reviewed_sha": "b" * 40,
                "last_reviewed_at": "2026-08-03T00:00:00Z",
                "result": "pass",
            },
        ]
        for record in invalid_records:
            with self.subTest(record=record):
                value = copy.deepcopy(baseline)
                value["chapters"]["01/01-one.md"] = record
                self.state.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    MODULE.load_state(self.state)

    def test_state_json_rejects_top_level_and_nested_duplicate_keys(self):
        result = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", "a" * 40,
            "--frozen-verified-at", "2026-07-25",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        baseline = self.state.read_text(encoding="utf-8")
        cases = (
            baseline.replace(
                '  "schema_version": 1,',
                '  "schema_version": 1,\n  "schema_version": 1,',
                1,
            ),
            baseline.replace(
                '      "review_count": 0,',
                '      "review_count": 0,\n      "review_count": 0,',
                1,
            ),
        )
        for duplicate in cases:
            with self.subTest(duplicate=duplicate[:80]):
                self.state.write_text(duplicate, encoding="utf-8")
                with self.assertRaises(ValueError):
                    MODULE.load_state(self.state)

    def test_atomic_json_replaces_target_without_temp_residue(self):
        target = self.root / "nested/state.json"
        MODULE.atomic_json(target, {"value": "first"})
        MODULE.atomic_json(target, {"value": "second"})
        self.assertEqual(json.loads(target.read_text()), {"value": "second"})
        self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])

    def test_atomic_json_does_not_follow_preseeded_temp_symlink(self):
        target = self.root / "nested/state.json"
        target.parent.mkdir(parents=True)
        victim = self.root / "victim.txt"
        victim.write_text("do not overwrite\n", encoding="utf-8")
        planted = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        planted.symlink_to(victim)

        MODULE.atomic_json(target, {"value": "safe"})

        self.assertEqual(victim.read_text(encoding="utf-8"), "do not overwrite\n")
        self.assertFalse(target.is_symlink())
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"value": "safe"})

    def test_init_state_rejects_symlinked_lock_file(self):
        victim = self.root / "victim.lock"
        victim.write_text("not a lock\n", encoding="utf-8")
        lock = self.state.with_name(f".{self.state.name}.lock")
        lock.symlink_to(victim)

        result = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", "a" * 40,
            "--frozen-verified-at", "2026-07-25",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.state.exists())
        self.assertEqual(victim.read_text(encoding="utf-8"), "not a lock\n")

    def test_repository_path_rejects_intermediate_symlink_into_git(self):
        root = self.root / "review"
        metadata = root / ".git"
        metadata.mkdir(parents=True)
        (metadata / "secret").write_text("metadata\n", encoding="utf-8")
        (root / "alias").symlink_to(metadata, target_is_directory=True)

        with self.assertRaises(ValueError):
            MODULE.require_repository_path(root, root / "alias/secret", "test path")
        with self.assertRaises(ValueError):
            MODULE.safe_review_file(root, "alias/secret", "test path")

    def test_repository_paths_reject_every_intermediate_symlink(self):
        root = self.root / "review"
        safe = root / "safe"
        safe.mkdir(parents=True)
        (safe / "file.txt").write_text("safe\n", encoding="utf-8")
        (root / "alias").symlink_to(safe, target_is_directory=True)

        with self.assertRaises(ValueError):
            MODULE.require_repository_path(root, root / "alias/file.txt", "test path")
        with self.assertRaises(ValueError):
            MODULE.safe_review_file(root, "alias/file.txt", "test path")

    def test_architecture_candidates_cover_the_approved_design_surface(self):
        snapshot = self.root / "snapshot"
        review_root = self.root / "review"
        chapter = "01/01-one.md"
        (review_root / chapter).parent.mkdir(parents=True)
        (review_root / chapter).write_text("# chapter\n", encoding="utf-8")
        cases = {
            "aevatar.sln": "project",
            "src/App/App.csproj": "project",
            "src/App/AppHost.cs": "component",
            "src/App/ChatAgent.cs": "component",
            "src/App/ChatGAgent.cs": "component",
            "src/App/ActorRuntime.cs": "component",
            "src/App/chat.proto": "protocol",
            "src/App/PublicContract.cs": "component",
            "src/App/StatusEndpoint.cs": "component",
            "src/App/SearchToolProvider.cs": "component",
            "src/App/SlackConnector.cs": "component",
            "src/App/WorkflowPrimitive.cs": "component",
            "src/App/MessagePersistence.cs": "component",
            "src/App/DocumentDatabase.cs": "component",
            "src/App/EventStore.cs": "component",
            "src/App/EventProjection.cs": "component",
            "src/App/AuthorizationService.cs": "component",
            "src/App/AuthenticationService.cs": "component",
            "src/Public/Contracts/Message.cs": "component",
            "src/ToolProviders/Search.cs": "component",
            "src/Workflow/Nodes/Sequence.cs": "component",
            "src/Persistence/Message.cs": "component",
            "src/Projections/ReadModel.cs": "component",
            "src/App/appsettings.Production.json": "configuration",
            "deploy/k8s/deployment.yaml": "topology",
            "deploy/runtime-topology.yml": "topology",
            "charts/aevatar/values.yaml": "topology",
            "docs/canon/runtime/nested-design.md": "design",
            "docs/adr/workflow/0001-decision.md": "design",
        }
        for path in cases:
            target = snapshot / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture\n", encoding="utf-8")

        candidates = MODULE.architecture_candidates(snapshot, review_root, [chapter], {})
        self.assertEqual(
            {item["path"]: item["kind"] for item in candidates},
            cases,
        )


class GitPrepareTests(CliFixture):
    def setUp(self) -> None:
        super().setUp()
        self.origin = self.root / "origin.git"
        self.upstream = self.root / "upstream"
        self.publisher = self.root / "publisher"
        self.review_root = self.root / "review"
        self.plan = self.review_root / "PLAN.md"
        self.state = self.review_root / ".config/aevatar-doc-update/state.json"
        self.source_map = self.review_root / ".config/upstream-sync/chapter-source-map.json"
        self.snapshot_root = self.root / "snapshots"
        self.snapshot_script = ROOT / "scripts/materialize-frozen-upstream.sh"
        self.counter = 0

        self.run_command("git", "init", "-q", "--bare", self.origin)
        self.run_command("git", "init", "-q", self.upstream)
        self.git("config", "user.name", "fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", self.origin)
        self.git("switch", "-q", "-c", "feature/integrate")
        self.write(self.upstream / "aevatar.slnx", "<Solution />\n")
        self.write(self.upstream / "src/Mapped/Existing.cs", "old\n")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")
        self.git("push", "-q", "-u", "origin", "feature/integrate")
        self.synced_sha = self.git("rev-parse", "HEAD")

        self.review_root.mkdir()
        chapter_rows = [
            ("01/01-existing.md", 1),
            ("01/02-old.md", 2),
            ("01/03-user-owned.md", 3),
            ("01/04-old.md", 4),
        ]
        for chapter, _ in chapter_rows:
            self.write(self.review_root / chapter, f"# {chapter}\n")
        self.plan.write_text("".join(
            f"- [x] [{chapter}]({chapter}) — `current` — Chapter — "
            f"[issue](https://github.com/fix/review/issues/{issue})\n"
            for chapter, issue in chapter_rows
        ), encoding="utf-8")
        self.write(self.source_map, json.dumps({
            "version": 2,
            "alias_expansion": {"canon": {}},
            "chapters": {"01/01-existing.md": ["src/Mapped/Existing.cs"]},
        }))
        initialized = self.cli(
            "init-state", "--state", self.state, "--plan", self.plan,
            "--frozen-sha", self.synced_sha,
            "--frozen-verified-at", "2026-07-25",
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        self.initial_state = self.state.read_bytes()
        self.write(self.review_root / "mkdocs.yml", "site_name: fixture\n")
        self.run_command("git", "init", "-q", "-b", "main", self.review_root)
        self.run_command("git", "config", "user.name", "fixture", cwd=self.review_root)
        self.run_command(
            "git", "config", "user.email", "fixture@example.invalid", cwd=self.review_root
        )
        self.run_command(
            "git", "add", "--", "PLAN.md", "01", ".config", "mkdocs.yml",
            cwd=self.review_root,
        )
        self.run_command("git", "commit", "-qm", "baseline", cwd=self.review_root)

        self.git("switch", "-q", "-c", "topic/dirty")
        self.write(self.upstream / "src/Mapped/Existing.cs", "old\ndirty\n")
        self.write(self.upstream / "local-only.txt", "untracked\n")
        self.run_command("git", "clone", "-q", "--branch", "feature/integrate", self.origin, self.publisher)
        self.run_command("git", "config", "user.name", "fixture", cwd=self.publisher)
        self.run_command("git", "config", "user.email", "fixture@example.invalid", cwd=self.publisher)
        self.write(self.publisher / "src/Mapped/Existing.cs", "old\nnew\n")
        self.write(self.publisher / "src/NewBoundary/NewBoundary.csproj", "<Project />\n")
        self.write(self.publisher / "src/NewBoundary/new_contract.proto", 'syntax = "proto3";\n')
        self.run_command("git", "add", "src", cwd=self.publisher)
        self.run_command("git", "commit", "-qm", "test: reveal protocol boundary", cwd=self.publisher)
        self.run_command("git", "push", "-q", "origin", "feature/integrate", cwd=self.publisher)
        self.remote_integrate_sha = self.run_command("git", "rev-parse", "HEAD", cwd=self.publisher)

    def write(self, path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def run_command(self, *args: object, cwd: Path | None = None) -> str:
        result = subprocess.run(
            [*map(str, args)], cwd=cwd, text=True, capture_output=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result.stdout.strip()

    def git(self, *args: object) -> str:
        return self.run_command("git", *args, cwd=self.upstream)

    def facts_path(self, prefix: str) -> Path:
        self.counter += 1
        directory = self.review_root / ".superpowers/test-facts"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{prefix}-{self.counter}.json"

    def write_facts(self, prefix: str, facts: dict) -> Path:
        path = self.facts_path(prefix)
        path.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def prepare_result(self, mode: str, topic: str | None = None):
        output = self.facts_path("prepared")
        args: list[object] = [
            "prepare", "--mode", mode,
            "--review-root", self.review_root,
            "--upstream-repo", self.upstream,
            "--state", self.state,
            "--map", self.source_map,
            "--snapshot-script", self.snapshot_script,
            "--snapshot-root", self.snapshot_root,
            "--branch", "feature/integrate",
            "--exclude-chapter", "01/03-user-owned.md",
            "--output", output,
        ]
        if topic is not None:
            args.extend(("--topic", topic))
        return self.cli(*args), output

    def prepare(self, mode: str, topic: str | None = None) -> dict:
        result, output = self.prepare_result(mode, topic)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(output.read_text())

    def select_review_result(
        self, facts: dict, changed: list[str], issues: list[str] | None = None,
        sample_size: int = 2, structural: list[str] | None = None,
    ):
        source, output = self.write_facts("input", facts), self.facts_path("selected")
        args: list[object] = [
            "select-review", "--state", self.state, "--plan", self.plan,
            "--facts", source, "--sample-size", sample_size, "--output", output,
        ]
        for path in changed:
            args.extend(("--changed-chapter", path))
        for issue in issues or []:
            args.extend(("--new-chapter-issue", issue))
        for path in structural or []:
            args.extend(("--structural-path", path))
        return self.cli(*args), output

    def select_review(
        self, facts: dict, changed: list[str], issues=None, sample_size=2,
        structural: list[str] | None = None,
    ) -> dict:
        result, output = self.select_review_result(
            facts, changed, issues, sample_size, structural
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(output.read_text())

    def valid_reviewer_evidence(self, facts: dict) -> dict:
        return {
            "schema_version": 1,
            "facts_sha256": facts["facts_sha256"],
            "reviewer": {
                "task_id": "fixture-review-1",
                "model": "fixture-reviewer-model",
                "fresh_context": True,
                "read_only": True,
                "independent": True,
            },
            "results": {path: "pass" for path in sorted(facts["sealed_files"])},
            "blocking_findings": [],
        }

    def valid_gate_evidence(self, facts: dict) -> dict:
        return {
            "schema_version": 1,
            "facts_sha256": facts["facts_sha256"],
            "gates": [
                {"name": name, "exit_code": 0}
                for name in (
                    "check-md", "check-links", "check-drift", "check-mermaid", "mkdocs"
                )
            ],
        }

    def write_evidence(self, prefix: str, value: dict) -> Path:
        path = self.review_root / ".superpowers/evidence" / f"{prefix}-{self.counter}.json"
        self.counter += 1
        self.write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        return path

    def commit_state_evidence(
        self, facts: dict, reviewer: dict | None = None, gates: dict | None = None,
    ) -> subprocess.CompletedProcess[str]:
        source = self.write_facts("commit-evidence", facts)
        review_path = self.write_evidence(
            "reviewer", reviewer if reviewer is not None else self.valid_reviewer_evidence(facts)
        )
        gate_path = self.write_evidence(
            "gates", gates if gates is not None else self.valid_gate_evidence(facts)
        )
        return self.cli(
            "commit-state", "--state", self.state, "--plan", self.plan,
            "--facts", source, "--completed-at", "2026-08-03T00:00:00Z",
            "--review-evidence", review_path, "--gate-evidence", gate_path,
        )

    def commit_state(self, facts: dict, gates: bool, reviewed: list[str]):
        source = self.write_facts("commit", facts)
        args: list[object] = [
            "commit-state", "--state", self.state, "--plan", self.plan,
            "--facts", source, "--completed-at", "2026-08-03T00:00:00Z",
        ]
        if gates:
            args.append("--gates-passed")
        for path in reviewed:
            args.extend(("--reviewed-chapter", path))
        return self.cli(*args)

    def selected_facts(self, mode: str, topic: str | None = None) -> dict:
        return self.select_review(
            self.prepare(mode, topic), changed=["01/01-existing.md"], sample_size=2
        )

    def commit_selected(self, facts: dict):
        return self.commit_state_evidence(facts)

    def reset_state(self) -> None:
        self.state.write_bytes(self.initial_state)

    def add_plan_chapter(self, chapter: str, issue_url: str) -> None:
        self.write(self.review_root / chapter, f"# {chapter}\n")
        issue_number = issue_url.rsplit("/", 1)[-1]
        with self.plan.open("a", encoding="utf-8") as handle:
            handle.write(
                f"- [x] [{chapter}]({chapter}) — `current` — New — "
                f"[issue](https://github.com/fix/review/issues/{issue_number})\n"
            )

    def force_rewrite_remote_integrate(self) -> None:
        self.run_command("git", "checkout", "-q", "--orphan", "rewritten", cwd=self.publisher)
        self.run_command("git", "rm", "-qrf", ".", cwd=self.publisher)
        self.write(self.publisher / "aevatar.slnx", "<Solution />\n")
        self.write(self.publisher / "src/Rewritten.cs", "new root\n")
        self.run_command("git", "add", ".", cwd=self.publisher)
        self.run_command("git", "commit", "-qm", "rewrite", cwd=self.publisher)
        self.run_command("git", "push", "-q", "--force", "origin", "HEAD:feature/integrate", cwd=self.publisher)

    def test_prepare_fetches_without_touching_upstream_head_status_or_index(self):
        before_head = self.git("rev-parse", "HEAD")
        before_status = self.git("status", "--porcelain=v1")
        index = Path(self.git("rev-parse", "--git-path", "index"))
        if not index.is_absolute():
            index = self.upstream / index
        before_index = index.read_bytes() if index.exists() else None
        tracked = self.upstream / "aevatar.slnx"
        stat = tracked.stat()
        os.utime(tracked, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
        facts = self.prepare(mode="full")
        after_index = index.read_bytes() if index.exists() else None
        self.assertTrue(after_index == before_index, "prepare changed upstream index bytes")
        self.assertEqual(self.git("rev-parse", "HEAD"), before_head)
        self.assertEqual(self.git("status", "--porcelain=v1"), before_status)
        self.assertEqual(facts["target_sha"], self.remote_integrate_sha)
        self.assertTrue(Path(facts["target_snapshot_path"], "aevatar.slnx").is_file())

    def test_prepare_keeps_all_commits_and_unmapped_architecture(self):
        facts = self.prepare(mode="full")
        self.assertIn("test: reveal protocol boundary", [r["subject"] for r in facts["commits"]])
        self.assertIn("01/01-existing.md", facts["chapter_hits"])
        self.assertIn("src/NewBoundary/NewBoundary.csproj", facts["unmapped_changed_files"])
        self.assertIn("src/NewBoundary/new_contract.proto", {r["path"] for r in facts["architecture_candidates"]})

    def test_topic_mode_records_topic_but_keeps_complete_mechanical_evidence(self):
        before = self.state.read_bytes()
        facts = self.prepare(mode="topic", topic="NewBoundary")
        self.assertEqual((facts["mode"], facts["topic"]), ("topic", "NewBoundary"))
        self.assertTrue(facts["commits"])
        self.assertEqual(self.state.read_bytes(), before)

    def test_prepare_reports_history_rewrite_from_tree_diff(self):
        self.force_rewrite_remote_integrate()
        facts = self.prepare(mode="full")
        self.assertTrue(facts["history_rewrite"])
        self.assertTrue(any(r["path"] == "src/Rewritten.cs" for r in facts["changes"]))

    def test_select_review_excludes_semantic_and_protected_paths(self):
        facts = self.select_review(
            self.prepare(mode="full"), changed=["01/01-existing.md"], sample_size=6
        )
        self.assertNotIn("01/01-existing.md", facts["review_sample"])
        self.assertNotIn("01/03-user-owned.md", facts["review_sample"])

    def test_select_review_rejects_sample_size_above_six_without_output(self):
        result, output = self.select_review_result(
            self.prepare(mode="full"), changed=["01/01-existing.md"], sample_size=7
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_select_review_requires_exact_issue_for_each_new_chapter(self):
        self.add_plan_chapter("01/02-new.md", "https://github.com/fix/review/issues/42")
        missing, _ = self.select_review_result(
            self.prepare(mode="full"), changed=["01/02-new.md"]
        )
        self.assertNotEqual(missing.returncode, 0)
        facts = self.select_review(
            self.prepare(mode="full"), changed=["01/02-new.md"],
            issues=["01/02-new.md=https://github.com/fix/review/issues/42"],
        )
        self.assertEqual(facts["new_chapter_issues"], {
            "01/02-new.md": "https://github.com/fix/review/issues/42"
        })

    def test_select_review_seals_all_reviewed_files_and_changed_structural_paths(self):
        prepared = self.prepare(mode="full")
        self.write(self.review_root / "mkdocs.yml", "site_name: changed\n")
        facts = self.select_review(
            prepared, changed=["01/01-existing.md"], structural=["mkdocs.yml"]
        )
        expected_paths = {
            "01/01-existing.md", "mkdocs.yml", *facts["review_sample"],
        }
        self.assertEqual(facts["structural_semantic_paths"], ["mkdocs.yml"])
        self.assertEqual(set(facts["sealed_files"]), expected_paths)
        self.assertEqual(facts["sealed_files"], {
            path: hashlib.sha256((self.review_root / path).read_bytes()).hexdigest()
            for path in sorted(expected_paths)
        })

        unchanged, output = self.select_review_result(
            prepared, changed=["01/01-existing.md"], structural=["PLAN.md"]
        )
        self.assertNotEqual(unchanged.returncode, 0)
        self.assertFalse(output.exists())

    def test_commit_state_requires_bound_evidence_and_current_sealed_bytes(self):
        facts = self.selected_facts(mode="full")
        self.assertEqual(self.commit_state_evidence(facts).returncode, 0)

        self.reset_state()
        before = self.state.read_bytes()
        self.write(self.review_root / "01/01-existing.md", "# edited after review\n")
        changed = self.commit_state_evidence(facts)
        self.assertNotEqual(changed.returncode, 0)
        self.assertEqual(self.state.read_bytes(), before)

    def test_commit_state_rejects_invalid_reviewer_and_gate_evidence(self):
        facts = self.selected_facts(mode="full")
        reviewer = self.valid_reviewer_evidence(facts)
        gates = self.valid_gate_evidence(facts)
        cases: list[tuple[str, dict, dict]] = []

        invalid = copy.deepcopy(reviewer)
        invalid["schema_version"] = True
        cases.append(("reviewer-schema-boolean", invalid, gates))
        for field in ("fresh_context", "read_only", "independent"):
            invalid = copy.deepcopy(reviewer)
            invalid["reviewer"][field] = False
            cases.append((f"reviewer-{field}", invalid, gates))
        invalid = copy.deepcopy(reviewer)
        invalid["reviewer"]["model"] = ""
        cases.append(("reviewer-model", invalid, gates))
        invalid = copy.deepcopy(reviewer)
        invalid["results"].pop(next(iter(invalid["results"])))
        cases.append(("reviewer-coverage", invalid, gates))
        invalid = copy.deepcopy(reviewer)
        invalid["blocking_findings"] = ["unresolved"]
        cases.append(("reviewer-blocking", invalid, gates))
        invalid = copy.deepcopy(reviewer)
        invalid["facts_sha256"] = "0" * 64
        cases.append(("reviewer-facts", invalid, gates))

        invalid_gates = copy.deepcopy(gates)
        invalid_gates["schema_version"] = True
        cases.append(("gate-schema-boolean", reviewer, invalid_gates))
        invalid_gates = copy.deepcopy(gates)
        invalid_gates["gates"].pop()
        cases.append(("gate-missing", reviewer, invalid_gates))
        invalid_gates = copy.deepcopy(gates)
        invalid_gates["gates"].append(copy.deepcopy(invalid_gates["gates"][0]))
        cases.append(("gate-duplicate", reviewer, invalid_gates))
        invalid_gates = copy.deepcopy(gates)
        invalid_gates["gates"][0]["exit_code"] = "0"
        cases.append(("gate-non-integer", reviewer, invalid_gates))
        invalid_gates = copy.deepcopy(gates)
        invalid_gates["gates"][0]["exit_code"] = 1
        cases.append(("gate-failed", reviewer, invalid_gates))
        invalid_gates = copy.deepcopy(gates)
        invalid_gates["facts_sha256"] = "0" * 64
        cases.append(("gate-facts", reviewer, invalid_gates))

        before = self.state.read_bytes()
        for name, review_value, gate_value in cases:
            with self.subTest(name=name):
                result = self.commit_state_evidence(facts, review_value, gate_value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.state.read_bytes(), before)

    def test_commit_state_rejects_evidence_inside_git_metadata(self):
        facts = self.selected_facts(mode="full")
        source = self.write_facts("git-evidence", facts)
        reviewer = self.review_root / ".git/reviewer-evidence.json"
        gates = self.review_root / ".git/gate-evidence.json"
        self.write(
            reviewer,
            json.dumps(self.valid_reviewer_evidence(facts), ensure_ascii=False) + "\n",
        )
        self.write(gates, json.dumps(self.valid_gate_evidence(facts)) + "\n")
        result = self.cli(
            "commit-state", "--state", self.state, "--plan", self.plan,
            "--facts", source, "--completed-at", "2026-08-03T00:00:00Z",
            "--review-evidence", reviewer, "--gate-evidence", gates,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.state.read_bytes(), self.initial_state)

    def test_commit_state_rejects_evidence_through_intermediate_symlink(self):
        facts = self.selected_facts(mode="full")
        source = self.write_facts("symlink-evidence", facts)
        evidence = self.review_root / ".superpowers/evidence"
        alias = self.review_root / "evidence-alias"
        alias.symlink_to(evidence, target_is_directory=True)
        reviewer = alias / "reviewer.json"
        gates = alias / "gates.json"
        self.write(
            evidence / "reviewer.json",
            json.dumps(self.valid_reviewer_evidence(facts), ensure_ascii=False) + "\n",
        )
        self.write(
            evidence / "gates.json",
            json.dumps(self.valid_gate_evidence(facts), ensure_ascii=False) + "\n",
        )

        result = self.cli(
            "commit-state", "--state", self.state, "--plan", self.plan,
            "--facts", source, "--completed-at", "2026-08-03T00:00:00Z",
            "--review-evidence", reviewer, "--gate-evidence", gates,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.state.read_bytes(), self.initial_state)

    def test_concurrent_state_commits_cannot_both_succeed(self):
        facts = self.selected_facts(mode="full")
        source = self.write_facts("concurrent", facts)
        reviewer = self.write_evidence("reviewer", self.valid_reviewer_evidence(facts))
        gates = self.write_evidence("gates", self.valid_gate_evidence(facts))
        args = (
            self.state, self.plan, source, "2026-08-03T00:00:00Z", reviewer, gates,
        )
        context = multiprocessing.get_context("fork")
        barrier = context.Barrier(2)
        queue = context.Queue()
        processes = [
            context.Process(target=concurrent_commit_worker, args=(barrier, queue, args))
            for _ in range(2)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)

        self.assertEqual(sorted(queue.get(timeout=1) for _ in processes), ["ValueError", "ok"])
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertTrue(all(
            state["chapters"][path]["review_count"] == 1
            for path in facts["review_sample"]
        ))

    def test_commit_state_rejects_boolean_and_path_only_interface(self):
        facts = self.selected_facts(mode="full")
        reviewed = facts["semantic_changed_chapters"] + facts["review_sample"]
        before = self.state.read_bytes()
        self.assertNotEqual(self.commit_state(facts, False, reviewed).returncode, 0)
        self.assertNotEqual(self.commit_state(facts, True, reviewed[:-1]).returncode, 0)
        self.assertEqual(self.state.read_bytes(), before)

    def test_full_advances_watermark_while_topic_never_does(self):
        full = self.selected_facts(mode="full")
        self.assertEqual(self.commit_selected(full).returncode, 0)
        full_state = json.loads(self.state.read_text())
        self.assertEqual(full_state["synced_upstream_sha"], full["target_sha"])
        self.assertEqual(full_state["chapters"]["01/01-existing.md"]["review_count"], 0)
        self.assertTrue(all(
            full_state["chapters"][path]["review_count"] == 1
            for path in full["review_sample"]
        ))
        self.reset_state()
        topic = self.selected_facts(mode="topic", topic="NewBoundary")
        self.assertEqual(self.commit_selected(topic).returncode, 0)
        self.assertEqual(json.loads(self.state.read_text())["synced_upstream_sha"], self.synced_sha)

    def test_mode_and_topic_must_match(self):
        full_with_topic, _ = self.prepare_result("full", "unexpected")
        topic_without_topic, _ = self.prepare_result("topic")
        self.assertNotEqual(full_with_topic.returncode, 0)
        self.assertNotEqual(topic_without_topic.returncode, 0)

    def test_prepare_rejects_missing_synced_object(self):
        value = json.loads(self.state.read_text())
        value["synced_upstream_sha"] = "c" * 40
        self.state.write_text(json.dumps(value) + "\n", encoding="utf-8")
        result, _ = self.prepare_result("full")
        self.assertNotEqual(result.returncode, 0)

    def test_select_review_rejects_duplicate_and_non_plan_changes(self):
        prepared = self.prepare(mode="full")
        duplicate, _ = self.select_review_result(
            prepared, changed=["01/01-existing.md", "01/01-existing.md"]
        )
        outside, _ = self.select_review_result(
            prepared, changed=["99/99-not-planned.md"]
        )
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertNotEqual(outside.returncode, 0)

    def test_select_review_rejects_unexpected_issue_entry(self):
        result, _ = self.select_review_result(
            self.prepare(mode="full"),
            changed=["01/01-existing.md"],
            issues=["01/01-existing.md=https://github.com/fix/review/issues/1"],
        )
        self.assertNotEqual(result.returncode, 0)

    def test_tampered_facts_and_changed_state_hash_fail_closed(self):
        prepared = self.prepare(mode="full")
        tampered = dict(prepared)
        tampered["target_sha"] = "d" * 40
        result, _ = self.select_review_result(
            tampered, changed=["01/01-existing.md"]
        )
        self.assertNotEqual(result.returncode, 0)

        self.state.write_bytes(self.state.read_bytes() + b" ")
        result, _ = self.select_review_result(
            prepared, changed=["01/01-existing.md"]
        )
        self.assertNotEqual(result.returncode, 0)

    def test_facts_and_source_map_reject_duplicate_json_keys(self):
        prepared = self.prepare(mode="full")
        facts_path = self.write_facts("duplicate-facts", prepared)
        facts_text = facts_path.read_text(encoding="utf-8").replace(
            '  "mode": "full",',
            '  "mode": "full",\n  "mode": "full",',
            1,
        )
        facts_path.write_text(facts_text, encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.load_facts(facts_path)

        self.source_map.write_text(
            '{"version":2,"alias_expansion":{"canon":{}},'
            '"chapters":{"01/01-existing.md":["src/Mapped/Existing.cs"],'
            '"01/01-existing.md":["src/Mapped/Existing.cs"]}}\n',
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            MODULE.load_source_map(self.source_map)

    def test_prepare_rejects_facts_output_in_git_before_fetch(self):
        before = self.git("rev-parse", "refs/remotes/origin/feature/integrate")
        output = self.review_root / ".git/prepared.json"
        result = self.cli(
            "prepare", "--mode", "full",
            "--review-root", self.review_root,
            "--upstream-repo", self.upstream,
            "--state", self.state,
            "--map", self.source_map,
            "--snapshot-script", self.snapshot_script,
            "--snapshot-root", self.snapshot_root,
            "--branch", "feature/integrate",
            "--exclude-chapter", "01/03-user-owned.md",
            "--output", output,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            self.git("rev-parse", "refs/remotes/origin/feature/integrate"), before
        )
        self.assertFalse(output.exists())

    def test_commit_rejects_bad_snapshot_marker(self):
        facts = self.selected_facts(mode="full")
        marker = Path(facts["target_snapshot_path"], ".source-commit")
        marker.write_text("e" * 40 + "\n", encoding="utf-8")
        self.assertNotEqual(self.commit_selected(facts).returncode, 0)

    def test_same_target_can_record_review_without_moving_frozen_fields(self):
        value = json.loads(self.state.read_text())
        value["synced_upstream_sha"] = self.remote_integrate_sha
        self.state.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        facts = self.selected_facts(mode="full")
        self.assertEqual(facts["target_sha"], self.remote_integrate_sha)
        self.assertEqual(self.commit_selected(facts).returncode, 0)
        after = json.loads(self.state.read_text())
        self.assertEqual(after["frozen_upstream_sha"], self.synced_sha)
        self.assertEqual(after["frozen_verified_at"], "2026-07-25")
        self.assertEqual(after["synced_upstream_sha"], self.remote_integrate_sha)

    def test_history_rewrite_cannot_auto_commit(self):
        self.force_rewrite_remote_integrate()
        facts = self.select_review(
            self.prepare(mode="full"), changed=[], sample_size=2
        )
        self.assertNotEqual(self.commit_selected(facts).returncode, 0)

    def test_prepare_rejects_duplicate_exclusions_before_fetch(self):
        before = self.git("rev-parse", "refs/remotes/origin/feature/integrate")
        output = self.facts_path("duplicate-exclusion")
        result = self.cli(
            "prepare", "--mode", "full",
            "--review-root", self.review_root,
            "--upstream-repo", self.upstream,
            "--state", self.state,
            "--map", self.source_map,
            "--snapshot-script", self.snapshot_script,
            "--snapshot-root", self.snapshot_root,
            "--branch", "feature/integrate",
            "--exclude-chapter", "01/03-user-owned.md",
            "--exclude-chapter", "01/03-user-owned.md",
            "--output", output,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            self.git("rev-parse", "refs/remotes/origin/feature/integrate"), before
        )
        self.assertFalse(output.exists())

    def test_prepare_rejects_inactive_source_map_owner_before_fetch(self):
        self.write(self.source_map, json.dumps({
            "version": 2,
            "alias_expansion": {"canon": {}},
            "chapters": {"01/99-inactive.md": ["src/Mapped/Existing.cs"]},
        }))
        before_ref = self.git("rev-parse", "refs/remotes/origin/feature/integrate")
        before_state = self.state.read_bytes()
        result, output = self.prepare_result("full")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            self.git("rev-parse", "refs/remotes/origin/feature/integrate"), before_ref
        )
        self.assertEqual(self.state.read_bytes(), before_state)
        self.assertFalse(output.exists())

    def test_prepare_rejects_missing_frozen_object(self):
        value = json.loads(self.state.read_text())
        value["frozen_upstream_sha"] = "f" * 40
        self.state.write_text(json.dumps(value) + "\n", encoding="utf-8")
        result, _ = self.prepare_result("full")
        self.assertNotEqual(result.returncode, 0)

    def test_source_map_aliases_and_unsafe_paths(self):
        self.write(self.source_map, json.dumps({
            "version": 2,
            "alias_expansion": {"canon": {
                "chat-api": "docs/canon/chat-api.md"
            }},
            "chapters": {
                "01/01-existing.md": {
                    "paths": ["chat-api", "0034-workflow-saga-compensation-protocol"]
                }
            },
        }))
        self.write(self.publisher / "docs/canon/chat-api.md", "# Chat API\n")
        self.write(
            self.publisher / "docs/adr/0034-workflow-saga-compensation-protocol.md",
            "# Saga\n",
        )
        self.run_command("git", "add", "docs", cwd=self.publisher)
        self.run_command("git", "commit", "-qm", "docs: update aliased design facts", cwd=self.publisher)
        self.run_command("git", "push", "-q", "origin", "feature/integrate", cwd=self.publisher)
        aliased = self.prepare(mode="full")
        self.assertIn("01/01-existing.md", aliased["chapter_hits"])

        self.write(self.source_map, json.dumps({
            "version": 2,
            "alias_expansion": {"canon": {}},
            "chapters": {"01/01-existing.md": ["../outside.cs"]},
        }))
        rejected, _ = self.prepare_result("full")
        self.assertNotEqual(rejected.returncode, 0)


class PublicationTests(CliFixture):
    def setUp(self) -> None:
        super().setUp()
        self.origin = self.root / "review-origin.git"
        self.review = self.root / "review"
        self.run_command("git", "init", "-q", "--bare", self.origin)
        self.run_command("git", "init", "-q", "-b", "main", self.review)
        self.run_command("git", "config", "user.name", "fixture", cwd=self.review)
        self.run_command(
            "git", "config", "user.email", "fixture@example.invalid", cwd=self.review
        )
        (self.review / "README.md").write_text("baseline\n", encoding="utf-8")
        self.run_command("git", "add", "README.md", cwd=self.review)
        self.run_command("git", "commit", "-qm", "baseline", cwd=self.review)
        self.run_command("git", "remote", "add", "origin", self.origin, cwd=self.review)
        self.run_command("git", "push", "-qu", "origin", "main", cwd=self.review)
        self.base = self.run_command("git", "rev-parse", "HEAD", cwd=self.review)

    def run_command(self, *args: object, cwd: Path | None = None) -> str:
        result = subprocess.run(
            [*map(str, args)], cwd=cwd, text=True, capture_output=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result.stdout.strip()

    def publication(self, phase: str, owned: list[str] | None = None):
        args: list[object] = [
            "verify-publication", "--review-root", self.review,
            "--base-sha", self.base, "--phase", phase,
        ]
        for path in owned or []:
            args.extend(("--owned-path", path))
        return self.cli(*args)

    def test_publication_rejects_concurrent_commit_and_accepts_one_owned_commit(self):
        self.assertEqual(self.publication("base").returncode, 0)

        (self.review / "unrelated.txt").write_text("concurrent\n", encoding="utf-8")
        self.run_command("git", "add", "unrelated.txt", cwd=self.review)
        self.run_command("git", "commit", "-qm", "concurrent local commit", cwd=self.review)
        self.assertNotEqual(self.publication("base").returncode, 0)
        (self.review / "owned.md").write_text("docs\n", encoding="utf-8")
        self.run_command("git", "add", "owned.md", cwd=self.review)
        self.run_command("git", "commit", "-qm", "docs: update", cwd=self.review)
        self.assertNotEqual(self.publication("commit", ["owned.md"]).returncode, 0)

        self.run_command("git", "reset", "--hard", self.base, cwd=self.review)
        (self.review / "owned.md").write_text("docs\n", encoding="utf-8")
        self.run_command("git", "add", "owned.md", cwd=self.review)
        self.run_command("git", "commit", "-qm", "docs: update", cwd=self.review)
        document_sha = self.run_command("git", "rev-parse", "HEAD", cwd=self.review)
        committed = self.publication("commit", ["owned.md"])
        ready = self.publication("push", ["owned.md"])
        self.assertEqual(committed.returncode, 0)
        self.assertEqual(ready.returncode, 0)
        self.assertEqual(committed.stdout.strip(), document_sha)
        self.assertEqual(ready.stdout.strip(), document_sha)

        publisher = self.root / "publisher"
        self.run_command("git", "clone", "-q", self.origin, publisher)
        self.run_command("git", "config", "user.name", "fixture", cwd=publisher)
        self.run_command(
            "git", "config", "user.email", "fixture@example.invalid", cwd=publisher
        )
        (publisher / "remote.txt").write_text("advanced\n", encoding="utf-8")
        self.run_command("git", "add", "remote.txt", cwd=publisher)
        self.run_command("git", "commit", "-qm", "remote advance", cwd=publisher)
        self.run_command("git", "push", "-q", "origin", "main", cwd=publisher)
        self.assertNotEqual(self.publication("push", ["owned.md"]).returncode, 0)

        self.run_command(
            "git", "push", "-q", "--force", "origin", f"{self.base}:main", cwd=publisher
        )
        ready = self.publication("push", ["owned.md"])
        self.assertEqual(ready.returncode, 0)
        (self.review / "late.txt").write_text("late local commit\n", encoding="utf-8")
        self.run_command("git", "add", "late.txt", cwd=self.review)
        self.run_command("git", "commit", "-qm", "late local commit", cwd=self.review)
        self.run_command(
            "git", "push", "-q", "origin", f"{ready.stdout.strip()}:main", cwd=self.review
        )
        remote_sha = self.run_command(
            "git", "ls-remote", "origin", "refs/heads/main", cwd=self.review
        ).split()[0]
        self.assertEqual(remote_sha, document_sha)


if __name__ == "__main__":
    unittest.main()
