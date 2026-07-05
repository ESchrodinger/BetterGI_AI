---
name: bettergi-ai
description: Single BetterGI + AutoBGI companion skill package. Use when an agent needs to set up BetterGI/AutoBGI paths, inspect status, edit BetterGI one-dragon or script-group JSON, search or update script subscriptions, reason about AutoBGI MCP tools, query backpack or character build data, capture BetterGI/AutoBGI screenshots on request, or launch a user-approved BetterGI one-dragon/config group through AutoBGI MCP.
---

# BetterGI AI

Use this as the only installed skill for BetterGI + AutoBGI work.

BetterGI remains the upstream desktop automation app. AutoBGI is the preferred execution service through MCP SSE. This skill provides setup, local JSON configuration, repository search, status, lifecycle, and safe execution rules.

## Route By Intent

Load only the reference needed for the request:

| Intent | Read |
| --- | --- |
| Unknown BetterGI/AutoBGI path, MCP URL, or apiKey | `references/setup.md` |
| Status, progress, "what can you do now" | `references/status.md` |
| Start/check/close AutoBGI, BetterGI, or Genshin relationship | `references/lifecycle.md` |
| Script groups, local inventory, subscriptions, repository search | `references/config-editor.md` |
| One-dragon config by BetterGI setting block | `references/one-dragon.md` |
| AutoBGI MCP tools, allowed/disabled tools, execution | `references/autobgi-safe-control.md` |

Do not load all references by default.

## Core Rules

- Prefer read-only discovery before mutation.
- Use scripts in this skill's `scripts/` directory for deterministic local JSON edits and AutoBGI MCP probing.
- Do not edit credentials, cookies, API keys, account secrets, or unrelated BetterGI settings.
- Do not directly control Genshin, raw keyboard/mouse input, shell execution, or AutoBGI's broad scheduler.
- For execution, use AutoBGI MCP only after checking status and validating the exact user-approved target.

## Script Path

When commands below refer to scripts, resolve them relative to this `SKILL.md`:

```text
scripts/
```

Example:

```bash
python scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

## Safe AutoBGI MCP Subset

Allowed by default:

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`, only when explicitly requested for visual verification
- `queryCharacterBuild`, only for one requested character
- `RunCronTask`, only immediate `启动一条龙` or `启动配置组` with `delayInSeconds=0`

Disabled until dedicated workflows exist:

- `continueOneDragon`
- `startObsRecording`
- `stopObsRecording`
- `collectMaterialRoutes`
- `collectCookingRoutes`
- shutdown, backup, sign-in, update, raw input, remote control, or arbitrary command execution
