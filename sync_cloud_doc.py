#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/交付文档.md 同步到资料库云端文档（全量覆盖）。

背景：交付文档有两份，本地 `docs/交付文档.md` 是权威源，资料库那份是给团队看的云端版本。
两者必须保持一致，否则线上文档会停留在旧版本。

用法：
  python sync_cloud_doc.py --dry-run     # 只校验 Markdown，不写入
  python sync_cloud_doc.py               # 全量覆盖云端正文

目标节点：
  https://www.workbuddy.cn/space/d/5BAUBU1Jd94bijxJ08gcYW
  nodeId   = 5BAUBU1Jd94bijxJ08gcYW
  spaceId  = 6bNhbSXRLfS3QH0xBPp2g6

注意：全量覆盖会重建正文块，云端已有的评论锚点会失效。
改动较大时（章节增删）用覆盖；只改几行文字时，直接在云端文档里编辑更稳妥。
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOC = ROOT / "docs" / "交付文档.md"

NODE_ID = "5BAUBU1Jd94bijxJ08gcYW"
SPACE_ID = "6bNhbSXRLfS3QH0xBPp2g6"

SKILL_DOC_DIR = Path(
    r"C:/Users/admin/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked"
    r"/resources/plugins/workbuddy-builtin/skills/library/doc"
)
CREATE = SKILL_DOC_DIR / "create_doc.py"


def main():
    if not DOC.exists():
        print("⛔ 找不到 %s" % DOC)
        return 2
    if not CREATE.exists():
        print("⛔ 找不到资料库脚本（WorkBuddy 安装路径可能变了）：%s" % CREATE)
        return 2

    dry = "--dry-run" in sys.argv
    body = DOC.read_text(encoding="utf-8")
    print("来源：%s（%d 字）" % (DOC, len(body)))
    print("目标：https://www.workbuddy.cn/space/d/%s" % NODE_ID)
    print("模式：%s" % ("仅校验（dry-run）" if dry else "全量覆盖"))

    cmd = [
        sys.executable, str(CREATE),
        "--node-block-id", NODE_ID,
        "--space-id", SPACE_ID,
        "--content-file", str(DOC),
    ]
    cmd.append("--dry-run" if dry else "--confirm-overwrite")

    r = subprocess.run(cmd, cwd=str(SKILL_DOC_DIR),
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if out:
        print(out)
    if err:
        print(err)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
