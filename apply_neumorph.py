# -*- coding: utf-8 -*-
"""
把 index.template.html 整体迁移到 Neumorphism（Soft UI）设计系统：
1) 用 neumorph_css.css 替换 <style>...</style> 内容（只动样式层）
2) 对 </style> 之后的 HTML/JS 做图表颜色映射（旧浅蓝主题 -> 冷灰 Neumorphism 调色）
只改样式/颜色，不动数据结构与业务逻辑。
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
tpl_path  = os.path.join(HERE, "index.template.html")
css_path  = os.path.join(HERE, "neumorph_css.css")

tpl = open(tpl_path, encoding="utf-8").read()
css = open(css_path, encoding="utf-8").read().rstrip()

if "</style>" not in tpl:
    sys.exit("找不到 </style>")

idx = tpl.index("</style>")
pre, post = tpl[:idx], tpl[idx:]

# 1) 替换样式层
if "<style>" not in pre:
    sys.exit("找不到 <style>")
pre_new = re.sub(r"<style>.*", "<style>\n" + css + "\n", pre, flags=re.S)

# 2) HTML/JS 图表颜色映射（仅 </style> 之后）
COLOR_MAP = [
    ("#2563EB", "#6C63FF"), ("#1E40AF", "#5A52E0"), ("#1D4ED8", "#4B45C6"),
    ("#3B82F6", "#8B84FF"), ("#93C5FD", "#C3BFFB"), ("#DBEAFE", "#EEEDFE"),
    ("#DC2626", "#CE5A57"), ("#B91C1C", "#A8413E"),
    ("#059669", "#2FA98C"), ("#047857", "#1E7C77"),
    ("#D97706", "#C98A3E"), ("#B45309", "#8E5C1E"),
    ("#7C3AED", "#8B7BE8"), ("#0D9488", "#38B2AC"), ("#EA580C", "#D2834A"),
    ("#DB2777", "#C86C97"), ("#0891B2", "#4B9FB5"), ("#65A30D", "#7E9B6B"),
    ("#94A3B8", "#8894A6"), ("#64748B", "#6B7280"),
    ("#374151", "#3D4852"), ("#111827", "#3D4852"),
    ("#F3F4F6", "rgba(163,177,198,0.16)"), ("#F9FAFB", "#E0E5EC"),
    ("#E5E7EB", "rgba(163,177,198,0.45)"),
    ("rgba(37,99,235,.12)", "rgba(108,99,255,.14)"),
    ("rgba(37,99,235,0.12)", "rgba(108,99,255,0.14)"),
]

post_new = post
report = []
for old, new in COLOR_MAP:
    n = post_new.count(old)
    if n:
        post_new = post_new.replace(old, new)
        report.append(f"  {old} -> {new}  x{n}")

out = pre_new + post_new
open(tpl_path, "w", encoding="utf-8").write(out)

print("✅ 样式已替换为 Neumorphism，颜色映射完成：")
for r in report:
    print(r)
print(f"\n模板行数: {len(out.splitlines())}")
