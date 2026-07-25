# Chapter Navigation Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all 14 top-level chapter entries directly visible in a wrapped, two-row desktop tab bar while preserving Material's narrow-screen drawer navigation.

**Architecture:** Keep `mkdocs.yml` as the only navigation data source and add one narrowly scoped desktop stylesheet through `extra_css`. Protect the behavior with a dependency-free Python check that validates the source contract and the generated MkDocs HTML, then run that check in the Pages build after `mkdocs build`.

**Tech Stack:** MkDocs Material, CSS flexbox/media queries, Python 3 standard library, GitHub Actions YAML

## Global Constraints

- Do not modify any file under `~/Code/aevatar`; it is a read-only fact source.
- Do not modify chapter Markdown, URLs, or the `nav` hierarchy.
- `mkdocs.yml` remains the only navigation fact source; do not hard-code chapter names in CSS, JavaScript, or templates.
- Desktop layout must expose all current 14 top-level entries at `1280px`, `1440px`, and wider viewports without horizontal scrolling.
- Preserve Material's own `max-width: 76.234375em` narrow-screen behavior; the custom rule starts at `min-width: 76.25em`.
- Do not add JavaScript, theme overrides, or a second navigation model.
- Preserve all pre-existing user changes and commits.

## File Map

- Create `scripts/check-site-ui.py`: dependency-free source and generated-HTML regression check for the navigation contract.
- Create `docs/stylesheets/extra.css`: desktop-only wrapped tabs layout; no navigation content.
- Modify `mkdocs.yml`: load `stylesheets/extra.css` through `extra_css`.
- Modify `.github/workflows/docs.yml`: run the generated-site UI check immediately after the strict MkDocs build.

---

### Task 1: Add the failing navigation regression check

**Files:**

- Create: `scripts/check-site-ui.py`

**Interfaces:**

- Consumes: repository-root `mkdocs.yml`, `.github/workflows/docs.yml`, `docs/stylesheets/extra.css`, and optional generated `site/index.html`.
- Produces: CLI `python3 scripts/check-site-ui.py [--source-only] [--site-dir PATH]`; exit code `0` means the wrapping contract is present, nonzero prints one actionable `check-site-ui: FAIL: ...` message.

- [ ] **Step 1: Write the failing check**

Create `scripts/check-site-ui.py` with this complete implementation:

```python
#!/usr/bin/env python3
"""Validate the desktop chapter-tab wrapping contract in source and built HTML."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "mkdocs.yml"
WORKFLOW = ROOT / ".github/workflows/docs.yml"
CSS_RELATIVE = Path("stylesheets/extra.css")
CSS_SOURCE = ROOT / "docs" / CSS_RELATIVE
DESKTOP_MEDIA = "@media screen and (min-width: 76.25em)"
CURRENT_TOP_LEVEL_COUNT = 14


class TabsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tabs = False
        self.current_item: Optional[Dict[str, object]] = None
        self.in_link = False
        self.items: List[Dict[str, object]] = []
        self.stylesheets: List[str] = []

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "link" and "stylesheet" in (attributes.get("rel") or "").split():
            self.stylesheets.append(attributes.get("href") or "")
        if tag == "nav" and "md-tabs" in classes:
            self.in_tabs = True
        elif self.in_tabs and tag == "li" and "md-tabs__item" in classes:
            self.current_item = {"href": "", "text": []}
            self.items.append(self.current_item)
        elif self.current_item is not None and tag == "a":
            self.current_item["href"] = attributes.get("href") or ""
            self.in_link = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.in_link = False
        elif tag == "li":
            self.current_item = None
        elif tag == "nav" and self.in_tabs:
            self.in_tabs = False

    def handle_data(self, data: str) -> None:
        if self.in_link and self.current_item is not None:
            text = self.current_item["text"]
            assert isinstance(text, list)
            text.append(data)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_balanced_rule(css: str, header: str) -> str:
    start = css.find(header)
    require(start >= 0, f"missing desktop media rule: {header}")
    opening = css.find("{", start)
    require(opening >= 0, f"media rule has no opening brace: {header}")
    depth = 0
    for index in range(opening, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[opening + 1 : index]
    raise AssertionError(f"media rule has no closing brace: {header}")


def declarations(rule: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^{{}}]*)\}}", rule, re.DOTALL)
    require(match is not None, f"missing selector inside desktop media rule: {selector}")
    return match.group(1)


def top_level_nav_count(config: str) -> int:
    lines = config.splitlines()
    nav_index = next((i for i, line in enumerate(lines) if line == "nav:"), -1)
    require(nav_index >= 0, "mkdocs.yml has no top-level nav section")
    return sum(1 for line in lines[nav_index + 1 :] if re.match(r"^  - \S", line))


def validate_source() -> int:
    config = CONFIG.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(
        re.search(r"(?m)^extra_css:\s*$[\s\S]*?^  - stylesheets/extra\.css\s*$", config)
        is not None,
        "mkdocs.yml must load stylesheets/extra.css through extra_css",
    )
    require(CSS_SOURCE.is_file(), "missing docs/stylesheets/extra.css")
    require(
        "python3 scripts/check-site-ui.py" in workflow,
        "docs workflow must run python3 scripts/check-site-ui.py after the build",
    )
    require(
        top_level_nav_count(config) == CURRENT_TOP_LEVEL_COUNT,
        f"expected {CURRENT_TOP_LEVEL_COUNT} current top-level nav entries",
    )

    css = CSS_SOURCE.read_text(encoding="utf-8")
    desktop_rule = extract_balanced_rule(css, DESKTOP_MEDIA)
    tabs = declarations(desktop_rule, ".md-tabs")
    tab_list = declarations(desktop_rule, ".md-tabs__list")
    tab_item = declarations(desktop_rule, ".md-tabs__item")
    require(re.search(r"overflow\s*:\s*visible\s*;", tabs) is not None, ".md-tabs must expose wrapped rows")
    require(re.search(r"flex-wrap\s*:\s*wrap\s*;", tab_list) is not None, ".md-tabs__list must wrap")
    require(re.search(r"overflow\s*:\s*visible\s*;", tab_list) is not None, ".md-tabs__list must not scroll horizontally")
    require(re.search(r"flex-shrink\s*:\s*0\s*;", tab_item) is not None, ".md-tabs__item labels must not collapse")
    for forbidden in ("display: none", "visibility: hidden", "text-overflow: ellipsis", "00 序章", "12 问题复盘"):
        require(forbidden not in css, f"navigation stylesheet contains forbidden hiding or hard-coded content: {forbidden}")
    return CURRENT_TOP_LEVEL_COUNT


def validate_built_site(site_dir: Path, expected_count: int) -> None:
    index = site_dir / "index.html"
    require(index.is_file(), f"missing built site entry: {index}")
    parser = TabsParser()
    parser.feed(index.read_text(encoding="utf-8"))
    require(
        any(href.endswith(CSS_RELATIVE.as_posix()) for href in parser.stylesheets),
        "built index.html does not load stylesheets/extra.css",
    )
    require(
        len(parser.items) == expected_count,
        f"built index.html has {len(parser.items)} top-level tabs, expected {expected_count}",
    )
    for position, item in enumerate(parser.items, start=1):
        text_parts = item["text"]
        assert isinstance(text_parts, list)
        require("".join(text_parts).strip() != "", f"tab {position} has no visible label")
        require(bool(item["href"]), f"tab {position} has no link target")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--site-dir", type=Path, default=ROOT / "site")
    args = parser.parse_args()
    try:
        count = validate_source()
        if not args.source_only:
            validate_built_site(args.site_dir, count)
    except (AssertionError, OSError) as error:
        print(f"check-site-ui: FAIL: {error}", file=sys.stderr)
        return 1
    scope = "source contract" if args.source_only else f"source + built site, tabs={count}"
    print(f"check-site-ui: OK ({scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the check and verify RED**

Run:

```bash
python3 scripts/check-site-ui.py --source-only
```

Expected: exit `1` with `check-site-ui: FAIL: mkdocs.yml must load stylesheets/extra.css through extra_css`.

Do not create CSS or edit MkDocs configuration before observing this failure.

---

### Task 2: Implement the wrapped desktop tabs and wire the gate into CI

**Files:**

- Create: `docs/stylesheets/extra.css`
- Modify: `mkdocs.yml:53`
- Modify: `.github/workflows/docs.yml:45-48`
- Test: `scripts/check-site-ui.py`

**Interfaces:**

- Consumes: Material's existing `.md-tabs`, `.md-tabs__list`, and `.md-tabs__item` DOM contract plus the check created in Task 1.
- Produces: `stylesheets/extra.css` loaded by every built page; desktop tabs wrap without changing generated navigation content; CI validates the source and generated HTML contract.

- [ ] **Step 1: Add the minimal desktop-only stylesheet**

Create `docs/stylesheets/extra.css`:

```css
/* Keep every top-level chapter visible when Material renders desktop tabs. */
@media screen and (min-width: 76.25em) {
  .md-tabs {
    overflow: visible;
  }

  .md-tabs__list {
    flex-wrap: wrap;
    overflow: visible;
  }

  .md-tabs__item {
    flex-shrink: 0;
  }
}
```

- [ ] **Step 2: Load the stylesheet from the existing navigation fact source**

Insert after the `extra:` block in `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css
```

Do not change the `nav:` tree or any chapter label.

- [ ] **Step 3: Run the source check and observe the remaining CI-gate failure**

Run:

```bash
python3 scripts/check-site-ui.py --source-only
```

Expected: exit `1` with `check-site-ui: FAIL: docs workflow must run python3 scripts/check-site-ui.py after the build`.

- [ ] **Step 4: Add the generated-site check after the strict build**

Insert in `.github/workflows/docs.yml` immediately after `Build site`:

```yaml
      - name: Validate site navigation layout
        run: python3 scripts/check-site-ui.py
```

- [ ] **Step 5: Verify the source contract is GREEN**

Run:

```bash
python3 scripts/check-site-ui.py --source-only
```

Expected: `check-site-ui: OK (source contract)`.

- [ ] **Step 6: Build the real site and verify generated HTML**

Create an isolated temporary environment and run the exact CI build path:

```bash
python3 -m venv /tmp/aevatar-review-mkdocs-venv
/tmp/aevatar-review-mkdocs-venv/bin/pip install mkdocs-material pymdown-extensions
/tmp/aevatar-review-mkdocs-venv/bin/mkdocs build --strict --clean
python3 scripts/check-site-ui.py
```

Expected: MkDocs exits `0`, then `check-site-ui: OK (source + built site, tabs=14)`.

- [ ] **Step 7: Commit the independently testable UI fix**

```bash
git add scripts/check-site-ui.py docs/stylesheets/extra.css mkdocs.yml .github/workflows/docs.yml
git commit -m "fix: show every chapter in desktop navigation"
```

---

### Task 3: Run repository gates and inspect the final change boundary

**Files:**

- Verify only; no expected production-file changes.

**Interfaces:**

- Consumes: the complete Task 2 implementation and repository-provided validation commands.
- Produces: fresh evidence that the UI fix builds, preserves chapter checks, and does not touch the read-only upstream repository.

- [ ] **Step 1: Re-run the focused UI gate**

```bash
python3 scripts/check-site-ui.py --source-only
python3 scripts/check-site-ui.py
```

Expected: both commands print `check-site-ui: OK`.

- [ ] **Step 2: Run Markdown and Mermaid gates**

```bash
bash scripts/check-md.sh
python3 scripts/check-mermaid.py
```

Expected: both exit `0`. If an unrelated pre-existing failure appears, capture its exact file and message rather than changing chapter content in this UI task.

- [ ] **Step 3: Re-run the strict site build from a clean output directory**

```bash
/tmp/aevatar-review-mkdocs-venv/bin/mkdocs build --strict --clean
python3 scripts/check-site-ui.py
```

Expected: strict build exits `0`; generated HTML check reports `tabs=14`.

- [ ] **Step 4: Inspect scope and whitespace**

```bash
git diff --check HEAD~1..HEAD
git show --stat --oneline HEAD
git status --short --branch
git -C ~/Code/aevatar status --short
```

Expected: the UI commit contains only the four planned files; no whitespace errors; `~/Code/aevatar` has no changes caused by this task. Existing unrelated upstream/worktree dirt must be reported, not modified.

- [ ] **Step 5: Record browser-validation limits accurately**

Try the configured in-app browser once against the locally served build. If no browser backend is available, do not substitute another browser-control surface; report that visual automation was unavailable and cite the generated-HTML/CSS contract plus strict build as the completed verification evidence.
