# 版本 2.1.6 交付说明

- 版本号：2.1.6
- 日期：2026-11-18
- 类型：小修/微调
- 父版本：v2.1.5
- 页面数据快照（updated_at）：2026-11-18 14:32

## 本次修改内容
wkExportExcel 调用了未定义的 wkDownload；改 downloadBytes 后仍失败，因为该函数在另一个 script 作用域。现将 wkToast/wkStamp/wkSafe/wkDownloadBytes 就地实现在周计划模块内，两处调用改为 wkDownloadBytes。独立页与 iframe 均导出 5.84MB xlsx。

## 修改原因
用户反馈导出按钮点击多次无反应，前几次修改未触及真正的未定义函数问题。

## 影响范围
仅 console/index.html；静态扫描确认无其他缺失业务函数。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.1.6` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.1.6`，可 `git checkout v2.1.6` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
