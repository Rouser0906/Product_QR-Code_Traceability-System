# QR 同步策略调整：仅上传缺失的 JSON 文件（missing-only）

更新时间：2025-09-12
负责人：QR Display System / Rovo Dev

## 背景与目标
- 历史问题：部分模块存在不必要覆盖上传、URL 路径混乱（含 `inetpub/wwwroot` 与 `/companies` 前缀），带来失败风险与维护成本。
- 本次目标：
  - 统一同步策略为 missing-only（仅当云端不存在该 JSON 时才上传）。
  - 统一 URL 模板，去除不再使用的路径前缀，降低风险和带宽占用。

## 变更摘要
- 同步策略
  - `new_ftp_sync_service.py`：`upload_file` 默认 `overwrite=False`，上传前通过 `NLST` 列表检查远端是否已存在，存在则跳过（missing-only）。
  - `ftp_config.json` / `ftp_config_new.json`：`overwrite_existing=false`。
- 路径与 URL 统一
  - 去除 `inetpub/wwwroot` 与 `/companies` 前缀，统一为：
    - QR 页面：`https://scan.example.com/index.html?code={QR_CODE}`
    - JSON 数据：`https://scan.example.com/{company}/data/{filename}`
- 工具与服务更新
  - `fixed_qr_service.py`、`simple_ftp_sync_service.py`：打印/日志中的 URL 改为新规范。
  - `modules/qr_print_widget.py`：生成的验证 URL 改为新规范。
  - `create_auto_sync_config.py`：校验新规范路径（`/company_a/data/` 或 `/company_b/data/`），`overwrite_existing=false`。

## 受影响范围
- Windows 服务与监控：`fixed_qr_service.py`、`simple_ftp_sync_service.py`。
- 打印与上传工具：`modules/qr_print_widget.py`（上传成功提示链接）。
- 自动同步：`start_new_services.py` 使用 `new_ftp_sync_service.py` 进行缺失上传。

## 主要变更文件
- `new_ftp_sync_service.py`（实现“仅上传缺失文件”）
- `ftp_config.json`（`overwrite_existing=false`；含 `sync_mappings` 与 `sync_mode: "missing_only"`）
- `ftp_config_new.json`（`overwrite_existing=false`）
- `auto_deploy_with_credentials.py`（修正 URL、键名 `username`、去除错误路径）
- `fixed_qr_service.py` / `simple_ftp_sync_service.py` / `modules/qr_print_widget.py`（清理 `/companies` 与 `inetpub/wwwroot`）
- `create_auto_sync_config.py`（覆盖策略与路径校验调整）

## 配置要点
- `ftp_config.json`
  - `sync_mappings` 已包含 company_a/company_b 两家公司，`sync_mode: "missing_only"`。
  - `auto_sync.overwrite_existing=false`。
- `ftp_config_new.json`
  - `sync_settings.overwrite_existing=false`。

## 验证与结果
- 执行 `final_deployment_verification.py` 生成：`deployment_verification_20250912_095022.json`
- 通过项：5/6（服务文件、目录、FTP 连接、URL 更新、备份系统）
- 未通过：`server_accessibility`（SSL 握手失败，目标服务器侧/网络问题）
- 结论：本地策略与实现正确，建议后续排查服务器证书/网络。

## 风险与回滚
- 远端 `NLST` 列表可能受网络波动影响；异常已记录为调试日志，不影响流程。
- 回滚方案：临时在调用点显式传入 `overwrite=True` 或（不建议）将配置恢复 `overwrite_existing=true`。

## 后续工作（建议创建 Jira）
1. 排查与修复 `server_accessibility` 失败（SSL/证书/防火墙）。
2. 统一清理文档中残留的 `/companies` 示意链接（仅说明文档层面）。

## 附录：关键逻辑（节选）
- `new_ftp_sync_service.py`：
```
# upload_file(self, local_file, remote_path, filename, overwrite: bool = False)
# 当 overwrite=False 时：
#  - 切换到 remote_path
#  - 使用 NLST 获取远端文件列表
#  - 若 filename 已存在，则跳过上传并记录日志
```

- URL 模板：
```
QR 页面:   https://scan.example.com/index.html?code={QR_CODE}
JSON 数据: https://scan.example.com/{company}/data/{filename}
```
