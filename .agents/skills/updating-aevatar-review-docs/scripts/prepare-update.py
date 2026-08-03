#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

SHA_RE = re.compile(r"[0-9a-f]{40}")
CHAPTER_RE = re.compile(r"(?:0[0-9]|1[0-3])/[0-9]{2}-[a-z0-9-]+\.md")
ROW_RE = re.compile(
    r"^- \[x\] \[([^]]+)\]\(([^)]+)\).+"
    r"\[issue\]\((https://github\.com/[^/]+/[^/]+/issues/[0-9]+)\)\s*$"
)
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
STATE_KEYS = {
    "schema_version", "frozen_upstream_sha", "frozen_verified_at",
    "synced_upstream_sha", "last_successful_update_at", "chapters",
}
CHAPTER_KEYS = {"review_count", "last_reviewed_sha", "last_reviewed_at", "result"}


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_sha(value: object) -> bool:
    return isinstance(value, str) and SHA_RE.fullmatch(value) is not None


def valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or UTC_RE.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def chapter_rows(plan: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    issues: set[str] = set()
    for line in plan.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- [x]"):
            continue
        match = ROW_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"malformed checked chapter row: {line}")
        label, target, issue = match.groups()
        if label != target or not CHAPTER_RE.fullmatch(label) or label.endswith("/index.md"):
            raise ValueError(f"invalid chapter path: {label}")
        if label in rows or issue in issues:
            raise ValueError(f"duplicate chapter path or issue: {label}")
        rows[label] = issue
        issues.add(issue)
    if not rows:
        raise ValueError("plan has no checked substantive chapter rows")
    return rows


def load_state(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != STATE_KEYS:
        raise ValueError("invalid state fields")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("invalid schema_version")
    if not valid_sha(value["frozen_upstream_sha"]):
        raise ValueError("invalid frozen_upstream_sha")
    if not valid_date(value["frozen_verified_at"]):
        raise ValueError("invalid frozen_verified_at")
    if not valid_sha(value["synced_upstream_sha"]):
        raise ValueError("invalid synced_upstream_sha")
    if value["last_successful_update_at"] is not None and not valid_timestamp(
        value["last_successful_update_at"]
    ):
        raise ValueError("invalid last_successful_update_at")
    chapters = value["chapters"]
    if not isinstance(chapters, dict):
        raise ValueError("invalid chapters")
    for chapter, record in chapters.items():
        if not isinstance(chapter, str) or not CHAPTER_RE.fullmatch(chapter):
            raise ValueError(f"invalid chapter path: {chapter}")
        if not isinstance(record, dict) or set(record) != CHAPTER_KEYS:
            raise ValueError(f"invalid chapter record: {chapter}")
        count = record["review_count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError(f"invalid review_count: {chapter}")
        reviewed_sha = record["last_reviewed_sha"]
        if reviewed_sha is not None and not valid_sha(reviewed_sha):
            raise ValueError(f"invalid last_reviewed_sha: {chapter}")
        reviewed_at = record["last_reviewed_at"]
        if reviewed_at is not None and not valid_timestamp(reviewed_at):
            raise ValueError(f"invalid last_reviewed_at: {chapter}")
        if record["result"] not in (None, "pass"):
            raise ValueError(f"invalid result: {chapter}")
    return value


def stable_rank(seed: str, chapter: str) -> str:
    return hashlib.sha256(f"{seed}\0{chapter}".encode()).hexdigest()


def stable_sample(
    chapters: list[str], state: dict, excluded: set[str], size: int, seed: str
) -> list[str]:
    eligible = [p for p in chapters if p not in excluded and not p.endswith("/index.md")]
    return sorted(eligible, key=lambda path: (
        int(state.get("chapters", {}).get(path, {}).get("review_count", 0)),
        state.get("chapters", {}).get(path, {}).get("last_reviewed_at") or "",
        stable_rank(seed, path),
    ))[:max(0, size)]


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def init_state(state: Path, plan: Path, frozen_sha: str, frozen_verified_at: str) -> None:
    if state.exists():
        raise ValueError(f"state already exists: {state}")
    if not valid_sha(frozen_sha):
        raise ValueError("frozen SHA must be 40 lowercase hexadecimal characters")
    if not valid_date(frozen_verified_at):
        raise ValueError("frozen verified date must be YYYY-MM-DD")
    chapters = {
        chapter: {
            "review_count": 0,
            "last_reviewed_sha": None,
            "last_reviewed_at": None,
            "result": None,
        }
        for chapter in chapter_rows(plan)
    }
    atomic_json(state, {
        "schema_version": 1,
        "frozen_upstream_sha": frozen_sha,
        "frozen_verified_at": frozen_verified_at,
        "synced_upstream_sha": frozen_sha,
        "last_successful_update_at": None,
        "chapters": chapters,
    })


def main() -> int:
    parser = argparse.ArgumentParser(prog="prepare-update.py")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("init-state")
    command.add_argument("--state", required=True, type=Path)
    command.add_argument("--plan", required=True, type=Path)
    command.add_argument("--frozen-sha", required=True)
    command.add_argument("--frozen-verified-at", required=True)
    args = parser.parse_args()
    try:
        init_state(args.state, args.plan, args.frozen_sha, args.frozen_verified_at)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"prepare-update: ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
