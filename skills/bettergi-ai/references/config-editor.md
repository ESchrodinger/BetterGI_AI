# Config Editor

Use this for BetterGI local JSON configuration, script groups, local inventory, script repository search, and subscriptions.

Primary paths:

```text
User\ScriptGroup\*.json
User\OneDragon\*.json
User\AutoPathing\...
User\JsScript\...
User\AutoFight\...
User\Subscriptions\*.json
Repos\<repo-folder>\repo.json
Repos\<repo-folder>\repo_updated.json
```

Safety:

- read/write UTF-8 JSON
- create backups for writes
- validate names against local inventory
- report changed fields
- do not edit credentials, cookies, API keys, or unrelated settings
- after creating or editing a script group, explicitly resolve its run entry before saying it is ready to execute

Script group run entry:

- Creating `User\ScriptGroup\<name>.json` only creates the reusable config group.
- It does not automatically add the group to any `User\OneDragon\<name>.json`.
- If the user wants the group to run as part of one-dragon, edit the target one-dragon config and enable the script-group entry there.
- If the user wants to run only this group, use AutoBGI MCP `RunCronTask` with taskName `启动配置组` and the exact group name after status checks.
- If the user's intent is unclear, ask whether to add the group to a one-dragon config or keep it as a standalone config-group launch target. Do not claim a newly-created group will run until one of these entries is confirmed.

Inventory:

```bash
python scripts/list_bettergi_inventory.py --install-path "C:\Program Files\BetterGI" --search "史莱姆" --limit 20
```

Create or edit script group:

```bash
python scripts/edit_bettergi_script_group.py --group-name "采集示例" --create --add-project "Pathing|史莱姆速刷.json|敌人与魔物\史莱姆" --dry-run
```

Search repository index:

```bash
python scripts/search_bettergi_repo.py --install-path "C:\Program Files\BetterGI" --search "子探测单元" --include-directories --limit 20
```

Edit subscriptions:

```bash
python scripts/edit_bettergi_subscriptions.py --install-path "C:\Program Files\BetterGI" --add-path "pathing/地方特产/枫丹/子探测单元" --dry-run
```

Editing subscriptions does not download files. BetterGI's UI "一键更新订阅" performs the update/sync.
