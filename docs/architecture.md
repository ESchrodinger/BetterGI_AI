# Architecture

BetterGI AI is a portable control plane that lets agents call BetterGI without forking or replacing BetterGI.

## Goals

- Keep BetterGI updateable as an upstream application.
- Expose stable semantic tools to agents through MCP.
- Support both local Windows execution and macOS-to-Windows execution over SSH.
- Keep all game-adjacent automation on the Windows host that owns the game window.
- Make every task observable, cancellable, and auditable.

## Non-Goals

- Do not reimplement BetterGI computer vision, OCR, route execution, or input simulation.
- Do not inject into the game process or read game memory.
- Do not expose arbitrary low-level mouse or keyboard control to agents.
- Do not require BetterGI source changes for the first usable version.

## Layers

```text
Agent host
  MCP client
    |
    | Model Context Protocol
    v
packages/mcp-server
    |
    | local stdio or SSH stdio
    v
packages/runner
    |
    | adapter calls
    v
BetterGI upstream install
    |
    v
Game window on Windows
```

## MCP Server

The MCP server is cross-platform. It owns the agent-facing tool names, validates arguments, applies policy, and forwards accepted calls to a configured runner transport.

Responsibilities:

- Load local configuration.
- Start a local runner or an SSH-backed runner process.
- Expose only semantic BetterGI operations.
- Normalize runner errors into tool results agents can reason about.
- Avoid host-specific BetterGI assumptions.

## Transport

Transports connect the MCP server to the runner.

- `local-stdio`: start the runner directly on the same Windows host.
- `ssh-stdio`: start the runner on a remote Windows host over SSH from macOS, Linux, or Windows.

The protocol is newline-delimited JSON-RPC over stdin/stdout so the same runner command works locally and remotely.

## Runner

The runner is the Windows-side executable. It runs near BetterGI and has access to Windows process, window, filesystem, and future bridge APIs.

Responsibilities:

- Detect Windows, BetterGI, and game-window state.
- Read configured BetterGI paths and logs.
- Enforce a single active job lock.
- Dispatch allowlisted BetterGI tasks or scripts.
- Report status, logs, and structured failures.
- Stop active jobs.

## Adapters

Adapters isolate BetterGI integration strategies from the runner core.

- `filesystem`: read config, script inventory, and logs.
- `process`: detect BetterGI and game processes.
- `ui`: optional window/hotkey integration for early prototypes.
- `bridge`: future stable local API if BetterGI exposes or accepts one.

Adapters should be replaceable without changing the MCP tool contract.

## BetterGI Separation

BetterGI remains an upstream dependency installed outside this repository. This project should reference BetterGI through configuration:

- install path
- executable path
- log directory
- script directory
- optional bridge endpoint

Do not vendor BetterGI binaries, models, logs, captures, or user credentials.

## Job Model

A task run creates a job:

- `jobId`: stable id returned to the caller
- `status`: `queued`, `running`, `succeeded`, `failed`, `cancelled`
- `startedAt` / `finishedAt`
- `capability`: semantic operation being executed
- `logRef`: source for tailing logs

The runner must reject a second mutating job while one is active unless the operation is `stop`.

## Versioning

The public compatibility surfaces are:

- MCP tool names and schemas
- runner JSON-RPC methods
- configuration file shape
- skill instructions

Breaking changes should update protocol version and examples together.
