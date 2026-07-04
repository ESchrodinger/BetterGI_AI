param(
  [string]$Configuration = "Debug",
  [string]$Runtime = "win-x64",
  [string]$PublishDir = "C:\Tools\bettergi-runner"
)

$ErrorActionPreference = "Stop"

foreach ($ToolPath in @(
    "C:\Program Files\Git\cmd",
    "C:\Program Files\nodejs",
    "$env:USERPROFILE\.dotnet",
    "$env:USERPROFILE\.dotnet\tools"
  )) {
  if ((Test-Path $ToolPath) -and (($env:Path -split ';') -notcontains $ToolPath)) {
    $env:Path = "$ToolPath;$env:Path"
  }
}

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Tool {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name,
    [string[]]$Arguments = @()
  )

  $Command = Get-Command $Name -ErrorAction Stop
  & $Command.Source @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$Name exited with code $LASTEXITCODE."
  }
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot
$DotnetCliHome = Join-Path $RepoRoot ".dotnet-cli"
New-Item -ItemType Directory -Force -Path $DotnetCliHome | Out-Null
$env:DOTNET_CLI_HOME = $DotnetCliHome
$env:DOTNET_NOLOGO = "true"
$env:NUGET_PACKAGES = Join-Path $DotnetCliHome "packages"
$env:APPDATA = Join-Path $DotnetCliHome "AppData\Roaming"
$env:LOCALAPPDATA = Join-Path $DotnetCliHome "AppData\Local"
New-Item -ItemType Directory -Force -Path (Join-Path $env:APPDATA "NuGet") | Out-Null
New-Item -ItemType Directory -Force -Path $env:LOCALAPPDATA | Out-Null
$NuGetConfig = Join-Path $DotnetCliHome "NuGet.Config"
@"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
  </packageSources>
</configuration>
"@ | Set-Content -LiteralPath $NuGetConfig -Encoding UTF8

Write-Step "Repository"
Invoke-Tool -Name "git" -Arguments @("status", "--short", "--branch")

Write-Step "Tool versions"
Invoke-Tool -Name "git" -Arguments @("--version")
Invoke-Tool -Name "dotnet" -Arguments @("--version")
Invoke-Tool -Name "node" -Arguments @("--version")
Invoke-Tool -Name "npm.cmd" -Arguments @("--version")

Write-Step "Node smoke test"
Invoke-Tool -Name "npm.cmd" -Arguments @("test")

Write-Step "Restore .NET runner"
Invoke-Tool -Name "dotnet" -Arguments @(
  "restore",
  ".\packages\runner\BetterGi.AgentRunner.sln",
  "-r",
  $Runtime,
  "--configfile",
  $NuGetConfig
)

Write-Step "Build .NET runner"
Invoke-Tool -Name "dotnet" -Arguments @(
  "build",
  ".\packages\runner\BetterGi.AgentRunner.sln",
  "-c",
  $Configuration,
  "--no-restore"
)

Write-Step "Publish .NET runner"
Invoke-Tool -Name "dotnet" -Arguments @(
  "publish",
  ".\packages\runner\src\BetterGi.AgentRunner",
  "-c",
  "Release",
  "-r",
  $Runtime,
  "--self-contained",
  "true",
  "--no-restore",
  "-o",
  $PublishDir
)

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
