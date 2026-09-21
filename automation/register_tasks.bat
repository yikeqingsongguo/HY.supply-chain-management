@echo off
chcp 65001 >nul
color 0E
title 金蝶看板-计划任务注册器
setlocal EnableDelayedExpansion

REM ============================================================
REM  金蝶 -> 供应链看板  每日固定时间自动同步
REM  【Windows 计划任务注册器】—— 以管理员身份运行本文件一次即可
REM
REM  原理：直接调用 automation\sync_kingdee.bat（纯 Python，无需 WorkBuddy 常驻）
REM        绕开应用内定时偶发的 spawn ENAMETOOLONG 失败
REM  创建 3 个每日任务：KingdeeSync-0915 / KingdeeSync-1430 / KingdeeSync-1745
REM  卸载见同目录 UNINSTALL_tasks.bat
REM ============================================================

set "BASE=%~dp0"
set "BAT=%BASE%sync_kingdee.bat"
set "LOG=%BASE%logs\register_tasks.log"

if not exist "%BASE%logs" mkdir "%BASE%logs"
(
  echo ========================================
  echo 开始注册计划任务  %date% %time%
  echo 当前用户: %USERDOMAIN%\%USERNAME%
  echo 入口脚本: %BAT%
  echo ========================================
  echo.
) > "%LOG%" 2>&1

REM --- 检查管理员权限 ---
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo [错误] 当前没有管理员权限，请右键点击本文件选择「以管理员身份运行」。
  echo [错误] 当前没有管理员权限 >> "%LOG%" 2>&1
  echo.
  pause
  exit /b 1
)
echo [OK] 已确认管理员权限

if not exist "%BAT%" (
  echo [错误] 找不到入口脚本：%BAT%
  echo [错误] 找不到入口脚本：%BAT% >> "%LOG%" 2>&1
  echo.
  pause
  exit /b 1
)
echo [OK] 入口脚本存在：%BAT%
echo.

echo 正在为当前用户注册每日自动同步任务...
echo 时间：09:15 / 14:30 / 17:45
echo.
echo 详细日志同时写入：%LOG%
echo.

for %%T in (0915 1430 1745) do (
  if "%%T"=="0915" ( set "NAME=KingdeeSync-0915" & set "TIME=09:15" )
  if "%%T"=="1430" ( set "NAME=KingdeeSync-1430" & set "TIME=14:30" )
  if "%%T"=="1745" ( set "NAME=KingdeeSync-1745" & set "TIME=17:45" )

  echo 正在注册 [!NAME!] 时间 [!TIME!] ...
  (
    echo ---- [!NAME!] [!TIME!] ----
    schtasks /create /tn "!NAME!" /tr "\"%BAT%\"" /sc daily /st !TIME! /rl HIGHEST /f
    echo 退出码: !ERRORLEVEL!
    echo.
  ) >> "%LOG%" 2>&1

  if !ERRORLEVEL! equ 0 (
    echo   [成功] [!NAME!] !TIME!
  ) else (
    echo   [失败] [!NAME!] !TIME!  退出码 !ERRORLEVEL!
    echo   详情见日志：%LOG%
  )
)

echo.
echo ========================================
echo 注册流程结束。下面列出已创建的任务：
echo ========================================
schtasks /query /tn "KingdeeSync-*" 2>&1
(
  echo.
  echo ========================================
  echo 最终任务列表：
  schtasks /query /tn "KingdeeSync-*" 2>&1
  echo ========================================
  echo 结束时间: %date% %time%
) >> "%LOG%" 2>&1

echo.
echo.
echo [操作完成]
echo 验证命令：  schtasks /query /tn "KingdeeSync-*"
echo 手动跑一次：schtasks /run /tn "KingdeeSync-1430"
echo 取消注册：  运行同目录 UNINSTALL_tasks.bat
echo.
pause
