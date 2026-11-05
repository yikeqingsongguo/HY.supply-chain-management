/* 数据订正：sku_quote.short_name 与 supplier 不一致的行，按 supplier 在 sku_map 里的简称改回。
 * 背景：保存报价时曾用「行的简称」写入 short_name，导致 忆恩/益滢 的报价被标成「经纬」。
 * 口径：只改「非空且与 supplier 不匹配」的行；空简称不动（显示侧会按索引查）。
 * 幂等：重复执行不会产生新的变更。
 * 用法：node _fix_quote_short.js          # 只报告，不写库
 *       node _fix_quote_short.js --apply  # 实际写库
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const DIR = __dirname;
const APPLY = process.argv.includes('--apply');
const html = fs.readFileSync(path.join(DIR, 'console/index.html'), 'utf8');
const sdkSrc = fs.readFileSync(path.join(DIR, 'vendor/workbuddy-cloud.js'), 'utf8');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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

function norm(s) { return String(s || '').replace(/\s+/g, ''); }
function contains(a, b) { return !!a && !!b && (a.indexOf(b) >= 0 || b.indexOf(a) >= 0); }

(async () => {
  const w = dom.window;
  await sleep(2000);
  const t = w.__test;
  if (!t || !t.db()) { console.log('云端不可用'); process.exit(1); }

  async function pull(table, cols) {
    const d = t.db();
    let out = [], from = 0;
    for (;;) {
      const res = await d.from(table).select(cols).order('id', { ascending: true }).range(from, from + 999);
      if (res && res.error) throw new Error(JSON.stringify(res.error));
      const list = (res && res.data) || [];
      out = out.concat(list);
      if (list.length < 1000) break;
      from += 1000;
    }
    return out;
  }

  const quotes = await pull('sku_quote', 'id,sku,supplier,short_name,price');
  const maps = await pull('sku_map', 'id,sku,supplier,short_name');

  // 供应商全称 → 简称（取映射表里出现最多的那个，避免个别脏行带偏）
  const tally = {};
  maps.forEach((r) => {
    const sup = norm(r.supplier), sn = String(r.short_name || '').trim();
    if (!sup || !sn) return;
    const k = sup.toLowerCase();
    tally[k] = tally[k] || {};
    tally[k][sn] = (tally[k][sn] || 0) + 1;
  });
  const shortOf = {};
  Object.keys(tally).forEach((k) => {
    let best = '', n = -1;
    Object.keys(tally[k]).forEach((sn) => { if (tally[k][sn] > n) { n = tally[k][sn]; best = sn; } });
    shortOf[k] = best;
  });

  const fixes = [];
  const unknown = {};
  quotes.forEach((q) => {
    const sup = norm(q.supplier), sn = String(q.short_name || '').trim();
    if (!sup || !sn) return;                     // 空简称不动
    if (contains(sn, sup) || sup.indexOf(sn) >= 0) return;  // 简称是全称的一部分 → 视为正确
    const want = shortOf[sup.toLowerCase()];
    if (!want) { unknown[sup] = (unknown[sup] || 0) + 1; return; }
    if (want === sn) return;
    fixes.push({ id: q.id, sku: q.sku, supplier: q.supplier, from: sn, to: want, price: q.price });
  });

  console.log('报价行总数        :', quotes.length);
  console.log('简称与供应商不匹配:', fixes.length + Object.keys(unknown).reduce((a, k) => a + unknown[k], 0));
  console.log('  可订正（映射表有该供应商）:', fixes.length);
  console.log('  无法订正（映射表查不到）  :', Object.keys(unknown).length, '家', unknown);
  const byPair = {};
  fixes.forEach((f) => { const k = f.from + ' → ' + f.to; byPair[k] = (byPair[k] || 0) + 1; });
  Object.keys(byPair).forEach((k) => console.log('    ', k, byPair[k], '行'));
  if (fixes.length) {
    const ex = {};
    fixes.forEach((f) => { ex[f.sku] = ex[f.sku] || f; });
    console.log('  示例：');
    Object.keys(ex).slice(0, 5).forEach((sku) => {
      const f = ex[sku];
      console.log('    ', sku, '|', f.supplier, '|', f.from, '→', f.to);
    });
  }

  if (!APPLY) { console.log('\n（仅报告，未写库。加 --apply 执行订正）'); process.exit(0); }
  if (!fixes.length) { console.log('\n无需订正'); process.exit(0); }

  let ok = 0, bad = 0;
  for (const f of fixes) {
    const res = await t.db().from('sku_quote').update({ short_name: f.to }).eq('id', f.id);
    if (res && res.error) { bad++; if (bad <= 3) console.log('  ✗', f.id, JSON.stringify(res.error)); }
    else ok++;
  }
  console.log('\n订正完成：成功', ok, '行 / 失败', bad, '行');

  // 复核
  const again = await pull('sku_quote', 'id,sku,supplier,short_name');
  const left = again.filter((q) => {
    const sup = norm(q.supplier), sn = String(q.short_name || '').trim();
    if (!sup || !sn) return false;
    if (sup.indexOf(sn) >= 0) return false;
    const want = shortOf[sup.toLowerCase()];
    return want && want !== sn;
  });
  console.log('复核：仍不匹配', left.length, '行');
  process.exit(0);
})();
