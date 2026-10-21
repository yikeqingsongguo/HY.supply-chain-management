/* 待下单汇总 v1.6.4 冒烟测试（jsdom）：
 * 1) 采购员汇总行点击下钻明细（含「（未填写）」）
 * 2) 补录填写采购员 → 待下单采购员统计同步（未填写归位）
 * 3) 导出 Excel 按钮 → 生成 .xlsx（Blob 有效）
 */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const HERE = __dirname;
const DIR = path.join(HERE, 'console');
const html = fs.readFileSync(path.join(DIR, 'index.html'), 'utf8');

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => {
  const msg = String(e && e.message || e);
  if (/DragEvent|DataTransfer|not implemented/i.test(msg)) return;
  errors.push('jsdomError: ' + msg);
});
vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));

class LocalLoader {}   // jsdom30 已移除 ResourceLoader，XLSX 在 beforeParse 里注入

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'http://localhost/console/index.html',
  virtualConsole: vc,
  beforeParse(w) {
    // jsdom 不加载外部 script，直接把 vendored SheetJS（UMD）挂到 window.XLSX
    w.XLSX = require(path.join(HERE, 'vendor', 'xlsx.full.min.js'));
    w.fetch = function (u) {
      const name = String(u).split('/').pop().split('?')[0];
      const p = path.join(DIR, name);
      if (!fs.existsSync(p)) return Promise.resolve({ ok: false, status: 404 });
      return Promise.resolve(new Response(fs.readFileSync(p), { status: 200 }));
    };
    w.DataTransfer = function () { this.items = { add() {} }; this.files = []; };
    w.DragEvent = class extends w.Event {
      constructor(t, o) { super(t, o); this.dataTransfer = (o && o.dataTransfer) || null; }
    };
    w.__lastBlob = null;
    w.URL.createObjectURL = function (b) { w.__lastBlob = b; return 'blob:test'; };
    w.URL.revokeObjectURL = function () {};
  }
});

const w = dom.window;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const A = (c, msg) => { if (!c) { console.log('FAIL:', msg); process.exitCode = 1; } else console.log('PASS:', msg); };

(async () => {
  let tries = 0;
  while (tries++ < 50 && !w.__wkPendingSkus) await sleep(100);
  A(!!w.__wkPendingSkus, 'weekly.json 加载且 __wkPendingSkus 就绪');
  await sleep(300);

  // 待下单汇总 = 侧边栏 supplier？实际 tab 是 supplier（透视）—— wk 模块渲染在 supplier tab
  const sb = w.document.querySelector('.sb-item[data-tab="supplier"]');
  A(!!sb, '存在待下单（透视）入口');
  sb.click();
  await sleep(300);

  const bs = w.document.getElementById('wkBuyerSummary');
  A(!!bs && /采购员/.test(bs.innerHTML), '采购员汇总已渲染');
  A(!!w.document.getElementById('wkExportExcel'), '存在「导出 Excel」按钮');

  const buyerRows = Array.prototype.slice.call(bs.querySelectorAll('tr.wk-row[data-buyer]'));
  A(buyerRows.length > 0, '采购员行可识别（' + buyerRows.length + ' 人）');
  const unfilled = buyerRows.find(r => r.getAttribute('data-buyer') === '（未填写）');
  A(!!unfilled, '「（未填写）」行存在且可点击下钻');

  // 下钻（未填写）
  unfilled.click();
  await sleep(200);
  const sub = bs.querySelector('tr.wk-sub[data-buyer="（未填写）"]');
  A(!!sub, '点击「（未填写）」展开明细子表');
  const subRows = sub ? sub.querySelectorAll('tbody tr').length : 0;
  A(subRows > 0, '子表含明细行（' + subRows + ' 行，含 SKU/规格/单号/数量/供应商列）');
  A(/规格型号/.test(sub.innerHTML) && /申请单号/.test(sub.innerHTML) && /供应商/.test(sub.innerHTML), '子表列头含 规格型号/申请单号/供应商');
  // 再点收起
  unfilled.click();
  await sleep(100);
  A(!bs.querySelector('tr.wk-sub[data-buyer="（未填写）"]'), '再次点击可收起明细');

  // 补录采购员 → 统计同步
  const before = (bs.querySelector('tr[data-buyer="（未填写）"]') || {}).outerHTML || '';
  const qtyBefore = (before.match(/<\/i><\/div><span class="wk-num">|text-align:right">([\d,.]+)/) || [])[1];
  w.__wkOnMappingSaved('VYGJZ011203', '', '', '梁成杰');
  await sleep(300);
  const html2 = bs.innerHTML;
  A(/data-buyer="梁成杰"/.test(html2), '补录采购员「梁成杰」后汇总出现该采购员行');
  const localMap = JSON.parse(w.localStorage.getItem('wk_sup_map_v1') || '{}');
  A(localMap['VYGJZ011203'] && localMap['VYGJZ011203'].buyer === '梁成杰', 'localStorage wk_sup_map_v1 已记录 buyer');

  // 导出 Excel
  const btn = w.document.getElementById('wkExportExcel');
  btn.click();
  await sleep(400);
  A(!!w.__lastBlob && w.__lastBlob.size > 5000, '点击导出生成有效 .xlsx Blob（' + (w.__lastBlob ? w.__lastBlob.size : 0) + ' bytes）');
  if (w.__lastBlob) {
    const buf = Buffer.from(await w.__lastBlob.arrayBuffer());
    A(buf.slice(0, 2).toString() === 'PK', 'Blob 为 zip 签名（.xlsx 容器正确）');
    const names = [];
    // 粗扫 zip local file headers 里的 sheet 名
    const s = buf.toString('latin1');
    ['xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml', 'xl/workbook.xml'].forEach(n => {
      if (s.indexOf(n) >= 0) names.push(n);
    });
    A(names.length === 3, '包含双 worksheet + workbook 结构（' + names.join(', ') + '）');
  }

  // 语法/错误
  A(errors.length === 0, '无致命 JS 错误' + (errors.length ? ' → ' + errors.slice(0, 3).join(' | ') : ''));
  process.exit(process.exitCode || 0);
})().catch(e => { console.log('FAIL: 测试异常', e && e.stack || e); process.exit(1); });
