#!/usr/bin/env python3
"""Validate the sidebar-first mint theme in source and built HTML."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "mkdocs.yml"
WORKFLOW = ROOT / ".github/workflows/docs.yml"
HOMEPAGE = ROOT / "docs" / "index.md"
CSS_RELATIVE = Path("stylesheets/extra.css")
CSS_SOURCE = ROOT / "docs" / CSS_RELATIVE
CURRENT_TOP_LEVEL_COUNT = 15


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: List[str] = []
        self.icons: List[str] = []
        self.h1_count = 0
        self.primary_sidebars = 0
        self.tabs = 0

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
        if "md-sidebar--primary" in classes:
            self.primary_sidebars += 1
        if tag == "nav" and "md-tabs" in classes:
            self.tabs += 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def top_level_nav_count(config: str) -> int:
    lines = config.splitlines()
    nav_index = next((i for i, line in enumerate(lines) if line == "nav:"), -1)
    require(nav_index >= 0, "mkdocs.yml has no top-level nav section")
    return sum(1 for line in lines[nav_index + 1 :] if re.match(r"^  - \S", line))


def feature_enabled(config: str, feature: str) -> bool:
    return re.search(rf"(?m)^\s+- {re.escape(feature)}\s*$", config) is not None


def validate_source() -> int:
    config = CONFIG.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    homepage = HOMEPAGE.read_text(encoding="utf-8")
    css = CSS_SOURCE.read_text(encoding="utf-8")

    require(
        re.search(r"(?m)^extra_css:\s*$[\s\S]*?^  - stylesheets/extra\.css\s*$", config)
        is not None,
        "mkdocs.yml must load stylesheets/extra.css through extra_css",
    )
    require(
        "python3 scripts/check-site-ui.py" in workflow,
        "docs workflow must validate the built site UI",
    )
    require(
        top_level_nav_count(config) == CURRENT_TOP_LEVEL_COUNT,
        f"expected {CURRENT_TOP_LEVEL_COUNT} current top-level nav entries",
    )
    require(not feature_enabled(config, "navigation.tabs"), "top navigation tabs must be disabled")
    require(
        not feature_enabled(config, "navigation.expand"),
        "the sidebar must expand only the current section",
    )
    require(feature_enabled(config, "navigation.sections"), "sidebar sections must remain enabled")
    require(feature_enabled(config, "navigation.indexes"), "section index pages must remain enabled")
    for scheme in ("aevatar-light", "aevatar-dark"):
        require(
            f"scheme: {scheme}" in config,
            f"missing custom palette scheme: {scheme}",
        )

    for token in (
        "--aevatar-bg",
        "--aevatar-sidebar",
        "--aevatar-primary",
        "--aevatar-accent",
    ):
        require(token in css, f"missing visual token: {token}")
    for selector in (
        ".md-sidebar--primary",
        ".md-header",
        ".md-typeset .home-hero",
        ".md-typeset .route-grid",
    ):
        require(selector in css, f"missing redesigned component: {selector}")
    require(".md-tabs" not in css, "obsolete top-tab styling must be removed")
    require("prefers-reduced-motion: reduce" in css, "missing reduced-motion support")
    require(
        re.search(r"\.md-typeset \.mermaid\s*\{[^}]*overflow-x\s*:\s*auto", css, re.DOTALL)
        is not None,
        "wide Mermaid diagrams must scroll inside their container",
    )

    for marker in ("home-hero", "route-grid", "开始阅读", "查看阅读路线"):
        require(marker in homepage, f"homepage is missing: {marker}")
    require(
        len(re.findall(r"(?m)^# \S", homepage)) == 1,
        "homepage Markdown must contain exactly one H1",
    )
    require(
        homepage.count('class="route-card"') == 3,
        "homepage must contain exactly three reading-route cards",
    )
    return CURRENT_TOP_LEVEL_COUNT


def resolve_asset(site_dir: Path, page_path: Path, href: str, site_prefix: str) -> Path:
    parsed = urlparse(href)
    if parsed.path.startswith(site_prefix):
        return site_dir / parsed.path.removeprefix(site_prefix)
    return (page_path.parent / parsed.path).resolve()


def validate_built_site(site_dir: Path) -> None:
    index = site_dir / "index.html"
    require(index.is_file(), f"missing built site entry: {index}")
    index_html = index.read_text(encoding="utf-8")
    homepage = SiteParser()
    homepage.feed(index_html)
    require(
        any(href.endswith(CSS_RELATIVE.as_posix()) for href in homepage.stylesheets),
        "built index.html does not load stylesheets/extra.css",
    )
    require(homepage.primary_sidebars > 0, "built index.html has no primary sidebar")
    require(homepage.tabs == 0, "built index.html still renders top navigation tabs")
    require(homepage.h1_count == 1, "built index.html must contain exactly one H1")
    require('class="home-hero"' in index_html, "built homepage has no hero")
    require(
        index_html.count('class="route-card"') == 3,
        "built homepage must contain exactly three reading-route cards",
    )

    config = CONFIG.read_text(encoding="utf-8")
    site_url = re.search(r"(?m)^site_url:\s*(\S+)\s*$", config)
    require(site_url is not None, "mkdocs.yml has no site_url")
    site_prefix = urlparse(site_url.group(1)).path.rstrip("/") + "/"
    for page_path in site_dir.rglob("*.html"):
        page = SiteParser()
        page.feed(page_path.read_text(encoding="utf-8"))
        relative = page_path.relative_to(site_dir)
        if page_path.name == "index.html":
            require(page.h1_count == 1, f"built {relative} must contain exactly one H1")
            require(page.primary_sidebars > 0, f"built {relative} has no primary sidebar")
            require(page.tabs == 0, f"built {relative} still renders top navigation tabs")
        for href in page.icons:
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc:
                continue
            icon = resolve_asset(site_dir, page_path, href, site_prefix)
            require(icon.is_file(), f"built {relative} references missing icon: {href}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--site-dir", type=Path, default=ROOT / "site")
    args = parser.parse_args()
    try:
        validate_source()
        if not args.source_only:
            validate_built_site(args.site_dir)
    except (AssertionError, OSError) as error:
        print(f"check-site-ui: FAIL: {error}", file=sys.stderr)
        return 1
    scope = (
        "source contract"
        if args.source_only
        else "source + built site, sidebar=present, tabs=0"
    )
    print(f"check-site-ui: OK ({scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
