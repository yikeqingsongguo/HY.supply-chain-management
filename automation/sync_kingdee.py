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

# 无控制台环境下启动子进程（后台 pythonw 调度器场景），
# 避免子进程因控制台被回收而收到 CTRL_CLOSE_EVENT（0xC000013A）被强杀。
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# 复制目标文件可能正被 Excel/WPS 打开而短暂占用（曾报 PermissionError: [Errno 13]）→ 带重试
COPY_MAX_ATTEMPTS = 5
COPY_RETRY_DELAY = 3  # 秒

# 本机未独立安装 Git，git 由 WorkBuddy 管理的 PortableGit 提供；
# 正常登录会话（含后台调度器）的 PATH 里没有它，必须用绝对路径。
_GIT_HARD_CANDIDATES = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    r"C:\Users\admin\AppData\Local\Programs\Git\cmd\git.exe",
]


def resolve_git(cfg=None):
    """解析 git 可执行文件绝对路径，避免依赖 PATH。"""
    cands = []
    # 1) 配置显式指定
    try:
        if cfg:
            g = cfg.get("paths", {}).get("git_exe")
            if g:
                cands.append(g)
    except Exception:
        pass
    # 2) 自动发现 WorkBuddy PortableGit（任意版本，优先新版）
    try:
        base = Path.home() / ".workbuddy" / "binaries" / "PortableGit" / "versions"
        if base.exists():
            for d in sorted(base.iterdir(), reverse=True):
                for sub in ("cmd", "mingw64/bin"):
                    p = d / sub / "git.exe"
                    if p.exists():
                        cands.append(str(p))
    except Exception:
        pass
    # 3) 常规安装位置
    cands.extend(_GIT_HARD_CANDIDATES)
    # 4) 兜底：PATH
    try:
        w = shutil.which("git")
        if w:
            cands.append(w)
    except Exception:
        pass
    for c in cands:
        try:
            if c and Path(c).exists():
                return c
        except Exception:
            pass
    return "git"


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
        timeout=timeout,
        creationflags=NO_WINDOW,
    )
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            log(f"  [stdout] {line}")
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            log(f"  [stderr] {line}")
    result.check_returncode()
    return result


def snapshot_exports(incoming_dir):
    """记录导出目录当前文件集合，供 find_latest_export 只认本次新文件。"""
    return {p.name for p in Path(incoming_dir).glob("*.xlsx")}


def find_latest_export(incoming_dir, since=None):
    """找 data/incoming/ 下最新的 .xlsx（按修改时间）。

    since 传入导出前的文件集合时，只在新产生的文件里挑，避免上一张单据
    导出失败时误把旧文件当成新数据复制进 src/（串表风险）。
    """
    incoming = Path(incoming_dir)
    files = list(incoming.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"{incoming} 下未找到导出的 xlsx 文件")
    if since is not None:
        fresh = [p for p in files if p.name not in since]
        if fresh:
            files = fresh
        else:
            log("⚠️ 本次导出未生成新文件，回退使用目录内最新文件，请检查上一步是否成功")
    latest = max(files, key=lambda p: p.stat().st_mtime)
    log(f"最新导出文件: {latest} (大小 {latest.stat().st_size} 字节)")
    return latest


def copy_with_retry(src, dst):
    """复制并处理 Excel/WPS 占用导致的 PermissionError；失败返回异常对象。"""
    copy_err = None
    for _try in range(1, COPY_MAX_ATTEMPTS + 1):
        try:
            shutil.copy2(str(src), str(dst))
            return None
        except PermissionError as e:
            copy_err = e
            log(f"复制被占用（第 {_try}/{COPY_MAX_ATTEMPTS} 次）: {e}")
            if _try < COPY_MAX_ATTEMPTS:
                time.sleep(COPY_RETRY_DELAY)
    return copy_err


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
    git_exe = resolve_git(cfg)
    log(f"使用 git: {git_exe}")

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
        log("=== 步骤 1/9: 金蝶导出采购订单 ===")
        snap1 = snapshot_exports(incoming_dir)
        run_subprocess(
            [python_exe, str(collector_dir / "kingdee_collector.py"), "--export-only"],
            cwd=str(collector_dir),
            env=env,
            timeout=600
        )

        # 2) 复制到看板 src（在途口径，现有页面使用）
        log("=== 步骤 2/9: 复制在途采购订单 ===")
        latest = find_latest_export(incoming_dir, snap1)
        copy_err = copy_with_retry(latest, target_file)
        if copy_err is not None:
            log(f"❌ 复制失败：{target_file} 被其他程序占用。"
                f"请关闭正在打开该文件的 Excel/WPS（或退出同步目录预览）后重试。")
            raise copy_err
        log(f"已覆盖: {target_file}")

        # 2b) 导出全量采购订单（含已关闭），供准交率使用
        log("=== 步骤 3/9: 金蝶导出全量采购订单（含已关闭） ===")
        snap2 = snapshot_exports(incoming_dir)
        env_full = env.copy()
        env_full["KINGDEE_PO_SCHEME"] = "默认方案（个人）"
        run_subprocess(
            [python_exe, str(collector_dir / "kingdee_collector.py"), "--export-only"],
            cwd=str(collector_dir),
            env=env_full,
            timeout=900
        )
        log("=== 步骤 4/9: 复制全量采购订单 ===")
        latest_full = find_latest_export(incoming_dir, snap2)
        full_target = dashboard_dir / "src" / "otd_po_full.xlsx"
        copy_err = copy_with_retry(latest_full, full_target)
        if copy_err is not None:
            log(f"❌ 复制失败：{full_target} 被其他程序占用。")
            raise copy_err
        log(f"已覆盖: {full_target}")

        # 2c) 收料通知单（准交率数据源）
        # 方案「111111」列最全（含源单单号/合格入库关联数量/实收数量），
        # 过滤已在金蝶侧固定为「收料日期 = 本月」，因此可直接用于当月准交率。
        if cfg.get("sync", {}).get("enable_recv_sync", False):
            log("=== 步骤 5/9: 金蝶导出收料通知单 ===")
            snap3 = snapshot_exports(incoming_dir)
            env_recv = env.copy()
            env_recv["KINGDEE_FORM"] = "收料通知单列表"
            env_recv["KINGDEE_PO_SCHEME"] = cfg.get("sync", {}).get("recv_scheme", "111111")
            run_subprocess(
                [python_exe, str(collector_dir / "kingdee_collector.py"), "--export-only"],
                cwd=str(collector_dir),
                env=env_recv,
                timeout=900
            )
            log("=== 步骤 6/9: 复制收料通知单 ===")
            latest_recv = find_latest_export(incoming_dir, snap3)
            recv_target = dashboard_dir / "src" / "otd_recv.xlsx"
            copy_err = copy_with_retry(latest_recv, recv_target)
            if copy_err is not None:
                log(f"❌ 复制失败：{recv_target} 被其他程序占用。")
                raise copy_err
            log(f"已覆盖: {recv_target}")
        else:
            log("=== 步骤 5-6/9: 收料单同步未启用（enable_recv_sync=false），跳过 ===")

        # 2d) 采购申请单（管理台「待下单汇总」与申请单匹配数据源）
        if cfg.get("sync", {}).get("enable_apply_sync", True):
            log("=== 步骤 7/9: 金蝶导出采购申请单 ===")
            snap4 = snapshot_exports(incoming_dir)
            env_apply = env.copy()
            env_apply["KINGDEE_FORM"] = "采购申请单列表"
            env_apply["KINGDEE_PO_SCHEME"] = cfg.get("sync", {}).get("apply_scheme", "周计划（含备注）")
            run_subprocess(
                [python_exe, str(collector_dir / "kingdee_collector.py"), "--export-only"],
                cwd=str(collector_dir),
                env=env_apply,
                timeout=900
            )
            log("=== 步骤 8/9: 复制采购申请单 ===")
            latest_apply = find_latest_export(incoming_dir, snap4)
            apply_target = dashboard_dir / "src" / "otd_apply.xlsx"
            copy_err = copy_with_retry(latest_apply, apply_target)
            if copy_err is not None:
                log(f"❌ 复制失败：{apply_target} 被其他程序占用。")
                raise copy_err
            log(f"已覆盖: {apply_target}")
        else:
            log("=== 步骤 7-8/9: 申请单同步未启用（enable_apply_sync=false），跳过 ===")

        # 3) git 提交并推送
        log("=== 步骤 9/9: git push ===")
        msg = git_cfg.get("commit_message", "daily: Kingdee 在途数据同步")
        # 只提交看板数据源 src/，避免误提交 .lnk/.workbuddy/ 等无关文件
        run_subprocess([git_exe, "add", "-A", "--", "src"], cwd=str(dashboard_dir))
        # 仅当有变更才提交；无变更时 git diff --exit-code 返回 0
        diff = subprocess.run(
            [git_exe, "diff", "--cached", "--exit-code"],
            cwd=str(dashboard_dir),
            capture_output=True,
            creationflags=NO_WINDOW,
        )
        if diff.returncode == 0:
            log("看板无变更，无需提交")
        else:
            run_subprocess([git_exe, "commit", "-m", msg], cwd=str(dashboard_dir))
            run_subprocess([git_exe, "push", "origin", "main"], cwd=str(dashboard_dir))
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
