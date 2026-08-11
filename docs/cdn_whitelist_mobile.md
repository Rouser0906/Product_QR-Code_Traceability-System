# CDN/防火墙加白工单（移动端扫码失败）

## 问题现象
- 移动端扫码 `https://scan.example.com/index.html?code=HS-DEMO-000000001`  
- 表现：空白页 / 无法连接 / 提示“网络错误”  
- 根因：CDN/WAF 拦截空/SNI 字段或非浏览器 UA，直接 RST 连接。

## 必须加白名单
| 类型 | 值 | 备注 |
|---|---|---|
| 出口 IP（脚本） | 10.0.0.200/32 | 当前办公网络 |
| 移动端常用段 | 198.51.100.0/24 | 示例，可按实际调整 |
| UA 关键词 | *Chrome* / *Safari* / *Mobile* | 允许移动端 UA |
| 目标域名 | scan.example.com | 443 端口 |

## 各厂商一键加白命令
### Cloudflare
```bash
# 安装 cfctl 后
cfctl waf rules create --zone scan.example.com --action allow --ip 10.0.0.200/32 --note "example-sync-bot"
```

### 阿里云（CLI）
```bash
aliyun waf OpenAPI --RegionId cn-hangzhou --Domain scan.example.com \
  --RuleType ip --RuleAction allow --RuleContent 10.0.0.200/32
```

### 腾讯云（CLI）
```bash
tccli cdn UpdateDomainConfig --Domain scan.example.com \
  --IpFilter.IpFilterType allow --IpFilter.IpList ["10.0.0.200/32"]
```

## 验证步骤
1. 加白后 30 秒生效。  
2. 手机扫码任意二维码 → 正常显示产品信息页即成功。  
3. PowerShell 执行：
```powershell
Invoke-WebRequest https://scan.example.com/index.html?code=HS-DEMO-000000001 -Headers @{'User-Agent'='Mozilla/5.0 (Linux; Android 13) Chrome/112.0.0.0 Mobile'} -UseBasicParsing
```
返回 200 即闭环。