# 版本 2.1.2 交付说明

- 版本号：2.1.2
- 日期：2026-11-18
- 类型：小修/微调
- 父版本：v2.1.1
- 页面数据快照（updated_at）：2026-11-18 14:24

## 本次修改内容
删除 index.html 全局 scroll-behavior:smooth，去掉周计划 iframe 每 2 秒 setInterval(fit)，改为切页签时按需同步高度。实测两页 scrollY 恒为 0。

## 修改原因
用户反馈页面仍会一卡一卡自动上移。

## 影响范围
index.html + index.template.html；数据口径不变。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.1.2` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.1.2`，可 `git checkout v2.1.2` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
