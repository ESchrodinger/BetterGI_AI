param(
  [string]$InstallPath = "C:\Program Files\BetterGI",
  [string]$Search = "",
  [int]$Limit = 50,
  [switch]$Full
)

$ErrorActionPreference = "Stop"

function Join-UserPath {
  param([string]$Child)
  return Join-Path (Join-Path $InstallPath "User") $Child
}

function Get-RelativePathCompat {
  param(
    [Parameter(Mandatory = $true)][string]$Root,
    [Parameter(Mandatory = $true)][string]$Path
  )

  $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
  $pathFull = [System.IO.Path]::GetFullPath($Path)

  if ($pathFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $pathFull.Substring($rootFull.Length)
  }

  return $pathFull
}

function Read-JsonFile {
  param([string]$Path)
  $text = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
  return $text | ConvertFrom-Json
}

function Matches-Search {
  param(
    [string]$Text,
    [string]$Search
  )

  if ([string]::IsNullOrWhiteSpace($Search)) {
    return $true
  }

  return $Text.IndexOf($Search, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

$userPath = Join-Path $InstallPath "User"
$autoPathingRoot = Join-UserPath "AutoPathing"
$jsScriptRoot = Join-UserPath "JsScript"
$keyMouseRoot = Join-UserPath "KeyMouseScript"
$scriptGroupRoot = Join-UserPath "ScriptGroup"
$oneDragonRoot = Join-UserPath "OneDragon"

$pathing = @()
if (Test-Path -LiteralPath $autoPathingRoot) {
  $pathing = Get-ChildItem -LiteralPath $autoPathingRoot -Recurse -Filter "*.json" -File -ErrorAction SilentlyContinue | ForEach-Object {
    $relative = Get-RelativePathCompat -Root $autoPathingRoot -Path $_.FullName
    $folder = Split-Path $relative -Parent
    $name = Split-Path $relative -Leaf
    [pscustomobject]@{
      type = "Pathing"
      name = $name
      folderName = $folder
      relativePath = $relative
      length = $_.Length
      lastWriteTime = $_.LastWriteTime.ToString("o")
    }
  } | Where-Object {
    Matches-Search -Text ($_.relativePath) -Search $Search
  }
}

$jsScripts = @()
if (Test-Path -LiteralPath $jsScriptRoot) {
  $jsScripts = Get-ChildItem -LiteralPath $jsScriptRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $manifestPath = Join-Path $_.FullName "manifest.json"
    $manifestName = $_.Name
    $hasManifest = Test-Path -LiteralPath $manifestPath
    if ($hasManifest) {
      try {
        $manifest = Read-JsonFile -Path $manifestPath
        if ($manifest.name) {
          $manifestName = [string]$manifest.name
        }
      } catch {
      }
    }
    [pscustomobject]@{
      type = "Javascript"
      name = $manifestName
      folderName = $_.Name
      hasManifest = $hasManifest
      relativePath = $_.Name
      lastWriteTime = $_.LastWriteTime.ToString("o")
    }
  } | Where-Object {
    Matches-Search -Text ($_.name + "\" + $_.folderName) -Search $Search
  }
}

$keyMouse = @()
if (Test-Path -LiteralPath $keyMouseRoot) {
  $keyMouse = Get-ChildItem -LiteralPath $keyMouseRoot -File -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{
      type = "KeyMouse"
      name = $_.Name
      folderName = $_.Name
      relativePath = $_.Name
      length = $_.Length
      lastWriteTime = $_.LastWriteTime.ToString("o")
    }
  } | Where-Object {
    Matches-Search -Text $_.name -Search $Search
  }
}

$scriptGroups = @()
if (Test-Path -LiteralPath $scriptGroupRoot) {
  $scriptGroups = Get-ChildItem -LiteralPath $scriptGroupRoot -Filter "*.json" -File -ErrorAction SilentlyContinue | ForEach-Object {
    try {
      $group = Read-JsonFile -Path $_.FullName
      [pscustomobject]@{
        name = $group.name
        fileName = $_.Name
        index = $group.index
        projectCount = @($group.projects).Count
        enabledCount = @($group.projects | Where-Object { $_.status -eq "Enabled" }).Count
      }
    } catch {
      [pscustomobject]@{
        name = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        fileName = $_.Name
        index = $null
        projectCount = $null
        enabledCount = $null
      }
    }
  }
}

$oneDragons = @()
if (Test-Path -LiteralPath $oneDragonRoot) {
  $oneDragons = Get-ChildItem -LiteralPath $oneDragonRoot -Filter "*.json" -File -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{
      name = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
      fileName = $_.Name
      length = $_.Length
      lastWriteTime = $_.LastWriteTime.ToString("o")
    }
  }
}

$allCallable = @($pathing) + @($jsScripts) + @($keyMouse)
$items = if ($Full) { $allCallable } else { $allCallable | Select-Object -First $Limit }

$topPathingFolders = @()
if ($pathing.Count -gt 0) {
  $topPathingFolders = $pathing | ForEach-Object {
    $top = ($_.folderName -split '\\')[0]
    if ([string]::IsNullOrWhiteSpace($top)) { $top = "." }
    [pscustomobject]@{ top = $top }
  } | Group-Object top | Sort-Object Count -Descending | ForEach-Object {
    [pscustomobject]@{ name = $_.Name; count = $_.Count }
  }
}

[pscustomobject]@{
  installPath = $InstallPath
  userPath = $userPath
  search = $Search
  counts = [pscustomobject]@{
    callableTotal = $allCallable.Count
    pathing = @($pathing).Count
    javascript = @($jsScripts).Count
    keyMouse = @($keyMouse).Count
    scriptGroups = @($scriptGroups).Count
    oneDragons = @($oneDragons).Count
  }
  topPathingFolders = @($topPathingFolders | Select-Object -First 30)
  callableItems = @($items)
  scriptGroups = @($scriptGroups)
  oneDragons = @($oneDragons)
} | ConvertTo-Json -Depth 8
