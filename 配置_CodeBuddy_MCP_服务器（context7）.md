# 配置 CodeBuddy MCP 服务器（context7）

## Core Features

- 设置 MCP 服务器地址为 https://mcp.context7.com/mcp

- 默认服务器设为 context7

- 超时 10000ms 与重试 3 次

- 备份与回退机制

- JSON 合法性校验

- 重启后连接验证

## Tech Stack

{
  "Windows": "PowerShell 7"
}

## Design

系统配置与脚本操作，无界面改动。

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] 备份现有配置文件到同目录 .bak

[X] 创建并验证目标路径与写入权限

[X] 写入含服务器地址与默认服务器的 JSON 配置

[X] 执行 JSON 合法性校验（ConvertFrom-Json 方案）

[ ] 如需要，注入鉴权字段（apiKey）并重写配置

[/] 重启 CodeBuddy/VS Code 以应用新配置

[ ] 在插件内验证 MCP 连接并测试请求
