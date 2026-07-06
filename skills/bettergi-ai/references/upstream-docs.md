# Upstream Docs

Use this when an agent needs project-level context, user-facing feature scope, update policy, or links to upstream BetterGI/AutoBGI documentation.

Sources checked:

- BetterGI docs: `https://www.bettergi.com/doc.html`
- BetterGI GitHub: `https://github.com/babalae/better-genshin-impact`
- AutoBGI Gitee: `https://gitee.com/wangjian0327/auto-bgi`
- Local mirrored source, when present: `tmp\better-genshin-impact`, `tmp\auto-bgi-src`

## New User Prerequisites

This skill is a companion layer, not an installer and not a replacement runner. For a new user:

1. Install BetterGI from the official BetterGI docs/download page.
2. Install AutoBGI from its upstream project/releases.
3. Configure AutoBGI with the BetterGI install path.
4. Enable AutoBGI MCP before expecting MCP tools to work.
5. If version checking reports an update, ask for explicit approval before calling any update endpoint.

## BetterGI Scope

BetterGI is the upstream desktop automation application. Its docs classify features into:

- Real-time tasks: auto pickup, auto story/dialogue-related flows, semi-auto fishing, quick teleport, map mask, cooldown hints.
- Independent tasks: Genius Invokation TCG, lumbering, combat, domains, boss combat, hard combat events, fishing, ley lines, rhythm game, artifact salvage, cooking.
- Auxiliary controls: macros, specific character helper controls, artifact enhancement, one-click purchase.
- Full automation: scheduler, JavaScript scripts, map tracking, key/mouse recording, script repository.
- Command-line startup and local file/config documentation.

For local configuration work, prefer reading BetterGI's current local files and options instead of hard-coding names from this summary. New domains, script options, and task labels should come from the installed BetterGI data.

## AutoBGI Scope

AutoBGI is an automation management and execution layer around BetterGI. Its README describes:

- Web UI backed by Go plus Vue.
- BetterGI path setup and ABGI login/auth configuration.
- AutoBGI Web/MCP execution of BetterGI one-dragon and config groups.
- Log visualization, configuration group run history, archive/estimated run time.
- Backpack/material statistics, Miyoushe-cookie-dependent statistics, material collection cooldown management.
- Notification integrations such as WeChat Work, Telegram, Feishu, OneBot/QQ, DingTalk.
- Script house/repository update workflows and batch script updates.
- ABGI/BGI update page and update APIs.
- Advanced automation such as log keyword actions, OBS recording/replay, remote access, online/co-op management.

For this skill, only use the constrained safe subset in `autobgi-safe-control.md`. Many AutoBGI capabilities are intentionally not exposed by default because they can close apps, operate raw input, run arbitrary scripts, record the screen, or mutate remote state.

## Version Checks

AutoBGI Web includes an update page that checks both AutoBGI and BetterGI versions. The local AutoBGI source maps that UI to these endpoints:

- `GET /api/aBgiUpdate/version`: current AutoBGI version.
- `POST /api/aBgiUpdate/GetLastVersion`: latest AutoBGI version.
- `GET /api/aBgiUpdate/GetBgiVersion`: current and latest BetterGI version.
- Update endpoints exist, but this skill must not call them without explicit user approval.

Use the read-only helper:

```bash
python scripts/check_upstream_versions.py --output .bettergi-ai/status/versions.json
```

Report `currentVersion`, `latestVersion`, and `canUpdate` for each project. If an update is available, remind the user that updates should be initiated explicitly through AutoBGI Web or a separately confirmed update workflow.

## Update Safety

- Version checking is safe and read-only.
- Updating AutoBGI can replace the running executable and restart the service.
- Updating BetterGI can download, backup, delete/replace, and restore files in the BetterGI install directory.
- Before any update action, confirm the exact target and ensure the user understands that currently running BetterGI/AutoBGI tasks may be interrupted.
