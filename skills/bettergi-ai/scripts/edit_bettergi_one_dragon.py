from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from bettergi_common import json_dump, read_json, resolve_bettergi_install_path, write_json


BUILTIN_TASKS = {
    "领取邮件",
    "合成树脂",
    "自动秘境",
    "自动首领讨伐",
    "自动幽境危战",
    "自动地脉花",
    "领取每日奖励",
    "领取尘歌壶奖励",
}

BOOL_FIELDS = {
    "WeeklyDomainEnabled",
    "LeyLineOneDragonMode",
    "LeyLineRunMonday",
    "LeyLineRunTuesday",
    "LeyLineRunWednesday",
    "LeyLineRunThursday",
    "LeyLineRunFriday",
    "LeyLineRunSaturday",
    "LeyLineRunSunday",
    "LeyLineResinExhaustionMode",
    "LeyLineOpenModeCountMin",
}

INT_FIELDS = {
    "MinResinToKeep",
    "LeyLineRunCount",
}

LIST_FIELDS = {
    "SecretTreasureObjects",
}

DAY_NAMES = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
}


def parse_bool(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "y", "on", "启用", "开启"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "禁用", "关闭"}:
        return False
    raise ValueError(f"not a boolean value: {value}")


def coerce_field_value(field: str, value: str) -> Any:
    if field in BOOL_FIELDS:
        return parse_bool(value)
    if field in INT_FIELDS:
        return int(value)
    if field in LIST_FIELDS:
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def split_assignment(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise ValueError(f"expected FIELD=VALUE assignment: {raw}")
    field, value = raw.split("=", 1)
    field = field.strip()
    if not field:
        raise ValueError(f"empty field in assignment: {raw}")
    return field, value


def one_dragon_path(install_path: Path, config_name: str) -> Path:
    if any(ch in config_name for ch in '<>:"/\\|?*'):
        raise ValueError(f"invalid one-dragon config name: {config_name}")
    return install_path / "User" / "OneDragon" / f"{config_name}.json"


def new_one_dragon_config(name: str) -> dict[str, Any]:
    return {
        "TaskEnabledList": {},
        "Name": name,
        "CraftingBenchCountry": "",
        "AdventurersGuildCountry": "",
        "PartyName": "",
        "DomainName": "",
        "WeeklyDomainEnabled": False,
        "DailyRewardPartyName": "",
        "MinResinToKeep": 0,
        "SundayEverySelectedValue": "0",
        "SundayWeeklySelectedValue": "0",
        "SereniteaPotTpType": "地图传送",
        "SecretTreasureObjects": [],
        "LeyLineOneDragonMode": False,
        "LeyLineRunMonday": True,
        "LeyLineRunTuesday": True,
        "LeyLineRunWednesday": True,
        "LeyLineRunThursday": True,
        "LeyLineRunFriday": True,
        "LeyLineRunSaturday": True,
        "LeyLineRunSunday": True,
        "LeyLineMondayType": "",
        "LeyLineMondayCountry": "",
        "LeyLineTuesdayType": "",
        "LeyLineTuesdayCountry": "",
        "LeyLineWednesdayType": "",
        "LeyLineWednesdayCountry": "",
        "LeyLineThursdayType": "",
        "LeyLineThursdayCountry": "",
        "LeyLineFridayType": "",
        "LeyLineFridayCountry": "",
        "LeyLineSaturdayType": "",
        "LeyLineSaturdayCountry": "",
        "LeyLineSundayType": "",
        "LeyLineSundayCountry": "",
        "LeyLineRunCount": 0,
        "LeyLineResinExhaustionMode": False,
        "LeyLineOpenModeCountMin": False,
        "MondayPartyName": "",
        "MondayDomainName": "",
        "MondaySelectedValue": "0",
        "TuesdayPartyName": "",
        "TuesdayDomainName": "",
        "TuesdaySelectedValue": "0",
        "WednesdayPartyName": "",
        "WednesdayDomainName": "",
        "WednesdaySelectedValue": "0",
        "ThursdayPartyName": "",
        "ThursdayDomainName": "",
        "ThursdaySelectedValue": "0",
        "FridayPartyName": "",
        "FridayDomainName": "",
        "FridaySelectedValue": "0",
        "SaturdayPartyName": "",
        "SaturdayDomainName": "",
        "SaturdaySelectedValue": "0",
        "SundayPartyName": "",
        "SundayDomainName": "",
        "SundaySelectedValue": "0",
        "CompletionAction": "",
    }


def load_domain_names(install_path: Path) -> set[str]:
    tp_path = install_path / "GameTask" / "AutoTrackPath" / "Assets" / "tp.json"
    if not tp_path.exists():
        return set()
    data = read_json(tp_path)
    domains: set[str] = set()
    for scene in data.get("data", []):
        if scene.get("mapName") != "Teyvat":
            continue
        for point in scene.get("points", []):
            if point.get("type") in {"BlessDomain", "ForgeryDomain", "MasteryDomain"}:
                name = point.get("name")
                if name:
                    domains.add(str(name))
    return domains


def load_domain_options(install_path: Path) -> list[dict[str, str]]:
    tp_path = install_path / "GameTask" / "AutoTrackPath" / "Assets" / "tp.json"
    if not tp_path.exists():
        return []
    data = read_json(tp_path)
    domains: list[dict[str, str]] = []
    for scene in data.get("data", []):
        if scene.get("mapName") != "Teyvat":
            continue
        for point in scene.get("points", []):
            if point.get("type") in {"BlessDomain", "ForgeryDomain", "MasteryDomain"}:
                name = point.get("name")
                if name:
                    domains.append(
                        {
                            "name": str(name),
                            "country": str(point.get("country") or ""),
                            "type": str(point.get("type") or ""),
                        }
                    )
    return domains


def load_script_group_names(install_path: Path) -> set[str]:
    root = install_path / "User" / "ScriptGroup"
    if not root.exists():
        return set()
    return {path.stem for path in root.glob("*.json")}


def load_combat_strategy_options(install_path: Path) -> list[str]:
    root = install_path / "User" / "AutoFight"
    if not root.exists():
        return []
    return [
        str(path.relative_to(root).with_suffix(""))
        for path in sorted(root.rglob("*.json"))
        if path.is_file()
    ]


def build_options(install_path: Path) -> dict[str, Any]:
    domains = load_domain_options(install_path)
    countries = sorted({item["country"] for item in domains if item["country"]})
    script_groups = sorted(load_script_group_names(install_path))
    return {
        "installPath": str(install_path),
        "source": {
            "domains": str(install_path / "GameTask" / "AutoTrackPath" / "Assets" / "tp.json"),
            "scriptGroups": str(install_path / "User" / "ScriptGroup"),
            "combatStrategies": str(install_path / "User" / "AutoFight"),
            "currentOneDragonConfigs": str(install_path / "User" / "OneDragon"),
        },
        "countries": countries,
        "domains": domains,
        "scriptGroups": script_groups,
        "combatStrategies": load_combat_strategy_options(install_path),
        "builtinTasks": sorted(BUILTIN_TASKS),
    }


def summarize(config_path: Path, config: dict[str, Any], install_path: Path) -> dict[str, Any]:
    tasks = config.get("TaskEnabledList") or {}
    script_groups = load_script_group_names(install_path)
    enabled = [name for name, value in tasks.items() if value]
    return {
        "configPath": str(config_path),
        "name": config.get("Name"),
        "enabledTasks": enabled,
        "builtinEnabledTasks": [name for name in enabled if name in BUILTIN_TASKS],
        "scriptGroupEnabledTasks": [name for name in enabled if name in script_groups],
        "missingScriptGroupTasks": [
            name for name in enabled if name not in BUILTIN_TASKS and name not in script_groups
        ],
        "domain": {
            "partyName": config.get("PartyName", ""),
            "domainName": config.get("DomainName", ""),
            "weeklyDomainEnabled": config.get("WeeklyDomainEnabled", False),
        },
        "crafting": {
            "craftingBenchCountry": config.get("CraftingBenchCountry", ""),
            "minResinToKeep": config.get("MinResinToKeep", 0),
        },
        "dailyReward": {
            "adventurersGuildCountry": config.get("AdventurersGuildCountry", ""),
            "dailyRewardPartyName": config.get("DailyRewardPartyName", ""),
        },
        "teapot": {
            "sereniteaPotTpType": config.get("SereniteaPotTpType", ""),
            "secretTreasureObjects": config.get("SecretTreasureObjects", []),
        },
        "leyLine": {
            "leyLineOneDragonMode": config.get("LeyLineOneDragonMode", False),
            "leyLineRunCount": config.get("LeyLineRunCount", 0),
            "leyLineResinExhaustionMode": config.get("LeyLineResinExhaustionMode", False),
            "leyLineOpenModeCountMin": config.get("LeyLineOpenModeCountMin", False),
        },
        "completionAction": config.get("CompletionAction", ""),
    }


def apply_edits(config: dict[str, Any], install_path: Path, args: argparse.Namespace) -> list[str]:
    changed: list[str] = []
    tasks = config.setdefault("TaskEnabledList", {})
    if not isinstance(tasks, dict):
        raise ValueError("TaskEnabledList must be a JSON object")

    script_groups = load_script_group_names(install_path)

    def validate_task_name(task: str) -> None:
        if task not in BUILTIN_TASKS and task not in script_groups:
            raise ValueError(f"task is not a BetterGI builtin task or script group: {task}")

    if args.only_task:
        tasks.clear()
        for task in args.only_task:
            validate_task_name(task)
            tasks[task] = True
        changed.append("TaskEnabledList")

    for task in args.enable_task:
        validate_task_name(task)
        tasks[task] = True
        changed.append(f"TaskEnabledList.{task}")

    for task in args.disable_task:
        tasks[task] = False
        changed.append(f"TaskEnabledList.{task}")

    for group_name in args.enable_script_group:
        if group_name not in script_groups:
            raise ValueError(f"script group does not exist: {group_name}")
        tasks[group_name] = True
        changed.append(f"TaskEnabledList.{group_name}")

    for group_name in args.disable_script_group:
        tasks[group_name] = False
        changed.append(f"TaskEnabledList.{group_name}")

    if args.domain_name is not None:
        domain_names = load_domain_names(install_path)
        if domain_names and args.domain_name not in domain_names:
            raise ValueError(f"domain is not in BetterGI tp.json: {args.domain_name}")
        config["DomainName"] = args.domain_name
        changed.append("DomainName")

    if args.party_name is not None:
        config["PartyName"] = args.party_name
        changed.append("PartyName")

    for assignment in args.day_domain:
        day, domain = split_assignment(assignment)
        day_key = DAY_NAMES.get(day.strip().casefold())
        if not day_key:
            raise ValueError(f"unknown day for domain assignment: {day}")
        if domain:
            domain_names = load_domain_names(install_path)
            if domain_names and domain not in domain_names:
                raise ValueError(f"domain is not in BetterGI tp.json: {domain}")
        config[f"{day_key}DomainName"] = domain
        changed.append(f"{day_key}DomainName")

    for assignment in args.day_party:
        day, party = split_assignment(assignment)
        day_key = DAY_NAMES.get(day.strip().casefold())
        if not day_key:
            raise ValueError(f"unknown day for party assignment: {day}")
        config[f"{day_key}PartyName"] = party
        changed.append(f"{day_key}PartyName")

    for assignment in args.day_leyline:
        day, raw = split_assignment(assignment)
        day_key = DAY_NAMES.get(day.strip().casefold())
        if not day_key:
            raise ValueError(f"unknown day for leyline assignment: {day}")
        parts = [part.strip() for part in raw.split(",")]
        if len(parts) >= 1 and parts[0]:
            config[f"LeyLineRun{day_key}"] = parse_bool(parts[0])
            changed.append(f"LeyLineRun{day_key}")
        if len(parts) >= 2:
            config[f"LeyLine{day_key}Type"] = parts[1]
            changed.append(f"LeyLine{day_key}Type")
        if len(parts) >= 3:
            config[f"LeyLine{day_key}Country"] = parts[2]
            changed.append(f"LeyLine{day_key}Country")

    for assignment in args.set_field:
        field, value = split_assignment(assignment)
        config[field] = coerce_field_value(field, value)
        changed.append(field)

    return changed


def edit_one_dragon(args: argparse.Namespace) -> dict[str, Any]:
    install_path = resolve_bettergi_install_path(args.install_path)
    config_path = one_dragon_path(install_path, args.config_name)
    explicit_task_edits = bool(args.only_task or args.enable_task or args.enable_script_group)

    created = False
    copied_from: str | None = None
    if args.create or args.copy_from:
        if config_path.exists():
            raise FileExistsError(config_path)
        if args.copy_from:
            source_path = one_dragon_path(install_path, args.copy_from)
            if not source_path.exists():
                raise FileNotFoundError(source_path)
            config = read_json(source_path)
            if not isinstance(config, dict):
                raise ValueError(f"source one-dragon config must be a JSON object: {source_path}")
            config["Name"] = args.config_name
            copied_from = str(source_path)
        else:
            if not explicit_task_edits:
                raise ValueError(
                    "creating a new one-dragon config requires at least one explicit task. "
                    "Use --only-task, --enable-task, or --enable-script-group; do not create an empty one-dragon config and claim it is runnable."
                )
            config = new_one_dragon_config(args.config_name)
        created = True
    else:
        if not config_path.exists():
            raise FileNotFoundError(config_path)
        config = read_json(config_path)

    if not isinstance(config, dict):
        raise ValueError(f"one-dragon config must be a JSON object: {config_path}")

    before = summarize(config_path, config, install_path)
    changed_fields = apply_edits(config, install_path, args)
    after = summarize(config_path, config, install_path)
    changed = created or bool(changed_fields)
    backup_path: str | None = None

    if changed and not args.dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.exists():
            backup = config_path.with_name(
                f"{config_path.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            shutil.copy2(config_path, backup)
            backup_path = str(backup)
        write_json(config_path, config)
        after = summarize(config_path, read_json(config_path), install_path)

    return {
        "installPath": str(install_path),
        "configName": args.config_name,
        "dryRun": args.dry_run,
        "created": created,
        "copiedFrom": copied_from,
        "changed": changed,
        "changedFields": sorted(set(changed_fields)),
        "backupPath": backup_path,
        "before": before,
        "after": after,
        "nextStep": {
            "requiredBeforeExecution": True,
            "reason": "Editing or creating User\\OneDragon\\<name>.json does not execute it. Run only after status checks through AutoBGI MCP RunCronTask taskName '启动一条龙' with params equal to this exact config name.",
            "enabledTasks": after.get("enabledTasks", []),
            "scriptGroupEnabledTasks": after.get("scriptGroupEnabledTasks", []),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect or edit BetterGI one-dragon configs.")
    parser.add_argument("--install-path", default="")
    parser.add_argument("--list-options", action="store_true")
    parser.add_argument("--config-name", default="默认配置")
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--copy-from")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only-task", action="append", default=[])
    parser.add_argument("--enable-task", action="append", default=[])
    parser.add_argument("--disable-task", action="append", default=[])
    parser.add_argument("--enable-script-group", action="append", default=[])
    parser.add_argument("--disable-script-group", action="append", default=[])
    parser.add_argument("--domain-name")
    parser.add_argument("--party-name")
    parser.add_argument("--day-domain", action="append", default=[], help="day=domain")
    parser.add_argument("--day-party", action="append", default=[], help="day=party")
    parser.add_argument(
        "--day-leyline",
        action="append",
        default=[],
        help="day=enabled,type,country; type/country may be empty",
    )
    parser.add_argument("--set-field", action="append", default=[], help="FIELD=VALUE")
    args = parser.parse_args()
    if args.list_options:
        print(json_dump(build_options(resolve_bettergi_install_path(args.install_path))))
        return
    print(json_dump(edit_one_dragon(args)))


if __name__ == "__main__":
    main()
