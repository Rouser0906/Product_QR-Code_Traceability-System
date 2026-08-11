# 发布前自动清理脚本
# 此脚本会删除所有敏感数据和临时文件，准备项目发布

param(
    [switch]$DryRun,  # 只显示将要删除的文件，不实际删除
    [switch]$KeepLegacy  # 保留 legacy_disabled 目录
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  项目发布前清理脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "【模拟模式】只显示将要删除的文件，不会实际删除" -ForegroundColor Yellow
    Write-Host ""
}

$deletedCount = 0
$errorCount = 0

function Remove-ItemSafely {
    param(
        [string]$Path,
        [string]$Description,
        [switch]$Recurse
    )
    
    if (Test-Path $Path) {
        if ($DryRun) {
            Write-Host "  [模拟] 将删除: $Path" -ForegroundColor Gray
        } else {
            try {
                if ($Recurse) {
                    Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
                } else {
                    Remove-Item -Path $Path -Force -ErrorAction Stop
                }
                Write-Host "  ✓ 已删除: $Description" -ForegroundColor Green
                $script:deletedCount++
            } catch {
                Write-Host "  ✗ 删除失败: $Description - $($_.Exception.Message)" -ForegroundColor Red
                $script:errorCount++
            }
        }
    } else {
        Write-Host "  - 不存在: $Description (跳过)" -ForegroundColor Gray
    }
}

# 1. 删除数据库文件
Write-Host "1. 清理数据库文件..." -ForegroundColor Cyan
Remove-ItemSafely "qr_system.db" "主数据库文件"
Remove-ItemSafely "qr_system_backup.db" "备份数据库文件"
Remove-ItemSafely "qr_system.db-shm" "数据库共享内存文件"
Remove-ItemSafely "qr_system.db-wal" "数据库WAL文件"
Write-Host ""

# 2. 删除临时文件
Write-Host "2. 清理临时文件..." -ForegroundColor Cyan
Get-ChildItem -Filter "tmp_dev_*" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely $_.FullName "临时文件: $($_.Name)" -Recurse
}
Get-ChildItem -Path "scripts" -Filter "tmp_dev_*" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely $_.FullName "脚本临时文件: $($_.Name)" -Recurse
}
Remove-ItemSafely "temp_error.log" "临时错误日志"
Remove-ItemSafely "temp_output.log" "临时输出日志"
Write-Host ""

# 3. 删除敏感配置文件
Write-Host "3. 清理敏感配置文件..." -ForegroundColor Cyan
Remove-ItemSafely "config/ftp_config.json" "FTP配置文件"
Remove-ItemSafely "auto_sync/config.json" "自动同步配置"
Remove-ItemSafely "auto_sync/enhanced_config.json" "增强配置"
Remove-ItemSafely "api/db_config.php" "数据库配置(PHP)"
Remove-ItemSafely "api/api_config.php" "API配置(PHP)"
Remove-ItemSafely "scripts/ftp_credentials.ps1" "FTP凭据脚本"
Write-Host ""

# 4. 清理备份目录
Write-Host "4. 清理备份和导出目录..." -ForegroundColor Cyan
if (Test-Path "backups") {
    Get-ChildItem "backups/*" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "备份: $($_.Name)" -Recurse
    }
}
if (Test-Path "exports") {
    Get-ChildItem "exports/*" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "导出: $($_.Name)" -Recurse
    }
}
if (Test-Path "imports") {
    Get-ChildItem "imports/*" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "导入: $($_.Name)" -Recurse
    }
}
Write-Host ""

# 5. 清理云数据目录
Write-Host "5. 清理云数据JSON文件..." -ForegroundColor Cyan
if (Test-Path "cloud/demo_json_a") {
    Get-ChildItem "cloud/demo_json_a/*.json" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "HS JSON: $($_.Name)"
    }
}
if (Test-Path "cloud/demo_json_b") {
    Get-ChildItem "cloud/demo_json_b/*.json" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "ZY JSON: $($_.Name)"
    }
}
Write-Host ""

# 6. 清理日志文件
Write-Host "6. 清理日志文件..." -ForegroundColor Cyan
if (Test-Path "auto_sync/logs") {
    Get-ChildItem "auto_sync/logs/*.log" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "同步日志: $($_.Name)"
    }
}
if (Test-Path "logs") {
    Get-ChildItem "logs/*.log" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "系统日志: $($_.Name)"
    }
}
Write-Host ""

# 7. 清理缓存目录
Write-Host "7. 清理缓存文件..." -ForegroundColor Cyan
if (Test-Path "cache") {
    Get-ChildItem "cache/*" -Exclude .gitkeep -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "缓存: $($_.Name)" -Recurse
    }
}
Write-Host ""

# 8. 清理Python缓存
Write-Host "8. 清理Python缓存..." -ForegroundColor Cyan
Get-ChildItem -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely $_.FullName "Python缓存: $($_.FullName)" -Recurse
}
Get-ChildItem -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely $_.FullName "Python字节码: $($_.Name)"
}
Write-Host ""

# 9. 清理构建产物
Write-Host "9. 清理构建产物..." -ForegroundColor Cyan
Remove-ItemSafely "build" "构建目录" -Recurse
Remove-ItemSafely "dist" "分发目录" -Recurse
Remove-ItemSafely "out" "输出目录" -Recurse
Write-Host ""

# 10. 可选：删除遗留代码
if (-not $KeepLegacy) {
    Write-Host "10. 清理遗留代码目录..." -ForegroundColor Cyan
    Remove-ItemSafely "legacy_disabled" "遗留代码目录" -Recurse
    Write-Host ""
} else {
    Write-Host "10. 保留遗留代码目录 (使用了 -KeepLegacy 参数)" -ForegroundColor Yellow
    Write-Host ""
}

# 11. 清理QR生成的文件
Write-Host "11. 清理生成的QR码文件..." -ForegroundColor Cyan
if (Test-Path "assets/qr") {
    Get-ChildItem "assets/qr/*.png" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "QR码图片: $($_.Name)"
    }
}
if (Test-Path "out/qr") {
    Get-ChildItem "out/qr/*.png" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-ItemSafely $_.FullName "QR码输出: $($_.Name)"
    }
}
Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "清理完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "这是模拟运行。要实际执行清理，请运行:" -ForegroundColor Yellow
    Write-Host "  .\cleanup_for_publish.ps1" -ForegroundColor White
} else {
    Write-Host "已删除文件数: $deletedCount" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "删除失败数: $errorCount" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "  1. 检查 PRE_PUBLISH_CHECKLIST.md 完成所有检查项" -ForegroundColor White
Write-Host "  2. 运行: git status  (确认没有敏感文件)" -ForegroundColor White
Write-Host "  3. 运行: git add .  (添加清理后的文件)" -ForegroundColor White
Write-Host "  4. 运行: git commit -m '清理敏感信息，准备发布'" -ForegroundColor White
Write-Host "  5. 推送到 Atlassian 仓库" -ForegroundColor White
Write-Host ""
Write-Host "提示: 使用 -DryRun 参数可以预览将要删除的文件" -ForegroundColor Gray
Write-Host "提示: 使用 -KeepLegacy 参数可以保留遗留代码目录" -ForegroundColor Gray
Write-Host ""
