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

Before any execution:

1. Confirm AutoBGI process or HTTP service is running.
2. Read `findBgiIndex`.
3. Validate exact one-dragon/config-group target.
4. If BetterGI is already running, warn that AutoBGI command-line launch may fail and ask whether to continue, stop BetterGI, or wait. Do not silently open another BetterGI instance.
5. Use AutoBGI MCP `RunCronTask` only for the allowed immediate launch form.
6. Report the actual MCP call result or error, then read `findBgiIndex` again. If there is no MCP result, say the launch was not verified.
