from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from bettergi_common import DEFAULT_SETTINGS_PATH, json_dump, read_json


DEFAULT_SERVICE_URL = "http://127.0.0.1:10086"
DEFAULT_API_KEY = "abgi"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = read_json(path)
    return value if isinstance(value, dict) else {}


def service_url_from_mcp_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))


def service_url_from_autobgi_main(settings: dict[str, Any]) -> str | None:
    autobgi = settings.get("autobgi")
    if not isinstance(autobgi, dict) or not autobgi.get("installPath"):
        return None
    main_json = Path(str(autobgi["installPath"])) / "main.json"
    if not main_json.exists():
        return None
    try:
        main = read_json(main_json)
    except Exception:
        return None
    if not isinstance(main, dict):
        return None
    post = str(main.get("post") or "").strip()
    if not post or post == ":":
        post = ":8082"
    if post.startswith(":"):
        return f"http://127.0.0.1{post}"
    if post.startswith("http://") or post.startswith("https://"):
        return post.rstrip("/")
    return None


def resolve_config(args: argparse.Namespace) -> tuple[str, str | None]:
    settings = load_settings(Path(args.settings))
    autobgi = settings.get("autobgi") if isinstance(settings.get("autobgi"), dict) else {}
    mcp = autobgi.get("mcp") if isinstance(autobgi.get("mcp"), dict) else {}

    service_url = args.service_url
    if not service_url and mcp.get("url"):
        service_url = service_url_from_mcp_url(str(mcp["url"]))
    if not service_url:
        service_url = service_url_from_autobgi_main(settings)
    service_url = (service_url or DEFAULT_SERVICE_URL).rstrip("/")

    api_key = args.api_key or mcp.get("apiKey") or DEFAULT_API_KEY
    return service_url, str(api_key) if api_key else None


def request_json(
    service_url: str,
    path: str,
    *,
    method: str = "GET",
    api_key: str | None,
    timeout: float,
) -> dict[str, Any]:
    body = b"{}" if method == "POST" else None
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["apiKey"] = api_key
    request = urllib.request.Request(
        service_url.rstrip("/") + path,
        data=body,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8", errors="replace")
    try:
        value = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return {"raw": text}
    return value if isinstance(value, dict) else {"value": value}


def normalize_version(value: Any) -> str:
    text = str(value or "").strip()
    if text.lower().startswith("v"):
        text = text[1:].strip()
    return text


def is_update_available(current: Any, latest: Any) -> bool:
    current_text = normalize_version(current)
    latest_text = normalize_version(latest)
    return bool(current_text and latest_text and current_text != latest_text)


def error_object(exc: BaseException) -> dict[str, Any]:
    return {"ok": False, "error": str(exc), "type": exc.__class__.__name__}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check BetterGI and AutoBGI versions through AutoBGI Web APIs.")
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS_PATH))
    parser.add_argument("--service-url", help="AutoBGI Web service base URL, for example http://127.0.0.1:10086")
    parser.add_argument("--api-key")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output")
    args = parser.parse_args()

    service_url, api_key = resolve_config(args)
    result: dict[str, Any] = {
        "serviceUrl": service_url,
        "apiKeyPresent": bool(api_key),
        "autobgi": {"ok": False},
        "bettergi": {"ok": False},
        "summary": [],
        "safeUpdatePolicy": "read-only check only; do not call update endpoints without explicit user approval",
    }

    try:
        current = request_json(
            service_url,
            "/api/aBgiUpdate/version",
            api_key=api_key,
            timeout=args.timeout,
        )
        latest = request_json(
            service_url,
            "/api/aBgiUpdate/GetLastVersion",
            method="POST",
            api_key=api_key,
            timeout=args.timeout,
        )
        current_version = current.get("version")
        latest_version = latest.get("version")
        result["autobgi"] = {
            "ok": True,
            "currentVersion": current_version,
            "latestVersion": latest_version,
            "canUpdate": is_update_available(current_version, latest_version),
            "sources": {
                "current": "/api/aBgiUpdate/version",
                "latest": "/api/aBgiUpdate/GetLastVersion",
            },
        }
    except Exception as exc:
        result["autobgi"] = error_object(exc)

    try:
        bgi = request_json(
            service_url,
            "/api/aBgiUpdate/GetBgiVersion",
            api_key=api_key,
            timeout=args.timeout,
        )
        current_version = bgi.get("currentVersion") or bgi.get("current")
        latest_version = bgi.get("lastVersion") or bgi.get("latest")
        result["bettergi"] = {
            "ok": True,
            "currentVersion": current_version,
            "latestVersion": latest_version,
            "canUpdate": is_update_available(current_version, latest_version),
            "message": bgi.get("msg") or bgi.get("message"),
            "sources": {
                "versions": "/api/aBgiUpdate/GetBgiVersion",
            },
        }
    except Exception as exc:
        result["bettergi"] = error_object(exc)

    for key, label in (("autobgi", "AutoBGI"), ("bettergi", "BetterGI")):
        item = result[key]
        if not item.get("ok"):
            result["summary"].append(f"{label}: version check failed ({item.get('error')})")
        elif item.get("canUpdate"):
            result["summary"].append(
                f"{label}: update available {item.get('currentVersion')} -> {item.get('latestVersion')}"
            )
        else:
            result["summary"].append(f"{label}: up to date ({item.get('currentVersion')})")

    text = json_dump(result)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["autobgi"].get("ok") or result["bettergi"].get("ok") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (urllib.error.URLError, TimeoutError) as exc:
        print(json_dump(error_object(exc)), file=sys.stderr)
        raise SystemExit(1)
