# Connector(HTTP/CLI/MCP)配置与 connector_call 执行、role allowlist

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `docs/canon/connector.md` 第 18-28 行:connector 契约 + 配置链;第 34-69 行:配置 shape + 解析规则;第 73-93 行:`ConnectorConfigEntry` + 类型子字段;第 104-108 行:builder 校验;第 141-181 行:`connector_call` 执行;第 186-260 行:各类型执行细节;第 264-281 行:`connector_call` vs `tool_call`。
- `docs/canon/connector.md` 第 248-260 行:host 责任边界(`host-not-controller`/`published-surfaces-only`/`no-new-aevatar-endpoints`)。
- `src/Aevatar.Configuration/README.md` 第 19 行:`AevatarConnectorConfig`;第 44-50 行:Role 与 Connector 分配(中心化配置 + 按角色授权);第 54-80 行:YAML 示例。
- `src/Aevatar.Bootstrap/Connectors/IConnectorBuilder.cs` 第 7-12 行:`IConnectorBuilder` 接口。
- `src/Aevatar.Bootstrap/Connectors/HttpConnectorBuilder.cs` 第 33 行;`HttpConnector.cs` 第 66 行。
- `src/Aevatar.Bootstrap/Connectors/CliConnectorBuilder.cs` 第 9 行;`CliConnector.cs` 第 48 行。
- `src/Aevatar.Bootstrap/Connectors/HostCallbackConnectorBuilder.cs` 第 19 行;`HostCallbackConnector.cs` 第 39 行。
- `src/Aevatar.Bootstrap/Connectors/TelegramUserConnectorBuilder.cs` 第 13 行;`TelegramUserConnector.cs` 第 82 行。
- `src/Aevatar.Bootstrap.Extensions.AI/Connectors/MCPConnectorBuilder.cs` 第 22 行(需 `mcp.command` 或 `mcp.url`,第 27-30 行)。
- `src/Aevatar.Bootstrap/ServiceCollectionExtensions.cs` 第 30-35 行:`RegisterConnectorBuilders`(http/cli/host_callback/telegram_user)。
- `src/Aevatar.Bootstrap.Extensions.AI/ServiceCollectionExtensions.cs` 第 126 行:`MCPConnectorBuilder` 注册(gated by AI features/MCP option)。
- `src/workflow/Aevatar.Workflow.Core/Modules/ConnectorCallModule.cs` 第 31 行:`Name => "connector_call"`;第 89-90 行:canonical 化 + `secure_connector_call` 区分。
- `src/workflow/Aevatar.Workflow.Core/ServiceCollectionExtensions.cs` 第 29 行:`IConnectorRegistry` → `ConfiguredConnectorRegistry`。

---

## Connector 是什么

Connector 是 workflow 调用外部系统的抽象(`docs/canon/connector.md` 第 18-21 行):

- 契约:`IConnector` / `IConnectorRegistry`(在 `Aevatar.Foundation.Abstractions`)
- 配置:集中式,`~/.aevatar/connectors.json`
- workflow 用 `connector_call` step + `parameters.connector` 调用
- role 的 `connectors` 是**授权 allowlist**,不是连接定义

> **关键区分**(`connector.md` 第 264-281 行):`connector_call`(经 `ConnectorCallModule`,workflow 步骤侧)vs `tool_call`(经 `ToolCallModule`,agent 工具系统)。当前 role-connector 授权只在 **workflow roles + connector_call** 真正生效(第 278-281 行)。

---

## 四种 connector 类型

| 类型 | builder / 文件 | connector 实现 | 校验要求 |
|---|---|---|---|
| `http` | `HttpConnectorBuilder.cs:33` | `HttpConnector.cs:66` | `http.baseUrl`(`connector.md:104`) |
| `cli` | `CliConnectorBuilder.cs:9` | `CliConnector.cs:48` | `cli.command`(不含 `://`) |
| `mcp` | `MCPConnectorBuilder.cs:22`(AI 扩展项目) | — | `mcp.command` 或 `mcp.url`(第 27-30 行) |
| `host_callback` | `HostCallbackConnectorBuilder.cs:19` | `HostCallbackConnector.cs:39` | handler |
| `telegram_user` | `TelegramUserConnectorBuilder.cs:13` | `TelegramUserConnector.cs:82` | — |

**DI 注册时机**(`connector.md` 第 94-113 行):
- `http`/`cli`/`host_callback`/`telegram_user`:由 `AddAevatarBootstrap()` 注册(`ServiceCollectionExtensions.cs` 第 30-35 行)
- `mcp`:仅当 `AddAevatarAIFeatures(..., options => options.EnableMCPTools = true)` 时注册(`ServiceCollectionExtensions.cs:126`,`connector.md:113`)

---

## 配置(`connectors.json`)

`~/.aevatar/connectors.json`(`connector.md` 第 34-39 行),可用 `AEVATAR_HOME` 覆盖路径。支持三种 JSON shape(array/object/`definitions`),解析规则(`connector.md` 第 43-69 行):`enabled=false` 过滤、缺 `name`/`type` 过滤、`timeoutMs` clamp 100..300000、`retry` clamp 0..5。

`ConnectorConfigEntry` 公共字段(第 73-79 行):`name`/`type`/`enabled`/`timeoutMs=30000`/`retry=0`。类型子字段(http/cli/mcp/host_callback,第 83-93 行)。

HTTP 示例(`src/Aevatar.Configuration/README.md` 第 104-195 行有完整示例):
```json
{
  "name": "github_router",
  "type": "http",
  "enabled": true,
  "timeoutMs": 30000,
  "http": {
    "baseUrl": "https://api.github.com",
    "allowedMethods": ["GET", "POST"],
    "allowedPaths": ["/repos/*"],
    "auth": { "type": "secret_ref_header", "header": "Authorization", "secretRef": "GITHUB_TOKEN" }
  }
}
```

---

## connector_call 执行

`ConnectorCallModule`(`ConnectorCallModule.cs` 第 31 行)执行流程(`connector.md` 第 141-181 行):

1. 读 `connector`/`operation`/`retry`/`timeout_ms`/`optional`/`on_missing`/`on_error`
2. 经 `IConnectorRegistry` 解析 connector
3. 校验 role 的 `connectors` allowlist 包含该 connector
4. 构造 `ConnectorRequest`,调 `IConnector.ExecuteAsync()`

**容错语义**(第 166-174 行):
- connector 缺失 → `optional`/`on_missing: skip` 成功(返回 input)
- 失败 → `on_error: continue` 继续
- `attempts = retry + 1`,retry 上限 5

最小 YAML:
```yaml
steps:
  - id: list_repos
    type: connector_call
    role: coordinator        # role 的 connectors 须含 github_router
    connector: github_router
    operation: list_repos
```

---

## role connector allowlist

`src/Aevatar.Configuration/README.md` 第 44-50 行(方案 A:中心化配置 + 按角色授权):

- connector 定义集中在 `connectors.json`
- "谁能用"按 role 配置:`connectors: [name…]`(`RoleDefinition.connectors`,`WorkflowDefinition.cs:186`)
- `connector_call` step 必须设 `role`/`target_role`
- 运行时检查 role 的 `connectors` 是否包含该 connector(第 49 行)
- 省略 `role` 跳过 allowlist(向后兼容,第 50 行)

---

## host 责任边界(`connector.md` 第 248-260 行)

- `host-not-controller`:host 提供回调端点,不控制 workflow 执行
- `published-surfaces-only`:host 只暴露已发布面
- `no-new-aevatar-endpoints`:不为 connector 新增 aevatar 内部端点

---

## 验收

1. connector 配置在哪?(`~/.aevatar/connectors.json`,中心化)
2. role 的 `connectors` 是什么?(授权 allowlist,不是连接定义)
3. `connector_call` 和 `tool_call` 区别?(前者 workflow 步骤侧调外部系统;后者 agent 工具系统,`connector.md` 第 264-281 行)
4. MCP connector 什么时候注册?(仅当 `EnableMCPTools=true`,`connector.md` 第 113 行)

⟦AI:AUTO-LOOP⟧
