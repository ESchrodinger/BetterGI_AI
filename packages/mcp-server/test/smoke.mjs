import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { resolve } from "node:path";

const rootDir = resolve(import.meta.dirname, "../../..");
const server = spawn(
  "node",
  ["packages/mcp-server/src/index.mjs", "--config", "examples/dev-mock.config.json"],
  {
    cwd: rootDir,
    stdio: ["pipe", "pipe", "pipe"]
  }
);

let nextId = 1;
let buffer = "";
const pending = new Map();

server.stdout.setEncoding("utf8");
server.stdout.on("data", (chunk) => {
  buffer += chunk;
  let newlineIndex = buffer.indexOf("\n");
  while (newlineIndex >= 0) {
    const line = buffer.slice(0, newlineIndex).trim();
    buffer = buffer.slice(newlineIndex + 1);
    newlineIndex = buffer.indexOf("\n");
    if (!line) {
      continue;
    }
    const response = JSON.parse(line);
    const handler = pending.get(String(response.id));
    if (handler) {
      pending.delete(String(response.id));
      handler(response);
    }
  }
});

server.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
});

function request(method, params = {}) {
  const id = String(nextId++);
  const payload = { jsonrpc: "2.0", id, method, params };
  server.stdin.write(`${JSON.stringify(payload)}\n`);
  return new Promise((resolvePromise, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`timed out waiting for ${method}`));
    }, 5000);
    pending.set(id, (response) => {
      clearTimeout(timeout);
      if (response.error) {
        reject(new Error(response.error.message));
      } else {
        resolvePromise(response.result);
      }
    });
  });
}

try {
  const initialize = await request("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: {
      name: "smoke-test",
      version: "0.1.0"
    }
  });
  assert.equal(initialize.serverInfo.name, "bettergi-ai");

  const tools = await request("tools/list");
  assert.ok(tools.tools.some((tool) => tool.name === "bettergi_detect"));

  const detect = await request("tools/call", {
    name: "bettergi_detect",
    arguments: {}
  });
  assert.equal(detect.isError, false);
  assert.match(detect.content[0].text, /"protocolVersion": "0.1.0"/);

  const status = await request("tools/call", {
    name: "bettergi_status",
    arguments: {}
  });
  assert.equal(status.isError, false);
  assert.match(status.content[0].text, /"status": "ready"/);

  const logs = await request("tools/call", {
    name: "bettergi_logs",
    arguments: {
      tail: 5
    }
  });
  assert.equal(logs.isError, false);
  assert.match(logs.content[0].text, /mock runner started/);

  const stop = await request("tools/call", {
    name: "bettergi_stop",
    arguments: {
      reason: "smoke test"
    }
  });
  assert.equal(stop.isError, false);

  server.stdin.end();
  server.kill();
  console.log("mcp smoke test passed");
} catch (error) {
  server.kill();
  throw error;
}
