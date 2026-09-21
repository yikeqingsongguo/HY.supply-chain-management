#Requires -RunAsAdministrator
<#
.SYNOPSIS
    注册金蝶 -> 供应链看板 每日自动同步的 Windows 计划任务
.DESCRIPTION
    以管理员身份运行一次本脚本，会创建 3 个每日任务：
    KingdeeSync-0915 / KingdeeSync-1430 / KingdeeSync-1745
.NOTES
    若提示“无法加载脚本”，先在管理员 PowerShell 里执行：
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
#>
$ErrorActionPreference = "Stop"

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BatPath = Join-Path $BaseDir "sync_kingdee.bat"
$LogDir  = Join-Path $BaseDir "logs"
$LogPath = Join-Path $LogDir "register_tasks_ps.log"

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Log($msg) {
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $msg
    Write-Host $line
    $line | Out-File -FilePath $LogPath -Append -Encoding utf8
}

Write-Log "===== 开始注册计划任务 ====="
Write-Log "入口脚本: $BatPath"
Write-Log "当前用户: $($env:USERDOMAIN)\$($env:USERNAME)"

if (-not (Test-Path $BatPath)) {
    Write-Log "[错误] 找不到入口脚本：$BatPath"
    Read-Host "按回车退出"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`""
$Principal = New-ScheduledTaskPrincipal -UserId "$($env:USERDOMAIN)\$($env:USERNAME)" -LogonType Interactive -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

$Created = @()
$Failed  = @()

foreach ($time in @("09:15", "14:30", "17:45")) {
    $name = "KingdeeSync-" + $time.Replace(":", "")
    $Trigger = New-ScheduledTaskTrigger -Daily -At $time
    try {
        Register-ScheduledTask -TaskName $name -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
        Write-Log "[成功] 已创建 $name（每天 $time）"
        $Created += $name
    } catch {
        Write-Log "[失败] 创建 $name 失败: $($_.Exception.Message)"
        $Failed += $name
    }
}

Write-Log ""
Write-Log "===== 当前 KingdeeSync-* 任务列表 ====="
Get-ScheduledTask -TaskName "KingdeeSync-*" -ErrorAction SilentlyContinue | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName -ErrorAction SilentlyContinue
    Write-Log "$($_.TaskName) | State=$($_.State) | NextRunTime=$($info.NextRunTime)"
}

if ($Failed.Count -eq 0) {
    Write-Log ""
    Write-Log "全部创建成功。验证命令： schtasks /query /tn `"KingdeeSync-*`""
    Write-Log "手动跑一次：    schtasks /run /tn `"KingdeeSync-1430`""
    Write-Log "日志路径：      $LogPath"
} else {
    Write-Log ""
    Write-Log "部分任务创建失败，请查看上方错误信息。"
}

Read-Host "`n按回车退出"
