#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金蝶在途数据 -> 供应链看板 每日同步管道

执行步骤：
  1. 调用 kingdee_collector.py --export-only 导出采购订单 xlsx
  2. 将导出的最新 xlsx 复制到 supply-dashboard/src/采购订单.xlsx（覆盖）
  3. git add/commit/push origin main
  4. GitHub Actions 自动 clean + build + 部署到 Pages

失败时通过企业微信群机器人 webhook 发送告警。
"""
import os
import sys
import json
import time
import shutil
import subprocess
import glob
import urllib.request
from datetime import datetime
from pathlib import Path

# 默认编码容错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        with open(log_dir / "sync.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config():
    cfg_path = Path(__file__).parent / "kingdee_config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {cfg_path}")
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def send_wecom(webhook_url, title, content, mentioned_mobiles=None):
    """通过企业微信群机器人 webhook 发送 markdown 消息。"""
    if not webhook_url or webhook_url.endswith("YOUR_KEY_HERE"):
        log("⚠️ 企微 webhook 未配置，跳过通知")
        return
    body = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"**{title}**\n> {content}\n\n时间：{datetime.now():%Y-%m-%d %H:%M:%S}"
        }
    }
    if mentioned_mobiles:
        body["markdown"]["mentioned_mobile_list"] = mentioned_mobiles
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            rsp = json.loads(resp.read().decode("utf-8"))
            log(f"企微通知结果: {rsp}")
    except Exception as e:
        log(f"企微通知失败: {e}")


def run_subprocess(cmd, cwd=None, env=None, timeout=300):
    """运行子进程，失败时抛出异常。"""
    log(f"执行: {' '.join(str(c) for c in cmd)} (cwd={cwd})")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout
    )
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            log(f"  [stdout] {line}")
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            log(f"  [stderr] {line}")
    result.check_returncode()
    return result


def find_latest_export(incoming_dir):
    """找 data/incoming/ 下最新的 .xlsx（按修改时间）。"""
    incoming = Path(incoming_dir)
    files = list(incoming.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"{incoming} 下未找到导出的 xlsx 文件")
    latest = max(files, key=lambda p: p.stat().st_mtime)
    log(f"最新导出文件: {latest} (大小 {latest.stat().st_size} 字节)")
    return latest


def main():
    cfg = load_config()
    kd = cfg["kingdee"]
    paths = cfg["paths"]
    wecom = cfg.get("wecom", {})
    git_cfg = cfg.get("git", {})

    collector_dir = Path(paths["collector_dir"])
    dashboard_dir = Path(paths["dashboard_dir"])
    target_file = dashboard_dir / "src" / paths["target_filename"]
    incoming_dir = collector_dir / "data" / "incoming"
    python_exe = paths.get("python_exe", r"C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe")

    # 环境变量注入金蝶凭证（kingdee_collector 优先读环境变量）
    env = os.environ.copy()
    env["KINGDEE_URL"] = kd["url"]
    env["KINGDEE_USER"] = kd["username"]
    env["KINGDEE_PASS"] = kd["password"]
    env["KINGDEE_DC"] = kd.get("datacenter", "华熠网络")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    error_msg = None
    try:
        # 1) 导出
        log("=== 步骤 1/4: 金蝶导出采购订单 ===")
        run_subprocess(
            [python_exe, str(collector_dir / "kingdee_collector.py"), "--export-only"],
            cwd=str(collector_dir),
            env=env,
            timeout=600
        )

        # 2) 复制到看板 src
        log("=== 步骤 2/4: 复制到看板 src ===")
        latest = find_latest_export(incoming_dir)
        shutil.copy2(str(latest), str(target_file))
        log(f"已覆盖: {target_file}")

        # 3) git 提交并推送
        log("=== 步骤 3/4: git push ===")
        msg = git_cfg.get("commit_message", "daily: Kingdee 在途数据同步")
        run_subprocess(["git", "add", "-A"], cwd=str(dashboard_dir))
        # 仅当有变更才提交；无变更时 git diff --exit-code 返回 1
        diff = subprocess.run(
            ["git", "diff", "--cached", "--exit-code"],
            cwd=str(dashboard_dir),
            capture_output=True
        )
        if diff.returncode == 0:
            log("看板无变更，无需提交")
        else:
            run_subprocess(["git", "commit", "-m", msg], cwd=str(dashboard_dir))
            run_subprocess(["git", "push", "origin", "main"], cwd=str(dashboard_dir))
            log("已推送至 origin/main，GitHub Actions 将自动部署")

        log("=== 同步完成 ===")

    except subprocess.TimeoutExpired as e:
        error_msg = f"子进程超时: {e.cmd}"
        log(f"❌ {error_msg}")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        log(f"❌ {error_msg}")

    # 4) 失败通知
    if error_msg:
        log("=== 步骤 4/4: 发送失败告警 ===")
        title = "金蝶→看板同步失败"
        content = error_msg.replace("\n", "\n> ")
        send_wecom(wecom.get("webhook_url", ""), title, content, wecom.get("mentioned_mobiles"))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
