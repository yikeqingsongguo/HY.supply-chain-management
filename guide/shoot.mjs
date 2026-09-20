// Real screenshots of the dashboard with numbered annotations, via puppeteer-core.
// Usage: node shoot.mjs <chrome-headless-shell.exe> <index.html abs path> <outDir>
import puppeteer from 'puppeteer-core';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const EXE = process.argv[2];
const PAGE = process.argv[3];
const OUT = process.argv[4];
fs.mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({
  executablePath: EXE,
  headless: 'shell',
  args: ['--no-sandbox', '--disable-gpu', '--force-color-profile=srgb', '--font-render-hinting=none'],
  defaultViewport: { width: 1440, height: 900, deviceScaleFactor: 2 },
});

const page = await browser.newPage();
await page.goto(pathToFileURL(PAGE).href, { waitUntil: 'load', timeout: 60000 });
await page.waitForFunction(() => document.getElementById('boot') && document.getElementById('boot').classList.contains('hide'), { timeout: 60000 });
await sleep(1500);

async function go(tab) {
  await page.evaluate((t) => document.querySelector('.tab[data-page="' + t + '"]').click(), tab);
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1500);
}

// Inject numbered badges + labels over real elements (viewport coords).
async function annotate(specs) {
  await page.evaluate((specs) => {
    document.getElementById('__annot')?.remove();
    const layer = document.createElement('div');
    layer.id = '__annot';
    Object.assign(layer.style, { position: 'fixed', inset: '0', zIndex: 2147483000, pointerEvents: 'none' });
    const mk = (css, text) => { const d = document.createElement('div'); Object.assign(d.style, css); if (text != null) d.textContent = text; layer.appendChild(d); return d; };
    for (const s of specs) {
      const el = document.querySelector(s.sel);
      if (!el) { console.warn('no el for', s.sel); continue; }
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) { continue; }
      if (s.box) mk({ position: 'absolute', left: r.left + 'px', top: r.top + 'px', width: r.width + 'px', height: r.height + 'px', border: '3px solid #EF4444', borderRadius: '10px', boxShadow: '0 0 0 2px rgba(255,255,255,.75)' });
      let bx = r.left + (s.dx != null ? s.dx : 8), by = r.top + (s.dy != null ? s.dy : 8);
      if (s.pos === 'above') { bx = r.left + 8; by = r.top - 30; }
      if (s.pos === 'below') { bx = r.left + 8; by = r.top + r.height + 8; }
      mk({ position: 'absolute', left: bx + 'px', top: by + 'px', width: '28px', height: '28px', borderRadius: '50%', background: '#EF4444', color: '#fff', font: '800 16px/28px "Segoe UI",sans-serif', textAlign: 'center', boxShadow: '0 3px 10px rgba(0,0,0,.4)', border: '2px solid #fff' }, s.n);
      if (s.text) {
        let ly = by + 1, lx = bx + 36;
        if (s.pos === 'above') { ly = by + 1; lx = r.left + 44; }
        if (s.pos === 'below') { ly = by + 1; lx = r.left + 44; }
        const css = { position: 'absolute', top: ly + 'px', background: '#EF4444', color: '#fff', font: '700 14px/1.5 "Segoe UI",sans-serif', padding: '3px 10px', borderRadius: '9px', whiteSpace: 'nowrap', boxShadow: '0 3px 10px rgba(0,0,0,.4)' };
        if (s.side === 'left') { css.right = (window.innerWidth - r.left + 10) + 'px'; } else { css.left = lx + 'px'; }
        mk(css, s.text);
      }
    }
    document.body.appendChild(layer);
  }, specs);
}
const clearAnnot = () => page.evaluate(() => document.getElementById('__annot')?.remove());

async function shot(name, clip) {
  const opts = { path: path.join(OUT, name) };
  if (clip) opts.clip = clip;
  await page.screenshot(opts);
  console.log('shot', name);
}

// ---- 1 整体界面（带编号标注） ----
await go('overview');
await annotate([
  { sel: '#tabs', n: '1', text: '① 标签页：切换 6 个页面（手机端变 ☰）', box: true },
  { sel: '#filterbar', n: '2', text: '② 通用筛选条（各页共用）', box: true, pos: 'below' },
  { sel: '#f_chips', n: '3', text: '③ 筛选反馈 chips：可单项移除 / 清除全部', box: true, pos: 'below' },
  { sel: '.page.active .pt-month', n: '4', text: '④ 本月 / 下月：点一下全站联动', side: 'left' },
  { sel: '#ov_kpi', n: '5', text: '⑤ KPI 卡片', box: true },
  { sel: '#ov_bar', n: '6', text: '⑥ 点图表元素即可下钻明细', box: true },
]);
await shot('overview-full.png');
await clearAnnot();

// ---- 2 筛选条 closeup ----
await page.evaluate(() => { document.getElementById('filterbar').scrollIntoView({ block: 'start' }); window.scrollBy(0, -80); });
await sleep(400);
await annotate([
  { sel: '#f_supplier', n: '1', text: '① 供应商：下拉多选，勾选即筛选', box: true, pos: 'above' },
  { sel: '#f_month', n: '2', text: '② 月份', box: true, pos: 'above' },
  { sel: '#f_creator', n: '3', text: '③ 创建人', box: true, pos: 'above' },
  { sel: '#f_search', n: '4', text: '④ 搜索：单据号/物料/规格/供应商', box: true, pos: 'above' },
  { sel: '#f_reset', n: '5', text: '⑤ 重置：清空全部筛选', box: true, pos: 'above', side: 'left' },
  { sel: '#f_chips', n: '6', text: '⑥ chips：点 × 移除单项 / 清除全部', box: true, pos: 'below' },
]);
const fr = await page.evaluate(() => document.getElementById('filterbar').getBoundingClientRect().top);
await shot('filter.png', { x: 0, y: Math.max(0, fr - 60), width: 1440, height: 280 });
await clearAnnot();

// ---- 3 页面标题 + 月份开关 closeup ----
await go('capacity');
await annotate([
  { sel: '.page.active .page-title', n: '1', text: '① 每个页面都有标题', box: true },
  { sel: '.page.active .pt-month', n: '2', text: '② 本月 / 下月 开关', box: true },
]);
const tr = await page.evaluate(() => document.querySelector('.page.active .page-title').getBoundingClientRect().top);
await shot('month.png', { x: 0, y: Math.max(0, tr - 20), width: 1440, height: 150 });
await clearAnnot();

// ---- 4 在途概览（页面①） ----
await go('overview');
await annotate([
  { sel: '.page.active .pt-month', n: '4', text: '④ 本月 / 下月', side: 'left' },
  { sel: '#ov_kpi', n: '5', text: '⑤ 8 张 KPI 卡', box: true },
  { sel: '#ov_bar', n: '6', text: '⑥ 核心切换 / 点柱体下钻', box: true },
  { sel: '#ov_ring', n: '7', text: '⑦ 切口径 / 点扇区下钻', box: true },
  { sel: '#ov_daily', n: '8', text: '⑧ 点数据点下钻当日订单', box: true },
]);
await shot('page-overview.png');
await clearAnnot();

// ---- 5 下钻抽屉 ----
await go('overview');
await page.evaluate(() => { try { window.APP.openOrderSummary(window.APP.ORDERS.slice(0, 400), '供应商 · 订单汇总'); } catch (e) { console.warn(e.message); } });
await sleep(1000);
await annotate([
  { sel: '#dw_back', n: '1', text: '① ‹ 返回上一级', side: 'left' },
  { sel: '#dw_crumbs', n: '2', text: '② 面包屑：当前层级', box: true },
  { sel: '#drawer tbody tr', n: '3', text: '③ 点行 → 该订单的 SKU 明细', side: 'left' },
  { sel: '#dw_close', n: '4', text: '④ ✕ 关闭', side: 'left' },
]);
await shot('drawer.png');
await clearAnnot();
// 关闭抽屉，避免遮挡后续页面截图
await page.evaluate(() => document.getElementById('dw_close')?.click());
await sleep(500);

// ---- 6~10 逐页（真实截图 + 少量标注） ----
const pageSpecs = {
  supplier: [
    { sel: '#sup_doc_seg', n: '1', text: '① 单据类型：全部 / 标准采购 / VMI', box: true },
    { sel: '#sup_bub', n: '2', text: '② 气泡图：X=计划量 Y=剩余 气泡=订单数', box: true },
    { sel: '#sup_line_table', n: '3', text: '③ 点「详情」下钻该产线', box: true },
  ],
  capacity: [
    { sel: '#cap_month_txt', n: '1', text: '① 当前统计月份（由顶部开关控制）' },
    { sel: '#cap_dist', n: '2', text: '② 点负荷率区间 → 右侧详情联动', box: true },
  ],
  weekly: [
    { sel: '#wk_thr', n: '1', text: '① 调分界值：图A/图B 重新分组' },
    { sel: '#wk_import', n: '2', text: '② 导入新一周周计划', side: 'left' },
    { sel: '#wk_a', n: '3', text: '③ 点柱体下钻 SPU → SKU', box: true },
  ],
  overdue: [
    { sel: '#od_kpi', n: '1', text: '① 逾期 KPI（4 张）', box: true },
    { sel: '#od_sup_bar', n: '2', text: '② 点柱体下钻该供应商逾期明细', box: true },
    { sel: '#od_table', n: '3', text: '③ 一行一家，点行展开明细', box: true },
  ],
  cross: [
    { sel: '#cross_heat_seg', n: '1', text: '① 显示范围：TOP20 / 全部 / 仅核心', box: true },
    { sel: '#cross_heat', n: '2', text: '② 点单元格下钻（颜色越深=剩余越多）', box: true },
  ],
};
for (const tab of ['supplier', 'capacity', 'weekly', 'overdue', 'cross']) {
  await go(tab);
  await annotate(pageSpecs[tab]);
  await shot('page-' + tab + '.png');
  await clearAnnot();
}

// ---- 11 表格排序/筛选 closeup ----
await go('overdue');
await page.evaluate(() => { document.getElementById('od_table').scrollIntoView({ block: 'start' }); window.scrollBy(0, -100); });
await sleep(500);
await annotate([
  { sel: '#od_table th:nth-child(3)', n: '1', text: '① 点表头 ▲▼ 排序' },
  { sel: '#od_table th:last-child', n: '2', text: '② ▾ 列内勾选筛选', side: 'left' },
  { sel: '#od_table tbody tr', n: '3', text: '③ 点行展开明细' },
]);
// 表格已在视口内，直接截视口（带 clip 且超出视口会触发重排导致滚动被重置）
await shot('table.png');
await clearAnnot();

await browser.close();
console.log('ALL DONE');
