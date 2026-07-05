from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from bettergi_common import json_dump, read_json, relative_windows_path, resolve_bettergi_install_path


def matches(text: str, search: str) -> bool:
    return not search or search.casefold() in text.casefold()


def list_pathing(auto_pathing_root: Path, search: str) -> list[dict]:
    if not auto_pathing_root.exists():
        return []

    items = []
    for path in sorted(auto_pathing_root.rglob("*.json")):
        if not path.is_file():
            continue
        relative = relative_windows_path(path, auto_pathing_root)
        if not matches(relative, search):
            continue
        items.append(
            {
                "type": "Pathing",
                "name": path.name,
                "folderName": str(Path(relative).parent) if str(Path(relative).parent) != "." else "",
                "relativePath": relative,
                "length": path.stat().st_size,
                "lastWriteTime": path.stat().st_mtime,
            }
        )
    return items


def list_js_scripts(js_root: Path, search: str) -> list[dict]:
    if not js_root.exists():
        return []

    items = []
    for folder in sorted(p for p in js_root.iterdir() if p.is_dir()):
        manifest_path = folder / "manifest.json"
        manifest_name = folder.name
        has_manifest = manifest_path.exists()
        if has_manifest:
            try:
                manifest = read_json(manifest_path)
                manifest_name = str(manifest.get("name") or manifest_name)
            except Exception:
                pass
        if not matches(f"{manifest_name}\\{folder.name}", search):
            continue
        items.append(
            {
                "type": "Javascript",
                "name": manifest_name,
                "folderName": folder.name,
                "hasManifest": has_manifest,
                "relativePath": folder.name,
                "lastWriteTime": folder.stat().st_mtime,
            }
        )
    return items


def list_key_mouse(key_mouse_root: Path, search: str) -> list[dict]:
    if not key_mouse_root.exists():
        return []

    items = []
    for path in sorted(p for p in key_mouse_root.iterdir() if p.is_file()):
        if not matches(path.name, search):
            continue
        items.append(
            {
                "type": "KeyMouse",
                "name": path.name,
                "folderName": path.name,
                "relativePath": path.name,
                "length": path.stat().st_size,
                "lastWriteTime": path.stat().st_mtime,
            }
        )
    return items


def list_script_groups(script_group_root: Path) -> list[dict]:
    if not script_group_root.exists():
        return []

    groups = []
    for path in sorted(script_group_root.glob("*.json")):
        try:
            group = read_json(path)
            projects = group.get("projects") or []
            groups.append(
                {
                    "name": group.get("name"),
                    "fileName": path.name,
                    "index": group.get("index"),
                    "projectCount": len(projects),
                    "enabledCount": sum(1 for p in projects if p.get("status") == "Enabled"),
                }
            )
        except Exception:
            groups.append(
                {
                    "name": path.stem,
                    "fileName": path.name,
                    "index": None,
                    "projectCount": None,
                    "enabledCount": None,
                }
            )
    return groups


def list_one_dragons(one_dragon_root: Path) -> list[dict]:
    if not one_dragon_root.exists():
        return []

    return [
        {
            "name": path.stem,
            "fileName": path.name,
            "length": path.stat().st_size,
            "lastWriteTime": path.stat().st_mtime,
        }
        for path in sorted(one_dragon_root.glob("*.json"))
    ]


def build_inventory(install_path: Path, search: str, limit: int, full: bool) -> dict:
    user_path = install_path / "User"
    pathing = list_pathing(user_path / "AutoPathing", search)
    js_scripts = list_js_scripts(user_path / "JsScript", search)
    key_mouse = list_key_mouse(user_path / "KeyMouseScript", search)
    script_groups = list_script_groups(user_path / "ScriptGroup")
    one_dragons = list_one_dragons(user_path / "OneDragon")
    callable_items = pathing + js_scripts + key_mouse

    top_counter = Counter()
    for item in pathing:
        folder = item["folderName"]
        top = folder.split("\\", 1)[0] if folder else "."
        top_counter[top] += 1

    return {
        "installPath": str(install_path),
        "userPath": str(user_path),
        "search": search,
        "counts": {
            "callableTotal": len(callable_items),
            "pathing": len(pathing),
            "javascript": len(js_scripts),
            "keyMouse": len(key_mouse),
            "scriptGroups": len(script_groups),
            "oneDragons": len(one_dragons),
        },
        "topPathingFolders": [
            {"name": name, "count": count} for name, count in top_counter.most_common(30)
        ],
        "callableItems": callable_items if full else callable_items[:limit],
        "scriptGroups": script_groups,
        "oneDragons": one_dragons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="List BetterGI callable local inventory.")
    parser.add_argument("--install-path", default="")
    parser.add_argument("--search", default="")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    print(json_dump(build_inventory(resolve_bettergi_install_path(args.install_path), args.search, args.limit, args.full)))


if __name__ == "__main__":
    main()
