# 版本 2.2.2 交付说明

- 版本号：2.2.2
- 日期：2026-11-19
- 类型：小修/微调
- 父版本：v2.2.1
- 页面数据快照（updated_at）：2026-11-19 15:01

## 本次修改内容
负荷评分反转（低分高）；删热力图/逾期图；新增5个可下钻指标卡；详情面板9项指标逐项下钻；修复气泡标签与表格列文字挤占。

## 修改原因
用户反馈文字挤占看不清、无法判断数据准确性、要求指标可下钻。

## 影响范围
build_supplier_score.py/data.json/index.template.html；评分方向变更。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.2.2` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.2.2`，可 `git checkout v2.2.2` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
