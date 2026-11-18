# 版本 2.1.1 交付说明

- 版本号：2.1.1
- 日期：2026-11-18
- 类型：小修/微调
- 父版本：v2.1.0
- 页面数据快照（updated_at）：2026-11-18 12:06

## 本次修改内容
1) SPU 汇总表列序改为 SPU/待下单量/物料名称/采购员/供应商/SKU数/行数/单据，物料名称固定 150px；2) 修复 lookupSKU 漏传 mapIndex 与跨作用域调用 buildMapIndex 导致抽屉报错、补录后仍显示待填写的问题；3) 去掉切页签的 smooth 滚动。

## 修改原因
用户反馈物料名称列留白过长、补录页 0 条但汇总表仍显示待填写、页面自动缓慢滚动。

## 影响范围
仅 console/index.html 与文档；实测 41 行待填写=0/含未匹配=0，列顺序正确。

## 本版本留存的完整文件
- console/index.html（采购管理台完整页面）
- console/logo-vayi.png、console/logo-mark.png（品牌图）
- index.template.html（源模板，build.py 的输入；改 index.html 无效，必须改它）

## 可恢复说明
1. **直接看当时效果**：双击本目录 `index.html`（含内联数据，零依赖）；管理台打开 `console/index.html`。
2. **回滚线上**：`git checkout v2.1.1` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.1.1`，可 `git checkout v2.1.1` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
