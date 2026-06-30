# Runner Protocol

The runner speaks newline-delimited JSON-RPC 2.0 over stdin/stdout.

## Transport Rules

- Each request and response is a single UTF-8 JSON line.
- `stdout` is reserved for JSON-RPC messages.
- Human diagnostics must go to `stderr`.
- The runner exits non-zero only for startup failures. Per-call failures are JSON-RPC errors.

## Request

```json
{"jsonrpc":"2.0","id":"1","method":"runner.detect","params":{}}
```

## Success Response

```json
{"jsonrpc":"2.0","id":"1","result":{"ok":true}}
```

## Error Response

```json
{"jsonrpc":"2.0","id":"1","error":{"code":-32001,"message":"BetterGI is not running","data":{"reason":"process_not_found"}}}
```

## Common Methods

### `runner.detect`

Returns host and dependency detection details.

### `runner.status`

Returns current runner state, BetterGI state, game-window state, and active job summary.

### `runner.capabilities`

Returns operations available under the current adapter configuration.

### `runner.logs`

Returns recent runner or BetterGI logs.

### `runner.stop`

Requests cancellation of the active job.

### `tasks.list`

Returns allowlisted semantic tasks and scripts.

### `tasks.run`

Starts an allowlisted task or script and returns a `jobId`.

### `jobs.status`

Returns job state.

### `jobs.logs`

Returns logs attached to a job.

## Status Values

- `unknown`
- `unavailable`
- `ready`
- `running`
- `degraded`
- `failed`

## Job Status Values

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

## Error Codes

- `-32601`: method not found
- `-32602`: invalid params
- `-32001`: BetterGI unavailable
- `-32002`: game window unavailable
- `-32003`: task not allowed
- `-32004`: job already running
- `-32005`: stop failed
- `-32010`: adapter failure

## Compatibility

Protocol messages include a `protocolVersion` field in detection and status results. The first version is `0.1.0`.
