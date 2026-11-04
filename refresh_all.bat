@echo off
chcp 65001 >nul
setlocal
set "DASH=%~dp0"
cd /d "%DASH%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PY=C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%DASH%refresh_all.py" %*
echo.
pause
