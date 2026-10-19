# 供应链看板 · 版本存档规范

## 1. 目的
在每次**较大幅度修改前**，保存当前页面完整内容 + 一份「产品交付说明」，形成独立、可追溯、可对比、可恢复的版本档案。存档同时落**本地**（`versions/`）与**云端**（GitHub 仓库，随 `git push` 上线）。

## 2. 目录结构
```
supply-dashboard/
  archive_version.py              # 存档脚本（标准库，零外部依赖）
  versions/
    README.md                     # 本规范
    INDEX.md                      # 版本索引（时间线表格，每次存档追加一行）
    vX.Y.Z_YYYY-MM-DD/            # 单版本档案目录
      index.html                  # 完整页面快照（含内联数据，可直接打开恢复）
      delivery-note.md            # 产品交付说明
      meta.json                   # 机器可读元数据
```

## 3. 文件命名规范
| 对象 | 命名 | 说明 |
|---|---|---|
| 版本目录 | `v{MAJOR}.{MINOR}.{PATCH}_{YYYY-MM-DD}` | 如 `v1.0.0_2026-10-19` |
| 页面快照 | `index.html` | 固定名，便于直接双击打开恢复 |
| 交付说明 | `delivery-note.md` | 固定名 |
| 元数据 | `meta.json` | 固定名 |

> 若同日同版本号重复（极少见），自动追加 `_2`、`_3` 序号避免覆盖。

## 4. 版本号规则（语义化 vMAJOR.MINOR.PATCH）
- **MAJOR**：架构级 / 重大重构
- **MINOR**：新增功能或较大改动
- **PATCH**：小修、文案、样式微调
- **首次基线 = v1.0.0**
- `archive_version.py` 按 `--type` 基于最近一个版本目录自动 bump（`major/minor/patch`）；`baseline` 强制从 `v1.0.0` 起（仅首次用）。

## 5. 版本记录格式
**INDEX.md**（仓库内总索引，表格）：
```
| 版本 | 日期 | 类型 | 摘要 | 影响范围 | 目录 |
|---|---|---|---|---|---|
| v1.0.0 | 2026-10-19 | 基线 | 初始看板基线 | 全局 | [v1.0.0_2026-10-19](versions/v1.0.0_2026-10-19) |
```

**delivery-note.md**（单版本交付说明，模板）：
```
# 版本 vX.Y.Z 交付说明
- 版本号 / 日期 / 类型 / 父版本 / 页面数据快照(updated_at)
## 本次修改内容
## 修改原因
## 影响范围
## 可恢复说明
```

**meta.json**（机器可读）：版本号、日期、类型、标题、描述、原因、影响、父版本、数据快照时间、作者、创建时间。

## 6. 触发流程（推荐工作流）
1. **大改前**：运行脚本存档「改前」状态（`--type` 选 `before` 或对应改动级别，标题写「改前：…」）。
2. **改完**：再运行一次存档「改后」状态（`--type` 选 `feature/fix/refactor` 或 `after`）。
3. 两次形成**前后对比**，可追溯每次交付的修改内容 / 原因 / 影响范围。
4. 首次基线 `v1.0.0` 记录初始稳定状态。

## 7. 运行方式
```bat
:: 基线（仅首次）
python archive_version.py --type baseline --title "初始基线：供应链在途看板 2026-10-19 状态"

:: 大改前存档（改前快照）
python archive_version.py --type before --title "改前：周计划表重构" --desc "…" --reason "…" --impact "…"

:: 大改后存档（交付）
python archive_version.py --type minor  --title "周计划表改为阴影曲线" --desc "…" --reason "…" --impact "…"

:: 仅本地存档、不推送云端（调试用）
python archive_version.py --type patch --title "文案微调" --no-push
```

脚本行为：
- **页面来源**：优先抓取线上已部署页面（与用户看到的看板一致）；失败则 fallback 本地 `index.html`；都没有则报错（请先 `build.py`）。
- 自动解析 `updated_at` 写入元数据。
- 默认自动 `git add versions/ archive_version.py` + commit + push（本地+云端双存）；`--no-push` 仅本地。

## 8. 记忆系统同步
每次存档后，脚本在 `.workbuddy/memory/VERSION_ARCHIVE.md` 追加一条索引（版本 / 日期 / 类型 / 一句话），与 `versions/INDEX.md` 保持一致，确保记忆系统内也可追溯。

## 9. 对比与恢复
- **对比**：在 GitHub 仓库或本地 `versions/` 下，任意两个版本目录的 `index.html` 即可并排对比渲染效果；`delivery-note.md` 对比修改意图。
- **恢复页面**：浏览器直接打开目标版本目录的 `index.html`（含当时内联数据），即看到当时渲染的看板。
- **回滚源码**：`git checkout <commit> -- <file>` 取回对应源码；或保留版本目录作为静态快照。
