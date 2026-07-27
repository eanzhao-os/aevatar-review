#!/usr/bin/env python3
"""Freeze an auditable upstream issue-membership cohort as Markdown ledger rows.

    python3 scripts/snapshot-upstream-issues.py \
      --repo OWNER/REPO --state open|closed \
      [--from YYYY-MM-DD --through YYYY-MM-DD | --snapshot-date YYYY-MM-DD] \
      [--reconstruct-at ISO8601] \
      --expect-count N --format markdown

Output: one escaped Markdown row per unique issue, sorted by issue number.
Fields: snapshot_state, issue, title, created_at, closed_at, labels, URL,
        classification=unclassified, implementation_evidence, destinations.

exit 0: unique row count equals N
exit 1: malformed arguments, gh/pagination failure, duplicate conflict, or count drift

Two acquisition modes:

* search mode (default) queries the REST search API through ``gh api --paginate``.
  It reflects *live* repository state, so it can only freeze a cohort while the
  live counts still equal the approved ones. It is the drift-telemetry mode.

* ``--reconstruct-at`` mode rebuilds the membership a repository had at a past
  instant by replaying each issue's ``closed`` / ``reopened`` events up to that
  instant. It is the recovery mode used when live search has already drifted
  past the approved snapshot. Issues untouched since the cutoff keep their
  current state; only issues updated at or after the cutoff need event replay.

This script never infers implementation status. Classification is always
emitted as ``unclassified`` and is filled in by a separate reconciliation task.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

GH = os.environ.get("GH_CLI", "gh")
ISO = "%Y-%m-%dT%H:%M:%SZ"


class SnapshotError(Exception):
    """Any condition that must stop the run instead of emitting a partial cohort."""


# --------------------------------------------------------------------------- io


def gh_json(endpoint: str, paginate: bool = True) -> List[object]:
    """Run ``gh api`` and decode every concatenated JSON document it printed.

    ``gh api --paginate`` emits one JSON document per page, so the output is a
    stream of documents rather than a single value. Decoding with ``raw_decode``
    keeps both object pages (search) and array pages (list endpoints) working
    without depending on a jq expression.
    """
    command = [GH, "api"]
    if paginate:
        command.append("--paginate")
    command.append(endpoint)
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise SnapshotError(f"cannot execute {GH}: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else f"exit {completed.returncode}"
        raise SnapshotError(f"gh api failed for {endpoint}: {tail}")

    documents: List[object] = []
    decoder = json.JSONDecoder()
    text = completed.stdout
    index = 0
    length = len(text)
    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index >= length:
            break
        try:
            value, offset = decoder.raw_decode(text, index)
        except ValueError as error:
            raise SnapshotError(f"malformed JSON from gh for {endpoint}: {error}") from error
        documents.append(value)
        index = offset
    return documents


def flatten_issue_documents(documents: Iterable[object]) -> List[dict]:
    """Accept either search pages ({"items": [...]}) or list pages ([...])."""
    issues: List[dict] = []
    for document in documents:
        if isinstance(document, dict) and "items" in document:
            entries = document.get("items") or []
        elif isinstance(document, list):
            entries = document
        else:
            raise SnapshotError("unexpected gh response shape (neither search page nor list page)")
        for entry in entries:
            if not isinstance(entry, dict) or "number" not in entry:
                raise SnapshotError("unexpected issue payload without a number")
            issues.append(entry)
    return issues


# ------------------------------------------------------------------- time utils


def parse_instant(value: str, label: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise SnapshotError(f"malformed {label}: {value}") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_date(value: str, label: str, end_of_day: bool) -> datetime:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        raise SnapshotError(f"malformed {label} (expected YYYY-MM-DD): {value}")
    suffix = "T23:59:59Z" if end_of_day else "T00:00:00Z"
    return parse_instant(value + suffix, label)


def field_instant(issue: dict, key: str) -> Optional[datetime]:
    value = issue.get(key)
    if not value:
        return None
    return parse_instant(str(value), f"{key} of issue #{issue.get('number')}")


# ------------------------------------------------------------------ state model


def is_pull_request(issue: dict) -> bool:
    return bool(issue.get("pull_request"))


def state_at(issue: dict, cutoff: datetime, events: Dict[int, List[Tuple[datetime, str]]]):
    """Return None if the issue did not exist yet, else (state, closed_at)."""
    created = field_instant(issue, "created_at")
    if created is None:
        raise SnapshotError(f"issue #{issue.get('number')} has no created_at")
    if created > cutoff:
        return None
    updated = field_instant(issue, "updated_at")
    if updated is not None and updated <= cutoff:
        # No activity after the cutoff, so the recorded state is the state then.
        if issue.get("state") == "closed":
            closed_at = field_instant(issue, "closed_at")
            if closed_at is None:
                raise SnapshotError(f"issue #{issue.get('number')} is closed without closed_at")
            return ("closed", closed_at)
        return ("open", None)

    history = [item for item in events.get(int(issue["number"]), []) if item[0] <= cutoff]
    history.sort(key=lambda item: item[0])
    if not history or history[-1][1] == "reopened":
        return ("open", None)
    return ("closed", history[-1][0])


def fetch_state_events(repo: str, number: int) -> List[Tuple[datetime, str]]:
    documents = gh_json(f"/repos/{repo}/issues/{number}/events?per_page=100")
    history: List[Tuple[datetime, str]] = []
    for document in documents:
        entries = document if isinstance(document, list) else [document]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            event = entry.get("event")
            if event not in ("closed", "reopened"):
                continue
            created = entry.get("created_at")
            if not created:
                raise SnapshotError(f"issue #{number} event without created_at")
            history.append((parse_instant(str(created), f"event of issue #{number}"), event))
    history.sort(key=lambda item: item[0])
    return history


# --------------------------------------------------------------------- rendering


def escape_cell(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.replace("|", r"\|")
    return " ".join(text.split()).strip()


def render_row(state: str, issue: dict, closed_at: Optional[datetime]) -> str:
    labels = issue.get("labels") or []
    names: List[str] = []
    for label in labels:
        if isinstance(label, dict):
            names.append(str(label.get("name", "")))
        else:
            names.append(str(label))
    label_cell = escape_cell("; ".join(name for name in names if name)) or "—"
    closed_cell = closed_at.strftime(ISO) if closed_at else "—"
    return "| {state} | #{number} | {title} | {created} | {closed} | {labels} | {url} | unclassified | — | — |".format(
        state=state,
        number=int(issue["number"]),
        title=escape_cell(issue.get("title")) or "—",
        created=escape_cell(issue.get("created_at")) or "—",
        closed=closed_cell,
        labels=label_cell,
        url=escape_cell(issue.get("html_url")) or "—",
    )


# -------------------------------------------------------------------- cohort ops


def dedupe(pairs: Sequence[Tuple[dict, Optional[datetime]]]) -> List[Tuple[dict, Optional[datetime]]]:
    seen: Dict[int, Tuple[dict, Optional[datetime]]] = {}
    for issue, closed_at in pairs:
        number = int(issue["number"])
        if number in seen:
            previous_issue, previous_closed = seen[number]
            same = (
                escape_cell(previous_issue.get("title")) == escape_cell(issue.get("title"))
                and previous_closed == closed_at
            )
            if not same:
                raise SnapshotError(
                    f"duplicate conflict for issue #{number}: two different payloads in one cohort"
                )
            continue
        seen[number] = (issue, closed_at)
    return [seen[number] for number in sorted(seen)]


def collect_search(repo: str, state: str, window: Optional[Tuple[datetime, datetime]]):
    query = f"repo:{repo} is:issue is:{state}"
    if state == "closed" and window is not None:
        low, high = window
        query += f" closed:{low.strftime('%Y-%m-%d')}..{high.strftime('%Y-%m-%d')}"
    # Match the documented endpoint form: spaces as "+", everything else percent-encoded.
    from urllib.parse import quote_plus

    endpoint = f"search/issues?q={quote_plus(query)}&per_page=100"
    issues = flatten_issue_documents(gh_json(endpoint))
    pairs: List[Tuple[dict, Optional[datetime]]] = []
    for issue in issues:
        if is_pull_request(issue):
            continue
        pairs.append((issue, field_instant(issue, "closed_at") if state == "closed" else None))
    return pairs


def collect_reconstructed(
    repo: str, state: str, cutoff: datetime, window: Optional[Tuple[datetime, datetime]]
):
    issues = flatten_issue_documents(
        gh_json(f"/repos/{repo}/issues?state=all&per_page=100")
    )
    issues = [issue for issue in issues if not is_pull_request(issue)]

    needs_replay = []
    for issue in issues:
        created = field_instant(issue, "created_at")
        if created is not None and created > cutoff:
            # The issue did not exist at the cutoff, so it belongs to neither
            # cohort and its timeline is irrelevant. Never spend an API call on it.
            continue
        updated = field_instant(issue, "updated_at")
        if updated is None or updated > cutoff:
            needs_replay.append(int(issue["number"]))
    print(
        f"snapshot-upstream-issues: replaying state events for {len(needs_replay)} "
        f"issue(s) touched after {cutoff.strftime(ISO)}",
        file=sys.stderr,
    )
    events: Dict[int, List[Tuple[datetime, str]]] = {}
    for number in needs_replay:
        events[number] = fetch_state_events(repo, number)

    pairs: List[Tuple[dict, Optional[datetime]]] = []
    for issue in issues:
        resolved = state_at(issue, cutoff, events)
        if resolved is None:
            continue
        resolved_state, closed_at = resolved
        if resolved_state != state:
            continue
        if state == "closed":
            if window is None:
                raise SnapshotError("closed reconstruction requires --from/--through")
            low, high = window
            effective_high = min(high, cutoff)
            if closed_at is None or not (low <= closed_at <= effective_high):
                continue
        pairs.append((issue, closed_at))
    return pairs


# --------------------------------------------------------------------------- cli


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--state", required=True, choices=("open", "closed"))
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--through", dest="through_date")
    parser.add_argument("--snapshot-date")
    parser.add_argument("--reconstruct-at")
    parser.add_argument("--expect-count", required=True, type=int)
    parser.add_argument("--format", required=True, choices=("markdown",))
    args = parser.parse_args(argv)

    try:
        if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", args.repo):
            raise SnapshotError(f"malformed --repo (expected OWNER/REPO): {args.repo}")
        if args.expect_count < 0:
            raise SnapshotError("--expect-count must not be negative")

        window: Optional[Tuple[datetime, datetime]] = None
        if args.state == "closed":
            if not (args.from_date and args.through_date):
                raise SnapshotError("--state closed requires --from and --through")
            window = (
                parse_date(args.from_date, "--from", end_of_day=False),
                parse_date(args.through_date, "--through", end_of_day=True),
            )
            if window[0] > window[1]:
                raise SnapshotError("--from must not be after --through")
        else:
            if not (args.snapshot_date or args.reconstruct_at):
                raise SnapshotError("--state open requires --snapshot-date or --reconstruct-at")
            if args.snapshot_date:
                parse_date(args.snapshot_date, "--snapshot-date", end_of_day=True)

        if args.reconstruct_at:
            cutoff = parse_instant(args.reconstruct_at, "--reconstruct-at")
            pairs = collect_reconstructed(args.repo, args.state, cutoff, window)
            method = f"reconstruct-at {cutoff.strftime(ISO)}"
        else:
            pairs = collect_search(args.repo, args.state, window)
            method = "live search"
            print(
                "snapshot-upstream-issues: live search reflects current repository "
                "state; use --reconstruct-at for historical membership",
                file=sys.stderr,
            )

        rows = dedupe(pairs)
        if len(rows) != args.expect_count:
            raise SnapshotError(
                f"count drift via {method}: expected {args.expect_count} unique "
                f"{args.state} issues, resolved {len(rows)}"
            )

        for issue, closed_at in rows:
            print(render_row(args.state, issue, closed_at))
        print(
            f"snapshot-upstream-issues: {len(rows)} {args.state} rows via {method}",
            file=sys.stderr,
        )
        return 0
    except SnapshotError as error:
        print(f"snapshot-upstream-issues: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
