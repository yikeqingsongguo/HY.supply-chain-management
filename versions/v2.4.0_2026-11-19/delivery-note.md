# 版本 2.4.0 交付说明

- 版本号：2.4.0
- 日期：2026-11-19
- 类型：功能/较大改动
- 父版本：v2.3.0
- 页面数据快照（updated_at）：2026-11-19 17:51

## 本次修改内容
交叉分析新增规模贡献维度(在途订单数量×准交率, 权重35/25/20/10/10)；修复产能负荷页因 cap_detail_sub 节点被删导致的渲染中断；修复 to_date 月日未补零导致 110 行期望到货丢失；KPI 卡改 .ckpi、详情面板默认展开首位、明细表 fixed 布局

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
2. **回滚线上**：`git checkout v2.4.0` 后重新发布，或把本目录文件覆盖回 `supply-dashboard/`。
3. **回滚源码**：`git tag` 已打 `v2.4.0`，可 `git checkout v2.4.0` 或 `git revert` 对应提交。
4. **恢复数据**：本目录页面的内联数据即当时快照；源表历史在 `git log -- src/`。
