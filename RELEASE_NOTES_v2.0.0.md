# Release v2.0.0

发布日期：请在发布时填写（YYYY-MM-DD）

亮点
- 首次公开发布版本，完善的发布与安全文档（PUBLISH_GUIDE / PRE_PUBLISH_CHECKLIST / SECURITY_SETUP）
- 统一默认密码为 `change_me_immediately` 并强化首次登录修改提示
- 新增 Apache-2.0 LICENSE、CONTRIBUTING、SECURITY、CODE_OF_CONDUCT
- 新增 GitHub Actions 最小 CI、Dependabot、.gitattributes
- 完整的敏感信息只读扫描与报告（SENSITIVE_SCAN_REPORT.md）

变更摘要
- 文档与指南：README、发布指南、安全指引等大量补充与修订
- 配置：修正 `config/system_config.json` 乱码占位，示例配置齐全
- 脚本：新增 `scripts/publish_to_github.ps1` 一键推送脚本

升级与注意事项
- 强烈建议部署后立刻修改管理员默认密码
- 生产环境凭据仅通过本地配置文件或环境变量注入（已被 .gitignore 忽略）
- 建议开启 GitHub Security（Secret scanning / Dependabot / Branch protection）

致谢
- 感谢贡献者与使用者！欢迎通过 Issue/PR 参与共建。
