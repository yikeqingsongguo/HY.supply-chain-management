# -*- coding: utf-8 -*-
"""
第 2 批（视觉 18–22 + 响应式/动画）：
1) 标题改名「供应链在途数据」（<title> + .brand）
2) 全局字体 +2px（逐条精确替换，命中数必须为 1）
3) 6 个页面标题放大 + 内联 SVG 卡通图标
4) 追加 CSS：图表卡片悬停、表格行悬停、标签悬停、响应式不溢出、淡入/浮动动画
"""
import io, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "index.template.html")
s = io.open(P, encoding="utf-8").read()
report = []


def rep1(old, new, label):
    global s
    n = s.count(old)
    if n == 1:
        s = s.replace(old, new, 1); report.append("  OK  " + label)
    else:
        report.append("  !!  %s 命中 %d 次（应为 1）" % (label, n))


# ---------- 1) 标题改名 ----------
rep1("<title>箱包外贸采购 · 供应链在途+产能看板</title>", "<title>供应链在途数据</title>", "title 标签")
rep1('class="brand">箱包外贸采购 · 供应链在途+产能<small>', 'class="brand">供应链在途数据<small>', "brand 文案")

# ---------- 2) 字体 +2px ----------
FONTS = [
    ("font-size:15px;font-weight:500;line-height:1.6;", "font-size:17px;font-weight:500;line-height:1.65;", "body 15→17"),
    (".brand{font-size:19px;", ".brand{font-size:21px;", "brand 19→21"),
    (".topmeta{margin-left:auto;color:var(--dim);font-size:12px;", ".topmeta{margin-left:auto;color:var(--dim);font-size:14px;", "topmeta 12→14"),
    (".page-sub{color:var(--muted);font-size:14px;", ".page-sub{color:var(--muted);font-size:16px;", "page-sub 14→16"),
    ("cursor:pointer;font-size:13px;font-weight:700;letter-spacing:.01em;user-select:none;white-space:nowrap;", "cursor:pointer;font-size:15px;font-weight:700;letter-spacing:.01em;user-select:none;white-space:nowrap;", "tab 13→15"),
    ("min-height:44px;display:flex;align-items:center;color:var(--muted);font-size:13px;font-weight:700;user-select:none;", "min-height:44px;display:flex;align-items:center;color:var(--muted);font-size:15px;font-weight:700;user-select:none;", "summary 13→15"),
    (".drop .drop-title{font-family:var(--f-head);font-size:13px;", ".drop .drop-title{font-family:var(--f-head);font-size:15px;", "drop-title 13→15"),
    ("padding:8px 10px;border-radius:var(--r-s);font-size:13px;font-weight:500;", "padding:8px 10px;border-radius:var(--r-s);font-size:15px;font-weight:500;", "drop label 13→15"),
    ("color:var(--text);padding:13px 18px;font-size:13px;font-weight:500;font-family:var(--f-body);outline:none;", "color:var(--text);padding:13px 18px;font-size:15px;font-weight:500;font-family:var(--f-body);outline:none;", "fsearch 13→15"),
    ("cursor:pointer;font-family:var(--f-body);\n    font-size:13px;font-weight:700;letter-spacing:.01em;user-select:none;", "cursor:pointer;font-family:var(--f-body);\n    font-size:15px;font-weight:700;letter-spacing:.01em;user-select:none;", "btn 13→15"),
    (".seg span{padding:9px 16px;font-size:13px;", ".seg span{padding:9px 16px;font-size:15px;", "seg span 13→15"),
    (".seg.seg-sm span{padding:7px 14px;font-size:12px;}", ".seg.seg-sm span{padding:7px 14px;font-size:14px;}", "seg-sm 12→14"),
    (".ctl-inline .lab{color:var(--muted);font-size:13px;", ".ctl-inline .lab{color:var(--muted);font-size:15px;", "ctl lab 13→15"),
    ("padding:12px 15px;font-size:14px;font-weight:800;font-family:var(--f-head);outline:none;", "padding:12px 15px;font-size:16px;font-weight:800;font-family:var(--f-head);outline:none;", "numin 14→16"),
    (".card .lab{color:var(--muted);font-size:13px;", ".card .lab{color:var(--muted);font-size:15px;", "card lab 13→15"),
    (".card .val{font-size:30px;", ".card .val{font-size:34px;", "card val 30→34"),
    (".card .hint{color:var(--dim);font-size:11px;", ".card .hint{color:var(--dim);font-size:13px;", "card hint 11→13"),
    (".panel h3{margin:0 0 8px;font-size:18px;", ".panel h3{margin:0 0 8px;font-size:22px;", "panel h3 18→22"),
    (".panel .ph-sub{color:var(--muted);font-size:12px;", ".panel .ph-sub{color:var(--muted);font-size:14px;", "ph-sub 12→14"),
    ("table.t{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;", "table.t{width:100%;border-collapse:separate;border-spacing:0;font-size:15px;", "table 13→15"),
    (".legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12px;", ".legend{display:flex;flex-wrap:wrap;gap:16px;font-size:14px;", "legend 12→14"),
    ("border-radius:9999px;font-size:11px;font-weight:700;box-shadow:var(--clay-pressed-s);", "border-radius:9999px;font-size:13px;font-weight:700;box-shadow:var(--clay-pressed-s);", "tag 11→13"),
    (".crumbs{padding:12px 26px;font-size:12px;", ".crumbs{padding:12px 26px;font-size:14px;", "crumbs 12→14"),
    (".drawer .dh .t{font-family:var(--f-head);font-size:20px;", ".drawer .dh .t{font-family:var(--f-head);font-size:24px;", "drawer title 20→24"),
    (".drawer .df{padding:16px 26px;font-size:13px;", ".drawer .df{padding:16px 26px;font-size:15px;", "drawer foot 13→15"),
    (".d-card .d-lab{font-size:12px;", ".d-card .d-lab{font-size:14px;", "d-lab 12→14"),
    (".d-card .d-val{font-size:22px;", ".d-card .d-val{font-size:24px;", "d-val 22→24"),
    (".empty{padding:48px 16px;text-align:center;color:var(--dim);font-size:14px;", ".empty{padding:48px 16px;text-align:center;color:var(--dim);font-size:16px;", "empty 14→16"),
    ("font-size:13px;font-weight:700;z-index:120;opacity:0;", "font-size:15px;font-weight:700;z-index:120;opacity:0;", "toast 13→15"),
]
for old, new, label in FONTS:
    rep1(old, new, "字体 " + label)

# ---------- 3) 页面标题放大 + 卡通图标 ----------
ICONS = {
 "overview": ('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
   '<rect x="3" y="6.5" width="18" height="14" rx="4" fill="#7C3AED"/>'
   '<path d="M3.6 10.6h16.8" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>'
   '<path d="M12 6.5v14" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>'
   '<rect x="5.5" y="2.6" width="13" height="5" rx="2.5" fill="#A78BFA"/></svg>', "#7C3AED"),
 "supplier": ('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
   '<path d="M3 20V13l4.2-2.4V13l4.3-2.4V13L15.8 10V20H3z" fill="#0EA5E9"/>'
   '<rect x="17" y="4" width="4" height="16" rx="1.6" fill="#38BDF8"/>'
   '<rect x="6" y="15.5" width="2.6" height="2.6" rx="1" fill="#fff"/>'
   '<rect x="10.6" y="15.5" width="2.6" height="2.6" rx="1" fill="#fff"/></svg>', "#0EA5E9"),
 "capacity": ('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
   '<path d="M4 16.5a8 8 0 1 1 16 0" stroke="#10B981" stroke-width="3.2" stroke-linecap="round"/>'
   '<path d="M12 16.5l4.3-4.6" stroke="#F59E0B" stroke-width="3" stroke-linecap="round"/>'
   '<circle cx="12" cy="16.6" r="2.3" fill="#10B981"/></svg>', "#10B981"),
 "weekly": ('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
   '<rect x="3" y="5" width="18" height="16" rx="4.5" fill="#F59E0B"/>'
   '<rect x="3" y="5" width="18" height="5" rx="4.5" fill="#FCD34D"/>'
   '<rect x="7" y="2.6" width="2.6" height="4.6" rx="1.3" fill="#B45309"/>'
   '<rect x="14.4" y="2.6" width="2.6" height="4.6" rx="1.3" fill="#B45309"/>'
   '<circle cx="8.6" cy="14" r="1.7" fill="#fff"/><circle cx="15.4" cy="14" r="1.7" fill="#fff"/></svg>', "#F59E0B"),
 "overdue": ('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
   '<path d="M12 3a6.6 6.6 0 0 0-6.6 6.6v4.1L3.8 17h16.4l-1.6-3.3V9.6A6.6 6.6 0 0 0 12 3z" fill="#EF4444"/>'
   '<circle cx="12" cy="19.4" r="2.2" fill="#FCA5A5"/>'
   '<rect x="11" y="7.4" width="2.2" height="5" rx="1.1" fill="#fff"/></svg>', "#EF4444"),
 "cross": ('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
   '<rect x="3" y="3" width="8.2" height="8.2" rx="2.6" fill="#DB2777"/>'
   '<rect x="12.8" y="3" width="8.2" height="8.2" rx="2.6" fill="#F9A8D4"/>'
   '<rect x="3" y="12.8" width="8.2" height="8.2" rx="2.6" fill="#F9A8D4"/>'
   '<rect x="12.8" y="12.8" width="8.2" height="8.2" rx="2.6" fill="#DB2777"/></svg>', "#DB2777"),
}
TITLES = {"在途概览": "overview", "供应商数据分析": "supplier", "产能负荷分析": "capacity",
          "周数据计划": "weekly", "逾期分析": "overdue", "交叉分析": "cross"}
for label, key in TITLES.items():
    old = '<div class="page-title">%s</div>' % label
    svg, color = ICONS[key]
    new = ('<div class="page-title"><span class="pico" style="--pico:%s">%s</span><span>%s</span></div>'
           % (color, svg, label))
    rep1(old, new, "标题图标 " + label)

# ---------- 4) 追加 CSS ----------
EXTRA = """
  /* ===== 第2批：标题图标 / 悬停 / 动画 / 响应式 ===== */
  .page-title{display:flex;align-items:center;gap:14px;margin:12px 0 8px;}
  .page-title .pico{width:52px;height:52px;flex:0 0 auto;border-radius:18px;
    display:flex;align-items:center;justify-content:center;
    background:rgba(255,255,255,0.88);box-shadow:var(--clay-card);
    animation:clay-float 7s ease-in-out infinite;}
  .page-title .pico svg{width:30px;height:30px;display:block;}
  .page-title > span:last-child{font-size:36px;font-weight:900;letter-spacing:-.02em;line-height:1.1;}

  /* 悬停：面板上浮（与卡片不同——卡片位移更大并带内发光） */
  .panel{transition:transform .35s cubic-bezier(.22,.61,.36,1), box-shadow .35s ease-out;}
  .panel:hover{transform:translateY(-4px);box-shadow:var(--clay-card-hover);}
  .d-card{transition:transform .3s ease-out, box-shadow .3s ease-out;}
  .d-card:hover{transform:translateY(-3px);box-shadow:var(--clay-card);}
  .tag{transition:transform .25s ease-out, filter .25s ease-out;}
  .tag:hover{transform:translateY(-2px) scale(1.04);filter:saturate(1.15);}
  table.t tbody tr td:first-child{transition:box-shadow .25s ease-out;}
  table.t tbody tr:hover td:first-child{box-shadow:inset 4px 0 0 0 var(--accent);}
  .btn,.seg span{will-change:transform;}

  /* 动画：页面淡入 + 卡片错峰上浮 */
  @keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}
  @keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
  .page.active{animation:fadeIn .35s ease-out both;}
  .page.active .cards,.page.active .ct1-inline,.page.active > .ctl-inline{animation:fadeUp .45s ease-out both;}
  .cards .card{animation:fadeUp .5s cubic-bezier(.22,.61,.36,1) both;}
  .cards .card:nth-child(1){animation-delay:.02s}
  .cards .card:nth-child(2){animation-delay:.06s}
  .cards .card:nth-child(3){animation-delay:.10s}
  .cards .card:nth-child(4){animation-delay:.14s}
  .cards .card:nth-child(5){animation-delay:.18s}
  .cards .card:nth-child(6){animation-delay:.22s}
  .cards .card:nth-child(7){animation-delay:.26s}
  .cards .card:nth-child(8){animation-delay:.30s}
  .grid > .panel{animation:fadeUp .5s cubic-bezier(.22,.61,.36,1) both;animation-delay:.10s;}
  .grid > .panel:nth-child(2){animation-delay:.16s}
  .grid > .panel:nth-child(3){animation-delay:.22s}
  .grid > .panel:nth-child(4){animation-delay:.28s}
  .drawer .db > *{animation:fadeUp .35s ease-out both;}

  /* 响应式：任何宽度都不溢出 */
  @media(max-width:1280px){ .cards{grid-template-columns:repeat(3,minmax(0,1fr));} }
  .grid{grid-template-columns:repeat(auto-fit,minmax(min(400px,100%),1fr));}
  .panel,#ov_month_table,#sup_line_table,#cap_detail_table,#od_table,#ov_daily{overflow-x:auto;}
  .page-title > span:last-child{word-break:break-word;}
  @media(max-width:900px){
    .page-title .pico{width:44px;height:44px;border-radius:15px;}
    .page-title .pico svg{width:25px;height:25px;}
    .page-title > span:last-child{font-size:28px;}
  }
  @media(max-width:600px){
    .cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;}
    .card{padding:14px 14px;}
    .card .val{font-size:26px;}
    .page-title{gap:10px;}
    .page-title .pico{width:38px;height:38px;border-radius:13px;}
    .page-title .pico svg{width:22px;height:22px;}
    .page-title > span:last-child{font-size:22px;}
    .filterbar{margin:12px 10px 4px;padding:12px;}
    header.topbar{margin:10px 10px 0;}
  }
"""
s = s.replace("</style>", EXTRA + "</style>", 1)
report.append("  OK  追加第2批 CSS")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("=== 第2批视觉 ===")
print("\n".join(report))
bad = [r for r in report if r.strip().startswith("!!")]
print("\n失败项:", len(bad))
