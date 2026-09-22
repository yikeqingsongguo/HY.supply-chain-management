@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 停止后台定时调度器

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "logs\scheduler.pid" (
    echo 未找到 scheduler.pid，尝试按进程名结束...
    taskkill /f /im pythonw.exe 2>nul
    pause
    exit /b 0
)

set /p PID=<"logs\scheduler.pid"
if "%PID%"=="" (
    echo PID 文件为空
    pause
    exit /b 1
)

echo 正在结束调度器进程 PID=%PID%...
taskkill /f /pid %PID% 2>nul
if !errorlevel! == 0 (
    echo 已停止
    del "logs\scheduler.pid" 2>nul
) else (
    echo 进程已不存在或无法结束
    del "logs\scheduler.pid" 2>nul
)
pause
exit /b 0
