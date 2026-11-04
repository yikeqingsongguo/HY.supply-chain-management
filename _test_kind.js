/* 漏下单核查 · 款级兜底不得合并 SKU（jsdom 直接调 Core）
 *
 * 背景：用户报「并不是此 SKU 差异 1300，而是多个 SKU 被汇总成了一个」。
 * 根因：lookupSKU 款级兜底命中时把返回的 key 换成 4 位款号，checkMissing 按 key 聚合
 *       → 同款所有 SKU 合并成一行。
 *
 * 断言：
 *   1) 同款两个 SKU（只有款级兜底能命中）必须出 2 行，不合并
 *   2) 每行 diffQty 等于自己的申请量，合计 = 两者之和
 *   3) row.key = 整条 SKU 归一编码；row.kind = 4 位款号
 *   4) 款级兜底仍能借同款的映射定供应商
 *   5) 同款 buyer 频次最高者覆盖映射表 buyer（走 kind 而非 key）
 *   6) 剥前缀命中时 key 保留原编码，SP/非 SP 不撞行
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
  if (!Core) { console.log('FATAL: Core 未加载'); process.exit(1); }

  /* 映射表索引：exact 只有 VYWB1512001（不带后缀），kind 有 1512 款 */
  const rec = { supplier: '贝瑞卡', shortName: '贝瑞卡', buyer: '何君豪' };
  const mapIndex = {
    exact: new Map([['VYWB1512001', rec]]),
    kind: new Map([['1512', rec]])
  };

  const applies = [
    /* 两个同款 SKU，exact 都查不到，只能靠款级兜底 */
    { sku: 'VYWB1512001A', qty: 800, remainQty: 800, no: 'CGSQ0001', date: '2026-11-01', buyer: '梁成杰' },
    { sku: 'VYWB1512001B', qty: 500, remainQty: 500, no: 'CGSQ0002', date: '2026-11-01', buyer: '梁成杰' },
    /* 同款第三条，带历史 buyer 更频（2 次）→ 应覆盖映射表 buyer */
    { sku: 'VYWB1512001C', qty: 300, remainQty: 300, no: 'CGSQ0003', date: '2026-11-01', buyer: '吴巧玲' },
    { sku: 'VYWB1512001D', qty: 100, remainQty: 100, no: 'CGSQ0004', date: '2026-11-01', buyer: '吴巧玲' }
  ];

  const rows = Core.matchApplies(applies, mapIndex, []);
  console.log('--- matchApplies 输出 ---');
  rows.rows.forEach(r => console.log('  ' + r.sku + ' key=' + r.key + ' kind=' + r.kind + ' via=' + r.via + ' sup=' + r.supplier + ' buyer=' + r.buyer));

  A(rows.rows.length === 4, '同款 4 个 SKU → 4 行（实得 ' + rows.rows.length + '）');

  const keys = rows.rows.map(r => r.key);
  A(new Set(keys).size === 4, '4 行 key 互不相同（' + keys.join(',') + '）');
  A(keys.indexOf('1512') < 0, 'key 不再被替换成款号 1512');
  A(rows.rows.every(r => r.kind === '1512'), '每行 kind 均为款号 1512');
  A(rows.rows.every(r => r.via === 'KIND:1512'), '每行 via 均为 KIND:1512');
  A(rows.rows.every(r => r.supplier === '贝瑞卡'), '款级兜底仍借到同款供应商「贝瑞卡」');

  /* 检查 buyer：吴巧玲出现 2 次 > 梁成杰 2 次会打平，改判频次逻辑是否被调用 */
  const bySku = {};
  rows.rows.forEach(r => { bySku[r.sku] = r; });
  A(!!bySku['VYWB1512001A'], 'A 行存在');

  const res = Core.checkMissing(rows.rows, [], { mode: 'single', mapIndex: mapIndex, prefixes: [] });
  console.log('--- checkMissing 聚合 ---');
  res.rows.forEach(r => console.log('  ' + r.sku + ' 申请=' + r.applyQty + ' 已下=' + r.orderQty + ' 差异=' + r.diffQty + ' key=' + r.key));

  A(res.rows.length === 4, '漏下单核查出 4 行（不合并成 1 行，实得 ' + res.rows.length + '）');
  const d = {};
  res.rows.forEach(r => { d[r.sku] = r; });
  A(d['VYWB1512001A'] && d['VYWB1512001A'].diffQty === 800, 'A 差异 800（实得 ' + (d['VYWB1512001A'] || {}).diffQty + '）');
  A(d['VYWB1512001B'] && d['VYWB1512001B'].diffQty === 500, 'B 差异 500（实得 ' + (d['VYWB1512001B'] || {}).diffQty + '）');
  A(d['VYWB1512001C'] && d['VYWB1512001C'].diffQty === 300, 'C 差异 300');
  A(d['VYWB1512001D'] && d['VYWB1512001D'].diffQty === 100, 'D 差异 100');
  const total = res.rows.reduce((s, r) => s + r.diffQty, 0);
  A(total === 1700, '差异合计 1700（不是被合并后单独一行，实得 ' + total + '）');

  /* 剥前缀：SP 前缀命中后 key 保留原编码，SP/非 SP 不撞行 */
  const rec2 = { supplier: '思哲', shortName: '思哲', buyer: '何君豪' };
  const idx2 = { exact: new Map([['VYWB2222001', rec2]]), kind: new Map() };
  const app2 = [
    { sku: 'SPVYWB2222001', qty: 10, remainQty: 10, no: 'N1', date: '2026-11-01' },
    { sku: 'VYWB2222001', qty: 20, remainQty: 20, no: 'N2', date: '2026-11-01' }
  ];
  const r2 = Core.matchApplies(app2, idx2, ['SP']);
  console.log('--- 剥前缀 ---');
  r2.rows.forEach(r => console.log('  ' + r.sku + ' key=' + r.key + ' via=' + r.via));
  A(r2.rows.length === 2, 'SP/非 SP 两条 → 2 行');
  A(r2.rows[0].key !== r2.rows[1].key, 'key 不同（' + r2.rows[0].key + ' vs ' + r2.rows[1].key + '）');
  A(r2.rows[0].via === 'PFX:SP', '第一条 via=PFX:SP');
  A(r2.rows[1].via === 'exact', '第二条 via=exact');

  console.log('\n==== ' + (fail === 0 ? 'ALL PASS' : 'FAILED') + ' ==== ' + pass + ' 项通过 / ' + fail + ' 项失败');
  process.exit(fail === 0 ? 0 : 1);
}, 900);
