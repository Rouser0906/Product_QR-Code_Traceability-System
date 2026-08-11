# 快速同步状态检查工具

param(
    [switch]$ShowDetails,
    [switch]$ShowLogs,
    [switch]$TestUpload
)

$LocalHS = 'C:\Projects\Demo\cloud\demo_json_a'
$LocalZY = 'C:\Projects\Demo\cloud\demo_json_b'
$LogFile = Join-Path $PSScriptRoot '..\auto_sync\logs\ultimate_sync.log'
$StatusFile = Join-Path $PSScriptRoot '..\auto_sync\logs\sync_status.json'

function Get-DirectoryInfo($path, $type) {
    if (Test-Path $path) {
        $files = Get-ChildItem -Path $path -Filter "*.json" -File
        return @{
            Path = $path
            Type = $type
            Exists = $true
            FileCount = $files.Count
            Files = $files
            LastModified = if($files) { ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime } else { $null }
        }
    } else {
        return @{
            Path = $path
            Type = $type
            Exists = $false
            FileCount = 0
            Files = @()
            LastModified = $null
        }
    }
}

function Show-SyncStatus {
    Write-Host "======== JSON文件同步状态检查 ========" -ForegroundColor Cyan
    Write-Host ""
    
    # 检查服务状态
    try {
        $service = Get-Service -Name "QRJsonAutoSync" -ErrorAction SilentlyContinue
        if ($service) {
            $statusColor = if($service.Status -eq 'Running') {'Green'} else {'Red'}
            Write-Host "🔧 同步服务状态: " -NoNewline
            Write-Host "$($service.Status)" -ForegroundColor $statusColor
        } else {
            Write-Host "⚠️  同步服务: " -NoNewline
            Write-Host "未安装" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ 无法检查服务状态" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 检查本地目录
    $hsInfo = Get-DirectoryInfo $LocalHS "HS"
    $zyInfo = Get-DirectoryInfo $LocalZY "ZY"
    
    Write-Host "📁 本地目录状态:" -ForegroundColor White
    
    foreach ($info in @($hsInfo, $zyInfo)) {
        $statusIcon = if($info.Exists) {"✅"} else {"❌"}
        $countColor = if($info.FileCount -gt 0) {"Green"} else {"Gray"}
        
        Write-Host "   $statusIcon $($info.Type) 目录: " -NoNewline
        Write-Host "$($info.FileCount) 个文件" -ForegroundColor $countColor
        
        if ($ShowDetails -and $info.FileCount -gt 0) {
            Write-Host "      路径: $($info.Path)" -ForegroundColor Gray
            if ($info.LastModified) {
                Write-Host "      最新文件: $($info.LastModified)" -ForegroundColor Gray
            }
            
            if ($info.FileCount -le 5) {
                foreach ($file in $info.Files) {
                    Write-Host "        - $($file.Name) ($($file.Length) bytes)" -ForegroundColor DarkGray
                }
            } else {
                $latest = $info.Files | Sort-Object LastWriteTime -Descending | Select-Object -First 3
                foreach ($file in $latest) {
                    Write-Host "        - $($file.Name) ($($file.Length) bytes)" -ForegroundColor DarkGray
                }
                Write-Host "        ... 和其他 $($info.FileCount - 3) 个文件" -ForegroundColor DarkGray
            }
        }
    }
    
    Write-Host ""
    
    # 检查同步状态文件
    if (Test-Path $StatusFile) {
        try {
            $status = Get-Content $StatusFile -Raw | ConvertFrom-Json
            $lastRun = [DateTime]$status.LastRun
            $timeDiff = (Get-Date) - $lastRun
            
            Write-Host "📊 上次同步: " -NoNewline
            if ($timeDiff.TotalMinutes -lt 5) {
                Write-Host "$($status.LastRun) (刚刚)" -ForegroundColor Green
            } elseif ($timeDiff.TotalHours -lt 1) {
                Write-Host "$($status.LastRun) ($([math]::Round($timeDiff.TotalMinutes))分钟前)" -ForegroundColor Yellow
            } else {
                Write-Host "$($status.LastRun) ($([math]::Round($timeDiff.TotalHours))小时前)" -ForegroundColor Red
            }
            
            Write-Host "📈 累计上传: " -NoNewline
            Write-Host "$($status.TotalUploaded) 个文件" -ForegroundColor Cyan
            
        } catch {
            Write-Host "⚠️  无法读取同步状态文件" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  同步状态文件不存在" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

function Show-RecentLogs {
    Write-Host "======== 最近的同步日志 ========" -ForegroundColor Cyan
    
    if (Test-Path $LogFile) {
        try {
            $lines = Get-Content $LogFile -Tail 20 -Encoding UTF8
            foreach ($line in $lines) {
                $color = "White"
                if ($line -match '\[ERROR\]') { $color = "Red" }
                elseif ($line -match '\[WARN\]') { $color = "Yellow" } 
                elseif ($line -match '\[SUCCESS\]') { $color = "Green" }
                elseif ($line -match '\[INFO\]') { $color = "Cyan" }
                
                Write-Host $line -ForegroundColor $color
            }
        } catch {
            Write-Host "无法读取日志文件: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "日志文件不存在: $LogFile" -ForegroundColor Yellow
    }
}

function Test-UploadFunction {
    Write-Host "======== 测试上传功能 ========" -ForegroundColor Cyan
    
    # 创建测试文件
    $testContent = @{
        test = $true
        timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        computer = $env:COMPUTERNAME
    } | ConvertTo-Json
    
    $testFile = Join-Path $LocalHS "TEST-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    
    try {
        $testContent | Out-File -FilePath $testFile -Encoding UTF8
        Write-Host "✅ 创建测试文件: $([System.IO.Path]::GetFileName($testFile))" -ForegroundColor Green
        Write-Host "📁 等待自动同步..." -ForegroundColor Yellow
        Write-Host "   (请观察日志文件中的上传记录)" -ForegroundColor Gray
        
        # 等待一段时间后删除测试文件
        Start-Sleep -Seconds 5
        if (Test-Path $testFile) {
            Remove-Item $testFile -Force
            Write-Host "🗑️  清理测试文件" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "❌ 测试失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 主程序
if ($ShowLogs) {
    Show-RecentLogs
} elseif ($TestUpload) {
    Test-UploadFunction
} else {
    Show-SyncStatus
    
    if ($ShowDetails) {
        Write-Host ""
        Show-RecentLogs
    }
}

Write-Host ""
Write-Host "💡 提示: 使用以下参数获取更多信息:" -ForegroundColor Gray
Write-Host "   -ShowDetails  显示详细信息" -ForegroundColor Gray
Write-Host "   -ShowLogs     显示最近日志" -ForegroundColor Gray  
Write-Host "   -TestUpload   测试上传功能" -ForegroundColor Gray