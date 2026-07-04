# Windows Codex Handoff

Date: 2026-07-04

## Mission

Continue BetterGI AI development on Windows. The immediate goal is to validate and harden the Windows runner, not to execute real BetterGI automation yet.

## Current Branch

```text
codex/agent-control-plane
```

Remote:

```text
https://github.com/ESchrodinger/BetterGI_AI
```

Latest known commit on this branch:

```text
53bd03b feat(runner): add task allowlist surface
```

## Existing Architecture

The project separates the agent control plane from upstream BetterGI:

```text
Agent / MCP client
  -> packages/mcp-server
  -> local stdio or ssh stdio
  -> packages/runner
  -> BetterGI adapter
  -> upstream BetterGI
```

BetterGI should remain unmodified and updateable.

## What Already Works on Mac

- MCP server skeleton.
- Local mock runner.
- JSON-RPC over stdio.
- Tool mapping for:
  - `bettergi_detect`
  - `bettergi_status`
  - `bettergi_list_capabilities`
  - `bettergi_logs`
  - `bettergi_list_tasks`
  - `bettergi_run_task`
  - `bettergi_run_script`
  - `bettergi_job_status`
  - `bettergi_job_logs`
  - `bettergi_stop`
- Smoke test:

```bash
npm test
```

## Windows Work To Do First

1. Clone repo and switch branch:

```powershell
git clone https://github.com/ESchrodinger/BetterGI_AI.git
cd BetterGI_AI
git switch codex/agent-control-plane
```

2. Validate tools:

```powershell
git --version
dotnet --version
node --version
npm --version
```

3. Run Windows verification:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify-runner.ps1
```

4. Publish runner:

```powershell
dotnet publish .\packages\runner\src\BetterGi.AgentRunner `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -o C:\Tools\bettergi-runner
```

5. Run local JSON-RPC detect:

```powershell
$request = '{"jsonrpc":"2.0","id":"1","method":"runner.detect","params":{"context":{"protocolVersion":"0.1.0","bettergi":{},"policy":{"allowTasks":[],"allowScripts":[],"requireSingleActiveJob":true}}}}'
$request | C:\Tools\bettergi-runner\bettergi-runner.exe rpc --stdio
```

## Important Safety Boundary

Do not wire real task execution yet. Current `tasks.run` should:

- accept dry-runs for allowlisted tasks/scripts
- reject unknown tasks/scripts
- reject non-dry-run execution with `BetterGI execution adapter is not configured yet`

That refusal is intentional until the adapter design is reviewed.

## Recommended Next Implementation

Work in this order:

1. Fix any .NET compile issues on Windows.
2. Improve `runner.detect` on Windows:
   - BetterGI process names
   - Genshin process names
   - configured path existence
   - log/script directory existence
3. Improve `runner.logs`:
   - handle UTF-8/GBK logs if needed
   - read latest `.log` preferentially
   - avoid huge reads
4. Add Windows tests or smoke scripts.
5. Commit and push after each coherent change.

## Git Discipline

Before changing:

```powershell
git pull
git status
```

After a coherent change:

```powershell
git add <files>
git commit -m "fix(runner): ..."
git push
```

Avoid committing:

- `bin/`
- `obj/`
- `C:\Tools\bettergi-runner`
- local config files ending in `.local.json`
- BetterGI logs or screenshots
