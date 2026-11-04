/* 云端读写往返测试（jsdom + 真实云服务 SDK + 真实网络）
 * 覆盖：
 *   1) 云端能拉到 10677 条映射 + 18403 条报价
 *   2) 改一条映射 → saveMapping → 换新实例重新读，能看到改动
 *   3) 新增一个 SKU + 报价 → 保存 → 新实例能读到，且报价挂在正确 SKU 上
 *   4) 删除该测试 SKU → 新实例读不到（清理干净）
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const DIR = __dirname;
const html = fs.readFileSync(path.join(DIR, 'console/index.html'), 'utf8');
const sdkSrc = fs.readFileSync(path.join(DIR, 'vendor/workbuddy-cloud.js'), 'utf8');

let pass = 0, fail = 0;
function A(ok, msg) { if (ok) { pass++; console.log('PASS: ' + msg); } else { fail++; console.log('FAIL: ' + msg); } }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function boot() {
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', resources: undefined,
    url: 'http://localhost/console/index.html',
    beforeParse(w) {
      w.fetch = globalThis.fetch;              // 让 SDK 走真实网络
      w.Headers = globalThis.Headers; w.Request = globalThis.Request; w.Response = globalThis.Response;
      w.AbortController = globalThis.AbortController;
      w.scrollTo = () => {};
      w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
      w.eval(sdkSrc);                          // 注入 SDK（等价于 <script src>）
    }
  });
  return dom;
}

(async () => {
  /* ---------- 第一实例：读全量 ---------- */
  const dom1 = boot();
  const w1 = dom1.window;
  await sleep(1500);
  const t1 = w1.__test;
  A(!!w1.WorkBuddyCloud, 'SDK 全局已注入');
  A(!!t1 && !!t1.db && !!t1.db(), 'db() 拿到云数据库客户端（非 null）');
  const st1 = t1.state();
  for (let i = 0; i < 60 && (!st1.mapping || st1.mapping.length < 1000); i++) await sleep(250);
  A(st1.mapping.length === 10677, '云端拉到映射 ' + st1.mapping.length + ' 条（期望 10677）');
  const priced = st1.mapping.filter((m) => m.price || (m.alts && m.alts.length)).length;
  A(priced > 10000, '带报价的映射行 ' + priced + ' 条');
  A(!!st1.cloudOK, 'state.cloudOK = true');
  const syncTxt = w1.document.getElementById('syncTxt').textContent;
  A(/已同步/.test(syncTxt), '状态条显示已同步：' + syncTxt);

  /* ---------- 改一条已有行 ---------- */
  const target = st1.mapping[0];
  const skuT = target.sku, oldBuyer = target.buyer;
  const newBuyer = oldBuyer === '张洁' ? '测试采购员A' : '张洁';
  target.buyer = newBuyer;
  target._dirty = true;
  await t1.saveMapping(true);
  await sleep(500);
  A(!target._dirty, '保存后脏标记已清除');

  /* ---------- 新增一个测试 SKU（含报价） ---------- */
  const TEST_SKU = 'ZZTEST_SKU_0001';
  st1.mapping.push({
    rid: '', sku: TEST_SKU, supplier: '广州市忆恩皮具有限公司', buyer: '测试采购员B',
    shortName: '忆恩', note: '自动化测试行', price: '12.34', priceSupplier: '广州市忆恩皮具有限公司',
    alts: [{ supplier: '广州思哲箱包有限公司', buyer: '', shortName: '思哲', price: '13.00', currency: '人民币', validFrom: '2026-01-01' }],
    updated: '', _new: true, _dirty: true, _deleted: false, _sel: false
  });
  await t1.saveMapping(true);
  await sleep(500);

  /* ---------- 第二实例：重新读，验证持久化 ---------- */
  const dom2 = boot();
  const w2 = dom2.window;
  await sleep(1500);
  const t2 = w2.__test, st2 = t2.state();
  for (let i = 0; i < 60 && (!st2.mapping || st2.mapping.length < 1000); i++) await sleep(250);
  const got1 = st2.mapping.find((m) => m.sku === skuT);
  A(!!got1 && got1.buyer === newBuyer, '修改已持久化：' + skuT + ' 采购员 → ' + (got1 ? got1.buyer : '(缺失)'));
  const got2 = st2.mapping.find((m) => m.sku === TEST_SKU);
  A(!!got2, '新增 SKU 已持久化：' + TEST_SKU);
  if (got2) {
    A(got2.supplier === '广州市忆恩皮具有限公司', '新增行供应商正确：' + got2.supplier);
    A(String(got2.price) === '12.34', '主报价正确：' + got2.price);
    const alt = (got2.alts || []).find((a) => a.supplier === '广州思哲箱包有限公司');
    A(!!alt && Number(alt.price) === 13, '备选报价正确：' + (alt ? alt.price : '(缺失)'));
  }
  A(st2.mapping.length <= 10678, '总行数没有膨胀：' + st2.mapping.length);

  /* ---------- 清理：删掉测试 SKU，恢复被改的行 ---------- */
  const del = st2.mapping.find((m) => m.sku === TEST_SKU);
  if (del) { del._deleted = true; await t2.saveMapping(true); await sleep(400); }
  const back = st2.mapping.find((m) => m.sku === skuT);
  if (back) { back.buyer = oldBuyer; back._dirty = true; await t2.saveMapping(true); await sleep(400); }

  const dom3 = boot();
  await sleep(1500);
  const t3 = dom3.window.__test, st3 = t3.state();
  for (let i = 0; i < 60 && (!st3.mapping || st3.mapping.length < 1000); i++) await sleep(250);
  A(!st3.mapping.some((m) => m.sku === TEST_SKU), '测试 SKU 已删除（新实例读不到）');
  const restored = st3.mapping.find((m) => m.sku === skuT);
  A(!!restored && restored.buyer === oldBuyer, '被修改行已还原：' + (restored ? restored.buyer : '(缺失)'));

  console.log('\n==== ' + (fail === 0 ? 'ALL PASS' : 'FAILED') + ' ==== ' + pass + ' 通过 / ' + fail + ' 失败');
  process.exit(fail === 0 ? 0 : 1);
})();
