@echo off
setlocal EnableExtensions
REM =============================================================
REM QRJsonAutoSync �ƻ����񴴽��ű����� .bat �汾��
REM ʹ��˵�����Ҽ����ļ� �� �Թ���Ա�������
REM ���ã���������������ļƻ����񣬺�̨��פ���� run_auto_sync.py
REM =============================================================

REM --- ����ԱȨ�޼�� ---
net session >nul 2>&1
if %errorlevel% NEQ 0 (
  echo [ERROR] ��Ҫ�Թ���Ա������б��_����Ո���Iԓ .bat �� �Թ���T����\�С�
  pause
  exit /b 1
)

REM --- �ɰ����޸����²��� ---
set "TASK_NAME=QRJsonAutoSync"
set "PROJECT_ROOT=C:\Projects\Demo"
set "PYTHONW=C:\Python313\pythonw.exe"
set "SCRIPT_PATH=%PROJECT_ROOT%\scripts\run_auto_sync.py"

REM --- Python ·���z���c���� ---
if not exist "%PYTHONW%" (
  echo [WARN] δ�ҵ� %PYTHONW% ������ C:\Python313\python.exe
  set "PYTHONW=C:\Python313\python.exe"
)

REM --- Ŀ��ű������Լ�� ---
if not exist "%SCRIPT_PATH%" (
  echo [ERROR] δ�ҵ��_����%SCRIPT_PATH%
  echo Ո�_�J PROJECT_ROOT �O�����_��
  pause
  exit /b 1
)

REM --- ������־Ŀ¼ ---
if not exist "%PROJECT_ROOT%\auto_sync\logs" (
  mkdir "%PROJECT_ROOT%\auto_sync\logs" 2>nul
)

REM --- ɾ�������񣨺��Դ��� ---
schtasks /delete /tn "%TASK_NAME" /f >nul 2>&1

REM --- ��װ�΄������У�����̖��---
set "TR_CMD=\"%PYTHONW%\" \"%SCRIPT_PATH%\""

echo [INFO] ���ڄ���Ӌ���΄գ�%TASK_NAME%
SCHTASKS /CREATE /TN "%TASK_NAME" /SC ONSTART /RU SYSTEM /RL HIGHEST /TR %TR_CMD% /F
if %errorlevel% NEQ 0 (
  echo [ERROR] ����Ӌ���΄�ʧ����Ո�z��·���c���ޡ�
  pause
  exit /b 1
)

echo [INFO] ��������Ӌ���΄�...
SCHTASKS /RUN /TN "%TASK_NAME%"

REM --- ݔ����ʾ ---
echo.
echo [OK] Ӌ���΄��ф����K���ӣ�%TASK_NAME%
echo [PATH] �ĿĿ䛣�%PROJECT_ROOT%
echo [LOG] Ո�鿴���I��%PROJECT_ROOT%\auto_sync\logs\auto_sync.log

echo.
pause
endlocal
