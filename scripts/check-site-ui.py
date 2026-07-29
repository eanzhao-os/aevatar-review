#!/usr/bin/env python3
"""Validate the desktop chapter-tab wrapping contract in source and built HTML."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "mkdocs.yml"
WORKFLOW = ROOT / ".github/workflows/docs.yml"
CSS_RELATIVE = Path("stylesheets/extra.css")
CSS_SOURCE = ROOT / "docs" / CSS_RELATIVE
DESKTOP_MEDIA = "@media screen and (min-width: 76.25em)"
CURRENT_TOP_LEVEL_COUNT = 15


class TabsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tabs = False
        self.current_item: Optional[Dict[str, object]] = None
        self.in_link = False
        self.items: List[Dict[str, object]] = []
        self.stylesheets: List[str] = []
        self.icons: List[str] = []
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        rel = (attributes.get("rel") or "").split()
        if tag == "link" and "stylesheet" in rel:
            self.stylesheets.append(attributes.get("href") or "")
        if tag == "link" and "icon" in rel:
            self.icons.append(attributes.get("href") or "")
        if tag == "h1":
            self.h1_count += 1
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
    favicon = re.search(r"(?m)^\s+favicon:\s*(\S+)\s*$", config)
    if favicon is not None:
        favicon_path = ROOT / "docs" / favicon.group(1)
        require(
            favicon_path.is_file(),
            f"configured favicon does not exist: {favicon_path.relative_to(ROOT)}",
        )
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
    mermaid = declarations(css, ".md-typeset .mermaid")
    require(
        re.search(r"max-width\s*:\s*100%\s*;", mermaid) is not None,
        "Mermaid diagrams must stay within the article width",
    )
    require(
        re.search(r"overflow-x\s*:\s*auto\s*;", mermaid) is not None,
        "wide Mermaid diagrams must scroll inside their container",
    )
    desktop_rule = extract_balanced_rule(css, DESKTOP_MEDIA)
    tabs = declarations(desktop_rule, ".md-tabs")
    tab_list = declarations(desktop_rule, ".md-tabs__list")
    tab_item = declarations(desktop_rule, ".md-tabs__item")
    require(
        re.search(r"overflow\s*:\s*visible\s*;", tabs) is not None,
        ".md-tabs must expose wrapped rows",
    )
    require(
        re.search(r"flex-wrap\s*:\s*wrap\s*;", tab_list) is not None,
        ".md-tabs__list must wrap",
    )
    require(
        re.search(r"overflow\s*:\s*visible\s*;", tab_list) is not None,
        ".md-tabs__list must not scroll horizontally",
    )
    require(
        re.search(r"flex-shrink\s*:\s*0\s*;", tab_item) is not None,
        ".md-tabs__item labels must not collapse",
    )
    for forbidden in (
        "display: none",
        "visibility: hidden",
        "text-overflow: ellipsis",
        "00 序章",
        "12 问题复盘",
    ):
        require(
            forbidden not in css,
            f"navigation stylesheet contains forbidden hiding or hard-coded content: {forbidden}",
        )
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
    config = CONFIG.read_text(encoding="utf-8")
    site_url = re.search(r"(?m)^site_url:\s*(\S+)\s*$", config)
    require(site_url is not None, "mkdocs.yml has no site_url")
    site_prefix = urlparse(site_url.group(1)).path.rstrip("/") + "/"
    for page_path in site_dir.rglob("*.html"):
        page = TabsParser()
        page.feed(page_path.read_text(encoding="utf-8"))
        if page_path.name == "index.html":
            relative = page_path.relative_to(site_dir)
            require(
                page.h1_count == 1,
                f"built {relative} has {page.h1_count} h1 elements, expected 1",
            )
        for href in page.icons:
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path.startswith(site_prefix):
                icon = site_dir / parsed.path.removeprefix(site_prefix)
            else:
                icon = (page_path.parent / parsed.path).resolve()
            relative = page_path.relative_to(site_dir)
            require(icon.is_file(), f"built {relative} references missing icon: {href}")
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
