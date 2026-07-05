# Status

Use this for current progress, "what is BetterGI doing", "is AutoBGI idle", or "what can you do now".

Read AutoBGI progress first when available:

```bash
python scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
```

Summarize status plus local inventory:

```bash
python scripts/summarize_bettergi_capabilities.py --status-json .bettergi-ai/status/findBgiIndex.json
```

If `findBgiIndex` is unavailable, say MCP progress is unavailable and report only local inventory. Do not pretend AutoBGI is idle.

Safe next actions when idle:

- inspect configs
- edit one-dragon JSON
- edit script groups
- search installed/repository scripts
- query backpack
- launch a validated one-dragon or config group after explicit user intent
