from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from bettergi_common import json_dump, read_json, write_json


DEFAULT_LOCAL_SETTINGS = Path(".bettergi-ai") / "local.settings.json"


def read_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"settings must be a JSON object: {path}")
    return value


def validate_bettergi_path(path: Path) -> dict[str, Any]:
    checks = {
        "exe": path / "BetterGI.exe",
        "user": path / "User",
        "oneDragon": path / "User" / "OneDragon",
        "scriptGroup": path / "User" / "ScriptGroup",
        "tpJson": path / "GameTask" / "AutoTrackPath" / "Assets" / "tp.json",
    }
    return {
        "path": str(path),
        "valid": checks["exe"].exists() and checks["user"].exists(),
        "checks": {key: value.exists() for key, value in checks.items()},
    }


def validate_autobgi_path(path: Path) -> dict[str, Any]:
    exe_candidates = [
        path / "auto-bgi.exe",
        path / "autobgi.exe",
        path / "auto-bgi无窗口.exe",
    ]
    checks = {
        "mainJson": path / "main.json",
        "abgiUserYaml": path / "abgiUser.yaml",
        "anyExe": any(candidate.exists() for candidate in exe_candidates),
    }
    return {
        "path": str(path),
        "valid": checks["anyExe"] or checks["mainJson"].exists(),
        "exeCandidates": [str(candidate) for candidate in exe_candidates if candidate.exists()],
        "checks": {key: (value if isinstance(value, bool) else value.exists()) for key, value in checks.items()},
    }


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA", "APPDATA", "USERPROFILE"):
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value))
    for drive in "CDEFG":
        root = Path(f"{drive}:\\")
        if root.exists():
            roots.append(root)
    seen = set()
    unique = []
    for root in roots:
        key = str(root).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def discover_named_dirs(names: list[str], max_depth: int = 3) -> list[Path]:
    candidates: list[Path] = []
    wanted = {name.casefold() for name in names}
    for root in candidate_roots():
        if not root.exists():
            continue
        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            try:
                children = list(current.iterdir())
            except (PermissionError, OSError):
                continue
            for child in children:
                try:
                    if not child.is_dir():
                        continue
                except (PermissionError, OSError):
                    continue
                lowered = child.name.casefold()
                if lowered in wanted or any(name in lowered for name in wanted):
                    candidates.append(child)
                if depth + 1 < max_depth and child.name not in {"Windows", "$Recycle.Bin", "System Volume Information"}:
                    stack.append((child, depth + 1))
    return sorted(set(candidates), key=lambda path: str(path).casefold())


def discover_bettergi() -> list[dict[str, Any]]:
    raw = [
        Path(os.environ.get("BETTERGI_HOME", "")) if os.environ.get("BETTERGI_HOME") else None,
        Path(r"C:\Program Files\BetterGI"),
        Path(r"C:\Program Files (x86)\BetterGI"),
    ]
    raw += discover_named_dirs(["BetterGI", "Better Genshin Impact"], max_depth=2)
    candidates = []
    seen = set()
    for path in raw:
        if not path:
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        result = validate_bettergi_path(path)
        if result["valid"] or any(result["checks"].values()):
            candidates.append(result)
    return candidates


def discover_autobgi() -> list[dict[str, Any]]:
    raw = [
        Path(os.environ.get("AUTOBGI_HOME", "")) if os.environ.get("AUTOBGI_HOME") else None,
        Path(r"C:\auto-bgi"),
        Path(r"D:\auto-bgi"),
        Path(r"C:\Program Files\auto-bgi"),
    ]
    raw += discover_named_dirs(["auto-bgi", "autobgi"], max_depth=2)
    candidates = []
    seen = set()
    for path in raw:
        if not path:
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        result = validate_autobgi_path(path)
        if result["valid"] or any(result["checks"].values()):
            candidates.append(result)
    return candidates


def read_autobgi_main(path: Path) -> dict[str, Any]:
    main_json = path / "main.json"
    if not main_json.exists():
        return {}
    try:
        value = read_json(main_json)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def read_autobgi_api_key(path: Path) -> str | None:
    yaml_path = path / "abgiUser.yaml"
    if not yaml_path.exists():
        return None
    try:
        text = yaml_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = yaml_path.read_text(encoding="utf-8-sig")
    match = re.search(r"(?m)^\s*api_key\s*:\s*['\"]?([^'\"\r\n#]+)", text)
    if match:
        return match.group(1).strip()
    return None


def probe_mcp(url: str, api_key: str, timeout: float = 1.0) -> dict[str, Any]:
    request = Request(url, headers={"apiKey": api_key})
    try:
        with urlopen(request, timeout=timeout) as response:
            return {"url": url, "reachable": True, "status": response.status}
    except URLError as exc:
        return {"url": url, "reachable": False, "error": str(exc.reason)}
    except Exception as exc:
        return {"url": url, "reachable": False, "error": str(exc)}


def build_mcp_candidates(settings: dict[str, Any], api_key: str | None) -> list[dict[str, Any]]:
    saved = settings.get("autobgi", {}).get("mcp", {}) if isinstance(settings.get("autobgi"), dict) else {}
    urls = []
    if saved.get("url"):
        urls.append(str(saved["url"]))
    urls.extend(
        [
            "http://127.0.0.1:10086/mcp/sse",
            "http://localhost:10086/mcp/sse",
        ]
    )
    deduped = []
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        if api_key:
            deduped.append(probe_mcp(url, api_key))
        else:
            deduped.append({"url": url, "reachable": None, "error": "apiKey unknown"})
    return deduped


def merge_settings(
    settings: dict[str, Any],
    bettergi_path: str | None,
    autobgi_path: str | None,
    mcp_url: str | None,
    api_key: str | None,
) -> dict[str, Any]:
    result = dict(settings)
    if bettergi_path:
        result.setdefault("bettergi", {})["installPath"] = bettergi_path
    if autobgi_path:
        result.setdefault("autobgi", {})["installPath"] = autobgi_path
    if mcp_url or api_key:
        result.setdefault("autobgi", {}).setdefault("mcp", {})
        if mcp_url:
            result["autobgi"]["mcp"]["url"] = mcp_url
        if api_key:
            result["autobgi"]["mcp"]["apiKey"] = api_key
    return result


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    settings_path = Path(args.settings_path)
    settings = read_settings(settings_path)

    bettergi_path = args.bettergi_path or settings.get("bettergi", {}).get("installPath")
    autobgi_path = args.autobgi_path or settings.get("autobgi", {}).get("installPath")
    api_key = args.api_key or settings.get("autobgi", {}).get("mcp", {}).get("apiKey")
    mcp_url = args.mcp_url or settings.get("autobgi", {}).get("mcp", {}).get("url")

    candidates = {
        "bettergi": discover_bettergi() if args.discover else [],
        "autobgi": discover_autobgi() if args.discover else [],
    }

    if not bettergi_path:
        valid_bettergi = [item for item in candidates["bettergi"] if item.get("valid")]
        if len(valid_bettergi) == 1:
            bettergi_path = valid_bettergi[0]["path"]

    if not autobgi_path:
        valid_autobgi = [item for item in candidates["autobgi"] if item.get("valid")]
        if len(valid_autobgi) == 1:
            autobgi_path = valid_autobgi[0]["path"]

    bettergi_validation = validate_bettergi_path(Path(bettergi_path)) if bettergi_path else None
    autobgi_validation = validate_autobgi_path(Path(autobgi_path)) if autobgi_path else None

    autobgi_main: dict[str, Any] = {}
    if autobgi_path:
        autobgi_main = read_autobgi_main(Path(autobgi_path))
        if not bettergi_path and autobgi_main.get("BetterGIAddress"):
            bettergi_path = str(autobgi_main["BetterGIAddress"])
            bettergi_validation = validate_bettergi_path(Path(bettergi_path))
        if not api_key:
            api_key = read_autobgi_api_key(Path(autobgi_path))

    mcp_candidates = build_mcp_candidates(
        merge_settings(settings, bettergi_path, autobgi_path, mcp_url, api_key),
        api_key,
    )

    resolved = merge_settings(settings, bettergi_path, autobgi_path, mcp_url, api_key)
    if args.write:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(settings_path, resolved)

    return {
        "settingsPath": str(settings_path),
        "wroteSettings": args.write,
        "resolved": resolved,
        "validation": {
            "bettergi": bettergi_validation,
            "autobgi": autobgi_validation,
            "autobgiMain": {
                "path": str(Path(autobgi_path) / "main.json") if autobgi_path else None,
                "betterGIAddress": autobgi_main.get("BetterGIAddress"),
                "isMcp": (autobgi_main.get("Control") or {}).get("IsMcp")
                if isinstance(autobgi_main.get("Control"), dict)
                else None,
            },
            "mcpCandidates": mcp_candidates,
        },
        "candidates": candidates,
        "needsUserInput": {
            "bettergiInstallPath": not bool(bettergi_path),
            "autobgiInstallPath": not bool(autobgi_path),
            "autobgiMcpUrl": not bool(mcp_url),
            "autobgiApiKey": not bool(api_key),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve BetterGI and AutoBGI local setup.")
    parser.add_argument("--settings-path", default=str(DEFAULT_LOCAL_SETTINGS))
    parser.add_argument("--bettergi-path")
    parser.add_argument("--autobgi-path")
    parser.add_argument("--mcp-url")
    parser.add_argument("--api-key")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json_dump(resolve(args)))


if __name__ == "__main__":
    main()
