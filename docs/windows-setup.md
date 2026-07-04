# Windows Setup

Use this guide to continue BetterGI AI development on Windows.

## Repository

Clone the private repository and switch to the active branch:

```powershell
git clone https://github.com/ESchrodinger/BetterGI_AI.git
cd BetterGI_AI
git switch codex/agent-control-plane
```

Before each work session:

```powershell
git pull
git status
```

After each scoped change:

```powershell
git status
git add <files>
git commit -m "type(scope): summary"
git push
```

## Required Tools

- Git
- .NET 8 SDK
- Node.js 20 or newer
- BetterGI installed and configured
- Optional: Windows OpenSSH Server for Mac-to-Windows runner validation

Check tools:

```powershell
git --version
dotnet --version
node --version
npm --version
```

## Build Runner

```powershell
dotnet build .\packages\runner\BetterGi.AgentRunner.sln
```

Publish a self-contained Windows runner:

```powershell
dotnet publish .\packages\runner\src\BetterGi.AgentRunner `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -o C:\Tools\bettergi-runner
```

## Local Runner Smoke

The runner speaks newline-delimited JSON-RPC over stdio. From PowerShell:

```powershell
$request = '{"jsonrpc":"2.0","id":"1","method":"runner.detect","params":{"context":{"protocolVersion":"0.1.0","bettergi":{},"policy":{"allowTasks":[],"allowScripts":[],"requireSingleActiveJob":true}}}}'
$request | C:\Tools\bettergi-runner\bettergi-runner.exe rpc --stdio
```

Expected: one JSON-RPC response with `protocolVersion`, `runner`, `bettergi`, and `game`.

## BetterGI Paths

Create a local config copied from `examples/windows-local.config.json` and adjust paths for the Windows machine. Do not commit local machine paths or secrets unless they are generic examples.

The runner can infer BetterGI subdirectories from `installPath`, but explicit paths are useful when the install layout differs:

```json
{
  "bettergi": {
    "installPath": "C:\\Program Files\\BetterGI",
    "executablePath": "C:\\Program Files\\BetterGI\\BetterGI.exe",
    "logDirectory": "C:\\Program Files\\BetterGI\\log",
    "userDirectory": "C:\\Program Files\\BetterGI\\User",
    "oneDragonDirectory": "C:\\Program Files\\BetterGI\\User\\OneDragon",
    "scriptGroupDirectory": "C:\\Program Files\\BetterGI\\User\\ScriptGroup",
    "scriptDirectory": "C:\\Program Files\\BetterGI\\User\\JsScript"
  }
}
```

Recommended local file name:

```text
examples/windows-local.config.local.json
```

This file is ignored by Git through `*.local.json`.

## Windows Acceptance Criteria

The next Windows-side milestone is complete when:

- `dotnet build` succeeds.
- `dotnet publish` creates `C:\Tools\bettergi-runner\bettergi-runner.exe`.
- `runner.detect` returns `isWindows: true`.
- BetterGI install/log/script paths are reflected in `runner.detect`.
- `runner.logs` can read the configured BetterGI log directory, or reports a clear unavailable reason.
- Non-dry-run `tasks.run` still refuses execution with `BetterGI execution adapter is not configured yet`.

Do not start real BetterGI tasks until a concrete adapter is designed and reviewed.
