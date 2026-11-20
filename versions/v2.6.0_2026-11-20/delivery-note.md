# 版本 2.6.0 交付说明

- 版本号：2.6.0
- 日期：2026-11-20
- 类型：功能/较大改动
- 父版本：v2.5.0
- 页面数据快照（updated_at）：2026-11-20 09:59

## 本次修改内容
新增 otd_from_k3.py，准交率页改读 k3_live.json + q2_rows.json（judge_std 口径），与采购部工作台、交叉分析完全同源；采购员按供应商映射表归集；明细粒度 SPU；交付文档 8.1 重写

## 修改原因
（基线存档：建立首个可追溯快照，作为后续对比基准）

## 影响范围
（基线存档：全局页面，作为后续对比基准）

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.6.0` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.6.0`，可 `git checkout v2.6.0` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
