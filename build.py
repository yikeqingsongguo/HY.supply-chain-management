# -*- coding: utf-8 -*-
"""
构建脚本：把 ECharts 库 + data.json 注入 index.template.html
产出单文件 index.html（内联全部 JS/CSS/数据，双击 file:// 即可用，零后端零 API）。
"""
import os, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    tpl_path = os.path.join(HERE, "index.template.html")
    ec_path = os.path.join(HERE, "vendor", "echarts.min.js")
    data_path = os.path.join(HERE, "data.json")
    out_path = os.path.join(HERE, "index.html")

    for p in (tpl_path, ec_path, data_path):
        if not os.path.exists(p):
            sys.exit("缺少文件: " + p)

    with open(tpl_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    with open(ec_path, "r", encoding="utf-8") as f:
        echarts_src = f.read()
    # 防止库内出现 </script> 提前闭合
    echarts_src = echarts_src.replace("</script", "<\\/script")
    with open(data_path, "r", encoding="utf-8") as f:
        data = f.read().strip()
    if not data.startswith("{"):
        data = json.dumps(json.load(open(data_path, encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))

    echarts_tag = "<script>\n" + echarts_src + "\n</script>"
    data_tag = "<script>\nwindow.DATA = " + data + ";\n</script>"

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
