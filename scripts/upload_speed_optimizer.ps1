#!/usr/bin/env powershell
# 上传速度优化器 - 专门优化单个文件的上传速度
param(
    [string]$TestFile = "",
    [switch]$Benchmark = $false,
    [switch]$OptimizeSettings = $false,
    [switch]$NetworkTest = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

function Write-Log($msg, $level = "INFO") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $color = switch($level) {
        "ERROR" { "Red" }; "WARN" { "Yellow" }; "SUCCESS" { "Green" }
        "PERF" { "Magenta" }; default { "Cyan" }
    }
    Write-Host "$ts [$level] $msg" -ForegroundColor $color
}

function Test-NetworkLatency {
    Write-Log "测试网络延迟和带宽..." "INFO"
    
    try {
        # Ping测试
        $pingResult = Test-NetConnection -ComputerName "scan.example.com" -Port 21 -InformationLevel Detailed
        if ($pingResult.PingSucceeded) {
            Write-Log "Ping延迟: $($pingResult.PingReplyDetails.RoundtripTime)ms" "SUCCESS"
        } else {
            Write-Log "Ping测试失败" "ERROR"
        }
        
        # FTP连接速度测试
        $connectionTime = Measure-Command {
            try {
                $uri = "ftp://scan.example.com:21"
                $req = [System.Net.FtpWebRequest]::Create($uri)
                $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
                $req.Credentials = New-Object System.Net.NetworkCredential("your_ftp_username", "[REDACTED-FTP-PASSWORD]")
                $req.UsePassive = $true
                $req.Proxy = $null
                $resp = $req.GetResponse()
                $resp.Close()
            } catch {}
        }
        
        Write-Log "FTP连接时间: $($connectionTime.TotalMilliseconds)ms" "PERF"
        
        return @{
            PingTime = if($pingResult.PingSucceeded) { $pingResult.PingReplyDetails.RoundtripTime } else { 0 }
            ConnectionTime = $connectionTime.TotalMilliseconds
        }
    } catch {
        Write-Log "网络测试失败: $($_.Exception.Message)" "ERROR"
        return @{ PingTime = 0; ConnectionTime = 0 }
    }
}

function Test-UploadMethods {
    param([string]$TestFilePath)
    
    if (-not (Test-Path $TestFilePath)) {
        Write-Log "测试文件不存在: $TestFilePath" "ERROR"
        return
    }
    
    $fileSize = (Get-Item $TestFilePath).Length
    Write-Log "开始上传方法基准测试，文件大小: $fileSize 字节" "INFO"
    
    $methods = @(
        @{ Name = "标准方法"; UsePassive = $true; Timeout = 30000; BufferSize = 0 },
        @{ Name = "主动模式"; UsePassive = $false; Timeout = 30000; BufferSize = 0 },
        @{ Name = "长超时"; UsePassive = $true; Timeout = 60000; BufferSize = 0 },
        @{ Name = "短超时"; UsePassive = $true; Timeout = 10000; BufferSize = 0 }
    )
    
    $results = @()
    
    foreach ($method in $methods) {
        Write-Log "测试方法: $($method.Name)" "INFO"
        
        $uploadTime = Measure-Command {
            try {
                $uri = "ftp://scan.example.com:21/companies/demo_json_a/speed_test_$(Get-Date -Format 'yyyyMMddHHmmss').json"
                $req = [System.Net.FtpWebRequest]::Create($uri)
                $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
                $req.Credentials = New-Object System.Net.NetworkCredential("your_ftp_username", "[REDACTED-FTP-PASSWORD]")
                $req.UseBinary = $true
                $req.UsePassive = $method.UsePassive
                $req.Timeout = $method.Timeout
                $req.Proxy = $null
                
                $bytes = [System.IO.File]::ReadAllBytes($TestFilePath)
                $req.ContentLength = $bytes.Length
                
                $stream = $req.GetRequestStream()
                $stream.Write($bytes, 0, $bytes.Length)
                $stream.Close()
                
                $resp = $req.GetResponse()
                $resp.Close()
                
                $success = $true
            } catch {
                Write-Log "上传失败: $($_.Exception.Message)" "WARN"
                $success = $false
            }
        }
        
        if ($success) {
            $speedKBps = [math]::Round(($fileSize / 1024) / ($uploadTime.TotalSeconds), 2)
            Write-Log "$($method.Name) - 上传成功: $($uploadTime.TotalMilliseconds)ms, ${speedKBps}KB/s" "SUCCESS"
            
            $results += @{
                Method = $method.Name
                Time = $uploadTime.TotalMilliseconds
                Speed = $speedKBps
                Success = $true
            }
        } else {
            $results += @{
                Method = $method.Name
                Time = 0
                Speed = 0
                Success = $false
            }
        }
        
        Start-Sleep -Seconds 2  # 避免过于频繁的请求
    }
    
    Write-Log "=== 基准测试结果 ===" "PERF"
    $results | Sort-Object Speed -Descending | ForEach-Object {
        if ($_.Success) {
            Write-Log "$($_.Method): $($_.Time)ms, $($_.Speed)KB/s" "PERF"
        } else {
            Write-Log "$($_.Method): 失败" "ERROR"
        }
    }
    
    return $results
}

function Optimize-FtpSettings {
    Write-Log "优化FTP设置..." "INFO"
    
    # 创建优化的配置文件
    $optimizedConfig = @{
        connection = @{
            timeout_ms = 15000
            use_passive = $true
            buffer_size = 65536
            keep_alive = $true
        }
        upload = @{
            chunk_size = 32768
            parallel_streams = 1
            verify_upload = $false
            retry_attempts = 3
            retry_delay_ms = 500
        }
        performance = @{
            tcp_no_delay = $true
            socket_send_buffer = 131072
            socket_recv_buffer = 131072
        }
    }
    
    $configPath = Join-Path $ProjectRoot "auto_sync\optimized_ftp_config.json"
    $optimizedConfig | ConvertTo-Json -Depth 3 | Out-File -FilePath $configPath -Encoding utf8
    
    Write-Log "优化配置已保存到: $configPath" "SUCCESS"
    
    # 创建优化版上传函数
    $optimizedUploadScript = @"
function Invoke-OptimizedUpload {
    param([string]`$LocalPath, [string]`$RemotePath)
    
    try {
        # 使用优化的设置
        `$uri = "ftp://scan.example.com:21`$RemotePath"
        `$req = [System.Net.FtpWebRequest]::Create(`$uri)
        `$req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        `$req.Credentials = New-Object System.Net.NetworkCredential("your_ftp_username", "[REDACTED-FTP-PASSWORD]")
        `$req.UseBinary = `$true
        `$req.UsePassive = `$true
        `$req.Timeout = 15000
        `$req.ReadWriteTimeout = 30000
        `$req.Proxy = `$null
        
        # 启用KeepAlive
        `$req.KeepAlive = `$true
        
        # 优化传输
        `$bytes = [System.IO.File]::ReadAllBytes(`$LocalPath)
        `$req.ContentLength = `$bytes.Length
        
        `$stream = `$req.GetRequestStream()
        
        # 分块上传以提高效率
        `$chunkSize = 32768
        `$offset = 0
        while (`$offset -lt `$bytes.Length) {
            `$remainingBytes = `$bytes.Length - `$offset
            `$currentChunkSize = [Math]::Min(`$chunkSize, `$remainingBytes)
            `$stream.Write(`$bytes, `$offset, `$currentChunkSize)
            `$offset += `$currentChunkSize
        }
        
        `$stream.Close()
        `$resp = `$req.GetResponse()
        `$resp.Close()
        
        return `$true
    } catch {
        Write-Host "上传失败: `$(`$_.Exception.Message)" -ForegroundColor Red
        return `$false
    }
}
"@
    
    $optimizedScriptPath = Join-Path $ProjectRoot "scripts\optimized_upload_functions.ps1"
    $optimizedUploadScript | Out-File -FilePath $optimizedScriptPath -Encoding utf8
    
    Write-Log "优化上传函数已保存到: $optimizedScriptPath" "SUCCESS"
}

function Create-TestFile {
    $testDir = Join-Path $ProjectRoot "cloud\demo_json_a"
    if (-not (Test-Path $testDir)) {
        New-Item -ItemType Directory -Force -Path $testDir | Out-Null
    }
    
    $testFile = Join-Path $testDir "SPEED_TEST_$(Get-Date -Format 'yyyyMMddHHmmss').json"
    
    # 创建一个合适大小的测试文件
    $testData = @{
        test_id = "SPEED_TEST_$(Get-Date -Format 'yyyyMMddHHmmssff')"
        timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
        data = "A" * 1024  # 1KB的数据
        performance_test = $true
        file_size_kb = 2
    }
    
    $testData | ConvertTo-Json -Depth 3 | Out-File -FilePath $testFile -Encoding utf8
    
    Write-Log "测试文件已创建: $testFile" "SUCCESS"
    return $testFile
}

# 主逻辑
Write-Log "上传速度优化器启动" "INFO"

if ($NetworkTest) {
    $networkStats = Test-NetworkLatency
    Write-Log "网络测试完成" "INFO"
} elseif ($Benchmark) {
    $testFile = if ($TestFile) { $TestFile } else { Create-TestFile }
    $benchmarkResults = Test-UploadMethods -TestFilePath $testFile
    
    # 清理测试文件
    if (-not $TestFile -and (Test-Path $testFile)) {
        Remove-Item $testFile -Force
        Write-Log "测试文件已清理" "INFO"
    }
} elseif ($OptimizeSettings) {
    Optimize-FtpSettings
} else {
    Write-Host "🚀 上传速度优化器" -ForegroundColor Cyan
    Write-Host "================" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "🛠️  使用方法:" -ForegroundColor Yellow
    Write-Host "  网络测试: .\scripts\upload_speed_optimizer.ps1 -NetworkTest" -ForegroundColor White
    Write-Host "  基准测试: .\scripts\upload_speed_optimizer.ps1 -Benchmark" -ForegroundColor White
    Write-Host "  优化设置: .\scripts\upload_speed_optimizer.ps1 -OptimizeSettings" -ForegroundColor White
    Write-Host "  指定文件: .\scripts\upload_speed_optimizer.ps1 -Benchmark -TestFile 'path\to\file.json'" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 推荐优化流程:" -ForegroundColor Yellow
    Write-Host "  1. 先运行网络测试了解基础性能" -ForegroundColor Gray
    Write-Host "  2. 运行基准测试找出最佳上传方法" -ForegroundColor Gray
    Write-Host "  3. 应用优化设置" -ForegroundColor Gray
    Write-Host "  4. 使用高性能管理器部署" -ForegroundColor Gray
    Write-Host ""
}