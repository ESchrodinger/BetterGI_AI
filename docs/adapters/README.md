# Integration Research

This directory records how BetterGI AI pairs with BetterGI and AutoBGI.

## Current Decision

Publish one skill package: `skills/bettergi-ai`.

The package has one installed entry point, `SKILL.md`, and focused internal references for setup, status, lifecycle, BetterGI JSON configuration, script repository work, one-dragon settings, and constrained AutoBGI MCP execution.

AutoBGI is the primary execution path. BetterGI AI should configure BetterGI and AutoBGI, read BetterGI's local options dynamically, and call only the constrained AutoBGI MCP subset for status/query/launch.

## Package Architecture

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

The top-level skill chooses one reference and loads only what is needed.

## AutoBGI MCP Safe Subset

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`, explicit visual verification only
- `queryCharacterBuild`, one requested character only
- `RunCronTask`, restricted to immediate `启动一条龙` or `启动配置组`

Disabled until separate workflows exist:

- continuing one-dragon plans
- shutdown/backup/sign-in/update/scheduler actions
- OBS recording control
- broad account data reads
- material/cooking route collection
- arbitrary shell or remote-control behavior

See:

- [BetterGI capability map](bettergi-capability-map.md)
- [AutoBGI capability map](autobgi-capability-map.md)
