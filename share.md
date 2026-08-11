# 打包需求固化

一、项目基本信息
- 系统名称：示例集团多功能数智系统-产品溯源二维码发行和管理子系统
- 产物：PT-QRC.exe（onedir模式，绿色便携）
- 技术栈：Python3.x + PyQt5（排除 PyQt6/PySide）

二、核心原则
- 仅封装，不更改业务逻辑（优先遵循）。如需兼容性处理，使用 runtime hook。
- 100% 功能保留。

三、关键功能
- 动态云同步：cloud/demo_json_a 与 cloud/demo_json_b 自动上传到 /companies/demo_json_a 与 /companies/demo_json_b。
- 公网扫码：二维码“无感秒开”展示溯源信息。

四、文件纯净度（白名单策略）
- datas 仅收集必要目录与文件，排除 .git/.svn、*.tmp/*.temp、*_test.*、test.*、*.log、*.bak/*.old、fix.* 等。

五、附属文档
- 系统使用说明书.md、系统简介.txt、readme.md、版本号更新说明书.txt、share.md 一并输出到 dist 根目录。

六、兼容性
- 支持 Windows 7/10/11 绿色便携。

七、构建工具
- PyInstaller（onedir，禁用 UPX，runtime hook chdir）。
