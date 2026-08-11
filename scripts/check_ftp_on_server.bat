@echo off
rem 在 Windows Server 本地以 Administrator 运行，一键检查并修复 FTP
chcp 65001 >nul
echo === 检查 FTP 服务状态 ===
sc query FTPSVC | findstr /i "running" >nul
if %errorlevel% neq 0 (
    echo FTP 服务未运行，正在启动...
    sc start FTPSVC
    sc config FTPSVC start= auto
) else (
    echo FTP 服务已运行
)

echo.
echo === 检查 FTP 站点状态（IIS） ===
%windir%\system32\inetsrv\appcmd list site | findstr /i "ftp" >nul
if %errorlevel% neq 0 (
    echo 未找到 FTP 站点，需手动创建或检查站点名称
) else (
    echo 已发现 FTP 站点
)

echo.
echo === 检查/创建用户主目录并赋权 ===
set userHome=C:\inetpub\qr-system\companies\data
if not exist "%userHome%" (
    echo 正在创建 %userHome%...
    mkdir "%userHome%"
)
echo 授予 your_ftp_username 完全控制权限...
icacls "%userHome%" /grant "your_ftp_username:(OI)(CI)F" /T /Q >nul
if %errorlevel% equ 0 (
    echo 权限设置完成
) else (
    echo 权限设置失败，请确认用户存在
)

echo.
echo === 设置被动模式端口范围 50000-50100 ===
rem 导入 IIS 管理模块
%windir%\system32\inetsrv\appcmd set config -section:system.ftpServer/firewallSupport /lowDataChannelPort:50000 /highDataChannelPort:50100 /commit:apphost >nul
if %errorlevel% equ 0 (
    echo 被动端口范围已设置为 50000-50100
) else (
    echo 被动端口设置失败，可手动在 IIS 中配置
)

echo.
echo === 本地测试 127.0.0.1:21 ===
echo 请手动验证：打开命令提示符，执行：
echo   ftp 127.0.0.1
echo   用户名：your_ftp_username
echo   密码：[REDACTED-FTP-PASSWORD]
echo 若能正常登录，说明服务器端已修复，可远程连接。
echo.
echo === 检查完成 ===
pause