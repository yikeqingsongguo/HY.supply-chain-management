# 版本 2.1.0 交付说明

- 版本号：2.1.0
- 日期：2026-11-18
- 类型：功能/较大改动
- 父版本：v2.0.0
- 页面数据快照（updated_at）：2026-11-18 09:24

## 本次修改内容
1) 抽屉未匹配改实时判定并补录后重绘；2) 趋势图读 WK_RAW 与其他页筛选隔离、日期轴随筛选铺连续日期；3) 漏下单默认全部申请日到今天；4) 总览 KPI 卡与胶囊可点击跳转；5) 供应商汇总改 SPU→SKU、采购员改供应商→SPU→SKU；6) 周计划抽屉按 SPU 分组加备注列与新品/新变体彩色标签。

## 修改原因
用户反馈已填映射仍显示未匹配、日期跨页联动、漏下单日期单边导致筛选失灵、总览卡片点不动，以及汇总下钻层级过粗、备注信息缺失。

## 影响范围
console/index.html 与 index.html/index.template.html 均改动；新增 console 弹窗两级下钻函数、周计划抽屉 SPU 分组；未改数据口径；云端交付文档已同步。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.1.0` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.1.0`，可 `git checkout v2.1.0` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
