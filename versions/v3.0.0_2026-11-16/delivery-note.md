# 版本 3.0.0 交付说明

- 版本号：3.0.0
- 日期：2026-11-16
- 类型：重大重构
- 父版本：v2.0.0
- 页面数据快照（updated_at）：2026-11-16 14:17

## 本次修改内容
1) index.html 新增总览为全站首屏（胶囊指标、4 KPI、近14天交付节奏、近14天申请单柱图、今日待办、模块入口、供应商Top6），原在途概览退为第二页签；2) 顶部固定华熠 VAYI 品牌 logo，点击回总览；3) 配色统一蓝绿：警示粉红改 #E2554F、指标数字 #0B4F47、图表粉红改蓝；4) 新增错峰入场、数字滚动、hover 位移等动效；5) 修复待下单明细抽屉退不出去（遮罩层级、头部被压成0高度、被 .wrap 层叠上下文覆盖），新增返回按钮/圆形×/点遮罩/Esc 四种出口；6) 采购管理台移除总览页签，恢复概览为首项。

## 修改原因
用户要求总览作为全站首页（而非管理台专属）、顶部加 logo 并固定、视觉与配色统一到蓝绿风格；抽屉无法退出影响周例会使用。

## 影响范围
index.html 2.67MB；console/index.html 1.36MB；新增 console/logo-vayi.png(37KB)/logo-mark.png(8KB)；新增 console/overview.json；index.template.html 同步修改（关键：产物需从模板重建）；新增 CHANGELOG.md 与 docs/交付文档.md。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v3.0.0` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v3.0.0`，可 `git checkout v3.0.0` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
