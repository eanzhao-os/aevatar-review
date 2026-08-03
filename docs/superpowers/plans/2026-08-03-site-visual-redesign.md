# Site Visual Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the crowded top chapter tabs with Material’s native sidebar and apply the approved bright mint visual system across the homepage and article UI without changing chapter URLs or content.

**Architecture:** Keep MkDocs Material and `mkdocs.yml` as the only navigation data source. Express the redesign through Material feature flags, the existing CSS entrypoint, and semantic homepage Markdown; update the dependency-free UI contract before production changes so the old layout demonstrably fails.

**Tech Stack:** MkDocs Material, CSS custom properties, Markdown with `md_in_html`, Python 3 standard library

## Global Constraints

- Work directly on `main`; do not create a branch or worktree.
- Do not modify anything under `~/Code/aevatar`.
- Preserve all 72 chapter files, 14 block indexes, URLs, anchors, nav order, and source claims.
- Do not add JavaScript, template overrides, images, frontend frameworks, or dependencies.
- Keep `mkdocs.yml` as the only complete navigation fact source.
- Preserve unrelated tracked and untracked user changes; stage only files named by this plan.
- Use the approved light colors `#F7FFFC`, `#E9FBF4`, `#08745B`, `#0EAF83`, and `#17352F`, plus a corresponding dark teal palette. Primary text contrast must be at least `4.5:1`; the bright accent does not carry text or keyboard focus by itself.
- Maintain keyboard focus, non-color selection cues, mobile drawer access, wide-content containment, and `prefers-reduced-motion` support.

---

### Task 1: Replace the top-tab regression contract

**Files:**

- Modify: `scripts/check-site-ui.py`
- Test: `scripts/check-site-ui.py --source-only`

**Interfaces:**

- Consumes: `mkdocs.yml`, `docs/stylesheets/extra.css`, `docs/index.md`, `.github/workflows/docs.yml`, and generated `site/**/*.html`.
- Produces: exit `0` only when source and built output implement the sidebar, mint-theme, and homepage contracts; failures retain the `check-site-ui: FAIL:` prefix.

- [ ] **Step 1: Rewrite source assertions for the approved behavior**

Keep the current standard-library parser and icon checks. Replace wrapped-tab assertions with these exact behaviors:

```python
require("navigation.tabs" not in config, "top navigation tabs must be disabled")
require("navigation.expand" not in config, "the sidebar must expand only the current section")
for scheme in ("aevatar-light", "aevatar-dark"):
    require(f"scheme: {scheme}" in config, f"missing custom palette scheme: {scheme}")
for token in ("--aevatar-bg", "--aevatar-sidebar", "--aevatar-primary", "--aevatar-accent"):
    require(token in css, f"missing visual token: {token}")
for selector in (".md-sidebar--primary", ".md-header", ".md-typeset .home-hero", ".md-typeset .route-grid"):
    require(selector in css, f"missing redesigned component: {selector}")
require("prefers-reduced-motion: reduce" in css, "missing reduced-motion support")
for marker in ("home-hero", "route-grid", "开始阅读", "查看阅读路线"):
    require(marker in homepage, f"homepage is missing: {marker}")
```

Extend the HTML parser with `primary_sidebars` and `tabs` counters. Built output must contain a primary sidebar, contain no `md-tabs` nav, load `stylesheets/extra.css`, and preserve exactly one H1 per index page.

- [ ] **Step 2: Run the new contract and verify RED**

Run:

```bash
python3 scripts/check-site-ui.py --source-only
```

Expected: exit `1` with `check-site-ui: FAIL: top navigation tabs must be disabled`. This proves the contract rejects the existing site for the intended reason.

- [ ] **Step 3: Commit the independently failing contract**

```bash
git add scripts/check-site-ui.py
git commit -m "test: define sidebar site design contract"
```

---

### Task 2: Implement the native sidebar and mint design

**Files:**

- Modify: `mkdocs.yml`
- Modify: `docs/stylesheets/extra.css`
- Modify: `docs/index.md`
- Test: `scripts/check-site-ui.py`

**Interfaces:**

- Consumes: Material’s `.md-header`, `.md-sidebar--primary`, `.md-content`, `.md-nav`, `.md-typeset`, and palette data-attribute contracts.
- Produces: sidebar-first navigation, custom light/dark mint palettes, styled document primitives, and homepage classes `home-hero`, `hero-actions`, `home-stats`, `route-grid`, and `route-card`.

- [ ] **Step 1: Switch Material to native sidebar navigation**

Remove only `navigation.tabs` and `navigation.expand` from `theme.features`. Keep `navigation.sections` and `navigation.indexes`. Rename the palette schemes to `aevatar-light` and `aevatar-dark` so the manual toggle changes a stable DOM attribute as well as respecting each entry’s `media` default.

- [ ] **Step 2: Replace old wrapped-tab CSS with the complete theme**

Define light tokens on `[data-md-color-scheme="aevatar-light"]` and dark tokens on `[data-md-color-scheme="aevatar-dark"]`. Map Material variables `--md-primary-fg-color`, `--md-accent-fg-color`, `--md-default-bg-color`, and text/code variables to the approved palette.

Style only existing Material contracts and homepage classes. Cover header, primary sidebar, active/hover/focus nav items, content width and typography, links, code, tables, admonitions, pagination, Mermaid overflow, homepage hero/actions/stats/routes, mobile breakpoints, and reduced motion. Delete all `.md-tabs` wrapping rules because tabs no longer render.

- [ ] **Step 3: Replace the homepage directory tables with focused entry points**

Keep one H1 and the frozen SHA claim. Add this structure and the exact required links:

```markdown
<div class="home-hero" markdown>
<span class="eyebrow">AEVATAR STRUCTURED GUIDE</span>

# Aevatar 结构化中文解读

从请求、Actor 与 Workflow 出发，看清系统边界、事实所有权与生产运行。

<div class="hero-actions" markdown>
[开始阅读](00/01-reading-guide.md){ .primary-action }
[查看阅读路线](#选择你的阅读路线){ .secondary-action }
</div>
</div>

## 选择你的阅读路线

<div class="route-grid" markdown>
<a class="route-card" href="01/01-quick-start/">快速上手 …</a>
<a class="route-card" href="02/01-agent-actor-runtime/">理解架构 …</a>
<a class="route-card" href="11/01-run-a-simple-workflow/">实践与查证 …</a>
</div>
```

Add a `home-stats` row for 14 blocks, 72 chapters, and frozen evidence; retain concise status definitions, the upstream boundary warning, PLAN link, and README link. Do not reproduce the complete block directory.

- [ ] **Step 4: Run the focused source contract and verify GREEN**

```bash
python3 scripts/check-site-ui.py --source-only
```

Expected: `check-site-ui: OK (source contract)`.

- [ ] **Step 5: Build and verify generated output**

```bash
mkdocs build --strict --clean
python3 scripts/check-site-ui.py
```

Expected: build exit `0` and `check-site-ui: OK (source + built site, sidebar=present, tabs=0)`.

- [ ] **Step 6: Commit the complete visual implementation**

```bash
git add mkdocs.yml docs/stylesheets/extra.css docs/index.md
git commit -m "feat: redesign documentation site"
```

---

### Task 3: Verify real pages and release main

**Files:**

- Verify only; no planned production changes.

**Interfaces:**

- Consumes: the built local site and all repository-provided gates.
- Produces: current evidence for desktop/mobile rendering, structural validity, and a fast-forward push of `main` to `origin/main`.

- [ ] **Step 1: Inspect representative pages in a real browser**

Serve `site/` locally and inspect `/` plus `/03/03-execution-kernel-and-outcomes/` at desktop and mobile widths. Confirm the desktop sidebar is visible, top tabs are absent, primary actions and route cards are readable, current chapter and page TOC remain visible, no horizontal page overflow occurs, and the mobile drawer opens.

- [ ] **Step 2: Run every repository gate fresh**

```bash
AEVATAR_SRC="$FROZEN_AEVATAR_ARCHIVE" AEVATAR_SRC2="$HOME/Code/aevatar" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
python3 scripts/check-site-ui.py
git diff --check origin/main..HEAD
```

Use the repository’s existing frozen archive location for `FROZEN_AEVATAR_ARCHIVE`; if absent, materialize it with `scripts/materialize-frozen-upstream.sh`. Every command must exit `0` before release.

- [ ] **Step 3: Verify scope, remote ancestry, and upstream immutability**

```bash
git status --short --branch
git diff --name-only origin/main..HEAD
git -C ~/Code/aevatar status --short
git fetch origin main
git merge-base --is-ancestor origin/main HEAD
```

Confirm task commits contain only the design, plan, UI checker, config, CSS, and homepage. Existing unrelated dirt remains untracked or unstaged. The read-only upstream has no task-caused changes, and the push is fast-forward.

- [ ] **Step 4: Push the verified main branch**

```bash
git push origin main
```

Read back `git status --short --branch` and `git rev-parse HEAD origin/main`; the two SHAs must match.
