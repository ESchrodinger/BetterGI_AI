#!/usr/bin/env node
import { createInterface } from "node:readline";

const startedAt = new Date().toISOString();
const logs = [`${startedAt} mock runner started`];
const jobs = new Map();

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
  },
  {
    name: "list_tasks",
    description: "List allowlisted BetterGI tasks and scripts.",
    mutating: false,
    available: true
  },
  {
    name: "run_task",
    description: "Start or dry-run an allowlisted BetterGI task.",
    mutating: true,
    available: true
  },
  {
    name: "run_script",
    description: "Start or dry-run an allowlisted BetterGI script.",
    mutating: true,
    available: true
  },
  {
    name: "job_status",
    description: "Read a runner job status.",
    mutating: false,
    available: true
  },
  {
    name: "job_logs",
    description: "Read runner job logs.",
    mutating: false,
    available: true
  }
];

function detectionResult(params = {}) {
  const bettergiConfig = params.context?.bettergi ?? {};
  return {
    protocolVersion: "0.1.0",
    runner: {
      version: "0.1.0-dev",
      hostOs: process.platform,
      isWindows: process.platform === "win32",
      pid: process.pid
    },
    bettergi: {
      configured: Object.keys(bettergiConfig).length > 0,
      processFound: false,
      installPath: bettergiConfig.installPath,
      executablePath: bettergiConfig.executablePath,
      logDirectory: bettergiConfig.logDirectory,
      scriptDirectory: bettergiConfig.scriptDirectory
    },
    game: {
      processFound: false,
      windowDetected: false
    }
  };
}

function statusResult(params = {}) {
  return {
    ...detectionResult(params),
    status: "ready",
    activeJob: activeJob()
  };
}

function activeJob() {
  return [...jobs.values()].find((job) => job.status === "running") ?? null;
}

function policy(params = {}) {
  return {
    allowTasks: params.context?.policy?.allowTasks ?? [],
    allowScripts: params.context?.policy?.allowScripts ?? [],
    requireSingleActiveJob: params.context?.policy?.requireSingleActiveJob ?? true
  };
}

function listTasks(params = {}) {
  const currentPolicy = policy(params);
  return {
    protocolVersion: "0.1.0",
    tasks: currentPolicy.allowTasks.map((name) => ({
      kind: "task",
      name,
      allowed: true
    })),
    scripts: currentPolicy.allowScripts.map((name) => ({
      kind: "script",
      name,
      allowed: true
    }))
  };
}

function runTask(params = {}) {
  const kind = params.kind ?? "task";
  const name = params.name;
  const dryRun = params.dryRun === true;
  const currentPolicy = policy(params);
  const allowedNames = kind === "script" ? currentPolicy.allowScripts : currentPolicy.allowTasks;

  if (!allowedNames.includes(name)) {
    const error = new Error(`${kind} is not allowlisted: ${name}`);
    error.code = -32003;
    throw error;
  }

  if (dryRun) {
    return {
      accepted: true,
      dryRun: true,
      reason: "mock runner dry run accepted"
    };
  }

  const jobId = `mock-${Date.now()}`;
  const now = new Date().toISOString();
  const job = {
    jobId,
    capability: `${kind}:${name}`,
    status: "succeeded",
    startedAt: now,
    finishedAt: now
  };
  jobs.set(jobId, job);
  logs.push(`${now} mock job succeeded: ${job.capability}`);

  return {
    accepted: true,
    dryRun: false,
    jobId,
    status: job.status
  };
}

function jobStatus(params = {}) {
  const job = jobs.get(params.jobId);
  if (!job) {
    const error = new Error(`job not found: ${params.jobId}`);
    error.code = -32006;
    throw error;
  }
  return job;
}

function jobLogs(params = {}) {
  const job = jobs.get(params.jobId);
  if (!job) {
    const error = new Error(`job not found: ${params.jobId}`);
    error.code = -32006;
    throw error;
  }

  const tail = Number.isInteger(params.tail) ? params.tail : 100;
  const lines = [
    `${job.startedAt} mock job started: ${job.capability}`,
    `${job.finishedAt ?? job.startedAt} mock job status: ${job.status}`
  ];

  return {
    source: "job",
    lines: lines.slice(-tail),
    truncated: lines.length > tail
  };
}

function handle(method, params) {
  switch (method) {
    case "runner.detect":
      return detectionResult(params);
    case "runner.status":
      return statusResult(params);
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
    case "tasks.list":
      return listTasks(params);
    case "tasks.run":
      return runTask(params);
    case "jobs.status":
      return jobStatus(params);
    case "jobs.logs":
      return jobLogs(params);
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
