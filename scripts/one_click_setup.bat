@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Move to repo root if executed from elsewhere
cd /d "%~dp0.."

echo [1/5] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
  echo Python not found in PATH. Please install Python 3.9+ and retry.
  pause
  exit /b 1
)

echo [2/5] Creating virtual environment (.venv) if not exists...
if not exist ".venv" (
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
)

set PY=.venv\Scripts\python.exe
set PIP=.venv\Scripts\pip.exe

echo [3/5] Upgrading pip and installing requirements...
"%PY%" -m pip install --upgrade pip wheel setuptools
if errorlevel 1 (
  echo Failed to upgrade pip/setuptools.
  pause
  exit /b 1
)
"%PIP%" install -r requirements.txt
if errorlevel 1 (
  echo Failed to install dependencies from requirements.txt
  pause
  exit /b 1
)

echo [4/5] Running dependency checks...
"%PY%" scripts\deps_check.py
if errorlevel 1 (
  echo Dependency check failed.
  pause
  exit /b 1
)

echo [5/5] Running UI smoke test...
"%PY%" scripts\ui_smoketest.py
if errorlevel 1 (
  echo UI smoke test reported warnings or errors. Continuing to start app...
)

echo Starting application...
"%PY%" main.py
endlocal