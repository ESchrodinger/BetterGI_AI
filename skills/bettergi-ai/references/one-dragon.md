# One-Dragon

Use this for `User\OneDragon\<name>.json`.

If the user describes a target with fuzzy game language, such as a nickname, "new domain", weekly boss, or talent material source, read `intent-resolution.md` first. Resolve the canonical current game names through web search, then match them against BetterGI's installed options.

BetterGI setting blocks:

- 自动秘境
- 合成树脂
- 自动地脉花
- 领取邮件 / 领取每日奖励
- 领取尘歌壶奖励
- 自动首领讨伐 / 自动幽境危战
- user ScriptGroup entries

Script group entries:

- One-dragon runs script groups only when the target one-dragon JSON references and enables them.
- A script group can exist under `User\ScriptGroup` without being part of any one-dragon flow.
- When the user creates a script group for daily/one-dragon automation, add or enable that group in the intended one-dragon config before launch.
- When the user wants standalone execution, do not edit one-dragon; use AutoBGI MCP `启动配置组` for the exact group name after status checks.

Creation rules:

- Do not create an empty one-dragon config and call it runnable.
- A new one-dragon config must explicitly enable at least one BetterGI task or one existing script group.
- If the user wants a narrow one-dragon, prefer `--only-task` so unrelated tasks are disabled.
- If the user asks to include a configuration group, first create/validate the group under `User\ScriptGroup`, then enable that exact group name in `TaskEnabledList`.
- If creating by copying another one-dragon config, report inherited enabled tasks and disable anything outside the user's requested scope.

List dynamic options from the user's installed BetterGI:

```bash
python scripts/edit_bettergi_one_dragon.py --install-path "C:\Program Files\BetterGI" --list-options
```

Inspect:

```bash
python scripts/edit_bettergi_one_dragon.py --install-path "C:\Program Files\BetterGI" --config-name "默认配置" --dry-run
```

Create by copying:

```bash
python scripts/edit_bettergi_one_dragon.py --config-name "ai_daily" --copy-from "默认配置" --only-task "自动秘境" --domain-name "霜凝的机枢" --dry-run
```

Create a new one-dragon from scratch with one explicit task:

```bash
python scripts/edit_bettergi_one_dragon.py --config-name "ai_domain_only" --create --only-task "自动秘境" --domain-name "霜凝的机枢" --dry-run
```

Examples by block:

```bash
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-task "合成树脂" --set-field CraftingBenchCountry=枫丹 --set-field MinResinToKeep=0 --dry-run
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-task "自动地脉花" --set-field LeyLineRunCount=3 --dry-run
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-task "领取邮件" --enable-task "领取每日奖励" --set-field AdventurersGuildCountry=枫丹 --dry-run
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-script-group "ai_combat_demo" --dry-run
```

Rules:

- do not hardcode new domains or options; read them from BetterGI
- do not rely on memory for new characters, domains, weekly bosses, or talent materials; search the web first, then validate with BetterGI `--list-options`
- dry-run first unless the user gave exact values in the same turn
- report `changedFields` and backup path
- when adding or removing script groups, report the one-dragon config name and the exact script-group names that are enabled
- after editing or creating one-dragon JSON, state that it has not executed yet
- to execute it, switch to AutoBGI safe control and call `RunCronTask` with taskName `启动一条龙`, params equal to the exact one-dragon config name, and `delayInSeconds=0` after status checks
- do not launch one-dragon from this reference; use AutoBGI safe control after config is verified
