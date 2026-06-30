#!/usr/bin/env node
import { createInterface } from "node:readline";

const startedAt = new Date().toISOString();
const logs = [`${startedAt} mock runner started`];

const capabilities = [
  {
    name: "detect",
    description: "Detect runner, BetterGI, and game state.",
    mutating: false,
    available: true
  },
  {
    name: "status",
    description: "Read current runner status.",
    mutating: false,
    available: true
  },
  {
    name: "logs",
    description: "Read recent runner logs.",
    mutating: false,
    available: true
  },
  {
    name: "stop",
    description: "Request active job cancellation.",
    mutating: true,
    available: true
  }
];

function detectionResult() {
  return {
    protocolVersion: "0.1.0",
    runner: {
      version: "0.1.0-dev",
      hostOs: process.platform,
      isWindows: process.platform === "win32",
      pid: process.pid
    },
    bettergi: {
      configured: false,
      processFound: false
    },
    game: {
      processFound: false,
      windowDetected: false
    }
  };
}

function statusResult() {
  return {
    ...detectionResult(),
    status: "ready",
    activeJob: null
  };
}

function handle(method, params) {
  switch (method) {
    case "runner.detect":
      return detectionResult();
    case "runner.status":
      return statusResult();
    case "runner.capabilities":
      return {
        protocolVersion: "0.1.0",
        capabilities
      };
    case "runner.logs": {
      const tail = Number.isInteger(params?.tail) ? params.tail : 100;
      return {
        source: params?.source ?? "runner",
        lines: logs.slice(-tail),
        truncated: logs.length > tail
      };
    }
    case "runner.stop":
      logs.push(`${new Date().toISOString()} stop requested: ${params?.reason ?? "no reason"}`);
      return {
        stopped: false,
        reason: "no active job"
      };
    default: {
      const error = new Error(`unknown runner method: ${method}`);
      error.code = -32601;
      throw error;
    }
  }
}

const rl = createInterface({
  input: process.stdin,
  crlfDelay: Infinity
});

for await (const line of rl) {
  if (!line.trim()) {
    continue;
  }

  let request;
  try {
    request = JSON.parse(line);
  } catch (error) {
    process.stdout.write(
      `${JSON.stringify({
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32700,
          message: "Parse error"
        }
      })}\n`
    );
    continue;
  }

  try {
    const result = handle(request.method, request.params ?? {});
    process.stdout.write(
      `${JSON.stringify({
        jsonrpc: "2.0",
        id: request.id,
        result
      })}\n`
    );
  } catch (error) {
    process.stdout.write(
      `${JSON.stringify({
        jsonrpc: "2.0",
        id: request.id ?? null,
        error: {
          code: error.code ?? -32603,
          message: error.message
        }
      })}\n`
    );
  }
}
