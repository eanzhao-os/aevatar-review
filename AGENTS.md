# AGENTS.md

> 本仓库是 **aevatar 的结构化中文解读项目**(documentation / review repo),
> 不是 aevatar 源码仓库。源码以 `~/Code/aevatar`(上游 `aelf:aevatarAI/aevatar`)
> 为唯一事实源;本仓库只产出**中文 Markdown 章节文档**。

## 仓库性质

- **产物**:纯 Markdown 文档(`XX/NN-name.md`),对照 `PLAN.md` 当前 72 篇实质章节清单；`00–13` 的 14 个 `index.md` 只承担导读与顺序。
- **事实源唯一性**:所有关于 aevatar 内部的论断**必须**指向 `~/Code/aevatar` 下的真实
  `.cs` / `.yaml` / `docs/canon/*` / `docs/adr/*` 文件路径 + 行号锚点。禁止脑补、禁止
  泛泛而谈、禁止不引用源码就下结论。
- **源码无改动权**:本仓库**不得**修改 `~/Code/aevatar` 的任何文件;只读引用。
- **工作语言**:中文 Markdown(`$HOST_WORK_LANGUAGE=zh`)。代码块 / 文件路径 / 标识符 /
  协议词汇保持英文原样。

## 分层与目录约定

```
00/  导读与版本基线
01/  启动与请求全景
02/  Actor 运行内核
03/  Workflow 编排
04/  AI 执行与工具
05/  CQRS、Projection 与 Audit
06/  产品资源与身份
07/  Conversation、NyxIdChat 与 Agent Profile
08/  Ingress、Channel、文件与语音
09/  Automation、调度与凭证
10/  分布式与生产运行
11/  场景教程与 Cookbook
12/  架构演进、案例与开放缺口
13/  术语与事实源索引
```

普通章节文件命名为 `<block>/<NN>-<slug>.md`；不再新增嵌套方案区。所有合法路径以 `PLAN.md`
和 `mkdocs.yml` 为准。

## 写作原则 v2(强制,见 issue #87)

### 原则 1:设计导向,不堆代码引用

**默认**:不引用代码文件路径 + 行号。改用设计语言(职责/边界/协议/状态/不变量)描述。

**例外(可引用 + 摘抄)**:仅当满足全部三条 —— 这段代码基本不可能改(协议/proto/核心抽象);摘抄能让读者理解设计;摘抄内容用 `<details>` 折叠。反例(必须删):`X.cs:389 行` 实现细节行号。

**事实源清单**:每篇开头用 1-2 句话说明"本设计链路涉及哪些抽象/职责",不贴文件行号表。

### 原则 2:每段必须有图(普通章节每章 ≥ 2 张)

- 时序图/流程图/状态机/分层 → **mermaid**(纯文本可 diff)
- 复杂拓扑/数据流 → **手绘 PNG**(`docs/assets/<block>-<slug>.png`)
- 仅承担导航/概览职责的 `index.md` 可不满足“两张图”,但其中的事实论断仍必须有事实源。

禁止单纯文字描述一个本该用图的流程。

### 原则 3:每段论证设计正当性("为什么是它,不是别的")

- ✅ "为什么 Actor 而非线程池" / "为什么事实源是 EventStore"
- ❌ 只写"怎么做"不写"为什么"
- 说不清正当性 → 加 `!!! warning "设计待论证"` admonition + 登记到附录 TODO List

### 诚实标注

- "当前实现 vs 目标态"按代码事实描述。已删/退役组件标"历史/已移除"+ commit。设计可疑标 ⚠️。

## Build / Test

本仓库无编译产物。验证手段:

- **BUILD**:`AEVATAR_SRC=<frozen-f02aa690-archive> bash scripts/check-md.sh --all` —— 校验所有章节 Markdown 文件存在、frontmatter /
  标题层级 / 空文件 / 孤儿链接基本结构合规。`check-md.sh` 对引用的上游路径采用**双基准**：冻结树（`AEVATAR_SRC`）与同步基线工作树（`AEVATAR_SRC2`，默认 `~/Code/aevatar`，可设空串禁用）任一存在且行号锚点在任一基准内即通过；正文同步 HEAD 的章节可引用 HEAD 特有文件（见 `00/02` 正文同步例外）。
- **TEST**:同上脚本 + `python3 scripts/check-links.py --all` + `bash scripts/check-drift.sh`，并检查每篇章节是否含「事实源/设计抽象」入口(可回指
  `~/Code/aevatar` 的真实路径),且引用的源码文件真实存在。
- **MERMAID**:`python3 scripts/check-mermaid.py` —— 用真实 mermaid 引擎(`mermaid-cli`,
  pin 11.15.0 = 站点 mermaid 大版本)解析每个 ` ```mermaid ` 块。`mkdocs --strict` **抓不到**
  图的语法错误(mermaid 在浏览器渲染,坏图只在页面显示 "Syntax error in text"),所以单列此 gate。
  CI(`.github/workflows/docs.yml` build job)在 `mkdocs build` 前强制运行它,坏图 ⇒ 不部署。
  本地需先 `npm i -g @mermaid-js/mermaid-cli@11.15.0`(或脚本回退到 `npx`)。
  每个 Mermaid 块必须在首行写 `%%{init: ...}%%`;flowchart 标签统一用引号包裹。
  `sequenceDiagram` 使用紧凑 sequence 配置,消息文本**禁用 ASCII `;`**(用 `、`/`；` 代替)。

## 章节验收(对照各 issue 的「验收标准」)

每篇章节完成需同时满足:

1. 文件存在且非空,路径对照 `PLAN.md`。
2. 开头有「事实源/设计抽象(以 ~/Code/aevatar 为准)」清单,默认不超过 3 条高价值
   路径 + 行号锚点;需要更多锚点时必须说明它们属于事实源清单而非正文骨架。
3. 论断均可回指源码 / canon / adr,不脑补;正文用图、示例和边界论证解释模型,不得把
   源码文件 / Name / 行号表当作正文主体。
4. 配最小 demo / YAML 片段(如适用)。
5. 满足该 issue 的「验收标准」读者可回答的问题。

## 外部仓库边界

- `~/Code/aevatar` 为**只读**事实源,不得修改。
- 不得新增对 aevatar 源码的依赖或改动。
- 现有 aevatar 文档(`docs/canon/*`、`docs/adr/*`)内容可引用、可转述并加导读,但不得
  整篇复制(版权与可维护性)。

## Agent 协作约束

- 所有 agent 必须直接在 `main` 分支工作;不得创建或切换其他分支。
- 禁止创建或使用 Git worktree。
- 允许多个 agent 并行工作,但同一文档同时只能由一个 agent 修改;并行派发前必须按文档
  划分互不重叠的 `scope_paths`。

## consensus-loop 工作单元边界

- 每个 chapter issue 是一个独立工作单元,产物为单个 Markdown 文件(或一组同目录文件)。
- 实现者(写章节)的 `scope_paths` 限定在该章节对应的目录/文件;不越界改其它章节。
- 若发现需要扩展新章节(PLAN.md 未列),先 print `SCOPE_EXTEND` 并补 issue,再写。

## 文档补充自动化

- 用户要求在本仓库中更新、同步或刷新文档，或检查文档是否落后于上游时，必须使用仓库内 `$updating-aevatar-review-docs`；未限定主题走 `full`，点名 feature、模块、协议、流程或实现细节走 `topic`。
- 发现 `PLAN.md` 未覆盖的独立职责边界时，已获授权打印 `SCOPE_EXTEND`，创建并唯一核验 chapter issue，然后扩充正文、`PLAN.md`、`mkdocs.yml`、block index、source map 和必要索引。
- 每轮写入只调度一个全新上下文的只读 reviewer，复核全部语义变更和最多 6 篇轮转旧正文；reviewer 或门禁未通过不得推进状态。
- 写入任务在全部门禁和状态提交成功后，只提交本轮显式文件并安全推送 `origin/main`；查询、审阅和建议不写入、不提交、不推送。


<!-- consensus-rnd:foundational-invariants:start version=1 sha256=f5c24b0c3515993a7b86c4ed78ce7386add665f8c8b84cc7275aedebd6c3e6af -->
## 共识研发不动点（由 consensus-rnd 管理）

- FI-001 AI 产物默认不可信；进入主线前必须经过独立检查，至少包含共识、review 或自动验证中的适用组合。
- FI-002 Host 事实必须由 host 配置或 host 规则注入；通用 skill / engine 不硬编码具体项目、组织、路径、分支或人员事实；skill-private runtime directories such as `.refactor-loop/` must not become host production configuration or ledger SSOT.
- FI-003 稳定核心保持小而可审计；高频变化留在 host 规则、prompt、脚本或扩展层，不下沉为核心不变量。
- FI-004 跨进程、跨 turn 或跨节点的事实必须有权威记录；进程内记忆、cache、临时变量不能冒充事实源。
- FI-005 边界优先于便利；职责、层级、协议和状态所有权必须清楚，禁止用中间层快捷方式绕过主链路。
- FI-006 变更必须可验证且基于 evidence；失败、缺口和越界承诺要显式暴露，禁止用静默假设或禁用测试换取通过。
- FI-007 删除优先；废弃路径直接移除，除非 host 规则明确要求迁移期兼容。
<!-- consensus-rnd:foundational-invariants:end -->
