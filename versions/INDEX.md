# 版本存档索引

| 版本 | 日期 | 类型 | 摘要 | 影响范围 | 目录 |
|---|---|---|---|---|---|
| 1.0.0 | 2026-10-19 | 基线 | 初始基线：供应链在途看板 2026-10-19 状态 | - | [1.0.0](versions/v1.0.0_2026-10-19) |
| 1.1.0 | 2026-10-19 | 功能/较大改动 | 新增准交率分析页（收料单+全量采购订单） | 新增一页，不改动原6页口径；clean.py 增加 otd/otd_error 字段；sync_kingdee.py 每轮多一次全量导出（约+30s）；仓库新增 src/otd_recv.xlsx、src/otd_po_full.xlsx。 | [1.1.0](versions/v1.1.0_2026-10-19) |
| 1.2.0 | 2026-10-19 | 功能/较大改动 | 周数据计划嵌入完整采购管理台；准交率改为到货期数量加权 | 新增 console/（index.html 1.2MB + map.json 830KB + price.json 2.1MB），deploy.yml 同步发布 console/；otd.py 输出结构变更为 order_details 逐单明细；index.html 体积 2.78MB→2.91MB；原6页口径不变。 | [1.2.0](versions/v1.2.0_2026-10-19) |
| 1.3.0 | 2026-10-20 | 功能/较大改动 | 准交率两列与趋势下钻；待交新品简称列；管理台改待下单汇总 | index.html 3.15MB（19张图）；console/index.html +9.3KB，新增 apply.csv/weekly.json；sync_kingdee.py 增加收料单导出分支（enable_recv_sync 默认 false）；kingdee_collector.py 增加 KINGDEE_FORM 与过滤重置能力。 | [1.3.0](versions/v1.3.0_2026-10-20) |
| 1.4.0 | 2026-10-20 | 功能/较大改动 | 三表单定时同步；准交率仅当月+柱体下钻；待下单明细改造 | index.html 3.28MB（19图）；console/index.html 1.22MB；新增 build_console_data.py；sync_kingdee.py 步骤 7→9；kingdee_config.json 打开 enable_recv_sync/enable_apply_sync；src/otd_recv.xlsx 换为 3,462 行本月数据，src/otd_apply.xlsx 换为 216 行。 | [1.4.0](versions/v1.4.0_2026-10-20) |
| 1.5.0 | 2026-10-20 | 功能/较大改动 | 待下单改申请单驱动+批量指定供应商；准交率列级下钻；图表刻度修复 | index.html 3.29MB；console 1,232,424 字节；weekly.json 变为申请单驱动（含 doc/ling/pending 字段）；build_console_data.py 重写；otd.py 读可选「单据类型」列。 | [1.5.0](versions/v1.5.0_2026-10-20) |
| 1.6.0 | 2026-10-20 | 功能/较大改动 | 全局口径与概览/准交率/待下单界面调整 | index.html 3.45MB；console 1,235,010 字节；data.json 订单行 3,912→3,911（VYTK 排除 0 行，待下单侧排除 9 行 1,000 件）；otd 供应商记录新增 short 字段。 | [1.6.0](versions/v1.6.0_2026-10-20) |
| 1.6.1 | 2026-10-20 | 小修/微调 | 待填写回流补录、采购员统计、弹窗定位、移除VMI | 待下单 203 行/35,614 件/16 家/待填写 6 行；console 1,240,498 字节；otd.py 去掉 doc_type 过滤段；准交率本月 49.02% 不变。 | [1.6.1](versions/v1.6.1_2026-10-20) |
| 1.6.2 | 2026-10-20 | 小修/微调 | 补录保存即时生效与待补数量常显 | console 1,242,766 字节；实测 9→8 行、待填写 2,040/6→1,450/4；线上 200。 | [1.6.2](versions/v1.6.2_2026-10-20) |
| 2.0.0 | 2026-11-16 | 重大重构 | 全站总览首页 + 品牌 logo + 蓝绿配色 + 抽屉/同步修复 | index.html 2.67MB；console/index.html 1.36MB；新增 console/logo-vayi.png(37KB)/logo-mark.png(8KB)；新增 console/overview.json；index.template.html 同步修改（关键：产物需从模板重建）；新增 CHANGELOG.md 与 docs/交付文档.md。 | [2.0.0](versions/v2.0.0_2026-11-16) |
| 2.1.0 | 2026-11-18 | 功能/较大改动 | 匹配/日期/点击修复 + 待下单两级下钻 | console/index.html 与 index.html/index.template.html 均改动；新增 console 弹窗两级下钻函数、周计划抽屉 SPU 分组；未改数据口径；云端交付文档已同步。 | [2.1.0](versions/v2.1.0_2026-11-18) |
| 2.1.1 | 2026-11-18 | 小修/微调 | 列宽顺序调整 + 补录实时判定修复 + 切页滚动修复 | 仅 console/index.html 与文档；实测 41 行待填写=0/含未匹配=0，列顺序正确。 | [2.1.1](versions/v2.1.1_2026-11-18) |
| 2.1.2 | 2026-11-18 | 小修/微调 | 修复页面周期性自动上移 | index.html + index.template.html；数据口径不变。 | [2.1.2](versions/v2.1.2_2026-11-18) |
| 2.1.3 | 2026-11-18 | 小修/微调 | SPU汇总表恢复筛选、放大表头、新增标记列、留白移至末尾 | 仅 console/index.html；DOM 验证 11 列/7 筛选按钮/13.5px/标记胶囊正常。 | [2.1.3](versions/v2.1.3_2026-11-18) |
| 2.1.4 | 2026-11-18 | 小修/微调 | 修复iframe内导出Excel无反应 | index.html / index.template.html / console/index.html；数据口径不变。 | [2.1.4](versions/v2.1.4_2026-11-18) |
| 2.1.5 | 2026-11-18 | 小修/微调 | 顶层代理下载彻底修复iframe导出 | index.html / index.template.html / console/index.html；数据口径不变。 | [2.1.5](versions/v2.1.5_2026-11-18) |
| 2.1.6 | 2026-11-18 | 小修/微调 | 彻底修复采购员汇总导出：补全跨作用域缺失函数 | 仅 console/index.html；静态扫描确认无其他缺失业务函数。 | [2.1.6](versions/v2.1.6_2026-11-18) |
| 2.2.0 | 2026-11-19 | 功能/较大改动 | 交叉分析新增供应商综合评估评分表 | index.template.html/data.json/build.py/refresh_all.py/新增build_supplier_score.py；准交率照搬工作台口径，不用含VMI的skill口径。 | [2.2.0](versions/v2.2.0_2026-11-19) |
