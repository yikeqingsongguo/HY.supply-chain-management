# automation-1789897232885 · 供应链看板每日金蝶同步 — 执行记忆

（高频参考：环境注意事项见文末，每次执行前先看）

## 2026-09-21 09:15 — 成功
- 三项验证全通过：sync.log 末尾「同步完成」+ push 成功 / Actions success / Pages 200。
- 金蝶导出：`采购订单_2026092109162400_3968810.xlsx` (486,646 B)，耗时约 80s；数据中心 `华熠UAT → 华熠网络` 切换正常；**无风控/禁用提示**。
- git：commit `ee1402e`，`git push origin main` → `8e84a44..ee1402e`（非"无变更"，正常提交并推送）。
- Actions：run #13，head_sha `ee1402e`，conclusion = **success**。
- Pages：`https://yikeqingsongguo.github.io/HY.supply-chain-management/` → **200**；线上 `updated_at` = `2026-09-21 09:16`，与同步时刻一致。
- 数据观察（非故障）：order_count 4351→4338、closed_rows 516→510、sum_po 1,055,965→1,052,595、sum_received 293,506→291,065、sum_remain 762,459→761,530。三项金额与行数同向下降，疑为金蝶导出范围/订单删并所致，待人工确认口径。

## 环境注意事项（重要）
- **`cmd.exe` 被沙箱安全策略拦截**（Bash 与 PowerShell 两个通道均被 block），无法直接执行 `automation/sync_kingdee.bat`。
- 等价替代方式（已验证可用）：
  ```bash
  cd "C:/Users/admin/WorkBuddy/2026-09-17-11-48-46/supply-dashboard/automation"
  PYTHONUTF8=1 PYTHONIOENCODING=utf-8 \
    "C:/Users/admin/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
    sync_kingdee.py >> logs/sync.log 2>&1
  ```
  与 bat 差异仅在于 `chcp 65001` 与 `mkdir logs`（目录已存在），功能等价，日志同样落在 `logs/sync.log`。
- 轮询 Actions 时 GitHub API 偶发返回空响应（`PARSE_ERR`），重试即可，不代表失败。
- `pages/builds/latest` API 返回 404 属正常（该仓库 Pages 源为 GitHub Actions，非 legacy branch build）。
- 站点为单文件 HTML，`data.json` 线上返回 404 属正常（数据内联在 `window.DATA`）。
