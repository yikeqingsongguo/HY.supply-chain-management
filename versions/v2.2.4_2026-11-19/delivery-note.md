# 版本 2.2.4 交付说明

- 版本号：2.2.4
- 日期：2026-11-19
- 类型：小修/微调
- 父版本：v2.2.3
- 页面数据快照（updated_at）：2026-11-19 16:48

## 本次修改内容
打通期望到货数据链路，修趋势图重复绑定与日期联动，明细表列序重排+SPU数量区分样式，sticky表头修复，日期筛选固定，交叉指标加在途数量与6000门槛。

## 修改原因
用户截图反馈8项问题：日期不联动、列混乱、缺期望到货、表头错行、日期隐藏、指标点不了。

## 影响范围
build_console_data.py/console/index.html/index.template.html/data.json；新增期望到货字段，矩阵门槛6000。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.2.4` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.2.4`，可 `git checkout v2.2.4` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
