---
name: updating-aevatar-review-docs
description: Use when a user requests an aevatar-review documentation change for an Aevatar feature, module, protocol, flow, or technical detail.
---

# 补充 Aevatar Review 文档

只完成用户点名的主题；以固定上游快照为证据，验证后安全发布最小改动。

## 工作流

1. **守住发布基线。** 读取根 `AGENTS.md`、`PLAN.md` 和完整 `git status`。确认仓库身份、当前分支为 `main`，且不是 linked worktree。若 index 已有任何暂存改动，立即停止。执行 `git fetch origin main`；本地含任何尚未存在于 `origin/main` 的既有提交或双方分叉时停止。仅落后时可用 `git merge --ff-only origin/main`，然后记录 `BASE_SHA=$(git rev-parse origin/main)`。既有改动归用户所有；目标文件与其重叠时停止，禁止 stash、覆盖或顺带提交。

2. **固定事实树。** 执行 `git -C ~/Code/aevatar fetch origin feature/integrate`，只解析一次完整 `origin/feature/integrate` SHA。调用 `scripts/materialize-frozen-upstream.sh` 分别物化仓库批准的 frontmatter 冻结提交和本轮目标提交。任一 fetch、解析或快照失败即停止。所有新增事实从目标快照读取。禁止在上游执行 `pull`、`checkout`、`switch`、`reset`、`clean`、`stash` 或文件写入；其当前分支和脏工作树不得影响对象读取。

3. **定位最小落点。** 搜索用户术语及标识符、`PLAN.md`、现有章节、block index、`.config/upstream-sync/chapter-source-map.json` 和目标快照中的实现、contract、canon、ADR。优先补一个能够完整回答该读者问题的现有章节。只有形成独立职责边界且确实无处容纳时，才按根规则先输出 `SCOPE_EXTEND`、补 issue，再更新章节与必要导航。

4. **按仓库规则写作。** 保留批准的冻结 frontmatter；清楚标明本轮正文同步 SHA。用职责、边界、协议、状态、不变量和取舍解释设计；事实可回指真实路径与行号。维护至少两张合规 Mermaid 图、适用的最小示例，以及 current、target、historical/removed 的诚实区分。只改本主题与一致性必需文件。

5. **跑完双基准门禁。** 执行：

```bash
AEVATAR_SRC="$FROZEN_SNAPSHOT" AEVATAR_SRC2="$TARGET_SNAPSHOT" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
```

任一失败即停止；不得禁用测试或扩大范围掩盖无关失败。

6. **只发布本轮文件。** 用显式路径 `git add -- <paths>`，检查 `git diff --cached` 与暂存文件清单，再创建一个 `docs:` 提交。重新 `git fetch origin main`；只有 `origin/main` 仍等于 `BASE_SHA` 才执行 `git push origin HEAD:main`。随后用 `git ls-remote origin refs/heads/main` 确认远端 SHA 等于本地 `HEAD`。结果不明确时先 readback；不得盲目重试。远端推进或 push 拒绝时保留本地提交并停止，禁止 merge、rebase、force-push 或提交任何原有改动。
