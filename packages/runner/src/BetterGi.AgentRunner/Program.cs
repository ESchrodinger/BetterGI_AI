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
        JsonObject parameters = request?["params"]?.AsObject() ?? new JsonObject();

        try
        {
            object result = method switch
            {
                "runner.detect" => BuildDetectionResult(),
                "runner.status" => BuildStatusResult(),
                "runner.capabilities" => BuildCapabilitiesResult(),
                "runner.logs" => BuildLogsResult(parameters),
                "runner.stop" => BuildStopResult(parameters),
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

static object BuildDetectionResult()
{
    bool isWindows = OperatingSystem.IsWindows();
    bool betterGiFound = isWindows && AnyProcess("BetterGI", "BetterGenshinImpact");
    bool gameFound = isWindows && AnyProcess("YuanShen", "GenshinImpact", "Genshin Impact");

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
            configured = false,
            processFound = betterGiFound
        },
        game = new
        {
            processFound = gameFound,
            windowDetected = false
        }
    };
}

static object BuildStatusResult()
{
    object detection = BuildDetectionResult();
    JsonObject detectionJson = JsonSerializer.SerializeToNode(detection)!.AsObject();
    detectionJson["status"] = "ready";
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
                description = "Read recent runner logs.",
                mutating = false,
                available = true
            },
            new
            {
                name = "stop",
                description = "Request active job cancellation.",
                mutating = true,
                available = true
            }
        }
    };
}

static object BuildLogsResult(JsonObject parameters)
{
    int tail = parameters["tail"]?.GetValue<int>() ?? 100;
    string source = parameters["source"]?.GetValue<string>() ?? "runner";

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
