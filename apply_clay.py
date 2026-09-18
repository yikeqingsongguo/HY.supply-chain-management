# -*- coding: utf-8 -*-
"""
把 index.template.html 迁移到 High-Fidelity Claymorphism 设计系统：
1) <style> 内容 = 内联字体(_fonts/fonts_inline.css) + clay_css.css
2) </style> 之后的 HTML/JS 做图表颜色映射（Neumorphism 冷灰 -> Clay 糖果色）
3) <body> 后注入 4 个动画光斑 .clay-bg
4) 概览页布局：柱状图取消全宽，与 Top8 环形图同排；月度订单表改为全宽
只改样式/颜色/布局，不动数据结构与业务逻辑。
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
tpl_path  = os.path.join(HERE, "index.template.html")
css_path  = os.path.join(HERE, "clay_css.css")
font_path = os.path.join(HERE, "_fonts", "fonts_inline.css")

tpl  = open(tpl_path,  encoding="utf-8").read()
css  = open(css_path,  encoding="utf-8").read().rstrip()
font = open(font_path, encoding="utf-8").read().rstrip()
style_block = "/* ==== inlined latin subsets: Nunito + DM Sans (variable) ==== */\n" + font + "\n\n" + css

if "</style>" not in tpl or "<style>" not in tpl:
    sys.exit("找不到 <style> / </style>")
idx = tpl.index("</style>")
pre, post = tpl[:idx], tpl[idx:]
pre_new = re.sub(r"<style>.*", "<style>\n" + style_block + "\n", pre, flags=re.S)

report = []

# ---- 2) 图表颜色映射（Neumorphism -> Clay 糖果色）----
COLOR_MAP = [
    ("#3D4852", "#332F3A"), ("#6C63FF", "#7C3AED"), ("#CE5A57", "#EF4444"),
    ("#6B7280", "#635F69"), ("#2FA98C", "#10B981"), ("#C98A3E", "#F59E0B"),
    ("#8B7BE8", "#A78BFA"), ("#38B2AC", "#0EA5E9"), ("#D2834A", "#F97316"),
    ("#C86C97", "#DB2777"), ("#8894A6", "#94A3B8"), ("#4B9FB5", "#06B6D4"),
    ("#7E9B6B", "#84CC16"), ("#F4F7FB", "#FFFFFF"), ("#EEEDFE", "#F3E8FF"),
    ("#C3BFFB", "#DDD6FE"), ("#8B84FF", "#A78BFA"), ("#4B45C6", "#6D28D9"),
    ("rgba(163,177,198,0.45)", "rgba(124,58,237,0.12)"),
    ("rgba(163,177,198,0.7)",  "rgba(124,58,237,0.22)"),
    ("rgba(108,99,255,.14)",   "rgba(124,58,237,.14)"),
]
for old, new in COLOR_MAP:
    n = post.count(old)
    if n:
        post = post.replace(old, new)
        report.append(f"  {old} -> {new}  x{n}")

# ---- 3) 注入背景光斑（幂等）----
if "clay-bg" not in post:
    blobs = ('<div class="clay-bg" aria-hidden="true">'
             '<span class="blob b1"></span><span class="blob b2"></span>'
             '<span class="blob b3"></span><span class="blob b4"></span></div>\n')
    if "<body>\n" in post:
        post = post.replace("<body>\n", "<body>\n" + blobs, 1)
    else:
        post = post.replace("<body>", "<body>\n" + blobs, 1)
    report.append("  + 注入 .clay-bg 背景光斑 x1")

# ---- 4) 概览页布局：柱状图取消全宽，与环形图同排；月度表全宽 ----
LAYOUT = [
    ('<div class="panel" style="grid-column:1/-1">\n      <h3>整体在途分布</h3>',
     '<div class="panel">\n      <h3>整体在途分布</h3>', "柱状图取消全宽 grid-column:1/-1"),
    ('<div class="panel">\n      <h3>供应商月度订单数据</h3>',
     '<div class="panel" style="grid-column:1/-1">\n      <h3>供应商月度订单数据</h3>', "月度订单表改全宽"),
]
for old, new, desc in LAYOUT:
    n = post.count(old)
    if n != 1:
        report.append(f"  !! 布局锚点命中 {n} 次（应为 1）: {desc}")
    else:
        post = post.replace(old, new, 1)
        report.append(f"  ✓ {desc}")

open(tpl_path, "w", encoding="utf-8").write(pre_new + post)
print("✅ Claymorphism 迁移完成：")
for r in report:
    print(r)
print(f"\n模板行数: {len((pre_new+post).splitlines())}")
