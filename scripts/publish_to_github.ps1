param(
  [string]$RepoUrl = "https://github.com/Rouser0906/Product_QR-Code_Traceability-System",
  [string]$InitialTag = "v2.0.0",
  [switch]$CreateTag
)

Write-Host "Preparing to publish repository to $RepoUrl" -ForegroundColor Cyan

# Initialize git repo if needed
if (-not (Test-Path .git)) {
  git init
}

# Basic commit if no commits yet
$hasCommits = (git rev-parse --verify HEAD 2>$null) -ne $null
if (-not $hasCommits) {
  git add .
  git commit -m "chore: initial public release"
}

# Ensure main branch
try { git branch -M main } catch {}

# Set remote
try { git remote remove origin } catch {}
 git remote add origin $RepoUrl

# Push main
 git push -u origin main

# Optional tag
if ($CreateTag) {
  git tag -a $InitialTag -m "Public release $InitialTag"
  git push origin $InitialTag
}

Write-Host "Done. Repository pushed to $RepoUrl" -ForegroundColor Green
