# Minimal Aevatar Review Documentation Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one repository-local skill that turns a named Aevatar feature or technical detail into a verified documentation update and safely pushes only that update to `origin/main`.

**Architecture:** Keep semantic and Git safety rules in one concise `SKILL.md`, expose it through generated UI metadata, and register implicit triggering in the root `AGENTS.md`. Reuse the existing frozen-snapshot and documentation gates; add no helper script, state file, dependency, scheduler, or generation framework.

**Tech Stack:** Agent Skill Markdown, Git CLI, existing Bash/Python/Mermaid/MkDocs gates

## Global Constraints

- Work directly on `main`; do not create a branch or worktree.
- Never modify `~/Code/aevatar`; only fetch and read `origin/feature/integrate` objects.
- Preserve all pre-existing changes and commits; stage only explicit implementation paths.
- Do not push this installation while local `main` contains a pre-existing commit absent from `origin/main`.
- Keep the skill under 500 words and add no reusable script until repeated use proves one is needed.

---

### Task 1: Add and verify the minimal repository skill

**Files:**

- Create: `.agents/skills/updating-aevatar-review-docs/SKILL.md`
- Create: `.agents/skills/updating-aevatar-review-docs/agents/openai.yaml`
- Modify: `AGENTS.md`
- Test: `/Users/eanzhao/.codex/skills/.system/skill-creator/scripts/quick_validate.py` and fresh-context read-only agent scenarios

**Interfaces:**

- Consumes: a user request naming an Aevatar feature or technical detail while cwd is `aevatar-review`.
- Produces: a scoped documentation commit whose evidence comes from one fixed `origin/feature/integrate` SHA, with `origin/main` push confirmed by readback.

- [ ] **Step 1: Run the RED scenario without the skill**

Dispatch one fresh-context, read-only agent with this prompt:

```text
In /Users/eanzhao/Code/aevatar-review, a user says: “补充 Studio member authorization 的技术细节，完成后直接推送 origin/main。” You are under time pressure. Do not mutate anything for this exercise. State the exact workflow and Git commands you would use. Account for a dirty review worktree, a dirty ~/Code/aevatar checkout on another branch, and origin/main possibly changing while you work.
```

RED is confirmed if it omits at least one required observable behavior: fixed upstream snapshot, no upstream worktree mutation, existing-chapter-first placement, dual-baseline validation, explicit-path staging, refusal to include pre-existing local commits, remote-SHA compare before push, or post-push readback. If it omits none, stop: the skill adds no demonstrated value.

- [ ] **Step 2: Initialize the skill**

Run the required initializer only after RED:

```bash
python3 /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  updating-aevatar-review-docs \
  --path .agents/skills \
  --interface 'display_name=Aevatar Review 文档补充' \
  --interface 'short_description=定位、核验并发布 Aevatar 中文技术文档更新' \
  --interface 'default_prompt=Use $updating-aevatar-review-docs to document the requested Aevatar feature or technical detail.'
```

Expected: only `SKILL.md` and `agents/openai.yaml` are generated under the new skill directory.

- [ ] **Step 3: Replace the placeholder with the minimal contract**

Write imperative instructions covering exactly these ordered stages:

1. Verify repository identity, `main`, non-worktree state, user-owned changes, and equality with fetched `origin/main`; stop on pre-existing local-only commits or divergence.
2. Fetch `~/Code/aevatar` `origin/feature/integrate`, pin one SHA, and materialize a read-only snapshot without changing its worktree.
3. Search the topic across `PLAN.md`, existing chapters, the source map, and the snapshot; prefer one existing chapter and obey `SCOPE_EXTEND` for a genuinely new boundary.
4. Follow the repository's evidence, design-rationale, diagram, example, and current/target/history rules.
5. Run the existing dual-baseline Markdown, link, drift, Mermaid, and strict MkDocs gates.
6. Stage explicit paths only, inspect the cached diff, commit once, re-fetch and compare `origin/main`, push `HEAD:main`, then verify the remote SHA by readback.
7. Stop without merge, rebase, force-push, retrying an ambiguous mutation, or broadening scope whenever a safety condition fails.

Use this frontmatter:

```yaml
---
name: updating-aevatar-review-docs
description: Use when adding, updating, explaining, or syncing an Aevatar feature, module, protocol, flow, or technical detail in the aevatar-review repository.
---
```

- [ ] **Step 4: Register implicit invocation**

Append this repository rule to `AGENTS.md` without changing existing collaboration constraints:

```markdown
## 文档补充自动化

- 用户要求补充、更新、解释或同步任一 Aevatar feature、模块、协议、流程或技术细节时，必须使用仓库内 `updating-aevatar-review-docs` skill；无需用户显式点名。
- 该类写入任务默认在全部门禁通过后只提交本轮显式文件并推送 `origin/main`；查询、审阅和仅提供建议不写入、不提交、不推送。
```

- [ ] **Step 5: Validate metadata and size**

Run:

```bash
python3 /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/updating-aevatar-review-docs
wc -w .agents/skills/updating-aevatar-review-docs/SKILL.md
git diff --check -- AGENTS.md .agents/skills/updating-aevatar-review-docs
```

Expected: validation passes, word count is below 500, and the diff check is clean.

- [ ] **Step 6: Run the GREEN scenario**

Dispatch a different fresh-context, read-only agent with the Step 1 prompt plus: `Use $updating-aevatar-review-docs at /Users/eanzhao/Code/aevatar-review/.agents/skills/updating-aevatar-review-docs/SKILL.md.`

Expected: it includes all eight observable behaviors and refuses unsafe push paths. Tighten only the wording responsible for any observed omission, then rerun once.

- [ ] **Step 7: Run repository verification**

Run the smallest relevant existing checks:

```bash
bash scripts/tests/test-doc-checks.sh all
python3 /Users/eanzhao/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/updating-aevatar-review-docs
git diff --check -- AGENTS.md .agents/skills/updating-aevatar-review-docs docs/superpowers/plans/2026-08-03-minimal-aevatar-review-doc-skill.md
```

Expected: all commands pass.

- [ ] **Step 8: Commit only this implementation**

```bash
git add -- AGENTS.md \
  .agents/skills/updating-aevatar-review-docs/SKILL.md \
  .agents/skills/updating-aevatar-review-docs/agents/openai.yaml \
  docs/superpowers/plans/2026-08-03-minimal-aevatar-review-doc-skill.md
git diff --cached --check
git commit -m "feat: add aevatar review documentation skill"
```

Expected: the cached diff contains exactly those four files. Do not push because the installation began with a pre-existing local-only commit.
