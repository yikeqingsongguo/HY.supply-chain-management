# -*- coding: utf-8 -*-
"""一键刷新：先清洗生成 data.json，再注入构建 index.html。"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))

def run(script):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=HERE)
    if r.returncode != 0:
        sys.exit(f"[失败] {script} 返回码 {r.returncode}")

if __name__ == "__main__":
    print(">> 运行 clean.py 解析 Excel ...")
    run("clean.py")
    print(">> 运行 build.py 注入构建 index.html ...")
    run("build.py")
    print(">> 完成：index.html 已刷新（双击即可在浏览器打开）")
