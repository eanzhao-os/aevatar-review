#!/usr/bin/env python3
"""Resolve one exact-scope GitHub issue per target chapter, idempotently.

    python3 scripts/create_issues.py --manifest PATH --repo OWNER/REPO [--create]

    default: dry-run, no GitHub mutation
    --create: create only rows whose exact target path has no recorded issue
    output: CREATE|REUSE|RECORDED <path> <url-or-title>
    exit 0: every manifest row is resolved (or planned, in dry-run)
    exit 1: malformed manifest, duplicate path, gh failure, or unresolved row

Every chapter is one independent work unit. An issue therefore carries a
``scope_paths`` block naming exactly one target chapter: a worker may read the
governance ledgers and the old chapters, but may modify only that single file.
A broad legacy issue covering several chapters is migration *evidence*, never
implementation authority, so it is never reused as a chapter work unit.

This replaces the earlier 43-chapter generator, whose hard-coded issue bodies
described a book structure that no longer exists.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

GH = os.environ.get("GH_CLI", "gh")

# --------------------------------------------------------------------------
# Host facts for this repository's approved restructure, per
# docs/superpowers/plans/2026-07-25-aevatar-review-restructure.md.
# --------------------------------------------------------------------------
SCOPE_EXTEND = "SCOPE_EXTEND: restructure aevatar-review into 00-13 with 72 target chapters"
UPSTREAM_COMMIT = "f02aa690bbebb9cabeac30a553d737486b0eb661"
VERIFIED_AT = "2026-07-25"
DESIGN_DOC = "docs/superpowers/specs/2026-07-25-aevatar-review-restructure-design.md"
PLAN_DOC = "docs/superpowers/plans/2026-07-25-aevatar-review-restructure.md"

# Legacy issues that are migration evidence for a target but must not be reused
# or mutated as that target's work unit.
LEGACY_EVIDENCE: Dict[str, str] = {
    # #147 carries a six-path legacy scope, so 09/05 needs its own exact-scope issue.
    "09/05-production-canary-and-recovery.md": "#147",
}

ROW = re.compile(
    r"^- \[(?P<done>[ x])\] `(?P<path>[0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md)` "
    r"— status:(?P<status>current|mixed|historical|target) — issue:(?P<issue>\S+)\s*$"
)
# Legacy issues declare scope as a "## Scope paths" heading; new ones use a
# "scope_paths:" key. Both must be recognised, otherwise a broad legacy scope
# looks like no scope at all and could be adopted by accident.
SCOPE_BLOCK = re.compile(r"(?i)^\s*(?:#{1,6}\s*)?scope[_ ]paths\s*:?\s*$")
# Capture any listed path, not just target-shaped ones: a scope naming one target
# plus PLAN.md is a multi-path scope and must never be adopted as a work unit.
SCOPE_ITEM = re.compile(r"^\s*[-*]\s+`?([^`\s]+)`?\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


class IssueError(Exception):
    """A condition that must stop the run instead of leaving rows half-resolved."""


# ------------------------------------------------------------------------ gh io


def run_gh(args: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            [GH, *args], capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise IssueError(f"cannot execute {GH}: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else f"exit {completed.returncode}"
        raise IssueError(f"gh {' '.join(args[:2])} failed: {tail}")
    return completed.stdout


def list_existing_issues(repo: str) -> List[dict]:
    raw = run_gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,body,url",
        ]
    )
    text = raw.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except ValueError as error:
        raise IssueError(f"malformed gh issue list output: {error}") from error
    if not isinstance(parsed, list):
        raise IssueError("gh issue list did not return a JSON array")
    return parsed


# -------------------------------------------------------------------- manifest


def parse_manifest(path: str) -> List[dict]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as error:
        raise IssueError(f"cannot read manifest: {error}") from error

    rows: List[dict] = []
    seen: Dict[str, int] = {}
    fence: Optional[str] = None
    for index, line in enumerate(lines):
        opener = FENCE.match(line)
        if opener is not None:
            marker = opener.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            # The manifest documents its own row format inside a fenced block;
            # that example is documentation, not a target row.
            continue
        if not line.startswith("- ["):
            continue
        match = ROW.match(line)
        if match is None:
            raise IssueError(f"malformed manifest row at line {index + 1}: {line}")
        target = match.group("path")
        if target in seen:
            raise IssueError(
                f"duplicate target path {target} at lines {seen[target] + 1} and {index + 1}"
            )
        seen[target] = index
        rows.append(
            {
                "line": index,
                "path": target,
                "status": match.group("status"),
                "issue": match.group("issue"),
            }
        )
    if not rows:
        raise IssueError("manifest contains no target rows")
    return rows


def write_issue_url(path: str, line_index: int, url: str) -> None:
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines(keepends=True)
    original = lines[line_index]
    newline = "\n" if original.endswith("\n") else ""
    updated = re.sub(r"— issue:\S+\s*$", f"— issue:{url}", original.rstrip("\n"))
    lines[line_index] = updated + newline
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(lines))


# ------------------------------------------------------------------ issue body


def scope_paths_of(body: Optional[str]) -> List[str]:
    """Extract the declared scope_paths list from an issue body."""
    if not body:
        return []
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if not SCOPE_BLOCK.match(line):
            continue
        collected: List[str] = []
        for candidate in lines[index + 1 :]:
            if not candidate.strip():
                break
            item = SCOPE_ITEM.match(candidate)
            if item is None:
                break
            collected.append(item.group(1))
        return collected
    return []


def issue_title(row: dict) -> str:
    return f"[00-13 restructure] {row['path']}"


def issue_body(row: dict) -> str:
    target = row["path"]
    block = target.split("/", 1)[0]
    evidence = LEGACY_EVIDENCE.get(target)
    legacy = ""
    if evidence:
        legacy = (
            "\n## 迁移证据（只读引用）\n\n"
            f"- 旧 issue {evidence} 是本章的迁移证据；其 scope 覆盖多个路径，"
            "因此**不能**作为本工作单元复用。\n"
            f"- 本工作单元不得修改或关闭 {evidence}。\n"
        )

    return f"""{SCOPE_EXTEND}

target_path: {target}
status: {row['status']}
upstream_commit: {UPSTREAM_COMMIT}
verified_at: {VERIFIED_AT}

scope_paths:
- {target}

## 工作单元边界

- 本 issue 是**一个独立工作单元**，产物是**唯一**文件 `{target}`。
- 实现者可以**读**治理账本（`docs/migration/*`）与旧章节，但**只能改** `{target}`；
  共享账本只由目录协调步骤更新，避免多个章节工作单元在同一 SSOT 上竞争。
- 提交必须是精确单路径提交：`git commit --only -- {target}`。

## 事实基线

- 当前实现事实只能来自冻结提交 `{UPSTREAM_COMMIT}`，不得读取上游 live working tree。
- current 论断必须有 E1（冻结基线中的 code / proto / config / test）。
- closed issue 不等于已落地；open issue 只能写成缺口 / 风险 / 目标态。

## 验收标准

- frontmatter 含 `status: {row['status']}`、`upstream_commit: {UPSTREAM_COMMIT}`、`verified_at: {VERIFIED_AT}`。
- 开头列 1–3 个真正支撑整章的事实源路径与有效行号锚点。
- 至少两张职责不同的图：一张静态边界/所有权图，一张动态时序/状态/失败恢复图。
- 含设计正当性、协议与状态深入、最小 demo（诚实标注 demo 状态）、边界与演进、3–5 个验收问题。
- 通过 `check-md --paths`、`check-links --paths`、`check-mermaid` 与 placeholder 扫描。
- 通过独立内容 review（FI-001）。
{legacy}
## 依据

- 设计：`{DESIGN_DOC}`
- 计划：`{PLAN_DOC}`（目录 `{block}` 对应任务的主题表）
"""


# ------------------------------------------------------------------------ main


def resolve(rows: List[dict], repo: str, manifest: str, create: bool) -> Tuple[int, int]:
    existing = list_existing_issues(repo)
    by_scope: Dict[str, dict] = {}
    for issue in existing:
        scope = scope_paths_of(issue.get("body"))
        if len(scope) == 1:
            # Only an exact single-path scope may be adopted as a work unit.
            by_scope.setdefault(scope[0], issue)

    unresolved = 0
    created = 0
    for row in rows:
        target = row["path"]
        if row["issue"] != "pending":
            print(f"RECORDED {target} {row['issue']}")
            continue

        match = by_scope.get(target)
        if match is not None:
            url = str(match.get("url") or "")
            if not url:
                raise IssueError(f"existing issue for {target} has no url")
            write_issue_url(manifest, row["line"], url)
            row["issue"] = url
            print(f"REUSE {target} {url}")
            continue

        if not create:
            print(f"CREATE {target} {issue_title(row)}")
            continue

        output = run_gh(
            [
                "issue",
                "create",
                "--repo",
                repo,
                "--title",
                issue_title(row),
                "--body",
                issue_body(row),
            ]
        ).strip().splitlines()
        url = output[-1].strip() if output else ""
        if not url.startswith("http"):
            unresolved += 1
            print(f"gh issue create returned no URL for {target}", file=sys.stderr)
            continue
        write_issue_url(manifest, row["line"], url)
        row["issue"] = url
        created += 1
        print(f"CREATE {target} {url}")

    return created, unresolved


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args(argv)

    try:
        if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", args.repo):
            raise IssueError(f"malformed --repo (expected OWNER/REPO): {args.repo}")
        rows = parse_manifest(args.manifest)
        created, unresolved = resolve(rows, args.repo, args.manifest, args.create)
        mode = "create" if args.create else "dry-run"
        print(
            f"create_issues: {len(rows)} rows, mode={mode}, created={created}, "
            f"unresolved={unresolved}",
            file=sys.stderr,
        )
        return 1 if unresolved else 0
    except IssueError as error:
        print(f"create_issues: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
