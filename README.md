# BetterGI AI

BetterGI AI is a single Codex skill package and local helper toolkit for pairing BetterGI with AutoBGI.

It does not replace BetterGI, reimplement game automation, or build a separate execution engine. BetterGI stays as the upstream desktop automation app. AutoBGI is the preferred execution service through its MCP SSE endpoint.

## Published Skill

Install or copy only this directory:

```text
skills/bettergi-ai
```

The package contains:

- `SKILL.md`: the only installed skill entry point.
- `references/`: internal focused guides for setup, status, lifecycle, config editing, one-dragon, and AutoBGI safe control.
- `scripts/`: deterministic Python helpers for BetterGI JSON and AutoBGI MCP.

## Internal Architecture

`bettergi-ai` is the single outer skill. It routes internally to focused references:

```text
skills/bettergi-ai/SKILL.md
  -> references/setup.md
  -> references/status.md
  -> references/lifecycle.md
  -> references/config-editor.md
  -> references/one-dragon.md
  -> references/autobgi-safe-control.md
  -> scripts/*.py
```

Agents should load only the reference needed for the user's request.

## Local Settings

Machine-local settings are kept out of Git. The helper scripts read `.bettergi-ai/local.settings.json` when present:

```json
{
  "bettergi": {
    "installPath": "C:\\Program Files\\BetterGI"
  },
  "autobgi": {
    "installPath": "C:\\Tools\\autobgi",
    "mcp": {
      "url": "http://127.0.0.1:10086/mcp/sse",
      "apiKey": "..."
    }
  }
}
```

Do not commit real API keys, cookies, account data, logs, screenshots, or BetterGI user data.

## Useful Commands

Run BetterGI config helper smoke tests:

```bash
python skills/bettergi-ai/scripts/run_bettergi_config_smoke_tests.py
```

By default this creates a temporary BetterGI fixture so the helper logic can be
validated on macOS, Linux, or Windows without a real BetterGI installation.
Validate against a real BetterGI install when available:

```bash
python skills/bettergi-ai/scripts/run_bettergi_config_smoke_tests.py --install-path "C:\Program Files\BetterGI"
```

Probe AutoBGI MCP tools:

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

Validate AutoBGI MCP tool policy offline:

```bash
python skills/bettergi-ai/scripts/run_autobgi_policy_smoke_tests.py
```

Read AutoBGI progress and summarize safe capabilities:

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
python skills/bettergi-ai/scripts/summarize_bettergi_capabilities.py --status-json .bettergi-ai/status/findBgiIndex.json
```

## Safety Shape

The default AutoBGI MCP subset is:

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`, only when the user explicitly asks for visual verification
- `queryCharacterBuild`, only for one user-requested character
- `RunCronTask`, only for immediate `启动一条龙` or `启动配置组` with a user-approved target

Everything else is disabled until a dedicated workflow and policy are added.
