# -*- coding: utf-8 -*-
"""
配色换肤生成器（预览用）
输入：index.template.html
输出：preview_theme_A.html / preview_theme_B.html（单文件，内联 ECharts + 数据 + LOGO）

只改配色 + 加载页，不动任何布局、不变量名、不动数据逻辑。
"""
import os, re, sys, json, colorsys, base64

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(os.path.dirname(HERE), "assets", "logo-vayi.png")

# ---------------------------------------------------------------- 主题定义
# 显式映射：命中优先，覆盖所有高频色值（出现 >=2 次）
THEMES = {
    "A": {
        "name": "静水青绿",
        "hue": 174,        # 紫罗兰族 / 天蓝族 收敛到的目标色相
        "hue2": 338,       # 品红族 -> 灰玫瑰
        "map": {
            "#332F3A": "#26312F",  # text
            "#635F69": "#5C6B68",  # muted
            "#7C3AED": "#277A74",  # accent
            "#A78BFA": "#5FA69F",  # accent-light
            "#DB2777": "#AD5A76",  # accent-2 灰玫瑰
            "#6D28D9": "#1C5D58",
            "#5B21B6": "#164A46",
            "#C4B5FD": "#9BC7C0",
            "#EDE9FE": "#E4F0EE",
            "#DDD6FE": "#C9E2DE",
            "#F4F1FA": "#EEF3F2",  # bg
            "#EFEBF5": "#E5ECEA",  # recess
            "#10B981": "#3E9C7C",  # success
            "#EF4444": "#C9595B",  # danger
            "#F59E0B": "#C08F45",  # warn
            "#F97316": "#BE7A45",
            "#FCD34D": "#E4CE96",
            "#FCA5A5": "#E3B5B5",
            "#F9A8D4": "#DDBECB",
            "#0EA5E9": "#4E93B0",  # sky
            "#94A3B8": "#8FA3A8",
            "#6EE7B7": "#8FCFB2",
            "#B45309": "#8E6126",
        },
        "blobs": ["#5FB8AE", "#7FC0BC", "#6FA6C8", "#8CBFA0"],
        "blob_op": ".54",
        "bar_bg": "rgba(39,122,116,.14)",
        # 卡片五档：全部收在主色系内，只做细微色相/明度差
        "card": "linear-gradient(155deg,#FFFFFF 0%,#F3F9F8 52%,#F4F9F6 100%)",
        "g": ["linear-gradient(155deg,#FFFFFF 0%,#EAF3F1 55%,#DBEBE7 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EEF5F3 55%,#E0EFEC 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EAF2F6 55%,#DCEBF2 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EEF6EF 55%,#E3F1E5 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#F0F5F3 55%,#E5EEEC 100%)"],
        "warn": "linear-gradient(160deg, rgba(255,255,255,0.92), rgba(246,236,239,0.88))",
        "panel": "linear-gradient(160deg,#FFFFFF 0%,#F7FBFA 48%,#F8FAF5 100%)",
        "pal": ["#277A74", "#8FA9A0", "#4E93B0", "#B8935E", "#6BA8A8",
                "#B3737E", "#7A8FA8", "#96B88A", "#A88A6E", "#6B8E8A"],
        "pal_l": ["#9CC8C2", "#D2E0DA", "#A8C8DA", "#E0CDAE", "#BED8D8",
                  "#DEC3C8", "#C6D2DE", "#CBDFC2", "#D6C5B2", "#BFD6D2"],
        # 管理台（console/index.html）额外的靛蓝/中性色体系
        "map_console": {
            "#4F46E5": "#277A74", "#4338CA": "#1C5D58",
            "#0F172A": "#20302D", "#475569": "#4E605D", "#64748B": "#647874",
            "#F8FAFC": "#F2F7F6", "#EEF2FF": "#E7F2F0", "#F5F3FF": "#EAF4F2",
            "#E0E7FF": "#D6E8E4", "#3730A3": "#1B514C", "#A5B4FC": "#8FC0B9",
            "#E2E8F0": "#DFE9E7", "#F1F5F9": "#EAF1F0",
            "#16A34A": "#3D9770", "#DC2626": "#C05656", "#B91C1C": "#A34A4A",
            "#FECACA": "#EFC9C9", "#FEE2E2": "#F7E4E4", "#D1FAE5": "#DBEFE8",
            "#FEF3C7": "#F2E8D5", "#0F6E56": "#2A6357",
        },
    },
    "B": {
        "name": "远山蓝",
        "hue": 202,
        "hue2": 338,
        "map": {
            "#332F3A": "#242E38",
            "#635F69": "#5A6875",
            "#7C3AED": "#2E7BA6",
            "#A78BFA": "#6BA3C7",
            "#DB2777": "#AD5A76",
            "#6D28D9": "#20607F",
            "#5B21B6": "#1A4C66",
            "#C4B5FD": "#A3C4DC",
            "#EDE9FE": "#E4EDF4",
            "#DDD6FE": "#CBDCE9",
            "#F4F1FA": "#EDF1F6",
            "#EFEBF5": "#E3E9F0",
            "#10B981": "#41987F",
            "#EF4444": "#C9595B",
            "#F59E0B": "#C08F45",
            "#F97316": "#BE7A45",
            "#FCD34D": "#E4CE96",
            "#FCA5A5": "#E3B5B5",
            "#F9A8D4": "#DDBECB",
            "#0EA5E9": "#5A93B8",
            "#94A3B8": "#8FA0AE",
            "#6EE7B7": "#8FCFBB",
            "#B45309": "#8E6126",
        },
        "blobs": ["#6FA8CE", "#7FBFC4", "#4E93BE", "#8CBFA8"],
        "blob_op": ".54",
        "bar_bg": "rgba(46,123,166,.14)",
        "card": "linear-gradient(155deg,#FFFFFF 0%,#F4F8FB 52%,#F5FAF9 100%)",
        "g": ["linear-gradient(155deg,#FFFFFF 0%,#EAF1F7 55%,#DCE9F3 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EDF4F8 55%,#E2EEF6 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#E9F3F6 55%,#DAEDF3 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EDF5F1 55%,#E1EFE9 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#F1F5F8 55%,#E6EDF3 100%)"],
        "warn": "linear-gradient(160deg, rgba(255,255,255,0.92), rgba(246,236,239,0.88))",
        "panel": "linear-gradient(160deg,#FFFFFF 0%,#F6FAFD 48%,#F7FAF9 100%)",
        "pal": ["#2E7BA6", "#8FA9A0", "#B8935E", "#5FA6A6", "#B3737E",
                "#6B8E8A", "#8FA3B8", "#96B88A", "#A88A6E", "#7A9EB8"],
        "pal_l": ["#A8C6DC", "#D2E0DA", "#E0CDAE", "#BED8D8", "#DEC3C8",
                  "#BFD6D2", "#C6D2DE", "#CBDFC2", "#D6C5B2", "#B8CCDC"],
        "map_console": {
            "#4F46E5": "#2E7BA6", "#4338CA": "#20607F",
            "#0F172A": "#1B2631", "#475569": "#4A5A68", "#64748B": "#617283",
            "#F8FAFC": "#F1F6FA", "#EEF2FF": "#E6EEF6", "#F5F3FF": "#E9F1F7",
            "#E0E7FF": "#D5E3EF", "#3730A3": "#1B5573", "#A5B4FC": "#8FB4D2",
            "#E2E8F0": "#DEE7EF", "#F1F5F9": "#E9F0F5",
            "#16A34A": "#3D9770", "#DC2626": "#C05656", "#B91C1C": "#A34A4A",
            "#FECACA": "#EFC9C9", "#FEE2E2": "#F7E4E4", "#D1FAE5": "#DCEFE7",
            "#FEF3C7": "#F2E8D5", "#0F6E56": "#2A5F73",
        },
    },
    "C": {
        "name": "极光三色",
        "hue": 172,
        "hue2": 340,
        "map": {
            "#332F3A": "#1B3330",
            "#635F69": "#4E6B67",
            "#7C3AED": "#12877D",
            "#A78BFA": "#45C4B0",
            "#DB2777": "#D95F7C",
            "#6D28D9": "#0B665F",
            "#5B21B6": "#08534D",
            "#C4B5FD": "#9ADFD4",
            "#EDE9FE": "#E2F7F2",
            "#DDD6FE": "#C8EDE5",
            "#F4F1FA": "#EFF8F7",
            "#EFEBF5": "#E2F1EF",
            "#10B981": "#2E9B6A",
            "#EF4444": "#D64B4B",
            "#F59E0B": "#D39A3E",
            "#F97316": "#D27F3C",
            "#FCD34D": "#F0CE7E",
            "#FCA5A5": "#EFBFBF",
            "#F9A8D4": "#EFC0CF",
            "#0EA5E9": "#3AA0CC",
            "#94A3B8": "#93ADB4",
            "#6EE7B7": "#8FE0BC",
            "#B45309": "#9E6620",
        },
        "blobs": ["#5EDCC6", "#3FC6D6", "#4A9FE0", "#7FDC9C"],
        "blob_op": ".56",
        "bar_bg": "rgba(18,135,125,.13)",
        "card": "linear-gradient(155deg,#FFFFFF 0%,#F0FBF9 52%,#F2FBF6 100%)",
        "g": ["linear-gradient(155deg,#FFFFFF 0%,#E6F9F2 55%,#CFF2E4 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#E4F7F8 55%,#CBEEF1 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#E6F3FC 55%,#CDE8F8 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EAF9EC 55%,#D4F0D8 100%)",
              "linear-gradient(155deg,#FFFFFF 0%,#EDF8F6 55%,#D8EFEA 100%)"],
        "warn": "linear-gradient(160deg, rgba(255,255,255,0.94), rgba(255,240,244,0.90))",
        "panel": "linear-gradient(160deg,#FFFFFF 0%,#F6FCFB 48%,#F7FCF8 100%)",
        "pal": ["#12877D", "#45C4B0", "#2E9BC9", "#E0A44E", "#D95F7C",
                "#5FB8E0", "#7FD1A8", "#E8C48A", "#A8D96B", "#6ECBC4"],
        "pal_l": ["#8FDCCF", "#A8E6DA", "#A6D3EC", "#F0D5A8", "#EFB3C2",
                  "#B5DDF0", "#B8E6CC", "#F4E2C4", "#D9EDAE", "#B9E3DE"],
        "map_console": {
            "#4F46E5": "#12877D", "#4338CA": "#0B665F",
            "#0F172A": "#182F2C", "#475569": "#43605C", "#64748B": "#5A7A76",
            "#F8FAFC": "#F3FAF8", "#EEF2FF": "#E6F8F3", "#F5F3FF": "#E9F8F6",
            "#E0E7FF": "#D2F0E9", "#3730A3": "#0F625B", "#A5B4FC": "#8FDCCF",
            "#E2E8F0": "#DCEFEB", "#F1F5F9": "#E8F6F3",
            "#16A34A": "#2E9B6A", "#DC2626": "#D64B4B", "#B91C1C": "#B33A3A",
            "#FECACA": "#F5CBCB", "#FEE2E2": "#FBE8E8", "#D1FAE5": "#D2F2E4",
            "#FEF3C7": "#F8EBD0", "#0F6E56": "#1E6B58",
        },
    },
    "D": {
        "name": "LOGO 原色玻璃",
        "hue": 172,
        "hue2": 342,
        "glass": True,
        # 语义色一律保留原鲜艳值：降饱和会让橙/红发土，反而显得脏
        "map": {
            "#332F3A": "#16302D",
            "#635F69": "#5A736F",
            "#7C3AED": "#0E9E8E",
            "#A78BFA": "#4FD1C5",
            "#DB2777": "#E8547C",
            "#6D28D9": "#0B8878",
            "#5B21B6": "#087066",
            "#C4B5FD": "#A0E3DA",
            "#EDE9FE": "#E6F7F4",
            "#DDD6FE": "#CCEFE9",
            "#F4F1FA": "#F8FCFB",
            "#EFEBF5": "#ECF5F3",
            "#10B981": "#10B981",
            "#EF4444": "#EF4444",
            "#F59E0B": "#F59E0B",
            "#F97316": "#F97316",
            "#FCD34D": "#FCD34D",
            "#FCA5A5": "#FCA5A5",
            "#F9A8D4": "#F9A8D4",
            "#0EA5E9": "#0EA5E9",
            "#94A3B8": "#94A3B8",
            "#6EE7B7": "#6EE7B7",
            "#B45309": "#B45309",
        },
        # 直接用 LOGO 原始三色
        "blobs": ["#22B573", "#0071BC", "#109090", "#4FD1C5"],
        "blob_size": [52, 48, 50, 42],
        "blob_op": ".58",
        "blob_blur": 100,
        "bar_bg": "rgba(14,158,142,.16)",
        "card": "rgba(255,255,255,0.72)",
        "g": ["rgba(255,255,255,0.72)"] * 5,
        "warn": "rgba(255,249,243,0.94)",
        "panel": "rgba(255,255,255,0.70)",
        "pal": ["#12A08E", "#2FC98A", "#109090", "#5FD8C8", "#1E8FD0",
                "#7FC8F0", "#22B573", "#A0E8DC", "#0E9E9E", "#B8EDE6"],
        "pal_l": ["#A8E4D6", "#B4EFCC", "#A8DFDA", "#C8EDE4", "#B4DCF0",
                  "#D6EEFA", "#B0EAC8", "#DCF4EE", "#B4E6E6", "#E4F7F2"],
        "map_console": {
            "#4F46E5": "#0E9E8E", "#4338CA": "#0B8878",
            "#0F172A": "#16302D", "#475569": "#4A6B66", "#64748B": "#5A736F",
            "#F8FAFC": "#F8FCFB", "#EEF2FF": "#E8F7F4", "#F5F3FF": "#ECF8F6",
            "#E0E7FF": "#D4F0EA", "#3730A3": "#0B6F66", "#A5B4FC": "#9EE2D8",
            "#E2E8F0": "#E0F0EC", "#F1F5F9": "#EDF6F4",
            "#16A34A": "#10B981", "#DC2626": "#EF4444", "#B91C1C": "#DC2626",
            "#FECACA": "#FECACA", "#FEE2E2": "#FEE2E2", "#D1FAE5": "#D1FAE5",
            "#FEF3C7": "#FEF3C7", "#0F6E56": "#0F6E56",
        },
    },
}

def patch_surfaces(html, th):
    """卡片 / 面板 / 警示卡 / 图表色板：显式指定，不走色相算法"""
    def one(pat, repl):
        nonlocal html
        html, n = re.subn(pat, repl, html, count=1)
        if n == 0:
            sys.exit("未匹配: " + pat[:48])

    one(r"\.card\{background:linear-gradient\(155deg,[^;]*;",
        ".card{background:%s;" % th["card"])
    for i, g in enumerate(th["g"], start=1):
        one(r"\.card\.g%d\{background:linear-gradient\(155deg,[^;]*;\}" % i,
            ".card.g%d{background:%s;}" % (i, g))
    one(r"\.kpi-warn\{background:linear-gradient\(160deg,[^;]*;\}",
        ".kpi-warn{background:%s;}" % th["warn"])
    one(r"\.panel\{background:linear-gradient\(160deg,[^;]*;",
        ".panel{background:%s;" % th["panel"])

    js = lambda a: "[" + ",".join("'%s'" % x for x in a) + "]"
    one(r"var PALETTE = \[[^\]]*\];", "var PALETTE = %s;" % js(th["pal"]))
    one(r"var RING_PALETTE = \[[^\]]*\];", "var RING_PALETTE = %s;" % js(th["pal"][:8]))
    one(r"var PALETTE_LIGHT = \[[^\]]*\];", "var PALETTE_LIGHT = %s;" % js(th["pal_l"]))
    return html


def fallback(rgb, th):
    """未在显式表命中的色值：按色相族归并 + 降饱和；近灰色一律不动"""
    r, g, b = rgb
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    if s < 0.12:            # 灰阶（边框、底色、分隔线）保持原样，避免整体发脏
        return (r, g, b)
    H = h * 360
    if 245 <= H <= 302:
        H2, s2 = th["hue"], s * 0.62
    elif 302 < H <= 352:
        H2, s2 = th["hue2"], s * 0.58
    elif 175 <= H < 245:
        H2, s2 = th["hue"], s * 0.70
    elif 150 <= H < 175:
        H2, s2 = 160.0, s * 0.72
    elif 80 <= H < 150:
        H2, s2 = 140.0, s * 0.75
    else:
        H2, s2 = H, s * 0.82
    rr, gg, bb = colorsys.hls_to_rgb(H2 / 360.0, l, min(s2, 1.0))
    return (round(rr * 255), round(gg * 255), round(bb * 255))


def to_hex(t):
    return "#%02X%02X%02X" % t


def recolor(text, th, extra=None):
    lut = {k.upper(): v for k, v in th["map"].items()}
    if extra:
        lut.update({k.upper(): v for k, v in extra.items()})
    stats = {"explicit": 0, "fallback": 0, "rgb": 0}

    def hex_sub(m):
        hx = m.group(0).upper()
        if hx in lut:
            stats["explicit"] += 1
            return lut[hx]
        rgb = tuple(int(hx[1:][i:i + 2], 16) for i in (0, 2, 4))
        stats["fallback"] += 1
        return to_hex(fallback(rgb, th))

    text = re.sub(r"#[0-9A-Fa-f]{6}\b", hex_sub, text)

    def rgb_sub(m):
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hx = "#%02X%02X%02X" % (r, g, b)
        stats["rgb"] += 1
        out = lut.get(hx) or to_hex(fallback((r, g, b), th))
        tail = m.group(4) or ""
        if tail:
            return "rgba(%d,%d,%d%s)" % (int(out[1:3], 16), int(out[3:5], 16), int(out[5:7], 16), tail)
        return out

    text = re.sub(r"rgba?\((\d{1,3}), ?(\d{1,3}), ?(\d{1,3})(, ?[\d.]+)?\)", rgb_sub, text)
    return text, stats


BOOT_CSS = """  #boot{position:fixed;inset:0;z-index:200;display:flex;flex-direction:column;
    align-items:center;justify-content:center;background:var(--bg);
    transition:opacity .45s ease-out;overflow:hidden;}
  #boot::before,#boot::after{content:"";position:absolute;border-radius:50%;
    filter:blur(80px);pointer-events:none;}
  #boot::before{width:56vh;height:56vh;background:__B1__;opacity:.58;top:-16%;left:-12%;}
  #boot::after{width:50vh;height:50vh;background:__B3__;opacity:.52;bottom:-16%;right:-10%;}
  #boot.hide{opacity:0;pointer-events:none;}
  #boot .boot-in{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;}
  #boot .boot-logo{width:186px;height:auto;display:block;}
  #boot .bt{font-family:var(--f-head);font-weight:900;font-size:22px;color:var(--text);
    margin-top:16px;letter-spacing:.02em;}
  #boot .bs{font-size:12px;font-weight:700;letter-spacing:.22em;color:var(--muted);margin-top:3px;}
  #boot .bar{width:206px;height:5px;border-radius:3px;background:__BARBG__;
    margin-top:22px;overflow:hidden;}
  #boot .bar i{display:block;width:36%;height:100%;border-radius:3px;background:var(--grad);
    animation:bslide 1.25s ease-in-out infinite;}
  #boot .bst{margin-top:10px;font-size:13px;color:var(--muted);}
  @keyframes bslide{0%{transform:translateX(-105%)}100%{transform:translateX(300%)}}
  @keyframes bspin{to{transform:rotate(360deg)}}
"""


def patch_boot(html, th, logo_b64):
    """整段替换 #boot 的 CSS 与 DOM"""
    css = BOOT_CSS.replace("__B1__", th["blobs"][0]) \
                  .replace("__B3__", th["blobs"][2]) \
                  .replace("__BARBG__", th["bar_bg"])
    start = html.index("  #boot{")
    end = html.index("  #errbar{")
    html = html[:start] + css + html[end:]

    old_dom = '<div id="boot"><div class="sp"></div><div class="bt">供应链在途数据</div><div class="bs">正在加载数据与图表…</div></div>'
    new_dom = (
        '<div id="boot"><div class="boot-in">'
        '<img class="boot-logo" src="data:image/png;base64,' + logo_b64 + '" alt="华熠供应链">'
        '<div class="bt">供应链在途数据</div>'
        '<div class="bs">SUPPLY CHAIN BI</div>'
        '<div class="bar"><i></i></div>'
        '<div class="bst">正在加载数据与图表…</div>'
        '</div></div>'
    )
    if old_dom not in html:
        sys.exit("未找到加载页 DOM 原文，结构可能已变更")
    return html.replace(old_dom, new_dom)


GLASS_CSS = """
  /* ---- 底层：整页绿→白→蓝渐变，避免光斑形成割裂色块 ---- */
  html{background:linear-gradient(158deg,#DCF6EA 0%,#EFFBF7 26%,#F8FDFC 52%,#EDF6FD 78%,#DBEBFB 100%);}
  /* ---- 玻璃层：卡片半透明，让背后的 LOGO 色光斑真正透出来 ---- */
  .card,.panel,.filterbar,.drop,.seg,.drawer,.d-card{
    backdrop-filter:blur(28px) saturate(1.55);
    -webkit-backdrop-filter:blur(28px) saturate(1.55);}
  .card:hover{box-shadow:var(--clay-card-hover);}
"""

ROOT_EXTRA = """
    --bg:#F8FCFB; --panel:rgba(255,255,255,0.72); --recess:#ECF5F3;
    --text:#16302D; --muted:#587370; --dim:#587370;
    --accent:#0E9E8E; --accent-light:#4FD1C5; --accent-2:#E8547C;
    --grad:linear-gradient(135deg,#22B573 0%,#109090 52%,#0071BC 100%);
    --clay-card:
      0 18px 40px -12px rgba(18,94,88,0.20),
      0 3px 8px rgba(18,94,88,0.06),
      inset 0 1px 0 rgba(255,255,255,0.92);
    --clay-card-hover:
      0 28px 56px -14px rgba(18,94,88,0.28),
      0 6px 14px rgba(18,94,88,0.10),
      inset 0 1px 0 rgba(255,255,255,1);
    --clay-deep:
      0 34px 68px -18px rgba(18,94,88,0.26),
      inset 0 1px 0 rgba(255,255,255,0.95);
    --clay-btn:
      0 10px 22px -6px rgba(14,158,142,0.42),
      inset 0 1px 0 rgba(255,255,255,0.35);
    --clay-btn-hover:
      0 14px 28px -6px rgba(14,158,142,0.52),
      inset 0 1px 0 rgba(255,255,255,0.42);
"""


def patch_glass(html, th):
    """玻璃态：覆盖 surface/orange 变量，并给卡片挂上 backdrop-filter"""
    html = html.replace("--spec-w:130px;", "--spec-w:130px;" + ROOT_EXTRA, 1)
    html = html.replace("</style>", GLASS_CSS + "</style>", 1)
    return html


def patch_blobs(html, th):
    """精确覆盖四个背景光斑颜色（+ 可选尺寸）"""
    blur = th.get("blob_blur", 80)
    html = html.replace("filter:blur(80px);opacity:.44;",
                        "filter:blur(%dpx);opacity:%s;" % (blur, th["blob_op"]))
    sizes = th.get("blob_size")
    for i, color in enumerate(th["blobs"], start=1):
        if sizes:
            pat = re.compile(r"(\.clay-bg \.b%d\{)width:[^;]*;height:[^;]*;background:#[0-9A-Fa-f]{6}" % i)
            html, n = pat.subn(lambda m: "%swidth:%svh;height:%svh;background:%s" % (
                m.group(1), sizes[i - 1], sizes[i - 1], color), html)
            if n == 0:
                sys.exit("光斑 .b%d 尺寸未匹配到" % i)
            continue
        pat = re.compile(r"(\.clay-bg \.b%d\{[^}]*?background:)(#[0-9A-Fa-f]{6})" % i)
        html, n = pat.subn(lambda m: m.group(1) + color, html)
        if n == 0:
            sys.exit("光斑 .b%d 未匹配到" % i)
    return html


def main():
    tpl_path = os.path.join(HERE, "index.template.html")
    ec_path = os.path.join(HERE, "vendor", "echarts.min.js")
    data_path = os.path.join(HERE, "data.json")

    tpl = open(tpl_path, encoding="utf-8").read()
    echarts_src = open(ec_path, encoding="utf-8").read().replace("</script", "<\\/script")
    raw = open(data_path, encoding="utf-8").read().strip()
    if not raw.startswith("{"):
        raw = json.dumps(json.load(open(data_path, encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))
    data_tag = "<script>\nwindow.DATA = " + raw + ";\n</script>"
    echarts_tag = "<script>\n" + echarts_src + "\n</script>"

    logo_b64 = base64.b64encode(open(LOGO, "rb").read()).decode("ascii")

    for key, th in THEMES.items():
        out, stats = recolor(tpl, th)
        out = patch_surfaces(out, th)
        if th.get("glass"):
            out = patch_glass(out, th)
        out = patch_blobs(out, th)
        out = patch_boot(out, th, logo_b64)
        out = out.replace('src="console/index.html"', 'src="console/preview_%s.html"' % key)
        out = out.replace("<!--ECHARTS-->", echarts_tag).replace("<!--DATA-->", data_tag)
        dst = os.path.join(HERE, "preview_theme_%s.html" % key)
        open(dst, "w", encoding="utf-8").write(out)
        print("[%s] %s -> %s  (显式 %d / 兜底 %d / rgb %d)  %.2f MB" % (
            key, th["name"], os.path.basename(dst),
            stats["explicit"], stats["fallback"], stats["rgb"],
            os.path.getsize(dst) / 1024 / 1024))

        # 管理台（iframe 独立页面）同步换肤
        csrc = os.path.join(HERE, "console", "index.html")
        chtml, cstats = recolor(open(csrc, encoding="utf-8").read(), th, th.get("map_console"))
        cdst = os.path.join(HERE, "console", "preview_%s.html" % key)
        open(cdst, "w", encoding="utf-8").write(chtml)
        print("      管理台 -> console/%s  (显式 %d / 兜底 %d / rgb %d)" % (
            os.path.basename(cdst), cstats["explicit"], cstats["fallback"], cstats["rgb"]))


if __name__ == "__main__":
    main()
