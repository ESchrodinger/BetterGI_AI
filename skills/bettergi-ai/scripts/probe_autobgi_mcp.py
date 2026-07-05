from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_PATH = Path(".bettergi-ai") / "local.settings.json"
READ_ONLY_TOOLS = {"findBgiIndex", "queryBackpack", "queryCharacterBuild"}
ALLOWED_RUN_CRON_TASK_NAMES = {"启动一条龙", "启动配置组"}
DISABLED_TOOLS = {
    "continueOneDragon",
    "startObsRecording",
    "stopObsRecording",
    "collectMaterialRoutes",
    "collectCookingRoutes",
}


class McpProbeError(RuntimeError):
    pass


class SseMcpClient:
    def __init__(self, url: str, api_key: str | None, timeout: float) -> None:
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self._endpoint: str | None = None
        self._events: "queue.Queue[dict[str, Any]]" = queue.Queue()
        self._errors: "queue.Queue[BaseException]" = queue.Queue()
        self._response: Any = None
        self._request_id = 0

    def __enter__(self) -> "SseMcpClient":
        headers = {"Accept": "text/event-stream"}
        if self.api_key:
            headers["apiKey"] = self.api_key
        request = urllib.request.Request(self.url, headers=headers, method="GET")
        self._response = urllib.request.urlopen(request, timeout=self.timeout)
        thread = threading.Thread(target=self._read_sse, daemon=True)
        thread.start()
        self._endpoint = self._wait_for_endpoint()
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._response is not None:
            try:
                self._response.close()
            except Exception:
                pass

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "bettergi-ai-autobgi-probe",
                    "version": "0.1.0",
                },
            },
        )
        self.notify("notifications/initialized", {})
        return result

    def list_tools(self) -> list[dict[str, Any]]:
        result = self.request("tools/list", {})
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            raise McpProbeError("tools/list result did not contain a tools array")
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments or {},
            },
        )

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._request_id += 1
        request_id = self._request_id
        self._post_json(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
        )
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            self._raise_reader_error_if_any()
            try:
                event = self._events.get(timeout=0.2)
            except queue.Empty:
                continue
            if event.get("id") != request_id:
                continue
            if "error" in event:
                raise McpProbeError(f"{method} failed: {event['error']}")
            result = event.get("result")
            if not isinstance(result, dict):
                raise McpProbeError(f"{method} returned a non-object result")
            return result
        raise McpProbeError(f"timed out waiting for {method} response")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._post_json(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
            }
        )

    def _read_sse(self) -> None:
        event_name = "message"
        data_lines: list[str] = []
        try:
            while True:
                line_bytes = self._response.readline()
                if not line_bytes:
                    return
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                if line == "":
                    self._dispatch_sse_event(event_name, data_lines)
                    event_name = "message"
                    data_lines = []
                    continue
                if line.startswith(":"):
                    continue
                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                    continue
                if line.startswith("data:"):
                    data_lines.append(line.split(":", 1)[1].lstrip())
        except BaseException as exc:
            self._errors.put(exc)

    def _dispatch_sse_event(self, event_name: str, data_lines: list[str]) -> None:
        if not data_lines:
            return
        data = "\n".join(data_lines)
        if event_name == "endpoint":
            self._endpoint = urllib.parse.urljoin(self.url, data)
            return
        if event_name != "message":
            return
        try:
            value = json.loads(data)
        except json.JSONDecodeError:
            return
        if isinstance(value, dict):
            self._events.put(value)

    def _wait_for_endpoint(self) -> str:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            self._raise_reader_error_if_any()
            if self._endpoint:
                return self._endpoint
            time.sleep(0.05)
        raise McpProbeError("timed out waiting for SSE endpoint event")

    def _post_json(self, payload: dict[str, Any]) -> None:
        if not self._endpoint:
            raise McpProbeError("SSE message endpoint is not available")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["apiKey"] = self.api_key
        request = urllib.request.Request(
            self._endpoint,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                return
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise McpProbeError(f"POST {payload.get('method')} failed with HTTP {exc.code}: {detail}") from exc

    def _raise_reader_error_if_any(self) -> None:
        try:
            exc = self._errors.get_nowait()
        except queue.Empty:
            return
        raise McpProbeError(f"SSE reader failed: {exc}") from exc


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    return value if isinstance(value, dict) else {}


def resolve_mcp_config(args: argparse.Namespace) -> tuple[str, str | None]:
    settings = load_settings(Path(args.settings))
    mcp = settings.get("autobgi", {}).get("mcp", {}) if isinstance(settings, dict) else {}
    url = args.url or mcp.get("url")
    api_key = args.api_key or mcp.get("apiKey")
    if not url:
        raise McpProbeError("AutoBGI MCP URL is missing")
    return str(url), str(api_key) if api_key else None


def parse_json_arg(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("JSON argument must be an object")
    return parsed


def tool_names(tools: list[dict[str, Any]]) -> list[str]:
    names = []
    for tool in tools:
        name = tool.get("name")
        if isinstance(name, str):
            names.append(name)
    return names


def validate_tool_call_policy(
    name: str,
    arguments: dict[str, Any],
    *,
    allow_screenshot: bool = False,
    confirm_run: bool = False,
) -> dict[str, Any]:
    if name in DISABLED_TOOLS:
        raise McpProbeError(f"AutoBGI MCP tool is disabled by BetterGI AI policy: {name}")

    if name == "captureDesktopScreenshot":
        if not allow_screenshot:
            raise McpProbeError(
                "captureDesktopScreenshot requires --allow-screenshot because it can expose screen contents"
            )
        return {"allowed": True, "policy": "explicit visual verification"}

    if name == "queryBackpack":
        material_name = str(arguments.get("materialName") or "").strip()
        if not material_name:
            raise McpProbeError("queryBackpack requires a non-empty materialName")
        return {"allowed": True, "policy": "read-only material query", "materialName": material_name}

    if name == "queryCharacterBuild":
        character_name = str(arguments.get("characterName") or "").strip()
        if not character_name:
            raise McpProbeError("queryCharacterBuild requires one non-empty characterName")
        return {"allowed": True, "policy": "read-only single character query", "characterName": character_name}

    if name == "RunCronTask":
        task_name = str(arguments.get("taskName") or "").strip()
        target = str(arguments.get("params") or "").strip()
        delay = arguments.get("delayInSeconds")
        if task_name not in ALLOWED_RUN_CRON_TASK_NAMES:
            raise McpProbeError(
                "RunCronTask is allowed only for 启动一条龙 or 启动配置组"
            )
        if not target:
            raise McpProbeError("RunCronTask requires params to be the exact approved target name")
        if delay != 0:
            raise McpProbeError("RunCronTask requires delayInSeconds=0")
        if not confirm_run:
            raise McpProbeError("RunCronTask requires --confirm-run after exact user approval")
        return {
            "allowed": True,
            "policy": "confirmed immediate launch",
            "taskName": task_name,
            "target": target,
        }

    if name in READ_ONLY_TOOLS:
        return {"allowed": True, "policy": "read-only"}

    raise McpProbeError(f"AutoBGI MCP tool is not in the BetterGI AI safe subset: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe AutoBGI MCP over SSE.")
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS_PATH))
    parser.add_argument("--url")
    parser.add_argument("--api-key")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--call-tool", help="Optionally call one MCP tool after tools/list.")
    parser.add_argument("--arguments", type=parse_json_arg, default={})
    parser.add_argument(
        "--allow-screenshot",
        action="store_true",
        help="Allow captureDesktopScreenshot after explicit visual-verification request.",
    )
    parser.add_argument(
        "--confirm-run",
        action="store_true",
        help="Confirm the user explicitly approved the exact RunCronTask target.",
    )
    parser.add_argument(
        "--policy-only",
        action="store_true",
        help="Validate --call-tool policy and print the decision without connecting to AutoBGI.",
    )
    parser.add_argument("--output", help="Write full JSON probe result to this path.")
    args = parser.parse_args()

    policy: dict[str, Any] | None = None
    if args.call_tool:
        policy = validate_tool_call_policy(
            args.call_tool,
            args.arguments,
            allow_screenshot=args.allow_screenshot,
            confirm_run=args.confirm_run,
        )

    if args.policy_only:
        print(json.dumps({"tool": args.call_tool, "policy": policy}, ensure_ascii=False, indent=2))
        return 0

    url, api_key = resolve_mcp_config(args)
    result: dict[str, Any] = {
        "url": url,
        "apiKeyPresent": bool(api_key),
        "initialized": False,
        "tools": [],
    }

    with SseMcpClient(url, api_key, args.timeout) as client:
        result["initialize"] = client.initialize()
        result["initialized"] = True
        tools = client.list_tools()
        result["tools"] = tools
        result["toolNames"] = tool_names(tools)
        if args.call_tool:
            if args.call_tool == "RunCronTask":
                result["preflightFindBgiIndex"] = client.call_tool("findBgiIndex", {})
            result["toolCall"] = {
                "name": args.call_tool,
                "policy": policy,
                "result": client.call_tool(args.call_tool, args.arguments),
            }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")

    summary = {
        "url": url,
        "apiKeyPresent": bool(api_key),
        "initialized": result["initialized"],
        "toolNames": result.get("toolNames", []),
        "calledTool": args.call_tool or None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except McpProbeError as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
