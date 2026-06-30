---
name: bettergi-agent
description: Use when an agent needs to inspect, run, stop, or troubleshoot BetterGI automation through the BetterGI AI MCP tools or runner. Trigger for requests involving BetterGI task execution, BetterGI status checks, macOS-to-Windows SSH control of BetterGI, allowlisted BetterGI scripts, BetterGI logs, or safe agent orchestration around BetterGI. Do not use for reimplementing BetterGI vision/game logic or for raw mouse/keyboard automation.
---

# BetterGI Agent

## Operating Model

Treat BetterGI as an external automation backend. Use MCP tools to inspect and dispatch semantic BetterGI capabilities; do not modify BetterGI internals or invent low-level input actions.

Preferred control chain:

```text
Agent -> BetterGI MCP tools -> runner transport -> Windows runner -> BetterGI adapter
```

## Required Workflow

1. Call `bettergi_detect` before any mutating action.
2. Call `bettergi_status` and confirm there is no conflicting active job.
3. Use `bettergi_list_capabilities` when the requested operation is ambiguous or not already known to be available.
4. For execution, prefer semantic task/script tools when present, such as `bettergi_run_task` or `bettergi_run_script`.
5. After a failure, call `bettergi_logs` before retrying.
6. Use `bettergi_stop` when the task is stuck, unsafe, or the user asks to stop.

## Safety Rules

- Do not call or propose arbitrary `click`, `pressKey`, `moveMouse`, or similar primitive controls.
- Do not run task or script names that are not allowlisted by the runner configuration.
- Do not start a second mutating task while a job is active.
- Do not repeatedly retry a failed automation without reading logs and changing the plan.
- Ask for user confirmation before high-impact actions such as long unattended routes, account-sensitive flows, or any task with unclear effects.
- If BetterGI, the runner, SSH, or the game window is unavailable, report the blocker and the exact missing dependency.

## Interpreting Status

- `ready`: safe to inspect capabilities or start an allowlisted task.
- `running`: read active job details; do not start another mutating task.
- `degraded`: inspect logs and explain the degraded dependency.
- `unavailable` or `failed`: do not run tasks; surface the detection result.

## Troubleshooting

Use `bettergi_logs` with a small tail first. Increase the tail only when the immediate failure context is insufficient.

When macOS controls a Windows host over SSH, distinguish:

- local MCP server failure
- SSH connection failure
- remote runner startup failure
- BetterGI process/window failure
- task adapter failure

Keep the response action-oriented: state what was checked, what failed, and the next concrete fix.
