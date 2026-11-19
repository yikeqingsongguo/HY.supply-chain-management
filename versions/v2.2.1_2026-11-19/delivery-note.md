# 版本 2.2.1 交付说明

- 版本号：2.2.1
- 日期：2026-11-19
- 类型：小修/微调
- 父版本：v2.2.0
- 页面数据快照（updated_at）：2026-11-19 14:33

## 本次修改内容
移除款数，15%给新品准交率；展示改为四象限气泡矩阵（X综合分/Y总准交），点击显示明细指标与逐项评分说明。VMI数据用11-19新调拨明细更新。

## 修改原因
用户要求呈现四象限/波士顿矩阵，计算在途新品和新品准交率，点击工厂看明细指标和评分说明。

## 影响范围
build_supplier_score.py/data.json/index.template.html；评分公式变更，2026-11-19 下午生效。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.2.1` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.2.1`，可 `git checkout v2.2.1` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
