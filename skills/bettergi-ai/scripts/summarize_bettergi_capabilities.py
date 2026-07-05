from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bettergi_common import (
    DEFAULT_SETTINGS_PATH,
    json_dump,
    read_json,
    resolve_bettergi_install_path,
)
from list_bettergi_inventory import build_inventory


def read_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}
    try:
        settings = read_json(settings_path)
    except Exception:
        return {}
    return settings if isinstance(settings, dict) else {}


def read_status_json(status_path: str | None) -> Any:
    if not status_path:
        return None
    path = Path(status_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": f"failed to read status json: {exc}", "path": str(path)}
    return extract_find_bgi_index_payload(raw)


def extract_find_bgi_index_payload(raw: Any) -> Any:
    """Accept either raw findBgiIndex JSON or probe_autobgi_mcp.py output."""
    if not isinstance(raw, dict):
        return raw

    tool_call = raw.get("toolCall")
    if not isinstance(tool_call, dict):
        return raw

    result = tool_call.get("result")
    if not isinstance(result, dict):
        return raw

    content = result.get("content")
    if not isinstance(content, list):
        return raw

    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not isinstance(text, str):
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}
    return raw


def first_map_entry(status: Any) -> dict[str, Any]:
    if not isinstance(status, dict):
        return {}
    map_data = status.get("MapData")
    if not isinstance(map_data, list):
        return {}
    for item in map_data:
        if isinstance(item, dict):
            return item
    return {}


def status_hint(status: Any) -> dict[str, Any]:
    if status is None:
        return {
            "source": "not-provided",
            "summary": "AutoBGI MCP progress was not read in this run.",
            "canStartSafely": None,
        }
    if isinstance(status, dict) and status.get("error"):
        return {
            "source": "provided-error",
            "summary": status["error"],
            "canStartSafely": None,
        }

    entry = first_map_entry(status)
    current_config = str(entry.get("当前配置组：", ""))
    current_route = str(entry.get("当前路线：", ""))
    progress = str(entry.get("进度：", ""))
    bgi_running = entry.get("bgi运行状态：")
    js_progress = str(entry.get("js运行进度：", ""))

    status_text = json.dumps(status, ensure_ascii=False)
    running_markers = ["运行中", "执行中", "进行中", "running", "progress"]
    idle_markers = ["已经结束", "空闲", "未运行", "stopped", "idle"]
    lowered = status_text.casefold()
    likely_running = any(marker.casefold() in lowered for marker in running_markers)
    likely_idle = any(marker.casefold() in lowered for marker in idle_markers)

    ended = "已经结束" in current_route or "已经结束" in js_progress or "已经结束" in current_config
    if ended:
        can_start: bool | None = True
        summary = "AutoBGI reports BetterGI is open and the last task has ended."
    elif likely_running and not likely_idle:
        can_start = False
        summary = "Status text looks like AutoBGI/BetterGI is running a task."
    elif likely_idle and not likely_running:
        can_start = True
        summary = "Status text looks idle."
    else:
        can_start = None
        summary = "Status text is available, but running/idle state is unclear."

    return {
        "source": "findBgiIndex",
        "summary": summary,
        "canStartSafely": can_start,
        "currentConfig": current_config,
        "currentRoute": current_route,
        "progress": progress,
        "bgiRunning": bgi_running,
        "jsProgress": js_progress,
        "raw": status,
    }


def build_summary(install_path: Path, settings: dict[str, Any], status: Any, limit: int) -> dict[str, Any]:
    inventory = build_inventory(install_path, search="", limit=limit, full=False)
    one_dragons = [item["name"] for item in inventory["oneDragons"]]
    script_groups = [item["name"] for item in inventory["scriptGroups"] if item.get("name")]

    autobgi = settings.get("autobgi", {}) if isinstance(settings.get("autobgi"), dict) else {}
    mcp_settings = autobgi.get("mcp", {}) if isinstance(autobgi.get("mcp"), dict) else {}
    mcp_url = (
        mcp_settings.get("url")
        or mcp_settings.get("mcpUrl")
        or mcp_settings.get("mcpSseUrl")
        or autobgi.get("mcpUrl")
        or autobgi.get("mcpSseUrl")
        or autobgi.get("url")
    )
    api_key_present = bool(mcp_settings.get("apiKey") or autobgi.get("apiKey"))

    actions = [
        "inspect_status",
        "list_one_dragon_configs",
        "list_script_groups",
        "edit_one_dragon_json_with_backup",
        "edit_script_group_json_with_backup",
        "search_installed_scripts",
        "search_script_repository_index",
    ]
    if mcp_url and api_key_present:
        actions.extend(
            [
                "autobgi_mcp_findBgiIndex",
                "autobgi_mcp_queryBackpack",
                "autobgi_mcp_run_one_dragon_after_validation",
                "autobgi_mcp_run_script_group_after_validation",
            ]
        )

    return {
        "installPath": str(install_path),
        "settingsPath": str(DEFAULT_SETTINGS_PATH),
        "autobgiMcp": {
            "configured": bool(mcp_url and api_key_present),
            "mcpUrl": mcp_url or "",
            "apiKeyPresent": api_key_present,
        },
        "status": status_hint(status),
        "counts": inventory["counts"],
        "oneDragons": one_dragons,
        "scriptGroups": script_groups,
        "topPathingFolders": inventory["topPathingFolders"][:10],
        "availableActions": actions,
        "guidance": [
            "Use findBgiIndex before any execution when AutoBGI MCP is configured.",
            "Treat canStartSafely=null as unknown; ask or inspect logs before launching.",
            "Validate one-dragon and script-group names locally before RunCronTask.",
            "Use local JSON editors for configuration; AutoBGI MCP does not edit fine-grained config.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize BetterGI/AutoBGI status context and safe capabilities.")
    parser.add_argument("--install-path", default="")
    parser.add_argument("--settings-path", default=str(DEFAULT_SETTINGS_PATH))
    parser.add_argument("--status-json", default="", help="Optional path containing raw findBgiIndex or probe JSON output.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    install_path = resolve_bettergi_install_path(args.install_path, args.settings_path)
    settings = read_settings(Path(args.settings_path))
    status = read_status_json(args.status_json)
    print(json_dump(build_summary(install_path, settings, status, args.limit)))


if __name__ == "__main__":
    main()
