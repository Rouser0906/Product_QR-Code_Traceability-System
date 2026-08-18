# 域名配置说明

本项目文档中所有的域名引用均为示例，实际部署时需要替换为您自己的域名。

## 需要替换的域名

文档中出现的以下域名需要替换为您的实际域名：

### 主要域名
- `scan.example.com` → 您的扫码专用子域名
- `example.com` → 您的主域名
- `your-company-domain.com` → 您的公司域名（如适用）

### FTP/服务器配置
- `your-ftp-server.com` → 您的FTP服务器地址
- `192.0.2.100` → 您的服务器IP地址（如文档中出现）

## 配置步骤

### 1. 更新FTP配置
编辑 `config/ftp_config.json`：
```json
{
  "A": {
    "host": "your-actual-ftp-server.com",
    ...
  }
}
```

### 2. 更新扫码系统配置
如果使用Cloudflare Workers或其他边缘服务：
- 在 `cloud/scan-worker/wrangler.toml` 中配置您的域名
- 更新环境变量 `ORIGIN_API` 为您的实际API地址

### 3. 更新二维码生成逻辑
在代码中搜索并替换所有域名引用：
```bash
# Windows PowerShell
Get-ChildItem -Recurse -Include *.py,*.php,*.js | ForEach-Object {
    (Get-Content $_.FullName) -replace 'scan\.example\.com', 'your-domain.com' | Set-Content $_.FullName
}
```

### 4. DNS配置
确保您的域名已正确配置DNS记录：
- A记录：指向您的服务器IP
- CNAME记录：如使用CDN服务
- SSL证书：配置HTTPS

## 安全建议

1. 不要在公开仓库中提交包含实际域名的配置文件
2. 使用环境变量管理敏感配置
3. 定期更新SSL证书
4. 启用HTTPS强制跳转
5. 配置适当的CORS策略

## 相关文档

- [安全配置说明](../SECURITY_SETUP.md)
- [扫码系统部署](./share_scan.md)
- [系统操作手册](./系统操作手册.md)
