# 版本 2.2.0 交付说明

- 版本号：2.2.0
- 日期：2026-11-19
- 类型：功能/较大改动
- 父版本：v2.1.6
- 页面数据快照（updated_at）：2026-11-19 12:06

## 本次修改内容
评分表按核心/普通分组，准交率与采购部工作台同源(k3_live.json)，权重40/30/15/15，产能负荷按当月剩余天数折算，含评级与下钻。build.py与refresh_all.py已接入自动刷新。

## 修改原因
用户要求结合逾期数量、准交率、产能、款数做多维综合评估。

## 影响范围
index.template.html/data.json/build.py/refresh_all.py/新增build_supplier_score.py；准交率照搬工作台口径，不用含VMI的skill口径。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.2.0` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.2.0`，可 `git checkout v2.2.0` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
