# Aevatar 结构化中文解读

> 14 个 block、72 篇实质章节，基于冻结上游 `f02aa690bbebb9cabeac30a553d737486b0eb661`。

本书从请求、Actor、Workflow 与 CQRS 主线出发，继续解释产品身份、Conversation、Channel、Automation 和生产运行；教程、演进层与事实源索引负责实践和审计。

## 怎么读

| 你想做什么 | 从哪里开始 |
|---|---|
| 第一次启动并观察请求 | [00 导读与版本基线](00/index.md) → [01 启动与请求全景](01/index.md) |
| 理解 Actor / Workflow / AI / CQRS | [02 Actor 内核](02/index.md) → [03 Workflow](03/index.md) → [04 AI 执行](04/index.md) → [05 CQRS](05/index.md) |
| 理解产品、集成与生产 | [06 产品资源](06/index.md) → [07 Conversation](07/index.md) → [08 Channel](08/index.md) → [09 Automation](09/index.md) → [10 生产运行](10/index.md) |
| 动手、排障或反向查证 | [11 教程](11/index.md) → [12 演进与缺口](12/index.md) → [13 事实源索引](13/index.md) |

## 全书结构

| Block | 实质章节 | 主题 |
|---|---:|---|
| [00 导读与版本基线](00/index.md) | 3 | 导读与版本基线 |
| [01 启动与请求全景](01/index.md) | 4 | 启动与请求全景 |
| [02 Actor 运行内核](02/index.md) | 6 | Actor 运行内核 |
| [03 Workflow 编排](03/index.md) | 7 | Workflow 编排 |
| [04 AI 执行与工具](04/index.md) | 5 | AI 执行与工具 |
| [05 CQRS、Projection 与 Audit](05/index.md) | 6 | CQRS、Projection 与 Audit |
| [06 产品资源与身份](06/index.md) | 5 | 产品资源与身份 |
| [07 Conversation、NyxIdChat 与 Agent Profile](07/index.md) | 4 | Conversation、NyxIdChat 与 Agent Profile |
| [08 Ingress、Channel、文件与语音](08/index.md) | 5 | Ingress、Channel、文件与语音 |
| [09 Automation、调度与凭证](09/index.md) | 5 | Automation、调度与凭证 |
| [10 分布式与生产运行](10/index.md) | 8 | 分布式与生产运行 |
| [11 场景教程与 Cookbook](11/index.md) | 5 | 场景教程与 Cookbook |
| [12 架构演进、案例与开放缺口](12/index.md) | 5 | 架构演进、案例与开放缺口 |
| [13 术语与事实源索引](13/index.md) | 4 | 术语与事实源索引 |

!!! tip "进度：72/72"
    目录索引不计入实质章节。

## 证据与状态

- `current`：冻结基线中的当前设计或能力。
- `mixed`：主体当前有效，但明确隔离历史、版本化生产证据或目标态。
- `historical`：只保留长期设计教训。
- `target`：尚未落地，只登记 current limit、owner 与 exit criterion。

!!! warning "外部仓库边界"
    `~/Code/aevatar` 是只读事实源；本仓库不得修改其任何文件。

完整路径、状态与 issue 对照见
[PLAN](https://github.com/eanzhao-os/aevatar-review/blob/main/PLAN.md)，验证命令见
[README](https://github.com/eanzhao-os/aevatar-review/blob/main/README.md)。
