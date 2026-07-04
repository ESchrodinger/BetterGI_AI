# Prompt for Windows Codex

You are continuing the BetterGI_AI project on Windows.

Open this repository:

```text
BetterGI_AI
```

Use branch:

```text
codex/agent-control-plane
```

First read:

```text
docs/handoff/windows-codex-handoff.md
docs/windows-setup.md
docs/architecture.md
docs/protocol.md
docs/security.md
```

Then do the following:

1. Run `git pull` and confirm the working tree is clean.
2. Check `dotnet --version`, `node --version`, and `npm --version`.
3. Run `powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify-runner.ps1`.
4. Fix any Windows-specific compile or runtime issues in `packages/runner`.
5. Keep BetterGI separated. Do not modify upstream BetterGI. Do not implement real task execution until the adapter design is explicit.
6. Commit and push each coherent change to `codex/agent-control-plane`.

Immediate target: make the .NET runner build and respond to `runner.detect`, `runner.status`, `runner.logs`, `tasks.list`, and dry-run `tasks.run` on Windows.
