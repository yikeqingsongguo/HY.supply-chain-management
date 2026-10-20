/* 补录页改动冒烟测试（jsdom）：
 * 1) 页面无致命 JS 错误
 * 2) 补录表有「款号」列 + 「同款号自动带出」开关
 * 3) 填一行 → 同款号 SKU 整组落库（SPU 联动），且行立即从列表消失
 * 4) 重复填写 → 弹冲突确认 → 更新原行，不插重复行
 * 5) localStorage 持久化包含补录行
 */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const DIR = path.join(__dirname, 'console');
const html = fs.readFileSync(path.join(DIR, 'index.html'), 'utf8');

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => {
  const msg = String(e && e.message || e);
  if (/DragEvent|DataTransfer|not implemented/i.test(msg)) return; // jsdom 已知缺失，忽略
  errors.push('jsdomError: ' + msg);
});
vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'http://localhost/console/index.html',
  virtualConsole: vc,
  beforeParse(w) {
    w.fetch = function (u) {
      const name = String(u).split('/').pop().split('?')[0];
      const p = path.join(DIR, name);
      if (!fs.existsSync(p)) return Promise.resolve({ ok: false, status: 404 });
      const buf = fs.readFileSync(p);
      return Promise.resolve(new Response(buf, { status: 200, headers: { 'Content-Type': 'application/json' } }));
    };
    w.DataTransfer = function () { this.items = { add() {} }; this.files = []; };
    w.DragEvent = class extends w.Event {
      constructor(t, o) { super(t, o); this.dataTransfer = (o && o.dataTransfer) || null; }
    };
  }
});

const w = dom.window;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const A = (c, msg) => { if (!c) { console.log('FAIL:', msg); process.exitCode = 1; } else console.log('PASS:', msg); };
const norm = s => String(s || '').trim().toUpperCase();

function fakeRow(doc, sku, spu, shortVal) {
  const tr = doc.createElement('tr');
  tr.innerHTML = '<td class="ctr"><input type="checkbox" checked class="unmatch-cb"></td>'
    + '<td class="ctr"><span class="unmatch-spu-cell grp">' + spu + '</span></td>'
    + '<td class="sku-big mono">' + sku + '</td>'
    + '<td><input class="inp-cell" data-k="' + sku + '" data-f="short" value="' + (shortVal || '') + '"></td>'
    + '<td><input class="inp-cell" data-k="' + sku + '" data-f="supplier"></td>'
    + '<td><input class="inp-cell" data-k="' + sku + '" data-f="buyer"></td>'
    + '<td><input class="inp-cell" data-k="' + sku + '" data-f="note"></td>';
  return tr;
}

(async () => {
  // 等 boot + loadWk
  let tries = 0;
  while (tries++ < 50 && !w.__wkPendingSkus) await sleep(100);
  A(!!w.__wkPendingSkus, 'weekly.json 加载且 __wkPendingSkus 就绪（' + ((w.__wkPendingSkus || []).length) + ' 条）');

  // 切到补录 Tab
  const sb = w.document.querySelector('.sb-item[data-tab="unmatch"]');
  A(!!sb, '侧边栏存在未匹配补录入口');
  sb.click();
  await sleep(300);

  const tbl = w.document.getElementById('unmatchTable');
  A(!!tbl, '补录表已渲染');
  A(tbl && /款号/.test(tbl.querySelector('thead').innerHTML), '表头含「款号」列');
  const spuCb0 = w.document.getElementById('unmatchBySpu');
  A(!!spuCb0 && spuCb0.checked, '存在「同款号自动带出」开关且默认勾选');

  const keys = Array.prototype.map.call(w.document.querySelectorAll('#unmatchTable input[data-f="short"]'), i => i.dataset.k);
  A(keys.indexOf('VYWB6115LKP1M') >= 0 && keys.indexOf('VYWB6115LKP2M') >= 0, '待补录列表包含同款号对 VYWB6115LKP1M / VYWB6115LKP2M');

  const kdCells = Array.prototype.map.call(w.document.querySelectorAll('#unmatchTable .unmatch-spu-cell'), s => s.textContent);
  A(kdCells.filter(x => x === '6115').length >= 2, '款号列正确显示 6115（' + kdCells.join(',') + '）');

  // ① 填第一行 → 整组联动落库并从列表消失
  const st = w.__test.state();
  const inp = w.document.querySelector('#unmatchTable input[data-k="VYWB6115LKP1M"][data-f="short"]');
  inp.value = '战獒';
  w.__test.saveUnmatchRowByKey('VYWB6115LKP1M');
  await sleep(300);

  const rows6115 = st.mapping.filter(m => norm(m.sku) === 'VYWB6115LKP1M' || norm(m.sku) === 'VYWB6115LKP2M');
  A(rows6115.length === 2, 'SPU 联动：两个同款号 SKU 各落 1 行映射（实得 ' + rows6115.length + '）');
  A(rows6115.every(m => m.shortName === '战獒'), '两行简称均为「战獒」(' + rows6115.map(m => m.sku + '=' + m.shortName).join(', ') + ')');

  const keysAfter = Array.prototype.map.call(w.document.querySelectorAll('#unmatchTable input[data-f="short"]'), i => i.dataset.k);
  A(keysAfter.indexOf('VYWB6115LKP1M') < 0 && keysAfter.indexOf('VYWB6115LKP2M') < 0, '保存后整组行立即从补录列表消失');

  // ② 重复填写：模拟行重新出现（陈旧快照回流），同款号另一行已绑「战獒」→ 应弹冲突确认
  const st2m = st.mapping.find(m => norm(m.sku) === 'VYWB6115LKP2M');
  st2m.supplier = '广州市战獒箱包有限公司';   // 模拟已绑定过战獒
  const tb = w.document.querySelector('#unmatchTable tbody');
  tb.appendChild(fakeRow(w.document, 'VYWB6115LKP1M', '6115', '格莱尔'));
  tb.appendChild(fakeRow(w.document, 'VYWB6115LKP2M', '6115', ''));
  w.__test.saveUnmatchRowByKey('VYWB6115LKP1M');
  await sleep(300);

  const dlg = w.document.querySelector('.mask .dlg');
  A(!!dlg, '同款号供应商冲突时弹出确认弹窗');
  if (dlg) {
    const btns = Array.prototype.slice.call(dlg.querySelectorAll('button'));
    const cover = btns.find(b => /全部覆盖/.test(b.textContent));
    const skip = btns.find(b => /跳过冲突行/.test(b.textContent));
    A(!!cover && !!skip, '弹窗含「全部覆盖」/「跳过冲突行」按钮');
    cover.click();
    await sleep(300);
  }
  const cnt1 = st.mapping.filter(m => norm(m.sku) === 'VYWB6115LKP1M').length;
  const updated = st.mapping.find(m => norm(m.sku) === 'VYWB6115LKP1M');
  A(cnt1 === 1, '重复填写只更新原行，不插重复行（共 ' + cnt1 + ' 行）');
  A(updated && updated.shortName === '格莱尔', '重复填写后简称已更新为「格莱尔」');
  const sib = st.mapping.find(m => norm(m.sku) === 'VYWB6115LKP2M');
  A(sib && sib.shortName === '格莱尔', '冲突覆盖后同款号另一行也同步更新为「格莱尔」');

  // ③ localStorage 持久化
  const lsKey = Object.keys(w.localStorage).find(k => /mapping/i.test(k));
  const lsArr = lsKey ? JSON.parse(w.localStorage.getItem(lsKey) || '[]') : [];
  A(lsArr.some(m => norm(m.sku) === 'VYWB6115LKP1M'), 'localStorage（' + lsKey + '）已持久化补录行');

  A(errors.length === 0, '无致命 JS 错误' + (errors.length ? ' → ' + errors.slice(0, 3).join(' | ') : ''));
  process.exit(process.exitCode || 0);
})().catch(e => { console.log('FAIL: 测试异常', e && e.stack || e); process.exit(1); });
