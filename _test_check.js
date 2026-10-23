/* 漏下单核查 · 差异口径单测（jsdom 直接调 Core.checkMissing 单文件模式）
 * 覆盖：
 *   1) 申请 194 / 剩余 -6  → 已下单 200、差异 -6（三个数能对上）
 *   2) 剩余 0             → 已下单 = 申请、差异 0
 *   3) 剩余 > 0           → 视为未下单，已下单 0
 *   4) 分组/汇总中「超下单」不污染缺口统计
 */
const path = require('path');
const fs = require('fs');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, 'console/index.html'), 'utf8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  resources: undefined,
  url: 'http://localhost/console/index.html',
  beforeParse(w) {
    w.fetch = () => Promise.reject(new Error('offline'));
    w.scrollTo = () => {};
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
    w.addEventListener('error', (e) => { lastErr = String(e.message || e.error); });
    let lastErr = '';
  }
});

const w = dom.window;
let pass = 0, fail = 0;
function A(ok, msg) {
  if (ok) { pass++; console.log('PASS: ' + msg); }
  else { fail++; console.log('FAIL: ' + msg); }
}

setTimeout(() => {
  const Core = w.Core;
  A(!!Core && !!Core.checkMissing, '核心库 Core.checkMissing 可用');
  if (!Core) return finish();

  // 申请单行：qty=申请数量，remainQty=剩余数量
  const applies = [
    { key: 'A1', sku: 'SKU-A', qty: 194, remainQty: -6,  no: 'NO1', date: '2026-10-15', buyer: '吴巧玲', supplier: '贝瑞卡', ling: '吴颖', status: '', closeStatus: '' },
    { key: 'A2', sku: 'SKU-B', qty: 100, remainQty: 0,   no: 'NO2', date: '2026-10-15', buyer: '吴巧玲', supplier: '贝瑞卡', ling: '吴颖', status: '', closeStatus: '' },
    { key: 'A3', sku: 'SKU-C', qty: 500, remainQty: 500, no: 'NO3', date: '2026-10-15', buyer: '吴巧玲', supplier: '贝瑞卡', ling: '吴颖', status: '', closeStatus: '' }
  ];
  const res = Core.checkMissing(applies, [], { mode: 'single', mapIndex: null, prefixes: [] });
  const bySku = {};
  (res.rows || []).forEach(r => { bySku[r.sku] = r; });

  const a = bySku['SKU-A'];
  A(!!a, '超下单 SKU-A 出现在核查结果中');
  if (a) {
    A(a.orderQty === 200, '申请194/剩余-6 → 已下单 200（实得 ' + a.orderQty + '）');
    A(a.diffQty === -6, '差异数量 = -6（实得 ' + a.diffQty + '）');
    A(a.applyQty - a.orderQty === a.diffQty, '三数自洽：申请 - 已下单 = 差异');
    A(a.gapType === 'over', '判定类型为 over（实得 ' + a.gapType + '）');
  }
  const b = bySku['SKU-B'];
  A(b && b.orderQty === 100 && b.diffQty === 0 && b.gapType === 'ok', '剩余0 → 已下单100/差异0/ok');
  const c = bySku['SKU-C'];
  A(c && c.orderQty === 0 && c.diffQty === 500 && c.gapType === 'not_ordered', '剩余500 → 已下单0/差异500/未下单');

  A(res.summary.diffQty === 500, '汇总差异总量只累计正缺口（实得 ' + res.summary.diffQty + '）');
  A(res.summary.overSku === 1 && res.summary.overQty === 6, '超下单单独统计 1 个 SKU / 6 件');

  // 明细列表「查看全部」（差异档）：超下单行必须出现
  const st = w.__test.state();
  st.checkResult = res;
  st.checkFilter = 'diff';
  st.checkSearch = '';
  st.checkColsFilt = {};
  st.checkRemainFilter = '';
  st.checkSupplierFilter = '';
  st.checkBuyerFilter = '';
  const list = w.__test.filteredCheckRows().map(r => r.sku);
  A(list.indexOf('SKU-A') >= 0, '「查看全部（有差异）」包含超下单行 SKU-A（当前 ' + list.join(',') + '）');
  A(list.indexOf('SKU-C') >= 0, '「查看全部（有差异）」包含未下单行 SKU-C');
  A(list.indexOf('SKU-B') < 0, '已下齐行 SKU-B 不出现在差异列表');

  st.checkFilter = 'over';
  const overList = w.__test.filteredCheckRows().map(r => r.sku);
  A(overList.length === 1 && overList[0] === 'SKU-A', '「仅超量下单」筛出 SKU-A');

  finish();

  function finish() {
    console.log('\n' + (fail ? '❌ FAILED ' + fail + ' / ' : '==== ALL PASS ==== ') + (pass + fail) + ' 项');
    process.exit(fail ? 1 : 0);
  }
}, 1200);
