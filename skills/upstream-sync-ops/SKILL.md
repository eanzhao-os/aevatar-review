---
name: upstream-sync-ops
description: Use when an agent is asked to install, enable, run, inspect, troubleshoot, reload, or uninstall the aevatar-review upstream-sync launchd job on macOS, including GitHub issue creation, logs, state.json, or a not-running status.
---

# Upstream Sync Operations

## Core principle

Treat `docs/upstream-sync.md` as the operational source of truth. Inspect before acting, preserve
the read-only upstream boundary, and match every side effect to the user's request.

## Required context

1. Resolve the repository root with `git rev-parse --show-toplevel`.
2. Read `docs/upstream-sync.md` completely.
3. Read `scripts/upstream-sync.sh` or `.config/upstream-sync/launchd.plist.template` only when the
   request depends on their current behavior.

Do not copy host paths, usernames, repository slugs, or branch facts into this skill.

## Operation contract

| Request | Allowed action |
|---|---|
| Status or troubleshooting | Read-only checks only |
| Install, enable, reload, or start | Follow the matching runbook section after resolving exact paths and launchd domain |
| Initialize | Explain that `--init` replaces the baseline and filed-issue ledger before running it |
| Run a scan | Explain that default mode may create GitHub issues; use `--dry-run` only when previewing is requested |
| Uninstall | Resolve the exact label and plist first; remove only launchd registration and plist unless broader deletion is explicit |

Never modify the upstream repository. Never delete or rewrite `state.json` as a generic repair.

## Status interpretation

This is an interval job, not a daemon. `state = not running` is healthy when the last exit code is
zero and logs are recent. Distinguish four states: not installed, loaded and idle, currently
running, and loaded with a failed last run.

Query the user launchd domain before checking transient processes.

Interpret log timestamps using the freshness guidance in `docs/upstream-sync.md`.

## Reporting

Report the resolved LaunchAgent label and domain, loaded/running state, run count, last exit code,
latest stdout/stderr timestamps, state-file timestamp, and whether an actual issue creation was
observed. Do not claim GitHub write success from `--dry-run` alone.
