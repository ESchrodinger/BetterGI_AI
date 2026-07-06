---
name: bettergi-ai
display_name: BetterGI AI
title: BetterGI AI skill
description: Single BetterGI + AutoBGI companion skill package. Use when an agent needs to set up BetterGI/AutoBGI paths, inspect status, edit BetterGI one-dragon or script-group JSON, search or update script subscriptions, reason about AutoBGI MCP tools, query backpack or character build data, capture BetterGI/AutoBGI screenshots on request, or launch a user-approved BetterGI one-dragon/config group through AutoBGI MCP.
homepage: https://github.com/ESchrodinger/BetterGI_AI
author: ESchrodinger
version: 0.2.0
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
| Ambiguous Genshin terms, nicknames, materials, weekly bosses, domains, or user shorthand | `references/intent-resolution.md` |
| AutoBGI MCP tools, allowed/disabled tools, execution | `references/autobgi-safe-control.md` |
| Upstream project docs, feature scope, version/update checks | `references/upstream-docs.md` |
| Windows PowerShell Chinese text or JSON appears garbled | `references/windows-encoding.md` |

Do not load all references by default.

## Core Rules

- Prefer read-only discovery before mutation.
- When the user's Genshin request is ambiguous or likely time-sensitive, search the web before mapping it to BetterGI config. Do not rely only on model memory for nicknames, new characters, new domains, weekly bosses, or material names.
- Use scripts in this skill's `scripts/` directory for deterministic local JSON edits and AutoBGI MCP probing.
- Do not bake a user's local BetterGI/AutoBGI install path into reusable code or docs; keep real paths in local settings or task-local commands only.
- Read AutoBGI and BetterGI JSON files as UTF-8 and tolerate UTF-8 BOM. Windows PowerShell default decoding can corrupt Chinese JSON text and create false parse failures.
- On Windows, initialize PowerShell UTF-8 handling with `scripts/Use-Utf8PowerShell.ps1` before reading/writing Chinese JSON or Markdown through PowerShell. Prefer Python helpers for JSON mutation.
- After changing JSON/config path handling, run `scripts/run_encoding_smoke_tests.py` to verify Chinese JSON, UTF-8 BOM, and AutoBGI MCP URL derivation.
- For version checks, use `scripts/check_upstream_versions.py` and report only read-only results unless the user explicitly approves an update.
- Do not edit credentials, cookies, API keys, account secrets, or unrelated BetterGI settings.
- Do not directly control Genshin, raw keyboard/mouse input, shell execution, or AutoBGI's broad scheduler.
- Do not invent BetterGI JavaScript, pathing, key-mouse, or shell script entries. Script-group projects must come from local BetterGI inventory or repository search results that the user chooses.
- Creating a script group is not execution. After creating `User\ScriptGroup\<name>.json`, either add/enable it in a target one-dragon config or launch it standalone through AutoBGI MCP `启动配置组` after status checks.
- Creating a one-dragon config is not execution. A new one-dragon config must explicitly enable concrete BetterGI tasks or existing script groups, then launch through AutoBGI MCP `启动一条龙` only after status checks and user-approved target validation.
- Derive AutoBGI MCP URL from AutoBGI `main.json` field `post` when an install path is known; MCP runs at `/mcp/sse` on the same port as AutoBGI Web. `:8082` is AutoBGI's fallback when `post` is empty.
- For execution, use AutoBGI MCP only after checking status and validating the exact user-approved target.
- Do not open BetterGI before an AutoBGI MCP execution command. AutoBGI's BetterGI command-line launch can fail when BetterGI is already open; let AutoBGI start BetterGI and let BetterGI start/control Genshin.
- When restarting AutoBGI, verify the PID/start time changed and then verify Web plus MCP SSE headers. AutoBGI Web login is not required for MCP; MCP requires `Control.IsMcp=true` and the correct `apiKey` header.
- After any execution attempt, report the actual MCP call result or error and then read `findBgiIndex` again. Do not claim that a task started without tool-result evidence.
- If `probe_autobgi_mcp.py` fails, report its structured JSON error (`category`, `error`, `hints`) and classify the cause. Do not say only "probe script failed".
- Creating or editing a script group only writes `User\ScriptGroup\<name>.json`. It does not automatically add that group to any one-dragon flow. After script-group changes, explicitly choose the run entry: add/enable it in a target one-dragon config, or launch it as a standalone config group through AutoBGI MCP `启动配置组`.

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
