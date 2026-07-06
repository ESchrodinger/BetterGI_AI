# Intent Resolution

Use this when the user gives a fuzzy Genshin request such as:

- "博士的周本"
- "木偶的周本天赋材料"
- "新出的圣遗物本"
- "某个角色突破材料"
- "帮我刷她的天赋"
- nicknames, abbreviations, unreleased/newly released content, or names that may have changed in the current version

## Principle

Do not guess from model memory. Use web search to resolve the user's words into concrete game concepts, then verify the executable target against the user's installed BetterGI data.

Web search answers "what does the user mean?" BetterGI local inventory answers "what can this machine actually run?"

## Resolution Flow

1. Parse the user's request into possible entities:
   - character or nickname
   - weekly boss / trounce domain
   - talent material domain
   - weapon material domain
   - artifact/domain name
   - route/material/script target
   - desired BetterGI task block, such as `自动秘境`, `自动首领讨伐`, `自动地脉花`, or a script group
2. Search the web when any entity is ambiguous, new, nickname-based, or version-sensitive.
3. Prefer current, structured sources:
   - official Genshin pages or announcements when available
   - reliable wiki/database pages with page titles and current names
   - BetterGI docs/repository indexes for automation names
4. Record the resolved canonical Chinese names and the evidence source in the final response. Keep quotes short and mostly paraphrase.
5. Match the resolved name against BetterGI local data:
   - `python scripts/edit_bettergi_one_dragon.py --list-options` for one-dragon task/domain options
   - `python scripts/list_bettergi_inventory.py --search "<resolved name>" --limit 20`
   - `python scripts/search_bettergi_repo.py --search "<resolved name>" --include-directories --limit 20`
6. If BetterGI already has an exact local option, use that exact label.
7. If the script/route exists only in the repository index, add/update the subscription path and ask the user to run BetterGI's repository update/download flow before creating a runnable config group.
8. If multiple mappings remain plausible, ask a short clarifying question before editing JSON or launching.

## What Not To Do

- Do not invent BetterGI script names, JS file names, artifact domain names, or weekly boss labels.
- Do not treat a wiki/game result as proof that BetterGI can run it. Always verify local BetterGI options or repository inventory.
- Do not create a script group with a placeholder route because a search result says the material exists.
- Do not launch anything until the resolved BetterGI target has been validated locally and the user has approved the exact run target.

## Mapping Hints

For "weekly boss" / "周本":

- Resolve whether the user means a boss, a trounce domain, or a character talent material source.
- If the request is about farming a weekly boss through BetterGI, map it to BetterGI's boss/weekly-boss task only if the installed BetterGI exposes that target or a repository script exists.
- If BetterGI does not expose a matching task, report the limitation and offer repository search/subscription instead.

For "talent material" / "天赋材料":

- Resolve the character first.
- Search the current talent books and weekly boss material for that character.
- Map talent-book domains to BetterGI `自动秘境` only after checking BetterGI's installed domain options.
- If the request combines weekly boss material and talent books, split the plan into separate executable targets because they may use different BetterGI modules.

For "new domain" / "新出的秘境":

- Search the current version name and official/localized Chinese domain label.
- Then run `--list-options` and use the installed BetterGI label exactly.
- If not present locally, tell the user to update BetterGI/script repository first; do not hard-code the new label into config if BetterGI does not know it.

## Report Template

When resolving fuzzy intent, include:

```text
我把你的说法解析为：
- 用户说法：...
- 联网确认：...
- BetterGI 本地匹配：...
- 将要修改/运行：...
- 仍不确定：...
```

Only include `仍不确定` when something actually needs confirmation.
