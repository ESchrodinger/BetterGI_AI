# Adapter Research

This directory captures integration research for BetterGI AI adapters.

## Current Decision

Use AutoBGI safe-control skill as the fastest first usable path, while keeping direct BetterGI CLI and AutoBGI adapter work as later hardening paths.

| Option | Strength | Risk | Decision |
| --- | --- | --- | --- |
| AutoBGI safe-control skill | Fastest route to usable AI control; reuses AutoBGI MCP | Behavioral guardrails only; not a hard policy boundary | First landing path |
| Direct BetterGI CLI | Uses BetterGI's own supported entry points; no extra service required | Sparse status feedback; needs careful process/log handling | Hardening path |
| AutoBGI HTTP/MCP adapter | Rich status, Web UI, cron, logs, notifications | Broad privileged surface; AGPL code cannot be copied; another service to configure | Later hardening path |
| Copy AutoBGI logic | Fast-looking shortcut | License and safety mismatch | Do not do |

## Next Implementation Target

Create and iterate `skills/autobgi-safe-control` so agents can quickly operate the safe subset of AutoBGI MCP:

- read status through `findBgiIndex`
- query backpack materials through `queryBackpack`
- launch allowlisted one-dragon tasks through `RunCronTask`
- launch allowlisted script/config groups through `RunCronTask`

Do not expose AutoBGI shutdown, backup, update, config mutation, arbitrary cron, hotkey, recording, or remote-control features through this fast path.

## Runner Hardening Target

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
