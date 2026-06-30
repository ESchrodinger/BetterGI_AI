using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Nodes;

const string ProtocolVersion = "0.1.0";
const string RunnerVersion = "0.1.0";

if (args.Length >= 2 && args[0] == "rpc" && args[1] == "--stdio")
{
    await RunRpcLoop();
    return;
}

Console.Error.WriteLine("Usage: bettergi-runner rpc --stdio");
Environment.ExitCode = 2;

static async Task RunRpcLoop()
{
    string? line;
    while ((line = await Console.In.ReadLineAsync()) is not null)
    {
        if (string.IsNullOrWhiteSpace(line))
        {
            continue;
        }

        JsonNode? request;
        try
        {
            request = JsonNode.Parse(line);
        }
        catch
        {
            await WriteError(null, -32700, "Parse error");
            continue;
        }

        JsonNode? id = request?["id"]?.DeepClone();
        string? method = request?["method"]?.GetValue<string>();
        JsonObject parameters = request?["params"] as JsonObject ?? new JsonObject();

        try
        {
            object result = method switch
            {
                "runner.detect" => BuildDetectionResult(parameters),
                "runner.status" => BuildStatusResult(parameters),
                "runner.capabilities" => BuildCapabilitiesResult(),
                "runner.logs" => BuildLogsResult(parameters),
                "runner.stop" => BuildStopResult(parameters),
                "tasks.list" => BuildTasksListResult(parameters),
                "tasks.run" => BuildTaskRunResult(parameters),
                "jobs.status" => throw new RpcException(-32006, "job not found"),
                "jobs.logs" => throw new RpcException(-32006, "job not found"),
                _ => throw new RpcException(-32601, $"unknown runner method: {method}")
            };

            await WriteSuccess(id, result);
        }
        catch (RpcException ex)
        {
            await WriteError(id, ex.Code, ex.Message);
        }
        catch (Exception ex)
        {
            await WriteError(id, -32603, ex.Message);
        }
    }
}

static object BuildDetectionResult(JsonObject parameters)
{
    JsonObject betterGiConfig = BetterGiConfig(parameters);
    bool isWindows = OperatingSystem.IsWindows();
    bool betterGiFound = isWindows && AnyProcess("BetterGI", "BetterGenshinImpact");
    bool gameFound = isWindows && AnyProcess("YuanShen", "GenshinImpact", "Genshin Impact");
    string? installPath = GetString(betterGiConfig, "installPath");
    string? executablePath = GetString(betterGiConfig, "executablePath");
    string? logDirectory = GetString(betterGiConfig, "logDirectory");
    string? scriptDirectory = GetString(betterGiConfig, "scriptDirectory");

    return new
    {
        protocolVersion = ProtocolVersion,
        runner = new
        {
            version = RunnerVersion,
            hostOs = RuntimeInformation.OSDescription,
            isWindows,
            pid = Environment.ProcessId
        },
        bettergi = new
        {
            configured = betterGiConfig.Count > 0,
            processFound = betterGiFound,
            installPath,
            installPathExists = Directory.Exists(installPath),
            executablePath,
            executablePathExists = File.Exists(executablePath),
            logDirectory,
            logDirectoryExists = Directory.Exists(logDirectory),
            scriptDirectory,
            scriptDirectoryExists = Directory.Exists(scriptDirectory)
        },
        game = new
        {
            processFound = gameFound,
            windowDetected = false
        }
    };
}

static object BuildStatusResult(JsonObject parameters)
{
    JsonObject detectionJson = JsonSerializer.SerializeToNode(BuildDetectionResult(parameters))!.AsObject();
    bool isWindows = detectionJson["runner"]?["isWindows"]?.GetValue<bool>() ?? false;

    detectionJson["status"] = isWindows ? "ready" : "degraded";
    detectionJson["activeJob"] = null;
    return detectionJson;
}

static object BuildCapabilitiesResult()
{
    return new
    {
        protocolVersion = ProtocolVersion,
        capabilities = new object[]
        {
            new
            {
                name = "detect",
                description = "Detect runner, BetterGI, and game state.",
                mutating = false,
                available = true
            },
            new
            {
                name = "status",
                description = "Read current runner status.",
                mutating = false,
                available = true
            },
            new
            {
                name = "logs",
                description = "Read recent runner or BetterGI logs.",
                mutating = false,
                available = true
            },
            new
            {
                name = "stop",
                description = "Request active job cancellation.",
                mutating = true,
                available = true
            },
            new
            {
                name = "list_tasks",
                description = "List allowlisted BetterGI tasks and scripts.",
                mutating = false,
                available = true
            },
            new
            {
                name = "run_task",
                description = "Dry-run allowlisted tasks; real execution needs an adapter.",
                mutating = true,
                available = true
            },
            new
            {
                name = "run_script",
                description = "Dry-run allowlisted scripts; real execution needs an adapter.",
                mutating = true,
                available = true
            },
            new
            {
                name = "job_status",
                description = "Read job status after task execution is implemented.",
                mutating = false,
                available = false
            },
            new
            {
                name = "job_logs",
                description = "Read job logs after task execution is implemented.",
                mutating = false,
                available = false
            }
        }
    };
}

static object BuildLogsResult(JsonObject parameters)
{
    int tail = ClampTail(parameters["tail"]?.GetValue<int>() ?? 100);
    string source = parameters["source"]?.GetValue<string>() ?? "runner";

    if (source == "bettergi")
    {
        string? logDirectory = GetString(BetterGiConfig(parameters), "logDirectory");
        if (string.IsNullOrWhiteSpace(logDirectory) || !Directory.Exists(logDirectory))
        {
            return new
            {
                source,
                lines = Array.Empty<string>(),
                truncated = false,
                unavailableReason = "BetterGI log directory is not configured or does not exist."
            };
        }

        string? latestLog = Directory
            .GetFiles(logDirectory)
            .OrderByDescending(File.GetLastWriteTimeUtc)
            .FirstOrDefault();

        if (latestLog is null)
        {
            return new
            {
                source,
                lines = Array.Empty<string>(),
                truncated = false,
                unavailableReason = "BetterGI log directory contains no files."
            };
        }

        (string[] lines, bool truncated) = ReadTail(latestLog, tail);
        return new
        {
            source,
            file = latestLog,
            lines,
            truncated
        };
    }

    return new
    {
        source,
        lines = new[]
        {
            $"{DateTimeOffset.UtcNow:O} bettergi-runner is running",
            $"{DateTimeOffset.UtcNow:O} log tail requested: {tail}"
        },
        truncated = false
    };
}

static object BuildTasksListResult(JsonObject parameters)
{
    JsonObject policy = Policy(parameters);
    string[] allowTasks = GetStringArray(policy, "allowTasks");
    string[] allowScripts = GetStringArray(policy, "allowScripts");

    return new
    {
        protocolVersion = ProtocolVersion,
        tasks = allowTasks.Select(name => new
        {
            kind = "task",
            name,
            allowed = true
        }),
        scripts = allowScripts.Select(name => new
        {
            kind = "script",
            name,
            allowed = true
        })
    };
}

static object BuildTaskRunResult(JsonObject parameters)
{
    string kind = parameters["kind"]?.GetValue<string>() ?? "task";
    string? name = parameters["name"]?.GetValue<string>();
    bool dryRun = parameters["dryRun"]?.GetValue<bool>() ?? false;

    if (string.IsNullOrWhiteSpace(name))
    {
        throw new RpcException(-32602, "task or script name is required");
    }

    JsonObject policy = Policy(parameters);
    string[] allowedNames = kind == "script"
        ? GetStringArray(policy, "allowScripts")
        : GetStringArray(policy, "allowTasks");

    if (!allowedNames.Contains(name))
    {
        throw new RpcException(-32003, $"{kind} is not allowlisted: {name}");
    }

    if (dryRun)
    {
        return new
        {
            accepted = true,
            dryRun = true,
            reason = "allowlist check passed; no BetterGI task was started"
        };
    }

    throw new RpcException(-32010, "BetterGI execution adapter is not configured yet");
}

static object BuildStopResult(JsonObject parameters)
{
    string reason = parameters["reason"]?.GetValue<string>() ?? "no reason";
    return new
    {
        stopped = false,
        reason = "no active job",
        requestedReason = reason
    };
}

static JsonObject Context(JsonObject parameters)
{
    return parameters["context"] as JsonObject ?? new JsonObject();
}

static JsonObject BetterGiConfig(JsonObject parameters)
{
    return Context(parameters)["bettergi"] as JsonObject ?? new JsonObject();
}

static JsonObject Policy(JsonObject parameters)
{
    return Context(parameters)["policy"] as JsonObject ?? new JsonObject();
}

static string? GetString(JsonObject obj, string propertyName)
{
    return obj[propertyName]?.GetValue<string>();
}

static string[] GetStringArray(JsonObject obj, string propertyName)
{
    if (obj[propertyName] is not JsonArray array)
    {
        return Array.Empty<string>();
    }

    return array
        .Select(node => node?.GetValue<string>())
        .Where(value => !string.IsNullOrWhiteSpace(value))
        .Cast<string>()
        .ToArray();
}

static int ClampTail(int tail)
{
    return Math.Min(Math.Max(tail, 1), 1000);
}

static (string[] Lines, bool Truncated) ReadTail(string path, int tail)
{
    Queue<string> queue = new();
    int total = 0;

    foreach (string line in File.ReadLines(path))
    {
        total += 1;
        if (queue.Count == tail)
        {
            queue.Dequeue();
        }
        queue.Enqueue(line);
    }

    return (queue.ToArray(), total > tail);
}

static bool AnyProcess(params string[] names)
{
    foreach (string name in names)
    {
        try
        {
            if (Process.GetProcessesByName(name).Length > 0)
            {
                return true;
            }
        }
        catch
        {
            return false;
        }
    }

    return false;
}

static async Task WriteSuccess(JsonNode? id, object result)
{
    await Console.Out.WriteLineAsync(JsonSerializer.Serialize(new
    {
        jsonrpc = "2.0",
        id,
        result
    }));
}

static async Task WriteError(JsonNode? id, int code, string message)
{
    await Console.Out.WriteLineAsync(JsonSerializer.Serialize(new
    {
        jsonrpc = "2.0",
        id,
        error = new
        {
            code,
            message
        }
    }));
}

internal sealed class RpcException : Exception
{
    public RpcException(int code, string message) : base(message)
    {
        Code = code;
    }

    public int Code { get; }
}
