# -*- coding: utf-8 -*-
"""
把 Google Fonts 的 latin 子集 woff2 下载并内联成 base64 @font-face，
输出 _fonts/fonts_inline.css（供单文件看板离线使用，零外链）。
仅保留 latin 子集（中文由系统字体兜底）。
Google 返回的是可变字体（同一文件覆盖多个字重）→ 按 URL 去重，用 font-weight 区间声明，避免重复内联。
"""
import os, re, base64, urllib.request, json

HERE = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.join(HERE, "_fonts")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 目标字重区间（可变字体一次声明到位）
RANGE = {"Nunito": "200 1000", "DM Sans": "100 1000"}

def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read() if binary else r.read().decode("utf-8")

seen = {}          # url -> b64
fam_url = {}       # family -> url（取第一个 latin 子集的 url）
for fname in ("nunito.css", "dmsans.css"):
    css = open(os.path.join(FDIR, fname), encoding="utf-8").read()
    for blk in re.findall(r"@font-face\s*\{(.*?)\}", css, flags=re.S):
        if "U+0000-00FF" not in blk:            # 只要 latin 子集
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", blk).group(1)
        url = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", blk).group(1)
        fam_url.setdefault(fam, url)

out, total = [], 0
for fam, url in fam_url.items():
    if url not in seen:
        data = fetch(url, binary=True)
        total += len(data)
        seen[url] = base64.b64encode(data).decode("ascii")
        print(f"  {fam}: {len(data):,} bytes  <- {url.rsplit('/',1)[-1]}")
    out.append(
        "@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
        "src:url(data:font/woff2;base64,%s) format('woff2');}"
        % (fam, RANGE.get(fam, "100 1000"), seen[url])
    )

css_out = "\n".join(out) + "\n"
open(os.path.join(FDIR, "fonts_inline.css"), "w", encoding="utf-8").write(css_out)
print(f"\n✅ {len(out)} 个 family / 去重后 {len(seen)} 个文件，原始 {total:,} bytes，CSS 产物 {len(css_out):,} 字符")
