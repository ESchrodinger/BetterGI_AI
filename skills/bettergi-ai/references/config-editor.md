# Config Editor

Use this for BetterGI local JSON configuration, script groups, local inventory, script repository search, and subscriptions.

If the user names a fuzzy target, nickname, material, boss, or "new" script/domain, read `intent-resolution.md` first. Resolve the canonical game term through web search, then search BetterGI local inventory or repository index. Do not turn fuzzy user words directly into script filenames.

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
- never invent JavaScript, pathing, or key-mouse script names
- add script-group projects only from installed BetterGI files or repository search results that the user chooses
- report changed fields
- do not edit credentials, cookies, API keys, or unrelated settings
- after creating or editing a script group, explicitly resolve its run entry before saying it is ready to execute

Script provenance rules:

- A script group project is a reference to an existing BetterGI asset. It is not a place for the agent to write new JS code.
- For `Javascript`, select from `User\JsScript\...` or from a script repository result that has been downloaded into BetterGI. Do not fabricate `.js` file names, folders, function names, or code bodies.
- For `Pathing`, select from `User\AutoPathing\...`.
- For `KeyMouse`, select from `User\KeyMouseScript\...`.
- `Shell` entries are not part of the default safe workflow. Do not create shell entries unless the user explicitly asks for that exact entry and accepts the risk.
- If the desired script is not installed, search the repository index first, add/update the subscription if needed, ask the user to run BetterGI's repository update/download flow, then re-scan local inventory. Do not create a fake placeholder and call it done.
- If the user only describes the goal, such as "刷木偶材料" or "博士周本", use web search to resolve what that phrase means before local/repository search.

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

The helper rejects missing project references by default. A failure here usually means the agent skipped inventory/repository search and invented a script name. Fix by searching installed assets or repository index, not by bypassing validation.

Search repository index:

```bash
python scripts/search_bettergi_repo.py --install-path "C:\Program Files\BetterGI" --search "子探测单元" --include-directories --limit 20
```

Edit subscriptions:

```bash
python scripts/edit_bettergi_subscriptions.py --install-path "C:\Program Files\BetterGI" --add-path "pathing/地方特产/枫丹/子探测单元" --dry-run
```

Editing subscriptions does not download files. BetterGI's UI "一键更新订阅" performs the update/sync.

Execution handoff after creating a script group:

1. Report that `User\ScriptGroup\<name>.json` was created or edited.
2. Choose exactly one run entry with the user:
   - add/enable the group in a target one-dragon config, then launch that one-dragon; or
   - launch the group standalone with AutoBGI MCP `RunCronTask` taskName `启动配置组`.
3. Before launching, read AutoBGI status with `findBgiIndex`.
4. After launching, report the actual MCP result and read `findBgiIndex` again.

Do not say "the configuration group is running" merely because the JSON file exists.
