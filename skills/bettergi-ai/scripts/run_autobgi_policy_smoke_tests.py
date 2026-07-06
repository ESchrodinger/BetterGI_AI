from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from bettergi_common import json_dump


SCRIPT_DIR = Path(__file__).resolve().parent
PROBE = SCRIPT_DIR / "probe_autobgi_mcp.py"


def run_policy(args: list[str], *, should_pass: bool) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(PROBE), "--policy-only", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if should_pass and completed.returncode != 0:
        raise AssertionError(f"policy should pass: {args}\n{completed.stderr or completed.stdout}")
    if not should_pass and completed.returncode == 0:
        raise AssertionError(f"policy should fail: {args}\n{completed.stdout}")
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        try:
            parsed = json.loads(message)
        except json.JSONDecodeError:
            parsed = {"error": message}
        return {"passed": False, "message": message, "structuredError": parsed}
    return json.loads(completed.stdout)


def json_arg(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    results: list[dict[str, Any]] = []

    allowed_cases = [
        [
            "--call-tool", "findBgiIndex",
        ],
        [
            "--call-tool", "queryBackpack",
            "--arguments", json_arg({"materialName": "清水玉"}),
        ],
        [
            "--call-tool", "queryCharacterBuild",
            "--arguments", json_arg({"characterName": "芙宁娜"}),
        ],
        [
            "--call-tool", "captureDesktopScreenshot",
            "--allow-screenshot",
        ],
        [
            "--call-tool", "RunCronTask",
            "--confirm-run",
            "--arguments", json_arg(
                {
                    "taskName": "启动一条龙",
                    "params": "默认配置",
                    "delayInSeconds": 0,
                }
            ),
        ],
        [
            "--call-tool", "RunCronTask",
            "--confirm-run",
            "--arguments", json_arg(
                {
                    "taskName": "启动配置组",
                    "params": "ai_combat_demo",
                    "delayInSeconds": 0,
                }
            ),
        ],
    ]

    rejected_cases = [
        [
            "--call-tool", "captureDesktopScreenshot",
        ],
        [
            "--call-tool", "queryBackpack",
            "--arguments", json_arg({}),
        ],
        [
            "--call-tool", "queryCharacterBuild",
            "--arguments", json_arg({}),
        ],
        [
            "--call-tool", "RunCronTask",
            "--arguments", json_arg(
                {
                    "taskName": "启动一条龙",
                    "params": "默认配置",
                    "delayInSeconds": 0,
                }
            ),
        ],
        [
            "--call-tool", "RunCronTask",
            "--confirm-run",
            "--arguments", json_arg(
                {
                    "taskName": "启动一条龙",
                    "params": "默认配置",
                    "delayInSeconds": 5,
                }
            ),
        ],
        [
            "--call-tool", "RunCronTask",
            "--confirm-run",
            "--arguments", json_arg(
                {
                    "taskName": "备份user",
                    "params": "默认配置",
                    "delayInSeconds": 0,
                }
            ),
        ],
        [
            "--call-tool", "continueOneDragon",
        ],
        [
            "--call-tool", "collectMaterialRoutes",
            "--arguments", json_arg({"materialName": "清水玉"}),
        ],
    ]

    for case in allowed_cases:
        output = run_policy(case, should_pass=True)
        results.append({"case": case, "allowed": output["policy"]["allowed"]})

    for case in rejected_cases:
        output = run_policy(case, should_pass=False)
        structured = output["structuredError"]
        assert structured.get("ok") is False, f"rejected policy should emit structured ok=false: {case}"
        assert structured.get("category"), f"rejected policy should emit category: {case}"
        assert structured.get("hints"), f"rejected policy should emit hints: {case}"
        results.append({"case": case, "rejected": structured["category"]})

    print(json_dump({"passed": len(results), "results": results}))


if __name__ == "__main__":
    main()
