const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: () => () => Promise.resolve({ ok: true }) }) };
  },
});
const w = dom.window;
const ev = (type, dt) => { const e = new w.Event(type, { bubbles: true, cancelable: true }); if (dt) e.dataTransfer = dt; return e; };
(async () => {
  await new Promise(r => setTimeout(r, 200));
  const tabs = () => [...w.document.querySelectorAll('.rp-tab[data-rp]')];
  console.log('初始顺序:', tabs().map(t => t.dataset.rp).join(','));
  const dt = { effectAllowed: '', setData() {} };
  tabs()[0].dispatchEvent(ev('dragstart', dt));      // 拖 aux
  tabs()[3].dispatchEvent(ev('dragover', dt));
  tabs()[3].dispatchEvent(ev('drop', dt));           // 放到 todo
  await new Promise(r => setTimeout(r, 50));
  console.log('拖 aux→todo 后:', tabs().map(t => t.dataset.rp).join(','));
  // 右键菜单
  w.tabMoveMenu('aux', 100, 100);
  console.log('右键菜单:', [...w.document.querySelectorAll('#tabMenu button')].map(b => b.textContent).join(' | '));
  // 点「右移」
  [...w.document.querySelectorAll('#tabMenu button')][1].click();
  await new Promise(r => setTimeout(r, 50));
  console.log('aux 右移后:', tabs().map(t => t.dataset.rp).join(','));
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
