/* 云端不可达的两种真实形态，都必须优雅回退：
 *   A) 服务端 403 {error:'access_denied'}  —— Node / 非浏览器环境
 *   B) 浏览器跨域被拦 → TypeError: Failed to fetch —— GitHub Pages 上实际就是这种
 * 期望：不崩、退回本机发布件（BUNDLED_MAP）、亮提示条、保存时明确「未上传云端」
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

function boot(mode) {
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', resources: undefined,
    url: 'https://yikeqingsongguo.github.io/HY.supply-chain-management/console/index.html',
    beforeParse(w) {
      w.fetch = (url, init = {}) => {
        if (mode === 'cors') return Promise.reject(new TypeError('Failed to fetch'));
        const h = new Headers(init.headers || {});
        h.set('Origin', 'https://yikeqingsongguo.github.io');
        return globalThis.fetch(url, { ...init, headers: h });
      };
      w.Headers = globalThis.Headers;
      w.AbortController = globalThis.AbortController;
      w.scrollTo = () => {};
      w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
      w.eval(sdkSrc);
    }
  });
  return dom;
}

async function scenario(mode, label) {
  console.log('\n--- ' + label + ' ---');
  const dom = boot(mode);
  const w = dom.window;
  const t = w.__test, st = t.state();
  /* SDK 对失败请求会重试几轮，等它把回退走完 */
  for (let i = 0; i < 80 && (!st.mapping || !st.mapping.length); i++) await sleep(250);

  A(st.cloudBlocked === true, '[' + label + '] 识别为云端不可达');
  A(st.cloudOK === false, '[' + label + '] cloudOK = false');
  A(st.mapping.length > 1000, '[' + label + '] 退回发布映射：' + st.mapping.length + ' 条（不是 5 条 DEMO）');
  A(!(st.mapping.length === 5 && st.mapping[0] && st.mapping[0].sku === 'SKU-A1001'), '[' + label + '] 未落入 DEMO_MAP');

  const banner = w.document.getElementById('cloudBanner');
  A(banner && !banner.classList.contains('hidden'), '[' + label + '] 提示条已显示');
  A(/连不上云数据库/.test(banner ? banner.textContent : ''), '[' + label + '] 提示条文案说明云端不可达');
  const link = w.document.getElementById('cloudBannerLink');
  A(link && /supply-console\.app\.workbuddy\.host/.test(link.href), '[' + label + '] 提示条带云端管理台链接');
  const syncTxt = w.document.getElementById('syncTxt').textContent;
  A(/云端不可达/.test(syncTxt), '[' + label + '] 状态条：' + syncTxt);

  st.mapping[0].buyer = '测试采购员Z';
  st.mapping[0]._dirty = true;
  await t.saveMapping(true);
  await sleep(300);
  const toastTxt = w.document.getElementById('toast').textContent;
  A(/未上传云端/.test(toastTxt), '[' + label + '] 保存提示含「未上传云端」');
  A(!st.mapping[0]._dirty, '[' + label + '] 本地改动已落盘');
  w.close();
}

(async () => {
  await scenario('server', '服务端 403');
  await scenario('cors', '浏览器跨域拦截');
  console.log('\n==== ' + (fail === 0 ? 'ALL PASS' : 'FAILED') + ' ==== ' + pass + ' 通过 / ' + fail + ' 失败');
  process.exit(fail === 0 ? 0 : 1);
})();
