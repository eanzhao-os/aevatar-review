from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/skills/updating-aevatar-review-docs/scripts/prepare-update.py"
spec = importlib.util.spec_from_file_location("prepare_update", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)


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

    def test_atomic_json_replaces_target_without_temp_residue(self):
        target = self.root / "nested/state.json"
        MODULE.atomic_json(target, {"value": "first"})
        MODULE.atomic_json(target, {"value": "second"})
        self.assertEqual(json.loads(target.read_text()), {"value": "second"})
        self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])


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
        return self.root / f"{prefix}-{self.counter}.json"

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
        sample_size: int = 2,
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
        return self.cli(*args), output

    def select_review(self, facts: dict, changed: list[str], issues=None, sample_size=2) -> dict:
        result, output = self.select_review_result(facts, changed, issues, sample_size)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(output.read_text())

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
        reviewed = facts["semantic_changed_chapters"] + facts["review_sample"]
        return self.commit_state(facts, True, reviewed)

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

    def test_commit_state_requires_gates_exact_scope_and_state_hash(self):
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


if __name__ == "__main__":
    unittest.main()
