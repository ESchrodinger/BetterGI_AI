---
name: autobgi-safe-control
description: Use when an agent needs to control AutoBGI through its MCP SSE server or reason about safe AutoBGI MCP usage. Trigger for requests involving AutoBGI status checks, AutoBGI MCP tools, BetterGI one-dragon launch through AutoBGI, BetterGI script/config group launch through AutoBGI, backpack material queries, or quick BetterGI automation via AutoBGI. This skill restricts AutoBGI to a safe subset and must not be used for arbitrary AutoBGI cron tasks, shutdowns, backups, updates, config mutation, hotkeys, raw shell commands, or unrestricted system control.
---

# AutoBGI Safe Control

## Operating Model

Treat AutoBGI as a privileged BetterGI operations service. Use only its safe MCP subset, and keep all mutating calls narrow, explicit, and allowlisted.

Preferred fast path:

```text
Agent -> this skill -> AutoBGI MCP SSE -> AutoBGI -> BetterGI
```

This skill is a behavioral safety layer. It does not replace a programmatic adapter or policy gate. If BetterGI AI MCP/runner tools are available and configured for the same operation, prefer them for stronger enforcement.

## AutoBGI MCP Endpoint

AutoBGI exposes MCP over SSE:

```text
GET /mcp/sse
POST /mcp/messages?sessionId=...
```

The message endpoint requires:

```text
apiKey: <AutoBGI API key>
```

Do not ask the user to paste secrets into chat if a configured connector, environment variable, or local config already provides them.

Example MCP client configuration:

```json
{
  "mcpServers": {
    "AutoBGI": {
      "type": "sse",
      "url": "http://<autobgi-host>:10086/mcp/sse",
      "headers": {
        "apiKey": "<autobgi-api-key>"
      }
    }
  }
}
```

Never commit a real AutoBGI host, API key, token, cookie, or account secret to the repository.

## Allowed MCP Tools

Use only these AutoBGI MCP tools:

- `findBgiIndex`: read BetterGI/AutoBGI progress and status.
- `queryBackpack`: read the count of a named material.
- `RunCronTask`: only for the approved task names and constraints below.

## Tool Discovery

When AutoBGI MCP is available as a configured MCP server, first inspect the AutoBGI tool list unless the host already surfaced the exact tool schemas in the current context.

Expected tools:

```text
findBgiIndex
RunCronTask
queryBackpack
```

For `RunCronTask`, read its `inputSchema.properties.taskName.enum` and keep the exact enum values. AutoBGI task labels may be Chinese or mojibake depending on build/runtime encoding.

Classify enum values by meaning:

| Meaning | Allowed? | Notes |
| --- | --- | --- |
| start one-dragon | yes | use only with allowlisted one-dragon name |
| start script/config group | yes | use only with allowlisted group name |
| close Genshin and/or BetterGI | no | system control |
| HoYoLAB sign-in | no | account-sensitive |
| backup `User` | no | filesystem mutation |
| unknown or unclear | no | ask user to handle manually |

If the tool list does not contain all expected tools, use only the tools that exist and report the missing ones.

## Allowed `RunCronTask` Uses

`RunCronTask` is broad. Restrict it to immediate BetterGI task launch only.

Allowed:

- `taskName`: the exact `RunCronTask` enum value whose meaning is "start one-dragon"
- `taskName`: the exact `RunCronTask` enum value whose meaning is "start script/config group"
- `params`: exactly one user-requested, allowlisted one-dragon or group name
- `delayInSeconds`: `0`

Before calling `RunCronTask`:

1. Call `findBgiIndex`.
2. Confirm the requested target name is present in the user/config allowlist.
3. Confirm no conflicting AutoBGI/BetterGI task appears to be running.
4. State the exact task name and params to the user.
5. Ask for confirmation unless the user already gave an explicit run command in the same turn.

After calling `RunCronTask`:

1. Report that AutoBGI accepted or rejected the call.
2. Call `findBgiIndex` again when useful.
3. Inspect logs/status before any retry.

## Concrete Workflows

### Check AutoBGI/BetterGI Status

Use this for "check status", "what is BetterGI doing", "is AutoBGI running", or before any mutating task.

1. Call `findBgiIndex` with no arguments.
2. Summarize current task/group, route, progress, running state, and timestamp.
3. If fields are unclear or mojibake, say which fields were unclear and avoid guessing.

Do not call `RunCronTask` as part of a pure status check.

### Query Backpack Material

Use this for "how many X do I have" when X is a material name.

1. Call `queryBackpack` with:

```json
{"materialName":"<material name>"}
```

2. Return the material count as reported by AutoBGI.
3. If AutoBGI has no data for the material, say that AutoBGI did not report a count.

Do not use this for account inventory exports, file reads, or broad data scraping.

### Run One-Dragon

Use this only when the user explicitly asks to start a known one-dragon task, such as "run daily one-dragon now".

1. Normalize the requested target internally as `one_dragon:<name>`.
2. Confirm `one_dragon:<name>` is allowlisted by the user or local policy.
3. Call `findBgiIndex` and check for an obvious running/conflicting task.
4. Inspect `RunCronTask` enum values and choose the exact value meaning "start one-dragon".
5. Call `RunCronTask` with:

```json
{
  "taskName": "<exact enum for start one-dragon>",
  "params": "<name>",
  "delayInSeconds": 0
}
```

6. Report the accepted/rejected result and any returned message.

Do not pass multiple one-dragon names. Do not use plan/continuous one-dragon unless the user specifically asks and the exact safety policy has been updated to allow it.

### Run Script/Config Group

Use this only when the user explicitly asks to start a known BetterGI script/config group.

1. Normalize the requested target internally as `group:<name>`.
2. Confirm `group:<name>` is allowlisted by the user or local policy.
3. Call `findBgiIndex` and check for an obvious running/conflicting task.
4. Inspect `RunCronTask` enum values and choose the exact value meaning "start script/config group".
5. Call `RunCronTask` with:

```json
{
  "taskName": "<exact enum for start script/config group>",
  "params": "<name>",
  "delayInSeconds": 0
}
```

6. Report the accepted/rejected result and any returned message.

Do not pass multiple group names unless the skill/policy explicitly allows multi-group execution.

## Prohibited Uses

Never call AutoBGI MCP or REST endpoints for:

- closing Genshin or BetterGI
- backing up `User`
- HoYoLAB sign-in
- arbitrary cron scheduling
- delayed execution with `delayInSeconds > 0`
- AutoBGI, BetterGI, repo, script, or pathing updates
- uploading BetterGI binaries
- deleting files, archives, logs, videos, or scripts
- modifying BetterGI or AutoBGI config
- pressing hotkeys or raw input controls
- OBS/recording control
- remote-session control
- arbitrary command, shell, PowerShell, Python, BAT, or JS execution

If the user requests one of these, explain that the direct AutoBGI MCP path is intentionally restricted and ask whether they want to perform it manually.

## Allowlist Policy

Allowed targets must come from one of:

- an explicit user instruction in the same turn, such as "run the `daily` one-dragon now"
- a local project config dedicated to AutoBGI safe control
- a BetterGI AI runner policy allowlist

Do not infer an allowlist from AutoBGI's full task list. Discovery means "available", not "approved".

For this project, if no separate allowlist config exists yet, treat only a same-turn explicit user command as temporary approval for that exact target name. Example: "run one_dragon:daily now" approves only `one_dragon:daily` for that request, not future requests and not other names.

Recommended naming:

```text
one_dragon:<name>
group:<name>
```

Before mapping, inspect the MCP `tools/list` schema and use the exact enum spelling returned by AutoBGI. Do not invent or normalize task names, because local AutoBGI builds may expose Chinese labels or mojibake depending on encoding.

Map to AutoBGI MCP only at the last step:

```text
one_dragon:daily -> RunCronTask taskName=<exact enum for start one-dragon>, params="daily", delayInSeconds=0
group:route-a -> RunCronTask taskName=<exact enum for start script/config group>, params="route-a", delayInSeconds=0
```

## Status Interpretation

When using `findBgiIndex`, summarize the result in human terms:

- current group/config
- current route or map line
- execution progress
- BetterGI running state
- JS progress
- timestamp or estimate

If status data is unclear, stale, mojibake, or missing, do not start a new task unless the user explicitly accepts the uncertainty.

## Failure Handling

On failure:

1. Do not retry immediately.
2. Call `findBgiIndex` if reachable.
3. Explain the failed tool, params, and returned error.
4. Ask the user whether to retry only after the cause is understood.

If the MCP session cannot connect, check:

- AutoBGI is running
- MCP is enabled in AutoBGI settings
- base URL is correct
- `apiKey` is present and valid
- firewall or local network allows the SSE connection

## Response Style

Be concise and operational. Say what was checked, what will be called, and what happened. Do not expose API keys, tokens, cookies, or raw credentials in responses.
