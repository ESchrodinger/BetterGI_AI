# Status

Use this for current progress, "what is BetterGI doing", "is AutoBGI idle", or "what can you do now".

Read AutoBGI progress first when available:

```bash
python scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
```

Check BetterGI/AutoBGI versions when the user asks whether updates are needed:

```bash
python scripts/check_upstream_versions.py --output .bettergi-ai/status/versions.json
```

This is read-only. If `canUpdate` is true, report the current and latest versions and ask for explicit approval before any update action.

Probe failure handling:

- `probe_autobgi_mcp.py` defaults to `http://127.0.0.1:10086/mcp/sse` with apiKey `abgi` when local settings and AutoBGI `main.json` are unavailable.
- When an AutoBGI install path is known, derive the MCP URL from `main.json.post` and append `/mcp/sse`. If `post` is empty or `":"`, AutoBGI's source fallback is `:8082`.
- Read the actual MCP key from `abgiUser.yaml` field `auth.api_key` when the default key fails. The MCP header name is `apiKey`.
- If the probe exits non-zero, read and report the JSON written to stderr, especially `category`, `error`, and `hints`.
- Do not stop at "probe script failed". Classify the failure:
  - `connection_refused`: AutoBGI is probably not running or not listening on the configured port. Check `main.json.post`, fallback `:8082`, and whether an old process is still running.
  - `connection_timeout` / `mcp_timeout`: AutoBGI may be hung, blocked by firewall, or using a different endpoint.
  - `http_401` / `http_403`: apiKey is likely wrong.
  - `http_404`: the MCP path is wrong; use `/mcp/sse`.
  - `mcp_not_enabled_or_wrong_route`: AutoBGI Web is reachable but did not return SSE. Check `Control.IsMcp=true`, then restart AutoBGI from the install directory.
  - `policy_rejected`: the tool call was blocked by BetterGI AI policy; this is not a connectivity failure.
  - Python command not found: report that the local Python launcher is unavailable and use direct MCP tools if the agent has them, or ask the user to expose Python in PATH.
- If `findBgiIndex` is unavailable, say MCP progress is unavailable and report only local inventory. Do not pretend AutoBGI is idle.

Restart after config or port mismatch:

```bash
python scripts/manage_bettergi_lifecycle.py --action restart-autobgi
python scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
```

After restart, report whether the AutoBGI PID/start time changed and whether `/mcp/sse` returned `Content-Type: text/event-stream` plus an `event: endpoint` line. Do not claim the user is logged in or the task is running based only on the Web page loading.

Summarize status plus local inventory:

```bash
python scripts/summarize_bettergi_capabilities.py --status-json .bettergi-ai/status/findBgiIndex.json
```

Safe next actions when idle:

- inspect configs
- edit one-dragon JSON
- edit script groups
- search installed/repository scripts
- query backpack
- launch a validated one-dragon or config group after explicit user intent
