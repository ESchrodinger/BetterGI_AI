from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from bettergi_common import DEFAULT_SETTINGS_PATH, json_dump, read_json, resolve_bettergi_install_path


AUTOBGI_PROCESS_NAMES = {"auto-bgi.exe", "auto_bgi.exe", "autobgi.exe"}
BETTERGI_PROCESS_NAMES = {"bettergi.exe"}
GENSHIN_PROCESS_NAMES = {"yuanshen.exe", "genshinimpact.exe", "genshinimpactcloudgame.exe"}


def read_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}
    try:
        value = read_json(settings_path)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def tasklist() -> list[dict[str, str]]:
    completed = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode == 0:
        rows: list[dict[str, str]] = []
        for row in csv.reader(completed.stdout.splitlines()):
            if len(row) < 2:
                continue
            rows.append({"imageName": row[0], "pid": row[1]})
        return rows

    fallback = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Get-Process | Select-Object ProcessName,Id | ConvertTo-Json -Compress",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    parsed = json.loads(fallback.stdout) if fallback.stdout.strip() else []
    if isinstance(parsed, dict):
        parsed = [parsed]
    return [
        {"imageName": f"{item.get('ProcessName')}.exe", "pid": str(item.get("Id"))}
        for item in parsed
        if isinstance(item, dict) and item.get("ProcessName") and item.get("Id")
    ]


def matching_processes(names: set[str]) -> list[dict[str, str]]:
    lowered = {name.casefold() for name in names}
    return [row for row in tasklist() if row["imageName"].casefold() in lowered]


def autobgi_install_path(settings: dict[str, Any]) -> Path | None:
    autobgi = settings.get("autobgi")
    if isinstance(autobgi, dict) and autobgi.get("installPath"):
        return Path(str(autobgi["installPath"]))
    return None


def autobgi_start_target(install_path: Path | None) -> Path | None:
    if not install_path:
        return None
    candidates = [
        install_path / "run_auto_bgi.vbs",
        install_path / "run_auto_bgi_hidden.bat",
        install_path / "auto-bgi.exe",
    ]
    return next((path for path in candidates if path.exists()), None)


def autobgi_restart_target(install_path: Path | None) -> Path | None:
    if not install_path:
        return None
    candidates = [
        install_path / "auto-bgi.exe",
        install_path / "autobgi.exe",
        install_path / "run_auto_bgi_hidden.bat",
        install_path / "run_auto_bgi.vbs",
    ]
    return next((path for path in candidates if path.exists()), None)


def read_autobgi_main(install_path: Path | None) -> dict[str, Any]:
    if not install_path:
        return {}
    main_json = install_path / "main.json"
    if not main_json.exists():
        return {}
    try:
        value = read_json(main_json)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def autobgi_service_url(main: dict[str, Any]) -> str:
    post = str(main.get("post") or "").strip()
    if not post or post == ":":
        post = ":8082"
    if post.startswith(":"):
        return f"http://127.0.0.1{post}"
    if post.startswith("http://") or post.startswith("https://"):
        return post.rstrip("/")
    return "http://127.0.0.1:10086"


def bettergi_exe_path(install_path: Path) -> Path:
    return install_path / "BetterGI.exe"


def build_status(settings_path: Path, install_path_arg: str | None = None) -> dict[str, Any]:
    settings = read_settings(settings_path)
    bettergi_path = resolve_bettergi_install_path(install_path_arg or "", settings_path)
    auto_path = autobgi_install_path(settings)
    auto_main = read_autobgi_main(auto_path)
    auto_url = autobgi_service_url(auto_main)

    autobgi_processes = matching_processes(AUTOBGI_PROCESS_NAMES)
    bettergi_processes = matching_processes(BETTERGI_PROCESS_NAMES)
    genshin_processes = matching_processes(GENSHIN_PROCESS_NAMES)

    return {
        "settingsPath": str(settings_path),
        "bettergi": {
            "installPath": str(bettergi_path),
            "exePath": str(bettergi_exe_path(bettergi_path)),
            "exeExists": bettergi_exe_path(bettergi_path).exists(),
            "running": bool(bettergi_processes),
            "processes": bettergi_processes,
        },
        "autobgi": {
            "installPath": str(auto_path) if auto_path else "",
            "startTarget": str(autobgi_start_target(auto_path)) if autobgi_start_target(auto_path) else "",
            "startTargetExists": bool(autobgi_start_target(auto_path)),
            "mainJson": str(auto_path / "main.json") if auto_path else "",
            "configuredServiceUrl": auto_url,
            "configuredMcpUrl": auto_url.rstrip("/") + "/mcp/sse",
            "configuredIsMcp": (auto_main.get("Control") or {}).get("IsMcp")
            if isinstance(auto_main.get("Control"), dict)
            else None,
            "running": bool(autobgi_processes),
            "processes": autobgi_processes,
        },
        "genshin": {
            "running": bool(genshin_processes),
            "processes": genshin_processes,
            "startSupported": False,
            "note": "Do not start the game directly from BetterGI_AI. BetterGI has its own game launch/control flow.",
        },
        "recommendedOrder": {
            "startup": [
                "AutoBGI service",
                "AutoBGI MCP status preflight",
                "AutoBGI MCP RunCronTask for an allowlisted one-dragon or script group",
                "AutoBGI opens BetterGI through BetterGI.exe command-line; do not pre-open BetterGI",
                "BetterGI handles Genshin launch/control through its own configured flow",
            ],
            "shutdown": [
                "confirm AutoBGI/BetterGI is idle",
                "prefer AutoBGI/BetterGI supported stop flow when available",
                "stop AutoBGI service only when user explicitly asks",
                "do not close Genshin directly unless user explicitly requests it",
            ],
        },
    }


def start_process(path: Path, dry_run: bool) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    if dry_run:
        return {"action": "start", "target": str(path), "dryRun": True}

    if path.suffix.casefold() == ".vbs":
        cmd = ["wscript.exe", str(path)]
    elif path.suffix.casefold() in {".bat", ".cmd"}:
        cmd = ["cmd.exe", "/c", str(path)]
    else:
        cmd = [str(path)]

    subprocess.Popen(cmd, cwd=str(path.parent))
    return {"action": "start", "target": str(path), "dryRun": False}


def wait_for_process_state(names: set[str], *, running: bool, timeout_seconds: float) -> list[dict[str, str]]:
    deadline = time.monotonic() + timeout_seconds
    last: list[dict[str, str]] = []
    while time.monotonic() < deadline:
        last = matching_processes(names)
        if bool(last) == running:
            return last
        time.sleep(0.5)
    return last


def probe_http(url: str, api_key: str | None = None, timeout_seconds: float = 3.0) -> dict[str, Any]:
    headers = {"Accept": "text/event-stream"} if url.endswith("/mcp/sse") else {}
    if api_key:
        headers["apiKey"] = api_key
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get("Content-Type", "")
            if url.endswith("/mcp/sse"):
                return {
                    "url": url,
                    "reachable": True,
                    "status": response.status,
                    "contentType": content_type,
                    "isSse": "text/event-stream" in content_type,
                }
            return {
                "url": url,
                "reachable": True,
                "status": response.status,
                "contentType": content_type,
            }
    except urllib.error.URLError as exc:
        return {"url": url, "reachable": False, "error": str(getattr(exc, "reason", exc))}
    except Exception as exc:
        return {"url": url, "reachable": False, "error": str(exc)}


def stop_processes(processes: list[dict[str, str]], dry_run: bool, force: bool) -> dict[str, Any]:
    if dry_run:
        return {"action": "stop", "targets": processes, "dryRun": True, "force": force}
    stopped = []
    for proc in processes:
        cmd = ["taskkill", "/PID", proc["pid"], "/T"]
        if force:
            cmd.append("/F")
        completed = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        stopped.append(
            {
                "process": proc,
                "returnCode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
    return {"action": "stop", "targets": stopped, "dryRun": False, "force": force}


def read_autobgi_api_key(install_path: Path | None) -> str | None:
    if not install_path:
        return None
    yaml_path = install_path / "abgiUser.yaml"
    if not yaml_path.exists():
        return None
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            for line in yaml_path.read_text(encoding=encoding).splitlines():
                stripped = line.strip()
                if stripped.startswith("api_key:"):
                    return stripped.split(":", 1)[1].strip().strip("'\"") or None
        except UnicodeDecodeError:
            continue
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect or manage BetterGI/AutoBGI lifecycle.")
    parser.add_argument(
        "--action",
        choices=[
            "status",
            "start-autobgi",
            "restart-autobgi",
            "start-bettergi",
            "stop-autobgi",
            "stop-bettergi",
            "stop-genshin",
        ],
        default="status",
    )
    parser.add_argument("--settings-path", default=str(DEFAULT_SETTINGS_PATH))
    parser.add_argument("--install-path", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--allow-direct-bettergi-start",
        action="store_true",
        help="Troubleshooting only. Normal AutoBGI execution must let AutoBGI start BetterGI.",
    )
    args = parser.parse_args()

    settings_path = Path(args.settings_path)
    status = build_status(settings_path, args.install_path)

    if args.action == "status":
        print(json_dump(status))
        return

    if args.action == "start-autobgi":
        target = Path(status["autobgi"]["startTarget"]) if status["autobgi"]["startTarget"] else None
        if not target:
            raise FileNotFoundError("AutoBGI start target was not found")
        result = start_process(target, args.dry_run)
    elif args.action == "restart-autobgi":
        settings = read_settings(settings_path)
        auto_path = autobgi_install_path(settings)
        target = autobgi_restart_target(auto_path)
        if not target:
            raise FileNotFoundError("AutoBGI start target was not found")
        stopped = stop_processes(status["autobgi"]["processes"], args.dry_run, True)
        if not args.dry_run:
            wait_for_process_state(AUTOBGI_PROCESS_NAMES, running=False, timeout_seconds=8)
        started = start_process(target, args.dry_run)
        after_processes = [] if args.dry_run else wait_for_process_state(AUTOBGI_PROCESS_NAMES, running=True, timeout_seconds=10)
        service_url = status["autobgi"]["configuredServiceUrl"]
        mcp_url = status["autobgi"]["configuredMcpUrl"]
        api_key = read_autobgi_api_key(auto_path)
        result = {
            "action": "restart-autobgi",
            "stop": stopped,
            "start": started,
            "processesAfterRestart": after_processes,
            "webProbe": None if args.dry_run else probe_http(service_url),
            "mcpProbe": None if args.dry_run else probe_http(mcp_url, api_key=api_key),
            "expectedWorkingDirectory": str(auto_path) if auto_path else "",
        }
    elif args.action == "start-bettergi":
        if not args.allow_direct_bettergi_start:
            raise PermissionError(
                "Direct BetterGI startup is disabled by default. "
                "For AutoBGI execution, start/check AutoBGI and use MCP RunCronTask; "
                "do not pre-open BetterGI because AutoBGI command-line launch may fail. "
                "For troubleshooting only, rerun with --allow-direct-bettergi-start."
            )
        result = start_process(Path(status["bettergi"]["exePath"]), args.dry_run)
    elif args.action == "stop-autobgi":
        result = stop_processes(status["autobgi"]["processes"], args.dry_run, args.force)
    elif args.action == "stop-bettergi":
        result = stop_processes(status["bettergi"]["processes"], args.dry_run, args.force)
    elif args.action == "stop-genshin":
        result = stop_processes(status["genshin"]["processes"], args.dry_run, args.force)
    else:
        raise ValueError(args.action)

    print(json_dump({"before": status, "result": result, "afterHint": "run --action status again"}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json_dump({"error": str(exc)}), file=sys.stderr)
        raise
