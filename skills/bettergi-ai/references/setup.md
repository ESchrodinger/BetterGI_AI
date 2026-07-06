# Setup

Use this when BetterGI path, AutoBGI path, MCP URL, or apiKey is unknown.

Prerequisites for new users:

1. BetterGI must be installed first. This skill edits BetterGI local config and lets BetterGI execute game automation; it does not ship or replace BetterGI.
2. AutoBGI must be installed second. This skill uses AutoBGI as the preferred MCP/Web execution service; it does not implement its own runner.
3. AutoBGI must be configured with the BetterGI install path, and MCP must be enabled in AutoBGI settings before MCP execution can work.
4. If either install path is missing and discovery fails, tell the user to install the missing upstream project and provide the install directory.

Do not assume fixed install paths. Ask the user when discovery is ambiguous.

Do not hard-code a user's local install path into this project or skill. Store user-specific paths only in local settings or use them for the current task. For reusable logic, prefer explicit user input, environment variables (`BETTERGI_HOME`, `AUTOBGI_HOME`), validation of known app markers, or bounded discovery.

Local settings shape:

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

Discover:

```bash
python scripts/resolve_bettergi_autobgi.py --discover
```

Validate AutoBGI MCP:

```bash
python scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

Validate encoding-sensitive config handling after changes:

```bash
python scripts/run_encoding_smoke_tests.py
```

Initialize PowerShell UTF-8 handling before using PowerShell to inspect Chinese files:

```powershell
. .\scripts\Use-Utf8PowerShell.ps1
```

See `references/windows-encoding.md` when Chinese output appears garbled.

AutoBGI MCP defaults:

- URL: `http://127.0.0.1:10086/mcp/sse`
- apiKey: `abgi`

MCP connection contract for agents:

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

Use the example above only as the default local shape. Derive the real values before blaming MCP:

- `url` is the AutoBGI Web service base plus `/mcp/sse`.
- The local default is `http://127.0.0.1:10086/mcp/sse`.
- If AutoBGI runs on another host, replace `127.0.0.1` with that host or LAN IP and keep `/mcp/sse`.
- The port comes from AutoBGI `main.json` field `post`. For example, `":10086"` means `http://127.0.0.1:10086/mcp/sse`.
- If `post` is empty or `":"`, AutoBGI source code falls back to `:8082`.
- `apiKey` comes from AutoBGI `abgiUser.yaml` field `auth.api_key`. The generated default is usually `abgi`, but agents should read the actual file or ask the user when it differs.
- The HTTP header name is exactly `apiKey`. Do not use `Authorization`, and do not reuse a Web login token as the MCP key.
- Web login is separate from MCP. The browser being logged out does not prevent MCP from starting when `Control.IsMcp=true` and the request has the correct `apiKey` header.

AutoBGI local config:

- Main config: `<AutoBGI installPath>\main.json`
- Web/MCP auth config: `<AutoBGI installPath>\abgiUser.yaml`
- Web/MCP service port: `main.json` field `post`, for example `":10086"`
- MCP switch: `main.json` field `Control.IsMcp`
- MCP route: `/mcp/sse` on the same service port as AutoBGI Web
- Source fallback: if `post` is empty or `":"`, AutoBGI falls back to `:8082`

MCP must be enabled before agents can connect:

```json
{
  "Control": {
    "IsMcp": true
  }
}
```

After changing `main.json`, restart AutoBGI from its install directory so it loads the same config file. BetterGI does not need to be opened first; in fact, for execution, let AutoBGI launch BetterGI.

Recommended restart command:

```bash
python scripts/manage_bettergi_lifecycle.py --action restart-autobgi
```

Use this after changing `Control.IsMcp`, `post`, the BetterGI path, or any AutoBGI Web/MCP setting. The lifecycle script should stop the existing `auto-bgi.exe`, start AutoBGI from its install directory, then report enough status for the agent to verify that AutoBGI loaded the intended config. If the script cannot find AutoBGI, ask the user for the AutoBGI install directory and save it only in local settings.

Manual restart fallback:

1. Close the old AutoBGI process or use AutoBGI's bundled restart helper when the user points to it.
2. Start AutoBGI from the AutoBGI install directory, not from an arbitrary shell working directory.
3. Verify the PID or process start time changed.
4. Verify the Web service is on the port derived from `main.json.post`.
5. Verify MCP with the `apiKey` header before attempting `RunCronTask`.

Manual connection check:

```bash
curl.exe -i -N --max-time 5 -H "apiKey: abgi" http://127.0.0.1:10086/mcp/sse
```

Expected signs:

- HTTP success status.
- `Content-Type: text/event-stream`.
- An SSE line such as `event: endpoint`.

Common failures:

- `connection_refused`: AutoBGI is not running, the port is wrong, or an old process is serving a different config.
- `http_401` or `http_403`: `apiKey` is wrong. Read `abgiUser.yaml` or ask the user.
- `http_404`: the path is wrong; MCP lives at `/mcp/sse`.
- HTML or another non-SSE response: AutoBGI Web is reachable but MCP is not registered on that running instance. Check `Control.IsMcp=true`, restart AutoBGI, then probe again.
- Timeout from `Invoke-WebRequest` or `curl` after receiving `event: endpoint`: this can be normal because SSE connections stay open. Treat the response headers and endpoint event as success.
- `10086` vs `8082` mismatch: `main.json.post` may not have been loaded, `post` may be empty, or AutoBGI may have been started from the wrong working directory. Restart AutoBGI and verify the listening port again.

Always read AutoBGI `main.json` as UTF-8 and tolerate UTF-8 BOM. Do not trust Windows PowerShell's default text decoding for JSON with Chinese text; it can corrupt strings in memory and create a false JSON parse error. Use Python `encoding="utf-8"` with a UTF-8-SIG fallback, or PowerShell raw bytes plus `[System.Text.Encoding]::UTF8.GetString(...)`.

Only ask for MCP URL/apiKey when the default endpoint and the URL derived from `main.json.post` both fail, or when the user says AutoBGI uses a non-default port/key. If the probe fails, report the structured error JSON instead of saying only that the probe script failed.

Never print or commit real API keys, cookies, tokens, or account secrets.
