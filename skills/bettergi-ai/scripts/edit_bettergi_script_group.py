from __future__ import annotations

import argparse
import copy
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from bettergi_common import json_dump, read_json, resolve_bettergi_install_path, write_json


PROJECT_TYPES = {"Pathing", "Javascript", "KeyMouse", "Shell"}


def script_group_path(install_path: Path, group_name: str) -> Path:
    if any(ch in group_name for ch in '<>:"/\\|?*'):
        raise ValueError(f"invalid script group name: {group_name}")
    return install_path / "User" / "ScriptGroup" / f"{group_name}.json"


def list_group_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("*.json"))


def read_group(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"script group must be a JSON object: {path}")
    projects = value.setdefault("projects", [])
    if not isinstance(projects, list):
        raise ValueError(f"script group projects must be a JSON array: {path}")
    value.setdefault("config", {})
    return value


def project_summary(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": project.get("index"),
        "type": project.get("type"),
        "name": project.get("name"),
        "folderName": project.get("folderName"),
        "status": project.get("status"),
        "schedule": project.get("schedule"),
        "runNum": project.get("runNum"),
    }


def summarize_group(path: Path, group: dict[str, Any]) -> dict[str, Any]:
    projects = group.get("projects") or []
    pathing_config = (group.get("config") or {}).get("pathingConfig") or {}
    auto_fight = pathing_config.get("autoFightConfig") or {}
    return {
        "path": str(path),
        "name": group.get("name"),
        "index": group.get("index"),
        "projectCount": len(projects),
        "enabledCount": sum(1 for p in projects if p.get("status") == "Enabled"),
        "autoFightEnabled": pathing_config.get("autoFightEnabled"),
        "autoFightStrategyName": auto_fight.get("strategyName"),
        "projects": [project_summary(project) for project in projects],
    }


def max_group_index(root: Path) -> int:
    max_index = 0
    for path in list_group_files(root):
        try:
            group = read_group(path)
            index = group.get("index")
            if isinstance(index, int):
                max_index = max(max_index, index)
        except Exception:
            continue
    return max_index


def default_group(name: str, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "name": name,
        "config": {
            "pathingConfig": {},
            "shellConfig": {},
            "enableShellConfig": False,
        },
        "projects": [],
    }


def clone_template_config(root: Path) -> dict[str, Any]:
    for path in list_group_files(root):
        try:
            group = read_group(path)
            config = group.get("config")
            if isinstance(config, dict):
                return copy.deepcopy(config)
        except Exception:
            continue
    return default_group("_template", 1)["config"]


def normalize_indexes(projects: list[dict[str, Any]]) -> None:
    for index, project in enumerate(projects, start=1):
        project["index"] = index


def parse_project(raw: str) -> dict[str, Any]:
    parts = raw.split("|")
    if len(parts) < 3:
        raise ValueError(
            "--add-project expects TYPE|NAME|FOLDER_NAME, optionally |SCHEDULE|RUN_NUM"
        )
    project_type, name, folder_name = [part.strip() for part in parts[:3]]
    if project_type not in PROJECT_TYPES:
        raise ValueError(f"project type must be one of {', '.join(sorted(PROJECT_TYPES))}: {project_type}")
    schedule = parts[3].strip() if len(parts) >= 4 and parts[3].strip() else "Daily"
    run_num = int(parts[4]) if len(parts) >= 5 and parts[4].strip() else 1
    return {
        "name": name,
        "folderName": folder_name,
        "jsScriptSettingsObject": None,
        "index": 0,
        "type": project_type,
        "status": "Enabled",
        "schedule": schedule,
        "runNum": run_num,
        "allowJsNotification": True,
        "allowJsHTTPHash": "",
    }


def project_matches(project: dict[str, Any], selector: str) -> bool:
    return selector in {
        str(project.get("index")),
        str(project.get("name")),
        f"{project.get('type')}|{project.get('name')}|{project.get('folderName')}",
    }


def validate_project_reference(install_path: Path, project: dict[str, Any]) -> dict[str, Any]:
    project_type = project.get("type")
    name = str(project.get("name") or "")
    folder_name = str(project.get("folderName") or "")
    if project_type == "Pathing":
        path = install_path / "User" / "AutoPathing" / folder_name / name
    elif project_type == "Javascript":
        path = install_path / "User" / "JsScript" / folder_name
    elif project_type == "KeyMouse":
        path = install_path / "User" / "KeyMouseScript" / folder_name
    else:
        return {"project": project_summary(project), "valid": True, "path": None}
    return {"project": project_summary(project), "valid": path.exists(), "path": str(path)}


def apply_edits(install_path: Path, group: dict[str, Any], args: argparse.Namespace) -> list[str]:
    changed: list[str] = []
    projects = group.setdefault("projects", [])

    for raw in args.add_project:
        project = parse_project(raw)
        projects.append(project)
        changed.append(f"projects.add:{project['type']}:{project['name']}")

    if args.remove_project:
        before_count = len(projects)
        projects[:] = [
            project
            for project in projects
            if not any(project_matches(project, selector) for selector in args.remove_project)
        ]
        if len(projects) != before_count:
            changed.append("projects.remove")

    for selector in args.enable_project:
        for project in projects:
            if project_matches(project, selector):
                project["status"] = "Enabled"
                changed.append(f"projects.enable:{selector}")

    for selector in args.disable_project:
        for project in projects:
            if project_matches(project, selector):
                project["status"] = "Disabled"
                changed.append(f"projects.disable:{selector}")

    if args.set_strategy is not None:
        config = group.setdefault("config", {})
        pathing = config.setdefault("pathingConfig", {})
        pathing["autoFightEnabled"] = bool(args.set_strategy)
        auto_fight = pathing.setdefault("autoFightConfig", {})
        auto_fight["strategyName"] = args.set_strategy
        changed.append("config.pathingConfig.autoFightConfig.strategyName")
        changed.append("config.pathingConfig.autoFightEnabled")

    if args.auto_fight_enabled is not None:
        config = group.setdefault("config", {})
        pathing = config.setdefault("pathingConfig", {})
        pathing["autoFightEnabled"] = args.auto_fight_enabled
        changed.append("config.pathingConfig.autoFightEnabled")

    normalize_indexes(projects)
    return changed


def edit_script_group(args: argparse.Namespace) -> dict[str, Any]:
    install_path = resolve_bettergi_install_path(args.install_path)
    root = install_path / "User" / "ScriptGroup"
    path = script_group_path(install_path, args.group_name)

    created = False
    copied_from: str | None = None
    if args.create or args.copy_from:
        if path.exists():
            raise FileExistsError(path)
        if args.copy_from:
            source = script_group_path(install_path, args.copy_from)
            group = read_group(source)
            group["name"] = args.group_name
            group["index"] = max_group_index(root) + 1
            copied_from = str(source)
        else:
            group = default_group(args.group_name, max_group_index(root) + 1)
            group["config"] = clone_template_config(root)
        created = True
    else:
        if not path.exists():
            raise FileNotFoundError(path)
        group = read_group(path)

    before = summarize_group(path, group)
    changed_fields = apply_edits(install_path, group, args)
    validations = [validate_project_reference(install_path, project) for project in group.get("projects", [])]
    after = summarize_group(path, group)
    changed = created or bool(changed_fields)
    backup_path: str | None = None

    if changed and not args.dry_run:
        root.mkdir(parents=True, exist_ok=True)
        if path.exists():
            backup = path.with_name(f"{path.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            shutil.copy2(path, backup)
            backup_path = str(backup)
        write_json(path, group)
        after = summarize_group(path, read_group(path))

    return {
        "installPath": str(install_path),
        "groupName": args.group_name,
        "dryRun": args.dry_run,
        "created": created,
        "copiedFrom": copied_from,
        "changed": changed,
        "changedFields": sorted(set(changed_fields)),
        "backupPath": backup_path,
        "projectValidations": validations,
        "before": before,
        "after": after,
        "nextStep": {
            "requiredBeforeExecution": True,
            "reason": "Creating or editing a script group only writes User\\ScriptGroup\\<name>.json; it does not automatically add the group to any one-dragon config.",
            "options": [
                {
                    "entry": "oneDragon",
                    "action": "Add or enable this script group in the target User\\OneDragon\\<name>.json before launching one-dragon.",
                },
                {
                    "entry": "standaloneConfigGroup",
                    "action": "Launch this group directly with AutoBGI MCP RunCronTask taskName '启动配置组' and params equal to the exact group name after status checks.",
                },
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect or edit BetterGI script groups.")
    parser.add_argument("--install-path", default="")
    parser.add_argument("--group-name", required=True)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--copy-from")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--add-project", action="append", default=[])
    parser.add_argument("--remove-project", action="append", default=[])
    parser.add_argument("--enable-project", action="append", default=[])
    parser.add_argument("--disable-project", action="append", default=[])
    parser.add_argument("--set-strategy")
    parser.add_argument("--auto-fight-enabled", type=lambda value: value.casefold() in {"true", "1", "yes", "on"}, default=None)
    args = parser.parse_args()
    print(json_dump(edit_script_group(args)))


if __name__ == "__main__":
    main()
