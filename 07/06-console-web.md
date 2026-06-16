# 前端控制台 apps/aevatar-console-web:技术栈 + SSE 对接

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `apps/aevatar-console-web/README.md` 第 5-12 行(技术栈)、第 45-59 行(NyxID 登录 env)、第 78 行(Mainnet API `http://127.0.0.1:5080`)、第 93-108 行(本地代理 split + scope)。
- `apps/aevatar-console-web/package.json` 第 5-6 行:`packageManager pnpm 10.2.1`、`@umijs/max ^4.6.25`;第 30-31 行:`antd ^6.2.2` + `@ant-design/pro-components`;第 40-41 行:`react ^19.2.4`;第 60 行:@umijs/max。
- `apps/aevatar-console-web/src/shared/api/runtimeRunsApi.ts` 第 117 行(`invoke/${endpointId}:stream`)、第 124 行(`invoke/chat:stream`)、第 240/255 行(`streamChat` + `Accept: text/event-stream`)、第 275/290 行(`streamTeamChat`)、第 315/324 行(`streamDraftRun`)。
- `apps/aevatar-console-web/src/shared/agui/`:`sseFrameNormalizer.ts`、`runtimeEventSemantics.ts`(`RuntimeEvent` type)、`customEventData.ts` —— AGUI SSE 帧归一化。
- `apps/aevatar-console-web/src/shared/studio/observeSession.ts` 第 1、14、25 行:`RuntimeEvent` import、`mode: 'stream'|'invoke'`、storage prefix `aevatar-console:studio:observe-session:`。

---

## 技术栈

`apps/aevatar-console-web/README.md` 第 5-12 行 + `package.json`:

| 维度 | 选型 |
|---|---|
| 框架 | **React 19**(`react ^19.2.4`) |
| 应用骨架 | **@umijs/max ^4.6.25**(脚本用 `max dev`/`max build`) |
| UI | **antd ^6.2.2** + **@ant-design/pro-components 3.1.2-0** + `@ant-design/icons ^6.1.0` |
| 包管理 | **pnpm 10.2.1** |
| 数据 | `@tanstack/react-query ^5.90.21` |
| 图画布 | `@xyflow/react ^12.10.1` |
| 编辑器 | `@monaco-editor/react` + `monaco-editor` |
| AGUI SDK | `@aevatar-react-sdk/agui` + `@aevatar-react-sdk/types 0.5.0` |
| Lint/Test | Biome `^2.1.1` + `@umijs/lint`、Jest 29 + jsdom、TypeScript `^5.6.3` |

---

## SSE 对接(关键)

`runtimeRunsApi.ts` 是 SSE 消费核心:
- `streamChat`(第 240 行):`Accept: "text/event-stream"`(第 255 行)
- `streamTeamChat`(第 275 行)
- `streamDraftRun`(第 315 行)
- `streamEndpoint`(第 412 行)

`src/shared/agui/`(`sseFrameNormalizer.ts`/`runtimeEventSemantics.ts`/`customEventData.ts`)做 AGUI SSE 帧归一化 —— 把服务端 `WorkflowRunEventEnvelope` JSON 帧解析成 typed `RuntimeEvent`。

`observeSession.ts`(第 1、14、25 行):观察会话 `mode: 'stream'|'invoke'`,storage prefix `aevatar-console:studio:observe-session:`。

---

## 本地代理 split(`README.md` 第 93-96 行)

| 路由 | 转发到 |
|---|---|
| runtime(`/api/chat`、`/api/workflows/*`、`/api/actors/*`、`/api/runs/*`、`/api/primitives`、`/api/capabilities`、多数 `/api/scopes/*`) | Mainnet Host API(`http://127.0.0.1:5080`) |
| Studio(`/api/app/*`、`/api/auth/*`、`/api/workspace/*`、`/api/editor/*`、`/api/executions/*`、`/api/roles/*`、`/api/connectors/*`、`/api/settings/*`、`/api/scopes/{scopeId}/teams*`) | Studio Hosting API |

scope(README 第 98-108 行):Overview/Studio/Primitives/Runs/Actors/Workflows/Observability/Settings。

---

## 验收

1. 技术栈?(React 19 + @umijs/max + antd + pnpm)
2. SSE 怎么对接?(streamChat 等,Accept: text/event-stream + agui/sseFrameNormalizer 归一化)
3. 本地代理怎么 split?(runtime→Mainnet;Studio→Studio Hosting)

⟦AI:AUTO-LOOP⟧
