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
