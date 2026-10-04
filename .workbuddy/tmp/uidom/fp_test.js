const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const prev = { ok: true, name: 'demo.py', rel: 'demo.py', size: 1234, mtime: Date.now() / 1000,
  ext: '.py', kind: 'code', text: 'def f(x):\n    # 注释\n    return "hi" + str(1)\n', lines: 3 };
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: (t, name) => (...args) => {
      if (name === 'file_preview') return Promise.resolve(prev);
      if (name === 'ws_tree') return Promise.resolve({ ok: true, entries: [
        { name: 'demo.py', dir: false, size: 1234 }, { name: 'sub', dir: true, size: 0 }] });
      return Promise.resolve({ ok: true });
    } }) };
  },
});
const w = dom.window;
(async () => {
  w.dispatchEvent(new w.Event('pywebviewready'));
  await new Promise(r => setTimeout(r, 200));
  await w.loadWsTree();
  await new Promise(r => setTimeout(r, 50));
  const rows = w.document.querySelectorAll('.tree-row');
  console.log('树行数:', rows.length);
  rows[0].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  await new Promise(r => setTimeout(r, 80));
  const box = w.document.getElementById('filePreview');
  console.log('预览打开:', box.classList.contains('open'));
  console.log('预览HTML:', box.innerHTML.slice(0, 300));
  console.log('元信息:', box.querySelector('.fp-meta').textContent);
  console.log('着色片段:', (box.querySelector('.fp-code').innerHTML.match(/class="c-(com|str|num|kw)"/g) || []).join(','));
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
