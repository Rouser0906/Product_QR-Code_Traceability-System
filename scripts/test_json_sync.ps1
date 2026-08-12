# 测试JSON自动同步功能
param(
  [switch]$Cleanup = $false
)

$projectRoot = (Get-Location).Path
$aDir = Join-Path $projectRoot "cloud\demo_json_a"
$zyDir = Join-Path $projectRoot "cloud\demo_json_b"
$logFile = Join-Path $projectRoot "auto_sync\logs\ftp_uploader.log"

if ($Cleanup) {
  Write-Host "清理测试文件..." -ForegroundColor Yellow
  Remove-Item -Path "$aDir\test_*.json" -ErrorAction SilentlyContinue
  Remove-Item -Path "$zyDir\test_*.json" -ErrorAction SilentlyContinue
  Remove-Item -Path "C:\inetpub\qr-system\companies\demo_json_a\test_*.json" -ErrorAction SilentlyContinue
  Remove-Item -Path "C:\inetpub\qr-system\companies\demo_json_b\test_*.json" -ErrorAction SilentlyContinue
  Write-Host "清理完成" -ForegroundColor Green
  return
}

Write-Host "开始测试JSON自动同步功能..." -ForegroundColor Green

# 创建测试文件
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$hsTestFile = Join-Path $aDir "test_a_$timestamp.json"
$zyTestFile = Join-Path $zyDir "test_b_$timestamp.json"

$testData = @{
  test = $true
  timestamp = $timestamp
  source = "auto_sync_test"
} | ConvertTo-Json

Write-Host "创建测试文件..." -ForegroundColor Yellow
Set-Content -Path $hsTestFile -Value $testData -Encoding UTF8
Set-Content -Path $zyTestFile -Value $testData -Encoding UTF8

Write-Host "等待同步完成..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查结果
$aTarget = "C:\inetpub\qr-system\companies\demo_json_a\test_a_$timestamp.json"
$bTarget = "C:\inetpub\qr-system\companies\demo_json_b\test_b_$timestamp.json"

$aSuccess = Test-Path $aTarget
$bSuccess = Test-Path $bTarget

Write-Host "测试结果:" -ForegroundColor Cyan
Write-Host "  A同步: $(if($aSuccess){'成功'}else{'失败'}) - $aTarget" -ForegroundColor $(if($aSuccess){'Green'}else{'Red'})
Write-Host "  B同步: $(if($bSuccess){'成功'}else{'失败'}) - $bTarget" -ForegroundColor $(if($bSuccess){'Green'}else{'Red'})

# 显示最新日志
if (Test-Path $logFile) {
  Write-Host "最新日志:" -ForegroundColor Cyan
  Get-Content -Path $logFile -Tail 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

if ($aSuccess -and $bSuccess) {
  Write-Host "✓ 所有测试通过！JSON自动同步功能正常运行" -ForegroundColor Green
} else {
  Write-Host "✗ 测试失败，请检查守护进程状态和日志" -ForegroundColor Red
}