# Windows Encoding

Use this whenever Chinese text, BetterGI JSON, AutoBGI JSON/YAML, or Markdown appears garbled in PowerShell output.

## Rule

Do not trust Windows PowerShell's default encoding when inspecting Chinese files. Garbled terminal output is not proof that the file is corrupt.

Prefer Python helpers for JSON/YAML mutation. If PowerShell is necessary, initialize UTF-8 handling first.

## Initialize PowerShell UTF-8

From the skill directory:

```powershell
. .\scripts\Use-Utf8PowerShell.ps1
```

Or from the repository root:

```powershell
. .\skills\bettergi-ai\scripts\Use-Utf8PowerShell.ps1
```

This affects only the current PowerShell session. It sets console input/output encoding to UTF-8 and sets common cmdlet defaults such as `Get-Content`, `Set-Content`, `Out-File`, and `Export-Csv` to `-Encoding UTF8`.

## Read Files Safely

Preferred for JSON and Markdown:

```powershell
. .\skills\bettergi-ai\scripts\Use-Utf8PowerShell.ps1
Read-Utf8Text -LiteralPath .\README.zh-CN.md
```

Acceptable quick read:

```powershell
Get-Content -Encoding UTF8 -LiteralPath .\README.zh-CN.md
```

Raw-byte fallback when the shell still displays incorrectly:

```powershell
$bytes = [System.IO.File]::ReadAllBytes("C:\Path\To\main.json")
[System.Text.Encoding]::UTF8.GetString($bytes)
```

For JSON edits, prefer the bundled Python scripts because they read UTF-8, tolerate UTF-8 BOM, and write UTF-8 consistently.

## Write Files Safely

Preferred:

```powershell
. .\skills\bettergi-ai\scripts\Use-Utf8PowerShell.ps1
Write-Utf8Text -LiteralPath .\notes.txt -Value "启动一条龙"
```

Acceptable:

```powershell
Set-Content -Encoding UTF8 -LiteralPath .\notes.txt -Value "启动一条龙"
```

Avoid shell redirection (`>` and `>>`) for Chinese JSON/Markdown in Windows PowerShell. Redirection encoding differs by shell version and can create misleading results.

## Diagnosis

If an agent sees text such as `鍚姩涓€鏉￠緳` where it expected `启动一条龙`:

1. Re-read the file with `Get-Content -Encoding UTF8`.
2. If still suspicious, use `Read-Utf8Text` or raw bytes plus `[System.Text.Encoding]::UTF8.GetString(...)`.
3. Do not rewrite the file merely to "fix" display output.
4. Run the encoding smoke test after changing encoding-sensitive code:

```bash
python scripts/run_encoding_smoke_tests.py
```

## AutoBGI / BetterGI Notes

- AutoBGI `main.json` and BetterGI user JSON should be treated as UTF-8.
- Tolerate UTF-8 BOM on reads.
- Do not use PowerShell's default `Get-Content` output to decide that JSON parsing failed.
- If a script returns structured JSON error `invalid_json`, inspect both syntax and encoding before editing the file.
