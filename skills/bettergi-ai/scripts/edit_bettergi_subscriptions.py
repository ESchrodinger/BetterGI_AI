from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from bettergi_common import (
    json_dump,
    normalize_repo_path,
    read_json,
    resolve_bettergi_install_path,
    resolve_repo_folder_name,
    write_json,
)


def read_subscription(path: Path) -> list[str]:
    if not path.exists():
        return []
    value = read_json(path)
    if not isinstance(value, list):
        raise ValueError(f"subscription file must be a JSON array: {path}")
    return [str(item) for item in value]


def normalize_many(paths: list[str]) -> list[str]:
    return [normalize_repo_path(path) for path in paths]


def unique_preserving_order(paths: list[str]) -> list[str]:
    seen = set()
    result = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def is_covered_by_parent(path: str, candidates: list[str]) -> bool:
    return any(path == candidate or path.startswith(candidate + "/") for candidate in candidates)


def edit_subscriptions(
    install_path: Path,
    repo_folder_name: str,
    add_paths: list[str],
    remove_paths: list[str],
    set_paths: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    folder_name = resolve_repo_folder_name(install_path, repo_folder_name or None)
    subscriptions_root = install_path / "User" / "Subscriptions"
    subscription_path = subscriptions_root / f"{folder_name}.json"
    before = read_subscription(subscription_path)

    after = list(before)
    operation = "list"
    skipped_covered: list[str] = []
    if set_paths:
        after = unique_preserving_order(normalize_many(set_paths))
        operation = "set"
    if add_paths:
        for path in normalize_many(add_paths):
            if is_covered_by_parent(path, after):
                skipped_covered.append(path)
                continue
            after.append(path)
        operation = "set+add" if operation == "set" else "add"
    if remove_paths:
        remove = set(normalize_many(remove_paths))
        after = [path for path in after if path not in remove]
        operation = "remove" if operation == "list" else f"{operation}+remove"

    after = unique_preserving_order([path for path in after if path.strip()])
    changed = before != after
    backup_path: str | None = None

    if changed and not dry_run:
        subscriptions_root.mkdir(parents=True, exist_ok=True)
        if subscription_path.exists():
            backup = subscription_path.with_name(
                f"{subscription_path.name}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            shutil.copy2(subscription_path, backup)
            backup_path = str(backup)
        write_json(subscription_path, after)

    return {
        "installPath": str(install_path),
        "repoFolderName": folder_name,
        "subscriptionPath": str(subscription_path),
        "operation": operation,
        "dryRun": dry_run,
        "changed": changed,
        "backupPath": backup_path,
        "skippedCovered": skipped_covered,
        "before": before,
        "after": after,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="List or edit BetterGI subscription paths.")
    parser.add_argument("--install-path", default="")
    parser.add_argument("--repo-folder-name", default="")
    parser.add_argument("--add-path", action="append", default=[])
    parser.add_argument("--remove-path", action="append", default=[])
    parser.add_argument("--set-path", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(
        json_dump(
            edit_subscriptions(
                resolve_bettergi_install_path(args.install_path),
                args.repo_folder_name,
                args.add_path,
                args.remove_path,
                args.set_path,
                args.dry_run,
            )
        )
    )


if __name__ == "__main__":
    main()
