# Development Plan

## Current Direction

BetterGI AI is a BetterGI + AutoBGI companion, not a replacement execution-engine project.

- BetterGI remains the upstream automation app and local configuration source.
- AutoBGI is the preferred execution service through MCP SSE.
- BetterGI AI owns setup, local JSON config editing, repository search/subscriptions, status summaries, lifecycle guidance, and safe agent-facing rules.

## Completed

- Documented the BetterGI and AutoBGI integration surfaces.
- Added BetterGI install and AutoBGI MCP local settings discovery.
- Added Python helpers for local BetterGI inventory, one-dragon edits, script-group edits, subscriptions, repository search, lifecycle checks, status summaries, and AutoBGI MCP probing.
- Added top-level and focused skills for setup, status, lifecycle, config editing, script repository work, one-dragon configuration, and AutoBGI safe control.
- Validated BetterGI config smoke tests against local JSON fixtures and human-confirmed BetterGI UI cases.
- Validated AutoBGI MCP handshake, `tools/list`, and `findBgiIndex`.

## Next

- Validate `RunCronTask` end to end with one explicitly approved one-dragon or config-group target.
- Add a dedicated collection-planner skill before enabling AutoBGI `collectMaterialRoutes` or `collectCookingRoutes`.
- Add more focused tests for each one-dragon setting block.
- Add install/copy guidance for publishing these skills into a user's Codex skill directory.
- Add code-level policy enforcement only after the skill workflows stabilize.
