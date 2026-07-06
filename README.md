# BetterGI AI

[中文说明](README.zh-CN.md)

BetterGI AI is a single Codex skill package and local helper toolkit for pairing BetterGI with AutoBGI.

It does not replace BetterGI, reimplement game automation, or build a separate execution engine. BetterGI stays as the upstream desktop automation app. AutoBGI is the preferred execution service through its MCP SSE endpoint.

## Prerequisites

New users must install the two upstream applications before this skill can run real tasks:

- BetterGI: install the desktop automation app from the official BetterGI docs/download page.
- AutoBGI: install AutoBGI from its upstream project/releases, then configure it with the BetterGI install path.

After installation, open AutoBGI settings, set the BetterGI path, enable MCP, and note the AutoBGI Web/MCP service port and apiKey. This repository only provides the agent skill and helper scripts; it does not bundle BetterGI, AutoBGI, or a separate runner.

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
    "installPath": "C:\\Path\\To\\BetterGI"
  },
  "autobgi": {
    "installPath": "C:\\Path\\To\\AutoBGI",
    "mcp": {
      "url": "http://127.0.0.1:10086/mcp/sse",
      "apiKey": "..."
    }
  }
}
```

Do not commit real API keys, cookies, account data, logs, screenshots, or BetterGI user data.

## AutoBGI MCP Connection

Default local MCP client config:

```json
{
  "mcpServers": {
    "AutoBGI": {
      "type": "sse",
      "url": "http://127.0.0.1:10086/mcp/sse",
      "headers": {
        "apiKey": "abgi"
      }
    }
  }
}
```

The real URL is AutoBGI Web service base plus `/mcp/sse`. Read the service port from AutoBGI `main.json` field `post`; if `post` is empty or `":"`, AutoBGI falls back to `:8082`. Read the MCP key from AutoBGI `abgiUser.yaml` field `auth.api_key`; the header name is exactly `apiKey`.

MCP requires AutoBGI to be running and `main.json` `Control.IsMcp=true`. Web login is separate and is not required for MCP. After changing port, MCP switch, or BetterGI path, restart AutoBGI from its install directory:

```bash
python skills/bettergi-ai/scripts/manage_bettergi_lifecycle.py --action restart-autobgi
```

Then probe again:

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
```

## Useful Commands

Initialize a PowerShell session for UTF-8 Chinese text before inspecting or writing BetterGI/AutoBGI JSON through PowerShell:

```powershell
. .\skills\bettergi-ai\scripts\Use-Utf8PowerShell.ps1
```

Use Python helper scripts for JSON mutation whenever possible. If Chinese text looks garbled in PowerShell, re-read with `Get-Content -Encoding UTF8` or `Read-Utf8Text`; do not assume the file is corrupt.

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

Check upstream versions through AutoBGI's read-only Web APIs:

```bash
python skills/bettergi-ai/scripts/check_upstream_versions.py --output .bettergi-ai/status/versions.json
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

Agents must not invent BetterGI JavaScript/pathing/key-mouse entries. Script-group projects should be selected from local BetterGI inventory or repository search results, then validated before writing. Creating `User\ScriptGroup\<name>.json` or `User\OneDragon\<name>.json` does not execute anything; execution happens only through the constrained AutoBGI MCP `RunCronTask` flow after status checks.

For fuzzy user requests such as nicknames, "new domain", weekly bosses, or talent material sources, agents should search the web first to resolve the current canonical game names, then match those names against BetterGI's installed options or repository index. Web search clarifies intent; local BetterGI data decides what can actually run.
