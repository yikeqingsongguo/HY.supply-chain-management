#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""供应链看板 · 版本存档工具（标准库，零外部依赖）。

在每次较大幅度修改前/后运行：保存当前页面完整内容（index.html 快照）+ 产品交付说明，
写入 versions/vX.Y.Z_DATE/，并更新 INDEX.md 与记忆系统版本档案，可选 git push 上云。

用法：
  python archive_version.py --type baseline --title "初始基线"
  python archive_version.py --type before --title "改前：周计划表重构" --desc "..." --reason "..." --impact "..."
  python archive_version.py --type minor  --title "周计划表改为阴影曲线" --desc "..." --reason "..." --impact "..."
  python archive_version.py --type patch  --title "文案微调" --no-push

版本号语义化 vMAJOR.MINOR.PATCH，按最近一个版本目录自动 bump。
页面来源：优先抓取线上已部署页面（与用户看到的看板一致），失败 fallback 本地 index.html。
"""
import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent
VERSIONS_DIR = ROOT / "versions"
INDEX_MD = VERSIONS_DIR / "INDEX.md"
MEMORY_DIR = ROOT.parent / ".workbuddy" / "memory"
MEMORY_ARCHIVE = MEMORY_DIR / "VERSION_ARCHIVE.md"
PAGE_URL = "https://yikeqingsongguo.github.io/HY.supply-chain-management/"
ONLINE_TIMEOUT = 30

# 编码容错（Windows 控制台/重定向默认 GBK）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TYPE_LABEL = {
    "baseline": "基线", "major": "重大重构", "minor": "功能/较大改动",
    "patch": "小修/微调", "before": "改前快照", "after": "改后快照",
}


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def git_exe():
    cands = []
    base = Path.home() / ".workbuddy" / "binaries" / "PortableGit" / "versions"
    if base.exists():
        for d in sorted(base.iterdir(), reverse=True):
            for sub in ("cmd", "mingw64/bin"):
                p = d / sub / "git.exe"
                if p.exists():
                    cands.append(str(p))
    w = shutil.which("git")
    if w:
        cands.append(w)
    for c in cands:
        if c and Path(c).exists():
            return c
    return "git"


def find_latest_version_dir():
    if not VERSIONS_DIR.exists():
        return None
    dirs = [d for d in VERSIONS_DIR.iterdir()
            if d.is_dir() and re.match(r"^v\d+\.\d+\.\d+_", d.name)]
    if not dirs:
        return None
    def key(d):
        m = re.match(r"^v(\d+)\.(\d+)\.(\d+)_", d.name)
        return tuple(int(x) for x in m.groups())
    return max(dirs, key=key)


def bump_version(latest_dir, vtype):
    if latest_dir is None:
        return (1, 0, 0)
    m = re.match(r"^v(\d+)\.(\d+)\.(\d+)_", latest_dir.name)
    maj, minr, pat = (int(x) for x in m.groups())
    if vtype == "major":
        maj, minr, pat = maj + 1, 0, 0
    elif vtype == "minor":
        minr, pat = minr + 1, 0
    else:  # patch / baseline(已有历史时) / before / after
        pat += 1
    return (maj, minr, pat)


def fetch_online_page():
    try:
        req = Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=ONLINE_TIMEOUT) as r:
            data = r.read().decode("utf-8", errors="replace")
        log(f"已抓取线上页面（{len(data)} 字节）")
        return data
    except (URLError, HTTPError, OSError) as e:
        log(f"⚠️ 抓取线上页面失败：{e}")
        return None


def extract_updated_at(html):
    m = re.search(r'updated_at["\']?\s*[:=]\s*["\']?([^",}]+)', html)
    return m.group(1) if m else "unknown"


def local_index_html():
    p = ROOT / "index.html"
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return None


def page_source():
    html = fetch_online_page()
    if html:
        return html, "online"
    local = local_index_html()
    if local:
        log("使用本地 index.html 作为快照（线上抓取失败）")
        return local, "local"
    raise SystemExit("⛔ 无法获取页面快照：线上抓取失败且无本地 index.html，请先运行 build.py。")


def write_meta(p, version, date, vtype, title, desc, reason, impact, parent, updated_at):
    meta = {
        "version": version,
        "date": date,
        "type": vtype,
        "title": title,
        "description": desc,
        "reason": reason,
        "impact": impact,
        "data_updated_at": updated_at,
        "parent_version": parent,
        "page_file": "index.html",
        "author": "RE",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    (p / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def write_delivery_note(p, version, date, vtype, title, desc, reason, impact, parent, updated_at):
    label = TYPE_LABEL.get(vtype, vtype)
    content = f"""# 版本 {version} 交付说明

- 版本号：{version}
- 日期：{date}
- 类型：{label}
- 父版本：{parent or '无（初始基线）'}
- 页面数据快照（updated_at）：{updated_at}

## 本次修改内容
{desc or '（基线存档：记录初始稳定状态，无本次修改）'}

## 修改原因
{reason or '（基线存档：建立首个可追溯快照，作为后续对比基准）'}

## 影响范围
{impact or '（基线存档：全局页面，作为后续对比基准）'}

## 可恢复说明
本目录 `index.html` 为当时完整页面（含内联数据），直接用浏览器打开即可看到当时渲染的看板。
如需回滚源码，可 `git checkout` 对应提交或本版本目录。
"""
    (p / "delivery-note.md").write_text(content, encoding="utf-8")


def update_index_md(version, date, vtype, title, impact, relpath):
    label = TYPE_LABEL.get(vtype, vtype)
    row = f"| {version} | {date} | {label} | {title} | {impact or '-'} | [{version}]({relpath}) |\n"
    if not INDEX_MD.exists():
        INDEX_MD.write_text(
            "# 版本存档索引\n\n"
            "| 版本 | 日期 | 类型 | 摘要 | 影响范围 | 目录 |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8")
    with INDEX_MD.open("a", encoding="utf-8") as f:
        f.write(row)
    log(f"已更新 INDEX.md：{version}")


def update_memory_archive(version, date, vtype, title):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_ARCHIVE.exists():
        MEMORY_ARCHIVE.write_text(
            "# 看板版本存档（记忆系统索引）\n\n"
            "> 完整档案见 supply-dashboard/versions/ 与 GitHub 仓库（本地+云端双存）。\n\n",
            encoding="utf-8")
    line = f"- {version} ({date}) [{TYPE_LABEL.get(vtype, vtype)}] {title}\n"
    with MEMORY_ARCHIVE.open("a", encoding="utf-8") as f:
        f.write(line)
    log(f"已同步记忆系统：{MEMORY_ARCHIVE}")


def git_commit_push(version):
    g = git_exe()
    try:
        subprocess.run([g, "add", "-A", "--", "versions", "archive_version.py"],
                       cwd=str(ROOT), check=True,
                       capture_output=True, encoding="utf-8", errors="replace")
        diff = subprocess.run([g, "diff", "--cached", "--exit-code"],
                              cwd=str(ROOT), capture_output=True)
        if diff.returncode == 0:
            log("无变更，跳过提交")
            return
        subprocess.run([g, "commit", "-m", f"chore: 版本存档 {version}"],
                       cwd=str(ROOT), check=True,
                       capture_output=True, encoding="utf-8", errors="replace")
        subprocess.run([g, "push", "origin", "main"],
                       cwd=str(ROOT), check=True,
                       capture_output=True, encoding="utf-8", errors="replace")
        log("已提交并推送至 origin/main（云端已更新）")
    except subprocess.CalledProcessError as e:
        log(f"⛔ git 操作失败：{e}")
        raise


def main():
    ap = argparse.ArgumentParser(description="供应链看板版本存档工具")
    ap.add_argument("--type", default="patch",
                   choices=["major", "minor", "patch", "baseline", "before", "after"])
    ap.add_argument("--title", required=True, help="一句话摘要")
    ap.add_argument("--desc", default="", help="本次修改内容")
    ap.add_argument("--reason", default="", help="修改原因")
    ap.add_argument("--impact", default="", help="影响范围")
    ap.add_argument("--parent", default=None, help="父版本号（默认自动取上一版本）")
    ap.add_argument("--no-push", action="store_true", help="仅本地存档，不推送云端")
    args = ap.parse_args()

    VERSIONS_DIR.mkdir(exist_ok=True)
    latest = find_latest_version_dir()
    if args.type == "baseline" and latest is not None:
        log("⚠️ 已存在历史版本，baseline 仅用于首次；本次按 patch 递增，建议改用 major/minor/patch。")

    maj, minr, pat = bump_version(latest, args.type)
    version = f"{maj}.{minr}.{pat}"
    date = datetime.now().strftime("%Y-%m-%d")
    dirname = f"v{version}_{date}"
    vdir = VERSIONS_DIR / dirname
    if vdir.exists():
        i = 2
        while (VERSIONS_DIR / f"{dirname}_{i}").exists():
            i += 1
        dirname = f"{dirname}_{i}"
        vdir = VERSIONS_DIR / dirname
    vdir.mkdir(parents=True)

    html, src = page_source()
    (vdir / "index.html").write_text(html, encoding="utf-8")
    updated_at = extract_updated_at(html)
    parent = args.parent or (latest.name.split("_")[0] if latest else None)
    log(f"存档版本 {version}｜来源={src}｜数据快照={updated_at}｜目录={dirname}")

    write_meta(vdir, version, date, args.type, args.title, args.desc,
               args.reason, args.impact, parent, updated_at)
    write_delivery_note(vdir, version, date, args.type, args.title, args.desc,
                       args.reason, args.impact, parent, updated_at)
    rel = f"versions/{dirname}"
    update_index_md(version, date, args.type, args.title, args.impact, rel)
    update_memory_archive(version, date, args.type, args.title)
    log(f"✅ 本地存档完成：{vdir}")

    if args.no_push:
        log("（--no-push）未推送云端，请稍后手动 git push。")
    else:
        git_commit_push(version)


if __name__ == "__main__":
    main()
