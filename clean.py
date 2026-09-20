# -*- coding: utf-8 -*-
"""
供应链在途+产能 数据清洗脚本
================================
读取 Excel 源表（采购订单 / 产能匹配表 / 可选周计划），按业务规则清洗，
产出静态 data.json 供前端看板零 API 消费。

运行方式（无后端，本地双击或命令行均可）：
    python clean.py
    python clean.py --po "src/采购订单.xlsx" --cap "src/产能.xlsx" --weekly "src/周计划.xlsx"

输出： data.json  （与脚本同目录）

清洗规则（与需求文档一致）：
  ① 删空单    单据编号为空/空白、或 单据类型=='合计' 的行跳过（计 dropped_po）；
              但会先抓取「合计」行的三个数量用于末尾自检
  ② 业务关闭  `业务关闭` == '业务关闭' 的行 **保留**（计 closed_rows），并打 biz_closed 标记。
              理由：这些是"已收完并关单"的行，剩余收料恒为 0 → 保留不影响在途/剩余口径，
              却能保住其 采购数量 与 累计收料数量。（曾误删→采购总量/已收料/完成率系统性低估）
              注意：`作废状态` 整列也保留在明细里，不删
  ③ SPU 取码  SPU = 物料编码 仅留数字、取前 4 位（spu_of）
  ④ 交货日期  归一化为 YYYY-M-D（fmt_date）
  ⑤ 月份推导  由交货日期「月」推导 M月；无日期记 —
  ⑥ 标签取源  产线标签 / 时效标签 = 源表同名列（空则留空）
  ⑦ 字段映射  供应商简称 = 产能表.供应商简称（按供应商全称 join）
  ⑧ 自检      汇总的 Σ采购数量/Σ已收料/Σ剩余收料 必须等于源表「合计」行，否则控制台报 ❌
"""
import os
import re
import sys
import json
import argparse
import datetime as dt
from collections import Counter, defaultdict

try:
    import openpyxl
except ImportError:
    sys.exit("缺少依赖 openpyxl，请先: pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")

# 核心供应商简称（需求固定清单）
CORE_SUPPLIERS = ["忆恩", "佳俊", "同光", "拿可", "宝莎", "贝瑞卡", "浩川", "骏航", "思哲"]

# 手动简称覆盖：以下供应商不在产能表中，join 拿不到简称（否则短名会落成全称）
SHORT_OVERRIDE = {
    "广州市顺进皮具有限公司": "顺进",
    "广州顺进皮具有限公司": "顺进",
    "广州市苏弗儿皮具有限公司": "苏弗儿",
    "广州苏弗儿皮具有限公司": "苏弗儿",
    "广州明冠实业有限公司": "明冠",
    "广州市明冠实业有限公司": "明冠",
}


def short_of(full, cap):
    """简称优先级：手动覆盖 > 产能表 > 全称"""
    return SHORT_OVERRIDE.get(full) or (cap.get("short", full) if cap else full)


def spu_of(material_code):
    """③ SPU 取码：物料编码仅留数字、取前 4 位"""
    if material_code is None:
        return ""
    digits = "".join(ch for ch in str(material_code) if ch.isdigit())
    return digits[:4]


def fmt_date(v):
    """④ 交货日期归一化为 YYYY-M-D；无法解析返回 None"""
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    if isinstance(v, (dt.datetime, dt.date)):
        return f"{v.year}-{v.month}-{v.day}"
    s = str(v).strip().replace(" 00:00:00", "").replace(" 00:00", "")
    # 形如 2026/10/6 或 2026-10-06
    for sep in ("/", "-", "."):
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 3:
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2][:2])
                    return f"{y}-{m}-{d}"
                except ValueError:
                    pass
    return None


def parse_date(v):
    s = fmt_date(v)
    if not s:
        return None
    try:
        y, m, d = s.split("-")
        return dt.date(int(y), int(m), int(d))
    except Exception:
        return None


def month_of(date_obj):
    """⑤ 月份推导：M月；无日期 —"""
    return f"{date_obj.month}月" if date_obj else "—"


def to_num(v):
    """安全转数字，None/空 -> 0"""
    if v is None:
        return 0
    if isinstance(v, str):
        v = v.strip().replace(",", "")
        if v == "":
            return 0
    try:
        return float(v)
    except ValueError:
        return 0


def ifx(v):
    """整数就写成整数（JSON 少 2 字节/个），否则保留 2 位小数。用于压缩 data.json。"""
    v = to_num(v)
    return int(v) if abs(v - round(v)) < 1e-9 else round(v, 2)


def find_file(folder, *keywords):
    """在 folder 中按关键字模糊匹配第一个 xlsx（忽略大小写）"""
    if not os.path.isdir(folder):
        return None
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith(".xlsx") and not fn.startswith("~$"):
            low = fn.lower()
            if all(k.lower() in low for k in keywords):
                return os.path.join(folder, fn)
    return None


def find_all_matches(folder, *keywords):
    """返回 folder 中所有匹配关键字的 xlsx（按名称排序）"""
    if not os.path.isdir(folder):
        return []
    hits = []
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith(".xlsx") and not fn.startswith("~$"):
            low = fn.lower()
            if all(k.lower() in low for k in keywords):
                hits.append(os.path.join(folder, fn))
    return hits


def pick_unique(folder, keyword, label):
    """要求该关键字在 folder 下只对应一份源表；多份则报错中止。

    历史坑：find_file 只取排序后的第一个匹配项，于是把带日期的新导出文件
    （如「采购订单_20260918xxx.xlsx」）放进 src/ 时，旧的「采购订单.xlsx」
    因为字符 '.'(0x2E) < '_'(0x5F) 仍然排在前面 → 静默继续用旧数据，
    表现为「流水线成功、页面时间戳也变了，但数字没动」的假刷新。
    这里改为显式报错，宁可失败也不用错数据。
    """
    hits = find_all_matches(folder, keyword)
    if not hits:
        return None
    if len(hits) > 1:
        names = "\n".join("    - " + os.path.basename(h) for h in hits)
        sys.exit(
            "[源表冲突] %s：%s 下匹配到多份文件：\n%s\n"
            "  解决办法：只保留一份。带日期的新导出请【改名覆盖】为原文件名，或删掉旧文件。\n"
            "  （带日期的新文件直接放进去不会生效，且会让流水线不知道该用哪份——故此处主动中止。）"
            % (label, folder, names)
        )
    return hits[0]


def load_first_sheet(path):
    # 注意：某些 WPS/金蝶导出的 xlsx 在 read_only=True 下会漏读行（max_row=1），
    # 因此去掉 read_only，改用普通模式加载。
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    wb.close()
    if not rows:
        return [], []
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    return header, rows[1:]


def load_capacity(path):
    """产能及简称和采购员匹配表：供应商/供应商简称/采购负责人/月产能"""
    cap = {}
    if not path or not os.path.exists(path):
        return cap
    header, rows = load_first_sheet(path)
    idx = {h: i for i, h in enumerate(header)}
    g = lambda r, k: r[idx[k]] if k in idx and idx[k] < len(r) else None
    for r in rows:
        name = g(r, "供应商")
        if not name:
            continue
        cap[str(name).strip()] = {
            "full": str(name).strip(),
            "short": str(g(r, "供应商简称") or name).strip(),
            "buyer": str(g(r, "采购负责人") or "").strip(),
            "month_cap": to_num(g(r, "月产能")),
        }
    return cap


def month_from_source(path, extra=None):
    """周计划月份推导：优先 extra(上传日期)，否则解析文件名日期(M.D / YYYY-M-D)，+31 天取月；失败回退当前月。"""
    base = dt.date.today()
    cand = parse_date(extra) if extra else None
    if not cand:
        fn = os.path.basename(path)
        m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", fn)
        if m:
            try:
                cand = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                cand = None
        else:
            m = re.search(r"(\d{1,2})[-/.](\d{1,2})", fn)
            if m:
                try:
                    cand = dt.date(base.year, int(m.group(1)), int(m.group(2)))
                except ValueError:
                    cand = None
    if cand:
        return f"{(cand + dt.timedelta(days=31)).month}月"
    return f"{base.month}月"


def load_weekly(path, cap_map):
    """周计划表：sku / 物料名称 / 规格型号 / 数量 / 采购负责人 / 供应商（供应商全称需映射简称）。
    返回 list[dict]，字段与前端第5页一致： supplier_full/supplier_short/sku/spu/material_name/spec/buyer/plan_qty/month"""
    if not path or not os.path.exists(path):
        return []
    header, rows = load_first_sheet(path)
    idx = {h: i for i, h in enumerate(header)}
    out = []
    for r in rows:
        def g(k):
            return r[idx[k]] if k in idx and idx[k] < len(r) else None
        full = g("供应商") or g("供应商全称") or g("厂商")
        if not full:
            continue
        full = str(full).strip()
        cap = cap_map.get(full, {})
        short = short_of(full, cap)
        sku = str(g("sku") or g("SKU") or g("物料编码") or g("编码") or "").strip()
        plan = to_num(g("数量") or g("计划数量") or g("计划数"))
        if plan <= 0:
            continue
        out.append({
            "supplier_full": full,
            "supplier_short": short,
            "sku": sku,
            "spu": spu_of(sku),
            "material_name": str(g("物料名称") or "").strip(),
            "spec": str(g("规格型号") or "").strip(),
            "buyer": str(g("采购负责人") or cap.get("buyer", "") or "").strip(),
            "plan_qty": plan,
            "month": month_from_source(path, g("上传日期") or g("导入日期") or g("日期")),
        })
    return out


def clean():
    ap = argparse.ArgumentParser()
    ap.add_argument("--po", default=None)
    ap.add_argument("--cap", default=None)
    ap.add_argument("--weekly", default=None)
    ap.add_argument("--src", default=SRC)
    args = ap.parse_args()

    po_path = args.po or pick_unique(args.src, "采购订单", "采购订单")
    cap_path = args.cap or pick_unique(args.src, "产能", "产能匹配表")
    weekly_path = args.weekly or pick_unique(args.src, "周计划", "周计划")
    if not po_path:
        sys.exit(f"未找到采购订单 Excel，请放到 {args.src} 目录（文件名含'采购订单'）")
    print("源表: 采购订单=%s | 产能=%s | 周计划=%s" % (
        os.path.basename(po_path),
        os.path.basename(cap_path) if cap_path else "（无）",
        os.path.basename(weekly_path) if weekly_path else "（无）",
    ))

    cap_map = load_capacity(cap_path)
    weekly = load_weekly(weekly_path, cap_map)

    header, rows = load_first_sheet(po_path)
    idx = {h: i for i, h in enumerate(header)}
    g = lambda r, k: r[idx[k]] if k in idx and idx[k] < len(r) else None

    orders = []
    dropped_po = 0
    closed_rows = 0
    erp_total = {}   # 源表底部「合计」行，用于自检：我们的汇总必须等于它

    for r in rows:
        bid = g(r, "单据编号")
        dtype = g(r, "单据类型")
        # ① 删空单 / “合计”汇总行（但先抓下合计值用于自检）
        if bid is None or str(bid).strip() == "" or (dtype is not None and str(dtype).strip() == "合计"):
            for _k, _col in (("po", "采购数量"), ("received", "累计收料数量"), ("remain", "剩余收料数量")):
                _v = to_num(g(r, _col))
                if _v:
                    erp_total[_k] = _v
            dropped_po += 1
            continue
        # ② 「业务关闭」的行 —— 【保留，不再删除】
        #    它们都是“已收完并关单”的行：剩余收料恒为 0，所以保留不影响在途/剩余口径，
        #    却能保住其 采购数量 与 累计收料数量。
        #    历史坑：这里曾整行删除，导致 采购总量 / 已收料 / 完成率 被系统性低估
        #    （例：CGDD012512 应显示 采购 19,350 / 已收 7,500，却被算成 11,850 / 0，
        #      全局完成率 25.5% 被压成 16.1%）。
        biz_closed = str(g(r, "业务关闭") or "").strip() == "业务关闭"
        if biz_closed:
            closed_rows += 1

        full = str(g(r, "供应商") or "").strip()
        cap = cap_map.get(full, {})
        short = short_of(full, cap)
        buyer = cap.get("buyer", "") if cap else ""
        month_cap = cap.get("month_cap", 0) if cap else 0

        mc = g(r, "物料编码")
        deliv_raw = g(r, "交货日期")
        deliv = parse_date(deliv_raw)
        deliv_str = fmt_date(deliv_raw)

        po_qty = to_num(g(r, "采购数量"))
        remain = to_num(g(r, "剩余收料数量"))
        received = po_qty - remain if po_qty >= remain else to_num(g(r, "累计收料数量"))
        received = max(received, 0)

        # 状态 / 逾期 / 剩余 天数
        today = dt.date.today()
        if remain > 0:
            if deliv and deliv < today:
                overdue_days = (today - deliv).days
                status = f"逾期{overdue_days}天"
            else:
                remain_days = (deliv - today).days if deliv else 0
                status = f"剩{remain_days}天" if deliv else "待交期"
        else:
            status = "已完成"
            overdue_days = 0
            remain_days = 0

        rate = (received / po_qty) if po_qty > 0 else 0

        orders.append({
            "doc_no": str(bid).strip(),
            "doc_type": str(dtype).strip() if dtype else "",
            "supplier": full,
            "supplier_short": short,
            "buyer": buyer,
            "material_code": str(mc).strip() if mc else "",
            "spu": spu_of(mc),
            "material_name": str(g(r, "物料名称") or "").strip(),
            "spec": str(g(r, "规格型号") or "").strip(),
            "po_qty": ifx(po_qty),
            "received": ifx(received),
            "remain": ifx(remain),
            "delivery": deliv_str,
            "month": month_of(deliv),
            "pline": str(g(r, "产线标签") or "").strip() if g(r, "产线标签") else "",
            "timing": str(g(r, "时效标签") or "").strip() if g(r, "时效标签") else "",
            "close_status": str(g(r, "关闭状态") or "").strip(),
            "void_status": str(g(r, "作废状态") or "").strip(),
            "biz_closed": biz_closed,
            "rate": round(rate * 100, 2),
            "status": status,
            "overdue_days": overdue_days if (remain > 0 and deliv and deliv < today) else 0,
            "remain_days": remain_days if (remain > 0 and deliv and deliv >= today) else 0,
            "is_core": short in CORE_SUPPLIERS,
            "month_cap": ifx(month_cap),
            "creator": str(g(r, "创建人") or "").strip(),
        })

    # ---------- 自检：汇总结果必须等于源表「合计」行 ----------
    sum_po = sum(o["po_qty"] for o in orders)
    sum_rec = sum(o["received"] for o in orders)
    sum_rem = sum(o["remain"] for o in orders)
    checks = []
    for _k, _label, _got in (("po", "采购数量", sum_po), ("received", "累计收料数量", sum_rec), ("remain", "剩余收料数量", sum_rem)):
        _exp = erp_total.get(_k)
        if _exp is None:
            checks.append((_label, _got, None, None))
        else:
            checks.append((_label, _got, _exp, abs(_got - _exp) < 0.5))

    meta = {
        "updated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_po": os.path.basename(po_path),
        "source_cap": os.path.basename(cap_path) if cap_path else None,
        "source_weekly": os.path.basename(weekly_path) if weekly_path else None,
        "source_rows": len(rows),
        "dropped_po": dropped_po,
        "closed_rows": closed_rows,
        "order_count": len(orders),
        "capacity_count": len(cap_map),
        "weekly_count": len(weekly),
        "core_suppliers": CORE_SUPPLIERS,
        "today": dt.date.today().strftime("%Y-%m-%d"),
        "sum_po": round(sum_po),
        "sum_received": round(sum_rec),
        "sum_remain": round(sum_rem),
        "erp_total": {k: round(v) for k, v in erp_total.items()},
        "self_check_ok": all(c[3] is not False for c in checks) if any(c[2] is not None for c in checks) else None,
    }

    # 列式编码：orders 是 4k+ 行 × 25 字段，若写成对象数组，光重复的键名就约 1.2MB。
    # 改为「列名数组 + 行数组」后可省约 58% 体积（前端一次性还原成对象，见 index.template.html）。
    _ocols = list(orders[0].keys()) if orders else []
    _orows = [[o.get(c) for c in _ocols] for o in orders]
    out = {"meta": meta, "orders_cols": _ocols, "orders_rows": _orows,
           "capacity": list(cap_map.values()), "weekly": weekly}
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    # 控制台摘要
    print("=== 清洗完成 ===")
    print(f"源行数: {meta['source_rows']}  删除空单/合计行: {dropped_po}  保留业务关闭行: {closed_rows}")
    print(f"有效订单: {meta['order_count']}  产能供应商: {meta['capacity_count']}  周计划: {meta['weekly_count']}")
    print(f"核心供应商命中: {sum(1 for o in orders if o['is_core'])} 家订单")
    ov = [o for o in orders if o['overdue_days'] > 0]
    print(f"逾期订单数: {len(ov)}  逾期供应商数: {len(set(o['supplier_short'] for o in ov))}")
    print(f"Σ采购数量={sum_po:,.0f}  Σ已收料={sum_rec:,.0f}  Σ剩余收料={sum_rem:,.0f}")

    print("=== 自检：与源表「合计」行比对 ===")
    if not erp_total:
        print("  ⚠️ 源表未找到「合计」行，跳过校验")
    _bad = []
    for _label, _got, _exp, _ok in checks:
        if _exp is None:
            print(f"  {_label}: 合计行无此列（跳过）")
        elif _ok:
            print(f"  ✅ {_label}: {_got:,.0f} == 合计行 {_exp:,.0f}")
        else:
            _bad.append((_label, _got, _exp))
            print(f"  ❌ {_label}: {_got:,.0f} != 合计行 {_exp:,.0f}  (差 {_got - _exp:+,.0f})")

    if _bad:
        sys.exit(
            "\n[自检失败] 清洗后的汇总与源表「合计」行不一致，共 %d 项：\n%s\n"
            "  说明清洗规则把某些行算多/算少了（例如误删了不该删的行）。\n"
            "  为避免看板长期展示错误数据，此处主动中止。请检查 clean() 里的剔除规则。"
            % (len(_bad), "\n".join("    - %s: 我们 %s vs 合计行 %s" % (l, "{:,.0f}".format(g), "{:,.0f}".format(e)) for l, g, e in _bad))
        )


if __name__ == "__main__":
    clean()
