/* 只读探针：把云端 sku_quote / sku_map 全量拉下来，找出三类脏数据
 *   1) 同一 SKU 下同一家供应商出现两种写法（全称/简称并存）→ 映射表「价格」与「备选1」显示一模一样
 *   2) 同一 SKU 下同一家供应商出现两个不同价格 → 同一家两种报价
 *   3) 映射行没有供应商，但云端有报价 → 价格有值、简称/全称/采购员为空
 * 结果写入 _probe_quote.json，供 Python 侧统计。只读，不写库。
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const DIR = __dirname;
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

(async () => {
  const w = dom.window;
  await sleep(2000);
  const t = w.__test;
  if (!t || !t.db() ) { console.log('云端不可用'); process.exit(1); }

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

  const quotes = await pull('sku_quote', 'id,sku,supplier,buyer,short_name,price');
  const maps = await pull('sku_map', 'id,sku,supplier,buyer,short_name');
  console.log('quote rows', quotes.length, '| map rows', maps.length);

  fs.writeFileSync(path.join(DIR, '_probe_quote.json'),
    JSON.stringify({ quotes, maps, at: new Date().toISOString() }), 'utf8');
  console.log('已写 _probe_quote.json');
  process.exit(0);
})();
