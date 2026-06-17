# Demo Cookbook:Maker / CaseProjection / Workflow.Web / Cli / Inspector 可复现合集

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## 当前 HEAD 可用

### `demos/lark-interaction-probe/` ✅ 在 HEAD
- `README.md`、`cn-reimbursement fixture`(18 字段报销审核 fixture)
- **演示**:把 n8n 表单页迁移到 typed Lark card 交互的 Phase 1 探针。load YAML → `notify` 步骤经 Lark card composer 渲染 → 发到真实 Lark test tenant → 截 desktop+mobile 截图 + 脱敏 callback → 校验 18 个逻辑字段 key。证据策略:截图/callback 必须来自实际 run。

---

## 已删除(可从 git 恢复)

### `Aevatar.Demos.Workflow/`(删于 `4a029981c`)
- **演示**:每个 workflow 内建 primitive 一个 YAML,preset 输入,开箱即跑。`dotnet run` 列 demo;`--deterministic` 跑全部非 LLM demo;完整集需 `DEEPSEEK_API_KEY`。
- **workflows/**:~50 YAML(assign/cache/conditional/foreach/parallel/pipeline/race/reflect/transform/switch/llm_call/llm_chain/map_reduce/human_approval×4/human_input×2/mixed×3/role_event_module×~14/subworkflow level1-3/tool_call_fallback/wait_signal×2/workflow_call_multilevel/retrieve_facts/evaluate/emit/delay_checkpoint/demo_csv_markdown/demo_json_pick/demo_template/connector_cli/cli_call_alias/guard)
- 恢复:`git show 4a029981c^:demos/Aevatar.Demos.Workflow/`

### `Aevatar.Demos.Workflow.Web/`(删于 `4a029981c`)
- **演示**:Workflow Web Playground 的 Auto 模式 prompt cookbook(copy-paste prompt 生成复杂 workflow YAML;模板要求 ≥6 roles、≥18 steps、含 assign/llm_call/parallel/map_reduce/evaluate/reflect/conditional/cache/checkpoint/human_approval/delay/emit)
- 含自定义 module(DemoCsvMarkdown/DemoJsonPick/DemoTemplate)+ `DemoWorkflowModulePack`
- 恢复:`git show 4a029981c^:demos/Aevatar.Demos.Workflow.Web/`

### `Aevatar.Demos.Cli/`(删于 `4a029981c`)
- **演示**:runtime 行为场景 CLI(list/run hierarchy/fanout/pipeline/hooks/lifecycle),JSON timeline 渲染到 CLI + HTML
- agents:DemoCollector/Counter/Faulty/Transformer + `demo_messages`
- 恢复:`git show 4a029981c^:demos/Aevatar.Demos.Cli/`

### `Aevatar.Demos.Inspector/`(删于 `40a36bbe2`,残留在 `67795553f` 起清理)
- **演示**:本地两级 Actor Inspector 可视化(`dotnet run -- --no-browser`,默认 `http://localhost`)
- Tier 1 REST:`/api/inspector/actors`、`/workflow-runs`、`/readmodels[/{name}]`
- Tier 2 `/api/inspector/events`:live SSE,由 `Aevatar.Agents` OTel activities 喂
- 无需 LLM 可 populate:`curl -X POST .../api/inspector/demo/hierarchy`
- 配 `Aevatar.Demos.Inspector.Web/`(Vite/React/TS 前端)
- 恢复:`git show 7b8b78dac:demos/Aevatar.Demos.Inspector/`(peak 版本)

### `Aevatar.Demos.Maker/`(删于 `4a029981c`)
- **演示**:MAKER 模式(论文 arXiv 2511.09030):MAD(Maximal Agentic Decomposition)+ first-to-ahead-by-k voting + red-flagging
- `DeterministicMakerProvider`、`maker.connectors.json`、roles(coordinator/worker)、`maker_analysis`(已删 demo)
- 核心实现已迁到 Maker 核心实现(已从 demo 迁出)
- 恢复:`git show 4a029981c^:demos/Aevatar.Demos.Maker/`

### CaseProjection 四件套(删于 `4ff5c2d1b`)
- **演示**:parallel-to-Workflow 域 demo(Case Management),复用通用 CQRS kernel —— **OCP 示例**
- `CaseProjection.Abstractions/`(context factory/service/proto)
- `CaseProjection/`(core:`CaseProjectionService`/`CaseReadModelProjector`/`Reducers`/`InMemoryCaseReadModelStore`)
- `CaseProjection.Extensions.Sla/`(外部 assembly 扩展:`CaseEscalatedEventReducer` 加 SLA 升级**不改核心投影项目** —— OCP open-for-extension + DIP 示例)
- `CaseProjection.Host/`(`Program` DI 组合 `AddCaseProjectionDemo` + `AddCaseProjectionExtensionsFromAssembly`)
- 恢复:`git show 4ff5c2d1b^:demos/Aevatar.Demos.CaseProjection*/`

---

## 复现建议

1. **想看 primitive 全集** → 恢复 `Aevatar.Demos.Workflow`,跑 `--deterministic`(非 LLM 全集)
2. **想看两级 Inspector** → 恢复 `Aevatar.Demos.Inspector`,无需 LLM 即可 populate
3. **想看 OCP 扩展示例** → 恢复 CaseProjection 四件套
4. **想看 Lark 交互** → `demos/lark-interaction-probe/`(HEAD 可用)

---

## 验收

1. 当前 HEAD 有哪些 demo 可跑?(仅 lark-interaction-probe)
2. 怎么看 primitive 全集?(恢复 Aevatar.Demos.Workflow,跑 --deterministic)
3. CaseProjection 演示什么设计原则?(OCP open-for-extension + DIP)
4. 怎么恢复已删 demo?(`git show <deletion>^:`)

⟦AI:AUTO-LOOP⟧
