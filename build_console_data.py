# -*- coding: utf-8 -*-
"""
构建管理台数据文件（console/weekly.json、console/apply.csv）。

weekly.json 口径：仅周计划数量（用户确认），按供应商聚合；
明细 items 额外关联采购申请单，补齐「申请单单据编号」与「领星创建人」。

关联策略（申请单是按物料编码的台账，周计划是领星 SKU，两套编码不能直接对等）：
  1) SKU 规范化精确匹配：去非字母数字、大写、去 SP 前缀
  2) 兜底：物料名称 + 规格型号
未命中时留空，前端显示「—」。
"""
import csv
import json
import os
import re

try:
    import openpyxl
except ImportError:
    openpyxl = None

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
CONSOLE = os.path.join(HERE, "console")


def norm_code(s):
    t = re.sub(r"[^A-Za-z0-9]", "", str(s or "")).upper()
    return re.sub(r"^SP(?=[A-Z])", "", t)


def norm_text(s):
    return re.sub(r"[\s\u3000]", "", str(s or ""))


def load_apply_map(apply_path):
    """物料编码 -> {docs, ling, name, spec}；再按 名称+规格 建二级索引。"""
    by_code, by_spec = {}, {}
    if not apply_path or not os.path.exists(apply_path) or openpyxl is None:
        return by_code, by_spec
    wb = openpyxl.load_workbook(apply_path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    idx = {h: i for i, h in enumerate(header) if h}
    # 同名列（备注）取第一次出现
    for r in rows[1:]:
        def g(k):
            i = idx.get(k)
            return r[i] if i is not None and i < len(r) else None

        code = norm_code(g("物料编码"))
        doc = str(g("单据编号") or "").strip()
        ling = str(g("领星创建人") or "").strip()
        spec = norm_text(g("规格型号"))
        name = norm_text(g("物料名称"))
        if not code and not spec:
            continue
        rec = {"doc": doc, "ling": ling}
        if code:
            a = by_code.setdefault(code, {"docs": [], "lings": []})
            if doc and doc not in a["docs"]:
                a["docs"].append(doc)
            if ling and ling not in a["lings"]:
                a["lings"].append(ling)
        if spec and name:
            a = by_spec.setdefault((name, spec), {"docs": [], "lings": []})
            if doc and doc not in a["docs"]:
                a["docs"].append(doc)
            if ling and ling not in a["lings"]:
                a["lings"].append(ling)
    return by_code, by_spec


def build():
    os.makedirs(CONSOLE, exist_ok=True)
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        data = json.load(f)

    core = set((data.get("meta") or {}).get("core_suppliers") or [])
    weekly = data.get("weekly") or []
    apply_path = os.path.join(SRC, "otd_apply.xlsx")
    by_code, by_spec = load_apply_map(apply_path)

    agg = {}
    hit_code = hit_spec = hit_none = 0
    for r in weekly:
        full = r.get("supplier_full") or ""
        short = r.get("supplier_short") or full
        a = agg.setdefault(full, {
            "name": full, "short": short, "plan": 0.0,
            "skus": set(), "spus": set(), "buyers": set(), "items": [],
        })
        qty = float(r.get("plan_qty") or 0)
        a["plan"] += qty
        if r.get("sku"):
            a["skus"].add(r["sku"])
        if r.get("spu"):
            a["spus"].add(r["spu"])
        if r.get("buyer"):
            a["buyers"].add(r["buyer"])

        code = norm_code(r.get("sku"))
        m = by_code.get(code)
        if m:
            hit_code += 1
        else:
            m = by_spec.get((norm_text(r.get("material_name")), norm_text(r.get("spec"))))
            if m:
                hit_spec += 1
            else:
                hit_none += 1
        a["items"].append({
            "sku": r.get("sku") or "",
            "spu": r.get("spu") or "",
            "name": r.get("material_name") or "",
            "spec": r.get("spec") or "",
            "buyer": r.get("buyer") or "",
            "qty": round(qty, 1),
            "doc": "、".join((m or {}).get("docs") or []),
            "ling": "、".join((m or {}).get("lings") or []),
        })

    suppliers = []
    for a in agg.values():
        suppliers.append({
            "name": a["name"],
            "short": a["short"],
            "core": a["short"] in core,
            "plan": round(a["plan"], 1),
            "skus": len(a["skus"]),
            "spus": len(a["spus"]),
            "buyers": sorted(a["buyers"]),
            "items": a["items"],
        })
    suppliers.sort(key=lambda x: -x["plan"])

    out = {
        "updated_at": (data.get("meta") or {}).get("updated_at"),
        "total_plan": round(sum(x["plan"] for x in suppliers), 1),
        "rows": len(weekly),
        "supplier_count": len(suppliers),
        "core_count": sum(1 for x in suppliers if x["core"]),
        "apply_source": os.path.basename(apply_path),
        "apply_match": {"by_sku": hit_code, "by_spec": hit_spec, "miss": hit_none},
        "suppliers": suppliers,
    }
    with open(os.path.join(CONSOLE, "weekly.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    # apply.csv 供管理台自动载入解析（金蝶 xlsx 在内联 SheetJS 里会内存溢出）
    if os.path.exists(apply_path):
        wb = openpyxl.load_workbook(apply_path, data_only=True)
        ws = wb[wb.sheetnames[0]]
        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        def cv(v):
            import datetime as dt
            if isinstance(v, (dt.datetime, dt.date)):
                return v.strftime("%Y/%-m/%-d") if os.name != "nt" else "%d/%d/%d" % (v.year, v.month, v.day)
            return "" if v is None else v

        with open(os.path.join(CONSOLE, "apply.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            for r in rows:
                w.writerow([cv(x) for x in r])

    print("console/weekly.json 供应商 %d（核心 %d）｜周计划 %s｜申请单关联 SKU %d / 规格 %d / 未命中 %d"
          % (out["supplier_count"], out["core_count"], out["total_plan"],
             hit_code, hit_spec, hit_none))


if __name__ == "__main__":
    build()
