# 安装JSON文件同步服务为Windows服务
# 需要管理员权限运行

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart
)

$ServiceName = "QRJsonAutoSync"
$ServiceDisplayName = "QR JSON文件自动同步服务"
$ServiceDescription = "自动同步本地cloud目录中的JSON文件到远程FTP服务器"
$ScriptPath = Join-Path $PSScriptRoot "ultimate_sync_guardian.ps1"
$ServicePath = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`""

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-SyncService {
    Write-Host "安装JSON同步服务..." -ForegroundColor Yellow
    
    try {
        # 使用sc.exe创建服务
        $result = & sc.exe create $ServiceName binPath= $ServicePath DisplayName= $ServiceDisplayName start= auto
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 服务创建成功" -ForegroundColor Green
            
            # 设置服务描述
            & sc.exe description $ServiceName $ServiceDescription
            
            # 设置服务恢复选项（失败后自动重启）
            & sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/10000/restart/30000
            
            Write-Host "✓ 服务配置完成" -ForegroundColor Green
            
            # 启动服务
            Start-SyncService
            
        } else {
            Write-Host "✗ 服务创建失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ 安装服务时发生错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Uninstall-SyncService {
    Write-Host "卸载JSON同步服务..." -ForegroundColor Yellow
    
    try {
        # 先停止服务
        Stop-SyncService
        
        # 删除服务
        $result = & sc.exe delete $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 服务卸载成功" -ForegroundColor Green
        } else {
            Write-Host "✗ 服务卸载失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ 卸载服务时发生错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-SyncService {
    Write-Host "启动JSON同步服务..." -ForegroundColor Yellow
    
    try {
        $result = & sc.exe start $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 服务启动成功" -ForegroundColor Green
        } else {
            Write-Host "✗ 服务启动失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ 启动服务时发生错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-SyncService {
    Write-Host "停止JSON同步服务..." -ForegroundColor Yellow
    
    try {
        $result = & sc.exe stop $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 服务停止成功" -ForegroundColor Green
        } else {
            Write-Host "⚠ 服务可能已经停止" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ 停止服务时发生错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Get-ServiceStatus {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "服务状态: $($service.Status)" -ForegroundColor $(if($service.Status -eq 'Running'){'Green'}else{'Yellow'})
            Write-Host "启动类型: $($service.StartType)" -ForegroundColor Cyan
            return $service
        } else {
            Write-Host "服务未安装" -ForegroundColor Gray
            return $null
        }
    } catch {
        Write-Host "无法获取服务状态: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 主程序逻辑
Write-Host "======== QR JSON自动同步服务管理器 ========" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Administrator)) {
    Write-Host "✗ 需要管理员权限！请以管理员身份运行此脚本。" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "✗ 找不到同步脚本: $ScriptPath" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "当前状态:" -ForegroundColor White
$currentService = Get-ServiceStatus
Write-Host ""

if ($Install) {
    if ($currentService) {
        Write-Host "服务已存在，是否要重新安装？(y/N): " -ForegroundColor Yellow -NoNewline
        $confirm = Read-Host
        if ($confirm -eq 'y' -or $confirm -eq 'Y') {
            Uninstall-SyncService
            Start-Sleep -Seconds 2
            Install-SyncService
        }
    } else {
        Install-SyncService
    }
} elseif ($Uninstall) {
    if ($currentService) {
        Write-Host "确认卸载服务？(y/N): " -ForegroundColor Yellow -NoNewline
        $confirm = Read-Host
        if ($confirm -eq 'y' -or $confirm -eq 'Y') {
            Uninstall-SyncService
        }
    } else {
        Write-Host "服务未安装" -ForegroundColor Gray
    }
} elseif ($Start) {
    Start-SyncService
} elseif ($Stop) {
    Stop-SyncService
} elseif ($Restart) {
    Stop-SyncService
    Start-Sleep -Seconds 3
    Start-SyncService
} else {
    # 交互式菜单
    Write-Host "请选择操作:" -ForegroundColor White
    Write-Host "1. 安装服务" -ForegroundColor Green
    Write-Host "2. 卸载服务" -ForegroundColor Red
    Write-Host "3. 启动服务" -ForegroundColor Cyan
    Write-Host "4. 停止服务" -ForegroundColor Yellow
    Write-Host "5. 重启服务" -ForegroundColor Magenta
    Write-Host "6. 查看状态" -ForegroundColor Gray
    Write-Host "0. 退出" -ForegroundColor White
    Write-Host ""
    
    do {
        Write-Host "请输入选项 (0-6): " -ForegroundColor White -NoNewline
        $choice = Read-Host
        
        switch ($choice) {
            "1" { 
                if ($currentService) {
                    Write-Host "服务已存在，是否要重新安装？(y/N): " -ForegroundColor Yellow -NoNewline
                    $confirm = Read-Host
                    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
                        Uninstall-SyncService
                        Start-Sleep -Seconds 2
                        Install-SyncService
                    }
                } else {
                    Install-SyncService
                }
                break 
            }
            "2" { 
                if ($currentService) {
                    Uninstall-SyncService 
                } else {
                    Write-Host "服务未安装" -ForegroundColor Gray
                }
                break 
            }
            "3" { Start-SyncService; break }
            "4" { Stop-SyncService; break }
            "5" { 
                Stop-SyncService
                Start-Sleep -Seconds 3
                Start-SyncService
                break 
            }
            "6" { 
                Write-Host ""
                Get-ServiceStatus | Out-Null
                break 
            }
            "0" { 
                Write-Host "退出..." -ForegroundColor Gray
                break 
            }
            default { 
                Write-Host "无效选项，请重新输入" -ForegroundColor Red 
                continue
            }
        }
        
        if ($choice -ne "0" -and $choice -ne "6") {
            Write-Host ""
            Write-Host "操作完成，当前状态:" -ForegroundColor White
            Get-ServiceStatus | Out-Null
        }
        
    } while ($choice -ne "0")
}

Write-Host ""
Write-Host "操作完成！" -ForegroundColor Green