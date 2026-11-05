/* 报价一致性回归（jsdom + 真实 console/index.html）
 * 覆盖用户 2026-11-05 报的三个问题：
 *   1) 价格列与备选列显示同一家同一个价（同一条报价既算主价又算备选）
 *   2) 改供应商后价格仍挂在原供应商；同一家出现两种报价
 *   3) 导入价目表建出的「有价无供应商」行要进未匹配补录清单
 * 只改内存中的合成行，不写云端。
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

const YIEN = '广州市忆恩皮具有限公司';
const JINGWEI = '广州经纬革物科技有限公司';
const RUNFENG = '广州市润峰箱包科技有限公司';
const YIYING = '广州益滢实业有限公司';

(async () => {
  const w = dom.window;
  await sleep(1500);
  const t = w.__test;
  A(!!t, '__test 可用');
  if (!t) process.exit(1);
  /* 等云端映射真正加载完：简称索引依赖 state.mapping，没加载完会回退成全称 */
  const st0 = t.state();
  for (let i = 0; i < 80 && (!st0.mapping || st0.mapping.length < 1000); i++) await sleep(250);
  A(st0.mapping.length > 1000, '云端映射已加载 ' + st0.mapping.length + ' 条');

  /* ---------- 1. 供应商同一性 ---------- */
  A(t.sameSupplier(YIEN, ' 广州市忆恩皮具有限公司 ') === true, 'sameSupplier 忽略首尾空格');
  A(t.sameSupplier('广州经纬革物科技有限公司', '广州市经纬革物科技有限公司') === true,
    'sameSupplier 忽略「广州/广州市」差异');
  A(t.sameSupplier(YIEN, JINGWEI) === false, 'sameSupplier 不把两家不同公司判成同一家');

  /* ---------- 2. 同一条报价不能既主又备（问题 1） ---------- */
  const row1 = {
    sku: 'TEST-Q-001', supplier: YIEN, buyer: '张洁', shortName: '忆恩', note: '',
    price: '64.77', priceSupplier: YIEN,
    alts: [
      { supplier: YIEN, price: '64.77', shortName: '经纬' },          // 历史脏数据：同家同业，简称还写错
      { supplier: RUNFENG, price: '70.00' }
    ],
    _new: true
  };
  t.ensureRowShape(row1);
  A((row1.alts || []).length === 1, '同主价同供应商的备选被去掉（只剩 1 条）', 'alts=' + JSON.stringify(row1.alts));
  A(!(row1.alts || []).some((a) => t.sameSupplier(a.supplier, YIEN)), '备选里不再有主报价那家');

  const prev1 = t.mapColValue(row1, 'price');
  const prev2 = t.mapColValue(row1, 'alt1');
  A(prev1 !== prev2, '价格列与备选列不再显示成同一家同一价', prev1 + ' / ' + prev2);
  A(/^忆恩 64\.77$/.test(prev1), '价格列简称取报价方（忆恩）而不是行简称', prev1);

  /* ---------- 3. 同家多条报价只留最低价 ---------- */
  const dup = t.dedupeAlts([
    { supplier: RUNFENG, price: '75.90' },
    { supplier: '广州市润峰箱包科技有限公司 ', price: '74.80' }
  ], '');
  A(dup.length === 1, '同一供应商多条报价合并成 1 条', 'n=' + dup.length);
  A(String(dup[0].price) === '74.80', '合并后保留最低价 74.80', String(dup[0].price));

  /* ---------- 4. 改供应商：旧价降备选、新家价升主价（问题 2） ---------- */
  const row2 = {
    sku: 'TEST-Q-002', supplier: YIYING, buyer: '聂婷', shortName: '益滢', note: '',
    price: '75.90', priceSupplier: YIYING,
    alts: [{ supplier: RUNFENG, price: '74.80', shortName: '润峰' }],
    _new: true
  };
  row2.supplier = RUNFENG;                       // 模拟批量改成润峰
  row2.shortName = '润峰';
  const ch = t.reconcileQuotesForRow(row2, YIYING);
  A(ch === true, '改供应商触发报价重排');
  A(String(row2.price) === '74.80', '新供应商（润峰）的备选价升为主价', String(row2.price));
  A(t.sameSupplier(row2.priceSupplier, RUNFENG), '主价归属改为润峰', row2.priceSupplier);
  A((row2.alts || []).some((a) => t.sameSupplier(a.supplier, YIYING) && String(a.price) === '75.90'),
    '原主价 75.90（益滢）降为备选', JSON.stringify(row2.alts));
  A(!t.mapColValue(row2, 'price').includes('益滢') || t.mapColValue(row2, 'price').indexOf('润峰') === 0,
    '价格列显示的是润峰而不是益滢', t.mapColValue(row2, 'price'));

  /* ---------- 5. 新供应商没有报价：主价清空，绝不挂别家价 ---------- */
  const row3 = {
    sku: 'TEST-Q-003', supplier: YIYING, buyer: '聂婷', shortName: '益滢', note: '',
    price: '80.00', priceSupplier: YIYING, alts: [], _new: true
  };
  row3.supplier = '广州思哲箱包有限公司';
  row3.shortName = '思哲';
  t.reconcileQuotesForRow(row3, YIYING);
  A(row3.price === '' && row3.priceSupplier === '', '新供应商无报价时主价清空', 'price=' + row3.price);
  A((row3.alts || []).some((a) => t.sameSupplier(a.supplier, YIYING) && String(a.price) === '80.00'),
    '原价 80.00 仍以益滢名义保留在备选', JSON.stringify(row3.alts));
  A(t.mapColValue(row3, 'price') === '—', '主价清空后价格列显示「—」', t.mapColValue(row3, 'price'));

  /* ---------- 6. 供应商没变时不动报价 ---------- */
  const row4 = {
    sku: 'TEST-Q-004', supplier: RUNFENG, buyer: '聂婷', shortName: '润峰', note: '',
    price: '74.80', priceSupplier: RUNFENG, alts: [], _new: true
  };
  A(t.reconcileQuotesForRow(row4, '广州市润峰箱包科技有限公司 ') === false, '同一家（写法不同）不触发重排');
  A(String(row4.price) === '74.80', '未重排时价格保持不变');

  /* ---------- 7. applyPriceJson 用「同一家」比较，不会被空格/前缀卡住 ---------- */
  const m5 = { sku: 'TEST-Q-005', supplier: '广州经纬革物科技有限公司', shortName: '经纬', buyer: '何君豪', price: '', priceSupplier: '', alts: [], _new: true };
  const pj = {};
  pj['TEST-Q-005'] = {
    '广州市经纬革物科技有限公司': { price: '66.00' },
    '广州市忆恩皮具有限公司': { price: '64.77' }
  };
  t.applyPriceJson([m5], pj);
  A(String(m5.price) === '66.00', '主价按「同一家」匹配到 66.00（不再因写法差异掉进备选）', String(m5.price));
  A((m5.alts || []).length === 1 && String(m5.alts[0].price) === '64.77', '另一家进备选 64.77');

  /* ---------- 8. 有价无供应商的行要进未匹配补录（问题 3） ---------- */
  const st = t.state();
  st.mapping.push({
    rid: '', sku: 'TEST-Q-006', supplier: '', buyer: '', shortName: '',
    note: '价目表导入·待指定供应商', updated: '', price: '', priceSupplier: '',
    alts: [{ supplier: JINGWEI, price: '73.90' }], _new: true, _dirty: false, _deleted: false, _sel: false
  });
  const keys = t.allUnmatchKeys().map((k) => String(k).toUpperCase());
  A(keys.indexOf('TEST-Q-006') >= 0, '「有价无供应商」的 SKU 出现在未匹配补录清单');
  const r6 = st.mapping[st.mapping.length - 1];
  A(t.mapColValue(r6, 'alt1').indexOf('73.90') > 0, '该行报价显示在备选列', t.mapColValue(r6, 'alt1'));

  console.log('\n==== ' + (fail ? 'FAIL ' + fail + ' / ' : 'ALL PASS ') + pass + ' 项' + (fail ? '' : ' ====') + ' ====');
  process.exit(fail ? 1 : 0);
})();
