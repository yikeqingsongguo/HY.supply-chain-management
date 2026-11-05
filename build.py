# -*- coding: utf-8 -*-
"""
构建脚本：把 ECharts 库 + data.json 注入 index.template.html
产出单文件 index.html（内联全部 JS/CSS/数据，双击 file:// 即可用，零后端零 API）。

2026-11-03 起：DATA.weekly 不再取旧「周计划」表，改为取管理台的待下单数据
（console/weekly.json），并按「今天 + 31 天」所属月份归集，供「预计在途」使用。
"""
import os, json, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# 待下单并入在途的时间窗：今天 + N 天所在月份
EXPECT_DAYS = 31


def expect_month_label(days=EXPECT_DAYS):
    d = datetime.date.today() + datetime.timedelta(days=days)
    return "%d月" % d.month, d.isoformat()


def inject_weekly(data):
    """用采购申请单（待下单）替换旧周计划，字段与前端 weekly 结构一致。
    返回注入行数；失败时不改动原数据。"""
    wpath = os.path.join(HERE, "console", "weekly.json")
    if not os.path.exists(wpath):
        print("⚠️ 缺少 console/weekly.json，跳过待下单注入（沿用 data.json 原 weekly）")
        return 0

    with open(wpath, "r", encoding="utf-8") as f:
        wj = json.load(f)

    mlab, mdate = expect_month_label()
    rows = []
    for s in wj.get("suppliers", []):
        short = (s.get("short") or "").strip()
        full = (s.get("name") or "").strip()
        for it in s.get("items", []):
            qty = float(it.get("qty") or 0)
            if qty <= 0:
                continue
            rows.append({
                "supplier_full": full,
                "supplier_short": short,
                "sku": it.get("sku") or "",
                "spu": it.get("spu") or "",
                "material_name": it.get("name") or "",
                "spec": it.get("spec") or "",
                "buyer": it.get("buyer") or "",
                "plan_qty": qty,
                "qty": qty,                       # 剩余数量（待下单）—— 波动折线表用
                "apply_qty": float(it.get("apply_qty") or 0),  # 申请数量
                "date": it.get("date") or "",      # 创建日期 —— 波动折线表按日聚合
                "ling": it.get("ling") or "",      # 领星创建人
                "month": mlab,          # 归入的预计月份
                "doc": it.get("doc") or "",
            })

    data["weekly"] = rows
    meta = data.setdefault("meta", {})
    meta["source_weekly"] = "采购申请单（待下单）"
    meta["expect_month"] = mlab
    meta["expect_date"] = mdate
    meta["expect_days"] = EXPECT_DAYS
    meta["weekly_rows"] = len(rows)
    meta["weekly_updated_at"] = wj.get("updated_at") or ""
    print("待下单注入: %d 行 / 归入 %s（今天+%d天 = %s）" % (len(rows), mlab, EXPECT_DAYS, mdate))
    return len(rows)


def main():
    tpl_path = os.path.join(HERE, "index.template.html")
    ec_path = os.path.join(HERE, "vendor", "echarts.min.js")
    data_path = os.path.join(HERE, "data.json")
    out_path = os.path.join(HERE, "index.html")

    for p in (tpl_path, ec_path, data_path):
        if not os.path.exists(p):
            sys.exit("缺少文件: " + p)

    # 1) 先刷新管理台数据（console/weekly.json），「预计在途」依赖它
    try:
        import build_console_data
        build_console_data.build()
    except Exception as e:
        print("⚠️ 管理台数据生成失败:", e)

    # 2) 模板 + 数据
    with open(tpl_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    with open(ec_path, "r", encoding="utf-8") as f:
        echarts_src = f.read()
    # 防止库内出现 </script> 提前闭合
    echarts_src = echarts_src.replace("</script", "<\\/script")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    inject_weekly(data)
    # 写回 data.json：保证仓库内的数据文件与 index.html 内联数据一致
    # （clean.py 写 data.json 时 weekly 仍取自旧「周计划」表，无创建日期；build 注入后回写避免口径漂移）
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    except Exception as e:
        print("⚠️ 写回 data.json 失败:", e)
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    echarts_tag = "<script>\n" + echarts_src + "\n</script>"
    data_tag = "<script>\nwindow.DATA = " + data_json + ";\n</script>"

    if "<!--ECHARTS-->" not in tpl:
        sys.exit("模板缺少 <!--ECHARTS--> 占位符")
    if "<!--DATA-->" not in tpl:
        sys.exit("模板缺少 <!--DATA--> 占位符")

    out = tpl.replace("<!--ECHARTS-->", echarts_tag).replace("<!--DATA-->", data_tag)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)

    print("构建完成 ->", out_path)
    print("index.html 大小: %.2f MB" % (os.path.getsize(out_path) / 1024 / 1024))


if __name__ == "__main__":
    main()
