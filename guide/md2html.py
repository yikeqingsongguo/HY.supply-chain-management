# -*- coding: utf-8 -*-
"""Minimal Markdown -> HTML for the usage guide, inlining the SVG diagrams.
No external deps. Produces 使用说明.html (single file, clay theme).
"""
import os, re, html, base64, mimetypes

BASE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(BASE, "使用说明.md")
OUT = os.path.join(BASE, "使用说明.html")
INLINE_LIMIT = 0  # 真实截图较大，统一用相对引用，保持 HTML 轻量

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def embed(img_path):
    full = os.path.join(BASE, img_path)
    if not os.path.exists(full):
        return '<p style="color:#B91C1C">[缺图: %s]</p>' % esc(img_path)
    if img_path.lower().endswith(".svg"):
        return read(full).strip().replace('<svg ', '<svg class="fig" ', 1)
    if os.path.getsize(full) <= INLINE_LIMIT:
        mime = mimetypes.guess_type(full)[0] or "image/png"
        b64 = base64.b64encode(open(full, "rb").read()).decode()
        return '<img class="fig" src="data:%s;base64,%s" alt=""/>' % (mime, b64)
    return '<img class="fig" src="%s" alt=""/>' % esc(img_path)

def img_block(src, alt):
    return '<figure>' + embed(src) + '<figcaption>' + esc(alt) + '</figcaption></figure>'

def esc(t):
    return html.escape(t, quote=False)

def inline_fmt(t):
    t = esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

def convert(md):
    lines = md.split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1; continue
        # image-only line -> embedded figure
        m = re.match(r'^!\[(.*?)\]\((.*?)\)$', s)
        if m:
            out.append(img_block(m.group(2), m.group(1)))
            i += 1; continue
        # hr
        if re.match(r'^-{3,}$', s):
            out.append('<hr/>'); i += 1; continue
        # headings
        hm = re.match(r'^(#{1,4})\s+(.*)$', s)
        if hm:
            lvl = len(hm.group(1))
            out.append('<h%d>%s</h%d>' % (lvl, inline_fmt(hm.group(2)), lvl))
            i += 1; continue
        # table
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = cells[2:] if len(cells) > 1 and re.match(r'^[-: ]+$', rows[1].strip("| ").replace("|", "")) else cells[1:]
            head = cells[0]
            t = '<table><thead><tr>' + ''.join('<th>%s</th>' % inline_fmt(c) for c in head) + '</tr></thead><tbody>'
            for r in body:
                t += '<tr>' + ''.join('<td>%s</td>' % inline_fmt(c) for c in r) + '</tr>'
            t += '</tbody></table>'
            out.append(t); continue
        # blockquote
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            out.append('<blockquote>' + '<br/>'.join(inline_fmt(b) for b in buf if b) + '</blockquote>')
            continue
        # lists (ordered / unordered), flat
        if re.match(r'^(\-|\d+\.)\s+', s):
            ordered = bool(re.match(r'^\d+\.\s+', s))
            tag = 'ol' if ordered else 'ul'
            items = []
            while i < n:
                cur = lines[i].strip()
                mm = re.match(r'^(\-|\d+\.)\s+(.*)$', cur)
                if not mm:
                    break
                items.append(mm.group(2)); i += 1
            out.append('<%s>' % tag + ''.join('<li>%s</li>' % inline_fmt(x) for x in items) + '</%s>' % tag)
            continue
        # paragraph
        buf = [s]; i += 1
        while i < n and lines[i].strip() and not re.match(r'^(#{1,4}\s|>|\||\-{3,}$|!\[|\- |\d+\. )', lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append('<p>' + '<br/>'.join(inline_fmt(b) for b in buf) + '</p>')
    return "\n".join(out)

CSS = """
:root{--ink:#3A2E4D;--mut:#7A7088;--purple:#7C3AED;--line:#E7E1F2;--bg:#F4F1FA;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:'Segoe UI','PingFang SC','Microsoft YaHei',system-ui,sans-serif;line-height:1.75;}
.wrap{max-width:1080px;margin:0 auto;padding:40px 24px 80px;}
h1{font-size:30px;margin:0 0 6px;letter-spacing:.3px}
h2{font-size:22px;margin:44px 0 12px;padding-left:12px;border-left:5px solid var(--purple);}
h3{font-size:18px;margin:30px 0 10px;color:#5B3FA6}
h4{font-size:15px;margin:20px 0 8px}
p{margin:10px 0}
a{color:var(--purple)}
hr{border:none;border-top:1px dashed var(--line);margin:34px 0}
blockquote{margin:14px 0;padding:12px 18px;background:#fff;border-left:5px solid #A78BFA;
 border-radius:0 12px 12px 0;color:#554B66;box-shadow:0 6px 18px rgba(124,58,237,.06)}
code{background:#EFEAFA;border-radius:6px;padding:2px 6px;font-size:13px;color:#6D28D9}
figure{margin:18px 0;background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px;
 box-shadow:0 10px 28px rgba(124,58,237,.08)}
svg.fig{display:block;width:100%;height:auto}
img.fig{display:block;width:100%;height:auto;border-radius:10px}
figcaption{margin-top:8px;text-align:center;font-size:12.5px;color:var(--mut)}
table{width:100%;border-collapse:collapse;margin:14px 0;background:#fff;border-radius:14px;overflow:hidden;
 box-shadow:0 8px 22px rgba(124,58,237,.07);font-size:14px}
th{background:var(--purple);color:#fff;text-align:left;padding:10px 14px;font-weight:700}
td{padding:9px 14px;border-top:1px solid var(--line)}
tbody tr:nth-child(even){background:#FAF8FE}
ul,ol{margin:10px 0;padding-left:24px}
li{margin:4px 0}
strong{color:#4C1D95}
sub{color:var(--mut)}
"""

def main():
    body = convert(read(MD))
    doc = ("<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>"
           "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
           "<title>供应链在途数据看板 · 使用说明</title><style>" + CSS + "</style></head>"
           "<body><div class='wrap'>" + body + "</div></body></html>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote", os.path.basename(OUT), len(doc), "chars")

if __name__ == "__main__":
    main()
