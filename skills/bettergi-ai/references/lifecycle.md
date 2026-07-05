# Lifecycle

Normal relationship:

```text
BetterGI AI -> start/check AutoBGI -> AutoBGI MCP -> BetterGI -> Genshin, if BetterGI opens it
```

BetterGI AI should start/check AutoBGI first. Direct BetterGI startup is a troubleshooting fallback. Do not directly start Genshin from this skill.

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
4. Use AutoBGI MCP `RunCronTask` only for the allowed immediate launch form.
