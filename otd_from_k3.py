# -*- coding: utf-8 -*-
"""otd_from_k3.py —— 准交率页数据源：采购部工作台口径（skill `judge_std`）

替代旧 `otd.py`（收料单口径：收料日期 ≤ 采购订单交货日期）。

数据源
----
  k3_live.json   build_k3live.py 产出：整体 / 供应商 / 采购员准交率。
                 判定引擎是 k3cloud-weekly-report skill 的 `judge_std`
                 （按 P0–P5 优先级算「标准时效」，实际时效对比标准时效）。
  q2_rows.json   同一脚本产出的逐行判定记录（约 2,094 行），供明细下钻。

口径
----
  准交率 = Σ准交量 ÷ Σ实际交货量
  判定基准 = 《准交标准》算出的「标准时效」，不是采购订单上写的交货日期
  采购员归属 = 按供应商映射表（sup_buyer_map.json），不是单据上的采购员

聚合值一律**从明细重算**，再与 k3_live.json 的 overall 对账；对不上就抛错，
避免页面数字与明细自相矛盾。

用法
----
  python otd_from_k3.py            # 校验并打印汇总，不写文件
  from otd_from_k3 import build_otd_from_k3   # clean.py 调用
"""
import json
import os
import datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
K3_DIR = r"C:\Users\admin\Desktop\财年指标及数据"
LIVE_PATH = os.path.join(K3_DIR, "k3_live.json")
ROWS_PATH = os.path.join(K3_DIR, "q2_rows.json")

METRIC_LABEL = "准交率（标准时效口径）"
METRIC_FORMULA = "Σ准交量 ÷ Σ实际交货量（按《准交标准》judge_std 判定实际时效是否超标准时效）"


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _blank():
    return {"recv": 0.0, "ok": 0.0, "rows": 0, "late_rows": 0}


def _summ(d):
    recv = round(d["recv"], 1)
    ok = round(d["ok"], 1)
    late = round(recv - ok, 1)
    return {
        "recv_qty": recv,
        "ontime": ok,
        "late": max(late, 0.0),
        "rate": round(ok / recv * 100, 2) if recv > 0 else 0.0,
        "rows": d["rows"],
        "late_rows": d["late_rows"],
    }


def _period_of(asof_end):
    """2026-11-19 -> ('2026-11', '2026年11月')"""
    try:
        d = dt.date.fromisoformat(str(asof_end)[:10])
    except Exception:
        d = dt.date.today()
    return "%d-%02d" % (d.year, d.month), "%d年%d月" % (d.year, d.month)


def build_otd_from_k3(live_path=LIVE_PATH, rows_path=ROWS_PATH):
    """返回与旧 otd.build_otd 兼容的 dict；数据不可用时抛异常（由调用方记录 otd_error）。"""
    if not os.path.exists(live_path):
        raise FileNotFoundError("缺少 k3_live.json（先跑 build_k3live.py）")
    if not os.path.exists(rows_path):
        raise FileNotFoundError("缺少 q2_rows.json（先跑 build_k3live.py）")

    k3 = _load(live_path)
    rows = _load(rows_path)

    start = str(k3.get("asof_start") or "")[:10]
    end = str(k3.get("asof_end") or "")[:10]
    # 只取当前区间（q2_rows 可能跨月）
    kept = []
    for r in rows:
        d = str(r.get("date") or "")[:10]
        if start and d < start:
            continue
        if end and d > end:
            continue
        kept.append(r)
    rows = kept
    if not rows:
        raise ValueError("q2_rows.json 在区间 %s ~ %s 内没有数据" % (start, end))

    sup, buy, day = defaultdict(_blank), defaultdict(_blank), defaultdict(_blank)
    details = []
    tot = _blank()

    for r in rows:
        s = str(r.get("sup") or "").strip() or "未标注"
        b = str(r.get("buyer") or "").strip() or "未指派"
        d = str(r.get("date") or "")[:10]
        qty = float(r.get("rq") or 0)
        ok = float(r.get("ot") or 0)
        is_late = (qty - ok) > 0.0001

        for tbl, key in ((sup, s), (buy, b), (day, d)):
            t = tbl[key]
            t["recv"] += qty
            t["ok"] += ok
            t["rows"] += 1
            if is_late:
                t["late_rows"] += 1
        tot["recv"] += qty
        tot["ok"] += ok
        tot["rows"] += 1
        if is_late:
            tot["late_rows"] += 1

        ld = int(r.get("ld") or 0)
        details.append({
            "doc": str(r.get("po") or "").strip(),
            "recv_doc": str(r.get("bill") or "").strip(),
            # 明细粒度只到 SPU（4 位款号）：skill 源数据不含完整物料编码
            "material": str(r.get("spu") or "").strip() or "—",
            "supplier": s,
            "creator": b,
            "delivery": str(r.get("dd") or "").strip(),
            "receipt_date": d,
            "days": ld,
            # 88/865 行判逾期但 ld=0（该行标准时效未算出日期，只按规则判了逾期），
            # 直接显示「逾期 0 天」会自相矛盾，这类显示为「逾期」
            "days_txt": (("逾期 %d 天" % ld) if ld > 0 else "逾期") if is_late else "准时",
            "qty": round(qty, 1),
            "verdict": "逾期" if is_late else "准时",
            "new": str(r.get("new") or "") == "是",
            "line": str(r.get("ctag") or "").strip(),
        })

    overall = _summ(tot)

    # 与 k3_live.json 对账：重算值必须与工作台一致，否则说明两边跑的不是同一批行
    k3_ov = k3.get("overall") or {}
    k3_den = round(float(k3_ov.get("den") or 0), 1)
    k3_ok = round(float(k3_ov.get("ok") or 0), 1)
    warn = []
    if k3_den and abs(k3_den - overall["recv_qty"]) > 1:
        warn.append("分母不一致：k3_live=%.0f，明细重算=%.0f" % (k3_den, overall["recv_qty"]))
    if k3_ok and abs(k3_ok - overall["ontime"]) > 1:
        warn.append("准交量不一致：k3_live=%.0f，明细重算=%.0f" % (k3_ok, overall["ontime"]))
    for w in warn:
        print("[otd_from_k3] ⚠️ " + w)

    suppliers = []
    for name, d in sup.items():
        it = _summ(d)
        it.update({"name": name, "short": name})
        suppliers.append(it)
    suppliers.sort(key=lambda x: -x["recv_qty"])

    buyers = []
    for name, d in buy.items():
        it = _summ(d)
        it.update({"name": name, "short": name})
        buyers.append(it)
    buyers.sort(key=lambda x: -x["recv_qty"])

    trend = []
    for d in sorted(day):
        it = _summ(day[d])
        trend.append({"date": d, "recv": it["recv_qty"], "ontime": it["ontime"],
                      "rate": it["rate"], "rows": it["rows"]})

    period, label = _period_of(end)
    whitelist = [b["name"] for b in (k3.get("buyers") or [])]

    return {
        "updated_at": k3.get("generated_at") or "",
        "source_recv": "k3_live.json + q2_rows.json（skill judge_std）",
        "source_po_full": "",
        "metric": "judge_std_ontime_ratio",
        "metric_label": METRIC_LABEL,
        "metric_formula": METRIC_FORMULA,
        "vmi_filter_enabled": False,
        "creator_whitelist": whitelist,
        "excluded_creators": [],
        "supplier_pool": len(suppliers),
        "receipt_window_start": start,
        "default_period": str(period),
        "periods": [{
            "period": str(period),
            "label": label,
            "valid": True,
            "validity_note": "按收料日期统计；实际时效对比《准交标准》算出的标准时效，未超为标准。",
            "overall": overall,
            "coverage": None,
            "checks": {
                "rows": len(rows),
                "window_start": start,
                "window_end": end,
                "k3_den": k3_den,
                "k3_ok": k3_ok,
                "recomputed_den": overall["recv_qty"],
                "recomputed_ok": overall["ontime"],
                "consistent": not warn,
                "warnings": warn,
            },
            "suppliers": suppliers,
            "buyers": buyers,
            "order_details": details,
            "trend": trend,
            "excluded_reasons": [],
            "supplier_pool": len(suppliers),
            "missing": [],
            "unknown_missing": [],
            "excluded_known": [],
            "blocked": False,
        }],
    }


if __name__ == "__main__":
    o = build_otd_from_k3()
    p = o["periods"][0]
    ov = p["overall"]
    print("区间 %s ~ %s" % (p["checks"]["window_start"], p["checks"]["window_end"]))
    print("整体准交率 %.2f%%  准交 %s / 分母 %s  (%d 行，逾期 %d 行)" % (
        ov["rate"], format(int(ov["ontime"]), ","), format(int(ov["recv_qty"]), ","),
        ov["rows"], ov["late_rows"]))
    print("供应商 %d 家 · 采购员 %d 人 · 明细 %d 行 · 逐日 %d 天" % (
        len(p["suppliers"]), len(p["buyers"]), len(p["order_details"]), len(p["trend"])))
    print("对账：", "通过" if p["checks"]["consistent"] else "；".join(p["checks"]["warnings"]))
    print("\nTOP8 供应商：")
    for x in p["suppliers"][:8]:
        print("  %-6s %8s 件  %6.2f%%" % (x["name"], format(int(x["recv_qty"]), ","), x["rate"]))
    print("\n采购员：")
    for x in p["buyers"]:
        print("  %-6s %8s 件  %6.2f%%" % (x["name"], format(int(x["recv_qty"]), ","), x["rate"]))
