# 版本 2.1.3 交付说明

- 版本号：2.1.3
- 日期：2026-11-18
- 类型：小修/微调
- 父版本：v2.1.2
- 页面数据快照（updated_at）：2026-11-18 14:32

## 本次修改内容
表头 13.5px + 7 个筛选按钮（含标记列），筛选改事件委托以适配两层表头动态替换；新增新品/新变体数量标记列；所有列固定宽度，剩余留白集中到末尾。

## 修改原因
用户反馈表头字体小、失去筛选功能、留白位置不对，且新品/新变体需在汇总页体现。

## 影响范围
仅 console/index.html；DOM 验证 11 列/7 筛选按钮/13.5px/标记胶囊正常。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.1.3` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.1.3`，可 `git checkout v2.1.3` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
