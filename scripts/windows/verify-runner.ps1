param(
  [string]$Configuration = "Debug",
  [string]$Runtime = "win-x64",
  [string]$PublishDir = "C:\Tools\bettergi-runner"
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

Write-Step "Repository"
git status --short --branch

Write-Step "Tool versions"
git --version
dotnet --version
node --version
npm --version

Write-Step "Node smoke test"
npm test

Write-Step "Build .NET runner"
dotnet build ".\packages\runner\BetterGi.AgentRunner.sln" -c $Configuration

Write-Step "Publish .NET runner"
dotnet publish ".\packages\runner\src\BetterGi.AgentRunner" `
  -c Release `
  -r $Runtime `
  --self-contained true `
  -o $PublishDir

$RunnerExe = Join-Path $PublishDir "bettergi-runner.exe"
if (-not (Test-Path $RunnerExe)) {
  throw "Runner executable not found: $RunnerExe"
}

Write-Step "Runner detect JSON-RPC"
$Context = @{
  protocolVersion = "0.1.0"
  bettergi = @{}
  policy = @{
    allowTasks = @("windows_verify_task")
    allowScripts = @("windows_verify_script")
    requireSingleActiveJob = $true
  }
}

$DetectRequest = @{
  jsonrpc = "2.0"
  id = "detect"
  method = "runner.detect"
  params = @{
    context = $Context
  }
} | ConvertTo-Json -Depth 12 -Compress

$DetectResponse = $DetectRequest | & $RunnerExe rpc --stdio
Write-Host $DetectResponse

$ParsedDetect = $DetectResponse | ConvertFrom-Json
if ($ParsedDetect.result.runner.isWindows -ne $true) {
  throw "Expected runner.detect result.runner.isWindows to be true."
}

Write-Step "Runner tasks dry-run"
$DryRunRequest = @{
  jsonrpc = "2.0"
  id = "dry-run"
  method = "tasks.run"
  params = @{
    kind = "task"
    name = "windows_verify_task"
    dryRun = $true
    context = $Context
  }
} | ConvertTo-Json -Depth 12 -Compress

$DryRunResponse = $DryRunRequest | & $RunnerExe rpc --stdio
Write-Host $DryRunResponse

$ParsedDryRun = $DryRunResponse | ConvertFrom-Json
if ($ParsedDryRun.result.accepted -ne $true) {
  throw "Expected dry-run tasks.run to be accepted."
}

Write-Step "Verification complete"
Write-Host "Runner published to $PublishDir" -ForegroundColor Green
