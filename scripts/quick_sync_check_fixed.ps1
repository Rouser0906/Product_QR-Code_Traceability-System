# Quick Sync Status Check Tool

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
    Write-Host "======== JSON File Sync Status Check ========" -ForegroundColor Cyan
    Write-Host ""
    
    # Check service status
    try {
        $service = Get-Service -Name "QRJsonAutoSync" -ErrorAction SilentlyContinue
        if ($service) {
            $statusColor = if($service.Status -eq 'Running') {'Green'} else {'Red'}
            Write-Host "Service Status: " -NoNewline
            Write-Host "$($service.Status)" -ForegroundColor $statusColor
        } else {
            Write-Host "Sync Service: " -NoNewline
            Write-Host "Not Installed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Cannot check service status" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Check local directories
    $hsInfo = Get-DirectoryInfo $LocalHS "HS"
    $zyInfo = Get-DirectoryInfo $LocalZY "ZY"
    
    Write-Host "Local Directory Status:" -ForegroundColor White
    
    foreach ($info in @($hsInfo, $zyInfo)) {
        $statusIcon = if($info.Exists) {"[OK]"} else {"[ERROR]"}
        $countColor = if($info.FileCount -gt 0) {"Green"} else {"Gray"}
        
        Write-Host "   $statusIcon $($info.Type) Directory: " -NoNewline
        Write-Host "$($info.FileCount) files" -ForegroundColor $countColor
        
        if ($ShowDetails -and $info.FileCount -gt 0) {
            Write-Host "      Path: $($info.Path)" -ForegroundColor Gray
            if ($info.LastModified) {
                Write-Host "      Latest file: $($info.LastModified)" -ForegroundColor Gray
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
                Write-Host "        ... and $($info.FileCount - 3) more files" -ForegroundColor DarkGray
            }
        }
    }
    
    Write-Host ""
    
    # Check sync status file
    if (Test-Path $StatusFile) {
        try {
            $status = Get-Content $StatusFile -Raw | ConvertFrom-Json
            $lastRun = [DateTime]$status.LastRun
            $timeDiff = (Get-Date) - $lastRun
            
            Write-Host "Last Sync: " -NoNewline
            if ($timeDiff.TotalMinutes -lt 5) {
                Write-Host "$($status.LastRun) (just now)" -ForegroundColor Green
            } elseif ($timeDiff.TotalHours -lt 1) {
                Write-Host "$($status.LastRun) ($([math]::Round($timeDiff.TotalMinutes)) min ago)" -ForegroundColor Yellow
            } else {
                Write-Host "$($status.LastRun) ($([math]::Round($timeDiff.TotalHours)) hours ago)" -ForegroundColor Red
            }
            
            Write-Host "Total Uploaded: " -NoNewline
            Write-Host "$($status.TotalUploaded) files" -ForegroundColor Cyan
            
        } catch {
            Write-Host "Cannot read sync status file" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Sync status file does not exist" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

function Show-RecentLogs {
    Write-Host "======== Recent Sync Logs ========" -ForegroundColor Cyan
    
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
            Write-Host "Cannot read log file: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Log file does not exist: $LogFile" -ForegroundColor Yellow
    }
}

function Test-UploadFunction {
    Write-Host "======== Test Upload Function ========" -ForegroundColor Cyan
    
    # Create test file
    $testContent = @{
        test = $true
        timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        computer = $env:COMPUTERNAME
    } | ConvertTo-Json
    
    $testFile = Join-Path $LocalHS "TEST-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    
    try {
        # Ensure directory exists
        if (-not (Test-Path $LocalHS)) {
            New-Item -ItemType Directory -Force -Path $LocalHS
        }
        
        $testContent | Out-File -FilePath $testFile -Encoding UTF8
        Write-Host "Test file created: $([System.IO.Path]::GetFileName($testFile))" -ForegroundColor Green
        Write-Host "Waiting for auto sync..." -ForegroundColor Yellow
        Write-Host "   (Please check log file for upload records)" -ForegroundColor Gray
        
        # Wait and cleanup test file
        Start-Sleep -Seconds 5
        if (Test-Path $testFile) {
            Remove-Item $testFile -Force
            Write-Host "Test file cleaned up" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "Test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main program
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
Write-Host "Tips: Use these parameters for more info:" -ForegroundColor Gray
Write-Host "   -ShowDetails  Show detailed information" -ForegroundColor Gray
Write-Host "   -ShowLogs     Show recent logs" -ForegroundColor Gray  
Write-Host "   -TestUpload   Test upload function" -ForegroundColor Gray