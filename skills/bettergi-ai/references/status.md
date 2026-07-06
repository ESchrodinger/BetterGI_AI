# Status

Use this for current progress, "what is BetterGI doing", "is AutoBGI idle", or "what can you do now".

Read AutoBGI progress first when available:

```bash
python scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
```

Probe failure handling:

- `probe_autobgi_mcp.py` defaults to `http://127.0.0.1:10086/mcp/sse` with apiKey `abgi` when local settings are absent.
- If the probe exits non-zero, read and report the JSON written to stderr, especially `category`, `error`, and `hints`.
- Do not stop at "probe script failed". Classify the failure:
  - `connection_refused`: AutoBGI is probably not running or not listening on port `10086`.
  - `connection_timeout` / `mcp_timeout`: AutoBGI may be hung, blocked by firewall, or using a different endpoint.
  - `http_401` / `http_403`: apiKey is likely wrong.
  - `policy_rejected`: the tool call was blocked by BetterGI AI policy; this is not a connectivity failure.
  - Python command not found: report that the local Python launcher is unavailable and use direct MCP tools if the agent has them, or ask the user to expose Python in PATH.
- If `findBgiIndex` is unavailable, say MCP progress is unavailable and report only local inventory. Do not pretend AutoBGI is idle.

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
