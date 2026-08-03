<div class="home-hero" markdown>
<span class="eyebrow">AEVATAR STRUCTURED GUIDE</span>

# Aevatar 结构化中文解读

从请求、Actor 与 Workflow 出发，看清系统边界、事实所有权与生产运行。14 个主题模块、72 篇实质章节，全部以冻结上游证据为基线。

<div class="hero-actions" markdown>
[开始阅读](00/01-reading-guide.md){ .primary-action }
[查看阅读路线](#选择你的阅读路线){ .secondary-action }
</div>
</div>

<div class="home-stats">
  <div><strong>14</strong><span>主题模块</span></div>
  <div><strong>72</strong><span>实质章节</span></div>
  <div><strong>f02aa690</strong><span>冻结证据基线</span></div>
</div>

## 选择你的阅读路线

<div class="route-grid">
  <a class="route-card" href="01/01-quick-start/">
    <span class="route-number">ROUTE 01</span>
    <strong>快速上手</strong>
    <span>启动 Host，发出第一次请求，再沿完整生命周期观察系统。</span>
    <span class="route-link">从第一次请求开始 →</span>
  </a>
  <a class="route-card" href="02/01-agent-actor-runtime/">
    <span class="route-number">ROUTE 02</span>
    <strong>理解架构</strong>
    <span>串联 Actor、Workflow、AI 与 CQRS，理解职责、边界与不变量。</span>
    <span class="route-link">进入核心设计 →</span>
  </a>
  <a class="route-card" href="11/01-run-a-simple-workflow/">
    <span class="route-number">ROUTE 03</span>
    <strong>实践与查证</strong>
    <span>从场景教程动手，再回到演进记录、术语和事实源索引审计结论。</span>
    <span class="route-link">打开 Cookbook →</span>
  </a>
</div>

## 事实先于解释

本站区分四类状态：`current` 是冻结基线中的当前设计，`mixed` 明确隔离历史或目标态，`historical` 只保留长期设计教训，`target` 仅登记尚未落地的限制与退出条件。

!!! info "证据基线"
    全书以冻结上游 `f02aa690bbebb9cabeac30a553d737486b0eb661` 为证据起点；完整章节、状态与 issue 对照见 [PLAN](https://github.com/eanzhao-os/aevatar-review/blob/main/PLAN.md)。

!!! warning "外部仓库边界"
    `~/Code/aevatar` 是只读事实源，本仓库不修改其任何文件。构建与验证方式见 [README](https://github.com/eanzhao-os/aevatar-review/blob/main/README.md)。
