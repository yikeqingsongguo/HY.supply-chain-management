# -*- coding: utf-8 -*-
"""供应链看板 · 一键刷新

把「金蝶导出 → 本地重建 → 提交推送 → 口径回显」串成一条链，双击 refresh_all.bat 即可。

用法：
    python refresh_all.py           完整刷新（导出四表 + 重建 + 推送）
    python refresh_all.py skip      跳过导出，仅用现有 src/ 重建 + 推送

设计要点：
  - 导出步骤直接复用 automation/sync_kingdee.py，与每日 3 次自动同步完全同源，
    方案（在途数据(共享) / 采购订单宽表默认方案 / 111111 / 周计划（含备注））由配置决定，
    这里不复制一份过滤逻辑，避免两套口径漂移。
  - 导出用 base python（与任务计划一致），重建必须用 venv python（含 openpyxl/pandas）。
  - 只提交构建产物，不 git add -A，避免把 preview_*.html 之类的临时文件带进仓库。
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

DASH = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(DASH, "automation", "logs")

# 重建需要 openpyxl / pandas：优先隔离 venv，不存在时退回当前解释器
VENV_PY = r"C:\Users\admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
BUILD_PY = VENV_PY if os.path.exists(VENV_PY) else sys.executable

GIT_CANDIDATES = [
    r"C:\Users\admin\.workbuddy\binaries\PortableGit\versions\1.3.0\bin\git.exe",
    shutil.which("git") or "",
]

# 构建产物：只提交这些，避免临时文件入库
COMMIT_PATHS = ["src", "data.json", "index.html",
                os.path.join("console", "weekly.json"),
                os.path.join("console", "apply.csv")]


def hr(ch="=", n=64):
    print(ch * n)


def step(no, total, title):
    print()
    print("[%d/%d] %s" % (no, total, title))


def run(cmd, label, cwd=DASH):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=os.environ.copy())
    cost = time.time() - t0
    if r.returncode != 0:
        print("  ✗ %s 失败（返回码 %d，用时 %.0fs）" % (label, r.returncode, cost))
        return False
    print("  ✓ %s 完成（%.0fs）" % (label, cost))
    return True


def find_git():
    for p in GIT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


def git(git_exe, *args):
    return subprocess.run([git_exe, *args], cwd=DASH,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def mtime(p):
    """源表导出时间：判断数据新旧只看这个，不看构建时间。"""
    try:
        return datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m-%d %H:%M")
    except OSError:
        return "-"


def print_summary():
    """回显本次口径，让人一眼看出数据截止时间和待下单规模。"""
    try:
        with open(os.path.join(DASH, "console", "weekly.json"), encoding="utf-8") as f:
            w = json.load(f)
        with open(os.path.join(DASH, "data.json"), encoding="utf-8") as f:
            meta = json.load(f).get("meta", {})
    except Exception as e:  # noqa: BLE001
        print("  （读取汇总失败：%s）" % e)
        return

    am = w.get("apply_match") or {}
    src = os.path.join(DASH, "src")
    print("  申请单源表  : %s（待下单数据截止）" % mtime(os.path.join(src, "otd_apply.xlsx")))
    print("  采购订单源表: %s（在途数据截止）" % mtime(os.path.join(src, "采购订单.xlsx")))
    print("  本次构建    : %s" % w.get("updated_at", "-"))
    print("  在途订单    : %s 行 / 剩余 %s 件" % (
        format(meta.get("order_count", 0), ","), format(int(meta.get("sum_remain", 0) or 0), ",")))
    print("  待下单      : %s 行 / %s 件" % (
        w.get("rows", 0), format(int(w.get("total_plan", 0) or 0), ",")))
    print("  供应商      : %s 家（核心 %s 家）" % (w.get("supplier_count", 0), w.get("core_count", 0)))
    pend = w.get("pending") or {}
    print("  待填写      : %s 行 / %s 件" % (
        pend.get("rows", 0), format(int(pend.get("qty", 0) or 0), ",")))
    print("  单据闸门    : 关闭/作废排除 %s 行，剩余为0排除 %s 行，VYTK排除 %s 行" % (
        am.get("skipped_closed", 0), am.get("skipped_zero", 0), am.get("skipped_vytk", 0)))


def main():
    skip_export = any(a.lower() in ("skip", "-skip", "--skip") for a in sys.argv[1:])

    hr()
    print("  供应链看板 · 一键刷新")
    print("  模式：%s" % ("跳过金蝶导出，仅用现有 src/ 重建" if skip_export
                        else "完整刷新（金蝶导出 + 重建 + 推送，约 4-6 分钟）"))
    hr()
    print("  目录：%s" % DASH)

    gi = 0
    total = 3 if skip_export else 4

    # ---- 1) 金蝶导出 ----
    if not skip_export:
        gi += 1
        step(gi, total, "金蝶导出四张表（采购订单 / 全量订单 / 收料通知单 / 采购申请单）")
        sync = os.path.join(DASH, "automation", "sync_kingdee.py")
        if not run([sys.executable, sync], "金蝶导出"):
            print()
            print("  导出没走完，后续步骤已跳过，仓库没有任何改动。")
            print("  日志：%s" % os.path.join(LOG_DIR, "sync.log"))
            print("  若只是暂时连不上金蝶，可改用：refresh_all.bat skip（用现有数据重建）")
            return 1

    # ---- 2) 本地重建 ----
    gi += 1
    step(gi, total, "重建看板数据（clean.py → build.py，含待下单汇总）")
    if not run([BUILD_PY, os.path.join(DASH, "run.py")], "数据重建"):
        print()
        print("  重建失败，未做任何提交。源表未被修改，可直接重试。")
        return 1

    # ---- 3) 提交推送 ----
    gi += 1
    step(gi, total, "提交构建产物并推送")
    git_exe = find_git()
    if not git_exe:
        print("  ✗ 找不到 git，跳过推送（数据已在本地生成，可手动提交）")
        return 1

    paths = [p for p in COMMIT_PATHS if os.path.exists(os.path.join(DASH, p))]
    r = git(git_exe, "add", "-A", "--", *paths)
    if r.returncode != 0:
        print("  ✗ git add 失败：%s" % (r.stderr or "").strip()[:200])
        return 1

    if git(git_exe, "diff", "--cached", "--quiet").returncode == 0:
        print("  构建产物与仓库一致，无需提交。")
    else:
        msg = "manual refresh: 一键刷新 %s" % datetime.now().strftime("%Y-%m-%d %H:%M")
        r = git(git_exe, "commit", "-m", msg)
        if r.returncode != 0:
            print("  ✗ git commit 失败：%s" % (r.stderr or "").strip()[:200])
            return 1
        print("  已提交：%s" % msg)
        r = git(git_exe, "push", "origin", "main")
        if r.returncode != 0:
            print("  ✗ git push 失败：%s" % (r.stderr or "").strip()[:200])
            return 1
        print("  已推送 origin/main，GitHub Pages 将自动部署。")

    # ---- 4) 口径回显 ----
    gi += 1
    step(gi, total, "本次数据口径")
    print_summary()

    print()
    hr()
    print("  完成")
    hr()
    print("  GitHub Pages：随推送自动更新（约 1-2 分钟）。")
    print("  托管管理台 supply-console.app.workbuddy.host：需重新发布才生效，")
    print("  回 WorkBuddy 说一句「发布」即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
