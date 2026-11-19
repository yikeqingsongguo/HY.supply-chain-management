# 供应链看板每日同步 — 2026-10-26 验证报告

---

## 17:45 窗口（✅ 成功）

| 项 | 值 |
|---|---|
| 触发 | 本自动化 17:45:38 触发；Windows 任务计划已在 17:45:00 拉起 `sync_kingdee.py`（PID 17972） |
| 处理策略 | 沿用「不重复触发、等待并验证」：本自动化未另起实例，避免双 Kingdee 会话互踩 |
| 新 commit | `dbb159b` daily: Kingdee 在途数据同步 |
| 推送 | `8794526..dbb159b  main -> main` |
| origin/main 验证 | `dbb159b4d715ae5083d216b3469bcfd197fff0b8`（2026-10-26 17:48:09） |
| HEAD == origin/main | 是（已推送、同步） |
| 变更文件 | 4 files changed：采购订单.xlsx、otd_po_full.xlsx、otd_recv.xlsx、otd_apply.xlsx |
| 自动部署 | GitHub Actions `deploy.yml` 自动 build + 发布到 Pages |

### 关键日志证据（logs/sync.log）
```
[2026-10-26 17:48:09]   [stdout] [main dbb159b] daily: Kingdee 在途数据同步
[2026-10-26 17:48:09]   [stdout]   4 files changed, 0 insertions(+), 0 deletions(-)
[2026-10-26 17:48:18]   [stderr]    8794526..dbb159b  main -> main
[2026-10-26 17:48:18] 已推送至 origin/main，GitHub Actions 将自动部署
[2026-10-26 17:48:18] === 同步完成 ===
```

### 说明
- 因 17:45 双触发（任务计划 17:45:00 + 本自动化 17:45:38），沿用既定安全策略：**未直接执行 `sync_kingdee.bat`**（bat 会起第二个金蝶会话和一轮冗余提交），改以在途 17:45:00 实例的实跑结果为准并独立验证。
- 工作区另有无关改动（`clean.py`、`data.json` 已改；`data_20261020_backup.json` 等未跟踪），非本次同步产生，未触碰。
- **`copy_with_retry` 的 errno=22 捕获修复仍未落地**（见 09:15 记录建议），长期仍建议加文件锁/单例根除双触发。

---

## 09:15 窗口（先失败一次，重试后 ✅ 成功）

### 触发与并发处理
- 本自动化 09:08 触发，但执行被延迟到 ~09:15。待运行前查进程发现：Windows 后台调度器 `background_scheduler.py`（PID 6468）**已在 09:15:00 自行拉起一次 sync_kingdee.py（PID 20000）→ 金蝶采集子进程**。
- 为消除「双 Kingdee 会话互踩」风险（2026-10-22 教训），**先 kill 了调度器父进程 6468**（子进程 20000 不受影响，继续跑）。本自动化未再自启重复实例，沿用 2026-10-23 的「不重复触发、等待并验证」策略。

### 首次失败（09:15 调度器那次）
- 步骤 5/9 金蝶导出收料通知单：采集器本身**导出成功**（`data/incoming/收料通知单_2026102609181229_3968810.xlsx`），但回到 `sync_kingdee.py` 的 `copy_with_retry` 复制 `src/otd_recv.xlsx` 时抛 `OSError: [Errno 22] Invalid argument`，落入失败告警、EXIT=1、未提交未推送。
- 根因：**当时 `otd_recv.xlsx` 被 Excel/WPS 占用**，`shutil.copy2` 写完后设置文件元数据（utime/chmod）时返回 EINVAL(22)。`copy_with_retry` 只 catch `PermissionError[13]`，未覆盖 `[22]`，异常外泄。
- 步骤 2/4 已成功覆盖 `采购订单.xlsx`、`otd_po_full.xlsx`；`otd_apply.xlsx` 未更新（仍 10-23 旧档）。

### 重试成功（本自动化手动重跑）
- 先手动 `shutil.copy2` 验证：锁已释放，复制成功，并顺手把新收料数据写入 `src/otd_recv.xlsx`。
- 重跑 `sync_kingdee.py`：4 个数据源全部导出并覆盖（含 收料/申请单），提交 `115b530`（4 files changed），推送 `df75a23..115b530  main -> main`。
- 日志确认：`[2026-10-26 09:26:05] 已推送至 origin/main` + `=== 同步完成 ===`。
- 验证：`git fetch` 后 `git log origin/main -1` = `115b530`；`HEAD == origin/main`；工作区干净。

### 收尾
- 重启后台调度器（pythonw，PID 20624，09:27:16 启动），保障 14:30 / 17:45 窗口。
- **建议代码修复（待用户确认）**：`copy_with_retry` 的 except 应同时捕获 `OSError(errno=22)` 等文件占用类错误，或复制失败时用 `shutil.copyfile` 回退，避免「采集成功但复制元数据失败」导致整轮空跑。
