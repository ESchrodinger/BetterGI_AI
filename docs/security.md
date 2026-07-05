# Security and Safety

This project controls local automation around BetterGI, AutoBGI, and a live game window. Treat it as a privileged local automation surface.

## Default Policy

- Expose semantic BetterGI/AutoBGI workflows, not raw input primitives.
- Prefer read-only status and inventory before any mutation.
- Require an exact user-approved target before starting one-dragon or config-group execution.
- Refuse unknown task names and broad AutoBGI scheduler actions.
- Use BetterGI's local JSON files as structured data; do not edit by ad hoc string replacement.
- Keep secrets and machine-local paths out of Git.

## Agent Boundary

Agents may:

- inspect BetterGI local inventory
- edit approved BetterGI JSON config files with backups
- search local BetterGI repository indexes
- call the safe AutoBGI MCP subset

Agents must not:

- directly send keyboard or mouse events
- run arbitrary shell, PowerShell, Python, BAT, or JS through AutoBGI
- modify account credentials, cookies, API keys, or game settings
- start unknown or broad scheduler tasks
- retry failed automation loops without reading status/log context

## Data Boundary

Do not commit:

- `.bettergi-ai/`
- `.env` files
- BetterGI or AutoBGI logs
- screenshots or captures
- cookies, API keys, tokens, UIDs tied to accounts, or other secrets
- BetterGI `User` data from a real user profile

## Higher-Risk Tools

- `captureDesktopScreenshot` is allowed only when the user asks for visual verification and may expose visible desktop/app data.
- `queryCharacterBuild` is allowed only for one named character requested by the user and may depend on local AutoBGI account configuration.
- `collectMaterialRoutes` and `collectCookingRoutes` are disabled until a dedicated route-planning policy exists.
