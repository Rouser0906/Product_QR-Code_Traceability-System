#requires -Version 7.0
<#
scan.example.com 一键部署脚本
- 依赖：Node.js、Cloudflare Wrangler（若无，将提示安装）
- 目标：发布 cloud/scan-worker/worker.js，创建/绑定 KV，路由到 scan.example.com
#>

param(
  [string]$WorkerDir = "cloud/scan-worker",
  [string]$KvBinding = "QRMAP",
  [string]$Zone = "example.com",
  [string]$TestToken = "TEST1234"
)

function Ensure-Wrangler {
  try {
    $v = (wrangler --version) 2>$null
    if (-not $v) {
      Write-Host "未检测到 wrangler，准备安装..." -ForegroundColor Yellow
      npm install -g wrangler --yes
    } else {
      Write-Host "已检测到 wrangler: $v" -ForegroundColor Green
    }
  } catch {
    Write-Host "安装 wrangler 失败，请确认已安装 Node.js 与 npm，再重试。" -ForegroundColor Red
    throw
  }
}

function Invoke-Deploy {
  Set-Location (Resolve-Path $WorkerDir)
  Write-Host "当前目录：" (Get-Location) -ForegroundColor Cyan

  wrangler login
  if ($LASTEXITCODE -ne 0) { throw "wrangler login 失败" }

  # 创建 KV 命名空间（存在则跳过）
  try {
    wrangler kv:namespace create $KvBinding --binding=$KvBinding
  } catch {
    Write-Host "KV 命名空间可能已存在，继续发布..." -ForegroundColor Yellow
  }

  wrangler publish
  if ($LASTEXITCODE -ne 0) { throw "wrangler publish 失败" }

  Write-Host "发布完成，请在 Cloudflare 控制台确认 routes 已生效：" -ForegroundColor Green
  Write-Host " - https://scan.$Zone/q/*"
  Write-Host " - https://scan.$Zone/api/resolve"

  Write-Host "验证示例：" -ForegroundColor Green
  Write-Host " 打开浏览器访问：https://scan.$Zone/q/$TestToken"
  Write-Host " 页面将请求 /api/resolve?id=$TestToken 并渲染结果。"
}

try {
  Ensure-Wrangler
  Invoke-Deploy
  Write-Host "全部完成 ✅" -ForegroundColor Green
} catch {
  Write-Host "部署失败：$($_.Exception.Message)" -ForegroundColor Red
  exit 1
}