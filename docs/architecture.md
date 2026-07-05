# Architecture

BetterGI AI is one Codex skill package plus local helper scripts for BetterGI and AutoBGI.

## Goals

- Keep BetterGI updateable as the upstream desktop automation application.
- Use AutoBGI as the preferred execution service through MCP SSE.
- Let agents configure BetterGI through safe, backed-up JSON edits.
- Let agents discover local BetterGI capabilities from installed files and repository indexes.
- Keep execution narrow, observable, and user-approved.

## Non-Goals

- Do not reimplement BetterGI OCR, computer vision, routing, combat, or input simulation.
- Do not inject into the game process or read game memory.
- Do not expose raw mouse, keyboard, shell, PowerShell, or arbitrary process control.
- Do not vendor BetterGI, AutoBGI, game data, logs, screenshots, cookies, or user secrets.
- Do not build or maintain a replacement execution engine while AutoBGI covers the execution path.

## Layers

```text
Agent
  -> bettergi-ai skill
      -> references/setup.md
      -> references/status.md
      -> references/lifecycle.md
      -> references/config-editor.md
      -> references/one-dragon.md
      -> references/autobgi-safe-control.md
      -> scripts/*.py
          -> AutoBGI MCP SSE
              -> AutoBGI
                  -> BetterGI
                      -> Genshin, if BetterGI opens it
```

## BetterGI Local Files

BetterGI remains installed outside this repository. The supported local surfaces are:

- `User\ScriptGroup`
- `User\OneDragon`
- `User\Subscriptions`
- `User\AutoPathing`
- `User\JsScript`
- `User\AutoFight`
- `Repos\<repo-folder>\repo.json`
- `Repos\<repo-folder>\repo_updated.json`

All writes must use structured JSON parsing, create backups where practical, and report changed fields.

## AutoBGI MCP

AutoBGI is treated as a privileged local operations service. The safe default subset is:

- read status through `findBgiIndex`
- read one material count through `queryBackpack`
- capture a desktop screenshot only when explicitly requested for visual verification
- query one named character build only when explicitly requested
- launch a validated one-dragon or config group through `RunCronTask`

Do not expose AutoBGI shutdown, backup, update, arbitrary cron, recording, hotkey, remote-control, broad account reads, or route collection tools by default.

## Versioning

The compatibility surfaces are:

- `skills/bettergi-ai/SKILL.md`
- `skills/bettergi-ai/references/*.md`
- helper script CLI arguments and JSON output
- local settings shape
- explicitly supported AutoBGI MCP tool names and schemas

Breaking changes should update docs and smoke tests together.
