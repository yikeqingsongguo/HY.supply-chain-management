@echo off
chcp 65001 >nul
color 0C
title 金蝶看板-计划任务卸载器
setlocal EnableDelayedExpansion

set "BASE=%~dp0"
set "LOG=%BASE%logs\uninstall_tasks.log"
if not exist "%BASE%logs" mkdir "%BASE%logs"

(
  echo ========================================
  echo 开始卸载计划任务  %date% %time%
  echo ========================================
) > "%LOG%" 2>&1

net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo [错误] 需要管理员权限，请右键选择「以管理员身份运行」。
  pause
  exit /b 1
)

echo 正在删除 3 个 KingdeeSync-* 计划任务...
echo.

for %%N in (KingdeeSync-0915 KingdeeSync-1430 KingdeeSync-1745) do (
  echo 正在删除 [%%N] ...
  (
    echo ---- [%%N] ----
    schtasks /delete /tn "%%N" /f
    echo 退出码: !ERRORLEVEL!
    echo.
  ) >> "%LOG%" 2>&1
  if !ERRORLEVEL! equ 0 ( echo   [成功] %%N ) else ( echo   [无需删除/失败] %%N )
)

echo.
echo [操作完成]
echo 日志：%LOG%
echo.
pause
