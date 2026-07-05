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

Never print or commit real API keys, cookies, tokens, or account secrets.
