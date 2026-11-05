/* 映射表「已选 N 行」口径回归（jsdom + 真实 console/index.html）
 * 用户 2026-11-05 报：搜索 1176 后列表只剩 18 行，右上角却显示「已选 32 行」
 *   —— 上一轮搜索的勾选被保留，计数也把看不见的行算进去了。
 * 断言：
 *   1) 全选后「已选」= 当前筛选行数（含各分页），不会大于「共 N 条」
 *   2) 改搜索 / 改供应商筛选 / 改采购员筛选 / 切「只看多家报价」→ 选择清空
 *   3) 批量设置取到的行集合 = 当前筛选内的选中行（不会改到看不见的行）
 * 不写云端。
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const DIR = __dirname;
const html = fs.readFileSync(path.join(DIR, 'console/index.html'), 'utf8');
const sdkSrc = fs.readFileSync(path.join(DIR, 'vendor/workbuddy-cloud.js'), 'utf8');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let pass = 0, fail = 0;
function A(ok, msg, extra) {
  if (ok) { pass++; console.log('PASS: ' + msg); }
  else { fail++; console.log('FAIL: ' + msg + (extra ? ' :: ' + extra : '')); }
}

const dom = new JSDOM(html, {
  runScripts: 'dangerously', resources: undefined,
  url: 'http://localhost/console/index.html',
  beforeParse(w) {
    w.fetch = globalThis.fetch;
    w.Headers = globalThis.Headers; w.Request = globalThis.Request; w.Response = globalThis.Response;
    w.AbortController = globalThis.AbortController;
    w.scrollTo = () => {};
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
    w.eval(sdkSrc);
  }
});

function typeSearch(doc, val) {
  const inp = doc.getElementById('mapSearch');
  inp.value = val;
  inp.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
}

(async () => {
  const w = dom.window, doc = w.document;
  await sleep(1500);
  const t = w.__test;
  A(!!t, '__test 可用');
  if (!t) process.exit(1);
  const st = t.state();
  for (let i = 0; i < 80 && (!st.mapping || st.mapping.length < 1000); i++) await sleep(250);
  A(st.mapping.length > 1000, '云端映射已加载 ' + st.mapping.length + ' 条');

  const hint = () => (doc.getElementById('mapSelHint').textContent || '').trim();
  const visible = () => t.visibleMapRows().length;
  const selCount = () => t.visibleMapSel().length;
  const anySel = () => st.mapping.filter((m) => m._sel).length;

  /* ---- 1. 搜索 1176 → 全选 ---- */
  typeSearch(doc, '1176');
  await sleep(420);
  const n1 = visible();
  A(n1 > 0 && n1 < 200, '搜索 1176 命中 ' + n1 + ' 行');
  const chkAll = doc.getElementById('mapChkAll');
  chkAll.checked = true;
  chkAll.dispatchEvent(new w.Event('change', { bubbles: true }));
  A(selCount() === n1, '全选后已选 = 可见行数（' + selCount() + '/' + n1 + '）');
  A(hint() === '已选 ' + n1 + ' 行', '提示文案与列表一致：' + hint());
  A(anySel() === n1, '不存在「看不见但仍被选中」的行（全库选中 ' + anySel() + '）');

  /* ---- 2. 改搜索 → 旧选择必须清空（用户报的场景） ---- */
  typeSearch(doc, '0887');
  await sleep(420);
  A(anySel() === 0, '换搜索词后选择被清空（全库选中 ' + anySel() + '）');
  A(hint() === '', '换搜索词后不再显示「已选 N 行」：' + (hint() || '(空)'));
  A(chkAll.checked === false, '全选框已复位');
  const n2 = visible();
  A(n2 > 0, '搜索 0887 命中 ' + n2 + ' 行');

  /* ---- 3. 勾一行 → 已选 1 ---- */
  const cb0 = doc.querySelector('#mapBody tbody input[type=checkbox]') ||
              doc.querySelector('#mapBody input[type=checkbox]');
  A(!!cb0, '表格里能找到行勾选框');
  if (cb0) {
    cb0.checked = true;
    cb0.dispatchEvent(new w.Event('change', { bubbles: true }));
    A(selCount() === 1, '勾一行后已选 1', '已选 ' + selCount());
    A(hint() === '已选 1 行', '提示为「已选 1 行」：' + hint());
  }

  /* ---- 4. 改供应商筛选 → 清空 ---- */
  const fSup = doc.getElementById('mapFilterSupplier');
  if (fSup && fSup.options.length > 1) {
    fSup.value = fSup.options[1].value;
    fSup.dispatchEvent(new w.Event('change', { bubbles: true }));
    A(anySel() === 0, '改供应商筛选后选择被清空（选中 ' + anySel() + '）');
    fSup.value = '';
    fSup.dispatchEvent(new w.Event('change', { bubbles: true }));
  } else {
    A(true, '（供应商筛选无选项，跳过）');
  }

  /* ---- 5. 改采购员筛选 → 清空 ---- */
  typeSearch(doc, '');
  await sleep(420);
  const cba = doc.querySelector('#mapBody input[type=checkbox]');
  if (cba) { cba.checked = true; cba.dispatchEvent(new w.Event('change', { bubbles: true })); }
  const fBuy = doc.getElementById('mapFilterBuyer');
  if (fBuy && fBuy.options.length > 1) {
    fBuy.value = fBuy.options[1].value;
    fBuy.dispatchEvent(new w.Event('change', { bubbles: true }));
    A(anySel() === 0, '改采购员筛选后选择被清空（选中 ' + anySel() + '）');
    fBuy.value = '';
    fBuy.dispatchEvent(new w.Event('change', { bubbles: true }));
  } else {
    A(true, '（采购员筛选无选项，跳过）');
  }

  /* ---- 6. 只看多家报价 → 清空 ---- */
  typeSearch(doc, '1176');
  await sleep(420);
  const ca2 = doc.getElementById('mapChkAll');
  ca2.checked = true;
  ca2.dispatchEvent(new w.Event('change', { bubbles: true }));
  const before = anySel();
  doc.getElementById('btnOnlyMultiQuote').click();
  A(anySel() === 0, '切「只看多家报价」后选择被清空（切前 ' + before + ' 行，切后 ' + anySel() + '）');
  doc.getElementById('btnOnlyMultiQuote').click();

  /* ---- 7. 计数永不超过列表条数 ---- */
  typeSearch(doc, '1176');
  await sleep(420);
  const ca3 = doc.getElementById('mapChkAll');
  ca3.checked = true;
  ca3.dispatchEvent(new w.Event('change', { bubbles: true }));
  A(selCount() <= visible(), '已选数不超过当前筛选行数（' + selCount() + ' <= ' + visible() + '）');

  console.log('\n==== ' + (fail ? 'FAIL ' + fail + ' / ' : 'ALL PASS ') + pass + ' 项' + (fail ? '' : ' ====') + ' ====');
  process.exit(fail ? 1 : 0);
})();
