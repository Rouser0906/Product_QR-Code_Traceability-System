# Simple JSON Monitor Loop - Direct Execution

# Configuration
$LocalHS = 'C:\Projects\Demo\cloud\demo_json_a'
$LocalZY = 'C:\Projects\Demo\cloud\demo_json_b'

# Define upload function directly
function Upload-JsonFile($localFile, $remoteDir) {
    try {
        $FtpHost = 'scan.example.com'
        $FtpPort = 21
        $Username = 'your_ftp_username'
        $Password = '[REDACTED-FTP-PASSWORD]'
        
        $fileName = Split-Path $localFile -Leaf
        $remoteUrl = "ftp://${FtpHost}:${FtpPort}${remoteDir}/${fileName}"
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 开始上传: $fileName" -ForegroundColor Yellow
        
        $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $req.UsePassive = $true
        $req.UseBinary = $true
        $req.Timeout = 30000
        
        $fileContent = [System.IO.File]::ReadAllBytes($localFile)
        $req.ContentLength = $fileContent.Length
        
        $stream = $req.GetRequestStream()
        $stream.Write($fileContent, 0, $fileContent.Length)
        $stream.Close()
        
        $response = $req.GetResponse()
        $response.Close()
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ 上传成功: $fileName" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✗ 上传失败: $fileName - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Tracking processed files
$processedFiles = @{}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] JSON监控程序已启动" -ForegroundColor Green
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 监控目录: $LocalHS" -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 监控目录: $LocalZY" -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 按 Ctrl+C 停止监控" -ForegroundColor Yellow
Write-Host ""

# Initial sync of existing files
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 执行初始同步..." -ForegroundColor Yellow

# Get current files to mark as processed (avoid re-uploading existing files)
if (Test-Path $LocalHS) {
    Get-ChildItem -Path $LocalHS -Filter "*.json" -File | ForEach-Object {
        $processedFiles[$_.FullName] = $_.LastWriteTime
    }
}
if (Test-Path $LocalZY) {
    Get-ChildItem -Path $LocalZY -Filter "*.json" -File | ForEach-Object {
        $processedFiles[$_.FullName] = $_.LastWriteTime
    }
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 开始监控新文件..." -ForegroundColor Green

# Main monitoring loop
while ($true) {
    try {
        $foundNewFile = $false
        
        # Check HS directory
        if (Test-Path $LocalHS) {
            $hsFiles = Get-ChildItem -Path $LocalHS -Filter "*.json" -File
            foreach ($file in $hsFiles) {
                if (-not $processedFiles.ContainsKey($file.FullName) -or $processedFiles[$file.FullName] -lt $file.LastWriteTime) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 发现新的HS文件: $($file.Name)" -ForegroundColor Yellow
                    
                    # Wait for file to be fully written
                    Start-Sleep -Seconds 2
                    
                    # Upload directly
                    $remoteDir = '/companies/demo_json_a'
                    Upload-JsonFile $file.FullName $remoteDir
                    
                    # Mark as processed
                    $processedFiles[$file.FullName] = $file.LastWriteTime
                    $foundNewFile = $true
                }
            }
        }
        
        # Check ZY directory
        if (Test-Path $LocalZY) {
            $zyFiles = Get-ChildItem -Path $LocalZY -Filter "*.json" -File
            foreach ($file in $zyFiles) {
                if (-not $processedFiles.ContainsKey($file.FullName) -or $processedFiles[$file.FullName] -lt $file.LastWriteTime) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 发现新的ZY文件: $($file.Name)" -ForegroundColor Yellow
                    
                    # Wait for file to be fully written
                    Start-Sleep -Seconds 2
                    
                    # Upload directly
                    $remoteDir = '/companies/demo_json_b'
                    Upload-JsonFile $file.FullName $remoteDir
                    
                    # Mark as processed
                    $processedFiles[$file.FullName] = $file.LastWriteTime
                    $foundNewFile = $true
                }
            }
        }
        
        if (-not $foundNewFile) {
            # Show heartbeat every 60 seconds
            if ((Get-Date).Second -eq 0) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 监控中... (已处理 $($processedFiles.Count) 个文件)" -ForegroundColor DarkGray
            }
        }
        
        # Check every 5 seconds
        Start-Sleep -Seconds 5
        
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 监控错误: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}