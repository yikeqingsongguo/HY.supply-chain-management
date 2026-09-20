@echo off
chcp 65001 >nul
setlocal

REM 金蝶 -> 供应链看板 每日同步（Windows 任务计划调用入口）
REM 如果运行失败，会写日志到 logs/sync.log，并通过企业微信 webhook 告警

set "PY=C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 确保日志目录存在
if not exist logs mkdir logs

"%PY%" sync_kingdee.py >> logs\sync.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 同步失败，详见 logs\sync.log
    exit /b 1
)

echo 同步成功
exit /b 0
