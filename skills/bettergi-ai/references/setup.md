# Setup

Use this when BetterGI path, AutoBGI path, MCP URL, or apiKey is unknown.

Do not assume fixed install paths. Ask the user when discovery is ambiguous.

Local settings shape:

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

Discover:

```bash
python scripts/resolve_bettergi_autobgi.py --discover
```

Validate AutoBGI MCP:

```bash
python scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

AutoBGI MCP defaults:

- URL: `http://127.0.0.1:10086/mcp/sse`
- apiKey: `abgi`

Only ask for these values when the default endpoint fails or the user says AutoBGI uses a non-default port/key. If the probe fails, report the structured error JSON instead of saying only that the probe script failed.

Never print or commit real API keys, cookies, tokens, or account secrets.
