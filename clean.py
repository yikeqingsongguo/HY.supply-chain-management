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
  ① 删空单    单据编号为空/空白 的行跳过（计 dropped_po）
  ② 删业务关闭 `业务关闭` 列 == '业务关闭' 的行跳过（计 dropped_closed）
              注意：保留 `作废状态` 整列在明细里，不删
  ③ SPU 取码  SPU = 物料编码 仅留数字、取前 4 位（spu_of）
  ④ 交货日期  归一化为 YYYY-M-D（fmt_date）
  ⑤ 月份推导  由交货日期「月」推导 M月；无日期记 —
  ⑥ 标签取源  产线标签 / 时效标签 = 源表同名列（空则留空）
  ⑦ 字段映射  供应商简称 = 产能表.供应商简称（按供应商全称 join）
"""
import os
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


def load_first_sheet(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
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


def load_weekly(path):
    """周计划表（可选）：尽力映射 供应商/物料编码/计划数量/上传日期。
    字段名不确定时做容错，缺失列用 None。返回 list[dict]。"""
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
        mc = g("物料编码") or g("编码")
        plan = to_num(g("计划数量") or g("数量") or g("计划数"))
        up = g("上传日期") or g("导入日期") or g("日期")
        up_date = parse_date(up)
        out.append({
            "supplier_full": str(full).strip(),
            "material_code": str(mc).strip() if mc else "",
            "spu": spu_of(mc),
            "plan_qty": plan,
            "upload_date": fmt_date(up),
            # 周计划恒待下单；月份按 上传日期+31天 推导
            "month": month_of(up_date + dt.timedelta(days=31)) if up_date else "—",
        })
    return out


def clean():
    ap = argparse.ArgumentParser()
    ap.add_argument("--po", default=None)
    ap.add_argument("--cap", default=None)
    ap.add_argument("--weekly", default=None)
    ap.add_argument("--src", default=SRC)
    args = ap.parse_args()

    po_path = args.po or find_file(args.src, "采购订单")
    cap_path = args.cap or find_file(args.src, "产能")
    weekly_path = args.weekly or find_file(args.src, "周计划")
    if not po_path:
        sys.exit(f"未找到采购订单 Excel，请放到 {args.src} 目录（文件名含'采购订单'）")

    cap_map = load_capacity(cap_path)
    weekly = load_weekly(weekly_path)

    header, rows = load_first_sheet(po_path)
    idx = {h: i for i, h in enumerate(header)}
    g = lambda r, k: r[idx[k]] if k in idx and idx[k] < len(r) else None

    orders = []
    dropped_po = 0
    dropped_closed = 0

    for r in rows:
        bid = g(r, "单据编号")
        dtype = g(r, "单据类型")
        # ① 删空单（含“合计”汇总行）
        if bid is None or str(bid).strip() == "":
            dropped_po += 1
            continue
        if dtype is not None and str(dtype).strip() == "合计":
            dropped_po += 1
            continue
        # ② 删业务关闭
        biz_close = g(r, "业务关闭")
        if biz_close is not None and str(biz_close).strip() == "业务关闭":
            dropped_closed += 1
            continue

        full = str(g(r, "供应商") or "").strip()
        cap = cap_map.get(full, {})
        short = cap.get("short", full) if cap else full
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
            "po_qty": po_qty,
            "received": received,
            "remain": remain,
            "delivery": deliv_str,
            "month": month_of(deliv),
            "pline": str(g(r, "产线标签") or "").strip() if g(r, "产线标签") else "",
            "timing": str(g(r, "时效标签") or "").strip() if g(r, "时效标签") else "",
            "close_status": str(g(r, "关闭状态") or "").strip(),
            "void_status": str(g(r, "作废状态") or "").strip(),
            "rate": round(rate * 100, 2),
            "status": status,
            "overdue_days": overdue_days if (remain > 0 and deliv and deliv < today) else 0,
            "remain_days": remain_days if (remain > 0 and deliv and deliv >= today) else 0,
            "is_core": short in CORE_SUPPLIERS,
            "month_cap": month_cap,
        })

    meta = {
        "updated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_po": os.path.basename(po_path),
        "source_cap": os.path.basename(cap_path) if cap_path else None,
        "source_weekly": os.path.basename(weekly_path) if weekly_path else None,
        "source_rows": len(rows),
        "dropped_po": dropped_po,
        "dropped_closed": dropped_closed,
        "order_count": len(orders),
        "capacity_count": len(cap_map),
        "weekly_count": len(weekly),
        "core_suppliers": CORE_SUPPLIERS,
        "today": dt.date.today().strftime("%Y-%m-%d"),
    }

    out = {"meta": meta, "orders": orders, "capacity": list(cap_map.values()), "weekly": weekly}
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    # 控制台摘要
    print("=== 清洗完成 ===")
    print(f"源行数: {meta['source_rows']}  删除空单: {dropped_po}  删除业务关闭: {dropped_closed}")
    print(f"有效订单: {meta['order_count']}  产能供应商: {meta['capacity_count']}  周计划: {meta['weekly_count']}")
    print(f"核心供应商命中: {sum(1 for o in orders if o['is_core'])} 家订单")
    ov = [o for o in orders if o['overdue_days'] > 0]
    print(f"逾期订单数: {len(ov)}  逾期供应商数: {len(set(o['supplier_short'] for o in ov))}")
    print(f"data.json 大小: {os.path.getsize(os.path.join(HERE,'data.json'))/1024:.1f} KB")


if __name__ == "__main__":
    clean()
