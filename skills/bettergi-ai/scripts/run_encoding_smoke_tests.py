from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from bettergi_common import json_dump, read_json, write_json
from manage_bettergi_lifecycle import autobgi_service_url, read_autobgi_main
from probe_autobgi_mcp import load_settings, mcp_url_from_autobgi_main
from resolve_bettergi_autobgi import mcp_url_from_autobgi_main as resolve_mcp_url_from_main


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def write_json_bytes(path: Path, value: object, *, bom: bool) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    encoded = text.encode("utf-8")
    if bom:
        encoded = b"\xef\xbb\xbf" + encoded
    path.write_bytes(encoded)


def main() -> None:
    cases: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="bettergi-ai-encoding-") as tmp:
        root = Path(tmp)

        chinese_json = {
            "content": "可以填autobgi的网页链接",
            "domain": "霜凝的机关",
            "nested": {"task": "启动一条龙"},
        }

        utf8_path = root / "utf8.json"
        write_json_bytes(utf8_path, chinese_json, bom=False)
        assert_equal(read_json(utf8_path), chinese_json, "read_json should parse UTF-8 Chinese JSON")
        cases.append({"case": "read-json-utf8-chinese", "ok": True})

        bom_path = root / "utf8-bom.json"
        write_json_bytes(bom_path, chinese_json, bom=True)
        assert_equal(read_json(bom_path), chinese_json, "read_json should parse UTF-8 BOM JSON")
        cases.append({"case": "read-json-utf8-bom", "ok": True})

        written_path = root / "written.json"
        write_json(written_path, chinese_json)
        assert_equal(written_path.read_bytes().startswith(b"\xef\xbb\xbf"), False, "write_json should not add BOM")
        assert_equal(read_json(written_path), chinese_json, "write_json output should round-trip")
        cases.append({"case": "write-json-no-bom-roundtrip", "ok": True})

        autobgi = root / "autobgi"
        autobgi.mkdir()
        main_json = {
            "BetterGIAddress": r"C:\Program Files\BetterGI",
            "post": ":10086",
            "Control": {"IsMcp": True},
            "content": "可以填autobgi的网页链接",
        }
        write_json_bytes(autobgi / "main.json", main_json, bom=True)

        lifecycle_main = read_autobgi_main(autobgi)
        assert_equal(lifecycle_main["content"], main_json["content"], "lifecycle should read Chinese main.json")
        assert_equal(autobgi_service_url(lifecycle_main), "http://127.0.0.1:10086", "service URL should use post")
        cases.append({"case": "lifecycle-main-json-bom", "ok": True})

        settings = {"autobgi": {"installPath": str(autobgi)}}
        settings_path = root / "settings.json"
        write_json_bytes(settings_path, settings, bom=True)
        assert_equal(load_settings(settings_path), settings, "probe settings should support UTF-8 BOM")
        assert_equal(
            mcp_url_from_autobgi_main(settings),
            "http://127.0.0.1:10086/mcp/sse",
            "probe should derive MCP URL from main.json post",
        )
        assert_equal(
            resolve_mcp_url_from_main(str(autobgi)),
            "http://127.0.0.1:10086/mcp/sse",
            "resolver should derive MCP URL from main.json post",
        )
        cases.append({"case": "mcp-url-from-bom-main-json", "ok": True})

        fallback = dict(main_json)
        fallback["post"] = ""
        write_json_bytes(autobgi / "main.json", fallback, bom=False)
        assert_equal(
            resolve_mcp_url_from_main(str(autobgi)),
            "http://127.0.0.1:8082/mcp/sse",
            "empty post should use AutoBGI 8082 fallback",
        )
        cases.append({"case": "mcp-url-fallback-8082", "ok": True})

        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            text_path = root / "中文.txt"
            expected = "启动一条龙"
            text_path.write_text(expected, encoding="utf-8")
            profile_path = Path(__file__).resolve().with_name("Use-Utf8PowerShell.ps1")
            command = (
                "$ErrorActionPreference = 'Stop'; "
                f". '{profile_path}'; "
                f"$text = Read-Utf8Text -LiteralPath '{text_path}'; "
                f"if ($text -ne '{expected}') {{ throw \"PowerShell UTF-8 read mismatch: $text\" }}; "
                "Write-Output $text"
            )
            powershell_args = [powershell, "-NoProfile"]
            if Path(powershell).name.casefold() == "powershell.exe":
                powershell_args.extend(["-ExecutionPolicy", "Bypass"])
            powershell_args.extend(["-Command", command])
            completed = subprocess.run(
                powershell_args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if completed.returncode != 0:
                raise AssertionError(completed.stderr or completed.stdout)
            assert_equal(
                completed.stdout.rstrip().endswith(expected),
                True,
                "PowerShell UTF-8 profile should read Chinese text",
            )
            cases.append({"case": "powershell-utf8-profile", "ok": True, "executable": powershell})
        else:
            cases.append({"case": "powershell-utf8-profile", "ok": True, "skipped": "powershell-not-found"})

    print(json_dump({"passed": len(cases), "cases": cases}))


if __name__ == "__main__":
    main()
