# Lifecycle

Normal relationship:

```text
BetterGI AI -> start/check AutoBGI -> AutoBGI MCP -> BetterGI -> Genshin, if BetterGI opens it
```

BetterGI AI should start/check AutoBGI first. Do not open BetterGI before an AutoBGI MCP execution command, because AutoBGI's BetterGI command-line launch can fail when BetterGI is already running. Let AutoBGI start BetterGI, then let BetterGI start/control Genshin.

Direct BetterGI startup is a troubleshooting fallback only. Do not directly start Genshin from this skill.

Check local process/service status:

```bash
python scripts/manage_bettergi_lifecycle.py --action status
```

Start AutoBGI only after user intent:

```bash
python scripts/manage_bettergi_lifecycle.py --action start-autobgi
```

Restart AutoBGI when config changes or the live port does not match `main.json.post`:

```bash
python scripts/manage_bettergi_lifecycle.py --action restart-autobgi
```

Use restart when:

- `Control.IsMcp` changed.
- `main.json.post` changed.
- AutoBGI Web loads but `/mcp/sse` returns HTML, 404, or non-SSE content.
- AutoBGI is listening on `8082` while config says `10086`, or any other port mismatch appears.
- The user changed the BetterGI path in AutoBGI.

Restart rules:

1. Prefer the lifecycle script because it stops the old `auto-bgi.exe`, starts AutoBGI from its install directory, and probes Web/MCP after restart.
2. If using AutoBGI's bundled `restart.bat`, verify the PID and process start time changed. Treat unchanged PID/start time as restart failure.
3. After restart, verify the process path is the expected AutoBGI executable, the Web port matches `main.json.post`, and the old fallback port is no longer serving the same instance.
4. Verify MCP with headers, not browser login: `GET <serviceUrl>/mcp/sse` with `apiKey` from `abgiUser.yaml` should return `Content-Type: text/event-stream` and an `event: endpoint` line.
5. `Invoke-WebRequest` may time out on `/mcp/sse` because SSE is a long-lived stream. A timeout after headers is not proof of failure; check headers or use `curl.exe -i -N --max-time 5 -H "apiKey: <key>" <url>`.

Manual restart fallback:

1. Ask the user for the AutoBGI install directory if discovery is ambiguous.
2. Stop the existing AutoBGI process.
3. Start `auto-bgi.exe` from the AutoBGI install directory so relative config files such as `main.json` and `abgiUser.yaml` resolve correctly.
4. Re-run `python scripts/manage_bettergi_lifecycle.py --action status`.
5. Re-run `python scripts/probe_autobgi_mcp.py --call-tool findBgiIndex`.

Do not treat opening the AutoBGI Web page as enough. A usable MCP restart requires the SSE endpoint and `apiKey` header to work.

Before any execution:

1. Confirm AutoBGI process or HTTP service is running.
2. Read `findBgiIndex`.
3. Validate exact one-dragon/config-group target.
4. If BetterGI is already running, warn that AutoBGI command-line launch may fail and ask whether to continue, stop BetterGI, or wait. Do not silently open another BetterGI instance.
5. Use AutoBGI MCP `RunCronTask` only for the allowed immediate launch form.
6. Report the actual MCP call result or error, then read `findBgiIndex` again. If there is no MCP result, say the launch was not verified.
