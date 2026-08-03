# Aevatar Review 文档持续更新 Skill 设计

> 确认日期：2026-08-03
>
> 适用仓库：~/Code/aevatar-review
>
> 只读事实源：~/Code/aevatar 的 origin/feature/integrate

## 1. 目标

让仓库文档同时满足两个目标：

1. **准确**：任何当前实现论断都来自同一个固定上游提交；完整更新不会漏掉同步水位之后的提交、未映射路径或新架构边界；AI 写作必须经过独立复核和现有门禁。
2. **快速**：日常只扫描真实增量或用户点名主题，优先补充现有章节；Git 事实整理、状态推进和轮转抽样由一个确定性脚本完成，语义判断仍交给 agent。

准确性是完成门槛。速度来自减少重复扫描、缩小写作范围、复用现有脚本，以及让旧正文复核与主 agent 写作并行，而不是跳过证据或门禁。

“尽可能记录所有 feature 和实现细节”以架构可理解性为边界：覆盖职责、边界、协议、状态、不变量、授权、持久化、失败恢复、运行拓扑和关键取舍；不把逐文件、逐类型或逐方法清单写成正文。

## 2. 采用方案

采用“薄 Skill + 一个 Python 标准库辅助脚本 + 一个仓库状态文件”：

~~~text
.agents/skills/updating-aevatar-review-docs/
├── SKILL.md
├── agents/openai.yaml
└── scripts/prepare-update.py

.config/aevatar-doc-update/state.json
.superpowers/aevatar-doc-update/       # 忽略的事实包和测试运行目录
~~~

- SKILL.md 负责触发、语义决策、写作、扩章、独立复核、门禁和发布编排。
- prepare-update.py 只负责可机械验证的 Git、映射、候选枚举、稳定抽样和状态转换。
- state.json 是跨 turn 的同步水位和复核覆盖权威记录；运行时临时目录不能替代它。
- agents/openai.yaml 提供仓库内 Skill 的展示元数据。

复用以下既有能力，不重复实现：

- scripts/materialize-frozen-upstream.sh：物化只读提交快照；
- .config/upstream-sync/chapter-source-map.json：章节与源码区域的导航映射；
- scripts/check-md.sh、scripts/check-links.py、scripts/check-drift.sh、scripts/check-mermaid.py 和 MkDocs：现有文档门禁；
- PLAN.md 与 mkdocs.yml：活跃书目和站点导航。

首版不改 CI、pre-push 或现有验证器。只有真实测试证明它们无法消费双基准或活跃 PLAN 时，才做最小兼容修改。

## 3. 触发与两种模式

根 AGENTS.md 继续负责自然语言触发。用户无需显式点名 Skill。

### 3.1 完整同步模式

当用户说“更新文档”“同步文档”“检查文档是否落后于上游”等没有限定单一主题的请求时：

- 扫描 synced_upstream_sha..target_sha 的完整提交和文件变化；
- 检查未映射路径和目标树中的架构候选；
- 修订所有真正受影响的章节，必要时自动扩章；
- 独立复核通过且全部门禁成功后，推进 synced_upstream_sha。

提交前缀不能作为过滤条件。merge、test、docs、fix 和 chore 都可能改变协议、失败语义或部署边界。

### 3.2 点题更新模式

当用户点名一个 feature、模块、协议、流程或实现细节时：

- 固定最新上游目标 SHA；
- 只搜索并更新该主题及一致性所需文件；
- 仍执行独立轮转复核和全量门禁；
- 可以更新通过复核的章节覆盖记录，但不得推进 synced_upstream_sha，也不得宣称全书已经同步到目标 SHA。

点题更新之后，下一次完整同步仍从旧同步水位扫描全部增量。重复命中的已更新内容由 agent 判断为已覆盖，不会丢失其他变化。

查询、审阅或仅要求建议时可以读取 Skill，但不写文档、不创建 issue、不推进状态，也不提交或推送。

## 4. 双基准与状态模型

仓库保持两个不同事实：

- frozen_upstream_sha / frozen_verified_at：普通章节 frontmatter 的冻结、可回放证据基线，更新流程永不修改；
- synced_upstream_sha：最近一次完整同步已经逐项审查到的正文水位。

初始值保持：

~~~text
frozen_upstream_sha = f02aa690bbebb9cabeac30a553d737486b0eb661
frozen_verified_at  = 2026-07-25
synced_upstream_sha = f02aa690bbebb9cabeac30a553d737486b0eb661
~~~

因此第一次完整更新必须扫描冻结提交之后的全部变化；既有零散正文更新不能冒充完整水位。

状态文件采用版本化 JSON，至少包含：

~~~json
{
  "schema_version": 1,
  "frozen_upstream_sha": "f02aa690bbebb9cabeac30a553d737486b0eb661",
  "frozen_verified_at": "2026-07-25",
  "synced_upstream_sha": "f02aa690bbebb9cabeac30a553d737486b0eb661",
  "last_successful_update_at": null,
  "chapters": {
    "02/01-agent-actor-runtime.md": {
      "review_count": 0,
      "last_reviewed_sha": null,
      "last_reviewed_at": null,
      "result": null
    }
  }
}
~~~

所有现有实质章节以 review_count 为 0 初始化。新章节同样从 0 开始，因而会在后续轮次优先被抽中。

## 5. 安全准备与事实包

### 5.1 仓库发布基线

开始写入前：

1. 确认当前仓库、main 分支和非 linked-worktree 状态；
2. 读取完整 git status，把所有既有修改视为用户所有；
3. fetch 当前仓库 origin/main 并记录 BASE_SHA；
4. 本地含尚未存在于 origin/main 的既有提交、发生分叉，或目标文件已有不明修改时停止；
5. 非重叠的用户修改可以保留，但永远不得被暂存或提交。

### 5.2 上游只读同步

上游只允许：

~~~bash
git -C ~/Code/aevatar fetch origin feature/integrate
~~~

随后只解析一次完整 origin/feature/integrate SHA，并从 Git 对象物化冻结基线和目标提交两个只读快照。本轮目标固定，即使远端继续推进也不移动。

禁止在上游执行 pull、checkout、switch、reset、clean、stash 或文件写入。上游当前分支、detached HEAD 和脏工作树都不得触发整理动作，也不影响读取远端提交对象。

### 5.3 辅助脚本边界

prepare-update.py 提供四个小命令：

- init-state：从 PLAN.md 初始化状态；
- prepare：fetch、固定 SHA、物化快照并输出事实包，不修改文档、issue 或状态；
- select-review：在语义修改范围固定后选择旧正文样本；
- commit-state：验证事实包、复核结果和门禁证据后原子更新状态。

事实包至少包含：

- 模式、冻结 SHA、同步水位、目标 SHA、状态文件旧哈希和事实包哈希；
- 完整 commit 列表及 changed files；
- source map 命中的章节和未覆盖路径；
- 目标快照中的架构候选与现有正文搜索命中；
- 计划语义修改章节、最终语义修改章节和旧正文复核样本；
- 新章节对应的唯一 GitHub issue 证据。

source map 只是加速导航，未命中不能解释为“无需更新”。候选面至少包括 solution/project、Host、Agent/GAgent、runtime、proto、公开 contract、endpoint、Tool Provider、Connector、Workflow primitive、持久化、Projection、授权、配置、运行拓扑、canon 和 ADR。

若同步水位不是目标 SHA 的祖先，脚本明确报告 history rewrite。旧对象存在时提供树差异但不自动推进；旧对象缺失时直接停止，禁止猜测历史。

## 6. 章节定位与自动扩章

主 agent 综合用户主题、提交变化、changed files、PLAN.md、现有正文、block index、source map、目标快照实现、canon 和 ADR 判断落点。

优先修改能够完整回答读者问题的最少数量现有章节。只有一项能力形成独立职责边界、协议或读者问题，且现有章节无法合理承接时才扩章。

扩章顺序固定：

1. 输出 SCOPE_EXTEND；
2. 搜索 PLAN.md、现有正文和全部 GitHub issues，排除重复主题；
3. 选定 block、下一个合法编号、slug 和目标路径；
4. 创建 chapter issue，写明目标 SHA、范围、高价值事实源、目标文件和读者验收问题；
5. readback 确认唯一 issue 后，继续写新章节；
6. 同步 PLAN.md、mkdocs.yml、block index、source map 以及受影响的计数和索引。

Issue 创建属于有副作用的操作。结果失败或不明确时，先按标题、目标路径和目标 SHA readback：唯一匹配则复用；明确不存在才允许一次经诊断的创建；仍无法判断则停止，不盲目重试，也不留下正文或导航半成品。

## 7. 写作契约

每篇语义变更章节必须：

- 以目标快照为当前事实源，同时保留冻结 frontmatter；
- 开头提供不超过 3 条高价值事实源入口，正文用设计语言解释职责、边界、协议、状态和不变量；
- 论证“为什么采用它，而不是替代方案”；无法证明时标记“设计待论证”并登记 TODO；
- 普通章节最终至少有两张符合仓库语法约束的 Mermaid 图；
- 适用时提供最小 YAML、协议或调用示例；
- 明确区分当前实现、目标态、历史和已移除组件；
- 只修改本主题、受真实增量影响的内容以及保持导航一致所必需的文件。

路径和行号用于事实入口与验证，不把实现文件或行号表当作正文骨架。

## 8. 独立轮转复核

每次写入更新自动调度一个全新上下文、只读且未参与写作的 reviewer。它只读取文档、固定目标快照、必要仓库规则和明确的 scope_paths，不创建 issue、不修改文件、不推进状态。

当计划语义修改范围固定后，select-review 排除这些章节并选择最多 6 篇旧正文：

1. review_count 最低优先；
2. 同计数时 last_reviewed_at 最早优先，未审查视为最早；
3. 仍相同时以目标 SHA 做稳定散列打散。

这满足“随机抽查”的覆盖目的，同时结果可重现。旧正文复核可与主 agent 写作并行；正文完成后，同一 reviewer 再检查本轮全部最终语义修改章节。若实际修改范围扩大，必须重新计算排除集并补足样本。

Reviewer 按章节返回 blocking 和 non-blocking findings。以下至少属于 blocking：

- 事实与目标快照不符或无证据；
- 漏掉关键职责、协议、状态或失败边界；
- 把目标态或历史组件写成当前实现；
- Mermaid、示例、导航或链接损坏；
- 新章节缺少唯一 issue 或未完整接入书目。

Blocking finding 必须修复并由独立 reviewer 复核。作者自审不能替代独立复核。只有 reviewer 实际通过的章节才增加 review_count。

## 9. 门禁、状态推进与发布

### 9.1 全量门禁

所有写入更新使用双基准运行现有门禁：

~~~bash
AEVATAR_SRC="$FROZEN_SNAPSHOT" \
  AEVATAR_SRC2="$TARGET_SNAPSHOT" \
  EXPECTED_UPSTREAM_COMMIT="$FROZEN_SHA" \
  EXPECTED_VERIFIED_AT="$FROZEN_VERIFIED_AT" \
  bash scripts/check-md.sh --all

python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
~~~

任一门禁失败即停止。只修复本轮造成或当前主题范围内的问题，不能禁用测试或扩大范围掩盖无关失败。

### 9.2 原子状态推进

commit-state 仅在以下证据全部成立时运行：

- 状态旧哈希与 prepare 时一致；
- 目标 SHA 与事实包一致；
- 最终语义修改章节和旧样本均有 reviewer pass；
- 没有未关闭 blocking finding；
- 每个新章节都有唯一 issue readback；
- 全量门禁明确成功。

完整同步模式推进 synced_upstream_sha、完成时间和复核覆盖；点题模式只更新完成时间和复核覆盖。两个模式都不得修改 frozen_upstream_sha 或 frozen_verified_at。写入采用临时文件加原子替换；任何失败保留旧状态。

### 9.3 精确提交与推送

按照根 AGENTS.md，写入任务在全部门禁通过后默认发布：

1. 只用显式路径暂存本轮文档、导航、source map 和状态文件，禁止 git add . 或 git add -A；
2. 检查 cached diff 和暂存文件清单，确认没有用户原有内容或运行时文件；
3. 创建一个 docs: 提交；
4. 再次 fetch origin/main，只有远端仍等于 BASE_SHA 时才 push HEAD:main；
5. push 后 readback refs/heads/main，确认它等于本地 HEAD。

远端推进、push 被拒或本地分叉时，不自动 merge、rebase 或 force-push；保留本地提交并报告。push 结果不明确时先 readback，远端已经是目标 SHA 即成功；明确未更新后才允许一次经诊断的重试。

## 10. 失败语义

- fetch 或快照失败：停止，不回退到上游 live working tree；
- 同步水位对象缺失：停止，不猜测 commit 区间；
- 用户改动与目标文件重叠：停止该文件并报告；
- issue 创建结果不明确：readback，仍不明确则停止扩章；
- reviewer 不可用或仍有 blocking finding：不推进状态；
- 门禁失败：不推进状态、不提交、不推送；
- 状态哈希变化：视为并发更新，重新 prepare；
- 当前仓库远端在执行期间推进：不自动整合，保留本地结果并停止发布。

所有失败都必须说明停在哪个边界，不能把部分完成描述为完整同步。

## 11. 测试策略

### 11.1 Skill 行为测试

遵循 writing-skills 的 RED-GREEN-REFACTOR：

- 在 Skill 指导缺失时，用全新上下文压力场景观察真实失败；
- 场景同时覆盖脏上游、未映射新边界、提交前缀诱导、模糊 issue 结果、门禁失败和远端并发推进；
- 无指导 control 至少运行 5 次，人工读取每次结果；
- Skill 完成后以相同压力运行至少 5 个全新上下文 guided repetitions；
- 只针对观察到的遗漏或错误收紧 SKILL.md，不加入臆测规则。

### 11.2 辅助脚本 TDD

使用 Python 标准库 unittest 和临时 Git 仓库，先观察失败再实现，至少覆盖：

- PLAN 解析、状态初始化和原子写入；
- 稳定抽样、排除语义修改章节和新章节优先；
- fetch 后固定目标 SHA，而不改变上游 HEAD 或工作树；
- 完整 commit 与 changed-file 枚举、映射和未覆盖路径；
- 正常增量、history rewrite 和对象缺失；
- 点题模式不能推进同步水位；
- 完整模式只有在复核、issue 和门禁证据齐全时推进；
- 冻结字段不可变、事实包哈希和状态哈希防并发。

### 11.3 集成验证

- 用 quick_validate.py 验证 Skill 元数据；
- 对真实上游执行一次 prepare-only dry run，确认不修改文档、不创建 issue、不推进状态；
- 执行现有全部文档门禁；
- 由全新只读 reviewer 审查最终 Skill、脚本、测试、状态模型和触发规则。

## 12. 完成定义

- “更新文档”类请求必然触发仓库内 Skill；
- 上游同步只 fetch 和读取 Git 对象，测试证明不会改变其工作树；
- 完整模式逐项处理同步水位后的全部提交、未映射路径和架构候选；
- 点题模式快速修改最小范围且不会错误推进完整同步水位；
- 新独立能力先获得唯一 issue，再完整更新正文、PLAN.md、mkdocs.yml、block index、source map 和必要索引；
- 每轮由一个独立 reviewer 检查全部语义修改和最多 6 篇轮转旧正文；
- 多轮 review_count 能形成可验证的全书覆盖；
- 任何失败都不会错误推进同步水位或复核计数；
- 双基准门禁和完整文档门禁通过；
- 发布只包含本轮显式文件，并经远端 SHA readback 确认。

## 13. 非目标

- 不修改、整理或提交 ~/Code/aevatar；
- 不安装后台 daemon、OS scheduler 或长期服务；
- 不建立通用文档生成框架、数据库或新依赖；
- 不以 source map、提交前缀或代码目录镜像替代架构语义判断；
- 不在首版改造 CI、pre-push 或所有验证器；
- 不机械重写全书，也不把点题更新冒充完整同步。
