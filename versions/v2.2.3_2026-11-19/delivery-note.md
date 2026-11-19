# 版本 2.2.3 交付说明

- 版本号：2.2.3
- 日期：2026-11-19
- 类型：小修/微调
- 父版本：v2.2.2
- 页面数据快照（updated_at）：2026-11-19 15:01

## 本次修改内容
按复述副标题/模块说明/免责声明/按钮提示/空状态长解释五类规则清理看板与管理台；口径公式收进ⓘ气泡。

## 修改原因
用户要求全站整改，保持界面简洁，给出'删掉会不会做错'判断标准。

## 影响范围
index.template.html/console/index.html/index.html；纯文案与样式，无数据口径变更。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.2.3` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.2.3`，可 `git checkout v2.2.3` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
