export const PROTOCOL_VERSION = "0.1.0" as const;

export type RunnerStatusValue =
  | "unknown"
  | "unavailable"
  | "ready"
  | "running"
  | "degraded"
  | "failed";

export type JobStatusValue =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export type TransportConfig =
  | {
      type: "local-stdio";
      command: string;
      args?: string[];
    }
  | {
      type: "ssh-stdio";
      host: string;
      user?: string;
      remoteCommand: string;
      remoteArgs?: string[];
    };

export interface BetterGiConfig {
  installPath?: string;
  executablePath?: string;
  logDirectory?: string;
  scriptDirectory?: string;
}

export interface PolicyConfig {
  allowTasks: string[];
  allowScripts: string[];
  requireSingleActiveJob: boolean;
}

export interface AppConfig {
  transport: TransportConfig;
  runner?: {
    protocolVersion?: string;
  };
  bettergi?: BetterGiConfig;
  policy?: PolicyConfig;
}

export interface JsonRpcRequest<TParams = unknown> {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: TParams;
}

export interface JsonRpcSuccess<TResult = unknown> {
  jsonrpc: "2.0";
  id: string | number | null;
  result: TResult;
}

export interface JsonRpcFailure<TData = unknown> {
  jsonrpc: "2.0";
  id: string | number | null;
  error: {
    code: number;
    message: string;
    data?: TData;
  };
}

export type JsonRpcResponse<TResult = unknown, TData = unknown> =
  | JsonRpcSuccess<TResult>
  | JsonRpcFailure<TData>;

export interface DetectionResult {
  protocolVersion: string;
  runner: {
    version: string;
    hostOs: string;
    isWindows: boolean;
    pid: number;
  };
  bettergi: {
    configured: boolean;
    processFound: boolean;
    installPath?: string;
    executablePath?: string;
  };
  game: {
    processFound: boolean;
    windowDetected: boolean;
  };
}

export interface StatusResult extends DetectionResult {
  status: RunnerStatusValue;
  activeJob: JobSummary | null;
}

export interface Capability {
  name: string;
  description: string;
  mutating: boolean;
  available: boolean;
}

export interface JobSummary {
  jobId: string;
  capability: string;
  status: JobStatusValue;
  startedAt: string;
  finishedAt?: string;
}

export interface LogResult {
  source: "runner" | "bettergi" | "job";
  lines: string[];
  truncated: boolean;
}
