# One-Dragon

Use this for `User\OneDragon\<name>.json`.

BetterGI setting blocks:

- 自动秘境
- 合成树脂
- 自动地脉花
- 领取邮件 / 领取每日奖励
- 领取尘歌壶奖励
- 自动首领讨伐 / 自动幽境危战
- user ScriptGroup entries

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

Examples by block:

```bash
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-task "合成树脂" --set-field CraftingBenchCountry=枫丹 --set-field MinResinToKeep=0 --dry-run
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-task "自动地脉花" --set-field LeyLineRunCount=3 --dry-run
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-task "领取邮件" --enable-task "领取每日奖励" --set-field AdventurersGuildCountry=枫丹 --dry-run
python scripts/edit_bettergi_one_dragon.py --config-name "默认配置" --enable-script-group "ai_combat_demo" --dry-run
```

Rules:

- do not hardcode new domains or options; read them from BetterGI
- dry-run first unless the user gave exact values in the same turn
- report `changedFields` and backup path
- do not launch one-dragon from this reference; use AutoBGI safe control after config is verified
