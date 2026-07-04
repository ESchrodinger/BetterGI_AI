#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-100.79.35.44}"
REMOTE_RUNNER="${2:-C:\\Tools\\bettergi-runner\\bettergi-runner.exe}"

REQUEST='{"jsonrpc":"2.0","id":"1","method":"runner.detect","params":{"context":{"protocolVersion":"0.1.0","bettergi":{},"policy":{"allowTasks":[],"allowScripts":[],"requireSingleActiveJob":true}}}}'

printf '%s\n' "$REQUEST" | ssh "$HOST" "$REMOTE_RUNNER" rpc --stdio
