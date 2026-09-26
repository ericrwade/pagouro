# Check every file on this stick against MANIFEST.md — no Python needed (PowerShell ships with Windows).
#   Double-click VERIFY.bat, or:  powershell -ExecutionPolicy Bypass -File verify_manifest.ps1
# Same rules as verify_manifest.py: one line per mismatch or missing file, then a verdict; extra files are
# reported and do not fail the check. Exit code 0 = every listed file matches; 1 otherwise. No network.
param([string]$Folder = $PSScriptRoot)
$ErrorActionPreference = "Continue"
$manifest = Join-Path $Folder "MANIFEST.md"
if (-not (Test-Path $manifest)) { Write-Host "MANIFEST.md not found in $Folder"; exit 1 }
$rows = @()
foreach ($line in Get-Content $manifest -Encoding UTF8) {
    if ($line -match '^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*([0-9,]+)\s*\|') {
        $rows += [pscustomobject]@{ Path = $Matches[1]; Sha = $Matches[2]; Bytes = [int64]($Matches[3] -replace ',', '') }
    }
}
if ($rows.Count -eq 0) { Write-Host "no file rows found in MANIFEST.md"; exit 1 }
$bad = 0; $n = 0
foreach ($r in $rows) {
    $n++
    $p = Join-Path $Folder ($r.Path -replace '/', '\')
    if (-not (Test-Path $p)) { Write-Host ("MISSING   {0}" -f $r.Path); $bad++; continue }
    $len = (Get-Item $p).Length
    if ($len -ne $r.Bytes) { Write-Host ("SIZE      {0}  ({1} bytes, manifest says {2})" -f $r.Path, $len, $r.Bytes); $bad++; continue }
    $h = (Get-FileHash -Algorithm SHA256 -Path $p).Hash.ToLower()
    if ($h -ne $r.Sha) { Write-Host ("MISMATCH  {0}" -f $r.Path); $bad++ }
    if ($n % 20 -eq 0) { Write-Host ("  ... {0} of {1} checked" -f $n, $rows.Count) }
}
$listed = @{}; foreach ($r in $rows) { $listed[($r.Path -replace '/', '\')] = $true }
$extra = Get-ChildItem -Path $Folder -File -Recurse | Where-Object {
    $rel = $_.FullName.Substring($Folder.TrimEnd('\').Length + 1)
    -not $listed.ContainsKey($rel) -and $rel -ne "MANIFEST.md" -and $rel -notlike "workspace\*"
}
foreach ($e in $extra) { Write-Host ("extra (not in manifest, not a failure): {0}" -f $e.FullName.Substring($Folder.TrimEnd('\').Length + 1)) }
Write-Host ""
Write-Host ("files hashed: {0}" -f $rows.Count)
if ($bad -eq 0) { Write-Host "VERDICT: every listed file matches the manifest"; exit 0 }
else { Write-Host ("VERDICT: {0} file(s) do not match — this copy is not what the manifest describes" -f $bad); exit 1 }
