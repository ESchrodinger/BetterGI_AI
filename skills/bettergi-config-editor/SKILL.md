---
name: bettergi-config-editor
description: Use when an agent needs to inspect, create, or safely modify BetterGI local JSON configuration files, especially script/config groups under User\\ScriptGroup and one-dragon configs under User\\OneDragon. Trigger for requests to add BetterGI config groups, edit BetterGI script groups, inspect project entries, add/remove/reorder/enable/disable group projects, or prepare safe configuration diffs. This skill must not run BetterGI tasks, call AutoBGI MCP execution tools, or silently modify configs without backup and user confirmation.
---

# BetterGI Config Editor

## Scope

Edit BetterGI local JSON configuration files, not live automation.

Primary paths under a BetterGI install:

```text
User\ScriptGroup\*.json
User\OneDragon\*.json
User\AutoPathing\...
User\JsScript\...
```

This skill is for configuration file work only. Use `autobgi-safe-control` or `bettergi-agent` to run tasks.

## Safety Rules

Before any write:

1. Locate the BetterGI install path and target JSON file.
2. Read the file as UTF-8.
3. Parse JSON with a structured parser.
4. Show the intended change in plain language.
5. Create a timestamped backup next to the original or in a dedicated backup folder.
6. Ask for user confirmation unless the user explicitly requested the exact write in the same turn.
7. Write UTF-8 without BOM.
8. Re-read and parse the resulting file.

Never:

- edit while BetterGI is actively running a task
- write invalid JSON
- overwrite an existing config when creating a new one
- delete a config without explicit confirmation
- silently change unrelated fields
- edit credentials, cookies, account secrets, or AutoBGI API keys

## Script Group Format

Script groups are stored under:

```text
User\ScriptGroup\<group-name>.json
```

Observed minimal structure:

```json
{
  "index": 1,
  "name": "group-name",
  "config": {
    "pathingConfig": {},
    "shellConfig": {},
    "enableShellConfig": false
  },
  "projects": []
}
```

BetterGI tolerates an empty `projects` array. Preserve the full `config` object when copying from an existing group so BetterGI keeps expected defaults.

## Script Group Project Entries

Pathing project entry shape:

```json
{
  "name": "route-file.json",
  "folderName": "relative\\path\\under\\User\\AutoPathing",
  "jsScriptSettingsObject": null,
  "index": 1,
  "type": "Pathing",
  "status": "Enabled",
  "schedule": "Daily",
  "runNum": 1,
  "allowJsNotification": true,
  "allowJsHTTPHash": ""
}
```

Important fields:

- `index`: 1-based ordering inside the group
- `name`: route/script file name or command depending on type
- `folderName`: relative folder for pathing/JS scripts
- `type`: commonly `Pathing`, `Javascript`, `KeyMouse`, or `Shell`
- `status`: `Enabled` or disabled state from BetterGI UI
- `schedule`: commonly `Daily`, or a custom cron-like value
- `runNum`: run count per execution

When adding/removing/reordering projects, normalize `index` to sequential 1-based values.

## Callable Inventory

A script group can reference only resources BetterGI can resolve from its `User` directory.

Callable project types:

| Type | Inventory source | Project fields |
| --- | --- | --- |
| `Pathing` | `User\AutoPathing\**\*.json` | `name` is file name, `folderName` is the relative folder under `User\AutoPathing` |
| `Javascript` | `User\JsScript\<folder>\manifest.json` | `name` is manifest name, `folderName` is the script folder |
| `KeyMouse` | `User\KeyMouseScript\*` | `name` and `folderName` normally use the file name |
| `Shell` | free-form command string | high risk; do not create unless the user explicitly requests shell execution |

Before adding a project, inventory the relevant source and verify the referenced file/folder exists. Do not guess `folderName` from UI labels.

Use the bundled script for reliable inventory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills\bettergi-config-editor\scripts\list_bettergi_inventory.ps1 -InstallPath "C:\Program Files\BetterGI" -Search "子探测单元" -Limit 20
```

The script returns JSON with:

- `counts`: callable totals by type
- `topPathingFolders`: top pathing categories
- `callableItems`: project entries ready to map into `projects`
- `scriptGroups`: existing groups and project counts
- `oneDragons`: existing one-dragon configs

When building a `Pathing` project entry from inventory, copy `name` and `folderName` exactly.

## Create Empty Script Group

Use this when the user asks to add a new config group.

1. Read an existing script group as a template if available.
2. Copy its `config` object.
3. Set `index` to one greater than the max existing script-group index.
4. Set `name` to the new group name.
5. Set `projects` to `[]`.
6. Write `User\ScriptGroup\<name>.json`.
7. Verify the new file parses and appears in group inventory.

Do not add route projects unless the user explicitly requested them.

## Edit Script Group Projects

Use this for adding, removing, enabling, disabling, or reordering group items.

1. Read target group JSON as UTF-8.
2. Parse `projects`.
3. Apply only the requested changes.
4. Recompute project indexes.
5. Preserve unknown fields.
6. Write backup.
7. Write updated JSON.
8. Re-read and summarize changed project count, enabled count, and affected entries.

## One-Dragon Configs

One-dragon configs are stored under:

```text
User\OneDragon\<name>.json
```

Treat one-dragon edits as higher risk than script group edits. Prefer inspection and diff generation first. Do not modify `TaskEnabledList` or task-specific parameters unless the user names the exact task and desired value.

## Encoding

Always read and write BetterGI JSON as UTF-8. On Windows PowerShell, do not rely on default `Get-Content` encoding for Chinese text.

Prefer explicit APIs:

```powershell
$text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$obj = $text | ConvertFrom-Json
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($path, $json, $utf8NoBom)
```

If text displays as mojibake, retry with explicit UTF-8 before concluding the file is corrupt.

## Response Style

Be precise. State the file path, what changed, backup path, validation result, and any remaining risk. Do not paste large full JSON files unless the user asks; summarize structure and key changed fields.
