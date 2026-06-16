# CLAUDE.md

> 本仓库是 **aevatar 的结构化中文解读项目**(documentation / review repo),
> 不是 aevatar 源码仓库。源码以 `~/Code/aevatar`(上游 `aelf:aevatarAI/aevatar`)
> 为唯一事实源;本仓库只产出**中文 Markdown 章节文档**。

## 仓库性质

- **产物**:纯 Markdown 文档(`XX/NN-name.md`),对照 `PLAN.md` 的 43 篇章节清单。
- **事实源唯一性**:所有关于 aevatar 内部的论断**必须**指向 `~/Code/aevatar` 下的真实
  `.cs` / `.yaml` / `docs/canon/*` / `docs/adr/*` 文件路径 + 行号锚点。禁止脑补、禁止
  泛泛而谈、禁止不引用源码就下结论。
- **源码无改动权**:本仓库**不得**修改 `~/Code/aevatar` 的任何文件;只读引用。
- **工作语言**:中文 Markdown(`$HOST_WORK_LANGUAGE=zh`)。代码块 / 文件路径 / 标识符 /
  协议词汇保持英文原样。

## 分层与目录约定

```
00/  序章(定位 / 主线 / 怎么跑)
01/  宿主与入口(Host / API / SSE-WS)
02/  编排层(Workflow YAML + 步骤模块 + Maker)★
03/  运行内核(Foundation: Actor / Event / State)★
04/  AI 能力层(RoleGAgent / LLM / Tool)
05/  CQRS 与读侧(Projection / ReadModel)★
06/  分布式与生产态(Orleans / Garnet / Kafka)
07/  周边(Channel / A2A / Voice / 前端)
08/  附录(术语表 / 文档索引 / demo cookbook)
```

每篇章节文件命名:`<block>/<NN>-<slug>.md`(对照 `PLAN.md` 章节清单)。

## 写作原则(强制)

1. **自顶向下**:先讲"一次请求怎么流过去",再逐层下钻。读者可以随时停在任何一层。
2. **以源码为准**:每篇开头列「关键代码」清单(文件路径 + 行号锚点),论断都指向真实
   代码或 `docs/canon/*`。
3. **配 demo**:每个关键概念给最小可读/可跑示例(优先用 `workflows/` 和 `demos/` 自带的)。
4. **说清楚边界**:重点讲 aevatar 区别于"普通 Agent 框架"的设计取舍
   (Actor + ES + CQRS),而不只是 API 用法。
5. **诚实标注**:对仓库里标 "当前实现 vs 目标态" 的部分,按代码事实描述,不脑补未来。

## Build / Test

本仓库无编译产物。验证手段:

- **BUILD**:`bash scripts/check-md.sh` —— 校验所有章节 Markdown 文件存在、frontmatter /
  标题层级 / 空文件 / 孤儿链接基本结构合规。
- **TEST**:同上脚本 + 检查每篇章节是否含「关键代码」清单(指向 `~/Code/aevatar` 的真实
  路径),且引用的源码文件真实存在。

## 章节验收(对照各 issue 的「验收标准」)

每篇章节完成需同时满足:

1. 文件存在且非空,路径对照 `PLAN.md`。
2. 开头有「关键代码(事实源,以 ~/Code/aevatar 为准)」清单,引用真实文件路径。
3. 论断均锚定源码 / canon / adr,不脑补。
4. 配最小 demo / YAML 片段(如适用)。
5. 满足该 issue 的「验收标准」读者可回答的问题。

## 外部仓库边界

- `~/Code/aevatar` 为**只读**事实源,不得修改。
- 不得新增对 aevatar 源码的依赖或改动。
- 现有 aevatar 文档(`docs/canon/*`、`docs/adr/*`)内容可引用、可转述并加导读,但不得
  整篇复制(版权与可维护性)。

## consensus-loop 工作单元边界

- 每个 chapter issue 是一个独立工作单元,产物为单个 Markdown 文件(或一组同目录文件)。
- 实现者(写章节)的 `scope_paths` 限定在该章节对应的目录/文件;不越界改其它章节。
- 若发现需要扩展新章节(PLAN.md 未列),先 print `SCOPE_EXTEND` 并补 issue,再写。


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
