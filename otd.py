# -*- coding: utf-8 -*-
"""准交率计算模块
================
输入：
  - 收料通知单（默认 src/otd_recv.xlsx）
  - 全量采购订单（默认 src/otd_po_full.xlsx，方案「默认方案（个人）」，含已关闭）
输出：dict，供 clean.py 写入 data.json 的 otd 字段。

口径：
  准交判定   收料日期 <= 采购订单交货日期
  准交数量   优先「合格入库关联数量」；为空且行状态=正常时取「实收数量」；否则 0
  分母      源单（源单单号+物料编码）对应采购订单「采购数量」，按源单+物料去重
  准交率     准交数量 / 分母
  采购员     采购订单创建人
"""
import os
import re
import datetime as dt
from collections import defaultdict

import openpyxl

# 已知例外：深圳市华熠网络账簿下的固资/办公采购，不在 104 账簿的全量采购订单导出内。
# 合计 8 行、10 件，占 10 月收料量约 0.0008%，明确剔除并在页面标注。
KNOWN_EXCLUDED = {
    "CGDD012692": "深圳市华熠网络·京东平台（固资）",
    "CGDD012720": "深圳市华熠网络·京东平台（固资）",
    "CGDD012843": "深圳市华熠网络·京东平台（固资）",
    "CGDD013390": "深圳市华熠网络·永隆达电脑（固资）",
}

_STATUS_RANK = {"已审核": 3, "重新审核": 2, "审核中": 1, "创建": 0, "": 0}


def _load(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    wb.close()
    if not rows:
        return [], []
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    return header, rows[1:]


def _num(v):
    if v is None:
        return 0.0
    if isinstance(v, str):
        v = v.strip().replace(",", "")
        if v == "":
            return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _date(v):
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip().replace(" 00:00:00", "")
    if not s:
        return None
    s = s[:10].replace("/", "-").replace(".", "-")
    try:
        y, m, d = s.split("-")
        return dt.date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return None


def _find_src(src_dir, exact, keyword):
    p = os.path.join(src_dir, exact)
    if os.path.exists(p):
        return p
    # 兜底：目录内按关键字取最新一份
    cands = []
    if os.path.isdir(src_dir):
        for fn in os.listdir(src_dir):
            if fn.lower().endswith(".xlsx") and not fn.startswith("~$") and keyword in fn:
                fp = os.path.join(src_dir, fn)
                cands.append((os.path.getmtime(fp), fp))
    return max(cands)[1] if cands else None


def _find_po_field(idx, *names):
    for n in names:
        if n in idx:
            return idx[n]
    return None


def build_otd(src_dir, periods=None):
    recv_path = _find_src(src_dir, "otd_recv.xlsx", "收料通知单")
    po_path = _find_src(src_dir, "otd_po_full.xlsx", "采购订单_全量")
    if not recv_path or not po_path:
        return None

    rh, rrows = _load(recv_path)
    ridx = {h: i for i, h in enumerate(rh)}

    def rg(r, name):
        i = ridx.get(name)
        return r[i] if i is not None and i < len(r) else None

    ph, prows = _load(po_path)
    pidx = {h: i for i, h in enumerate(ph)}

    def pg(r, name):
        i = pidx.get(name)
        return r[i] if i is not None and i < len(r) else None

    # 采购订单索引：同一(单据编号, 物料编码)多状态时优先「已审核」
    po_key = {}
    po_rank = {}
    po_docs = set()
    for r in prows:
        doc = str(pg(r, "单据编号") or "").strip()
        if not doc:
            continue
        po_docs.add(doc)
        mc = str(pg(r, "物料编码") or "").strip()
        status = str(pg(r, "单据状态") or "").strip()
        rank = _STATUS_RANK.get(status, 0)
        key = (doc, mc)
        if key not in po_key or rank > po_rank.get(key, -1):
            po_key[key] = {
                "po_qty": _num(pg(r, "采购数量")),
                "delivery": _date(pg(r, "交货日期")),
                "creator": str(pg(r, "创建人") or "").strip(),
                "supplier": str(pg(r, "供应商") or "").strip(),
                "close_status": str(pg(r, "关闭状态") or "").strip(),
            }
            po_rank[key] = rank

    if periods is None:
        months = sorted({str(rg(r, "收料日期") or "")[:7] for r in rrows if re.match(r"^\d{4}-\d{2}", str(rg(r, "收料日期") or ""))})
        periods = months[-2:] if months else []

    period_data = []
    for period in periods:
        rows = [r for r in rrows if str(rg(r, "收料日期") or "")[:7] == period]
        src_all = [str(rg(r, "源单单号") or "").strip() for r in rows]
        src_all = [s for s in src_all if s]
        uniq = set(src_all)
        matched_docs = {s for s in uniq if s in po_docs}

        sup = defaultdict(lambda: {"ontime": 0.0, "late": 0.0, "po_qty": 0.0, "rows": 0})
        buy = defaultdict(lambda: {"ontime": 0.0, "late": 0.0, "po_qty": 0.0, "rows": 0})
        seen_lines = set()
        missing = defaultdict(lambda: {"rows": 0, "qty": 0.0, "dates": []})
        ontime_total = late_total = 0.0
        po_total = 0.0
        rows_matched = 0

        for r in rows:
            doc = str(rg(r, "源单单号") or "").strip()
            mc = str(rg(r, "物料编码") or "").strip()
            recv_d = _date(rg(r, "收料日期"))
            q_assoc = rg(r, "合格入库关联数量")
            q_actual = rg(r, "实收数量")
            status = str(rg(r, "行状态") or "").strip()
            if str(q_assoc).strip() not in ("", "None"):
                qty = _num(q_assoc)
            elif status == "正常":
                qty = _num(q_actual)
            else:
                qty = 0.0

            po = po_key.get((doc, mc))
            if not doc or not po:
                if doc:
                    m = missing[doc]
                    m["rows"] += 1
                    m["qty"] += qty
                    if recv_d:
                        m["dates"].append(recv_d.isoformat())
                continue
            rows_matched += 1
            ontime = bool(recv_d and po["delivery"] and recv_d <= po["delivery"])
            supplier = str(rg(r, "供应商") or po["supplier"] or "").strip() or "（未知）"
            creator = po["creator"] or "（未知）"

            if ontime:
                ontime_total += qty
                sup[supplier]["ontime"] += qty
                buy[creator]["ontime"] += qty
            else:
                late_total += qty
                sup[supplier]["late"] += qty
                buy[creator]["late"] += qty
            sup[supplier]["rows"] += 1
            buy[creator]["rows"] += 1

            if (doc, mc) not in seen_lines:
                seen_lines.add((doc, mc))
                po_total += po["po_qty"]
                sup[supplier]["po_qty"] += po["po_qty"]
                buy[creator]["po_qty"] += po["po_qty"]

        def _pack(d, is_supplier=True):
            out = []
            for name, v in d.items():
                rate = (v["ontime"] / v["po_qty"] * 100) if v["po_qty"] > 0 else 0.0
                item = {
                    "name": name,
                    "ontime": round(v["ontime"]),
                    "late": round(v["late"]),
                    "po_qty": round(v["po_qty"]),
                    "rate": round(rate, 2),
                    "rate_capped": round(min(rate, 100.0), 2),
                    "rows": v["rows"],
                    "over": rate > 100.5,
                }
                out.append(item)
            out.sort(key=lambda x: -x["po_qty"])
            return out

        miss_list = []
        for doc, v in sorted(missing.items()):
            miss_list.append({
                "doc": doc,
                "rows": v["rows"],
                "qty": round(v["qty"]),
                "dates": [min(v["dates"]), max(v["dates"])] if v["dates"] else [],
                "reason": KNOWN_EXCLUDED.get(doc, "采购订单未匹配"),
                "known": doc in KNOWN_EXCLUDED,
            })

        unknown_missing = [m for m in miss_list if not m["known"]]
        rate = (ontime_total / po_total * 100) if po_total > 0 else 0.0
        share = (ontime_total / (ontime_total + late_total) * 100) if (ontime_total + late_total) > 0 else 0.0

        period_data.append({
            "period": period,
            "label": f"{period[:4]}年{int(period[5:7])}月" if len(period) == 7 else period,
            "overall": {
                "po_qty": round(po_total),
                "ontime": round(ontime_total),
                "late": round(late_total),
                "rate": round(rate, 2),
                "ontime_share": round(share, 2),
                "order_lines": len(seen_lines),
                "rows": len(rows),
            },
            "coverage": {
                "unique_total": len(uniq),
                "unique_matched": len(matched_docs),
                "unique_rate": round(len(matched_docs) / len(uniq) * 100, 2) if uniq else 0.0,
                "rows_total": len(rows),
                "rows_matched": rows_matched,
                "row_rate": round(rows_matched / len(rows) * 100, 2) if rows else 0.0,
            },
            "suppliers": _pack(sup),
            "buyers": _pack(buy, is_supplier=False),
            "missing": miss_list,
            "unknown_missing": unknown_missing,
            "excluded_known": [m for m in miss_list if m["known"]],
            "blocked": len(unknown_missing) > 0,
        })

    if not period_data:
        return None

    return {
        "updated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M"),
        "source_recv": os.path.basename(recv_path),
        "source_po_full": os.path.basename(po_path),
        "default_period": period_data[-1]["period"],
        "periods": period_data,
        "known_excluded": KNOWN_EXCLUDED,
    }
