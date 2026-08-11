# Install JSON File Sync Service for Windows
# Requires Administrator privileges

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart
)

$ServiceName = "QRJsonAutoSync"
$ServiceDisplayName = "QR JSON Auto Sync Service"
$ServiceDescription = "Automatically sync local cloud JSON files to remote FTP server"
$ScriptPath = Join-Path $PSScriptRoot "ultimate_sync_guardian.ps1"
$ServicePath = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`""

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-SyncService {
    Write-Host "Installing JSON sync service..." -ForegroundColor Yellow
    
    try {
        # Use sc.exe to create service
        $result = & sc.exe create $ServiceName binPath= $ServicePath DisplayName= $ServiceDisplayName start= auto
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service created successfully" -ForegroundColor Green
            
            # Set service description
            & sc.exe description $ServiceName $ServiceDescription
            
            # Set service recovery options (auto restart on failure)
            & sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/10000/restart/30000
            
            Write-Host "Service configuration completed" -ForegroundColor Green
            
            # Start service
            Start-SyncService
            
        } else {
            Write-Host "Failed to create service" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error installing service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Uninstall-SyncService {
    Write-Host "Uninstalling JSON sync service..." -ForegroundColor Yellow
    
    try {
        # Stop service first
        Stop-SyncService
        
        # Delete service
        $result = & sc.exe delete $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service uninstalled successfully" -ForegroundColor Green
        } else {
            Write-Host "Failed to uninstall service" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error uninstalling service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-SyncService {
    Write-Host "Starting JSON sync service..." -ForegroundColor Yellow
    
    try {
        $result = & sc.exe start $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service started successfully" -ForegroundColor Green
        } else {
            Write-Host "Failed to start service" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error starting service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-SyncService {
    Write-Host "Stopping JSON sync service..." -ForegroundColor Yellow
    
    try {
        $result = & sc.exe stop $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service stopped successfully" -ForegroundColor Green
        } else {
            Write-Host "Service may already be stopped" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Error stopping service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Get-ServiceStatus {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            $statusColor = if($service.Status -eq 'Running') {'Green'} else {'Yellow'}
            Write-Host "Service Status: $($service.Status)" -ForegroundColor $statusColor
            Write-Host "Startup Type: $($service.StartType)" -ForegroundColor Cyan
            return $service
        } else {
            Write-Host "Service not installed" -ForegroundColor Gray
            return $null
        }
    } catch {
        Write-Host "Cannot get service status: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Main program logic
Write-Host "======== QR JSON Auto Sync Service Manager ========" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Administrator)) {
    Write-Host "Administrator privileges required! Please run as administrator." -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "Cannot find sync script: $ScriptPath" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

Write-Host "Current Status:" -ForegroundColor White
$currentService = Get-ServiceStatus
Write-Host ""

if ($Install) {
    if ($currentService) {
        Write-Host "Service already exists. Reinstall? (y/N): " -ForegroundColor Yellow -NoNewline
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
        Write-Host "Confirm uninstall service? (y/N): " -ForegroundColor Yellow -NoNewline
        $confirm = Read-Host
        if ($confirm -eq 'y' -or $confirm -eq 'Y') {
            Uninstall-SyncService
        }
    } else {
        Write-Host "Service not installed" -ForegroundColor Gray
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
    # Interactive menu
    Write-Host "Please select an option:" -ForegroundColor White
    Write-Host "1. Install service" -ForegroundColor Green
    Write-Host "2. Uninstall service" -ForegroundColor Red
    Write-Host "3. Start service" -ForegroundColor Cyan
    Write-Host "4. Stop service" -ForegroundColor Yellow
    Write-Host "5. Restart service" -ForegroundColor Magenta
    Write-Host "6. Check status" -ForegroundColor Gray
    Write-Host "0. Exit" -ForegroundColor White
    Write-Host ""
    
    do {
        Write-Host "Enter option (0-6): " -ForegroundColor White -NoNewline
        $choice = Read-Host
        
        switch ($choice) {
            "1" { 
                if ($currentService) {
                    Write-Host "Service already exists. Reinstall? (y/N): " -ForegroundColor Yellow -NoNewline
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
                    Write-Host "Service not installed" -ForegroundColor Gray
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
                Write-Host "Exiting..." -ForegroundColor Gray
                break 
            }
            default { 
                Write-Host "Invalid option, please try again" -ForegroundColor Red 
                continue
            }
        }
        
        if ($choice -ne "0" -and $choice -ne "6") {
            Write-Host ""
            Write-Host "Operation completed. Current status:" -ForegroundColor White
            Get-ServiceStatus | Out-Null
        }
        
    } while ($choice -ne "0")
}

Write-Host ""
Write-Host "Operation completed!" -ForegroundColor Green