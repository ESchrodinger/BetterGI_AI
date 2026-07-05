from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from bettergi_common import (
    callable_type_for_repo_path,
    json_dump,
    read_json,
    resolve_bettergi_install_path,
    resolve_repo_folder_name,
    resolve_repo_index_path,
    tags_to_text,
)


def matches(text: str, search: str) -> bool:
    return not search or search.casefold() in text.casefold()


def project_fields(repo_path: str, callable_type: str, name: str) -> tuple[str, str]:
    parts = repo_path.split("/")
    if callable_type == "Pathing" and len(parts) >= 2:
        folder = "\\".join(parts[1:-1])
        return name, folder
    if callable_type == "Javascript" and len(parts) >= 2:
        return name, parts[1]
    return name, "\\".join(parts[1:])


def subscription_path_for(repo_path: str, node_type: str) -> str:
    if node_type == "file" and "/" in repo_path:
        return repo_path.rsplit("/", 1)[0]
    return repo_path


def walk_repo_node(
    node: dict[str, Any],
    prefix: str,
    search: str,
    include_directories: bool,
    output: list[dict[str, Any]],
) -> None:
    name = str(node.get("name") or "")
    if not name:
        return

    repo_path = f"{prefix}/{name}" if prefix else name
    node_type = str(node.get("type") or "")
    callable_type = callable_type_for_repo_path(repo_path)
    search_text = " ".join(
        [
            repo_path,
            str(node.get("description") or ""),
            tags_to_text(node.get("tags")),
            str(node.get("author") or ""),
            str(node.get("authors") or ""),
        ]
    )

    if matches(search_text, search) and (include_directories or node_type == "file"):
        project_name, folder_name = project_fields(repo_path, callable_type, name)
        output.append(
            {
                "repoPath": repo_path,
                "subscriptionPath": subscription_path_for(repo_path, node_type),
                "nodeType": node_type,
                "callableType": callable_type,
                "name": project_name,
                "folderName": folder_name,
                "version": str(node.get("version") or ""),
                "author": str(node.get("author") or ""),
                "tags": tags_to_text(node.get("tags")),
                "description": str(node.get("description") or ""),
                "lastUpdated": str(node.get("lastUpdated") or ""),
            }
        )

    children = node.get("children")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                walk_repo_node(child, repo_path, search, include_directories, output)


def search_repo(
    install_path: Path,
    repo_folder_name: str,
    search: str,
    limit: int,
    include_directories: bool,
) -> dict[str, Any]:
    repo_index_path = resolve_repo_index_path(install_path, repo_folder_name or None)
    if not repo_index_path.exists():
        raise FileNotFoundError(
            f"Repo index not found: {repo_index_path}. Update the BetterGI script repository first."
        )

    repo_json = read_json(repo_index_path)
    matches_out: list[dict[str, Any]] = []
    for node in repo_json.get("indexes") or []:
        if isinstance(node, dict):
            walk_repo_node(node, "", search, include_directories, matches_out)

    folder_name = resolve_repo_folder_name(install_path, repo_folder_name or None)
    return {
        "installPath": str(install_path),
        "repoFolderName": folder_name,
        "repoRoot": str(install_path / "Repos" / folder_name),
        "repoJsonPath": str(repo_index_path),
        "repoTime": str(repo_json.get("time") or ""),
        "search": search,
        "totalMatches": len(matches_out),
        "returned": len(matches_out[:limit]),
        "items": matches_out[:limit],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search BetterGI script repository index.")
    parser.add_argument("--install-path", default="")
    parser.add_argument("--repo-folder-name", default="")
    parser.add_argument("--search", default="")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--include-directories", action="store_true")
    args = parser.parse_args()

    print(
        json_dump(
            search_repo(
                resolve_bettergi_install_path(args.install_path),
                args.repo_folder_name,
                args.search,
                args.limit,
                args.include_directories,
            )
        )
    )


if __name__ == "__main__":
    main()
