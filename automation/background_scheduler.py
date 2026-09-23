#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金蝶在途数据同步 - 用户级后台定时调度器
======================================
不依赖 WorkBuddy 应用内自动化（避免 spawn ENAMETOOLONG），
也不依赖 Windows 计划任务（无需管理员权限）。

用法：
  1. 双击 start_scheduler.bat（或使用 pythonw 隐藏窗口）
  2. 任务在后台运行，每天 09:15 / 14:30 / 17:45 自动执行同步
  3. 需要停止时双击 stop_scheduler.bat

特性：
  - 纯标准库，无额外依赖
  - 机器睡眠唤醒后会自动判断是否需要补跑（60 秒宽限期）
  - 日志写到 logs/scheduler.log
  - 失败时会记录详细错误，但不阻断下一次调度
"""
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 目标调度时间（时, 分）
TRIGGERS = [(9, 15), (14, 30), (17, 45)]
GRACE_SECONDS = 60  # 唤醒后宽限期，错过目标时间 60 秒内仍补跑

# 无控制台环境（pythonw）下启动子进程：避免子进程因控制台被回收而收到
# CTRL_CLOSE_EVENT（0xC000013A）被强杀。
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MAX_ATTEMPTS = 3   # 单次调度内最多尝试次数
RETRY_DELAY = 30   # 两次尝试之间的间隔（秒）

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "logs" / "scheduler.log"
SYNC_SCRIPT = BASE_DIR / "sync_kingdee.py"
PID_FILE = BASE_DIR / "logs" / "scheduler.pid"


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def write_pid():
    try:
        PID_FILE.parent.mkdir(exist_ok=True)
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        log(f"写入 PID 文件失败: {e}")


def remove_pid():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except Exception:
        pass


def _pid_alive(pid):
    """用 OpenProcess 判断该 PID 是否存活（用户级权限即可）。"""
    try:
        import ctypes
        SYNCHRONIZE = 0x00100000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        h = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
        if h:
            kernel32.CloseHandle(h)
            return True
        return False
    except Exception:
        return False


def existing_instance():
    """若已有调度器实例在运行，返回其 PID；否则 None。

    启动途径不止一条（登录启动项 / 计划任务 / 手动），必须做单例保护，
    否则多个实例会在同一时刻重复跑同步、互相抢 src/采购订单.xlsx。
    """
    try:
        if not PID_FILE.exists():
            return None
        pid = int((PID_FILE.read_text(encoding="utf-8").strip() or "0"))
    except Exception:
        return None
    if pid <= 0 or pid == os.getpid():
        return None
    return pid if _pid_alive(pid) else None


def seconds_until_next_trigger(now=None):
    """计算距离下一个目标时刻还有多少秒。"""
    now = now or datetime.now()
    candidates = []
    for h, m in TRIGGERS:
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if t <= now:
            t += timedelta(days=1)
        candidates.append((t - now).total_seconds())
    return int(min(candidates))


def should_run_after_wake(now=None):
    """
    检查是否因为机器睡眠错过某个目标时刻（仍在宽限期内）。
    返回 (True, 目标datetime) 或 (False, None)。
    """
    now = now or datetime.now()
    for h, m in TRIGGERS:
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if now < target:
            target -= timedelta(days=1)
        if 0 <= (now - target).total_seconds() <= GRACE_SECONDS:
            return True, target
    return False, None


def run_sync():
    """调用 sync_kingdee.py，返回 (success_bool, 返回码/异常)。"""
    log("=== 调度触发，开始执行同步 ===")
    py_exe = Path(r"C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\python.exe")
    try:
        proc = subprocess.run(
            [str(py_exe), str(SYNC_SCRIPT)],
            cwd=str(BASE_DIR),
            # ⚠️ 必须显式给 stdin=DEVNULL：pythonw 没有控制台，父进程 stdin 是无效句柄，
            #    子进程继承它会让 CreateProcess 直接抛 `[Errno 22] Invalid argument`
            #    （2026-09-22 17:45 那次就是连续两次这个错，第 3 次才侥幸起来）。
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            creationflags=NO_WINDOW,
        )
        for line in proc.stdout.splitlines():
            log(f"[sync stdout] {line}")
        for line in proc.stderr.splitlines():
            log(f"[sync stderr] {line}")
        if proc.returncode == 0:
            log("同步成功完成")
            return True, proc.returncode
        else:
            log(f"同步失败，返回码: {proc.returncode}")
            return False, proc.returncode
    except subprocess.TimeoutExpired:
        log("同步执行超时（超过 10 分钟）")
        return False, "timeout"
    except Exception as e:
        log(f"同步过程异常: {e}")
        return False, e


def run_sync_with_retry():
    """带重试的同步：最多 MAX_ATTEMPTS 次，全部失败才返回 False。"""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        log(f"--- 同步尝试 {attempt}/{MAX_ATTEMPTS} ---")
        ok, rc = run_sync()
        if ok:
            return True
        if attempt < MAX_ATTEMPTS:
            log(f"第 {attempt} 次同步失败（返回码 {rc}），{RETRY_DELAY} 秒后重试")
            time.sleep(RETRY_DELAY)
    log(f"同步连续失败 {MAX_ATTEMPTS} 次，本次调度放弃")
    return False


def main(run_now=False):
    log("=" * 50)
    log("后台调度器启动")
    log(f"目标调度时间: {['%02d:%02d' % (h, m) for h, m in TRIGGERS]}")
    log(f"宽限期: {GRACE_SECONDS} 秒")

    if run_now:
        # 供手动/测试立即执行一次，不进入常驻循环
        log("--run-now：立即执行一次同步")
        ok = run_sync_with_retry()
        sys.exit(0 if ok else 1)

    running = existing_instance()
    if running:
        log(f"检测到已有调度器实例在运行（PID {running}），本次启动直接退出")
        sys.exit(0)

    write_pid()
    try:
        # 启动时检查是否刚刚错过某个点（例如机器从睡眠中唤醒后启动）
        missed, target = should_run_after_wake()
        if missed:
            log(f"启动时发现错过目标时间 {target:%H:%M}，在宽限期内，立即补跑")
            run_sync_with_retry()

        last_check = datetime.now()
        while True:
            now = datetime.now()

            # 轮询检测：从 last_check 到现在是否有目标时刻经过
            # 这比一次性 sleep 几个小时更可靠——Windows/pythonw 的长 sleep
            # 在系统睡眠/息屏后经常无法按时唤醒，导致整点同步被静默跳过。
            triggered = False
            for h, m in TRIGGERS:
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if now < target:
                    target -= timedelta(days=1)
                if last_check < target <= now:
                    log(f"到达调度时间 {target:%H:%M}，开始同步")
                    run_sync_with_retry()
                    triggered = True
                    break

            if not triggered:
                wait_sec = seconds_until_next_trigger(now)
                # 每次最多睡 60 秒，避免长 sleep 失效
                sleep_sec = max(1, min(60, wait_sec))
                if wait_sec > 60 and now.minute % 5 == 0 and now.second < 30:
                    next_time = now + timedelta(seconds=wait_sec)
                    log(f"距离下一次调度 {next_time:%H:%M} 还有 {wait_sec // 60} 分钟")
                time.sleep(sleep_sec)

            last_check = now
    except KeyboardInterrupt:
        log("收到中断信号，调度器退出")
    finally:
        remove_pid()


if __name__ == "__main__":
    main(run_now=("--run-now" in sys.argv))
