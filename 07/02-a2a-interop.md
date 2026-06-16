# A2A Interop:Agent-to-Agent 互操作

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `docs/history/2026-03/maf-integration.md` 第 62-116 行:A2A = "Agent-to-Agent Protocol v0.3.3-preview";adapter 在 Host boundary 把 A2A Task ↔ EventEnvelope 转换;A2A task state 不做权威(actor state + event store 才是);组件表第 88-93 行;映射表第 97-103 行。
- ⚠️ `src/Aevatar.Interop.A2A.{Abstractions,Application,Hosting}/` 在 HEAD 只剩空壳(`bin/`/`obj/`),源码在 `8bfd8605c`("iter38 cluster-038 A2A: 删 task facts process-local + orphan code",−2460 行)被删。历史实现可从 `git show 8bfd8605c^:` 恢复。

---

## A2A 是什么

A2A(Agent-to-Agent Protocol)是跨 Agent 系统互操作协议。aevatar 的 adapter 在 Host boundary 做转换:

- A2A Task ↔ `EventEnvelope`(框架消息)
- A2A task state **不做权威** —— actor state + event store 才是事实源
- adapter 不让 A2A task facts 进进程内本地状态

`docs/history/2026-03/maf-integration.md` 第 62-116 行记录了协议 v0.3.3-preview 的适配设计。

---

## ⚠️ 当前 HEAD 状态:源码已删

三个项目 `Aevatar.Interop.A2A.{Abstractions,Application,Hosting}/` 在当前 HEAD **只剩空壳**(build artifact)。源码在 commit `8bfd8605c`("删 task facts process-local + orphan code")被移除,原因是在 task facts 上引入了进程本地状态,违反"事实源唯一"不变量。

历史实现(可从 `git show 8bfd8605c^:` 恢复):
- **Abstractions**:`IA2AAdapterService`(SendTask/GetTask/CancelTask/GetAgentCard)、`IA2ATaskStore`、`A2ATask`(TaskState: submitted/working/input-required/completed/canceled/failed/unknown)、`AgentCard`、`JsonRpc`
- **Application**:`A2AAdapterService`、`InMemoryA2ATaskStore`
- **Hosting**:`A2AEndpoints` —— `GET /.well-known/agent.json`、`POST /a2a`(JSON-RPC:tasks/send、tasks/get、tasks/cancel)、`GET /a2a/subscribe/{taskId}`(SSE)

> 本篇记录设计意图与历史实现。如需恢复,从 `8bfd8605c^` checkout。

---

## 验收

1. A2A adapter 在哪一层?(Host boundary)
2. A2A task state 是权威吗?(不是,actor state + event store 才是)
3. 当前 HEAD 有 A2A 源码吗?(没有,在 8bfd8605c 被删)

⟦AI:AUTO-LOOP⟧
