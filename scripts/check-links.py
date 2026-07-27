#!/usr/bin/env python3
"""Validate in-repository Markdown links, images and heading anchors.

    python3 scripts/check-links.py [--all | --paths PATH...] [--allow-planned]
                                   [--repo-root PATH]

External links (``http:``, ``https:``, ``mailto:`` …) are out of scope: this gate
answers "does the book link to itself correctly", not "is the internet up".

``--allow-planned`` accepts a link whose target is a chapter listed in the target
manifest but not written yet. It exists only for the migration window, when
chapters land one commit at a time; final verification runs without it.

Reports ``file:line -> broken target`` and exits 1 if anything is unresolved.
Python standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

MANIFEST = "docs/migration/2026-07-25-target-chapters.md"
MANIFEST_ROW = re.compile(r"^- \[[ x]\] `([0-9]{2}/[0-9]{2}-[a-z0-9-]+\.md)` — status:")

# Inline link or image: [text](target) / ![alt](target). Reference-style links and
# bare autolinks are not used by this book.
LINK = re.compile(r"!?\[(?:[^\]\[]|\[[^\]]*\])*\]\(\s*<?([^)\s<>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
HTML_ID = re.compile(r"""(?:id|name)\s*=\s*["']([^"']+)["']""")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
EXTERNAL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def strip_code_spans(line: str) -> str:
    """Blank out inline code spans so links inside them are not scanned."""
    out = []
    index = 0
    length = len(line)
    while index < length:
        if line[index] == "`":
            ticks = 0
            while index + ticks < length and line[index + ticks] == "`":
                ticks += 1
            marker = "`" * ticks
            close = line.find(marker, index + ticks)
            if close == -1:
                out.append(" " * (length - index))
                break
            out.append(" " * (close + ticks - index))
            index = close + ticks
            continue
        out.append(line[index])
        index += 1
    return "".join(out)


def slugify(text: str) -> str:
    """Approximate the MkDocs/Python-Markdown 'toc' slug for a heading."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> their text
    text = text.replace("`", "")
    text = re.sub(r"<[^>]+>", "", text)
    text = unicodedata.normalize("NFKC", text)
    out = []
    for char in text.lower():
        if char.isalnum() or char in "_-":
            out.append(char)
        elif char.isspace():
            out.append("-")
        # everything else is dropped, matching the default slugify
    slug = "".join(out).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def anchors_of(path: Path) -> Set[str]:
    anchors: Set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return anchors
    fence: Optional[str] = None
    for line in lines:
        opener = FENCE.match(line)
        if opener is not None:
            marker = opener.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue
        heading = HEADING.match(line)
        if heading is not None:
            text = heading.group(2)
            anchors.add(slugify(text))
            # Also accept the raw heading text, which is how this book links to
            # Chinese sections in practice.
            anchors.add(text.strip().replace("`", ""))
        for found in HTML_ID.findall(line):
            anchors.add(found)
    return anchors


def collect_links(path: Path) -> List[Tuple[int, str]]:
    found: List[Tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return found
    fence: Optional[str] = None
    for number, line in enumerate(lines, start=1):
        opener = FENCE.match(line)
        if opener is not None:
            marker = opener.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue
        for target in LINK.findall(strip_code_spans(line)):
            found.append((number, target))
    return found


def site_view(root: Path, path: Path) -> Path:
    """Return where MkDocs sees this file.

    Chapter blocks live at the repository root and are exposed to MkDocs through
    relative symlinks (``docs/03 -> ../03``). A link like ``../assets/x.png``
    written inside ``03/01-….md`` therefore resolves against ``docs/03/``, not
    against the repository root. Checking the raw tree instead would report a
    working site link as broken.
    """
    try:
        rel = path.relative_to(root)
    except ValueError:
        return path
    parts = rel.parts
    if not parts or parts[0] == "docs":
        return path
    if (root / "docs" / parts[0]).exists():
        return root / "docs" / rel
    return path


def repo_form(root: Path, logical: str) -> str:
    """Normalise a ``docs/<block>/…`` site path back to its repository path."""
    rel = os.path.relpath(logical, str(root))
    parts = rel.split(os.sep)
    if len(parts) > 2 and parts[0] == "docs" and (root / "docs" / parts[1]).is_symlink():
        return "/".join(parts[1:])
    return rel.replace(os.sep, "/")


def markdown_files(root: Path) -> List[Path]:
    skip = {".git", ".refactor-loop", ".worktrees", "site", "node_modules"}
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for name in filenames:
            if name.endswith(".md"):
                out.append(Path(dirpath) / name)
    return sorted(out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--paths", nargs="*", default=None)
    parser.add_argument("--allow-planned", action="store_true")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    if not root.is_dir():
        print(f"check-links: FAIL: repo root not found: {root}", file=sys.stderr)
        return 1

    planned: Set[str] = set()
    manifest = root / MANIFEST
    if manifest.is_file():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            match = MANIFEST_ROW.match(line)
            if match:
                planned.add(match.group(1))

    if args.paths:
        selected = [root / p for p in args.paths]
    elif args.all:
        selected = markdown_files(root)
    else:
        print("check-links: FAIL: pass --all or --paths PATH...", file=sys.stderr)
        return 1

    anchor_cache: Dict[Path, Set[str]] = {}
    problems: List[str] = []
    checked = 0

    for path in selected:
        if not path.is_file():
            problems.append(f"{path}: file not found")
            continue
        checked += 1
        for number, raw in collect_links(path):
            target = raw.strip()
            if not target or target.startswith("#"):
                fragment = target[1:] if target.startswith("#") else ""
                if fragment:
                    if path not in anchor_cache:
                        anchor_cache[path] = anchors_of(path)
                    if fragment not in anchor_cache[path] and _decode(fragment) not in anchor_cache[path]:
                        rel = path.relative_to(root)
                        problems.append(f"{rel}:{number} -> missing heading fragment #{fragment}")
                continue
            if EXTERNAL.match(target) or target.startswith("//"):
                continue

            file_part, _, fragment = target.partition("#")
            fragment = _decode(fragment)
            if not file_part:
                continue
            base = site_view(root, path).parent
            logical = os.path.normpath(os.path.join(str(base), _decode(file_part)))
            resolved = Path(logical)
            rel = path.relative_to(root)
            inside = repo_form(root, logical)
            if inside.startswith(".."):
                problems.append(f"{rel}:{number} -> target escapes the repository: {target}")
                continue

            if not resolved.exists():
                if args.allow_planned and inside in planned:
                    continue
                problems.append(f"{rel}:{number} -> broken target: {inside}")
                continue

            if fragment and resolved.is_file() and resolved.suffix == ".md":
                if resolved not in anchor_cache:
                    anchor_cache[resolved] = anchors_of(resolved)
                available = anchor_cache[resolved]
                if fragment not in available and slugify(fragment) not in available:
                    problems.append(f"{rel}:{number} -> missing heading fragment: {inside}#{fragment}")

    if problems:
        print(f"check-links: FAIL ({len(problems)} unresolved)", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"check-links: OK ({checked} files)")
    return 0


def _decode(value: str) -> str:
    from urllib.parse import unquote

    return unquote(value)


if __name__ == "__main__":
    raise SystemExit(main())
