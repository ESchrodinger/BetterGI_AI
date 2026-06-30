#!/usr/bin/env node
import { spawn } from "node:child_process";
import { once } from "node:events";
import { readFile } from "node:fs/promises";
import { createInterface } from "node:readline";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SERVER_VERSION = "0.1.0";
const ROOT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

const TOOL_DEFINITIONS = [
  {
    name: "bettergi_detect",
    description: "Detect runner, BetterGI, and game-window availability.",
    inputSchema: emptyObjectSchema()
  },
  {
    name: "bettergi_status",
    description: "Return current BetterGI runner status and active job summary.",
    inputSchema: emptyObjectSchema()
  },
  {
    name: "bettergi_list_capabilities",
    description: "List semantic BetterGI operations available through the runner.",
    inputSchema: emptyObjectSchema()
  },
  {
    name: "bettergi_logs",
    description: "Return recent runner or BetterGI log lines.",
    inputSchema: {
      type: "object",
      properties: {
        source: {
          type: "string",
          enum: ["runner", "bettergi"],
          default: "runner"
        },
        tail: {
          type: "integer",
          minimum: 1,
          maximum: 1000,
          default: 100
        }
      },
      additionalProperties: false
    }
  },
  {
    name: "bettergi_stop",
    description: "Request cancellation of the active BetterGI runner job.",
    inputSchema: {
      type: "object",
      properties: {
        reason: {
          type: "string",
          maxLength: 200
        }
      },
      additionalProperties: false
    }
  }
];

const TOOL_TO_RUNNER_METHOD = new Map([
  ["bettergi_detect", "runner.detect"],
  ["bettergi_status", "runner.status"],
  ["bettergi_list_capabilities", "runner.capabilities"],
  ["bettergi_logs", "runner.logs"],
  ["bettergi_stop", "runner.stop"]
]);

function emptyObjectSchema() {
  return {
    type: "object",
    properties: {},
    additionalProperties: false
  };
}

function parseArgs(argv) {
  const result = {
    configPath: "examples/dev-mock.config.json"
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--config") {
      result.configPath = argv[index + 1];
      index += 1;
    }
  }

  return result;
}

async function loadConfig(configPath) {
  const absolutePath = resolve(process.cwd(), configPath);
  const text = await readFile(absolutePath, "utf8");
  return JSON.parse(text);
}

class RunnerClient {
  constructor(config) {
    const processConfig = buildProcessConfig(config.transport);
    this.nextId = 1;
    this.pending = new Map();
    this.buffer = "";
    this.process = spawn(processConfig.command, processConfig.args, {
      cwd: ROOT_DIR,
      stdio: ["pipe", "pipe", "pipe"]
    });

    this.process.stdout.setEncoding("utf8");
    this.process.stdout.on("data", (chunk) => this.#onStdout(chunk));
    this.process.stderr.on("data", (chunk) => {
      process.stderr.write(`[bettergi-runner] ${chunk}`);
    });
    this.process.on("exit", (code, signal) => {
      const message = `runner exited with code ${code ?? "null"} and signal ${signal ?? "null"}`;
      for (const { reject, timeout } of this.pending.values()) {
        clearTimeout(timeout);
        reject(new Error(message));
      }
      this.pending.clear();
    });
  }

  async request(method, params = {}, timeoutMs = 10000) {
    if (!this.process.stdin.writable) {
      throw new Error("runner stdin is not writable");
    }

    const id = String(this.nextId++);
    const payload = { jsonrpc: "2.0", id, method, params };
    const line = `${JSON.stringify(payload)}\n`;

    const responsePromise = new Promise((resolvePromise, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`runner request timed out: ${method}`));
      }, timeoutMs);
      this.pending.set(id, { resolve: resolvePromise, reject, timeout });
    });

    this.process.stdin.write(line);
    const response = await responsePromise;
    if (response.error) {
      const error = new Error(response.error.message);
      error.code = response.error.code;
      error.data = response.error.data;
      throw error;
    }
    return response.result;
  }

  close() {
    this.process.kill();
  }

  #onStdout(chunk) {
    this.buffer += chunk;
    let newlineIndex = this.buffer.indexOf("\n");

    while (newlineIndex >= 0) {
      const line = this.buffer.slice(0, newlineIndex).trim();
      this.buffer = this.buffer.slice(newlineIndex + 1);
      newlineIndex = this.buffer.indexOf("\n");

      if (line.length === 0) {
        continue;
      }

      let message;
      try {
        message = JSON.parse(line);
      } catch (error) {
        process.stderr.write(`[bettergi-mcp] invalid runner JSON: ${line}\n`);
        continue;
      }

      const pending = this.pending.get(String(message.id));
      if (!pending) {
        process.stderr.write(`[bettergi-mcp] unhandled runner response id: ${message.id}\n`);
        continue;
      }

      clearTimeout(pending.timeout);
      this.pending.delete(String(message.id));
      pending.resolve(message);
    }
  }
}

function buildProcessConfig(transport) {
  if (!transport || transport.type === "local-stdio") {
    return {
      command: transport?.command ?? "node",
      args: transport?.args ?? ["packages/runner/dev/mock-runner.mjs"]
    };
  }

  if (transport.type === "ssh-stdio") {
    const target = transport.user ? `${transport.user}@${transport.host}` : transport.host;
    return {
      command: "ssh",
      args: [target, transport.remoteCommand, ...(transport.remoteArgs ?? [])]
    };
  }

  throw new Error(`unsupported transport type: ${transport.type}`);
}

function makeToolContent(result) {
  return [
    {
      type: "text",
      text: JSON.stringify(result, null, 2)
    }
  ];
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const config = await loadConfig(args.configPath);
  let runnerClient = null;

  const getRunner = () => {
    runnerClient ??= new RunnerClient(config);
    return runnerClient;
  };

  const rl = createInterface({
    input: process.stdin,
    crlfDelay: Infinity
  });

  const send = (message) => {
    process.stdout.write(`${JSON.stringify(message)}\n`);
  };

  const cleanup = () => {
    runnerClient?.close();
  };

  process.on("SIGTERM", cleanup);
  process.on("SIGINT", cleanup);
  process.on("exit", cleanup);

  for await (const line of rl) {
    if (!line.trim()) {
      continue;
    }

    let request;
    try {
      request = JSON.parse(line);
    } catch (error) {
      send({
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32700,
          message: "Parse error"
        }
      });
      continue;
    }

    try {
      const result = await handleMcpRequest(request, getRunner);
      if (request.id !== undefined) {
        send({
          jsonrpc: "2.0",
          id: request.id,
          result
        });
      }
    } catch (error) {
      if (request.id !== undefined) {
        send({
          jsonrpc: "2.0",
          id: request.id,
          error: {
            code: error.code ?? -32603,
            message: error.message,
            data: error.data
          }
        });
      }
    }
  }

  cleanup();
  await once(process, "beforeExit").catch(() => undefined);
}

async function handleMcpRequest(request, getRunner) {
  switch (request.method) {
    case "initialize":
      return {
        protocolVersion: request.params?.protocolVersion ?? "2024-11-05",
        capabilities: {
          tools: {}
        },
        serverInfo: {
          name: "bettergi-ai",
          version: SERVER_VERSION
        }
      };

    case "ping":
      return {};

    case "tools/list":
      return {
        tools: TOOL_DEFINITIONS
      };

    case "tools/call":
      return callTool(request.params, getRunner);

    default: {
      const error = new Error(`unknown MCP method: ${request.method}`);
      error.code = -32601;
      throw error;
    }
  }
}

async function callTool(params, getRunner) {
  const name = params?.name;
  const args = params?.arguments ?? {};
  const runnerMethod = TOOL_TO_RUNNER_METHOD.get(name);

  if (!runnerMethod) {
    const error = new Error(`unknown tool: ${name}`);
    error.code = -32602;
    throw error;
  }

  try {
    const result = await getRunner().request(runnerMethod, args);
    return {
      content: makeToolContent(result),
      isError: false
    };
  } catch (error) {
    return {
      content: makeToolContent({
        error: {
          code: error.code ?? -32603,
          message: error.message,
          data: error.data
        }
      }),
      isError: true
    };
  }
}

main().catch((error) => {
  process.stderr.write(`[bettergi-mcp] ${error.stack ?? error.message}\n`);
  process.exitCode = 1;
});
