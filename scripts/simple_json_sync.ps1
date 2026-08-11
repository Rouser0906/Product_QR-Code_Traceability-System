# 简化版JSON同步脚本 - 直接测试同步功能
param(
  [string]$TestMode = 'false'
)

try {
  $projectRoot = (Get-Location).Path
  $hsDir = Join-Path $projectRoot "cloud\demo_json_a"
  $zyDir = Join-Path $projectRoot "cloud\demo_json_b"
  $serverHsDir = "C:\inetpub\qr-system\companies\demo_json_a"
  $serverZyDir = "C:\inetpub\qr-system\companies\demo_json_b"
  
  # 创建目录
  New-Item -ItemType Directory -Force -Path $hsDir | Out-Null
  New-Item -ItemType Directory -Force -Path $zyDir | Out-Null
  New-Item -ItemType Directory -Force -Path $serverHsDir -ErrorAction SilentlyContinue | Out-Null
  New-Item -ItemType Directory -Force -Path $serverZyDir -ErrorAction SilentlyContinue | Out-Null
  
  Write-Host "简化版JSON同步脚本启动" -ForegroundColor Green
  Write-Host "监控: $hsDir -> $serverHsDir" -ForegroundColor Yellow
  Write-Host "监控: $zyDir -> $serverZyDir" -ForegroundColor Yellow
  
  if ($TestMode -eq 'true') {
    # 测试模式：检查现有文件并同步
    Write-Host "测试模式：检查现有文件..." -ForegroundColor Cyan
    
    Get-ChildItem -Path $hsDir -Filter "*.json" | ForEach-Object {
      $targetFile = Join-Path $serverHsDir $_.Name
      if (-not (Test-Path $targetFile)) {
        Copy-Item -Path $_.FullName -Destination $targetFile -Force
        Write-Host "同步: $($_.Name) -> HS服务器" -ForegroundColor Green
      }
    }
    
    Get-ChildItem -Path $zyDir -Filter "*.json" | ForEach-Object {
      $targetFile = Join-Path $serverZyDir $_.Name
      if (-not (Test-Path $targetFile)) {
        Copy-Item -Path $_.FullName -Destination $targetFile -Force
        Write-Host "同步: $($_.Name) -> ZY服务器" -ForegroundColor Green
      }
    }
    
    return
  }
  
  # 监控模式：实时监控文件变化
  $watcher1 = New-Object System.IO.FileSystemWatcher
  $watcher1.Path = $hsDir
  $watcher1.Filter = "*.json"
  $watcher1.NotifyFilter = [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::LastWrite
  
  $watcher2 = New-Object System.IO.FileSystemWatcher
  $watcher2.Path = $zyDir
  $watcher2.Filter = "*.json"
  $watcher2.NotifyFilter = [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::LastWrite
  
  $action = {
    param($sender, $e)
    try {
      Start-Sleep -Milliseconds 500  # 等待文件稳定
      $sourceFile = $e.FullPath
      $fileName = [System.IO.Path]::GetFileName($sourceFile)
      
      if ($sender.Path -like "*demo_json_a*") {
        $targetFile = Join-Path "C:\inetpub\qr-system\companies\demo_json_a" $fileName
      } else {
        $targetFile = Join-Path "C:\inetpub\qr-system\companies\demo_json_b" $fileName
      }
      
      if (Test-Path $sourceFile) {
        Copy-Item -Path $sourceFile -Destination $targetFile -Force
        Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 同步成功: $fileName" -ForegroundColor Green
      }
    } catch {
      Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 同步失败: $($_.Exception.Message)" -ForegroundColor Red
    }
  }
  
  Register-ObjectEvent -InputObject $watcher1 -EventName "Created" -Action $action | Out-Null
  Register-ObjectEvent -InputObject $watcher1 -EventName "Changed" -Action $action | Out-Null
  Register-ObjectEvent -InputObject $watcher2 -EventName "Created" -Action $action | Out-Null
  Register-ObjectEvent -InputObject $watcher2 -EventName "Changed" -Action $action | Out-Null
  
  $watcher1.EnableRaisingEvents = $true
  $watcher2.EnableRaisingEvents = $true
  
  Write-Host "文件监控已启动，按 Ctrl+C 停止..." -ForegroundColor Green
  
  while ($true) {
    Start-Sleep -Seconds 1
  }
  
} catch {
  Write-Host "错误: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
} finally {
  if ($watcher1) { $watcher1.Dispose() }
  if ($watcher2) { $watcher2.Dispose() }
}