@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 启动后台定时调度器（无需管理员权限）
REM 使用 pythonw.exe 避免留下控制台窗口

set "PY=C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe"
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist logs mkdir logs

REM 检查是否已在运行
if exist "logs\scheduler.pid" (
    for /f %%i in ('type logs\scheduler.pid') do (
        tasklist /fi "PID eq %%i" 2>nul | findstr "%%i" >nul
        if !errorlevel! == 0 (
            echo 调度器已在运行（PID=%%i）
            pause
            exit /b 0
        )
    )
)

echo 正在启动后台调度器...
start "" "%PY%" "background_scheduler.py"
echo [%date% %time%] 调度器已启动 >> logs\scheduler.log 2>&1

echo 调度器已启动，日志: %SCRIPT_DIR%logs\scheduler.log
echo 停止请运行 stop_scheduler.bat
pause
exit /b 0
