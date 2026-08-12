# 快速部署指南

## 📖 概述

本指南帮助您快速部署和配置"产品溯源二维码发行与管理系统"。

## 🔧 前提条件

### 系统要求
- Windows 10/11 或 Windows Server
- Python 3.8+ （源码运行）或直接使用打包的 EXE
- PHP 7.4+ （如果使用Web API）
- SQLite（内置，无需单独安装）

### 网络要求
- 可选：FTP服务器（用于同步数据到云端）
- 可选：SMTP服务器（用于邮件通知）

## 📦 安装步骤

### 1. 获取代码
```bash
git clone <your-bitbucket-repo-url>
cd B_PT_QRC-SYS
```

### 2. 配置敏感信息

#### 2.1 FTP配置
```bash
# 复制示例文件
cp config/ftp_config.json.example config/ftp_config.json

# 编辑配置文件，填入实际的FTP凭据
notepad config/ftp_config.json
```

配置内容：
```json
{
  "A": {
    "host": "your-ftp-server.com",
    "port": 21,
    "user": "your_ftp_username",
    "pass": "your_ftp_password",
    "base_path": "/companies/demo_json_a/",
    "tls": false,
    "timeout": 30,
    "passive_mode": true
  }
}
```

#### 2.2 自动同步配置
```bash
# 复制示例文件
cp auto_sync/enhanced_config.json.example auto_sync/enhanced_config.json

# 编辑配置文件
notepad auto_sync/enhanced_config.json
```

更新FTP连接信息：
```json
{
  "ftp_connection": {
    "host": "your-ftp-server.com",
    "port": 21,
    "username": "your_ftp_username",
    "password": "your_ftp_password",
    "use_passive": true
  }
}
```

#### 2.3 API配置（可选）
如果使用Web API功能：

```bash
# PHP数据库配置
cp api/db_config.php.example api/db_config.php
notepad api/db_config.php

# API配置（微信、短信等）
cp api/api_config.php.example api/api_config.php
notepad api/api_config.php
```

### 3. 初始化数据库

```bash
# 运行Python主程序，会自动创建数据库
python main.py
```

首次运行时：
- 自动创建 `qr_system.db` 数据库
- 创建默认管理员账户：
  - 用户名: `admin`
  - 密码: `change_me_immediately`
  - **⚠️ 首次登录后请立即修改密码！**

### 4. 启动系统

#### 方式1：使用Python运行（开发环境）
```bash
# 启动主程序
python main.py
```

#### 方式2：使用打包的EXE（生产环境）
```bash
# 直接运行
PT-QRC_Main.exe
```

#### 启动自动同步服务（可选）
```bash
# 单独启动自动同步服务
python auto_sync/auto_sync_service.py
```

## 🔐 安全配置

### 修改默认密码
1. 启动系统
2. 使用默认账户登录（admin / change_me_immediately）
3. 立即在"用户管理"中修改密码

### 配置权限
参考 `SECURITY_SETUP.md` 文档配置用户权限。

## 🌐 配置公司域名

在以下文件中更新为您的实际域名：

### config/system_config.json
```json
{
  "system": {
    "name": "产品溯源二维码发行与管理系统",
    "company": "您的公司名称"
  }
}
```

### 更新验证URL
如果使用公网扫码功能，需要配置产品验证URL：

1. 编辑 `api/verify.php`
2. 找到 `get_product_url()` 函数
3. 更新 `base_urls` 为您的实际域名

## 📊 验证安装

### 1. 健康检查
```bash
# 运行健康检查脚本
python scripts/CRASH_DETECTIVE.py
```

### 2. 测试FTP连接
```bash
# 运行FTP上传测试
powershell scripts/enhanced_ftp_uploader.ps1 -TestMode
```

### 3. 数据库检查
```bash
# 检查数据库结构
python scripts/db_inspect.py
```

## 📁 目录结构说明

```
B_PT_QRC-SYS/
├── config/                 # 配置文件目录
│   ├── ftp_config.json    # FTP配置（需要手动创建）
│   └── system_config.json # 系统配置
├── auto_sync/             # 自动同步服务
│   ├── enhanced_config.json  # 同步配置（需要手动创建）
│   └── auto_sync_service.py  # 同步服务主程序
├── cloud/                 # 云同步数据目录
│   ├── demo_json_a/           # 公司A的JSON数据
│   └── demo_json_b/           # 公司B的JSON数据
├── modules/               # 业务模块
├── utils/                 # 工具模块
├── api/                   # Web API
├── logs/                  # 日志目录
└── qr_system.db          # 数据库文件（自动创建）
```

## 🔄 日常操作

### 备份数据库
```bash
# 手动备份
copy qr_system.db qr_system_backup_%date%.db

# 或使用脚本
python scripts/backup_database.py
```

### 查看日志
```bash
# 查看最新日志
type logs\qr_system_*.log | more

# 查看错误日志
type logs\errors_*.log | more
```

### 重置管理员密码
```bash
python scripts/reset_admin.py
```

## 🐛 故障排除

### 问题1：数据库无法创建
**解决方案**：
- 检查目录写入权限
- 确保没有其他程序占用数据库文件

### 问题2：FTP上传失败
**解决方案**：
- 检查 `config/ftp_config.json` 配置是否正确
- 测试FTP服务器连接性
- 查看 `logs/auto_sync.log` 详细错误信息

### 问题3：无法登录
**解决方案**：
- 使用重置脚本：`python scripts/reset_admin.py`
- 检查数据库文件是否存在且完整

更多故障排除信息，参考 `docs/故障排除指南.md`

## 📚 更多文档

- **系统维护**: `docs/系统维护最佳实践.md`
- **安全设置**: `SECURITY_SETUP.md`
- **API文档**: `docs/API_DOCUMENTATION.md`
- **权限系统**: `PERMISSION_SYSTEM_IMPROVEMENT_SUMMARY.md`

## 📞 支持

如有问题，请：
1. 查看项目文档目录
2. 查看故障排除指南
3. 联系项目维护者

## ⚠️ 重要提示

1. **不要**将包含敏感信息的配置文件提交到版本控制
2. **务必**修改默认管理员密码
3. **建议**定期备份数据库文件
4. **确保**日志文件定期清理，避免占用过多空间
5. **推荐**在生产环境使用打包的EXE版本

---

**部署完成后，系统即可投入使用！**

祝您使用愉快！🎉
