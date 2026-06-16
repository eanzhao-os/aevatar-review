# workflows/ 下 12 个示例逐个拆解

## 关键代码(事实源,以 ~/Code/aevatar 为准)

`~/Code/aevatar/workflows/` 目录下共 12 个 YAML 示例。每个都是可跑的 workflow,展示不同的 roles/steps/routes 组合。逐个拆解:

---

## 1. `simple_qa.yaml`(第 1-9 行)—— 最小

- **name**: `simple_qa`
- **roles**: 1 个 `assistant`(system_prompt `"You are a helpful assistant."`,第 2-5 行)
- **steps**: 1 个 `answer`(`llm_call`,role `assistant`,第 6-9 行)
- **演示**: 最小合法 workflow。单角色单步骤,无路由。见 `00/03-quick-start.md`。

## 2. `probe_vision_describe.yaml` —— 视觉能力探针

- **roles**: `vision_probe`(第 15 行)
- **steps**: `llm_call` `describe`(第 28 行)+ `assign` report(第 35 行)
- **演示**: 验证 chat 附件图片 → 视觉 LLM 路径。

## 3. `probe_document_extract.yaml` —— 文档抽取探针

- **roles**: `file_probe`(第 19 行)
- **steps**: `tool_call` `extract_file`(第 29 行)+ `llm_call` report(第 38 行)+ `assign` summary(第 45 行)
- **演示**: 验证文件 → document_extract 工具路径。

## 4. `resume_screening.yaml`(第 20-121 行)—— 简历筛选(多路由)

- **roles**: `resume_screener`(第 20 行)
- **steps**: `tool_call` extract(第 36 行)→ `switch` route_extract(第 43 行)→ `llm_call` screen(第 55 行)→ `switch` route_score(第 62 行)→ `assign` build_record(第 74 行)→ `tool_call` write_bitable(第 81 行)→ `switch` route_write(第 88 行)+ assign reports
- **演示**: 多路由审批式流程。`tool_call` + `switch` + `assign` 组合。

## 5. `petty_cash_approval.yaml`(第 13-92 行)—— 备用金审批

- **roles**: `receipt_extractor`(第 13 行)
- **steps**: `llm_call` extract(第 33 行)→ `switch`(第 40 行)→ `assign` build_body(第 52 行)→ `tool_call` submit_approval(第 59 行)→ `switch`(第 66 行)→ `transform`/`assign`/`workflow_call` wait_approval(第 92 行)+ report assigns
- **演示**: 报销 → Lark 审批完整循环。`workflow_call` 调子 workflow 等待审批结果。

## 6. `invoice_ocr_approval.yaml`(第 16-131 行)—— 发票 OCR 审批

- **roles**: `invoice_extractor`(第 16 行)+ `approval_builder`(第 30 行)
- **steps**: `llm_call` extract(第 60 行)→ `switch`→ `llm_call` build_body(第 79 行)→ `switch`→ `tool_call` submit(第 98 行)→ `switch`→ `transform`/`assign`/`workflow_call` wait_approval(第 131 行)
- **演示**: OCR + 双角色协作。`when_to_use` 设置(第 11 行)。

## 7. `employee_reimbursement_sg.yaml`(第 19-173 行)—— SG 报销

- **roles**: `invoice_extractor`(第 19 行)+ `approval_builder`(第 36 行)
- **steps**: 镜像 petty_cash,但加 `transform` sum_by_currency(第 84 行)+ `human_input` review_request(第 94 行)
- **演示**: 5 个 switch + 6 个 report assign,含 `human_input` 人工审核。

## 8. `cn_reimbursement_intake.yaml`(第 18-173 行)—— CN 报销(最复杂)

- **roles**: `reimbursement_extractor`(第 18 行)+ `approval_builder`(第 34 行)
- **steps**: extract→switch→`transform` pick_receipts(第 78 行)+ sum_by_currency(第 85 行)→`human_input` review(第 95 行)→switch→build→switch→`tool_call` submit→switch→`workflow_call` wait_approval(第 173 行)
- **演示**: 最复杂的报销变体。`transform` + `human_input` + `workflow_call` 全组合。

## 9. `lark_approval_wait.yaml`(第 5-60 行)—— Lark 审批等待模板(可复用)

- **roles**: 无(委托给子 workflow)
- **steps**: `while` `poll_until_terminal`(第 5 行,`step: workflow_call`,`max_iterations: "60"`)→ `switch` route_wait_result(第 15 行)→ 6 个 `assign` 终态标记(approved/rejected/withdrawn/terminated/failed/timeout)
- **演示**: 可复用的 Lark 审批轮询模板。`while` 循环调子 workflow。

## 10. `lark_approval_wait_poll.yaml`(第 5-40 行)—— 单次轮询叶子

- **steps**: `tool_call` `lark_approvals_get`(第 5 行)→ `switch` route_get_success(第 12 行)→ `switch` route_status(第 24 行)→ `delay` wait_before_next_poll(第 40 行)+ `assign` markers
- **演示**: 被 #9 调用的单次轮询叶子。`tool_call` + `delay` 轮询模式。

## 11. `codex_long_running_handoff.yaml`(第 4-25 行)—— 长任务外部回调

- **roles**: `reviewer`(第 4 行)
- **steps**: `emit` announce_job(第 10 行)→ `wait_signal` wait_for_codex_worker(第 17 行)→ `foreach` review_worker_output(第 25 行)
- **演示**: 长任务外部回调 + 并发 fan-out。被 `docs/canon/workflow-primitives.md:771` 引用。

## 12. `host-callback-budget-branch.yaml`(第 4-32 行)—— host 回调 + 预算守卫

- **roles**: `coordinator`,`connectors: [github_router]`(第 4 行)
- **steps**: `connector_call` classify_host_signal(第 10 行)→ `switch` route_by_host(第 18 行)→ `guard` budget_gate(第 26 行)→ `transform` fallback(第 32 行)
- **演示**: host-callback connector + `guard` 预算分支。

---

## 模式总结

| 模式 | 示例 |
|---|---|
| 最小单步 | `simple_qa` |
| 工具调用 | `probe_document_extract`, `resume_screening` |
| 多路由审批 | `resume_screening`, `petty_cash_approval`, `invoice_ocr_approval` |
| 子 workflow 等待 | `petty_cash_approval`, `invoice_ocr_approval`, `lark_approval_wait` |
| 轮询循环 | `lark_approval_wait`(`while`)+ `lark_approval_wait_poll`(`delay`) |
| 人工输入 | `employee_reimbursement_sg`, `cn_reimbursement_intake` |
| 长任务回调 | `codex_long_running_handoff`(`emit`+`wait_signal`+`foreach`) |
| 预算守卫 | `host-callback-budget-branch`(`guard`) |

---

## 验收

1. 最小 workflow 是哪个?(`simple_qa`,1 role + 1 step)
2. 审批等待用哪种组合?(`workflow_call` 调 `lark_approval_wait` 子 workflow,内部 `while` 轮询)
3. 长任务外部回调怎么实现?(`emit` 通知 + `wait_signal` 等待 + `foreach` fan-out,`codex_long_running_handoff`)

⟦AI:AUTO-LOOP⟧
