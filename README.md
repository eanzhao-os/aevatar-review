# Aevatar Review

> 基于冻结上游 `f02aa690bbebb9cabeac30a553d737486b0eb661` 的 Aevatar 结构化中文解读。

本仓库不是 Aevatar 源码仓库，只产出中文 Markdown 文档。关于当前实现的论断以只读冻结快照为准；`canon`、ADR、issue 与生产观察分别承担设计、决策、演进和版本化证据，不能互相冒充代码事实。

## 当前书目

- 14 个 block：`00–13`。
- 72 篇实质章节，另有 14 个只承担导读与顺序的 `index.md`。
- 上游基线：`f02aa690bbebb9cabeac30a553d737486b0eb661`。
- 核验日期：`2026-07-25`。

完整清单见 [PLAN.md](PLAN.md)，站点入口见 [docs/index.md](docs/index.md)。

## 三条阅读路线

| 目标 | 路线 |
|---|---|
| 第一次跑通并理解主线 | [00 导读](00/index.md) → [01 启动与请求](01/index.md) → [03 Workflow](03/index.md) → [05 CQRS](05/index.md) |
| 理解产品、集成与生产 | [06 产品资源](06/index.md) → [07 Conversation](07/index.md) → [08 Channel](08/index.md) → [09 Automation](09/index.md) → [10 生产运行](10/index.md) |
| 实作、排障与审计 | [11 教程](11/index.md) → [12 演进与缺口](12/index.md) → [13 事实源索引](13/index.md) |

## 状态模型

| 状态 | 含义 |
|---|---|
| `current` | 冻结基线中的当前设计或能力 |
| `mixed` | 主体当前有效，但明确隔离历史、生产版本证据或目标态 |
| `historical` | 只保留长期设计教训，不作为现行使用指南 |
| `target` | 尚未落地，只能作为缺口与退出条件阅读 |

## 验证

```bash
AEVATAR_SRC=<frozen-f02aa690-archive> bash scripts/check-md.sh --all
python3 scripts/check-links.py --all
bash scripts/check-drift.sh
python3 scripts/check-mermaid.py
mkdocs build --strict --clean
```

冻结快照可由 Git 对象生成，不读取上游 live working tree：

```bash
AEVATAR_SRC="$(bash scripts/materialize-frozen-upstream.sh   --repo ~/Code/aevatar   --sha f02aa690bbebb9cabeac30a553d737486b0eb661)"
export AEVATAR_SRC
```

## 边界与许可

- `~/Code/aevatar` 是只读外部仓库；本项目不得修改它。
- 当前事实、历史、目标态和生产版本化证据必须分层表达。
- 本解读仓库采用 [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)；引用源码片段的版权归原作者所有。
