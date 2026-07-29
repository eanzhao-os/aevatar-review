# Aevatar Review 全书最终验证报告

> 报告日期：2026-07-29
>
> Fresh-run 时间：2026-07-29T04:12:50Z–2026-07-29T04:38:02Z
>
> 文档验证 HEAD：`aee614ba89a7be426f4f6318327754f7541397f0`（本报告提交前）
>
> 唯一上游事实基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`

本报告是 2026-07-25 全库重构计划 Task 20 的验收记录。它区分“自动门禁已通过”、
“主代理语义复核已完成”和“独立子代理 reviewer 未成功创建”三类事实，不用其中一类替代另一类。
最终结构为 14 个 block、72 篇实质章节与 14 个 block index。

## 1. 验收范围与冻结边界

本轮只修改 `/Users/eanzhao/Code/aevatar-review`。Aevatar live working tree
`/Users/eanzhao/Code/aevatar` 只执行了 `git cat-file`、`rev-parse` 与 `status` 读操作；所有正文事实与
教程测试均读取派生冻结快照：

```text
/Users/eanzhao/Code/aevatar-review/.git/aevatar-frozen/
f02aa690bbebb9cabeac30a553d737486b0eb661
```

核验结果：

- `git -C /Users/eanzhao/Code/aevatar rev-parse f02aa690...^{commit}` 精确返回冻结 SHA。
- 冻结快照中的 `aevatar.slnx` 存在。
- Task 20 期间 live HEAD 从 `3ed4a28facbbdacaac0ed592a31d44491fab89ed` 漂移到
  `b0112600bfc6e08ec47c9bee52f05b7df4a4a15c`，live dirty 行数从 5 变为 2；这是外部并发变化，
  没有进入本文事实判断。
- 本任务没有对 live 上游执行 checkout、reset、stash、clean、格式化、生成或文件写入。
- 冻结目录是可重建的 `.git/` 派生缓存；`dotnet test` 可在其中产生 `bin/obj`，但它不是 SSOT，
  也没有修改 live 上游。

上游起始状态与受保护输入的完整记录见
[受保护工作区账本](2026-07-25-protected-worktree.md)。

## 2. 最终书目与迁移对账

| 项目 | 最终值 | 机械证据 |
|---|---:|---|
| Block | 14 | `00–13` |
| 实质章节 | 72 | `find 00 ... 13 -maxdepth 1 -name '[0-9][0-9]-*.md'` |
| Block index | 14 | 每个 block 一个 `index.md` |
| Active book Markdown | 86 | 72 章 + 14 index |
| Frontmatter status | 57 current / 12 mixed / 2 historical / 1 target | 逐章解析首个 YAML frontmatter |
| MkDocs 顶层导航 | 15 | 首页 + 14 block |
| current/mixed source-map | 69 | 与目标 manifest 精确集合相等 |
| 每个 source spine | 1–3 路径 | 69 个 mapping 均满足 |
| 旧文件迁移行 | 98 | 迁移账本逐行解析 |
| 旧路径删除 | 85 | retire list 85 行，工作树零残留 |
| 原位重写旧 index | 13 | `00–12/index.md` |
| 新增 block index | 1 | `13/index.md` |

98 个旧 Markdown 行的处置分布为：

| 处置 | 数量 |
|---|---:|
| `retain-rewrite` | 31 |
| `split` | 27 |
| `merge` | 11 |
| `move-evolution` | 6 |
| `promote-current` | 5 |
| `promote-current+split` | 2 |
| `delete` | 3 |
| `rewrite-in-place` | 13 |
| **合计** | **98** |

读者侧最终产物是 72 篇新结构章节；旧内容不是按文件一一复制，而是依上述处置拆分、合并、提升或
迁入演进层。完整逐行落点见
[旧章节迁移账本](2026-07-25-chapter-migration-ledger.md)。Task 19 的原子结构切换提交为
`474443b`，精确删除 85 个 retire path。

## 3. Issue 基线与分类守恒

Issue 成员使用冻结恢复结果，不重新以 live GitHub 状态生成：

```text
canonical cutoff: 2026-07-24T16:58:27Z
reconstruction interval: [2026-07-24T15:23:48Z, 2026-07-24T19:23:10Z)
closed: 154
open: 126
total: 280
```

Closed 分类：

| classification | 数量 |
|---|---:|
| `landed-current` | 113 |
| `failed/abandoned` | 17 |
| `administrative` | 16 |
| `landed-superseded` | 5 |
| `duplicate/replaced` | 1 |
| `ops-verified` | 1 |
| `design-only` | 1 |
| **合计** | **154** |

Open 分类：

| classification | 数量 |
|---|---:|
| `missing-contract` | 44 |
| `confirmed-bug` | 22 |
| `ops-ux-test` | 21 |
| `proposal/dispute` | 16 |
| `blocked/duplicate/tracking` | 15 |
| `security-debt` | 8 |
| **合计** | **126** |

`pending`、`unreviewed`、`unclassified` 在迁移治理文件中均为零。完整成员、逐行 evidence 与
destinations 见 [Issue 演进账本](2026-07-25-issue-evidence-ledger.md)；读者索引见
[13/04](../13/04-issue-evolution-index.md)。

## 4. Fresh 自动验证

### 4.1 环境

| 工具 | 版本 |
|---|---|
| Python | 3.9.6 |
| MkDocs | 1.6.1 |
| Material for MkDocs | 9.7.7 |
| Mermaid CLI | 11.15.0 |
| Git | 2.50.1 (Apple Git-155) |

MkDocs 环境安装在 `/tmp/aevatar-review-mkdocs-20260729`，不修改仓库依赖。仓库 CI 当前使用
未锁定的 `pip install mkdocs-material pymdown-extensions`；本地为复现此前构建证据，显式使用上述版本。

### 4.2 结果

| 命令 | 结果 |
|---|---|
| `bash scripts/tests/test-doc-checks.sh all` | exit 0；`frozen-upstream`、`issue-snapshot`、`issue-replay`、`issue-cli`、`validators` 全部 PASS |
| `AEVATAR_SRC="$AEVATAR_FROZEN" bash scripts/check-md.sh --all` | exit 0；86 个 active book 文件通过 |
| `python3 scripts/check-links.py --all` | exit 0；102 个文件通过 |
| `bash scripts/check-drift.sh` | exit 0；`check-drift: OK` |
| `python3 scripts/check-mermaid.py` | exit 0；184 个 Mermaid 块、123 个文件由 11.15.0 真解析 |
| `mkdocs build --strict --clean` | exit 0；MkDocs 1.6.1 / Material 9.7.7 构建成功 |
| `python3 scripts/check-site-ui.py` | exit 0；source + built site，15 个 tabs |
| source-map exact-set audit | 69 个 current/mixed 章节精确覆盖；每项 1–3 路径 |
| frontmatter/demo audit | 72 个章节均有唯一 frontmatter status 与唯一 Demo status |
| fact-source grouping audit | 72 章通过；超过 3 个路径的入口均显式说明分组边界 |
| retire-set audit | 85/85 已删除；Task 19 删除集合与 retire list 完全相等 |

第一次全书 Mermaid 进程的终端 session 被运行器回收，不能作为通过证据；随后使用持久日志与独立
退出码文件重跑。有效证据是 `/tmp/aevatar-review-mermaid-final.status = 0` 与日志末行的
`184 个 mermaid 块全部解析通过`。

## 5. 四个语义切片复核

### 5.1 复核方法与独立性限制

计划要求四个切片由独立 reviewer 复核。运行时支持显式选择
`chrono-llm/gpt-5.6-sol` 与 `reasoning_effort`；模型选择能力本身不是限制。实际 `spawn_agent` 调用在
多个继续回合均由工具返回 `missing field message`，校正尝试仍得到同一 schema 错误，且没有任何 agent ID
返回。依仓库 circuit breaker，未继续重试，也没有伪称 reviewer 已创建。

因此本轮独立性结论是：**没有独立子代理验收**。降级措施是主代理以两个不同方向做两遍复核：

1. 正向从章节读取 owner、协议、状态、不变量、成功边界与失败恢复；
2. 反向从冻结 source matrix、issue ledger、protected ledger 与源码 spine 回查章节落点。

自动门禁与两遍主代理复核能提供强证据，但不等价于独立 reviewer。FI-001 的这一缺口在此显式保留，
没有被“全绿”掩盖。

### 5.2 切片结论

| 切片 | 先查的 requirement failures | 结论 / resolution |
|---|---|---|
| `00–05` | message / StateEvent / command / query / committed fact / projection / ACK 是否互换；session observation 是否冒充耐久事实 | 未发现未解决的语义失败。HTTP/ACK 受理、actor commit、projection/read model 与实时 observation 已分层 |
| `06–07` | Scope/Team/Member/Draft/Revision/Service 身份；Conversation/Turn/NyxIdChat/Profile owner；retry 是否越权 | 未发现未解决的语义失败。产品身份、direct NyxIdChat、Channel run、archive 与 immutable profile 各自有 owner |
| `08–10` | raw secret/bytes 是否进入 durable fact；Channel/files/voice/Automation/security/production 是否越界；canary 是否外推 current | 未发现内容语义失败；修正了 `08/05`、`09/04`、`10/06` 的事实源分组说明，并收紧 source-map spine |
| `11–13` | 教程命令可复现性；historical/target 是否写成 current；issue/canon/ADR/index 是否丢行 | 未发现内容语义失败；修正了 `12/04` 的事实源分组说明；72 个 demo 全部保持 `verified-static` |

### 5.3 Task 20 发现与修复

| Finding | 修复 | 提交 |
|---|---|---|
| 站点校验仍期待 14 个顶层入口 | 改为首页 + 14 block = 15，并验证 built HTML | `0fd6746` |
| 5 个 source-map 条目含 4–5 个路径 | 收敛为每章 1–3 个触发 spine；69 项覆盖不变 | `4f9b7fe` |
| `08/05` 的 4 个事实源路径未解释分组 | 明确协议、volatile relay、Host 准入三边界 | `0751d66` |
| `09/04` 的 5 个事实源路径未解释分组 | 明确 schedule state、secret materialization、历史 repair 三边界 | `b9e9aeb` |
| `10/06` 的 5 个事实源路径未解释分组 | 明确 runtime contract、managed adapter、治理边界 | `abd2e3b` |
| `12/04` 的 4 个事实源路径未解释分组 | 明确 scope、tool ownership、schedule 三类事故边界 | `aee614b` |

每个章节修复均是单路径提交，并分别通过 `check-md --paths`、`check-links --paths` 与真实
Mermaid 解析。

## 6. Demo 诚实性审计

### 6.1 全书状态

72 篇实质章节各有且只有一个 Demo status，分布为：

```text
verified-static: 72
verified-local: 0
verified-production-versioned: 0
```

这是对“本轮 demo”的状态，不否认 `09/05` 正文引用了绑定 source/image/date/environment 的历史 E3。
历史 canary 没有被改写成本轮实际生产验证。

非教程章节按 block 汇总如下；“实际命令”是 Task 20 fresh 运行的验证，不代表启动了 Aevatar：

| 章节 | 数量 | 状态 | 本轮实际命令 | 未满足前提 / 不作出的承诺 |
|---|---:|---|---|---|
| `00/01–03` | 3 | verified-static | full-book gates + source/frontmatter audit | 不启动 Host，不把阅读/路径核对写成运行结果 |
| `01/01–04` | 4 | verified-static | full-book gates + frozen source validation | 缺 authenticated Host、唯一 scope、LLM；不声称 SSE E2E |
| `02/01–06` | 6 | verified-static | full-book gates + Mermaid | 不启动 Local/Orleans runtime 或 EventStore |
| `03/01–07` | 7 | verified-static | full-book gates + Mermaid | 不调用真实 connector/tool，不证明外部副作用 |
| `04/01–05` | 5 | verified-static | full-book gates + Mermaid | 不读取 LLM/MCP/NyxID credential，不执行真实 tool side effect |
| `05/01–06` | 6 | verified-static | full-book gates + Mermaid | 不写 Elasticsearch/stream provider，不测真实 projection latency |
| `06/01–05` | 5 | verified-static | full-book gates + Mermaid | 不创建/绑定/发布 Member，不把 201/202 当 terminal |
| `07/01–04` | 4 | verified-static | full-book gates + Mermaid | 不运行 NyxIdChat/Ornn/LLM，不测真实 retry/reconnect |
| `08/01–05` | 5 | verified-static | full-book gates + per-chapter fixes | 不连接 Lark/Voice，不上传文件，不声称 delivery |
| `09/01–05` | 5 | verified-static | full-book gates + per-chapter fixes | 不签发/revoke key，不等 cron，不访问 owner-only production evidence |
| `10/01–08` | 8 | verified-static | full-book gates + per-chapter fixes | 不启动集群、Kafka/Garnet/Chrono，不声称 production ready |
| `12/01–05` | 5 | verified-static | ledger conservation + full-book gates | 历史/E5 不晋级 current，不访问 live GitHub |
| `13/01–04` | 4 | verified-static | 72/82/280 行索引守恒 + full-book gates | 索引不替代 E1，不从 issue status 推断实现 |

### 6.2 五篇教程

| 教程 | 状态 | 本轮实际执行 | 结果 | 缺失前提 |
|---|---|---|---|---|
| `11/01` 最小 Workflow | verified-static | Ruby YAML shape check 读取冻结 `workflows/simple_qa.yaml` | `11/01 simple_qa-static: OK` | Standalone Host 未组合可用 authentication；无 bearer、唯一 scope、LLM provider |
| `11/02` 分支 Tool Workflow | verified-static | `dotnet test ... --filter FullyQualifiedName~WorkflowAsyncJobTemplateContractTests --no-restore` | 4/4 passed；0 failed；保留 NU1903/NU1510 告警 | 未调用 Firecrawl、未取 tool credential、未创建/禁用 schedule |
| `11/03` Team Member | verified-static | 用 `jq --rawfile` 从冻结 `simple_qa.yaml` 生成并验证 binding JSON | `11/03 member-bind-json-static: OK` | 无 authenticated Mainnet Host、scope、LLM、projection；未发 HTTP mutation |
| `11/04` Channel/files | verified-static | 生成并验证 snake_case registration JSON | `11/04 channel-registration-json-static: OK` | 无 Lark app、NyxID owner token、public HTTPS callback、ready Member |
| `11/05` Automation | verified-static | 生成并验证 preflight/create/delete 三种 JSON shape | `11/05 automation-json-static: OK` | 无 Host、owner credential、NyxID/Vault、真实 cron 或 owner-only evidence |

成功性措辞扫描只命中反例、问题句、带命令结果的 4/4 测试和版本化 canary 边界；没有把静态 demo
写成“已跑通”、端到端通过或当前生产验证。

## 7. 有意保留的不确定事实与上游缺口

本轮不确定项没有通过扩大结论消失：

- **Confirmed bugs（22）**：Studio/Console、Conversation/Workflow、production composition、
  Channel、Automation 与 Workflow observation 仍有冻结 open failure。
- **Security debt（8）**：secret store 兼容面、relay durable credential payload、对象级 read 授权、
  Automation credential source、Managed Codex allowlist/persistent key/宽 delegation 仍未闭合。
- **Missing contracts（44）**：Foundation wire guard、Workflow IO/debug/artifact、Studio identity/version、
  audit cursor、Channel files/Voice、Automation read side、Managed Codex authority、NyxIdChat stop/
  reconnect/steering/task lifecycle 等仍是 target。
- **Proposal / dispute（16）**：未用提案、Proposed ADR 或调查文本预支 current。
- **Ops / UX / test（21）**：发布证据、可达性、UI 诚实文案与测试覆盖不定义 runtime 语义。
- **Blocked / duplicate / tracking（15）**：只进入无损索引，不成为架构合同。

更具体的 owner、current limit、evidence 与 exit criterion 见
[12/05 开放缺口](../12/05-open-gaps-and-canon-drift.md)。

冻结 `dotnet test` 仍报告：

- `Microsoft.OpenApi 2.0.0`：NU1903 high-severity advisory；
- `SIPSorcery 8.0.23`：NU1903 high-severity advisory；
- 若干 `Microsoft.Extensions.*` PackageReference：NU1510。

这些是上游冻结基线告警；本仓库无权修改上游，也没有因 4/4 test passed 而宣称告警已解决。

## 8. 受保护输入与完成声明边界

- 85 个 retire path 在删除前均为 `migrated-reviewed`。
- protected canary、schedule 事故、`07/index.md`、`10/index.md`、`PLAN.md` 与 `mkdocs.yml`
  均有哈希、逐节落点和复核结论。
- `.superpowers/` 与 `CLAUDE_HANDOFF_PROMPT.md` 保持未跟踪、未修改、未提交；没有读取
  `.superpowers/brainstorm/.last-token`。
- `docs/13 -> ../13` 是仓库内相对 symlink。
- live Aevatar 上游没有本任务可归因写入。
- 独立子代理 reviewer 未创建；这是验收限制，不是完成项。模型可选性没有问题，失败发生在工具
  payload/schema 边界。

在本报告提交后仍必须重新执行 post-commit 全量门禁；只有该 fresh-run 与最终 refs 对账通过，才允许
把 `main` 推送到 `origin/main`。
