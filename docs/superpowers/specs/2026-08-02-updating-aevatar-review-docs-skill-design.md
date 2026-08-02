# Aevatar Review 文档更新 Skill 设计

> 批准日期：2026-08-02
>
> 适用仓库：`~/Code/aevatar-review`
>
> 只读事实源：`~/Code/aevatar` 的 `origin/feature/integrate`
>
> 产物位置：`.agents/skills/updating-aevatar-review-docs/`

## 1. 目标

为本仓库提供一个项目专用 skill。当用户表达“更新文档”“同步 aevatar 后修订文档”或“检查文档是否落后于上游”等意图时，Codex 必须先同步 `origin/feature/integrate` 的远端引用，再以固定提交的只读快照为事实源修订或增加中文章节。

每轮更新同时解决三个问题：

1. 审查上次文档基线之后的全部上游变化，更新受影响章节；
2. 枚举目标快照中的架构能力，补回没有明确文档归属的既有 feature；
3. 调度一个全新上下文的独立 reviewer，复核本轮改动和 6 篇旧正文，使多轮更新最终覆盖全书。

“尽可能记录所有 feature 和实现细节”以架构可理解性为边界：覆盖职责、协议、状态、不变量、授权、持久化、失败与恢复、运行拓扑和关键实现取舍；不把逐文件或逐方法清单当作正文。

## 2. 方案选择

### 方案 A：轻量 skill 加确定性辅助脚本（采用）

`SKILL.md` 承担语义判断，辅助脚本承担 Git、快照、差异事实包、映射和抽样。复用仓库已有脚本，不重复实现文档门禁或快照生成。

优点是安全边界明确、结果可测试、重复调用稳定；代价是 skill 目录中需要维护一个小脚本。

### 方案 B：纯 `SKILL.md`（未采用）

每次由 agent 临时拼装 Git、抽样和状态命令。文件较少，但容易在多次调用间产生状态格式和失败语义漂移。

### 方案 C：全自动文档生成程序（未采用）

把 feature 分类、章节归属和写作编码成程序。它无法可靠替代架构语义判断，还会复制 agent 和现有脚本的职责。

## 3. 文件与职责

```text
.agents/skills/updating-aevatar-review-docs/
├── SKILL.md
├── agents/openai.yaml
└── scripts/prepare-update.py

.config/aevatar-doc-update/
└── state.json
```

- `SKILL.md`：规定触发条件、主流程、证据要求、新章节扩展、独立复核、失败边界和完成条件。
- `agents/openai.yaml`：提供仓库内 skill 的展示名、简述和默认调用提示。
- `prepare-update.py`：执行安全 fetch、固定目标 SHA、生成冻结快照、输出增量事实包、列出架构候选、选择旧正文复核样本，并在成功后更新状态。
- `.config/aevatar-doc-update/state.json`：仓库级、可提交的跨 turn 权威记录。skill 私有目录不保存文档基线或覆盖台账。

复用现有组件：

- `scripts/materialize-frozen-upstream.sh` 生成只读提交快照；
- `.config/upstream-sync/chapter-source-map.json` 提供章节到源码路径的导航映射；
- `scripts/check-md.sh`、`scripts/check-links.py`、`scripts/check-drift.sh`、`scripts/check-mermaid.py` 和 `mkdocs build --strict` 承担现有质量门禁；
- `scripts/upstream-sync.sh` 继续服务定时 issue watch loop，其未提交的运行状态不作为“文档已经同步”的证据。

## 4. 上游同步与事实快照

同步只允许以下操作：

1. 校验 `~/Code/aevatar` 是 Git 仓库且存在 `origin`；
2. 执行 `git fetch origin feature/integrate`；
3. 解析完整的 `origin/feature/integrate` commit SHA；
4. 从该提交对象生成只读冻结快照；
5. 后续扫描、引用校验和写作都读取该快照。

不得对上游执行 `pull`、`checkout`、`switch`、`reset`、`clean`、`stash` 或任何文件写入。上游工作树脏、位于其他分支或 detached HEAD 都不得触发“整理”动作，也不阻止从远端引用读取提交对象。

每轮开始即固定一个目标 SHA。即使同步过程中远端继续推进，本轮也不移动目标；后续提交留给下一轮。

### 4.1 非快进改写

若旧 `documented_upstream_sha` 不是目标 SHA 的祖先：

- 旧提交对象仍存在时，明确报告 history rewrite，并比较旧树与新树的最终差异；
- 旧对象不存在时停止，不推断缺失历史，也不推进文档基线。

## 5. 更新事实包

`prepare-update.py` 产出机器可读 JSON，并在终端给出简洁摘要。事实包至少包含：

- 文档基线 SHA、目标 SHA、祖先关系和是否发生 history rewrite；
- 提交列表，包括 merge、fix、test、docs、删除和重命名；
- changed files 及其状态；
- 由章节映射命中的现有章节；
- 未被章节映射覆盖的上游路径；
- 目标快照中的架构候选及其现有文档命中情况；
- 本轮应交给独立 reviewer 的 6 篇旧正文。

提交前缀不能替代语义判断。`test`、`fix`、`docs` 或 `chore` 变化可能揭示真实协议、失败语义或部署边界，因此事实包不做设计性提交过滤。章节映射也只负责导航；未命中映射不能被解释为“无需更新”。

### 5.1 架构候选

候选扫描面至少包括：

- solution/project 与模块边界；
- Host、Agent/GAgent 和 runtime；
- proto、公开 contract、endpoint 和消息协议；
- Tool Provider、Connector 和 Workflow primitive；
- 持久化、Projection、授权、配置与运行拓扑实现；
- `docs/canon/*` 和 `docs/adr/*`。

脚本只列出候选和搜索命中，不判断“是否值得单独成章”。主 agent 必须结合已有章节、读者问题和职责边界作出判断。

## 6. 主更新流程

1. 确认当前目录和仓库身份，读取 `AGENTS.md`、`PLAN.md`、`mkdocs.yml`、章节映射、状态及当前工作树 diff。
2. 运行辅助脚本的 prepare 阶段，固定目标 SHA、生成冻结快照和事实包。
3. 逐项检查全部 commit、changed files、映射结果、未覆盖路径和架构候选。
4. 对已有能力，修改最少数量的现有章节，并同步事实源入口、设计图、示例、状态标记和相关索引。
5. 对新职责边界或独立读者问题，按第 7 节扩展新章节。
6. 调度一个全新上下文、只读的独立 reviewer，审查本轮全部变更章节和抽中的 6 篇旧正文。
7. 修复 findings；存在 blocking finding 时，由同一 reviewer 复核修订。
8. 执行全量文档门禁。
9. 全部通过后调用辅助脚本的 commit-state 阶段，原子推进文档基线和覆盖台账。

即使目标 SHA 与文档基线相同，也执行旧正文抽样复核和全量门禁。

## 7. 自动扩展新章节

当一项能力无法合理归入现有章节，且形成独立职责边界、协议或读者问题时，主 agent 自动完成扩章，不等待额外确认：

1. 搜索现有正文、`PLAN.md` 和 GitHub issues，排除重复主题；
2. 在最合适的现有 block 中选择下一个合法编号和 slug；
3. 创建 chapter GitHub issue，写明目标 SHA、高价值事实源、目标路径、范围和读者验收问题；
4. issue 创建成功后，新增正文并更新 `PLAN.md`、`mkdocs.yml`、block `index.md`、章节映射以及受影响的计数和索引；
5. 按普通章节要求加入至少两张 Mermaid 图，并论证“为什么采用当前设计，而不是其他选择”。

Issue 创建是一次有外部副作用的操作。调用失败或返回不明确时，先按标题、目标路径和目标 SHA readback：

- 已存在唯一匹配 issue：复用它；
- 明确不存在：只允许一次经诊断后的创建尝试；
- 仍无法判定：停止扩章，不留下正文或导航的半成品。

## 8. 独立复核与轮转覆盖

每轮更新只调度一个全新上下文的独立 reviewer。它不得参与本轮写作，只能读取文档、目标冻结快照和必要的仓库规则；作者的结论不能作为事实输入。

Reviewer 范围包括：

- 本轮全部新增或修改的章节；
- 由脚本选出的 6 篇旧正文。

Reviewer 按章节返回 `blocking` 和 `non-blocking` findings。事实错误、遗漏关键架构边界、把目标态写成当前实现、无证据论断、损坏的图或导航属于 blocking。存在 blocking finding 时不能推进状态。

### 8.1 抽样算法

旧正文选择顺序为：

1. 排除本轮已经新增或修改的章节；
2. 按 `review_count` 升序，优先覆盖审查次数最低的章节；
3. 同计数按 `last_reviewed_at` 升序，未审查视为最早；
4. 仍相同时，以目标 SHA 为种子做稳定打散；
5. 默认选择 6 篇。大规模增量时，主 agent 可以减少数量，但不得降为 0，并须在结果中说明。

只有 reviewer 通过的旧正文才增加 `review_count`。所有正文的最小 `review_count` 增加一次，代表完成一轮全书覆盖。新章节从 `review_count: 0` 开始，因此会在后续轮次优先进入抽样。

## 9. 状态模型与提交时机

`.config/aevatar-doc-update/state.json` 采用版本化 JSON：

```json
{
  "schema_version": 1,
  "documented_upstream_sha": "f02aa690bbebb9cabeac30a553d737486b0eb661",
  "last_successful_update_at": "2026-08-02T00:00:00Z",
  "chapters": {
    "02/01-agent-actor-runtime.md": {
      "review_count": 1,
      "last_reviewed_sha": "f02aa690bbebb9cabeac30a553d737486b0eb661",
      "last_reviewed_at": "2026-08-02T00:00:00Z",
      "result": "pass"
    }
  }
}
```

初次启用时，以当前文档明确声明的冻结上游 SHA 初始化 `documented_upstream_sha`；若无法唯一解析，停止并报告，不能直接把最新远端 SHA 当作“已经记录”。所有现有普通章节以 `review_count: 0` 初始化。

Prepare 阶段不改状态。只有以下条件全部满足后才原子替换状态文件：

- 本轮所有目标章节已经完成；
- 独立 reviewer 没有未关闭的 blocking finding；
- 全量门禁通过；
- 新章节 issue 均有可核验编号。

任一阶段失败都保留旧状态，使下一次调用能够从同一基线完整重试。

## 10. 工作树与权限边界

- `~/Code/aevatar` 永久只读。
- 当前文档仓库的既有改动均视为用户所有；目标文件有重叠修改时，先读取 diff 并做局部合并，无法确认所有权则停止该文件。
- skill 默认不 commit、push、merge 或安装后台调度。
- 默认允许的外部写操作只有新章节所需的 GitHub issue；其他 issue、PR、通知和发布不在范围内。
- 独立 reviewer 不修改文件，不创建 issue，不推进状态。

## 11. 失败处理

- fetch 失败：报告错误并停止，不读取可能过期的远端引用作为最新事实。
- 快照失败：停止，不回退到上游 live working tree。
- 基线对象缺失：停止，不猜测提交区间。
- `gh` 未认证或 issue 结果不明确：按第 7 节 readback；仍不明确则停止扩章。
- reviewer 不可用：停止，不以作者自审替代独立复核。
- blocking finding 未关闭：不推进状态。
- 任一门禁失败：保留旧状态，并在交付中列明失败命令和最小诊断。

## 12. 测试与验证

### 12.1 Skill 的 RED-GREEN-REFACTOR

创建 skill 前，用独立 agent 在没有该 skill 的情况下执行包含时间压力、脏上游工作树、遗漏映射和 GitHub 副作用的真实场景，记录它实际省略或误做的步骤。最小 skill 只针对观察到的失败编写，再用相同场景复测并关闭新漏洞。

### 12.2 辅助脚本测试

使用临时合成 Git 仓库留下一个最小可运行测试，覆盖：

- fetch 后解析远端目标 SHA，但不修改上游工作树；
- 正常增量与非快进树差异；
- 冻结快照调用；
- changed files、章节映射和未覆盖路径；
- 以目标 SHA 为种子的稳定抽样；
- prepare 失败和门禁失败时不推进状态；
- commit-state 成功时原子更新状态。

### 12.3 仓库验收

- skill 元数据通过 `skill-creator` 的 `quick_validate.py`；
- 在当前仓库执行一次不写文档、不建 issue、不推进状态的 dry-run 前向测试；
- 对实际 skill 行为做一次独立 agent 前向测试；
- 最终执行：

```bash
AEVATAR_SRC="$TARGET_SNAPSHOT" bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
```

## 13. 完成定义

- 仓库内 skill 可被显式调用，且根 `AGENTS.md` 明确登记“更新文档”类触发规则；
- 上游同步只 fetch 并读取 commit 对象，测试证明不会改变上游工作树；
- 每轮都生成完整增量事实包和架构候选覆盖报告；
- 已有能力被修订到正确章节，新独立能力会先建 issue 再完整接入导航与索引；
- 每轮由一个独立 reviewer 检查所有本轮变更及默认 6 篇旧正文；
- 覆盖台账可跨 turn 累积，并以最低 `review_count` 衡量全书轮次；
- 任何失败都不会错误推进 `documented_upstream_sha` 或审查计数；
- 全量文档门禁通过。

## 14. 非目标

- 不修改、整理或提交 `~/Code/aevatar`；
- 不把 skill 变成后台 daemon 或 OS scheduler；
- 不自动 commit、push、开 PR 或部署站点；
- 不以代码目录镜像替代面向读者问题的章节结构；
- 不为语义写作建立新的生成框架或长期服务。
