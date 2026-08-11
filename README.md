# 产品溯源二维码发行与管理系统 · Product QR-Code Traceability System

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](#)

一套面向制造 / 流通企业的**产品溯源二维码发行与管理**一体化方案：桌面端批量生成、打印、赋码管理 + 公网扫码验证 + 数据自动同步。多角色权限、审计日志、多公司 / 多产品线、移动端隐私合规的扫码数据采集。

> 本仓库为**开源版 (OSE)**。所有真实公司名 / 域名 / 凭据均已脱敏为占位符，部署前请按 [SECURITY_SETUP.md](SECURITY_SETUP.md) 填入你自己的配置。

---

## 功能特性

- **二维码发行**：按产品 / 批次 / 规格批量生成唯一溯源码（前缀如 `A-Q` / `B-Q`），含纠错等级、批次号、生产日期、检验结果、执行标准、规格等字段。
- **标签打印**：PyQt5 打印控件，标签模板、logo 选择、签发人、服务电话、生产地址，并记录打印来源（电脑指纹 / 用户 / IP / 时间戳）。
- **扫码验证**：消费者移动端扫码 → 公网页面展示产品溯源信息；中英双语 (i18n)、移动端适配。
- **权限系统**：基于角色的访问控制（admin / manager / operator / viewer / general_user），细粒度权限点、会话 token、失败锁定、审计日志。
- **业务管理**：公司、部门、员工、产品、经销商、扫码记录的全生命周期管理。
- **自动同步**：本地 QR-JSON 经 `watchdog` 文件监听 + FTP 上传到扫码服务器（PowerShell），支持增量 / 去重 / 重试 / 告警看板。
- **数据导入导出**：Excel 批量导入导出。
- **隐私合规**：扫码采集脚本默认不上报精确 GPS，仅采集模糊地域。
- **多部署形态**：IIS + PHP，或 Cloudflare Worker + KV（短链 `/q/{token}`）。

## 系统架构

```
┌──────────────────────┐     FTP / JSON (watchdog)    ┌────────────────────────┐
│  桌面端 (PyQt5)       │ ───────────────────────────▶ │  扫码服务器              │
│  发行 / 打印 / 管理    │                              │  IIS + PHP API          │
│  SQLite qr_system.db  │                              │  静态扫码页 (i18n)       │
└──────────┬───────────┘                              └───────────┬────────────┘
           │ admin / 角色管理                                       │ /index.html?code=...
           │                                                        ▼
┌──────────────────────┐                                          ┌─────────────────────┐
│  运维脚本 (PowerShell) │                                          │  消费者手机扫码       │
│  计划任务 / 告警看板    │                                          │  (移动端浏览器)       │
└──────────────────────┘                                          └─────────────────────┘
```

## 技术栈

| 层 | 技术 |
|---|---|
| 桌面应用 | Python 3.13、PyQt5、qrcode、Pillow、pandas、pyarrow |
| 存储 | SQLite (WAL) — `users / roles / user_roles / sessions / audit_log / companies / departments / staff / products / qr_records / scan_history / distributors` |
| 同步 | watchdog + PowerShell + FTP；可选 Cloudflare Worker + KV |
| 扫码服务端 | PHP 7.4+（`resolve` / `get_product_data`）、静态 HTML/JS/CSS、i18n |
| Web 服务器 | IIS（`web.config`）或 Cloudflare |

## 快速开始

### 环境要求
- Windows 10+（桌面端）；Python 3.13+；PHP 7.4+（扫码 API，可选）

### 安装
```bash
git clone https://github.com/Rouser0906/Product_QR-Code_Traceability-System.git
cd Product_QR-Code_Traceability-System
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 初始化数据库与配置
```bash
# 复制配置示例（详见 SECURITY_SETUP.md）
cp config/ftp_config.json.example      config/ftp_config.json
cp auto_sync/config.json.example       auto_sync/config.json
cp api/db_config.php.example           api/db_config.php
cp api/api_config.php.example          api/api_config.php

# 初始化数据库（建表 + 默认角色 + 默认 admin）
python -c "from utils.auth import auth_manager; print('DB ready')"
```

### 运行
```bash
python main_system.py    # 主程序
# 或
python safe_start.py     # 安全启动（含自检）
```
首次登录：**`admin` / `change_me_immediately`** → **立即改密**。

## 配置

| 文件 | 用途 | 入版本库？ |
|---|---|---|
| `config/ftp_config.json` | FTP 主机 / 账号（同步用） | 否（仅 `.example`） |
| `auto_sync/config.json` | 同步策略 / 路径 | 否（仅 `.example`） |
| `api/db_config.php` | 扫码服务器 JSON 数据根目录 | 否（仅 `.example`） |
| `api/api_config.php` | API 行为配置 | 否（仅 `.example`） |
| `qr_system.db` | 运行时数据库 | 否（`.gitignore`） |

> 仓库内一切真实凭据 / 域名 / 公司名均为占位符。`.gitignore` 已排除真实配置、数据库、构建产物、截图。

## 角色与权限

| 角色 | 说明 | 关键权限 |
|---|---|---|
| `admin` | 系统管理员 | 全部 |
| `manager` | 部门经理 | 部门 / 员工 / 产品 / 二维码管理、报表 |
| `operator` | 操作员 | 二维码生成、日常操作、导出 |
| `viewer` | 查看者 | 只读 |
| `general_user` | 一般使用者 | 仅二维码生成 / 打印 |

权限点采用 `资源.动作`（如 `qr.generate`、`users.create`），支持通配（`companies.*`）。

## 公网扫码部署

两种模式：

1. **IIS + PHP**：把 `qr_public_files/` 与 `api/` 部署到 IIS 站点；`api/*.php` 读取 `api/db_config.php` 指定的 JSON 数据目录；`web.config.sample` 提供重写 / 缓存 / CORS 样例。
2. **Cloudflare Worker + KV**（短链 `/q/{token}`）：边缘解析 token → 跳转完整溯源页，见 `docs/share_scan.md`。

二维码生成时的 `verification_url` 指向你的扫码域名（默认占位 `https://scan.example.com/index.html?code=...`，**部署时替换**）。

## 打包桌面应用

```bash
pip install pyinstaller
python build_PT-QRC.py        # 或 quick_build.bat
# 产物在 dist/PT-QRC/
```

## 项目结构

```
.
├── main_system.py / main.py / safe_start.py / welcome.py   # 入口
├── modules/          # 业务模块（二维码打印、扫码历史、权限、员工…）
├── utils/            # auth / config / security / qr_security / validator / computer_info / logger
├── auto_sync/        # 文件监听 + 事件队列（同步服务）
├── api/              # PHP 扫码 API（+ .example 配置）
├── qr_public_files/  # 公网扫码静态页（HTML/CSS/JS/i18n）
├── scripts/          # PowerShell 同步 / 告警脚本、计划任务安装器
├── config/           # 配置（.example）
├── database/         # 建表 / 示例 SQL
├── docs/             # 文档
├── assets/           # 应用图标 / 样式
└── PT-QRC.spec    # PyInstaller 规格
```

## 安全

- 首次登录**立即改默认密码**；为生产部署启用强密码 + 失败锁定（见 `utils/config.py`、`utils/security.py`）。
- 真实配置 / 数据库 / 构建产物 / 截图不入版本库（见 `.gitignore`）。
- 生产环境启用 HTTPS；为扫码域名配置 CSP / WAF / CDN 白名单。
- 详见 [SECURITY_SETUP.md](SECURITY_SETUP.md)。漏洞请按 [SECURITY.md](SECURITY.md) 私下报告。

## FAQ

- **忘密码？** 用 `scripts/` 下的管理员重置脚本，或直接更新库表 `users.password_hash`（用 `utils.security` 重新哈希）。
- **FTP 同步失败？** 核对 `config/ftp_config.json`、网络、防火墙；查看 `scripts/` 告警看板。
- **二维码扫不开？** 检查 `verification_url` 域名、PHP API 是否可达、对应 JSON 是否已同步到服务器目录。

## 许可证与贡献

- [Apache-2.0](LICENSE)
- 贡献：[CONTRIBUTING.md](CONTRIBUTING.md)　·　行为准则：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- 安全问题：[SECURITY.md](SECURITY.md)　·　一般问题：GitHub Issues
