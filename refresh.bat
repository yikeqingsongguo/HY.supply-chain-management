@echo off
chcp 65001 >nul
setlocal
REM 双击刷新：清理 Excel -> 生成 data.json -> 注入构建 index.html -> 打开浏览器
set "PY=C:\Users\admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=py"
echo 正在刷新供应链看板数据...
"%PY%" "%~dp0run.py"
if errorlevel 1 (
  echo.
  echo [错误] 运行失败，请确认 Python 环境或查看上方报错。
  pause
  exit /b 1
)
echo 已生成 index.html，正在打开浏览器...
start "" "%~dp0index.html"
pause
