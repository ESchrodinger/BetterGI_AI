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

async function callTool(name, args = {}) {
  const result = await request("tools/call", {
    name,
    arguments: args
  });
  const payload = JSON.parse(result.content[0].text);
  return {
    result,
    payload
  };
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

  const detect = await callTool("bettergi_detect");
  assert.equal(detect.result.isError, false);
  assert.equal(detect.payload.protocolVersion, "0.1.0");
  assert.equal(detect.payload.bettergi.configured, false);

  const status = await callTool("bettergi_status");
  assert.equal(status.result.isError, false);
  assert.equal(status.payload.status, "ready");

  const tasks = await callTool("bettergi_list_tasks");
  assert.equal(tasks.result.isError, false);
  assert.deepEqual(
    tasks.payload.tasks.map((task) => task.name),
    ["mock_route"]
  );
  assert.deepEqual(
    tasks.payload.scripts.map((script) => script.name),
    ["mock_script"]
  );

  const dryRun = await callTool("bettergi_run_task", {
    task: "mock_route",
    dryRun: true
  });
  assert.equal(dryRun.result.isError, false);
  assert.equal(dryRun.payload.accepted, true);
  assert.equal(dryRun.payload.dryRun, true);

  const run = await callTool("bettergi_run_task", {
    task: "mock_route"
  });
  assert.equal(run.result.isError, false);
  assert.equal(run.payload.accepted, true);
  assert.equal(run.payload.status, "succeeded");

  const job = await callTool("bettergi_job_status", {
    jobId: run.payload.jobId
  });
  assert.equal(job.result.isError, false);
  assert.equal(job.payload.jobId, run.payload.jobId);

  const jobLogs = await callTool("bettergi_job_logs", {
    jobId: run.payload.jobId,
    tail: 5
  });
  assert.equal(jobLogs.result.isError, false);
  assert.match(jobLogs.payload.lines.join("\n"), /mock job status: succeeded/);

  const logs = await callTool("bettergi_logs", {
    tail: 5
  });
  assert.equal(logs.result.isError, false);
  assert.match(logs.payload.lines.join("\n"), /mock runner started/);

  const stop = await callTool("bettergi_stop", {
    reason: "smoke test"
  });
  assert.equal(stop.result.isError, false);

  server.stdin.end();
  server.kill();
  console.log("mcp smoke test passed");
} catch (error) {
  server.kill();
  throw error;
}
