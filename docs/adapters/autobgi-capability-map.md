# AutoBGI Capability Map

AutoBGI is the preferred execution service for BetterGI AI. It is an external maintained project and must not be copied into this repository.

## Role

AutoBGI sits between the agent and BetterGI:

```text
Agent -> BetterGI AI skills -> AutoBGI MCP -> AutoBGI -> BetterGI
```

BetterGI AI owns intent mapping, local config edits, validation, and safety rules. AutoBGI owns execution, status, and its own maintained BetterGI launch behavior.

## MCP Endpoint

AutoBGI exposes MCP over SSE:

```text
GET /mcp/sse
POST /mcp/messages?sessionId=...
```

The message endpoint requires the configured `apiKey` header. Do not commit real keys.

## Validated Tools

The local AutoBGI MCP probe successfully listed:

- `findBgiIndex`
- `RunCronTask`
- `continueOneDragon`
- `startObsRecording`
- `stopObsRecording`
- `captureDesktopScreenshot`
- `queryCharacterBuild`
- `queryBackpack`
- `collectMaterialRoutes`
- `collectCookingRoutes`

## Safe Subset

Allowed by default:

- `findBgiIndex`: read BetterGI/AutoBGI progress.
- `queryBackpack`: read one material count.
- `captureDesktopScreenshot`: only when the user explicitly asks for visual verification.
- `queryCharacterBuild`: only for one user-requested character.
- `RunCronTask`: only immediate `启动一条龙` or `启动配置组`.

`RunCronTask` observed enum:

- `关闭原神和关闭bgi`: disabled
- `启动一条龙`: allowed with exact user-approved one-dragon name
- `启动配置组`: allowed with exact user-approved group name
- `备份user`: disabled
- `米游社签到`: disabled

Use `delayInSeconds=0` for allowed launches.

## Disabled By Default

- `continueOneDragon`: broad continuation over remaining groups.
- OBS recording tools: recording side effects.
- shutdown/backup/sign-in actions: system or account-sensitive.
- `collectMaterialRoutes` and `collectCookingRoutes`: route planning plus collection-management mutation.
- broad account reads, arbitrary scheduling, raw input, shell execution, upload/update operations.

## Route Collection Note

`collectMaterialRoutes` overlaps with BetterGI AI's repository/search/subscription work, but it is not the same capability.

BetterGI AI currently:

- searches installed route/script inventory
- searches local repository indexes
- edits subscription paths
- adds installed routes to config groups

AutoBGI `collectMaterialRoutes`:

- takes a material name and target quantity
- chooses routes from the script source
- adds route tasks to collection management

Treat it as a future `bettergi-collection-planner` workflow, not a replacement for repository search.
