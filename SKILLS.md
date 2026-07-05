# BetterGI AI Skill Package

This repository publishes one Codex skill:

```text
skills/bettergi-ai
```

Install or copy only that directory into a Codex skills directory, for example:

```text
C:\Users\10020\.agents\skills\bettergi-ai
```

## Internal Architecture

`bettergi-ai` is the single outer skill. It routes internally to focused references:

```text
bettergi-ai/SKILL.md
  -> references/setup.md
  -> references/status.md
  -> references/lifecycle.md
  -> references/config-editor.md
  -> references/one-dragon.md
  -> references/autobgi-safe-control.md
  -> scripts/*.py
```

The agent should load only the reference needed for the user's request.

## Responsibilities

- `setup.md`: BetterGI/AutoBGI path and MCP setup.
- `status.md`: AutoBGI `findBgiIndex` progress plus local BetterGI inventory.
- `lifecycle.md`: AutoBGI -> BetterGI -> Genshin startup relationship.
- `config-editor.md`: BetterGI JSON config groups, subscriptions, local inventory, and repository search.
- `one-dragon.md`: BetterGI one-dragon settings such as 自动秘境, 合成树脂, 自动地脉花, rewards, teapot, combat, and config groups.
- `autobgi-safe-control.md`: AutoBGI MCP allowed/disabled tools and execution policy.
- `scripts/`: deterministic Python helpers used by the references.

## Safe AutoBGI MCP Subset

Allowed by default:

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`, only when explicitly requested for visual verification
- `queryCharacterBuild`, only for one requested character
- `RunCronTask`, only immediate `启动一条龙` or `启动配置组` with `delayInSeconds=0`

Disabled until dedicated workflows exist:

- `continueOneDragon`
- OBS recording control
- `collectMaterialRoutes`
- `collectCookingRoutes`
- shutdown, backup, sign-in, update, raw input, remote control, or arbitrary command execution
