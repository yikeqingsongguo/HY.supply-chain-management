/* 手动补录待下单（Excel/CSV 自动识别列）专项测试（jsdom）
 * 覆盖：表头识别（不在首行 / 列顺序随意）、供应商三级归并、重复行去重、
 *       并入 WEEKLY 后预计在途汇总更新、localStorage 持久化、清空还原。
 */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const HERE = __dirname;
const html = fs.readFileSync(path.join(HERE, 'index.html'), 'utf8');

const STUB = `
(function(){
  var calls=[];
  function make(d){return {_id:d&&d.id,setOption:function(o,n){calls.push({id:this._id,opt:o});},resize:function(){},
    on:function(){},off:function(){},dispose:function(){},getDom:function(){return d;}};}
  window.__chartCalls=calls;
  window.echarts={init:function(d){return make(d);},getInstanceByDom:function(){return null;},
    connect:function(){},registerTheme:function(){},version:'stub',graphic:{}};
})();
`;
const replaced = html.replace(/<script>([\s\S]*?)<\/script>/, '<script>' + STUB + '</script>');

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push('jsdomError: ' + (e && (e.stack || e.message))));

const dom = new JSDOM(replaced, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost/'
});
const w = dom.window;
w.XLSX = require(path.join(HERE, 'vendor', 'xlsx.full.min.js'));

const sleep = ms => new Promise(r => setTimeout(r, ms));

const CSV = [
  '采购待下单明细（补录模板）,,,,,,,,,',
  ',,,,,,,,,',
  '序号,供应商名称,物料编码,SPU,物料名称,规格,待下单数量,申请单号,采购员,备注',
  '1,广州市忆恩皮具有限公司,SPTEST001,9999,测试包,黑色/中号,1200,CSV001,张洁,补录测试',
  '2,忆恩,SPTEST002,9998,测试包2,白色,300,CSV002,张洁,简称识别',
  '3,不存在的新厂,SPTEST003,9997,测试包3,灰色,"1,050",CSV003,某人,新供应商',
  '4,广州市忆恩皮具有限公司,SPTEST001,9999,测试包,黑色/中号,1200,CSV001,张洁,重复行'
].join('\r\n');

(async () => {
  await sleep(1200);
  const out = []; let ok = true;
  const A = (n, c, e) => { out.push((c ? 'PASS ' : 'FAIL ') + n + (e ? ' :: ' + e : '')); if (!c) ok = false; };
  const doc = w.document;
  const imp = w.__wkImport;

  A('补录接口已暴露', !!imp);
  A('按钮文案为「手动补录待下单」', /手动补录待下单/.test((doc.getElementById('wk_import') || {}).textContent || ''));
  A('「清空补录」默认隐藏', (doc.getElementById('wk_import_clear') || {}).style.display === 'none');

  // ---- 表头识别 ----
  const aoa = CSV.split('\r\n').map(l => {
    // 简易 CSV 切分（测试数据无逗号嵌套，除 "1,050" 用引号包裹）
    const cells = []; let cur = '', q = false;
    for (let i = 0; i < l.length; i++) {
      const ch = l[i];
      if (ch === '"') { q = !q; continue; }
      if (ch === ',' && !q) { cells.push(cur); cur = ''; continue; }
      cur += ch;
    }
    cells.push(cur);
    return cells;
  });
  const det = imp.detect(aoa);
  A('表头行定位到第 3 行（0 基 2）', det.headerIdx === 2, 'headerIdx=' + det.headerIdx);
  A('识别出供应商列', det.cols.supplier === 1, 'col=' + det.cols.supplier);
  A('识别出物料编码列', det.cols.sku === 2, 'col=' + det.cols.sku);
  A('识别出 SPU 列', det.cols.spu === 3, 'col=' + det.cols.spu);
  A('识别出待下单数量列', det.cols.plan_qty === 6, 'col=' + det.cols.plan_qty);
  A('识别出申请单号列', det.cols.doc === 7, 'col=' + det.cols.doc);
  A('识别出采购员列', det.cols.buyer === 8, 'col=' + det.cols.buyer);
  A('识别出备注列', det.cols.remark === 9, 'col=' + det.cols.remark);

  // ---- 真正走一遍导入流程 ----
  const base = imp.baseCount();
  const file = new w.File([CSV], '补录测试.csv', { type: 'text/csv' });
  imp.handle(file);
  await sleep(900);

  const rows = imp.rows();
  A('导入 3 行（第 4 行为重复被跳过）', rows.length === 3, '实际 ' + rows.length + ' 行');
  A('WEEKLY 行数 = 原 ' + base + ' + 3', imp.weeklyCount() === base + 3, 'now=' + imp.weeklyCount());
  const qty = rows.reduce((s, x) => s + x.plan_qty, 0);
  A('合计数量 2,550 件（含千分位解析）', Math.round(qty) === 2550, 'qty=' + qty);

  const byShort = {};
  rows.forEach(x => { byShort[x.supplier_short] = (byShort[x.supplier_short] || 0) + x.plan_qty; });
  A('全称「广州市忆恩皮具有限公司」归并为简称「忆恩」', byShort['忆恩'] === 1500, JSON.stringify(byShort));
  A('文件里直接写简称「忆恩」也能归并', rows.filter(x => x.sku === 'SPTEST002').every(x => x.supplier_short === '忆恩'));
  A('未匹配的供应商原样保留', !!byShort['不存在的新厂'], JSON.stringify(byShort));
  A('缺 SPU 时按 SKU 前 4 位数字兜底', rows.every(x => x.spu && x.spu.length === 4), rows.map(x => x.spu).join(','));

  // ---- 预计在途汇总已重算 ----
  const tbl = (doc.getElementById('wk_sup_table') || {}).textContent || '';
  A('汇总表出现新供应商「不存在的新厂」', tbl.indexOf('不存在的新厂') >= 0);
  A('汇总表「合计」家数已含补录供应商', /合计\s*\d+\s*家/.test(tbl));

  // ---- 持久化 ----
  const saved = JSON.parse(w.localStorage.getItem('wk_manual_weekly_v1') || '[]');
  A('localStorage 已持久化 3 行', saved.length === 3, 'saved=' + saved.length);
  A('清空按钮已显示', (doc.getElementById('wk_import_clear') || {}).style.display !== 'none');

  // ---- 清空还原 ----
  w.confirm = () => true;
  imp.clear();
  await sleep(400);
  A('清空后补录行归零', imp.rows().length === 0);
  A('清空后 WEEKLY 回到 ' + base + ' 行', imp.weeklyCount() === base, 'now=' + imp.weeklyCount());
  A('清空后 localStorage 同步清空', JSON.parse(w.localStorage.getItem('wk_manual_weekly_v1') || '[]').length === 0);
  A('清空按钮重新隐藏', (doc.getElementById('wk_import_clear') || {}).style.display === 'none');

  A('无致命 JS 错误', errors.length === 0, errors.slice(0, 2).join(' | '));

  console.log(out.join('\n'));
  console.log(ok ? '\n==== ALL PASS ====' : '\n==== HAS FAIL ====');
  process.exit(ok ? 0 : 2);
})().catch(e => { console.log('FAIL: 测试异常\n' + (e && e.stack || e)); process.exit(1); });
