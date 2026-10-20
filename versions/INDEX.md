# 版本存档索引

| 版本 | 日期 | 类型 | 摘要 | 影响范围 | 目录 |
|---|---|---|---|---|---|
| 1.0.0 | 2026-10-19 | 基线 | 初始基线：供应链在途看板 2026-10-19 状态 | - | [1.0.0](versions/v1.0.0_2026-10-19) |
| 1.1.0 | 2026-10-19 | 功能/较大改动 | 新增准交率分析页（收料单+全量采购订单） | 新增一页，不改动原6页口径；clean.py 增加 otd/otd_error 字段；sync_kingdee.py 每轮多一次全量导出（约+30s）；仓库新增 src/otd_recv.xlsx、src/otd_po_full.xlsx。 | [1.1.0](versions/v1.1.0_2026-10-19) |
| 1.2.0 | 2026-10-19 | 功能/较大改动 | 周数据计划嵌入完整采购管理台；准交率改为到货期数量加权 | 新增 console/（index.html 1.2MB + map.json 830KB + price.json 2.1MB），deploy.yml 同步发布 console/；otd.py 输出结构变更为 order_details 逐单明细；index.html 体积 2.78MB→2.91MB；原6页口径不变。 | [1.2.0](versions/v1.2.0_2026-10-19) |
| 1.3.0 | 2026-10-20 | 功能/较大改动 | 准交率两列与趋势下钻；待交新品简称列；管理台改待下单汇总 | index.html 3.15MB（19张图）；console/index.html +9.3KB，新增 apply.csv/weekly.json；sync_kingdee.py 增加收料单导出分支（enable_recv_sync 默认 false）；kingdee_collector.py 增加 KINGDEE_FORM 与过滤重置能力。 | [1.3.0](versions/v1.3.0_2026-10-20) |
| 1.4.0 | 2026-10-20 | 功能/较大改动 | 三表单定时同步；准交率仅当月+柱体下钻；待下单明细改造 | index.html 3.28MB（19图）；console/index.html 1.22MB；新增 build_console_data.py；sync_kingdee.py 步骤 7→9；kingdee_config.json 打开 enable_recv_sync/enable_apply_sync；src/otd_recv.xlsx 换为 3,462 行本月数据，src/otd_apply.xlsx 换为 216 行。 | [1.4.0](versions/v1.4.0_2026-10-20) |
