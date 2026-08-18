# JSON文件自动同步服务使用说明

## 🚀 一键启动（推荐）

### 方法1：手动启动
双击运行 `scripts\smart_auto_sync.bat`
- 自动同步所有现有文件
- 启动实时监控服务
- 一键完成所有操作

### 方法2：开机自动启动（推荐）
1. 双击运行 `scripts\install_auto_sync.bat` 安装到开机启动项
2. 重启电脑后服务会自动启动
3. 如需卸载，运行 `scripts\uninstall_auto_sync.bat`

## 📁 监控目录

服务会自动监控以下目录：
- `C:\Projects\Demo\cloud\demo_json_a\` → 上传到服务器 `companies/demo_json_a/`
- `C:\Projects\Demo\cloud\demo_json_b\` → 上传到服务器 `companies/demo_json_b/`

## ✨ 功能特点

- ✅ **智能启动** - 一键完成初始同步和监控启动
- ✅ **实时监控** - 新文件产生后2秒内自动上传
- ✅ **自动分类** - A-Q*.json和B-Q*.json自动上传到对应目录
- ✅ **开机启动** - 可选择开机自动启动服务
- ✅ **日志记录** - 详细的操作日志在 `scripts\auto_sync\logs\` 目录
- ✅ **错误处理** - 上传失败会自动重试

## 🔧 服务管理

- **启动服务**: 双击 `smart_auto_sync.bat`
- **停止服务**: 在服务窗口按 `Ctrl+C`
- **查看日志**: 打开 `scripts\auto_sync\logs\` 目录
- **安装开机启动**: 运行 `install_auto_sync.bat`
- **卸载开机启动**: 运行 `uninstall_auto_sync.bat`

## 📊 服务状态

服务运行时会显示：
- 初始同步的文件数量
- 实时监控状态
- 文件上传成功/失败信息
- 每5分钟的心跳日志

## ⚠️ 注意事项

1. 服务需要网络连接才能上传文件
2. 确保FTP服务器可访问（192.0.2.100）
3. 服务会在后台持续运行，占用少量系统资源
4. 如需停止服务，请按 `Ctrl+C` 而不是直接关闭窗口

## 🆘 故障排除

如果遇到问题：
1. 检查网络连接
2. 查看日志文件了解详细错误信息
3. 重新启动服务
4. 确认本地JSON文件存在且可读取