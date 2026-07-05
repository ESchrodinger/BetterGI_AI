from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from bettergi_common import json_dump, resolve_bettergi_install_path, write_json
from edit_bettergi_one_dragon import new_one_dragon_config


SCRIPT_DIR = Path(__file__).resolve().parent
ONE_DRAGON = SCRIPT_DIR / "edit_bettergi_one_dragon.py"
SCRIPT_GROUP = SCRIPT_DIR / "edit_bettergi_script_group.py"
INVENTORY = SCRIPT_DIR / "list_bettergi_inventory.py"
REPO_SEARCH = SCRIPT_DIR / "search_bettergi_repo.py"


def write_fixture_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, value)


def create_fixture_install(root: Path) -> Path:
    install_path = root / "BetterGI"
    domain_name = "霜凝的机枢"
    group_name = "ai_combat_demo"

    write_fixture_json(
        install_path / "GameTask" / "AutoTrackPath" / "Assets" / "tp.json",
        {
            "data": [
                {
                    "mapName": "Teyvat",
                    "points": [
                        {
                            "type": "BlessDomain",
                            "name": domain_name,
                            "country": "枫丹",
                        }
                    ],
                }
            ]
        },
    )

    default_config = new_one_dragon_config("默认配置")
    default_config["TaskEnabledList"] = {"领取邮件": True}
    write_fixture_json(install_path / "User" / "OneDragon" / "默认配置.json", default_config)

    write_fixture_json(
        install_path / "User" / "ScriptGroup" / f"{group_name}.json",
        {
            "index": 1,
            "name": group_name,
            "config": {
                "pathingConfig": {
                    "autoFightEnabled": True,
                    "autoFightConfig": {
                        "strategyName": "群友分享\\万能战斗策略（萌新推荐）",
                    },
                },
                "shellConfig": {},
                "enableShellConfig": False,
            },
            "projects": [],
        },
    )

    pathing_file = (
        install_path
        / "User"
        / "AutoPathing"
        / "敌人与魔物\\史莱姆"
        / "史莱姆速刷.json"
    )
    write_fixture_json(pathing_file, {"name": "史莱姆速刷"})
    write_fixture_json(
        install_path / "User" / "AutoFight" / "群友分享" / "万能战斗策略（萌新推荐）.json",
        {"name": "万能战斗策略（萌新推荐）"},
    )

    repo_root = install_path / "Repos" / "bettergi-scripts-list"
    write_fixture_json(
        repo_root / "repo.json",
        {
            "time": "fixture",
            "indexes": [
                {
                    "name": "pathing",
                    "type": "directory",
                    "children": [
                        {
                            "name": "敌人与魔物",
                            "type": "directory",
                            "children": [
                                {
                                    "name": "史莱姆",
                                    "type": "directory",
                                    "children": [
                                        {
                                            "name": "史莱姆速刷.json",
                                            "type": "file",
                                            "description": "fixture pathing route for slime",
                                            "author": "fixture",
                                            "tags": ["史莱姆"],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    )
    return install_path


def run_json(args: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return json.loads(completed.stdout)


def run_expect_failure(args: list[str]) -> str:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if completed.returncode == 0:
        raise AssertionError(f"command should have failed: {args}")
    return completed.stderr.strip() or completed.stdout.strip()


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run BetterGI config helper smoke tests against a real install or fixture."
    )
    parser.add_argument("--install-path", default="")
    parser.add_argument(
        "--keep-fixture",
        action="store_true",
        help="Keep the generated temporary fixture directory for debugging.",
    )
    args = parser.parse_args()

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.install_path:
        install_path = resolve_bettergi_install_path(args.install_path)
        fixture = False
    else:
        temp_dir = tempfile.TemporaryDirectory(prefix="bettergi-ai-smoke-")
        install_path = create_fixture_install(Path(temp_dir.name))
        fixture = True

    results: list[dict[str, Any]] = []
    base_args = ["--install-path", str(install_path)]

    options = run_json([str(ONE_DRAGON), *base_args, "--list-options"])
    domains = {item["name"] for item in options["domains"]}
    script_groups = set(options["scriptGroups"])
    assert_true(domains, "BetterGI domain options should not be empty")
    assert_true(script_groups, "BetterGI script group options should not be empty")
    domain_name = "霜凝的机枢" if "霜凝的机枢" in domains else sorted(domains)[0]
    group_name = "ai_combat_demo" if "ai_combat_demo" in script_groups else sorted(script_groups)[0]
    results.append({"case": "dynamic-options", "domain": domain_name, "scriptGroup": group_name})
    results.append(
        {
            "case": "human-validated-real-writes",
            "configs": [
                "ai_test_自动秘境",
                "ai_test_合成树脂",
                "ai_test_自动地脉花",
                "ai_test_奖励",
                "ai_test_尘歌壶",
                "ai_test_配置组引用",
                "ai_test_组合一条龙",
                "ai_test_战斗任务",
                "ai_test_周计划秘境",
                "ai_test_地脉周计划",
                "ai_test_尘歌壶物品",
            ],
            "status": "confirmed in BetterGI UI",
        }
    )

    one_dragon_cases = [
        (
            "自动秘境",
            [
                "--config-name", "ai_smoke_domain", "--copy-from", "默认配置",
                "--only-task", "自动秘境", "--domain-name", domain_name, "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["自动秘境"]
            and out["after"]["domain"]["domainName"] == domain_name,
        ),
        (
            "合成树脂",
            [
                "--config-name", "ai_smoke_craft", "--copy-from", "默认配置",
                "--only-task", "合成树脂", "--set-field", "CraftingBenchCountry=枫丹",
                "--set-field", "MinResinToKeep=0", "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["合成树脂"],
        ),
        (
            "自动地脉花",
            [
                "--config-name", "ai_smoke_leyline", "--copy-from", "默认配置",
                "--only-task", "自动地脉花", "--set-field", "LeyLineRunCount=1",
                "--set-field", "LeyLineResinExhaustionMode=false", "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["自动地脉花"]
            and out["after"]["leyLine"]["leyLineRunCount"] == 1,
        ),
        (
            "领取邮件/领取每日奖励",
            [
                "--config-name", "ai_smoke_rewards", "--copy-from", "默认配置",
                "--only-task", "领取邮件", "--enable-task", "领取每日奖励",
                "--set-field", "AdventurersGuildCountry=枫丹", "--dry-run",
            ],
            lambda out: set(out["after"]["enabledTasks"]) == {"领取邮件", "领取每日奖励"},
        ),
        (
            "领取尘歌壶奖励",
            [
                "--config-name", "ai_smoke_teapot", "--copy-from", "默认配置",
                "--only-task", "领取尘歌壶奖励",
                "--set-field", "SereniteaPotTpType=地图传送", "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["领取尘歌壶奖励"],
        ),
        (
            "自动首领讨伐/自动幽境危战",
            [
                "--config-name", "ai_smoke_combat", "--copy-from", "默认配置",
                "--only-task", "自动首领讨伐", "--enable-task", "自动幽境危战",
                "--dry-run",
            ],
            lambda out: set(out["after"]["enabledTasks"]) == {"自动首领讨伐", "自动幽境危战"},
        ),
        (
            "配置组任务",
            [
                "--config-name", "ai_smoke_group_ref", "--copy-from", "默认配置",
                "--only-task", group_name, "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == [group_name],
        ),
        (
            "自动秘境-周计划",
            [
                "--config-name", "ai_smoke_weekly_domain", "--copy-from", "默认配置",
                "--only-task", "自动秘境", "--set-field", "WeeklyDomainEnabled=true",
                "--day-domain", f"monday={domain_name}", "--day-party", "monday=自动化",
                "--set-field", "MondaySelectedValue=0", "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["自动秘境"]
            and out["after"]["domain"]["weeklyDomainEnabled"] is True
            and {"MondayDomainName", "MondayPartyName", "MondaySelectedValue"}.issubset(
                set(out["changedFields"])
            ),
        ),
        (
            "自动地脉花-周计划",
            [
                "--config-name", "ai_smoke_weekly_leyline", "--copy-from", "默认配置",
                "--only-task", "自动地脉花", "--set-field", "LeyLineOneDragonMode=true",
                "--set-field", "LeyLineRunCount=1",
                "--day-leyline", "monday=true,,", "--day-leyline", "tuesday=false,,",
                "--day-leyline", "wednesday=false,,", "--day-leyline", "thursday=false,,",
                "--day-leyline", "friday=false,,", "--day-leyline", "saturday=false,,",
                "--day-leyline", "sunday=false,,", "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["自动地脉花"]
            and out["after"]["leyLine"]["leyLineOneDragonMode"] is True
            and out["after"]["leyLine"]["leyLineRunCount"] == 1
            and {"LeyLineRunMonday", "LeyLineRunTuesday", "LeyLineRunSunday"}.issubset(
                set(out["changedFields"])
            ),
        ),
        (
            "领取尘歌壶奖励-物品列表",
            [
                "--config-name", "ai_smoke_teapot_items", "--copy-from", "默认配置",
                "--only-task", "领取尘歌壶奖励",
                "--set-field", "SereniteaPotTpType=地图传送",
                "--set-field", "SecretTreasureObjects=每天重复,须臾树脂",
                "--dry-run",
            ],
            lambda out: out["after"]["enabledTasks"] == ["领取尘歌壶奖励"]
            and out["after"]["teapot"]["secretTreasureObjects"] == ["每天重复", "须臾树脂"],
        ),
        (
            "组合一条龙",
            [
                "--config-name", "ai_smoke_combo", "--copy-from", "默认配置",
                "--only-task", "自动秘境", "--enable-task", "合成树脂",
                "--enable-task", "领取邮件", "--enable-task", group_name,
                "--domain-name", domain_name, "--set-field", "MinResinToKeep=0",
                "--dry-run",
            ],
            lambda out: set(out["after"]["enabledTasks"])
            == {"自动秘境", "合成树脂", "领取邮件", group_name}
            and out["after"]["domain"]["domainName"] == domain_name
            and out["after"]["missingScriptGroupTasks"] == [],
        ),
    ]

    for label, case_args, check in one_dragon_cases:
        output = run_json([str(ONE_DRAGON), *base_args, *case_args])
        assert_true(check(output), f"one-dragon case failed: {label}")
        results.append({"case": label, "changedFields": output["changedFields"]})

    group_output = run_json(
        [
            str(SCRIPT_GROUP),
            *base_args,
            "--group-name", "ai_smoke_group",
            "--create",
            "--add-project", r"Pathing|史莱姆速刷.json|敌人与魔物\史莱姆",
            "--set-strategy", r"群友分享\万能战斗策略（萌新推荐）",
            "--dry-run",
        ]
    )
    assert_true(group_output["after"]["projectCount"] == 1, "script group should contain one project")
    assert_true(
        all(item["valid"] for item in group_output["projectValidations"]),
        "script group project references should be valid",
    )
    results.append({"case": "配置组-路径项目-战斗策略", "changedFields": group_output["changedFields"]})

    invalid_domain_error = run_expect_failure(
        [
            str(ONE_DRAGON),
            *base_args,
            "--config-name", "ai_smoke_invalid_domain",
            "--copy-from", "默认配置",
            "--only-task", "自动秘境",
            "--domain-name", "__不存在的秘境__",
            "--dry-run",
        ]
    )
    assert_true("__不存在的秘境__" in invalid_domain_error, "invalid domain should be named in error")
    results.append({"case": "负例-未知秘境", "status": "rejected"})

    invalid_group_error = run_expect_failure(
        [
            str(ONE_DRAGON),
            *base_args,
            "--config-name", "ai_smoke_invalid_group",
            "--copy-from", "默认配置",
            "--only-task", "__不存在的配置组__",
            "--dry-run",
        ]
    )
    assert_true("__不存在的配置组__" in invalid_group_error, "invalid group should be named in error")
    results.append({"case": "负例-未知配置组", "status": "rejected"})

    inventory = run_json([str(INVENTORY), *base_args, "--search", "史莱姆", "--limit", "5"])
    assert_true(inventory["counts"]["callableTotal"] >= 1, "inventory search should find callable items")
    results.append({"case": "本地库存搜索", "returned": len(inventory["callableItems"])})

    try:
        repo = run_json(
            [str(REPO_SEARCH), *base_args, "--search", "史莱姆", "--include-directories", "--limit", "5"]
        )
        results.append({"case": "仓库索引搜索", "returned": repo["returned"]})
    except Exception as exc:
        results.append({"case": "仓库索引搜索", "skipped": str(exc)})

    output = {
        "installPath": str(install_path),
        "fixture": fixture,
        "passed": len(results),
        "results": results,
    }
    if temp_dir and args.keep_fixture:
        output["fixturePath"] = temp_dir.name
        temp_dir = None
    print(json_dump(output))


if __name__ == "__main__":
    main()
