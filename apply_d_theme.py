# -*- coding: utf-8 -*-
"""把 D 版配色一次性写入真身（index.template.html + console/index.html）。
只跑一次；之后所有功能改动直接改真身，不再依赖换色脚本。
"""
import os, io, base64
import recolor_preview as R

HERE = R.HERE
DST_TPL = os.path.join(HERE, "index.template.html")
DST_CON = os.path.join(HERE, "console", "index.html")

th = R.THEMES["D"]
logo_b64 = base64.b64encode(open(R.LOGO, "rb").read()).decode("ascii")

# ---- 主看板 ----
tpl = io.open(DST_TPL, encoding="utf-8").read()
assert "--spec-w:130px;" in tpl and "#boot{" in tpl, "模板结构不符，已中止"
out, st = R.recolor(tpl, th)
out = R.patch_surfaces(out, th)
out = R.patch_glass(out, th)
out = R.patch_blobs(out, th)
out = R.patch_boot(out, th, logo_b64)
io.open(DST_TPL, "w", encoding="utf-8").write(out)
print("index.template.html 已更新  显式%d/兜底%d/rgb%d  %.1f KB" % (
    st["explicit"], st["fallback"], st["rgb"], os.path.getsize(DST_TPL) / 1024))

# ---- 管理台 ----
con = io.open(DST_CON, encoding="utf-8").read()
cout, cst = R.recolor(con, th, th["map_console"])
io.open(DST_CON, "w", encoding="utf-8").write(cout)
print("console/index.html 已更新  显式%d/兜底%d/rgb%d  %.1f KB" % (
    cst["explicit"], cst["fallback"], cst["rgb"], os.path.getsize(DST_CON) / 1024))
