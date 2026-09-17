#!/bin/bash
# 双击 / 命令行刷新：clean -> build -> 尝试打开浏览器
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
"$PY" "$HERE/run.py" || { echo "运行失败"; exit 1; }
echo "已生成 index.html"
( command -v open >/dev/null && open "$HERE/index.html" ) \
  || ( command -v xdg-open >/dev/null && xdg-open "$HERE/index.html" ) \
  || echo "请手动打开 $HERE/index.html"
