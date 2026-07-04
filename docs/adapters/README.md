# Adapter Research

This directory captures integration research for BetterGI AI adapters.

## Current Decision

Use direct BetterGI CLI as the default first execution adapter, with AutoBGI as a future optional adapter.

| Option | Strength | Risk | Decision |
| --- | --- | --- | --- |
| Direct BetterGI CLI | Uses BetterGI's own supported entry points; no extra service required | Sparse status feedback; needs careful process/log handling | Default path |
| AutoBGI HTTP/MCP | Rich status, Web UI, cron, logs, notifications | Broad privileged surface; AGPL code cannot be copied; another service to configure | Optional later |
| Copy AutoBGI logic | Fast-looking shortcut | License and safety mismatch | Do not do |

## Next Implementation Target

The runner should gain a `bettergi-cli` adapter that can:

- discover configured BetterGI install/log/user paths
- list `User\OneDragon\*.json`
- list `User\ScriptGroup\*.json`
- tail BetterGI logs
- report BetterGI process state
- keep non-dry-run execution disabled until allowlist configuration exists

After that, enable allowlisted execution for:

- `BetterGI.exe --startOneDragon <name>`
- `BetterGI.exe --startGroups <name...>`

See:

- [BetterGI capability map](bettergi-capability-map.md)
- [AutoBGI capability map](autobgi-capability-map.md)

