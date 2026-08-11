@echo off
title 紧急修复系统
color 0C
echo ============================================
echo           紧急修复系统闪退问题
echo ============================================
echo.
echo 警告：此操作将撤销所有权限修改！
echo.
set /p choice="是否继续恢复原始系统？(Y/N): "
if /i "%choice%"=="Y" (
    echo.
    echo 正在恢复原始系统状态...
    python restore_system.py
    echo.
    echo 恢复完成！现在尝试启动系统...
    echo.
    python emergency_start.py
) else (
    echo 操作已取消
)
echo.
pause