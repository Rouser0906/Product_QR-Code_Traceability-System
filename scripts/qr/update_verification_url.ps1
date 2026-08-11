param(
  [string]$HsDir = "cloud/demo_json_a",
  [string]$ZyDir = "cloud/demo_json_b",
  [switch]$DryRun
)

function Update-Dir([string]$Dir) {
  if (-not (Test-Path -LiteralPath $Dir)) {
    Write-Host "Directory not found: $Dir" -ForegroundColor Yellow
    return
  }

  $files = Get-ChildItem -Path $Dir -Filter *.json -Recurse -File
  $pattern = '"verification_url"\s*:\s*"https://company_a\.com/index\.html\?code=([^"]+)"'
  $replacement = '"verification_url": "https://scan.example.com/index.html?code=$1"'

  foreach ($f in $files) {
    try {
      $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
      if ($content -match $pattern) {
        $new = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, $replacement)
        if ($DryRun) {
          Write-Host "[DRY] Would update: $($f.FullName)" -ForegroundColor Cyan
        } else {
          $bakPath = "$($f.FullName).bak"
          [System.IO.File]::Copy($f.FullName, $bakPath, $true)
          [System.IO.File]::WriteAllText($f.FullName, $new, [System.Text.Encoding]::UTF8)
          Write-Host "Updated: $($f.FullName)" -ForegroundColor Green
        }
      }
    } catch {
      Write-Host "Failed: $($f.FullName) -> $($_.Exception.Message)" -ForegroundColor Red
    }
  }
}

try {
  Update-Dir -Dir $HsDir
  Update-Dir -Dir $ZyDir
  Write-Host "Completed." -ForegroundColor Green
} catch {
  Write-Host "Process failed: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}