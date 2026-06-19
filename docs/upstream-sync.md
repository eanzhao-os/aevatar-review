# upstream-sync watch loop —— 运维 runbook

> 让 aevatar-review 文档实时跟踪 aevatar 上游 `feature/integrate` 的设计性变更。
> 本文档是 host 工具 `scripts/upstream-sync.sh` 的唯一运维手册。

## 它做什么(一句话)

每 15 分钟 `git fetch` 上游 → diff 出新变更文件 → 查「章节↔上游路径」映射表 → 为受影响的章节**自动建一个 GitHub issue**(零 `crnd:` label)→ consensus-loop 的常驻 controller 通过 default-issue-intake(Path A)自动 claim,走 design-consensus → 实现 → review-gate → merge。

watch 脚本与 consensus-loop **只通过 GitHub issue 这个公共状态面耦合**,各自独立运行。

```
┌─────────────────────────────┐    gh issue create    ┌──────────────────────────────┐
│ upstream-sync.sh            │ ────────────────────► │ aevatar-review GitHub issues  │
│ (launchd, 15min)            │  零 crnd label         │ (label-free, 待 claim)        │
│                             │                        │                               │
│ 1. fetch upstream           │                        │ consensus-loop controller     │
│ 2. diff <state>..HEAD       │ ◄──────────────────── │ (常驻 wakeup-runner daemon)   │
│ 3. 反向索引匹配章节          │  poll gh issue list    │ → claim → consensus → merge   │
│ 4. 过滤 test/CI/chore        │                        │                               │
│ 5. 去重 + 建 issue           │                        │                               │
│ 6. 更新 state sha           │                        │                               │
└─────────────────────────────┘                        └──────────────────────────────┘
```

## 文件清单

| 文件 | 用途 | 是否进 git |
|---|---|---|
| `scripts/upstream-sync.sh` | watch 脚本本体(单次扫描,幂等) | ✅ |
| `.config/upstream-sync/chapter-source-map.json` | 章节↔上游路径映射表(host-owned 事实) | ✅ |
| `.config/upstream-sync/state.json` | 运行时状态(上次处理到的 sha + 已建 issue 记录) | ❌(gitignore) |
| `.config/consensus-rnd/host.env` | host 事实注入(含 `AEVATAR_UPSTREAM_ROOT` + `DEFAULT_ISSUE_INTAKE_AUTHOR_ALLOWLIST`) | ❌(gitignore,含本地路径) |
| `~/Library/LaunchAgents/com.eanzhao.aevatar-review.upstream-sync.plist` | launchd 调度(**由你手动安装**) | ❌(用户级) |

## 首次启用(3 步)

### 1. 确认 host.env 已含必需变量

`.config/consensus-rnd/host.env` 应已含(本仓库已预置):

```bash
export DEFAULT_ISSUE_INTAKE_AUTHOR_ALLOWLIST="eanzhao"   # 否则 consensus-loop 会拒掉所有自建 issue
export AEVATAR_UPSTREAM_ROOT="/Users/zhaoyiqi/Code/aevatar"  # 上游只读事实源
```

**为什么 `DEFAULT_ISSUE_INTAKE_AUTHOR_ALLOWLIST` 必须设**:consensus-loop 的 default-issue-intake 默认空值会 fail-closed 拒掉**所有** issue(包括 maintainer 自建)。这是 skill 契约(`default_issue_intake_admission.py` 的 `author_not_allowlisted` 分支)。不设这一行,整个 loop 跑不通。

### 2. 初始化基线(只做一次)

```bash
cd ~/Code/aevatar-review
export CONSENSUS_RND_HOST_ENV=.config/consensus-rnd/host.env
bash scripts/upstream-sync.sh --init
```

这会把当前上游 `origin/feature/integrate` 的 HEAD 记为基线,**不建任何 issue**。之后所有新 commit 才会被检测。

### 3.(可选)安装 launchd 调度

见下文「launchd 安装」段。不装也能用——手动跑 `bash scripts/upstream-sync.sh` 即可。

## 日常运维

### 手动跑一次同步

```bash
cd ~/Code/aevatar-review
export CONSENSUS_RND_HOST_ENV=.config/consensus-rnd/host.env
bash scripts/upstream-sync.sh
```

### 先看会建什么(dry-run,不真建)

```bash
bash scripts/upstream-sync.sh --dry-run
```

### 看日志

launchd 装好后,日志在:
```bash
tail -f ~/Library/Logs/aevatar-review-upstream-sync.log
tail -f ~/Library/Logs/aevatar-review-upstream-sync.err.log
```

### 看已建/待 claim 的 issue

```bash
gh issue list --label upstream-sync --state open
```

## 调映射表(最常见的调整)

映射表是 `.config/upstream-sync/chapter-source-map.json`,**单点调整,无需改脚本**。

### 误报太多(某章节被频繁触发,但实际不用改)

收紧该章节的路径条目。例如 `00/02-repo-map.md` 当前匹配整个 `src/`(任何 src 改动都触发),如果太吵,可改成只匹配结构性文件:

```json
"00/02-repo-map.md": {
  "paths": ["aevatar.slnx", "docs/canon/module-placement-map.md"]
}
```

### 漏报(某章节该触发却没触发)

在对应章节条目加上游路径前缀。例如某次 `src/Aevatar.AI.Projection/` 改了但没触发任何章节,检查 `04/*` 或 `05/*` 是否覆盖了它。

### 匹配规则(脚本内置)

- 条目以 `/` 结尾 → 上游文件**以此前缀开头**即命中(递归目录)
- 条目带文件扩展名 → **精确文件**命中
- 别名(纯 `NNNN-slug` 或 canon 关键字如 `architecture`)→ 先展开成 `docs/adr/NNNN-slug.md` / `docs/canon/<alias>.md` 再匹配

## 调节流旋钮(在 host.env)

consensus-loop 消化 issue 的速度受两个变量约束:

| 变量 | 默认 | 含义 | 调大/调小 |
|---|---|---|---|
| `DEFAULT_ISSUE_INTAKE_CLAIM_COOLDOWN_SECONDS` | `3600` | 两次 claim 之间最小间隔 | 调小→消化更快,但 consensus 算力消耗上升 |
| `DEFAULT_ISSUE_INTAKE_ACTIVE_DESIGN_CAP` | `3` | 同时处于 design-solving 的最大 issue 数 | 调大→并行度更高,但资源占用上升 |

**典型场景**:一次上游 push 触发 5 个 issue。默认行为:第 1 个立即 claim,其余每小时放一个,直到 3 个同时在 design-solving 时 cap 顶住。对"文档同步"这个低频场景,**默认值通常够用**。

## commit 过滤规则

脚本会过滤掉这些前缀的 commit(不触发 issue),因为它们不改设计语义:

```
chore:  test:  ci:  style:  revert:  perf:
```

**不过滤**(会触发):`feat:` `fix:` `refactor:` `docs(canon/adr):` 等可能改变设计的 commit。
注意 `docs(canon)` / `docs(adr)` 不过滤,因为 canon/adr 是事实源文档,改了就要看。

## 边界(对齐 AGENTS.md 与 consensus-loop 契约)

- **不改 `~/Code/aevatar` 任何文件**(AGENTS.md:只读事实源)
- **不改 consensus-loop skill 目录**(FI-002:skill host-agnostic)
- **issue 不预打 `crnd:` label**(skill 契约:预打会让 loop 跳过 `target_already_managed`)
- **不绕过 cooldown/cap**(skill 契约:节流是设计,不是 bug)
- **不自动装 launchd**(SKILL.md:OS 调度由 host operator 执行)
- **`host.env` 不进 git**(含本地路径,FI-002)

## 卸载

```bash
# 1. 卸 launchd(如装了)
launchctl unload ~/Library/LaunchAgents/com.eanzhao.aevatar-review.upstream-sync.plist
rm ~/Library/LaunchAgents/com.eanzhao.aevatar-review.upstream-sync.plist

# 2. 关掉 consensus-loop 对 upstream-sync issue 的 claim(host.env)
#    把 DEFAULT_ISSUE_INTAKE_ENABLE 改 false,或删除 DEFAULT_ISSUE_INTAKE_AUTHOR_ALLOWLIST

# 3.(可选)删脚本与配置
rm scripts/upstream-sync.sh
rm -rf .config/upstream-sync/
```

## launchd 安装(可选)

> **SKILL.md 边界**:consensus-loop skill / agent 不得写、装、删 launchd plist。下面的 plist 内容由你手动保存、手动 `launchctl load`。

把以下内容存为 `~/Library/LaunchAgents/com.eanzhao.aevatar-review.upstream-sync.plist`(把 `YOUR_HOME` 换成你的家目录,可用 `echo $HOME` 取):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.eanzhao.aevatar-review.upstream-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>YOUR_HOME/Code/aevatar-review/scripts/upstream-sync.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>YOUR_HOME/Code/aevatar-review</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CONSENSUS_RND_HOST_ENV</key>
        <string>.config/consensus-rnd/host.env</string>
        <key>HOME</key>
        <string>YOUR_HOME</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
    <key>StartInterval</key>
    <integer>900</integer>
    <key>StandardOutPath</key>
    <string>YOUR_HOME/Library/Logs/aevatar-review-upstream-sync.log</string>
    <key>StandardErrorPath</key>
    <string>YOUR_HOME/Library/Logs/aevatar-review-upstream-sync.err.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

安装 + 立即触发一次测试:

```bash
launchctl load ~/Library/LaunchAgents/com.eanzhao.aevatar-review.upstream-sync.plist
# 立即手动跑一次(不等 15 分钟)
launchctl start com.eanzhao.aevatar-review.upstream-sync
# 看日志
tail -f ~/Library/Logs/aevatar-review-upstream-sync.log
```

`StartInterval=900` = 每 15 分钟一次。嫌慢可改小(如 `300` = 5 分钟),但 fetch + diff 有成本,15 分钟是文档同步场景的合理默认。
