#!/usr/bin/env python3
"""Batch-fetch frozen closed issue details from aevatarAI/aevatar via GraphQL.

Reads .superpowers/task3/open-issues.tsv (number<TAB>title), writes
.superpowers/task3/open-details.json keyed by issue number with:
body, closed event closer (PR number/title/url/mergedAt or commit oid),
labels. Read-only against GitHub; retries gh TLS flakes.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TSV = ROOT / "open-issues.tsv"
OUT = ROOT / "open-details.json"

FIELDS = """
body
labels(first: 20) { nodes { name } }
timelineItems(itemTypes: [CLOSED_EVENT], last: 3) {
  nodes {
    ... on ClosedEvent {
      createdAt
      closer {
        __typename
        ... on PullRequest { number title url mergedAt }
        ... on Commit { oid url }
      }
    }
  }
}
"""


def run_graphql(query: str) -> dict:
    for attempt in range(5):
        proc = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode == 0:
            payload = json.loads(proc.stdout)
            if "errors" not in payload:
                return payload["data"]["repository"]
            err = payload["errors"]
        else:
            err = proc.stderr.strip()[:300]
        time.sleep(2 + attempt * 3)
    raise SystemExit(f"graphql failed after retries: {err}")


def main() -> None:
    numbers = [
        int(line.split("\t", 1)[0])
        for line in TSV.read_text().splitlines()
        if line.strip()
    ]
    result = {}
    batch_size = 25
    for start in range(0, len(numbers), batch_size):
        batch = numbers[start : start + batch_size]
        aliases = "\n".join(
            f'i{n}: issue(number: {n}) {{ {FIELDS} }}' for n in batch
        )
        query = (
            'query { repository(owner: "aevatarAI", name: "aevatar") {\n'
            + aliases
            + "\n} }"
        )
        data = run_graphql(query)
        for n in batch:
            node = data.get(f"i{n}")
            if node is None:
                raise SystemExit(f"issue {n} missing from response")
            result[str(n)] = node
        print(f"fetched {start + len(batch)}/{len(numbers)}", flush=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(f"wrote {OUT} with {len(result)} issues")


if __name__ == "__main__":
    main()
