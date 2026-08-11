# 安全配置说明

本项目已移除所有敏感信息，在部署前需要配置以下文件。

## 必需配置文件

### 1. FTP配置
复制示例文件并填入实际配置：
```bash
cp config/ftp_config.json.example config/ftp_config.json
```
然后编辑 `config/ftp_config.json` 填入：
- FTP服务器地址
- FTP用户名和密码
- FTP路径配置

### 2. 自动同步配置
```bash
cp auto_sync/config.json.example auto_sync/config.json
cp auto_sync/enhanced_config.json.example auto_sync/enhanced_config.json
```
编辑这些文件，配置：
- 同步任务
- FTP连接信息
- 本地和远程路径

### 3. PHP API配置
```bash
cp api/db_config.php.example api/db_config.php
cp api/api_config.php.example api/api_config.php
```
编辑这些文件，配置：
- 数据库连接信息
- 微信API密钥
- 短信服务密钥

### 4. 系统配置
检查 `config/system_config.json`，确保邮件配置部分已填入实际值（如果启用邮件通知）。

## 初始管理员密码

首次运行系统时，会创建默认管理员账户：
- 用户名：`admin`
- 默认密码：`change_me_immediately`

**重要：首次登录后请立即修改密码！**

修改密码的方式：
1. 登录系统后在用户管理界面修改
2. 或使用命令行工具：
```bash
python scripts/reset_admin.py
```

## 数据库初始化

首次部署时需要初始化数据库：
```bash
# 创建权限系统表
python -c "from utils.auth import auth_manager; print('数据库初始化完成')"

# 或使用SQL脚本
sqlite3 qr_system.db < database/qr_login_system.sql
sqlite3 qr_system.db < database/permission_system_schema.sql
```

## .gitignore 说明

以下文件已添加到 `.gitignore`，不会被提交到版本控制：
- `config/ftp_config.json` - FTP密码
- `auto_sync/config.json` - 同步配置（可能包含密码）
- `auto_sync/enhanced_config.json` - 增强配置（包含FTP密码）
- `api/db_config.php` - 数据库密码
- `api/api_config.php` - API密钥
- `qr_system.db` - 数据库文件（包含用户数据）
- `*.db-shm`, `*.db-wal` - 数据库临时文件

## 安全建议

1. **修改默认密码**：立即修改所有默认密码
2. **使用强密码**：密码应包含大小写字母、数字和特殊字符
3. **定期备份**：定期备份数据库和配置文件
4. **限制访问**：使用防火墙限制数据库和FTP访问
5. **启用HTTPS**：生产环境必须使用HTTPS
6. **审计日志**：定期检查系统日志

## 环境变量（可选）

也可以使用环境变量来配置敏感信息：
```bash
# Windows
set FTP_HOST=your-server.com
set FTP_USER=your_username
set FTP_PASS=your_password

# Linux/Mac
export FTP_HOST=your-server.com
export FTP_USER=your_username
export FTP_PASS=your_password
```

然后修改代码读取环境变量而不是配置文件。
