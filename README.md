# BetterGI AI

Portable agent control plane for integrating BetterGI with MCP servers, skills, and local or SSH-based runners.

## Git Workflow

- Keep `main` as the stable integration branch.
- Use short feature branches such as `codex/setup-runner`, `codex/mcp-server`, or `codex/ssh-transport`.
- Use conventional commits with the repository template:
  - `feat(mcp): add status tool`
  - `fix(runner): handle missing BetterGI process`
  - `docs(skill): describe safe task invocation`
- Keep machine-local settings in `*.local.json` or `.env`; commit example files instead.

## Planned Modules

- `packages/mcp-server`: cross-platform MCP server exposed to agents.
- `packages/runner`: Windows-side runner that talks to BetterGI.
- `packages/protocol`: shared JSON schemas and transport contracts.
- `skills/bettergi-agent`: agent usage guide and safety rules.
