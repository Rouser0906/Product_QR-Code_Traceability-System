# ZY_PT-QRC 便携版

## 启动
- 运行 dist/ZY_PT-QRC/ZY_PT-QRC.exe

## 目录结构（onedir）
- ZY_PT-QRC.exe  主程序
- assets         资源（图标/Logo）
- config         配置（FTP 等）
- auto_sync      自动同步（Python 直传）
- scripts        辅助脚本
- cloud          建议与 EXE 同级放置 demo_json_a/demo_json_b 子目录

## 常见问题
- Logo 未显示：检查 assets 下是否存在 示例品牌A 透明.png / 示例品牌B 透明.png 或 demo_logo_b.png / demo_logo_a.png
- 上传失败：查看 auto_sync/logs/auto_sync.log 并检查 FTP 配置
