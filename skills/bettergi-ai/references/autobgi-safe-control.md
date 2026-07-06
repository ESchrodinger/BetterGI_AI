# AutoBGI Safe Control

Use AutoBGI MCP as the constrained execution/status layer.

Probe tools:

```bash
python scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

If this command fails, parse the structured JSON error on stderr and report `category`, `error`, and `hints`. Do not summarize it only as "probe script failed". The default endpoint is `http://127.0.0.1:10086/mcp/sse` and the default apiKey is `abgi`; override them only when the user configured different values.

Validate policy without connecting to AutoBGI:

```bash
python scripts/run_autobgi_policy_smoke_tests.py
```

Allowed tools:

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`, only when explicitly requested for visual verification
- `queryCharacterBuild`, only for one requested character
- `RunCronTask`, only immediate `启动一条龙` or `启动配置组`

`RunCronTask` policy:

| taskName | Policy |
| --- | --- |
| `关闭原神和关闭bgi` | disabled |
| `启动一条龙` | allowed with exact user-approved one-dragon name |
| `启动配置组` | allowed with exact user-approved config-group name |
| `备份user` | disabled |
| `米游社签到` | disabled |

Allowed launch shape:

```json
{
  "taskName": "启动一条龙 or 启动配置组",
  "params": "<one exact user-approved target name>",
  "delayInSeconds": 0
}
```

CLI launch shape:

```bash
python scripts/probe_autobgi_mcp.py \
  --call-tool RunCronTask \
  --confirm-run \
  --arguments '{"taskName":"启动一条龙","params":"默认配置","delayInSeconds":0}'
```

Before launch:

1. Call `findBgiIndex`.
2. Confirm no conflicting task is active.
3. Validate target name locally.
4. Do not open BetterGI manually before `RunCronTask`; AutoBGI's BetterGI command-line launch can fail when BetterGI is already running.
5. If BetterGI is already running, warn about the conflict and ask whether to continue, stop BetterGI, or wait.
6. Ask for confirmation unless the user already issued the exact run command.
7. After the call, report the MCP result or error and call `findBgiIndex` again. Never claim a task started without tool-result evidence.

Launch failure handling:

- If the probe reports `connection_refused`, ask the user to start AutoBGI or use lifecycle setup to start AutoBGI; do not open BetterGI directly as a workaround.
- If the probe reports `policy_rejected`, fix the arguments or ask for explicit approval; do not bypass the policy.
- If the probe reports a successful MCP connection but `RunCronTask` returns an error, report the tool error verbatim and do not claim the target started.

Other read-only calls:

```json
{"materialName":"清水玉"}
{"characterName":"芙宁娜"}
```

Disabled by default:

- `continueOneDragon`
- `startObsRecording`
- `stopObsRecording`
- `collectMaterialRoutes`
- `collectCookingRoutes`
- shutdown, backup, sign-in, update, raw input, remote control, or arbitrary command execution
