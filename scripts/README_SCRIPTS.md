# 脚本使用说明

## 重要：配置凭据

本目录下的PowerShell脚本包含FTP上传和同步功能。在使用这些脚本之前，您需要配置FTP凭据。

### 配置步骤

1. 复制凭据配置文件示例：
```powershell
Copy-Item scripts/ftp_credentials.ps1.example scripts/ftp_credentials.ps1
```

2. 编辑 `scripts/ftp_credentials.ps1`，填入您的实际FTP凭据：
```powershell
$FtpHost = 'your-actual-ftp-server.com'
$FtpUser = 'your_actual_username'
$FtpPassword = 'your_actual_password'
```

3. 确保 `ftp_credentials.ps1` 不会被提交到版本控制（已在 .gitignore 中配置）

### 脚本中的硬编码凭据

**注意**：本目录下的许多脚本仍包含硬编码的示例凭据（如 `your_ftp_username`）。这些是占位符值，您需要：

1. **方案A（推荐）**：修改脚本使用 `ftp_credentials.ps1` 配置文件
2. **方案B**：直接在各个脚本中替换为您的实际凭据（不推荐，因为可能误提交）

### 主要脚本说明

#### 同步相关
- `smart_auto_sync.bat` - 智能自动同步（推荐）
- `sync_now.bat` - 立即执行一次同步
- `auto_sync_to_server.ps1` - 自动同步服务

#### 监控相关
- `alert_checker.ps1` - 告警检查器
- `alert_monitoring_system.ps1` - 完整的监控系统
- `simple_alert_monitor.ps1` - 简化版监控

#### 测试相关
- `test_ftp_connection.ps1` - 测试FTP连接
- `single_test.ps1` - 单文件测试上传

#### 维护相关
- `reset_admin.py` - 重置管理员密码
- `db_inspect.py` - 数据库检查工具

### 安全建议

1. **不要直接在脚本中硬编码密码**
2. **使用配置文件或环境变量管理凭据**
3. **定期更新FTP密码**
4. **限制脚本文件的访问权限**
5. **定期审计日志文件**

### 域名配置

脚本中出现的域名（如 `scan.example.com`）仅为示例。实际使用时请替换为您的实际域名。

详见：[域名配置说明](../docs/DOMAIN_CONFIGURATION.md)

### 故障排除

如果脚本执行失败：
1. 检查网络连接：`Test-NetConnection your-ftp-server.com -Port 21`
2. 验证凭据是否正确
3. 查看日志文件（通常在 `auto_sync/logs/` 或 `logs/` 目录）
4. 检查防火墙设置

### 相关文档

- [安全配置说明](../SECURITY_SETUP.md)
- [系统维护最佳实践](../docs/系统维护最佳实践.md)
