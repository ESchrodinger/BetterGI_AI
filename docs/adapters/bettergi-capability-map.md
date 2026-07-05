# BetterGI Capability Map

BetterGI is the upstream desktop automation app. BetterGI AI should treat it as an installed external dependency and use its local files as the source of truth for configuration and available options.

## Supported Local Surfaces

| BetterGI surface | Local path | BetterGI AI use |
| --- | --- | --- |
| One-dragon configs | `User\OneDragon\*.json` | Inspect and edit named one-dragon configs |
| Script/config groups | `User\ScriptGroup\*.json` | Inspect, create, and edit config groups |
| Pathing routes | `User\AutoPathing\**\*.json` | Inventory and config-group project references |
| JavaScript scripts | `User\JsScript\*` | Inventory and config-group project references |
| Combat strategies | `User\AutoFight\**\*` | Inventory and pathing auto-fight configuration |
| Subscriptions | `User\Subscriptions\<repo>.json` | Edit subscribed repository paths |
| Repository index | `Repos\<repo>\repo.json` or `repo_updated.json` | Search script candidates before subscription |

## Config Editing Model

BetterGI AI edits BetterGI JSON only through structured helper scripts:

- read/write UTF-8 JSON
- validate known names against local inventory
- create backups for real writes when practical
- report changed fields
- avoid hand-copying repository files into `User` folders

## Script Groups

Pathing, JavaScript, and other project entries live in `projects[]`. Combat strategies are selected through:

```json
{
  "config": {
    "pathingConfig": {
      "autoFightEnabled": true,
      "autoFightConfig": {
        "strategyName": "..."
      }
    }
  }
}
```

Do not treat combat strategies as route projects.

## One-Dragon

One-dragon configs are edited by BetterGI setting block, such as:

- 自动秘境
- 合成树脂
- 自动地脉花
- 领取邮件 / 领取每日奖励
- 领取尘歌壶奖励
- 自动首领讨伐 / 自动幽境危战
- 配置组任务

Use installed BetterGI options when possible instead of hardcoding future-sensitive labels such as new domains or routes.

## Execution

Execution is normally delegated to AutoBGI MCP, not direct BetterGI process control. BetterGI AI validates and edits local configuration first, then uses AutoBGI to start a user-approved one-dragon or config group.
