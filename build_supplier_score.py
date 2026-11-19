# -*- coding: utf-8 -*-
"""build_supplier_score.py —— 生成「供应商综合评估」数据，写入 data.json 的 supplier_score 键。

口径（2026-11-19 锁定）：
  综合分 = 准交率×40% + 逾期控制×30% + 产能负荷×15% + 新品准交率×15%
  （2026-11-19 改：移除款数维度；矩阵 X=综合分，Y=总准交率）

  准交率     : 采购部工作台 k3_live.json 的 suppliers（judge_std，工作台口径，照搬不修）
  逾期控制   : 逾期未交量÷当月在途，min-max 反向归一化 × 准交修正系数(0.5+0.5×rate)
  产能负荷   : 当月在途 ÷ (月产能 × 当月剩余天数比)；85%-100% 满分，过低/过载递减
  款数规模   : 订单 SPU 去重数 min-max 正向

边界：在途为 0 不显示；核心/普通分组；无准交率不评分。

用法：
  python build_supplier_score.py            # 用现有 k3_live.json
  python build_supplier_score.py --refresh  # 先跑 build_k3live.py 刷新准交率再算
"""
import os, sys, json, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")
# 采购部工作台的准交率数据源（单一事实源，与工作台同源）
K3LIVE = r"C:\Users\admin\Desktop\财年指标及数据\k3_live.json"
BUILD_K3LIVE = r"C:\Users\admin\Desktop\财年指标及数据\build_k3live.py"
VENV_PY = r"C:\Users\admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if "--refresh" in sys.argv:
        import subprocess
        print("[score] 刷新准交率（build_k3live.py）…")
        r = subprocess.run([VENV_PY, BUILD_K3LIVE],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("[score] 准交率刷新失败，沿用现有 k3_live.json")
            print((r.stdout or "")[-600:])
        else:
            print("[score] 准交率已刷新")

    d = load_json(DATA)
    k3 = load_json(K3LIVE)

    # 供应商准交率（工作台口径）
    otd = {}
    for s in k3.get("suppliers", []):
        name = str(s.get("name") or "").strip()
        if not name:
            continue
        otd[name] = {
            "rate": round(float(s.get("rate") or 0) * 100, 2),
            "ok": int(s.get("ok") or 0),
            "den": int(s.get("den") or 0),
            "rows": int(s.get("rows") or 0),
            "new_rate": round(float(s.get("newRate") or 0) * 100, 2),
            "new_ok": int(s.get("newOk") or 0),
            "new_den": int(s.get("newDen") or 0),
        }

    core = set(d.get("meta", {}).get("core_suppliers", []))
    cols = d.get("orders_cols", [])
    rows = d.get("orders_rows", [])
    ix = {c: i for i, c in enumerate(cols)}
    capacity = {c["short"]: float(c.get("month_cap") or 0)
                for c in d.get("capacity", [])}

    # 按供应商聚合：当月在途 / 逾期未交 / SPU
    agg = defaultdict(lambda: {"cur": 0.0, "od": 0.0, "spus": set(), "new_cur": 0.0})
    for r in rows:
        s = r[ix["supplier_short"]] or "未标注"
        a = agg[s]
        rem = float(r[ix["remain"]] or 0)
        if str(r[ix["month"]] or "") == "11月":
            a["cur"] += rem
        a["spus"].add(str(r[ix["spu"]] or ""))
        # 在途新品：时效标签含 新品/新变体/爆款
        timing = str(r[ix.get("timing", 0)] or "") if "timing" in ix else ""
        if rem > 0 and any(k in timing for k in ("新品", "新变体", "爆款")):
            a["new_cur"] += rem
        try:
            od = int(r[ix["overdue_days"]] or 0)
        except (TypeError, ValueError):
            od = 0
        if od > 0:
            a["od"] += rem

    # 当月剩余产能比例
    today = dt.date.today()
    if today.month == 11:
        total_days, left_days = 30, max(1, 30 - today.day + 1)
    else:
        import calendar
        total_days = calendar.monthrange(today.year, today.month)[1]
        left_days = max(1, total_days - today.day + 1)
    ratio = left_days / total_days

    sups = [s for s in agg if agg[s]["cur"] > 0]

    def norm(vals, rev=False):
        lo, hi = min(vals), max(vals)
        if hi == lo:
            return lambda v: 50.0
        return (lambda v: (hi - v) / (hi - lo) * 100) if rev else \
               (lambda v: (v - lo) / (hi - lo) * 100)

    f_od = norm([agg[s]["od"] / max(agg[s]["cur"], 1) for s in sups], True)

    def load_score(v):
        """产能负荷：85%-100% 满分，过低/过载递减"""
        if v <= 0:
            return 0.0
        if 0.85 <= v <= 1.0:
            return 100.0
        if v < 0.85:
            return max(0.0, (v / 0.85) * 60 + 40)
        return max(0.0, 100 - (v - 1.0) / 0.5 * 60)

    result = []
    for s in sups:
        o = otd.get(s)
        if not o:
            continue  # 无准交率不评分
        a = agg[s]
        rate = o["rate"]
        od_score = f_od(a["od"] / max(a["cur"], 1)) * (0.5 + 0.5 * rate / 100)
        load_ratio = a["cur"] / max(capacity.get(s, 0) * ratio, 1)
        ld_score = load_score(load_ratio)
        # 新品准交率：无新品分母时给中性分 50，不惩罚
        new_score = o["new_rate"] if o["new_den"] > 0 else 50.0
        score = rate * 0.40 + od_score * 0.30 + ld_score * 0.15 + new_score * 0.15
        result.append({
            "short": s,
            "core": s in core,
            "score": round(score, 1),
            "rate": rate,
            "od": round(a["od"]),
            "cur": round(a["cur"]),
            "load": round(load_ratio * 100),
            "new_rate": new_score if o["new_den"] > 0 else None,
            "new_ok": o["new_ok"],
            "new_den": o["new_den"],
            "new_cur": round(a["new_cur"]),
            "recv_rows": o["rows"],
            "detail": {
                "rate": round(rate, 1), "od": round(a["od"]), "cur": round(a["cur"]),
                "load": round(load_ratio * 100), "new_rate": round(new_score, 1),
                "score_parts": [
                    {"label": "准交率", "value": round(rate, 1), "weight": 40, "contrib": round(rate * 0.4, 1)},
                    {"label": "逾期控制", "value": round(od_score, 1), "weight": 30, "contrib": round(od_score * 0.3, 1)},
                    {"label": "产能负荷", "value": round(ld_score, 1), "weight": 15, "contrib": round(ld_score * 0.15, 1)},
                    {"label": "新品准交", "value": round(new_score, 1), "weight": 15, "contrib": round(new_score * 0.15, 1)},
                ],
            },
        })

    result.sort(key=lambda x: (-x["core"], -x["score"]))
    for i, x in enumerate(result):
        x["rank"] = sum(1 for y in result if y["core"] == x["core"] and y["score"] > x["score"]) + 1

    payload = {
        "updated_at": k3.get("generated_at", ""),
        "asof_start": k3.get("asof_start", ""),
        "asof_end": k3.get("asof_end", ""),
        "source": k3.get("source", ""),
        "metric": "工作台口径 judge_std（同采购部工作台）",
        "formula": "准交率40% + 逾期控制30% + 产能负荷15% + 新品准交15%",
        "load_note": "当月在途 ÷ (月产能 × 剩余天数比)，%d/%d 天" % (left_days, total_days),
        "overall": round(k3.get("overall", {}).get("rate", 0) * 100, 2),
        "rows": result,
    }
    d["supplier_score"] = payload
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print("[score] 已写入 data.json supplier_score：%d 家（核心 %d / 普通 %d）" % (
        len(result), sum(1 for x in result if x["core"]), sum(1 for x in result if not x["core"])))
    print("[score] 准交率源：%s ~ %s，整体 %.1f%%" % (
        payload["asof_start"], payload["asof_end"], payload["overall"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
