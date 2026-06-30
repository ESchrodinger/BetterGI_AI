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

## Current Skeleton

- `docs/architecture.md`: module boundaries and BetterGI separation rules.
- `docs/protocol.md`: runner JSON-RPC method contract.
- `docs/security.md`: default safety and allowlist policy.
- `examples/dev-mock.config.json`: local mock config for development on macOS.
- `examples/windows-local.config.json`: Windows local runner config shape.
- `examples/mac-ssh.config.json`: macOS-to-Windows SSH config shape.

## Development Commands

Run the MCP smoke test against the local mock runner:

```bash
npm test
```

Start the MCP server with the local mock runner:

```bash
npm run mcp:dev
```

Start only the mock runner:

```bash
npm run runner:mock
```

The production runner is scaffolded as a .NET 8 project under `packages/runner`; build and publish it on Windows or another host with the .NET SDK installed.
