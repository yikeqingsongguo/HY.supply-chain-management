import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'index.template.html')
OUT = os.path.join(HERE, 'index.template.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

CSS = r'''
  :root{
    --bg:#EDF4FB; --panel:#FFFFFF; --panel2:#F8FAFC; --nav:#FFFFFF;
    --border:#D1D5DB; --border2:#9CA3AF;
    --text:#111827; --muted:#374151; --dim:#6B7280;
    --blue:#2563EB; --green:#059669; --amber:#D97706; --purple:#7C3AED;
    --red:#DC2626; --slate:#64748B; --blue-d:#1D4ED8; --pink:#DB2777;
    --teal:#0D9488; --orange:#EA580C;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    font-size:15px;line-height:1.55;}
  header.topbar{position:sticky;top:0;z-index:50;background:var(--nav);border-bottom:1px solid var(--border);
    display:flex;align-items:center;gap:18px;padding:0 18px;height:58px;flex-wrap:wrap;box-shadow:0 1px 3px rgba(0,0,0,.04);}
  .brand{font-size:17px;font-weight:600;white-space:nowrap;}
  .brand small{color:var(--blue);font-size:11px;font-weight:500;margin-left:6px;letter-spacing:1px;}
  nav.tabs{display:flex;gap:8px;flex-wrap:wrap;}
  .tab{padding:8px 16px;border-radius:18px;border:1px solid var(--border);color:var(--muted);
    cursor:pointer;font-size:13px;font-weight:500;user-select:none;transition:.15s;white-space:nowrap;background:var(--panel2);}
  .tab:hover{color:var(--text);border-color:var(--border2);}
  .tab.active{background:var(--blue-d);color:#fff;border-color:var(--blue-d);}
  .topmeta{margin-left:auto;color:var(--dim);font-size:12px;text-align:right;white-space:nowrap;line-height:1.4;}
  .topmeta b{color:var(--text);font-weight:600;}
  .page{display:none;padding:16px 20px 60px;}
  .page.active{display:block;}
  .page-title{font-size:18px;font-weight:600;margin:4px 0 6px;}
  .page-sub{color:var(--dim);font-size:13px;margin-bottom:14px;}
  .filterbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:var(--panel);
    border:1px solid var(--border);border-radius:12px;padding:10px 12px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
  .filterbar details{position:relative;}
  .filterbar summary{list-style:none;cursor:pointer;padding:8px 14px;border:1px solid var(--border);
    border-radius:8px;color:var(--muted);font-size:13px;font-weight:500;user-select:none;min-width:100px;background:var(--panel2);}
  .filterbar summary::-webkit-details-marker{display:none;}
  .filterbar summary:after{content:" ▾";color:var(--dim);}
  .filterbar details[open] summary{color:var(--text);border-color:var(--blue);background:#EFF6FF;}
  .drop{position:absolute;top:42px;left:0;z-index:40;background:#fff;border:1px solid var(--border2);
    border-radius:10px;padding:10px;max-height:300px;overflow:auto;min-width:200px;box-shadow:0 12px 32px rgba(0,0,0,.12);}
  .drop .drop-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
  .drop .drop-title{font-size:13px;font-weight:600;color:var(--text);}
  .drop .drop-btns{display:flex;gap:6px;}
  .drop .drop-btns .btn{padding:4px 10px;font-size:11px;}
  .drop label{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;font-size:13px;cursor:pointer;color:var(--text);}
  .drop label:hover{background:#F3F4F6;}
  .drop label b{font-weight:500;}
  .drop input{accent-color:var(--blue);width:15px;height:15px;}
  .drop .empty-tip{padding:10px;color:var(--dim);font-size:12px;}
  .fsearch{flex:1;min-width:180px;background:var(--panel2);border:1px solid var(--border);border-radius:8px;
    color:var(--text);padding:8px 12px;font-size:13px;outline:none;}
  .fsearch:focus{border-color:var(--blue);}
  .btn{padding:7px 16px;border-radius:8px;border:1px solid var(--border);background:#fff;color:var(--muted);
    cursor:pointer;font-size:13px;font-weight:500;user-select:none;}
  .btn:hover{color:var(--text);border-color:var(--border2);background:#F9FAFB;}
  .btn.primary{background:var(--blue-d);color:#fff;border-color:var(--blue-d);}
  .btn.primary:hover{filter:brightness(1.05);background:#1E40AF;}
  .seg{display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:#fff;}
  .seg span{padding:7px 14px;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;user-select:none;}
  .seg span:hover{background:#F9FAFB;}
  .seg span.on{background:var(--blue-d);color:#fff;}
  .ctl-inline{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px;}
  .ctl-inline .lab{color:var(--muted);font-size:13px;font-weight:500;}
  .numin{width:100px;background:var(--panel2);border:1px solid var(--border);border-radius:8px;color:var(--text);
    padding:7px 10px;font-size:13px;outline:none;font-weight:600;}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:16px;}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
  .card .lab{color:var(--muted);font-size:13px;font-weight:500;margin-bottom:6px;}
  .card .val{font-size:28px;font-weight:600;color:var(--text);}
  .card .hint{color:var(--dim);font-size:11px;margin-top:4px;}
  .kpi-warn .val{color:var(--red);}
  .grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));}
  .panel{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
  .panel h3{margin:0 0 6px;font-size:15px;font-weight:600;}
  .panel .ph-sub{color:var(--dim);font-size:12px;margin-bottom:10px;}
  .chart{width:100%;}
  .legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12px;color:var(--muted);margin:4px 0 8px;}
  .legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:middle;}
  table.t{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px;}
  table.t th,table.t td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--border);}
  table.t th{color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--panel);white-space:normal;line-height:1.3;}
  table.t td{white-space:nowrap;}
  table.t tbody tr:hover{background:#F3F4F6;cursor:pointer;}
  table.t tfoot td{font-weight:600;color:var(--text);border-top:2px solid var(--border2);}
  .tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:500;}
  .tag.core{background:#DBEAFE;color:#1D4ED8;}
  .tag.norm{background:#F3F4F6;color:#4B5563;}
  .tag.od{background:#FEE2E2;color:#B91C1C;}
  .tag.ok{background:#D1FAE5;color:#047857;}
  .tag.wait{background:#FEF3C7;color:#B45309;}
  .link{color:var(--blue);cursor:pointer;font-weight:500;}
  .bar-mini{height:8px;border-radius:4px;background:var(--border);overflow:hidden;min-width:70px;display:inline-block;vertical-align:middle;}
  .bar-mini i{display:block;height:100%;background:var(--green);}
  .drawer-mask{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:90;display:none;}
  .drawer{position:fixed;top:0;right:0;height:100%;width:560px;max-width:94vw;background:#fff;
    border-left:1px solid var(--border2);z-index:95;transform:translateX(100%);transition:transform .22s;
    display:flex;flex-direction:column;box-shadow:-8px 0 32px rgba(0,0,0,.12);}
  .drawer.open{transform:translateX(0);}
  .drawer .dh{display:flex;align-items:center;gap:12px;padding:16px 18px;border-bottom:1px solid var(--border);background:#F9FAFB;}
  .drawer .dh .t{font-size:16px;font-weight:600;flex:1;color:var(--text);}
  .drawer .dh .x{cursor:pointer;color:var(--dim);font-size:20px;line-height:1;font-weight:600;}
  .crumbs{padding:10px 18px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--border);background:#F9FAFB;}
  .crumbs b{color:var(--blue);cursor:pointer;font-weight:600;}
  .drawer .db{flex:1;overflow:auto;padding:14px 18px;}
  .drawer .df{padding:12px 18px;border-top:1px solid var(--border);font-size:13px;color:var(--muted);background:#F9FAFB;}
  .drawer .df b{color:var(--text);font-weight:600;}
  .d-card{background:#F8FAFC;border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:12px;}
  .d-card .d-lab{font-size:12px;color:var(--dim);margin-bottom:4px;}
  .d-card .d-val{font-size:20px;font-weight:600;color:var(--text);}
  .d-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;}
  .empty{padding:40px 16px;text-align:center;color:var(--dim);font-size:14px;}
  .empty .big{font-size:32px;margin-bottom:8px;}
  .toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#1F2937;
    border:1px solid #374151;color:#fff;padding:10px 18px;border-radius:10px;font-size:13px;
    z-index:120;opacity:0;transition:.2s;pointer-events:none;}
  .toast.show{opacity:1;}
  @media(max-width:760px){
    .grid{grid-template-columns:1fr;}
    .topmeta{display:none;}
  }
'''.strip()

new_html = re.sub(r'<style>.*?</style>', '<style>\n'+CSS+'\n</style>', html, flags=re.S)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(new_html)
print('CSS replaced. lines:', len(new_html.splitlines()))
