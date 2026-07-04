# AutoBGI Capability Map

This document records how AutoBGI relates to BetterGI AI. It is based on the public Gitee project snapshot downloaded into `tmp/auto-bgi-api` from branch `ginVue` at commit `2f60a237b5107758c15edf537acb5e6b6635ffc2`, inspected on 2026-07-05.

## Source Snapshot

Key files inspected:

- `README.md`
- `main.go`
- `task/Task.go`
- `MCP/server.go`
- `MCP/service.go`
- `OneLong/oneLong.go`
- `config/Config.go`
- `auth/AuthMiddleware.go`
- `bgiStatus/*`
- `autoLog/AutoLog.go`
- `TaskCron/*`
- `menu/web/src/utils/api.js`

AutoBGI is AGPL-3.0 licensed. BetterGI AI must not copy code from AutoBGI into this repository. It can be used as a behavioral reference or integrated as an external process/API selected by the user.

## What AutoBGI Is

AutoBGI is an operations layer around an existing BetterGI installation. It adds:

- Web UI and REST API
- BetterGI launch helpers
- one-dragon and script-group orchestration
- cron/scheduled tasks
- log analysis and progress status
- notification integrations
- OBS/recording helpers
- backup/update utilities
- an MCP-over-SSE endpoint for a small subset of capabilities

It does not replace BetterGI's core CV/OCR/input automation. Its execution layer still launches `BetterGI.exe` for the main BetterGI tasks.

## BetterGI Launch Bridge

`task/Task.go` is the clearest reference for practical BetterGI invocation:

| AutoBGI function | BetterGI command | Notes |
| --- | --- | --- |
| `StartOneDragon(name)` | `BetterGI.exe --startOneDragon <name>` | Matches BetterGI source CLI |
| `StartGroups(names)` | `BetterGI.exe --startGroups <names...>` | Matches BetterGI source CLI |
| `StartOneDragonPlan(planName)` | `BetterGI.exe --startContinuousOneDragon <planName>` | Found in AutoBGI only; not found in current BetterGI source CLI parser |

AutoBGI sets `cmd.Dir` to `config.Cfg.BetterGIAddress`, checks whether `BetterGI.exe` exists, starts the process, sleeps, and checks whether the process is running. That pattern is useful, but BetterGI AI should implement it independently with stricter validation and job tracking.

## Configuration

AutoBGI's `main.json` config includes:

- `BetterGIAddress`: BetterGI install directory
- `BgiLog`: inferred BetterGI log path
- `Control.IsMcp`: whether AutoBGI's MCP endpoint is enabled
- notification settings
- screen recording settings
- account and remote/session settings
- AI settings under `AbgiAiConfig`

BetterGI AI should not require AutoBGI config, but an optional `autobgi-http` adapter could use:

- base URL
- API key/token
- selected endpoints to call

## REST API Surface

The Vue frontend API wrapper shows the public operational shape. Important endpoint groups include:

| Area | Example endpoints | BetterGI AI relevance |
| --- | --- | --- |
| Status | `GET /api/index`, `GET /api/indexSX`, `GET /api/appInfo` | Optional read-only status source |
| One-dragon | `GET /api/oneLong/oneLongAllName`, `POST /api/oneLong/startOneLong`, `GET /api/oneLong/unfinishedOneLong` | Could back `tasks.list` and one-dragon launch |
| Script groups | `GET /api/scriptGroup/listGroups`, `POST /api/startGroups`, `GET /api/scriptGroup/listAllGroups` | Could back group listing/launch |
| Logs | `GET /api/logFiles`, `GET /api/logAnalysis`, `GET /api/autoLog` | Could back `runner.logs` |
| Cron | `GET /api/taskCron/list`, `POST /api/taskCron/add`, `POST /api/taskCron/AtOnceRun` | Too broad for default agent surface; maybe future scheduler |
| Config | `GET /api/config`, `POST /api/saveConfig`, BetterGI config endpoints | Read-only initially; mutating config is high risk |
| Backup/update | `/api/backup`, `/api/updateABgi`, `/api/uploadBgi`, repo/script update endpoints | Do not expose to agents by default |
| System control | `/api/closeBgi`, `/closeYuanShen`, hotkey endpoints | High risk; require explicit user-facing controls if ever exposed |
| Inventory/statistics | bag/material endpoints, archive endpoints, collection endpoints | Useful read-only context if user wants it |
| Recording/remote | OBS and 1Remote endpoints | Out of scope for initial BetterGI AI adapter |

The full backend route table was not downloaded, so this list should be treated as endpoint evidence from the frontend and selected backend files, not as a complete OpenAPI contract.

## MCP Surface

AutoBGI exposes MCP over SSE:

- `GET/POST /mcp/sse`
- `POST /mcp/messages?sessionId=...`
- message requests require header `apiKey` matching AutoBGI auth config

Tools found in `MCP/server.go`:

| Tool | Purpose | Notes |
| --- | --- | --- |
| `findBgiIndex` | Query current BetterGI progress/status | Useful read-only reference |
| `RunCronTask` | Run or schedule a named task with optional params/delay | Powerful and broad; not safe as a default direct agent passthrough |
| `queryBackpack` | Query material count from backpack/statistics data | Optional read-only context |

Tasks registered in `MCP/service.go` include launching one-dragon, closing Genshin/BetterGI, HoYoLAB sign-in, launching config groups, and backing up `User`. Some strings are mojibake in the local snapshot, but the behavior is clear from function calls.

## Auth and Security

AutoBGI auth accepts an API key/token style gate. The MCP message endpoint requires `apiKey`; REST auth is handled by middleware that accepts configured auth headers/query values.

For BetterGI AI, AutoBGI should be considered a privileged local automation service. Calling it gives access to more than BetterGI task launch:

- close applications
- update BetterGI/scripts
- run cron tasks
- modify config
- back up user data
- trigger notifications/recording/remotes

Therefore an `autobgi-http` adapter should be opt-in and allowlist individual operations instead of forwarding arbitrary AutoBGI tools.

## Can AutoBGI Replace BetterGI AI?

Not cleanly.

AutoBGI can already do many operational tasks, including a small MCP surface, so it can be useful if the user already runs it. But it exposes a broader, higher-permission control surface than BetterGI AI wants to give directly to an LLM.

BetterGI AI still adds value as:

- a stable, narrow agent-facing protocol
- dry-run and allowlist enforcement
- job state and cancellation semantics
- local/SSH runner transport
- adapter independence between direct BetterGI CLI and AutoBGI HTTP/MCP
- a place to normalize logs/status from whichever backend is active

## Recommended Use

Implement AutoBGI as an optional adapter later:

- `adapter: "autobgi-http"`
- required config: base URL and credential
- read-only methods first: status, logs, one-dragon list, script-group list
- mutating methods only after allowlist confirmation: start one-dragon, start script group

Do not use AutoBGI's MCP as the primary BetterGI AI MCP. That would put an MCP server behind another MCP server while also bypassing BetterGI AI's policy model.

