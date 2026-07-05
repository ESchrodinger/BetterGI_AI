from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_PATH = Path(".bettergi-ai") / "local.settings.json"
DEFAULT_BETTERGI_INSTALL_PATH = Path(r"C:\Program Files\BetterGI")

REPO_CHANNELS = {
    "CNB": "https://cnb.cool/bettergi/bettergi-scripts-list",
    "GitCode": "https://gitcode.com/huiyadanli/bettergi-scripts-list",
    "GitHub": "https://github.com/babalae/bettergi-scripts-list",
}

PATH_MAPPER = {
    "pathing": "AutoPathing",
    "js": "JsScript",
    "combat": "AutoFight",
    "tcg": "AutoGeniusInvokation",
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def resolve_bettergi_install_path(
    install_path: str | None = None,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> Path:
    if install_path:
        return Path(install_path)

    settings = Path(settings_path)
    if settings.exists():
        try:
            value = read_json(settings)
            if isinstance(value, dict):
                path = value.get("bettergi", {}).get("installPath")
                if path:
                    return Path(path)
        except Exception:
            pass

    return DEFAULT_BETTERGI_INSTALL_PATH


def normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/").strip("/")
    if not normalized:
        raise ValueError("subscription path is empty")
    if ".." in normalized.split("/"):
        raise ValueError(f"subscription path must not contain '..': {path}")
    root = normalized.split("/", 1)[0]
    if root not in PATH_MAPPER:
        raise ValueError(
            f"subscription path root must be one of {', '.join(PATH_MAPPER)}: {path}"
        )
    return normalized


def derive_repo_folder_name(repo_url: str | None) -> str:
    if not repo_url:
        return "bettergi-scripts-list"

    trimmed = repo_url.rstrip("/")
    name = trimmed.rsplit("/", 1)[-1] or "bettergi-scripts-list"
    if name.lower().endswith(".git"):
        name = name[:-4]

    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return sanitized or "bettergi-scripts-list"


def get_script_config(install_path: Path) -> dict[str, Any]:
    config_path = install_path / "User" / "config.json"
    if not config_path.exists():
        return {}
    try:
        config = read_json(config_path)
    except Exception:
        return {}
    script_config = config.get("scriptConfig")
    return script_config if isinstance(script_config, dict) else {}


def resolve_repo_url(install_path: Path) -> str:
    script_config = get_script_config(install_path)
    channel_name = script_config.get("selectedChannelName") or "CNB"

    if channel_name == "自定义":
        custom_url = str(script_config.get("customRepoUrl") or "").strip()
        if custom_url and custom_url != "https://example.com/custom-repo":
            return custom_url
        return REPO_CHANNELS["CNB"]

    return REPO_CHANNELS.get(str(channel_name), REPO_CHANNELS["CNB"])


def resolve_repo_folder_name(install_path: Path, repo_folder_name: str | None = None) -> str:
    if repo_folder_name:
        return repo_folder_name

    repo_url = resolve_repo_url(install_path)
    mapping_path = install_path / "Repos" / "repo_folder_mapping.json"
    if mapping_path.exists():
        try:
            mapping = read_json(mapping_path)
            if isinstance(mapping, dict):
                mapped = mapping.get(repo_url.rstrip("/"))
                if mapped:
                    return str(mapped)
        except Exception:
            pass

    return derive_repo_folder_name(repo_url)


def resolve_repo_index_path(install_path: Path, repo_folder_name: str | None = None) -> Path:
    folder = resolve_repo_folder_name(install_path, repo_folder_name)
    repo_root = install_path / "Repos" / folder
    updated = repo_root / "repo_updated.json"
    if updated.exists():
        return updated
    return repo_root / "repo.json"


def relative_windows_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def callable_type_for_repo_path(repo_path: str) -> str:
    root = repo_path.split("/", 1)[0]
    return {
        "pathing": "Pathing",
        "js": "Javascript",
        "combat": "CombatStrategy",
        "tcg": "GeniusInvokation",
    }.get(root, root)


def tags_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and "name" in item:
                parts.append(str(item["name"]))
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(value)
