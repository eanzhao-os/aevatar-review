#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path, PurePosixPath

SHA_RE = re.compile(r"[0-9a-f]{40}")
DIGEST_RE = re.compile(r"[0-9a-f]{64}")
CHAPTER_RE = re.compile(r"(?:0[0-9]|1[0-3])/[0-9]{2}-[a-z0-9-]+\.md")
ISSUE_URL_PATTERN = r"https://github\.com/[^/\s)]+/[^/\s)]+/issues/[0-9]+"
ISSUE_URL_RE = re.compile(ISSUE_URL_PATTERN)
ROW_RE = re.compile(
    r"^- \[x\] \[([^]]+)\]\(([^)]+)\).+"
    rf"\[issue\]\(({ISSUE_URL_PATTERN})\)\s*$"
)
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
STATE_KEYS = {
    "schema_version", "frozen_upstream_sha", "frozen_verified_at",
    "synced_upstream_sha", "last_successful_update_at", "chapters",
}
CHAPTER_KEYS = {"review_count", "last_reviewed_sha", "last_reviewed_at", "result"}
REQUIRED_GATES = {"check-md", "check-links", "check-drift", "check-mermaid", "mkdocs"}
CANDIDATE_RULES = (
    ("project", lambda p: p.suffix in {".csproj", ".sln", ".slnf", ".slnx"}),
    ("protocol", lambda p: p.suffix == ".proto"),
    ("design", lambda p: p.suffix == ".md" and tuple(p.parts[:2]) in {
        ("docs", "canon"), ("docs", "adr"),
    }),
    ("configuration", lambda p: p.name.lower().startswith("appsettings") and p.suffix == ".json"),
    ("topology", lambda p: p.suffix in {".yaml", ".yml"} and re.search(
        r"deploy|k8s|kubernetes|runtime[-_.]?topology|docker[-_.]?compose|helm|charts/",
        p.as_posix(), re.I,
    ) is not None),
    ("workflow", lambda p: p.suffix in {".yaml", ".yml"} and "workflow" in p.as_posix().lower()),
    ("component", lambda p: p.suffix == ".cs" and re.search(
        r"Host|Agent|GAgent|Runtime|Contract|Endpoint|ToolProvider|Connector|Workflow|Primitive|Persistence|Database|Store|Projection|Authorization|Authentication|Configuration",
        p.as_posix(), re.I,
    ) is not None),
)


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
        if len(ISSUE_URL_RE.findall(line)) != 1:
            raise ValueError(f"checked chapter row must contain exactly one GitHub issue URL: {line}")
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


def validate_state(value: object) -> dict:
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
        evidence = (reviewed_sha, reviewed_at, record["result"])
        if count == 0 and evidence != (None, None, None):
            raise ValueError(f"zero review_count must have null evidence: {chapter}")
        if count > 0 and (
            not valid_sha(reviewed_sha) or not valid_timestamp(reviewed_at)
            or record["result"] != "pass"
        ):
            raise ValueError(f"positive review_count requires complete PASS evidence: {chapter}")
    return value


def load_state(path: Path) -> dict:
    return validate_state(load_json(path))


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
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def require_repository_path(root: Path, path: Path, name: str) -> Path:
    root = root.resolve()
    absolute = path.absolute()
    resolved = absolute.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{name} must live under the repository root") from error
    if not relative.parts or relative.parts[0] == ".git":
        raise ValueError(f"invalid repository-local {name}")
    lexical_root = next(
        (candidate for candidate in absolute.parents if candidate.resolve() == root),
        None,
    )
    if lexical_root is None:
        raise ValueError(f"cannot locate repository root for {name}")
    current = lexical_root
    for part in absolute.relative_to(lexical_root).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"repository-local {name} cannot traverse symlinks")
    return resolved


@contextmanager
def state_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f".{path.name}.lock")
    descriptor = os.open(
        lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600
    )
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError("state lock must be a regular file")
    with os.fdopen(descriptor, "a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def init_state(state: Path, plan: Path, frozen_sha: str, frozen_verified_at: str) -> None:
    if not valid_sha(frozen_sha):
        raise ValueError("frozen SHA must be 40 lowercase hexadecimal characters")
    if not valid_date(frozen_verified_at):
        raise ValueError("frozen verified date must be YYYY-MM-DD")
    if plan.name != "PLAN.md" or plan.is_symlink():
        raise ValueError("plan must be a regular PLAN.md")
    require_repository_path(plan.resolve().parent, state, "state")
    chapters = {
        chapter: {
            "review_count": 0,
            "last_reviewed_sha": None,
            "last_reviewed_at": None,
            "result": None,
        }
        for chapter in chapter_rows(plan)
    }
    with state_lock(state):
        if state.exists():
            raise ValueError(f"state already exists: {state}")
        atomic_json(state, {
            "schema_version": 1,
            "frozen_upstream_sha": frozen_sha,
            "frozen_verified_at": frozen_verified_at,
            "synced_upstream_sha": frozen_sha,
            "last_successful_update_at": None,
            "chapters": chapters,
        })


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def no_duplicate_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_object)


def facts_sha256(value: dict) -> str:
    unsigned = dict(value)
    unsigned.pop("facts_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def seal_facts(value: dict) -> dict:
    sealed = dict(value)
    sealed["facts_sha256"] = facts_sha256(sealed)
    return sealed


def load_facts(path: Path) -> dict:
    value = load_json(path)
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("facts_sha256"), str)
        or DIGEST_RE.fullmatch(value["facts_sha256"]) is None
    ):
        raise ValueError("invalid facts document")
    if value["facts_sha256"] != facts_sha256(value):
        raise ValueError("facts hash mismatch")
    return value


def state_bytes(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    return raw, validate_state(json.loads(
        raw.decode("utf-8"), object_pairs_hook=no_duplicate_object
    ))


def run_command(args: list[object], ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    command = [*map(str, args)]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode not in ok:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise ValueError(f"command failed ({' '.join(command)}): {detail}")
    return result


def git(upstream: Path, *args: object, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    return run_command(["git", "-C", upstream, *args], ok)


def source_entry(value: object, aliases: dict[str, str]) -> str:
    if not isinstance(value, str):
        raise ValueError("source-map entries must be strings")
    configured = PurePosixPath(value)
    if not value or "\0" in value or configured.is_absolute() or ".." in configured.parts:
        raise ValueError(f"unsafe source-map path: {value!r}")
    expanded = (
        f"docs/adr/{value}.md"
        if re.fullmatch(r"[0-9]{4}-[a-z0-9-]+", value)
        else aliases.get(value, value)
    )
    path = PurePosixPath(expanded)
    if not expanded or "\0" in expanded or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe source-map path: {expanded!r}")
    return expanded


def load_source_map(path: Path) -> dict[str, tuple[str, ...]]:
    value = load_json(path)
    if not isinstance(value, dict) or value.get("version") != 2:
        raise ValueError("invalid source-map version")
    alias_expansion = value.get("alias_expansion", {})
    if not isinstance(alias_expansion, dict):
        raise ValueError("invalid alias_expansion")
    aliases = alias_expansion.get("canon", {})
    if not isinstance(aliases, dict) or any(
        not isinstance(key, str) or not isinstance(target, str)
        for key, target in aliases.items()
    ):
        raise ValueError("invalid canon aliases")
    for target in aliases.values():
        source_entry(target, {})

    chapters = value.get("chapters")
    if not isinstance(chapters, dict):
        raise ValueError("invalid source-map chapters")
    normalized: dict[str, tuple[str, ...]] = {}
    for chapter, configured in chapters.items():
        if not isinstance(chapter, str):
            raise ValueError("invalid source-map chapter")
        if chapter.startswith("_doc_"):
            continue
        if CHAPTER_RE.fullmatch(chapter) is None:
            raise ValueError(f"invalid source-map chapter: {chapter}")
        entries = configured if isinstance(configured, list) else (
            configured.get("paths", []) if isinstance(configured, dict) else None
        )
        if not isinstance(entries, list):
            raise ValueError(f"invalid source-map paths: {chapter}")
        normalized[chapter] = tuple(sorted({source_entry(item, aliases) for item in entries}))
    return normalized


def mapped_chapters(path: str, source_map: dict[str, tuple[str, ...]]) -> list[str]:
    return sorted(
        chapter
        for chapter, entries in source_map.items()
        if any(path.startswith(entry) if entry.endswith("/") else path == entry for entry in entries)
    )


def upstream_evidence(upstream: Path) -> dict[str, str]:
    head = git(upstream, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
    status = git(upstream, "--no-optional-locks", "status", "--porcelain=v1").stdout
    return {"head": head, "status": status}


def require_commit(upstream: Path, sha: str, name: str) -> None:
    result = git(upstream, "cat-file", "-e", f"{sha}^{{commit}}", ok=(0, 1, 128))
    if result.returncode != 0:
        raise ValueError(f"{name} commit object is missing: {sha}")


def commit_records(upstream: Path, shas: list[str]) -> list[dict]:
    records = []
    for sha in shas:
        fields = git(
            upstream, "show", "-s", "--no-show-signature",
            "--format=%H%x00%P%x00%s%x00%an%x00%aI", sha,
        ).stdout.rstrip("\n").split("\0")
        if len(fields) != 5:
            raise ValueError(f"cannot parse commit metadata: {sha}")
        commit_sha, parents, subject, author, authored_at = fields
        records.append({
            "sha": commit_sha,
            "parents": parents.split(),
            "subject": subject,
            "author": author,
            "authored_at": authored_at,
        })
    return records


def tree_changes(upstream: Path, synced_sha: str, target_sha: str) -> list[dict]:
    fields = git(
        upstream, "diff", "--name-status", "-z", "-M", synced_sha, target_sha
    ).stdout.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    records: list[dict] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if not status:
            raise ValueError("cannot parse empty Git change status")
        if status[0] in {"R", "C"}:
            if index + 1 >= len(fields):
                raise ValueError("cannot parse renamed Git path")
            old_path, path = fields[index:index + 2]
            index += 2
            records.append({"status": status, "old_path": old_path, "path": path})
        else:
            if index >= len(fields):
                raise ValueError("cannot parse changed Git path")
            records.append({"status": status, "path": fields[index]})
            index += 1
    return sorted(records, key=lambda record: (record["path"], record["status"]))


def changed_paths(changes: list[dict]) -> list[str]:
    return sorted({
        path
        for change in changes
        for path in (change.get("old_path"), change["path"])
        if path is not None
    })


def materialize_snapshot(script: Path, upstream: Path, root: Path, sha: str) -> Path:
    output = (root / sha).resolve()
    result = run_command([
        "bash", script, "--repo", upstream, "--sha", sha, "--output", output,
    ])
    lines = result.stdout.splitlines()
    if len(lines) != 1 or not Path(lines[0]).is_absolute():
        raise ValueError(f"snapshot script returned an invalid path for {sha}")
    reported = Path(lines[0]).resolve()
    if reported != output:
        raise ValueError(f"snapshot script returned the wrong path for {sha}")
    verify_snapshot(reported, sha)
    return reported


def verify_snapshot(snapshot: Path, sha: str) -> None:
    if not snapshot.is_absolute() or not snapshot.joinpath("aevatar.slnx").is_file():
        raise ValueError(f"invalid snapshot tree: {snapshot}")
    marker = snapshot / ".source-commit"
    if not marker.is_file() or marker.read_text(encoding="utf-8") != f"{sha}\n":
        raise ValueError(f"snapshot marker mismatch: {snapshot}")


def architecture_candidates(
    snapshot: Path, review_root: Path, plan_chapters: list[str],
    source_map: dict[str, tuple[str, ...]],
) -> list[dict]:
    chapter_text = {
        chapter: (review_root / chapter).read_text(encoding="utf-8")
        for chapter in plan_chapters
    }
    candidates = []
    for candidate in snapshot.rglob("*"):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(snapshot).as_posix()
        path = Path(relative)
        kind = next((name for name, rule in CANDIDATE_RULES if rule(path)), None)
        if kind is None:
            continue
        # ponytail: index chapter text only if measured candidate scans become material
        text_hits = sorted(
            chapter for chapter, text in chapter_text.items()
            if relative in text or path.name in text
        )
        candidates.append({
            "kind": kind,
            "path": relative,
            "mapped_chapters": mapped_chapters(relative, source_map),
            "chapter_text_hits": text_hits,
        })
    return sorted(candidates, key=lambda item: (item["path"], item["kind"]))


def validate_mode(mode: object, topic: object) -> None:
    if mode == "full" and topic is not None:
        raise ValueError("full mode does not accept --topic")
    if mode == "topic" and (not isinstance(topic, str) or not topic.strip()):
        raise ValueError("topic mode requires a non-empty --topic")
    if mode not in {"full", "topic"}:
        raise ValueError("invalid update mode")


def require_outside_upstream(path: Path, upstream: Path, name: str) -> Path:
    resolved = path.resolve()
    if resolved == upstream or upstream in resolved.parents:
        raise ValueError(f"{name} must be outside the upstream repository")
    return resolved


def require_distinct_output(output: Path, *inputs: Path) -> Path:
    resolved = output.resolve()
    if resolved in {path.resolve() for path in inputs}:
        raise ValueError("output must not replace an input file")
    return resolved


def prepare_update(
    mode: str, topic: str | None, review_root: Path, upstream: Path, state_path: Path,
    map_path: Path, snapshot_script: Path, snapshot_root: Path, branch: str,
    excluded: list[str], output: Path,
) -> None:
    validate_mode(mode, topic)
    if branch != "feature/integrate":
        raise ValueError("branch must be feature/integrate")
    if len(excluded) != len(set(excluded)):
        raise ValueError("duplicate excluded chapter")

    review_root = review_root.resolve()
    upstream = upstream.resolve()
    snapshot_script = snapshot_script.resolve()
    snapshot_root = require_outside_upstream(snapshot_root, upstream, "snapshot root")
    output = require_distinct_output(
        require_repository_path(
            review_root,
            require_outside_upstream(output, upstream, "facts output"),
            "facts output",
        ),
        state_path, map_path, snapshot_script, review_root / "PLAN.md",
    )
    require_outside_upstream(state_path, upstream, "state")
    plan_rows = chapter_rows(review_root / "PLAN.md")
    for chapter in excluded:
        if chapter not in plan_rows:
            raise ValueError(f"excluded chapter is not active: {chapter}")
    source_map = load_source_map(map_path)
    inactive_owners = sorted(set(source_map) - set(plan_rows))
    if inactive_owners:
        raise ValueError(f"source-map owners are not active PLAN chapters: {inactive_owners}")
    raw_state, state = state_bytes(state_path)

    before = upstream_evidence(upstream)
    run_command([
        "git", "-C", str(upstream), "fetch", "--no-tags", "origin",
        "+refs/heads/feature/integrate:refs/remotes/origin/feature/integrate",
    ])
    after = upstream_evidence(upstream)
    if after != before:
        raise ValueError("fetch changed upstream HEAD or working-tree status")

    target_sha = git(
        upstream, "rev-parse", "--verify",
        "refs/remotes/origin/feature/integrate^{commit}",
    ).stdout.strip()
    if not valid_sha(target_sha):
        raise ValueError("remote branch did not resolve to a full commit SHA")
    frozen_sha = state["frozen_upstream_sha"]
    synced_sha = state["synced_upstream_sha"]
    require_commit(upstream, frozen_sha, "frozen")
    require_commit(upstream, synced_sha, "synced")

    ancestry = git(
        upstream, "merge-base", "--is-ancestor", synced_sha, target_sha,
        ok=(0, 1),
    ).returncode == 0
    revision_args = [f"{synced_sha}..{target_sha}"] if ancestry else [target_sha, "--not", synced_sha]
    shas = git(
        upstream, "rev-list", "--reverse", "--topo-order", *revision_args
    ).stdout.splitlines()
    changes = tree_changes(upstream, synced_sha, target_sha)
    paths = changed_paths(changes)
    chapter_hits: dict[str, list[str]] = {}
    unmapped = []
    for path in paths:
        hits = mapped_chapters(path, source_map)
        if not hits:
            unmapped.append(path)
        for chapter in hits:
            chapter_hits.setdefault(chapter, []).append(path)
    chapter_hits = {
        chapter: sorted(set(hit_paths))
        for chapter, hit_paths in sorted(chapter_hits.items())
    }

    frozen_snapshot = materialize_snapshot(snapshot_script, upstream, snapshot_root, frozen_sha)
    target_snapshot = materialize_snapshot(snapshot_script, upstream, snapshot_root, target_sha)
    facts = seal_facts({
        "mode": mode,
        "topic": topic,
        "state_sha256": sha256_bytes(raw_state),
        "review_root": str(review_root),
        "upstream_repo": str(upstream),
        "frozen_sha": frozen_sha,
        "frozen_verified_at": state["frozen_verified_at"],
        "synced_sha": synced_sha,
        "target_sha": target_sha,
        "branch": branch,
        "target_ref": "refs/remotes/origin/feature/integrate",
        "frozen_snapshot_path": str(frozen_snapshot),
        "target_snapshot_path": str(target_snapshot),
        "upstream_before": before,
        "upstream_after": after,
        "history_rewrite": not ancestry,
        "commits": commit_records(upstream, shas),
        "changes": changes,
        "chapter_hits": chapter_hits,
        "unmapped_changed_files": sorted(unmapped),
        "architecture_candidates": architecture_candidates(
            target_snapshot, review_root, sorted(plan_rows), source_map
        ),
        "protected_chapters": sorted(excluded),
        "semantic_changed_chapters": [],
        "new_chapter_issues": {},
        "review_sample": [],
        "selection_completed": False,
    })
    atomic_json(output, facts)
    print(output)


def facts_state(facts: dict, state_path: Path) -> tuple[bytes, dict]:
    raw, state = state_bytes(state_path)
    if facts.get("state_sha256") != sha256_bytes(raw):
        raise ValueError("state hash mismatch")
    validate_mode(facts.get("mode"), facts.get("topic"))
    expected = (
        ("frozen_sha", "frozen_upstream_sha"),
        ("frozen_verified_at", "frozen_verified_at"),
        ("synced_sha", "synced_upstream_sha"),
    )
    if any(facts.get(fact_key) != state[state_key] for fact_key, state_key in expected):
        raise ValueError("facts do not match state metadata")
    if not valid_sha(facts.get("target_sha")):
        raise ValueError("invalid target SHA in facts")
    if facts.get("branch") != "feature/integrate":
        raise ValueError("invalid target branch in facts")
    upstream = facts.get("upstream_repo")
    if not isinstance(upstream, str) or not Path(upstream).is_absolute():
        raise ValueError("invalid upstream repository in facts")
    require_outside_upstream(state_path, Path(upstream), "state")
    return raw, state


def facts_review_root(facts: dict) -> Path:
    value = facts.get("review_root")
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError("invalid review root in facts")
    root = Path(value).resolve()
    if not root.is_dir():
        raise ValueError("review root does not exist")
    return root


def safe_review_file(root: Path, value: str, name: str) -> Path:
    configured = PurePosixPath(value)
    if (
        not value or "\0" in value or configured.is_absolute()
        or configured.as_posix() != value or any(part in {"", ".", ".."} for part in configured.parts)
        or configured.parts[0] == ".git"
    ):
        raise ValueError(f"unsafe {name}: {value!r}")
    path = root.joinpath(*configured.parts)
    resolved = require_repository_path(root, path, name)
    relative = resolved.relative_to(root)
    if not relative.parts or relative.parts[0] == ".git":
        raise ValueError(f"{name} cannot resolve into Git metadata: {value}")
    if not path.is_file():
        raise ValueError(f"{name} is not a regular file: {value}")
    return path


def changed_review_paths(root: Path) -> set[str]:
    top = run_command(["git", "-C", root, "rev-parse", "--show-toplevel"]).stdout.strip()
    if Path(top).resolve() != root:
        raise ValueError("review root must be the Git worktree root")
    tracked = run_command([
        "git", "-C", root, "diff", "--name-only", "-z", "HEAD", "--",
    ]).stdout.split("\0")
    untracked = run_command([
        "git", "-C", root, "ls-files", "--others", "--exclude-standard", "-z", "--",
    ]).stdout.split("\0")
    return {path for path in tracked + untracked if path}


def sealed_review_files(root: Path, paths: list[str]) -> dict[str, str]:
    return {
        path: sha256_bytes(safe_review_file(root, path, "sealed path").read_bytes())
        for path in sorted(paths)
    }


def unique_chapters(value: object, name: str, *, sort: bool = False) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(path, str) or CHAPTER_RE.fullmatch(path) is None for path in value
    ):
        raise ValueError(f"invalid {name}")
    if len(value) != len(set(value)):
        raise ValueError(f"duplicate {name}")
    return sorted(value) if sort else value


def parse_issue_entries(entries: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for entry in entries:
        chapter, separator, issue = entry.partition("=")
        if (
            not separator or CHAPTER_RE.fullmatch(chapter) is None
            or ISSUE_URL_RE.fullmatch(issue) is None or chapter in parsed
        ):
            raise ValueError(f"invalid new chapter issue: {entry}")
        parsed[chapter] = issue
    return parsed


def select_review(
    state_path: Path, plan: Path, facts_path: Path, sample_size: int,
    changed: list[str], issue_entries: list[str], structural_paths: list[str], output: Path,
) -> None:
    facts = load_facts(facts_path)
    _, state = facts_state(facts, state_path)
    review_root = facts_review_root(facts)
    if plan.resolve() != review_root / "PLAN.md":
        raise ValueError("plan must be REVIEW_ROOT/PLAN.md")
    if not 0 <= sample_size <= 6:
        raise ValueError("sample size must be between zero and six")
    semantic = unique_chapters(changed, "changed chapter", sort=True)
    rows = chapter_rows(plan)
    if any(chapter not in rows for chapter in semantic):
        raise ValueError("changed chapter is not active in PLAN.md")

    new_chapters = sorted(set(rows) - set(state["chapters"]))
    if any(chapter not in semantic for chapter in new_chapters):
        raise ValueError("every new PLAN chapter must be a semantic change")
    issues = parse_issue_entries(issue_entries)
    expected_issues = {chapter: rows[chapter] for chapter in new_chapters}
    if issues != expected_issues:
        raise ValueError("new chapter issue evidence does not exactly match PLAN.md")

    protected = unique_chapters(facts.get("protected_chapters"), "protected chapter")
    sample = stable_sample(
        sorted(rows), state, set(protected) | set(semantic), sample_size,
        facts["target_sha"],
    )
    if len(structural_paths) != len(set(structural_paths)):
        raise ValueError("duplicate structural path")
    structural = sorted(structural_paths)
    for path in structural:
        safe_review_file(review_root, path, "structural path")
        if CHAPTER_RE.fullmatch(path) is not None:
            raise ValueError(f"chapter must use --changed-chapter: {path}")
    if not set(structural).issubset(changed_review_paths(review_root)):
        raise ValueError("structural paths must be selected from the actual Git diff")
    sealed = sealed_review_files(review_root, semantic + sample + structural)
    selected = dict(facts)
    selected.update({
        "semantic_changed_chapters": semantic,
        "new_chapter_issues": expected_issues,
        "review_sample": sample,
        "structural_semantic_paths": structural,
        "sealed_files": sealed,
        "selection_completed": True,
    })
    output = require_distinct_output(
        require_repository_path(
            review_root,
            require_outside_upstream(
                output, Path(facts["upstream_repo"]), "facts output"
            ),
            "facts output",
        ),
        state_path, plan, facts_path,
    )
    atomic_json(output, seal_facts(selected))
    print(output)


def empty_chapter_record() -> dict:
    return {
        "review_count": 0,
        "last_reviewed_sha": None,
        "last_reviewed_at": None,
        "result": None,
    }


def load_evidence(path: Path, review_root: Path, name: str) -> dict:
    resolved = require_repository_path(review_root, path, f"{name} evidence")
    relative = resolved.relative_to(review_root.resolve())
    if not relative.parts or relative.parts[0] == ".git":
        raise ValueError(f"{name} evidence cannot live in Git metadata")
    if not path.is_file():
        raise ValueError(f"invalid {name} evidence path")
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"invalid {name} evidence")
    return value


def validate_reviewer_evidence(value: dict, facts: dict, sealed: dict[str, str]) -> None:
    if set(value) != {
        "schema_version", "facts_sha256", "reviewer", "results", "blocking_findings"
    } or type(value["schema_version"]) is not int or value["schema_version"] != 1 or (
        value["facts_sha256"] != facts["facts_sha256"]
    ):
        raise ValueError("invalid reviewer evidence fields or facts binding")
    reviewer = value["reviewer"]
    if not isinstance(reviewer, dict) or set(reviewer) != {
        "task_id", "model", "fresh_context", "read_only", "independent"
    }:
        raise ValueError("invalid reviewer identity")
    if any(
        not isinstance(reviewer[field], str) or not reviewer[field].strip()
        for field in ("task_id", "model")
    ) or any(reviewer[field] is not True for field in (
        "fresh_context", "read_only", "independent"
    )):
        raise ValueError("reviewer must be explicit, fresh, read-only, and independent")
    results = value["results"]
    if not isinstance(results, dict) or set(results) != set(sealed) or any(
        result != "pass" for result in results.values()
    ):
        raise ValueError("reviewer PASS coverage does not exactly match sealed files")
    if value["blocking_findings"] != []:
        raise ValueError("reviewer evidence has blocking findings")


def validate_gate_evidence(value: dict, facts: dict) -> None:
    if set(value) != {"schema_version", "facts_sha256", "gates"} or (
        type(value["schema_version"]) is not int or value["schema_version"] != 1
        or value["facts_sha256"] != facts["facts_sha256"] or not isinstance(value["gates"], list)
    ):
        raise ValueError("invalid gate evidence fields or facts binding")
    names = []
    for gate in value["gates"]:
        if not isinstance(gate, dict) or set(gate) != {"name", "exit_code"}:
            raise ValueError("invalid gate result")
        name, exit_code = gate["name"], gate["exit_code"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid gate name")
        if type(exit_code) is not int or exit_code != 0:
            raise ValueError(f"gate did not exit zero: {name}")
        names.append(name)
    if len(names) != len(set(names)) or not REQUIRED_GATES.issubset(names):
        raise ValueError("required gates are missing or duplicated")


def safe_owned_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value or "\0" in value or path.is_absolute() or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts) or path.parts[0] == ".git"
    ):
        raise ValueError(f"unsafe owned path: {value!r}")
    return value


def remote_main_sha(review_root: Path) -> str:
    fields = run_command([
        "git", "-C", review_root, "ls-remote", "--exit-code",
        "origin", "refs/heads/main",
    ]).stdout.split()
    if len(fields) != 2 or fields[1] != "refs/heads/main" or not valid_sha(fields[0]):
        raise ValueError("origin/main did not resolve to exactly one full SHA")
    return fields[0]


def verify_publication(
    review_root: Path, base_sha: str, phase: str, owned_paths: list[str],
) -> None:
    review_root = review_root.resolve()
    if not valid_sha(base_sha):
        raise ValueError("base SHA must be 40 lowercase hexadecimal characters")
    if phase not in {"base", "commit", "push"}:
        raise ValueError("invalid publication phase")
    top = run_command([
        "git", "-C", review_root, "rev-parse", "--show-toplevel",
    ]).stdout.strip()
    if Path(top).resolve() != review_root:
        raise ValueError("review root must be the Git worktree root")
    if run_command([
        "git", "-C", review_root, "branch", "--show-current",
    ]).stdout.strip() != "main":
        raise ValueError("publication requires main branch")
    require_commit(review_root, base_sha, "base")
    if len(owned_paths) != len(set(owned_paths)):
        raise ValueError("duplicate owned path")
    owned = {safe_owned_path(path) for path in owned_paths}
    head = git(review_root, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()

    if phase == "base":
        if owned:
            raise ValueError("base verification does not accept owned paths")
        if head != base_sha or remote_main_sha(review_root) != base_sha:
            raise ValueError("local HEAD and origin/main must equal BASE_SHA")
        return

    if not owned:
        raise ValueError("commit verification requires explicit owned paths")
    parents = git(
        review_root, "rev-list", "--parents", "-n", "1", "HEAD"
    ).stdout.split()
    if len(parents) != 2 or parents != [head, base_sha]:
        raise ValueError("documentation commit must have BASE_SHA as its only parent")
    changed = {
        path for path in git(
            review_root, "diff", "--name-only", "--no-renames", "-z",
            base_sha, head, "--",
        ).stdout.split("\0") if path
    }
    if changed != owned:
        raise ValueError("committed changed-file set does not equal owned paths")
    if phase == "push" and remote_main_sha(review_root) != base_sha:
        raise ValueError("origin/main changed before push")
    print(head)


def commit_state(
    state_path: Path, plan: Path, facts_path: Path, completed_at: str,
    review_evidence_path: Path, gate_evidence_path: Path,
) -> None:
    review_root = facts_review_root(load_facts(facts_path))
    require_repository_path(review_root, state_path, "state")
    with state_lock(state_path):
        commit_state_locked(
            state_path, plan, facts_path, completed_at,
            review_evidence_path, gate_evidence_path,
        )


def commit_state_locked(
    state_path: Path, plan: Path, facts_path: Path, completed_at: str,
    review_evidence_path: Path, gate_evidence_path: Path,
) -> None:
    facts = load_facts(facts_path)
    raw_state, state = facts_state(facts, state_path)
    review_root = facts_review_root(facts)
    if plan.resolve() != review_root / "PLAN.md":
        raise ValueError("plan must be REVIEW_ROOT/PLAN.md")
    if not valid_timestamp(completed_at):
        raise ValueError("completed-at must be a valid UTC Z timestamp")
    if facts.get("selection_completed") is not True:
        raise ValueError("review selection is incomplete")
    if facts.get("history_rewrite") is not False:
        raise ValueError("history rewrites cannot be committed automatically")

    semantic = unique_chapters(
        facts.get("semantic_changed_chapters"), "semantic changed chapter"
    )
    sample = unique_chapters(facts.get("review_sample"), "review sample")
    if set(semantic) & set(sample):
        raise ValueError("semantic changes and rotating sample overlap")
    structural = facts.get("structural_semantic_paths")
    sealed = facts.get("sealed_files")
    if not isinstance(structural, list) or any(not isinstance(path, str) for path in structural):
        raise ValueError("invalid structural semantic paths")
    if len(structural) != len(set(structural)):
        raise ValueError("duplicate structural semantic path")
    expected_sealed = set(semantic) | set(sample) | set(structural)
    if not isinstance(sealed, dict) or set(sealed) != expected_sealed or any(
        not isinstance(digest, str) or DIGEST_RE.fullmatch(digest) is None
        for digest in sealed.values()
    ):
        raise ValueError("sealed files do not exactly match review scope")
    reviewer_evidence = load_evidence(review_evidence_path, review_root, "reviewer")
    gate_evidence = load_evidence(gate_evidence_path, review_root, "gate")
    validate_reviewer_evidence(reviewer_evidence, facts, sealed)
    validate_gate_evidence(gate_evidence, facts)

    rows = chapter_rows(plan)
    if any(chapter not in rows for chapter in semantic + sample):
        raise ValueError("review scope is not active in PLAN.md")
    new_chapters = sorted(set(rows) - set(state["chapters"]))
    issues = facts.get("new_chapter_issues")
    if not isinstance(issues, dict) or issues != {
        chapter: rows[chapter] for chapter in new_chapters
    } or any(chapter not in semantic for chapter in new_chapters):
        raise ValueError("new chapter issue evidence is incomplete")

    target_sha = facts["target_sha"]
    verify_snapshot(Path(facts.get("frozen_snapshot_path", "")), state["frozen_upstream_sha"])
    verify_snapshot(Path(facts.get("target_snapshot_path", "")), target_sha)

    chapters = {
        chapter: dict(state["chapters"].get(chapter, empty_chapter_record()))
        for chapter in rows
    }
    for chapter in sample:
        if chapter not in state["chapters"]:
            continue
        record = chapters[chapter]
        record.update({
            "review_count": record["review_count"] + 1,
            "last_reviewed_sha": target_sha,
            "last_reviewed_at": completed_at,
            "result": "pass",
        })
    updated = {
        "schema_version": state["schema_version"],
        "frozen_upstream_sha": state["frozen_upstream_sha"],
        "frozen_verified_at": state["frozen_verified_at"],
        "synced_upstream_sha": (
            target_sha if facts["mode"] == "full" else state["synced_upstream_sha"]
        ),
        "last_successful_update_at": completed_at,
        "chapters": chapters,
    }
    if state_path.read_bytes() != raw_state:
        raise ValueError("state changed during commit")
    if sealed_review_files(review_root, list(sealed)) != sealed:
        raise ValueError("sealed file changed after final selection")
    atomic_json(state_path, updated)


def main() -> int:
    parser = argparse.ArgumentParser(prog="prepare-update.py")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init-state")
    init.add_argument("--state", required=True, type=Path)
    init.add_argument("--plan", required=True, type=Path)
    init.add_argument("--frozen-sha", required=True)
    init.add_argument("--frozen-verified-at", required=True)

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--mode", required=True, choices=("full", "topic"))
    prepare.add_argument("--topic")
    prepare.add_argument("--review-root", required=True, type=Path)
    prepare.add_argument("--upstream-repo", required=True, type=Path)
    prepare.add_argument("--state", required=True, type=Path)
    prepare.add_argument("--map", required=True, type=Path)
    prepare.add_argument("--snapshot-script", required=True, type=Path)
    prepare.add_argument("--snapshot-root", required=True, type=Path)
    prepare.add_argument("--branch", required=True)
    prepare.add_argument("--exclude-chapter", action="append", default=[])
    prepare.add_argument("--output", required=True, type=Path)

    select = commands.add_parser("select-review")
    select.add_argument("--state", required=True, type=Path)
    select.add_argument("--plan", required=True, type=Path)
    select.add_argument("--facts", required=True, type=Path)
    select.add_argument("--sample-size", type=int, default=6)
    select.add_argument("--changed-chapter", action="append", default=[])
    select.add_argument("--new-chapter-issue", action="append", default=[])
    select.add_argument("--structural-path", action="append", default=[])
    select.add_argument("--output", required=True, type=Path)

    commit = commands.add_parser("commit-state")
    commit.add_argument("--state", required=True, type=Path)
    commit.add_argument("--plan", required=True, type=Path)
    commit.add_argument("--facts", required=True, type=Path)
    commit.add_argument("--completed-at", required=True)
    commit.add_argument("--review-evidence", required=True, type=Path)
    commit.add_argument("--gate-evidence", required=True, type=Path)

    publication = commands.add_parser("verify-publication")
    publication.add_argument("--review-root", required=True, type=Path)
    publication.add_argument("--base-sha", required=True)
    publication.add_argument("--phase", required=True, choices=("base", "commit", "push"))
    publication.add_argument("--owned-path", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.command == "init-state":
            init_state(args.state, args.plan, args.frozen_sha, args.frozen_verified_at)
        elif args.command == "prepare":
            prepare_update(
                args.mode, args.topic, args.review_root, args.upstream_repo,
                args.state, args.map, args.snapshot_script, args.snapshot_root,
                args.branch, args.exclude_chapter, args.output,
            )
        elif args.command == "select-review":
            select_review(
                args.state, args.plan, args.facts, args.sample_size,
                args.changed_chapter, args.new_chapter_issue,
                args.structural_path, args.output,
            )
        elif args.command == "commit-state":
            commit_state(
                args.state, args.plan, args.facts, args.completed_at,
                args.review_evidence, args.gate_evidence,
            )
        else:
            verify_publication(
                args.review_root, args.base_sha, args.phase, args.owned_path,
            )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, f"prepare-update: ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
