$ErrorActionPreference = "Stop"

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$script:OutputEncoding = $utf8NoBom
$global:OutputEncoding = $utf8NoBom

$defaults = @{
    "Get-Content:Encoding" = "UTF8"
    "Set-Content:Encoding" = "UTF8"
    "Add-Content:Encoding" = "UTF8"
    "Out-File:Encoding" = "UTF8"
    "Export-Csv:Encoding" = "UTF8"
}

foreach ($key in $defaults.Keys) {
    $PSDefaultParameterValues[$key] = $defaults[$key]
}

function Read-Utf8Text {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath
    )

    $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $LiteralPath))
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        return [System.Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3)
    }
    return [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Write-Utf8Text {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath,

        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    [System.IO.File]::WriteAllText($LiteralPath, $Value, $utf8NoBom)
}

Write-Output "BetterGI_AI PowerShell UTF-8 profile loaded."
