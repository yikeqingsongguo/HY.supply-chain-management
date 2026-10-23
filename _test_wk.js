/* 待下单汇总 v1.6.5 冒烟测试（jsdom）：
 * 1) 采购员汇总行点击下钻 → 弹出「采购员详情」小窗（不再向下展开），可关闭
 * 2) 供应商行点击下钻 → 弹出「供应商详情」小窗，导出明细生成 .xlsx（Blob 有效）
 * 3) 补录填写采购员 → 待下单采购员统计同步（未填写归位）
 * 4) 整体导出 Excel 按钮 → 双 sheet .xlsx
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
  // jsdom 不实现 innerText，自动载入提示里的 s.innerText.trim() 会报错，忽略
  if (/reading 'trim'/.test(msg)) return;
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

  // 下钻（未填写）→ 弹出小窗
  unfilled.click();
  await sleep(200);
  let mask = w.document.querySelector('body > .mask');
  let dlgTitle = mask ? (mask.querySelector('.dlg-hd') || {}).textContent : '';
  A(!!mask && /采购员详情/.test(dlgTitle), '点击采购员行弹出「采购员详情」小窗（' + dlgTitle + '）');
  A(!!mask && /（未填写）/.test(dlgTitle), '小窗标题含采购员名（未填写）');
  const dlgTable = mask ? mask.querySelector('.dlg-bd table') : null;
  A(!!dlgTable && dlgTable.querySelectorAll('tbody tr').length > 0, '小窗含明细表（' + (dlgTable ? dlgTable.querySelectorAll('tbody tr').length : 0) + ' 行）');
  A(!!dlgTable && /申请单号/.test(dlgTable.innerHTML) && /规格型号/.test(dlgTable.innerHTML) && /供应商/.test(dlgTable.innerHTML), '小窗列头含 申请单号/规格型号/供应商');
  A(mask.querySelectorAll('.dlg-bd th button.wk-fil').length === 7, '采购员详情各列均有筛选按钮（' + mask.querySelectorAll('.dlg-bd th button.wk-fil').length + ' 个）');
  const specTd = mask.querySelector('.dlg-bd td.spec-cell');
  A(!!specTd && specTd.textContent.length <= 6 && !!specTd.getAttribute('title'), '规格型号仅显示前 5 字符且悬停有全文（' + (specTd ? specTd.textContent : '') + '）');
  // 小窗按钮：导出明细 + 关闭
  let dlgBtns = mask ? Array.prototype.slice.call(mask.querySelectorAll('.dlg-ft button')).map(b => b.textContent) : [];
  A(dlgBtns.indexOf('导出明细') >= 0 && dlgBtns.indexOf('关闭') >= 0, '小窗按钮含 导出明细/关闭');
  // 关闭
  const closeBtn = mask.querySelector('.dlg-ft button:last-child');
  closeBtn.click();
  await sleep(100);
  A(!w.document.querySelector('body > .mask'), '点「关闭」可收起小窗');

  // 供应商行下钻 → 弹出小窗 + 导出明细
  const supRow = w.document.querySelector('#wkA tr.wk-row[data-short], #wkB tr.wk-row[data-short]');
  A(!!supRow, '供应商行可点击下钻');
  supRow.click();
  await sleep(200);
  mask = w.document.querySelector('body > .mask');
  dlgTitle = mask ? (mask.querySelector('.dlg-hd') || {}).textContent : '';
  A(!!mask && /供应商详情/.test(dlgTitle), '点击供应商行弹出「供应商详情」小窗（' + dlgTitle + '）');
  // 导出明细
  w.__lastBlob = null;
  const expBtn = Array.prototype.slice.call(mask.querySelectorAll('.dlg-ft button')).find(b => b.textContent === '导出明细');
  expBtn.click();
  await sleep(400);
  A(!!w.__lastBlob && w.__lastBlob.size > 2000, '小窗「导出明细」生成有效 .xlsx Blob（' + (w.__lastBlob ? w.__lastBlob.size : 0) + ' bytes）');
  if (w.__lastBlob) {
    const buf = Buffer.from(await w.__lastBlob.arrayBuffer());
    A(buf.slice(0, 2).toString() === 'PK', '导出 Blob 为 zip 签名');
    const s = buf.toString('latin1');
    A(s.indexOf('xl/worksheets/sheet1.xml') >= 0 && s.indexOf('xl/worksheets/sheet2.xml') < 0, '明细导出为单 sheet（' + 'sheet1 only' + '）');
    // 用 SheetJS 解析回来校验列头（申请单号在前，与示例一致）
    const XL = require(path.join(HERE, 'vendor', 'xlsx.full.min.js'));
    const wb = XL.read(buf, { type: 'buffer' });
    const aoa = XL.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { header: 1, raw: false });
    A(aoa[0] && aoa[0][0] === '申请单号', '导出列头第一列为「申请单号」→ ' + ((aoa[0] || []).join(' / ')));
    A(aoa[0] && aoa[0].length === 10, '导出 10 列（' + (aoa[0] || []).length + ' 列）');
    A(aoa.length > 1, '导出含数据行（' + (aoa.length - 1) + ' 行）');
  }
  // 关闭
  mask.querySelector('.dlg-ft button:last-child').click();
  await sleep(100);
  A(!w.document.querySelector('body > .mask'), '供应商小窗可关闭');

  // 补录采购员 → 统计同步
  const before = (bs.querySelector('tr[data-buyer="（未填写）"]') || {}).outerHTML || '';
  const qtyBefore = (before.match(/<\/i><\/div><span class="wk-num">|text-align:right">([\d,.]+)/) || [])[1];
  w.__wkOnMappingSaved('VYGJZ011203', '', '', '梁成杰');
  await sleep(300);
  const html2 = bs.innerHTML;
  A(/data-buyer="梁成杰"/.test(html2), '补录采购员「梁成杰」后汇总出现该采购员行');
  const localMap = JSON.parse(w.localStorage.getItem('wk_sup_map_v1') || '{}');
  A(localMap['VYGJZ011203'] && localMap['VYGJZ011203'].buyer === '梁成杰', 'localStorage wk_sup_map_v1 已记录 buyer');

  // 导出 Excel（多分表）
  const btn = w.document.getElementById('wkExportExcel');
  btn.click();
  await sleep(600);
  A(!!w.__lastBlob && w.__lastBlob.size > 5000, '点击导出生成有效 .xlsx Blob（' + (w.__lastBlob ? w.__lastBlob.size : 0) + ' bytes）');
  if (w.__lastBlob) {
    const buf = Buffer.from(await w.__lastBlob.arrayBuffer());
    A(buf.slice(0, 2).toString() === 'PK', 'Blob 为 zip 签名（.xlsx 容器正确）');
    const XL = require(path.join(HERE, 'vendor', 'xlsx.full.min.js'));
    const wb = XL.read(buf, { type: 'buffer' });
    const want = ['下单明细', '供应商汇总', 'SKU映射表', '历史未下单明细'];
    A(want.every(n => wb.SheetNames.includes(n)), '包含 4 个分表（' + wb.SheetNames.join(' / ') + '）');
    const a1 = XL.utils.sheet_to_json(wb.Sheets['下单明细'], { header: 1, raw: false });
    A(a1[0][0] === '申请单号' && a1[0][4] === '创建日期' && a1[0][9] === '备注', '下单明细列序：申请单号→…→创建日期→…→备注');
    const a3 = XL.utils.sheet_to_json(wb.Sheets['SKU映射表'], { header: 1, raw: false });
    A(a3.length > 100, 'SKU映射表含数据（' + (a3.length - 1) + ' 行）');
    const a4 = XL.utils.sheet_to_json(wb.Sheets['历史未下单明细'], { header: 1, raw: false });
    A(a4[0][0] === '申请单号' && a4[0].length === 11, '历史未下单明细 11 列（' + (a4.length - 1) + ' 行）');
  }

  // 多分表导出后重新载入数据，供后续小窗用例
  // 只读 / 口令解锁
  const eb0 = w.document.getElementById('btnEditMode');
  A(!!eb0 && /只读模式/.test(eb0.textContent), '默认只读模式（编辑按钮显示「只读模式」）');
  A(!!w.document.querySelector('#tab-map .ro-bar'), '映射表页显示只读提示条');
  eb0.click();
  await sleep(150);
  const pwd = w.document.getElementById('editPwd');
  A(!!pwd, '点击后弹出管理员口令框');
  pwd.value = 'wrong';
  Array.from(w.document.querySelectorAll('.dlg-ft button')).find(b => /解锁/.test(b.textContent)).click();
  await sleep(150);
  A(/只读模式/.test(eb0.textContent), '口令错误仍保持只读');
  pwd.value = 'hy2026';
  Array.from(w.document.querySelectorAll('.dlg-ft button')).find(b => /解锁/.test(b.textContent)).click();
  await sleep(250);
  A(/退出编辑/.test(eb0.textContent), '口令正确后进入编辑模式');
  A(!w.document.querySelector('#tab-map .ro-bar'), '解锁后只读提示条消失');

  // 语法/错误
  A(errors.length === 0, '无致命 JS 错误' + (errors.length ? ' → ' + errors.slice(0, 3).join(' | ') : ''));
  process.exit(process.exitCode || 0);
})().catch(e => { console.log('FAIL: 测试异常', e && e.stack || e); process.exit(1); });
