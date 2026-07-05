# AutoBGI Safe Control

Use AutoBGI MCP as the constrained execution/status layer.

Probe tools:

```bash
python scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

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
4. Ask for confirmation unless the user already issued the exact run command.

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
