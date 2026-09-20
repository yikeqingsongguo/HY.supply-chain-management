# 金蝶 → 供应链看板 每日自动同步

## 作用
每天自动从金蝶云星空「采购订单列表 → 在途数据（共享）」导出 Excel，覆盖 `supply-dashboard/src/采购订单.xlsx`，并推送到 GitHub，触发 Actions 自动重建部署网页看板。

## 文件说明

| 文件 | 作用 |
|---|---|
| `kingdee_config.json` | 金蝶账号、路径、企微 webhook 配置（**已加入 .gitignore，勿提交**） |
| `sync_kingdee.py` | 同步管道主脚本：导出 → 复制 → git push → 失败告警 |
| `sync_kingdee.bat` | Windows 任务计划入口，处理 UTF-8 编码与日志目录 |
| `logs/sync.log` | 运行日志（自动创建） |

## 配置步骤

1. **配置企微告警（可选但推荐）**
   - 在企业微信群中添加一个「群机器人」，复制 webhook 地址。
   - 打开 `kingdee_config.json`，把 `wecom.webhook_url` 的 `YOUR_KEY_HERE` 替换为真实 key。
   - 把 `wecom.enabled` 改为 `true`。

2. **手动测试跑一次**
   ```bat
   cd C:\Users\admin\WorkBuddy\2026-09-17-11-48-46\supply-dashboard\automation
   sync_kingdee.bat
   ```
   成功后检查 `logs/sync.log` 和 GitHub Actions 是否被触发。

3. **注册 Windows 每日任务**
   以管理员身份运行：
   ```bat
   schtasks /Create /TN "KingdeeSupplyDailySync" /TR "C:\Users\admin\WorkBuddy\2026-09-17-11-48-46\supply-dashboard\automation\sync_kingdee.bat" /SC DAILY /ST 08:00 /RU %USERNAME% /RL HIGHEST /F
   ```
   含义：每天 08:00 以当前用户最高权限运行一次。可按需改 `/ST` 时间。

4. **查看/删除任务**
   ```bat
   schtasks /Query /TN "KingdeeSupplyDailySync" /V
   schtasks /Delete /TN "KingdeeSupplyDailySync" /F
   ```

## 注意事项

- 本机必须能无头登录金蝶（即运行时不弹验证码）。如金蝶触发风控，脚本会失败并通过企微告警。
- 导出文件落在 `C:\Users\admin\WorkBuddy\2026-08-07-16-17-10\data\incoming\`，脚本自动取最新一份 `.xlsx`。
- `kingdee_config.json` 含敏感信息，**已写入 `.gitignore`**，不要手动 `git add` 它。
- 若某天无数据变更，`git diff --cached` 会判断为无变更，脚本直接结束、不会空提交。
