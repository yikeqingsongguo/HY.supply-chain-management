/* 域名受限场景：云端按发布域名校验来源，GitHub Pages 域名会被 403
 * 期望：不崩、自动退回本机发布件（BUNDLED_MAP）、亮提示条、保存时明确说「未上传云端」
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const DIR = __dirname;
const html = fs.readFileSync(path.join(DIR, 'console/index.html'), 'utf8');
const sdkSrc = fs.readFileSync(path.join(DIR, 'vendor/workbuddy-cloud.js'), 'utf8');

let pass = 0, fail = 0;
const A = (ok, m) => { if (ok) { pass++; console.log('PASS: ' + m); } else { fail++; console.log('FAIL: ' + m); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', resources: undefined,
    url: 'https://yikeqingsongguo.github.io/HY.supply-chain-management/console/index.html',
    beforeParse(w) {
      w.fetch = (url, init = {}) => {
        const h = new Headers(init.headers || {});
        h.set('Origin', 'https://yikeqingsongguo.github.io');   // 模拟 Pages 域名
        return globalThis.fetch(url, { ...init, headers: h });
      };
      w.Headers = globalThis.Headers;
      w.AbortController = globalThis.AbortController;
      w.scrollTo = () => {};
      w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
      w.eval(sdkSrc);
    }
  });
  const w = dom.window;
  await sleep(2500);
  const t = w.__test, st = t.state();

  A(st.cloudBlocked === true, '识别出域名受限（cloudBlocked = true）');
  A(st.cloudOK === false, 'cloudOK = false');
  A(st.mapping.length > 1000, '已退回本机发布映射：' + st.mapping.length + ' 条（不是 DEMO）');
  const banner = w.document.getElementById('cloudBanner');
  A(banner && !banner.classList.contains('hidden'), '提示条已显示');
  A(/不在云端允许列表/.test(banner ? banner.textContent : ''), '提示条文案说明域名受限');
  const link = w.document.getElementById('cloudBannerLink');
  A(link && /supply-console\.app\.workbuddy\.host/.test(link.href), '提示条带云端管理台链接');
  const syncTxt = w.document.getElementById('syncTxt').textContent;
  A(/域名受限/.test(syncTxt), '状态条显示「域名受限」：' + syncTxt);

  /* 保存：应走本机路径，且明确告知未上传云端 */
  st.mapping[0].buyer = '测试采购员Z';
  st.mapping[0]._dirty = true;
  await t.saveMapping(true);
  await sleep(300);
  const toastTxt = w.document.getElementById('toast').textContent;
  A(/未上传云端/.test(toastTxt), '保存提示明确「未上传云端」：' + toastTxt.slice(0, 60));
  A(!st.mapping[0]._dirty, '本地改动已落盘（脏标记清除）');

  console.log('\n==== ' + (fail === 0 ? 'ALL PASS' : 'FAILED') + ' ==== ' + pass + ' 通过 / ' + fail + ' 失败');
  process.exit(fail === 0 ? 0 : 1);
})();
