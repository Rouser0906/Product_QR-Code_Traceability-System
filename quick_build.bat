@echo off
chcp 65001 > nul
echo.
echo =====================================
echo 示例集团多功能数智系统 - 快速打包
echo =====================================
echo.

echo 🔍 步骤1: 检查依赖...
python check_dependencies.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖检查失败，请先解决问题！
    pause
    exit /b 1
)

echo.
echo 🚀 步骤2: 开始打包...
python build_ZY_PT-QRC.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    pause
    exit /b 1
)

echo.
echo 🎉 打包完成！
echo 📁 输出目录: dist_package\
echo 🎯 主程序: ZY_PT-QRC.exe
echo.
echo 现在可以将 dist_package 目录中的所有文件分发给用户了。
echo.
pause