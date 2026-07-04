# Development Plan

## M0: Architecture and Protocol

- Document module boundaries.
- Define runner JSON-RPC protocol.
- Define default safety policy.
- Add local and SSH configuration examples.

## M1: Project Skeleton

- Create protocol package.
- Create MCP server package.
- Create Windows runner project.
- Create BetterGI agent skill.

## M2: Runner MVP

- Implement `runner.detect`.
- Implement `runner.status`.
- Implement `runner.capabilities`.
- Implement `runner.logs`.
- Implement `runner.stop`.

## M3: MCP MVP

- Implement MCP `initialize`.
- Implement `tools/list`.
- Implement `tools/call`.
- Proxy accepted calls to runner over local stdio.
- Add SSH stdio transport.

## M4: BetterGI Adapter

- Document BetterGI and AutoBGI integration surfaces. Done in `docs/adapters`.
- Add config-driven BetterGI path detection. Done in runner scaffold.
- Read BetterGI logs. Done for configured log directories.
- List BetterGI one-dragon/script-group inventory with allowlist state. Done through runner inventory scanning and policy context.
- Start allowlisted jobs.
- Track job status.

## M5: Skill and Operational Rules

- Create an AutoBGI safe-control skill for quick landing. Done in `skills/autobgi-safe-control`.
- Teach agents to call detection before mutating tasks.
- Require log inspection before retries.
- Require allowlisted task names.
- Prefer stop over repeated corrective actions.

## M5a: AutoBGI Fast Path

- Use AutoBGI MCP as the first practical control path.
- Restrict agents to `findBgiIndex`, `queryBackpack`, and immediate `RunCronTask` for allowlisted one-dragon/config-group launches.
- Keep shutdown, backup, updates, arbitrary cron, hotkeys, config mutation, recording, and remote-control operations out of the skill.
- Later, move these rules into a BetterGI AI `autobgi` adapter for programmatic enforcement.

## M6: Release Hardening

- Add tests for protocol and transport.
- Add config schema validation.
- Add Windows publish scripts.
- Add setup documentation.
