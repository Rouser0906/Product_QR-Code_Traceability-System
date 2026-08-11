# 产品溯源二维码发行与管理系统

[![CI](https://github.com/Rouser0906/Product_QR-Code_Traceability-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Rouser0906/Product_QR-Code_Traceability-System/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Rouser0906/Product_QR-Code_Traceability-System?display_name=tag&sort=semver)](https://github.com/Rouser0906/Product_QR-Code_Traceability-System/releases)

## 项目简介

这是一个完整的产品溯源二维码管理系统，支持二维码生成、打印、扫码验证和数据管理等功能。

## 主要功能

- **用户权限管理**：完善的角色权限系统
- **二维码生成与打印**：支持批量生成和打印二维码
- **产品信息管理**：管理产品类型、规格、颜色等信息
- **扫码验证**：移动端扫码查看产品溯源信息
- **自动同步**：自动将数据同步到FTP服务器
- **数据导入导出**：支持Excel格式的数据导入导出

## 技术栈

- **后端**：Python 3.x
- **前端**：HTML, CSS, JavaScript
- **桌面应用**：PyQt5
- **数据库**：SQLite
- **服务端**：PHP (API接口)

## 快速开始

### 1. 环境要求

- Python 3.8+
- PHP 7.4+ (用于API)
- Windows 10+ (桌面应用)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置系统

**重要**：首次部署前必须配置敏感信息，详见 [安全配置说明](SECURITY_SETUP.md)

```bash
# 复制配置文件示例
cp config/ftp_config.json.example config/ftp_config.json
cp auto_sync/config.json.example auto_sync/config.json
cp api/db_config.php.example api/db_config.php
cp api/api_config.php.example api/api_config.php

# 编辑配置文件，填入实际的配置信息
```

### 4. 初始化数据库

```bash
python -c "from utils.auth import auth_manager; print('数据库初始化完成')"
```

### 5. 运行系统

```bash
# 运行桌面应用
python main_system.py

# 或使用启动脚本
python safe_start.py
```

### 6. 首次登录

- 用户名：`admin`
- 密码：`change_me_immediately`

**重要**：首次登录后请立即修改密码！

## 项目结构

```
.
├── api/                    # PHP API接口
├── auto_sync/              # 自动同步服务
├── config/                 # 配置文件
├── database/               # 数据库脚本
├── docs/                   # 文档
├── modules/                # 业务模块
├── scripts/                # 工具脚本
├── utils/                  # 工具类
├── qr/                     # 二维码前端页面
├── main_system.py          # 主程序入口
└── requirements.txt        # Python依赖
```

## 文档

- [安全配置说明](SECURITY_SETUP.md) - **必读**
- [域名配置说明](docs/DOMAIN_CONFIGURATION.md)
- [系统操作手册](docs/系统操作手册.md)
- [系统维护最佳实践](docs/系统维护最佳实践.md)
- [扫码系统部署](docs/share_scan.md)

## 安全注意事项

1. **不要提交敏感信息**：配置文件中的密码、密钥等信息不应提交到版本控制
2. **修改默认密码**：首次登录后立即修改管理员密码
3. **使用HTTPS**：生产环境必须启用HTTPS
4. **定期备份**：定期备份数据库和重要配置文件
5. **权限控制**：合理分配用户权限

详见 [安全配置说明](SECURITY_SETUP.md)

## 常见问题

### Q: 如何重置管理员密码？
A: 运行 `python scripts/reset_admin.py`

### Q: FTP上传失败怎么办？
A: 检查 `config/ftp_config.json` 配置是否正确，确认网络连接正常

### Q: 如何添加新用户？
A: 登录系统后，在"用户管理"模块中添加

### Q: 数据库文件在哪里？
A: 默认位置是 `qr_system.db`，可在 `utils/database_config.py` 中配置

## 许可证

本项目基于 Apache-2.0 许可证开源。详见 [LICENSE](LICENSE)。

## 贡献

欢迎提交 Issue 和 Pull Request。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 联系方式

安全问题请通过 [SECURITY.md](SECURITY.md) 中的方式私下报告；一般问题可通过 GitHub Issues 反馈。

## 更新日志

详见各文档中的版本更新记录。
