# BetterGI Capability Map

This document records what BetterGI itself appears to expose and how BetterGI AI should call it. It is based on the local upstream checkout at `tmp/better-genshin-impact`, inspected on 2026-07-05.

## Source Snapshot

Key upstream files inspected:

- `BetterGenshinImpact/Helpers/CommandLineOptions.cs`
- `BetterGenshinImpact/Service/ApplicationHostService.cs`
- `BetterGenshinImpact/ViewModel/Pages/HomePageViewModel.cs`
- `BetterGenshinImpact/ViewModel/Pages/OneDragonFlowViewModel.cs`
- `BetterGenshinImpact/ViewModel/Pages/ScriptControlViewModel.cs`
- `BetterGenshinImpact/Service/ScriptService.cs`
- `BetterGenshinImpact/Core/Config/Global.cs`
- `BetterGenshinImpact/Core/Config/OneDragonFlowConfig.cs`
- `BetterGenshinImpact/Model/OneDragonTaskItem.cs`

BetterGI is GPL-3.0 licensed. BetterGI AI should not vendor or copy BetterGI code; it should treat BetterGI as an installed external application.

## Invocation Surface

BetterGI currently has a small command-line surface that is useful enough for the first real adapter.

| Operation | CLI form | Evidence | BetterGI AI mapping |
| --- | --- | --- | --- |
| Start capture/home flow | `BetterGI.exe start` | `CommandLineOptions.Parse` maps any arg containing `start` to `CommandLineAction.Start`, after more specific cases | `runner.start` or internal readiness action, not a general agent tool yet |
| Run one-dragon config | `BetterGI.exe --startOneDragon <configName>` | `CommandLineOptions.Parse`; `ApplicationHostService` navigates to `OneDragonFlowPage`; execution continues in `OneDragonFlowViewModel.OnLoaded` | `tasks.run` with `kind: "task"` and a BetterGI task id such as `one_dragon:<name>` |
| Run script/config groups | `BetterGI.exe --startGroups <groupName...>` | `CommandLineOptions.Parse`; `ApplicationHostService` calls `ScriptControlViewModel.OnStartMultiScriptGroupWithNamesAsync` | `tasks.run` with `kind: "script"` or `kind: "group"` and allowlisted group names |
| Resume task progress | `BetterGI.exe --TaskProgress <progressName...>` | `CommandLineOptions.Parse`; `ApplicationHostService` calls `OnStartMultiScriptTaskProgressAsync` | Future resume operation; do not expose until runner can validate progress files |

Important: `--startContinuousOneDragon` was found in AutoBGI, but not in this BetterGI checkout's `CommandLineOptions.cs`. Treat it as unverified for direct BetterGI execution until tested against the user's installed BetterGI build or found in another upstream revision.

## File and Directory Surface

BetterGI resolves relative paths from `AppContext.BaseDirectory` through `Global.Absolute(...)`.

| Purpose | Path under BetterGI install | Use in BetterGI AI |
| --- | --- | --- |
| Main executable | `BetterGI.exe` | Launch target for process adapter |
| Logs | `log\better-genshin-impact.log` and sibling log files | Read-only `runner.logs`, status parsing |
| One-dragon configs | `User\OneDragon\*.json` | Read-only inventory for `tasks.list`; possible future config preview |
| Script groups | `User\ScriptGroup\*.json` | Read-only inventory for `tasks.list`; validated launch names for `--startGroups` |
| JS scripts | `User\JsScript` | Inventory only; do not run arbitrary scripts outside configured groups |
| Auto pathing | `User\AutoPathing` | Inventory/status only |
| Auto fight | `User\AutoFight` | Inventory/status only |
| Task progress | likely under `log\task_progress` / task progress manager storage | Future resume support after exact format is verified |

The first adapter should read only filenames and minimal metadata. It should not mutate `User` JSON files.

## One-Dragon Tasks

`OneDragonTaskItem.InitAction` maps configured task names to concrete BetterGI task implementations. The current source includes these task names:

- `领取邮件`
- `合成树脂`
- `自动秘境`
- `自动首领讨伐`
- `自动幽境危战`
- `领取每日奖励`
- `领取尘歌壶奖励`
- `自动地脉花`

The one-dragon config file stores `TaskEnabledList` plus task-specific settings such as country, party, domain, boss, ley-line options, and completion action. BetterGI AI should not attempt to assemble or modify these per-task internals initially. The safe control point is choosing a named one-dragon config that the user already created in BetterGI.

## Script Groups

BetterGI script groups are stored as JSON files under `User\ScriptGroup`. The command line accepts one or more group names as separate arguments:

```powershell
BetterGI.exe --startGroups "group-a" "group-b"
```

`ScriptService.RunMulti` handles the actual execution and task progress tracking. BetterGI AI should expose only configured/allowlisted group names, not arbitrary folder paths or script names.

## Process Behavior

BetterGI is a WPF desktop app and uses a single-instance model. Command-line runs navigate the existing UI flow when the application starts; the exact behavior when another BetterGI instance is already running must be tested on the user's installed build.

Adapter implication: before enabling non-dry-run launch, the runner should detect:

- Windows host
- configured BetterGI install path
- `BetterGI.exe` exists
- log directory exists or can be identified
- whether `BetterGI.exe` process is already running
- whether a mutating runner job is already active

## Recommended BetterGI AI Adapter

Use a `bettergi-cli` adapter as the default first real executor.

Read-only operations:

- detect executable/log/config directories
- list one-dragon configs from `User\OneDragon\*.json`
- list script groups from `User\ScriptGroup\*.json`
- tail BetterGI logs
- report BetterGI process state

Mutating operations, gated by allowlist and dry-run support:

- `--startOneDragon <allowlistedName>`
- `--startGroups <allowlistedNames...>`

Do not expose:

- arbitrary process execution
- arbitrary PowerShell/cmd/bat execution
- editing BetterGI `User` files
- raw hotkey/mouse/keyboard actions
- task progress resume until storage and validation are understood

