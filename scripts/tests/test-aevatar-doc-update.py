from __future__ import annotations

import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
