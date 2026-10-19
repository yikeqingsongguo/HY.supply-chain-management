# -*- coding: utf-8 -*-
"""准交率计算模块 v2（2026-10-19 口径确认）
================================================
输入：
  - 收料通知单（默认 src/otd_recv.xlsx）
  - 全量采购订单（默认 src/otd_po_full.xlsx，方案「默认方案（个人）」，含已关闭）

口径：
  统计总体   交货日期在本月且已到期的采购订单行（按订单行判定）
  准交数量   该订单行在「收料日期 <= 交货日期」的累计收料数量，封顶 = 订单数量
  准交率     Σ各订单准交数量 / Σ各订单数量（数量加权）
             例：订单01 1000 件、期内交 800；订单02 100 件、期内交 100
             → (800+100) / (1000+100) = 81.82%
  人员       仅保留 10 位采购订单创建人；谭丁香 / 曾琨(曾坤) / 谢国超 排除
  收料数量   优先「合格入库关联数量」；为空且行状态=正常时取「实收数量」；否则 0
"""
import os
import re
import calendar
import datetime as dt
from collections import defaultdict

import openpyxl

# 已知例外：深圳市华熠网络账簿下的固资/办公采购，不在 104 账簿的全量采购订单导出内。
KNOWN_EXCLUDED = {
    "CGDD012692": "深圳市华熠网络·京东平台（固资）",
    "CGDD012720": "深圳市华熠网络·京东平台（固资）",
    "CGDD012843": "深圳市华熠网络·京东平台（固资）",
    "CGDD013390": "深圳市华熠网络·永隆达电脑（固资）",
}

# 仅保留这 10 位采购订单创建人（截图名单）
ALLOWED_CREATORS = [
    "吴巧玲", "张世豪", "聂婷", "梁成杰", "程美琪",
    "孔志豪", "姚冰婷", "张洁", "李淑云", "何君豪",
]
ALLOWED_SET = set(ALLOWED_CREATORS)
EXCLUDED_CREATORS = ["谭丁香", "曾琨", "曾坤", "谢国超"]

# 只统计有效采购订单（审核中/创建 不进入总体）
ALLOWED_STATUS = {"已审核", "重新审核"}
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


def _norm_creator(v):
    """张世豪01 -> 张世豪；去尾数字、去空格。"""
    s = str(v or "").strip()
    s = re.sub(r"\d+$", "", s)
    return s.strip()


def _find_src(src_dir, exact, keyword):
    p = os.path.join(src_dir, exact)
    if os.path.exists(p):
        return p
    cands = []
    if os.path.isdir(src_dir):
        for fn in os.listdir(src_dir):
            if fn.lower().endswith(".xlsx") and not fn.startswith("~$") and keyword in fn:
                fp = os.path.join(src_dir, fn)
                cands.append((os.path.getmtime(fp), fp))
    return max(cands)[1] if cands else None


def _month_bounds(period):
    y, m = int(period[:4]), int(period[5:7])
    start = dt.date(y, m, 1)
    end = dt.date(y, m, calendar.monthrange(y, m)[1])
    return start, end


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

    # ---------- 采购订单行（同一 单号+物料 多状态时优先已审核） ----------
    po = {}
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
        if key not in po or rank > po[key]["_rank"]:
            po[key] = {
                "_rank": rank,
                "qty": _num(pg(r, "采购数量")),
                "delivery": _date(pg(r, "交货日期")),
                "creator": _norm_creator(pg(r, "创建人")),
                "creator_raw": str(pg(r, "创建人") or "").strip(),
                "supplier": str(pg(r, "供应商") or "").strip(),
                "status": status,
            }

    # ---------- 收料行（按 源单+物料 汇总；收料日期可跨月） ----------
    receipts = defaultdict(list)
    receipt_dates = []
    for r in rrows:
        doc = str(rg(r, "源单单号") or "").strip()
        if not doc:
            continue
        mc = str(rg(r, "物料编码") or "").strip()
        q_assoc = rg(r, "合格入库关联数量")
        q_actual = rg(r, "实收数量")
        status = str(rg(r, "行状态") or "").strip()
        if str(q_assoc).strip() not in ("", "None"):
            qty = _num(q_assoc)
        elif status == "正常":
            qty = _num(q_actual)
        else:
            qty = 0.0
        d = _date(rg(r, "收料日期"))
        receipts[(doc, mc)].append({"date": d, "qty": qty})
        if d:
            receipt_dates.append(d)

    # ---------- 统计周期 ----------
    today = dt.date.today()
    cur_first = today.replace(day=1)
    prev_first = (cur_first - dt.timedelta(days=1)).replace(day=1)
    if periods is None:
        periods = [prev_first.strftime("%Y-%m"), cur_first.strftime("%Y-%m")]
    current_period = cur_first.strftime("%Y-%m")

    period_data = []
    for period in periods:
        start, end = _month_bounds(period)
        effective_end = min(end, today)
        valid = (period == current_period)
        if valid:
            validity_note = "当前月，已按“交货日期在本月且已到期”统计。"
        else:
            validity_note = (
                "收料通知单导出从 %s 起；该月到期订单的期前收料可能缺失，数值仅供参考。"
                % (min(receipt_dates).isoformat() if receipt_dates else "—")
            )

        rows = [r for r in rrows if str(rg(r, "收料日期") or "")[:7] == period]
        src_all = [str(rg(r, "源单单号") or "").strip() for r in rows]
        src_all = [s for s in src_all if s]
        uniq_docs = set(src_all)
        matched_docs = {s for s in uniq_docs if s in po_docs}
        rows_matched = sum(1 for r in rows if str(rg(r, "源单单号") or "").strip() in po_docs)

        orders = []
        for (doc, mc), v in po.items():
            if v["status"] not in ALLOWED_STATUS:
                continue
            if v["creator"] not in ALLOWED_SET:
                continue
            if v["qty"] <= 0 or not v["delivery"]:
                continue
            if not (start <= v["delivery"] <= effective_end):
                continue

            rs = receipts.get((doc, mc), [])
            ontime_raw = sum(x["qty"] for x in rs if x["date"] and x["date"] <= v["delivery"])
            ontime = min(ontime_raw, v["qty"])
            rate = ontime / v["qty"] * 100 if v["qty"] > 0 else 0.0
            full = ontime_raw >= v["qty"]

            orders.append({
                "doc": doc,
                "material": mc,
                "supplier": v["supplier"],
                "creator": v["creator"],
                "delivery": v["delivery"].isoformat(),
                "po_qty": round(v["qty"]),
                "ontime": round(ontime),
                "received": round(ontime),
                "remain": round(v["qty"] - ontime),
                "rate": round(min(rate, 100.0), 2),
                "full": full,
                "full_txt": "是" if full else "否",
                "_r": rate,
            })

        sup = defaultdict(lambda: {"ontime": 0.0, "po_qty": 0.0, "orders": 0,
                                   "full": 0, "no_receipt": 0, "partial": 0, "rate_sum": 0.0})
        buy = defaultdict(lambda: {"ontime": 0.0, "po_qty": 0.0, "orders": 0,
                                   "full": 0, "no_receipt": 0, "partial": 0, "rate_sum": 0.0})
        for o in orders:
            for bucket, name in ((sup, o["supplier"] or "（未知）"), (buy, o["creator"])):
                b = bucket[name]
                b["ontime"] += o["ontime"]
                b["po_qty"] += o["po_qty"]
                b["orders"] += 1
                b["rate_sum"] += o["_r"]
                if o["full"]:
                    b["full"] += 1
                if o["ontime"] <= 0:
                    b["no_receipt"] += 1
                elif not o["full"]:
                    b["partial"] += 1

        def _pack(d):
            out = []
            for name, v in d.items():
                rate = (v["ontime"] / v["po_qty"] * 100) if v["po_qty"] > 0 else 0.0
                full_rate = (v["full"] / v["orders"] * 100) if v["orders"] else 0.0
                out.append({
                    "name": name,
                    "ontime": round(v["ontime"]),
                    "po_qty": round(v["po_qty"]),
                    "late": round(v["po_qty"] - v["ontime"]),
                    "rate": round(rate, 2),
                    "rate_capped": round(min(rate, 100.0), 2),
                    "orders": v["orders"],
                    "full_orders": v["full"],
                    "full_rate": round(full_rate, 2),
                    "no_receipt": v["no_receipt"],
                    "partial": v["partial"],
                    "over": rate > 100.5,
                })
            out.sort(key=lambda x: -x["po_qty"])
            return out

        # 缺失源单（数据质量校验，与指标总体无关）
        missing = defaultdict(lambda: {"rows": 0, "qty": 0.0, "dates": []})
        for r in rows:
            doc = str(rg(r, "源单单号") or "").strip()
            if not doc or doc in po_docs:
                continue
            q_assoc = rg(r, "合格入库关联数量")
            q_actual = rg(r, "实收数量")
            status = str(rg(r, "行状态") or "").strip()
            qty = (_num(q_assoc) if str(q_assoc).strip() not in ("", "None")
                   else (_num(q_actual) if status == "正常" else 0.0))
            m = missing[doc]
            m["rows"] += 1
            m["qty"] += qty
            d = _date(rg(r, "收料日期"))
            if d:
                m["dates"].append(d.isoformat())

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

        po_qty = sum(o["po_qty"] for o in orders)
        ontime_total = sum(o["ontime"] for o in orders)
        full_orders = sum(1 for o in orders if o["full"])
        no_receipt = sum(1 for o in orders if o["ontime"] <= 0)
        partial = sum(1 for o in orders if 0 < o["ontime"] < o["po_qty"])
        rate = (ontime_total / po_qty * 100) if po_qty > 0 else 0.0
        order_avg = (sum(o["_r"] for o in orders) / len(orders)) if orders else 0.0

        for o in orders:
            o.pop("_r", None)
        orders.sort(key=lambda o: (o["supplier"], o["delivery"], o["doc"], o["material"]))

        period_data.append({
            "period": period,
            "label": f"{period[:4]}年{int(period[5:7])}月",
            "valid": valid,
            "validity_note": validity_note,
            "delivery_start": start.isoformat(),
            "delivery_end": effective_end.isoformat(),
            "overall": {
                "po_qty": round(po_qty),
                "ontime": round(ontime_total),
                "late": round(po_qty - ontime_total),
                "unfilled": round(po_qty - ontime_total),
                "rate": round(rate, 2),
                "order_avg_rate": round(order_avg, 2),
                "full_orders": full_orders,
                "full_rate": round(full_orders / len(orders) * 100, 2) if orders else 0.0,
                "order_lines": len(orders),
                "no_receipt": no_receipt,
                "partial": partial,
                "ontime_share": round(rate, 2),
            },
            "coverage": {
                "unique_total": len(uniq_docs),
                "unique_matched": len(matched_docs),
                "unique_rate": round(len(matched_docs) / len(uniq_docs) * 100, 2) if uniq_docs else 0.0,
                "rows_total": len(rows),
                "rows_matched": rows_matched,
                "row_rate": round(rows_matched / len(rows) * 100, 2) if rows else 0.0,
                "orders_with_receipt": sum(1 for o in orders if o["ontime"] > 0),
                "orders_with_receipt_rate": round(
                    sum(1 for o in orders if o["ontime"] > 0) / len(orders) * 100, 2
                ) if orders else 0.0,
                "receipt_window_start": min(receipt_dates).isoformat() if receipt_dates else None,
            },
            "suppliers": _pack(sup),
            "buyers": _pack(buy),
            "order_details": orders if valid else [],
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
        "metric": "qty_weighted_delivery_due",
        "metric_label": "按到货期数量加权",
        "creator_whitelist": ALLOWED_CREATORS,
        "excluded_creators": EXCLUDED_CREATORS,
        "receipt_window_start": min(receipt_dates).isoformat() if receipt_dates else None,
        "default_period": period_data[-1]["period"],
        "periods": period_data,
        "known_excluded": KNOWN_EXCLUDED,
    }
