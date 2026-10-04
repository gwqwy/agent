const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const calls = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: (t, name) => (...args) => {
      if (name === 'set_session_order') calls.push(['set_session_order', ...args]);
      if (name === 'sessions') return Promise.resolve({ ok: true, current: 's1', sessions: [
        { id: 's1', name: '会话一', ws: 'w1', updated: 100, pinned: false, done: false, order: 0 },
        { id: 's2', name: '会话二', ws: 'w1', updated: 90, pinned: false, done: false, order: 1 },
        { id: 's3', name: '会话三', ws: 'w1', updated: 80, pinned: false, done: false, order: 2 },
      ] });
      if (name === 'workspaces') return Promise.resolve({ ok: true, current: 'w1',
        workspaces: [{ id: 'w1', name: '测试', path: 'C:/ws' }] });
      return Promise.resolve({ ok: true });
    } }) };
  },
});
const w = dom.window;
(async () => {
  w.dispatchEvent(new w.Event('pywebviewready'));
  await new Promise(r => setTimeout(r, 300));
  const rows = () => [...w.document.querySelectorAll('.s-row')];
  console.log('行数:', rows().length, rows().map(r => r.__sess.id).join(','));
  // 桩 elementFromPoint：假装鼠标在第 3 行上
  const target = rows()[2];
  w.document.elementFromPoint = () => target;
  rows()[0].dispatchEvent(new w.MouseEvent('mousedown', { button: 0, clientY: 100, bubbles: true }));
  w.document.dispatchEvent(new w.MouseEvent('mousemove', { clientY: 130, bubbles: true }));
  console.log('dragging:', rows()[0].className.includes('dragging'),
              '| dragover:', target.className.includes('dragover'));
  w.document.dispatchEvent(new w.MouseEvent('mouseup', { clientY: 130, bubbles: true }));
  await new Promise(r => setTimeout(r, 150));
  console.log('set_session_order:', JSON.stringify(calls));
  console.log('重排后行序:', rows().map(r => r.__sess.id).join(','));
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
