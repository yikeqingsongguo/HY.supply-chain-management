# -*- coding: utf-8 -*-
"""Generate schematic SVG diagrams for the supply-chain dashboard usage guide.
Light 'clay' theme. No external deps. Each SVG: page layout + numbered click points.
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "imgs")
os.makedirs(OUT, exist_ok=True)

C = {
    "purple": "#7C3AED", "blue": "#0EA5E9", "green": "#10B981",
    "amber": "#F59E0B", "red": "#EF4444", "pink": "#DB2777",
    "ink": "#3A2E4D", "mut": "#7A7088", "line": "#E7E1F2",
    "bg": "#F4F1FA", "card": "#FFFFFF", "soft": "#EFEAFA",
}
FONT = "'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def svg(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'font-family="%s" font-size="13">' % (w, h, FONT)
            + '<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="7" refY="3.2" orient="auto">'
            + '<path d="M0,0 L8,3.2 L0,6.4 Z" fill="%s"/></marker></defs>' % C["red"]
            + '<rect width="%d" height="%d" fill="%s"/>' % (w, h, C["bg"]) + body + '</svg>')

def rect(x, y, w, h, fill=C["card"], stroke=C["line"], sw=1.5, r=14, extra=""):
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" ry="%g" fill="%s" '
            'stroke="%s" stroke-width="%g" %s/>' % (x, y, w, h, r, r, fill, stroke, sw, extra))

def txt(x, y, s, size=13, color=C["ink"], weight="600", anchor="start", extra=""):
    return ('<text x="%g" y="%g" font-size="%g" fill="%s" font-weight="%s" '
            'text-anchor="%s" %s>%s</text>' % (x, y, size, color, weight, anchor, extra, esc(s)))

def dot(x, y, color, r=6):
    return '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (x, y, r, color)

def panel(x, y, w, h, title, color=C["purple"], r=14):
    s = rect(x, y, w, h, r=r)
    s += rect(x, y, w, 30, fill=C["soft"], stroke="none", r=r)
    s += '<rect x="%g" y="%g" width="%g" height="15" fill="%s"/>' % (x, y + 15, w, C["soft"])
    s += dot(x + 16, y + 15, color)
    s += txt(x + 30, y + 20, title, size=13.5, color=C["ink"], weight="800")
    s += rect(x, y, w, h, fill="none", stroke=C["line"], sw=1.5, r=r)
    return s

def chip(x, y, label, color=C["purple"], active=False, w=None):
    w = w or (24 + len(label) * 13)
    fill = color if active else "#fff"
    fg = "#fff" if active else C["ink"]
    s = rect(x, y, w, 30, fill=fill, stroke=(color if not active else "none"), sw=1.5, r=15)
    s += txt(x + w / 2, y + 20, label, size=12.5, color=fg, weight="700", anchor="middle")
    return s

def arrow(x1, y1, x2, y2, color=C["red"], dash=False):
    d = 'stroke-dasharray="5 4" ' if dash else ""
    return ('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="2.4" '
            'marker-end="url(#ah)" %s/>' % (x1, y1, x2, y2, color, d))

def callout(x, y, n, label, color=C["red"], dx=16, dy=-6, anchor="start"):
    s = '<circle cx="%g" cy="%g" r="12" fill="%s"/>' % (x, y, color)
    s += txt(x, y + 4.5, n, size=13, color="#fff", weight="800", anchor="middle")
    lx = x + dx if anchor == "start" else x - dx
    s += txt(lx, y + dy + 4, label, size=12.5, color=color, weight="700", anchor=anchor)
    return s

def browser_bar(w):
    s = rect(0, 0, w, 30, fill="#ECE6F7", stroke="none", r=0)
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        s += '<circle cx="%g" cy="15" r="6" fill="%s"/>' % (22 + i * 18, c)
    s += rect(w / 2 - 170, 6, 340, 18, fill="#fff", stroke=C["line"], sw=1, r=9)
    s += txt(w / 2, 19, "supply-chain · 供应链在途数据看板", size=11, color=C["mut"], anchor="middle")
    return s

def topbar(w, active, tabs):
    s = rect(0, 30, w, 56, fill="#fff", stroke=C["line"], sw=1, r=0)
    s += dot(22, 58, C["purple"])
    s += txt(36, 64, "供应链在途数据", size=16, color=C["ink"], weight="800")
    s += txt(160, 64, "SUPPLY CHAIN BI", size=10, color=C["mut"], weight="700")
    # tabs
    tx = 320
    for t in tabs:
        tw = 96
        act = (t == active)
        if act:
            s += rect(tx, 44, tw, 30, fill=C["purple"], stroke="none", r=14)
            s += txt(tx + tw / 2, 64, t, size=13, color="#fff", weight="800", anchor="middle")
        else:
            s += txt(tx + tw / 2, 64, t, size=13, color=C["mut"], weight="700", anchor="middle")
        tx += tw
    s += txt(w - 18, 58, "数据:09-18 ｜ 数据源:采购订单.xlsx", size=10.5, color=C["mut"], anchor="end")
    return s

def filterbar(w, extra=False):
    s = rect(0, 86, w, 42, fill="#fff", stroke=C["line"], sw=1, r=0)
    items = ["供应商", "月份", "产线标签", "时效标签", "创建人"]
    if extra:
        items += ["物料名称", "SPU"]
    x = 16
    for it in items:
        ww = 30 + len(it) * 13
        s += rect(x, 94, ww, 26, fill=C["soft"], stroke=C["line"], sw=1, r=13)
        s += txt(x + ww / 2 - 6, 111, it, size=12, color=C["ink"], weight="700", anchor="middle")
        s += txt(x + ww - 14, 111, "▾", size=11, color=C["mut"], anchor="middle")
        x += ww + 8
    # search
    s += rect(x, 94, 200, 26, fill="#fff", stroke=C["line"], sw=1, r=13)
    s += txt(x + 12, 111, "🔍 搜索 单据号/物料/供应商…", size=11, color=C["mut"])
    x += 210
    s += rect(x, 94, 64, 26, fill=C["purple"], stroke="none", r=13)
    s += txt(x + 32, 111, "重置", size=12, color="#fff", weight="800", anchor="middle")
    return s

def chips_row(w):
    s = rect(0, 128, w, 30, fill="#F8F5FE", stroke="none", r=0)
    s += txt(16, 148, "已生效筛选：", size=11.5, color=C["mut"], weight="700")
    x = 96
    for lab, col in [("供应商：贝瑞卡 ×", C["purple"]), ("本月 ×", C["blue"]), ("核心供应商 ×", C["green"])]:
        ww = 30 + len(lab) * 12
        s += rect(x, 134, ww, 22, fill="#fff", stroke=col, sw=1.2, r=11)
        s += txt(x + 10, 149, lab, size=11, color=C["ink"], weight="700")
        x += ww + 8
    s += txt(x + 4, 149, "清除全部", size=11, color=C["red"], weight="800")
    return s

def page_title(title, color, show_month=True):
    s = dot(16, 180, color)
    s += txt(30, 186, title, size=18, color=C["ink"], weight="800")
    if show_month:
        mx = 980 - 16 - 150
        s += rect(mx, 166, 74, 30, fill=C["soft"], stroke=C["line"], sw=1, r=15)
        s += txt(mx + 37, 186, "本月", size=13, color="#fff", weight="800", anchor="middle")
        s += rect(mx + 76, 166, 74, 30, fill="#fff", stroke=C["line"], sw=1.2, r=15)
        s += txt(mx + 76 + 37, 186, "下月", size=13, color=C["mut"], weight="800", anchor="middle")
    return s

def bars(x, y, w, h, n, color, gap=10):
    s = ""
    bw = (w - gap * (n - 1)) / n
    for i in range(n):
        bh = h * (0.35 + 0.6 * ((i * 7 + 3) % n) / n)
        s += ('<rect x="%g" y="%g" width="%g" height="%g" rx="6" fill="%s"/>'
              % (x + i * (bw + gap), y + h - bh, bw, bh, color))
    return s

def hbars(x, y, w, h, n, color, gap=8):
    s = ""
    bh = (h - gap * (n - 1)) / n
    for i in range(n):
        bw = w * (0.5 + 0.5 * ((i * 5 + 2) % n) / n)
        s += ('<rect x="%g" y="%g" width="%g" height="%g" rx="7" fill="%s"/>'
              % (x, y + i * (bh + gap), bw, bh, color))
    return s

def donut(cx, cy, r, color):
    s = '<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="%g" opacity="0.9"/>' % (cx, cy, r, color, r * 0.9)
    s += '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx - r * 0.5, cy - r * 0.4, r * 0.32, "#fff")
    return s

def table_grid(x, y, w, h, ncol, nrow, color=C["purple"]):
    s = rect(x, y, w, h, r=10)
    rh = h / (nrow + 1)
    cw = w / ncol
    # header
    s += rect(x, y, w, rh, fill=color, stroke="none", r=10)
    s += '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>' % (x, y + rh / 2, w, rh / 2, color)
    for c in range(ncol):
        s += txt(x + cw * c + 10, y + rh - 6, "列%d" % (c + 1), size=10.5, color="#fff", weight="700")
    for r in range(nrow):
        for c in range(ncol):
            s += txt(x + cw * c + 10, y + rh * (r + 2) - 6, "·", size=10.5, color=C["mut"])
    return s

def drawer(x, y, w, h, lvl1, lvl2):
    s = rect(x, y, w, h, fill="#fff", stroke=C["line"], sw=2, r=18)
    s += rect(x, y, w, 46, fill=C["purple"], stroke="none", r=18)
    s += '<rect x="%g" y="%g" width="%g" height="23" fill="%s"/>' % (x, y + 23, w, C["purple"])
    s += txt(x + 16, y + 29, "‹ 返回", size=13, color="#fff", weight="800")
    s += txt(x + w / 2, y + 29, "钻取明细", size=13, color="#fff", weight="800", anchor="middle")
    s += txt(x + w - 24, y + 29, "✕", size=14, color="#fff", weight="800", anchor="middle")
    s += txt(x + 16, y + 66, lvl1, size=13, color=C["ink"], weight="800")
    s += txt(x + 16, y + 88, lvl2, size=11.5, color=C["mut"])
    s += table_grid(x + 14, y + 100, w - 28, h - 120, 3, 4, C["purple"])
    return s

# ---------------------------------------------------------------------------
W, H = 980, 660
TABS = ["在途概览", "供应商分析", "产能负荷", "周数据计划", "逾期分析", "交叉分析"]

def shell(active, title, color, show_month=True, show_filter=True, show_chips=True, subtitle=""):
    b = browser_bar(W)
    b += topbar(W, active, TABS)
    if show_filter:
        b += filterbar(W, extra=False)
    if show_chips:
        b += chips_row(W)
    b += page_title(title, color, show_month)
    if subtitle:
        b += txt(30, 206, subtitle, size=11.5, color=C["mut"])
    return b

def save(name, body):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg(W, H, body))
    print("wrote", name)

# 1) layout overview
def d_layout():
    b = shell("在途概览", "在途概览", C["purple"], subtitle="整体在途分布、供应商占比与逾期监控 · 点击图表元素可钻取明细")
    b += panel(16, 216, 300, 150, "KPI 卡片区（8 张）", C["purple"])
    b += bars(40, 250, 250, 90, 12, C["purple"], gap=8)
    b += panel(332, 216, 320, 210, "整体在途分布（柱状）", C["blue"])
    b += hbars(352, 250, 280, 150, 6, C["blue"])
    b += panel(668, 216, 296, 210, "Top8 占比（环形）", C["amber"])
    b += donut(816, 320, 70, C["amber"])
    b += panel(16, 382, 470, 250, "供应商月度订单表", C["green"])
    b += table_grid(36, 420, 430, 190, 4, 5, C["green"])
    b += panel(502, 382, 462, 250, "每日需交趋势（折线）", C["pink"])
    b += ('<path d="M520,600 C600,470 660,520 740,430 C800,360 860,400 940,330" '
          'stroke="%s" stroke-width="3" fill="none"/>' % C["pink"])
    # callouts
    b += callout(150, 250, "①", "标签页：切换 6 个页面（手机端变汉堡菜单）", dx=14)
    b += callout(120, 110, "②", "通用筛选条：供应商/月份/产线/时效/创建人/搜索/重置", dx=-110, anchor="end")
    b += callout(700, 142, "③", "筛选反馈 chips：可单独移除或一键清除", dx=14)
    b += callout(900, 180, "④", "本月/下月 开关（每页标题右侧，一处点击全站联动）", dx=-14, anchor="end")
    b += callout(770, 320, "⑤", "点击柱/扇区/折线点 → 右侧抽屉下钻", color=C["green"], dx=14)
    b += arrow(770, 332, 700, 360, C["green"])
    save("01-layout.svg", b)

# 2) filter bar + chips
def d_filter():
    b = shell("在途概览", "在途概览", C["purple"], show_month=False)
    b += txt(16, 250, "通用筛选条（所有页面共用，打开网页先看这里）", size=14, color=C["ink"], weight="800")
    # zoom filter bar
    b += rect(16, 270, 948, 120, fill="#fff", stroke=C["purple"], sw=2, r=14)
    items = [("供应商", C["purple"]), ("月份", C["blue"]), ("产线标签", C["green"]),
             ("时效标签", C["amber"]), ("创建人", C["pink"])]
    x = 36
    for it, col in items:
        ww = 30 + len(it) * 13
        b += rect(x, 300, ww, 34, fill=C["soft"], stroke=col, sw=1.4, r=15)
        b += txt(x + ww / 2 - 7, 322, it, size=13, color=C["ink"], weight="700", anchor="middle")
        b += txt(x + ww - 16, 322, "▾", size=12, color=col, anchor="middle")
        x += ww + 12
    b += rect(x, 300, 240, 34, fill="#fff", stroke=C["line"], sw=1.2, r=15)
    b += txt(x + 14, 322, "🔍 搜索 单据号/物料/供应商…", size=11.5, color=C["mut"])
    x += 252
    b += rect(x, 300, 70, 34, fill=C["purple"], stroke="none", r=15)
    b += txt(x + 35, 322, "重置", size=13, color="#fff", weight="800", anchor="middle")
    b += callout(150, 317, "①", "下拉多选，勾选即筛选；清空=全部", dx=14)
    b += callout(470, 317, "②", "月份下拉：选『本月/下月/全部』", dx=14, color=C["blue"])
    b += callout(770, 317, "③", "搜索框：跨字段模糊搜索", dx=14, color=C["green"])
    b += callout(910, 317, "④", "重置：一键清空所有筛选", dx=-14, anchor="end", color=C["amber"])
    # chips zoomed
    b += txt(16, 430, "筛选反馈 chips（已生效筛选实时显示，可单独移除）", size=14, color=C["ink"], weight="800")
    b += rect(16, 448, 948, 90, fill="#F8F5FE", stroke=C["line"], sw=1.5, r=14)
    b += txt(36, 478, "已生效筛选：", size=12, color=C["mut"], weight="700")
    x = 130
    for lab, col in [("供应商：贝瑞卡 ×", C["purple"]), ("本月 ×", C["blue"]), ("核心供应商 ×", C["green"])]:
        ww = 34 + len(lab) * 12
        b += rect(x, 462, ww, 26, fill="#fff", stroke=col, sw=1.4, r=13)
        b += txt(x + 12, 480, lab, size=11.5, color=C["ink"], weight="700")
        x += ww + 10
    b += txt(x + 6, 480, "清除全部", size=12, color=C["red"], weight="800")
    b += callout(180, 475, "⑤", "点 × 移除单项；或『清除全部』", dx=14, color=C["red"])
    b += callout(640, 510, "⑥", "无筛选时显示『当前无筛选』", dx=14, color=C["mut"])
    save("02-filter.svg", b)

# 3) month toggle + drawer
def d_drawer():
    b = shell("在途概览", "在途概览", C["purple"], show_filter=False, show_chips=False)
    b += txt(16, 250, "本月 / 下月 全局开关（每个页面标题右侧都有）", size=14, color=C["ink"], weight="800")
    b += rect(16, 268, 460, 70, fill="#fff", stroke=C["purple"], sw=2, r=14)
    b += txt(36, 300, "在途概览", size=16, color=C["ink"], weight="800")
    b += rect(360, 282, 70, 30, fill=C["purple"], stroke="none", r=15)
    b += txt(395, 302, "本月", size=13, color="#fff", weight="800", anchor="middle")
    b += rect(434, 282, 70, 30, fill="#fff", stroke=C["line"], sw=1.2, r=15)
    b += txt(469, 302, "下月", size=13, color=C["mut"], weight="800", anchor="middle")
    b += callout(395, 297, "①", "点『本月/下月』，全站联动切换统计月份", dx=14)
    b += txt(16, 380, "点击图表 / 表格 → 右侧抽屉两级下钻", size=14, color=C["ink"], weight="800")
    b += rect(16, 396, 470, 250, fill="#fff", stroke=C["line"], sw=1.5, r=14)
    b += txt(36, 426, "钻取明细（两级：订单汇总 → SKU 明细）", size=13, color=C["ink"], weight="800")
    b += table_grid(36, 444, 430, 180, 4, 4, C["purple"])
    b += callout(120, 470, "②", "点柱体/扇区/表格行，打开抽屉", dx=14, color=C["green"])
    b += drawer(540, 396, 424, 250, "订单汇总：CGDD012512（12 行 / 8 SPU）", "点击某行 → 展开该订单的 SKU 明细")
    b += arrow(486, 520, 540, 520, C["purple"])
    b += callout(640, 430, "③", "‹ 返回上一级；✕ 关闭抽屉", dx=14, color=C["purple"])
    b += callout(640, 540, "④", "两级：订单汇总 → SKU 明细", dx=14, color=C["pink"])
    save("03-month-drawer.svg", b)

# 4) overview page
def d_overview():
    b = shell("在途概览", "在途概览", C["purple"], subtitle="整体在途分布、供应商占比与逾期监控 · 点击图表元素可钻取明细")
    b += panel(16, 218, 948, 96, "KPI 卡片（8 张：总计划/剩余/完成率/供应商数/逾期供应商/逾期订单/逾期数量/逾期天数）", C["purple"])
    for i in range(8):
        col = [C["blue"], C["amber"], C["green"], C["purple"], C["red"], C["red"], C["red"], C["red"]][i]
        b += rect(30 + i * 116, 252, 104, 50, fill=C["soft"], stroke="none", r=10)
        b += txt(30 + i * 116 + 52, 280, "指标%d" % (i + 1), size=11, color=col, weight="800", anchor="middle")
    b += panel(16, 330, 470, 250, "整体在途分布（柱图·核心/普通切换）", C["blue"])
    b += hbars(36, 366, 430, 190, 7, C["blue"])
    b += panel(502, 330, 462, 250, "Top8 占比（环形·在途剩余/已收料/采购总量切换）", C["amber"])
    b += donut(733, 455, 78, C["amber"])
    b += panel(16, 596, 470, 50, "供应商月度订单表（本月/下月数字可点击）", C["green"])
    b += panel(502, 596, 462, 50, "每日需交趋势（折线·本月/下月切换）", C["pink"])
    b += callout(900, 200, "①", "标题右侧『本月/下月』联动本页所有图", dx=-14, anchor="end", color=C["blue"])
    b += callout(260, 366, "②", "核心/普通 切换；点柱体下钻订单→SKU", dx=14, color=C["blue"])
    b += callout(733, 455, "③", "点扇区切换口径；点扇区下钻供应商", dx=14, color=C["amber"])
    b += callout(250, 620, "④", "点月份数字下钻该月供应商明细", dx=14, color=C["green"])
    b += callout(733, 620, "⑤", "点数据点下钻当日订单明细", dx=14, color=C["pink"])
    save("04-page-overview.svg", b)

# 5) supplier page
def d_supplier():
    b = shell("供应商分析", "供应商数据分析", C["blue"], subtitle="按产线分类的订单分布、气泡对比与产线收料负荷")
    b += panel(16, 218, 948, 64, "KPI（4 张：订单行数/采购总量/已完成·在途/逾期订单） + 单据类型：全部/标准采购/VMI", C["blue"])
    for i in range(4):
        b += rect(30 + i * 230, 244, 210, 26, fill=C["soft"], stroke="none", r=10)
    b += panel(16, 296, 470, 230, "各供应商分类订单·按产线（柱图）", C["blue"])
    b += bars(36, 332, 430, 170, 9, C["blue"], gap=12)
    b += panel(502, 296, 462, 230, "占比/订单气泡图（X=计划量 Y=剩余 气泡=订单数）", C["purple"])
    b += ('<circle cx="600" cy="420" r="34" fill="%s" opacity="0.85"/><circle cx="720" cy="380" r="22" fill="%s" opacity="0.85"/>'
          '<circle cx="800" cy="450" r="40" fill="%s" opacity="0.85"/><circle cx="880" cy="400" r="18" fill="%s" opacity="0.85"/>'
          % (C["green"], C["amber"], C["blue"], C["pink"]))
    b += panel(16, 540, 948, 110, "各产线收料与负荷汇总表 / 时效标签收料与负荷汇总表（点『详情』下钻）", C["green"])
    b += table_grid(36, 566, 908, 70, 6, 2, C["green"])
    b += callout(250, 332, "①", "点产线柱体下钻 供应商→SKU", dx=14, color=C["blue"])
    b += callout(720, 420, "②", "产线/时效 口径切换；点气泡下钻", dx=14, color=C["purple"])
    b += callout(490, 600, "③", "点『详情』下钻该产线/时效订单", dx=14, color=C["green"])
    save("05-page-supplier.svg", b)

# 6) capacity page
def d_capacity():
    b = shell("产能负荷", "产能负荷分析", C["green"], subtitle="负荷率 = 该月在途(剩余收料) ÷ 供应商月产能；由顶部月份开关控制")
    b += panel(16, 218, 470, 220, "产能负荷率分布（点击区间联动右侧）", C["green"])
    b += bars(36, 254, 430, 160, 7, C["green"], gap=12)
    b += panel(502, 218, 462, 220, "负荷率详情（联动表）", C["blue"])
    b += table_grid(522, 254, 422, 160, 3, 4, C["blue"])
    b += panel(16, 452, 948, 120, "供应商产能负荷状态分布（超额/饱和/空闲） + 核心vs普通占比 + 占比排序", C["amber"])
    b += bars(36, 486, 300, 70, 6, C["red"], gap=10)
    b += donut(470, 540, 36, C["purple"])
    b += hbars(560, 486, 380, 70, 5, C["amber"], gap=8)
    b += callout(250, 254, "①", "点负荷率区间→右侧详情表联动", dx=14, color=C["green"])
    b += callout(490, 200, "②", "顶部月份 + 核心/普通 控制本页口径", dx=14, color=C["blue"])
    b += callout(300, 520, "③", ">100%超额 / 80-100%饱和 / <80%空闲", dx=14, color=C["red"])
    save("06-page-capacity.svg", b)

# 7) weekly page
def d_weekly():
    b = shell("周数据计划", "周数据计划", C["amber"], subtitle="合计（在途剩余 + 周计划）按分界值分组；图A/图B 独立比例尺；点击柱体下钻")
    b += rect(16, 218, 948, 40, fill="#fff", stroke=C["line"], sw=1.5, r=12)
    b += txt(30, 244, "分界值：合计 ≥", size=12.5, color=C["ink"], weight="700")
    b += rect(150, 226, 70, 24, fill=C["soft"], stroke=C["line"], sw=1, r=8)
    b += txt(185, 243, "5000", size=12, color=C["ink"], anchor="middle")
    b += txt(240, 244, "归入图 A（≥），< 归入图 B；步长 500", size=11.5, color=C["mut"])
    b += rect(760, 224, 180, 28, fill=C["amber"], stroke="none", r=13)
    b += txt(850, 243, "导入周计划文件…", size=11.5, color="#fff", weight="800", anchor="middle")
    b += panel(16, 272, 470, 250, "图 A：合计 ≥ 分界值（堆叠柱）", C["amber"])
    b += bars(36, 308, 430, 180, 8, C["amber"], gap=12)
    b += panel(502, 272, 462, 250, "图 B：合计 < 分界值（堆叠柱）", C["blue"])
    b += bars(522, 308, 422, 180, 8, C["blue"], gap=12)
    b += panel(16, 536, 948, 110, "各供应商本周计划数量汇总表（点行 → SPU → SKU）", C["green"])
    b += table_grid(36, 562, 908, 70, 5, 2, C["green"])
    b += callout(150, 238, "①", "调分界值，图 A/B 重新分组", dx=14, color=C["amber"])
    b += callout(850, 238, "②", "导入新一周周计划 .xlsx", dx=14, color=C["blue"])
    b += callout(250, 308, "③", "点柱体下钻 SPU→SKU", dx=14, color=C["amber"])
    b += callout(490, 600, "④", "点行下钻供应商本周计划明细", dx=14, color=C["green"])
    save("07-page-weekly.svg", b)

# 8) overdue page
def d_overdue():
    b = shell("逾期分析", "逾期分析", C["red"], subtitle="逾期供应商、逾期订单、逾期数量与逾期天数统计；点击行/柱下钻明细")
    b += panel(16, 218, 948, 70, "逾期 KPI（4 张：逾期供应商数/逾期订单数/逾期数量/最大·平均逾期天数）", C["red"])
    for i in range(4):
        b += rect(30 + i * 230, 240, 210, 34, fill="#FDECEC", stroke=C["red"], sw=1.2, r=10)
    b += panel(16, 302, 470, 200, "逾期供应商数量 TOP（横向柱）", C["red"])
    b += hbars(36, 334, 430, 150, 6, C["red"])
    b += panel(502, 302, 462, 200, "逾期天数分布", C["amber"])
    b += bars(522, 338, 422, 140, 7, C["amber"], gap=10)
    b += panel(16, 516, 948, 130, "逾期供应商汇总表（一行一家，默认逾期数量降序，可筛选；点行展开明细）", C["pink"])
    b += table_grid(36, 544, 908, 84, 6, 2, C["pink"])
    b += callout(250, 334, "①", "点柱体下钻该供应商逾期明细", dx=14, color=C["red"])
    b += callout(490, 600, "②", "点行展开该供应商逾期明细", dx=14, color=C["pink"])
    b += callout(900, 200, "③", "本页刻意保持全量，不跟随本月/下月", dx=-14, anchor="end", color=C["mut"])
    save("08-page-overdue.svg", b)

# 9) cross page
def d_cross():
    b = shell("交叉分析", "交叉分析", C["pink"], subtitle="全局切片器联动：供应商 × 本月/下月 热力图与工厂逾期 TOP，可逐层钻取")
    b += rect(16, 218, 948, 40, fill="#fff", stroke=C["line"], sw=1.5, r=12)
    b += txt(30, 244, "热力图供应商显示：", size=12.5, color=C["ink"], weight="700")
    b += chip(180, 226, "TOP 20", C["pink"], active=True)
    b += chip(270, 226, "全部", C["pink"])
    b += chip(340, 226, "仅核心", C["pink"])
    b += panel(16, 272, 948, 250, "交叉分析热力图 · 供应商 × 本月/下月（剩余收料数量，颜色越深越多）", C["pink"])
    # heat grid
    gx, gy, cw, ch = 40, 300, 70, 22
    for r in range(8):
        for c in range(2):
            v = (r * 7 + c * 3) % 10
            op = 0.15 + v * 0.08
            b += ('<rect x="%g" y="%g" width="%g" height="%g" rx="4" fill="%s" opacity="%g"/>'
                  % (gx + c * (cw + 30), gy + r * (ch + 4), cw, ch, C["pink"], op))
    b += txt(gx, gy - 8, "本月", size=11, color=C["mut"], weight="700")
    b += txt(gx + cw + 30, gy - 8, "下月", size=11, color=C["mut"], weight="700")
    b += panel(16, 536, 948, 110, "工厂逾期数量 TOP（点柱体下钻该供应商逾期明细）", C["red"])
    b += hbars(36, 568, 430, 60, 5, C["red"], gap=6)
    b += callout(120, 320, "①", "TOP20/全部/仅核心 切换显示范围", dx=14, color=C["pink"])
    b += callout(450, 360, "②", "点单元格下钻该供应商当月明细", dx=14, color=C["pink"])
    b += callout(250, 600, "③", "点柱体下钻工厂逾期明细", dx=14, color=C["red"])
    b += callout(900, 200, "④", "本页刻意保持双月对比，不跟随开关", dx=-14, anchor="end", color=C["mut"])
    save("09-page-cross.svg", b)

# 10) table ops
def d_table():
    b = shell("在途概览", "在途概览", C["purple"], show_month=False)
    b += txt(16, 250, "全局下钻明细表：表头可排序、关键列可列内筛选，自动带『完成进度』列", size=14, color=C["ink"], weight="800")
    b += rect(16, 270, 948, 320, fill="#fff", stroke=C["purple"], sw=2, r=14)
    cols = ["供应商", "本月", "下月", "合计", "完成进度 ▲▼", "状态 ▾"]
    cw = 948 / len(cols)
    b += rect(16, 270, 948, 38, fill=C["purple"], stroke="none", r=14)
    b += '<rect x="16" y="289" width="948" height="19" fill="%s"/>' % C["purple"]
    for i, c in enumerate(cols):
        col = C["red"] if "▲▼" in c or "▾" in c else "#fff"
        w8 = 14 if ("▲▼" in c or "▾" in c) else 0
        b += txt(16 + cw * i + 12, 295, c, size=12.5, color=col, weight="800")
    for r in range(6):
        yy = 320 + r * 44
        if r % 2 == 0:
            b += rect(20, yy, 940, 40, fill="#F8F5FE", stroke="none", r=8)
        for i in range(len(cols)):
            b += txt(28 + cw * i, yy + 26, "数据", size=11.5, color=C["mut"])
    b += callout(640, 290, "①", "点表头 ▲▼ 升/降序排序", dx=14, color=C["red"])
    b += callout(880, 290, "②", "关键列 ▾ 打开列内勾选筛选", dx=-14, anchor="end", color=C["red"])
    b += callout(360, 560, "③", "『完成进度』列自动计算（未满100%保留1位小数）", dx=14, color=C["green"])
    save("10-table.svg", b)

if __name__ == "__main__":
    d_layout(); d_filter(); d_drawer(); d_overview(); d_supplier()
    d_capacity(); d_weekly(); d_overdue(); d_cross(); d_table()
    print("ALL DONE")
