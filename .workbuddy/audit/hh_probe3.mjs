const PORT = 9333;
const URL = process.argv[2];
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function pickTarget() {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/list`); const l = await r.json();
      const p = l.find(t => t.type === 'page' && t.webSocketDebuggerUrl); if (p) return p; } catch {}
    await sleep(250);
  }
  throw new Error('devtools 不可达');
}
const page = await pickTarget();
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 0; const pending = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
function send(method, params = {}) { const mid = ++id; return new Promise(r => { pending.set(mid, r); ws.send(JSON.stringify({ id: mid, method, params })); }); }
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result && r.result.exceptionDetails) return { __error: JSON.stringify(r.result.exceptionDetails).slice(0, 300) };
  return r.result && r.result.result ? r.result.result.value : null;
}
async function click(x, y) {
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}
async function wheel(x, y, dy) {
  await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x, y, deltaX: 0, deltaY: dy });
}
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1180, height: 780, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: URL });
await sleep(2500);
const out = {};
await ev("switchPanel('ws')");
await sleep(900);

out.geom = await ev(`JSON.stringify((() => {
  const pane = $('wsTreePane');
  const p = pane.getBoundingClientRect();
  const rows = [...pane.querySelectorAll('.tree-row')];
  const last = rows[rows.length-1].getBoundingClientRect();
  return { paneClient: pane.clientHeight, paneScrollH: pane.scrollHeight,
           scrollTop: pane.scrollTop, canScroll: pane.scrollHeight > pane.clientHeight,
           rowCount: rows.length,
           paneTop: Math.round(p.top), paneBottom: Math.round(p.bottom),
           lastRowTop: Math.round(last.top), lastRowBottom: Math.round(last.bottom) };
})())`);

// A) 不滚动，直接用真实鼠标点击"折叠线以下"的行
out.belowFold = await ev(`JSON.stringify((() => {
  const pane = $('wsTreePane');
  const p = pane.getBoundingClientRect();
  const rows = [...pane.querySelectorAll('.tree-row')];
  const hidden = rows.find(r => r.getBoundingClientRect().top > p.bottom);
  if (!hidden) return { error: '没有超出可视区的行' };
  const b = hidden.getBoundingClientRect();
  const cy = Math.round((Math.max(b.top, p.top) + Math.min(b.bottom, p.bottom)) / 2);
  const hit = document.elementFromPoint(b.left + 5, b.bottom - 2);
  return { target: hidden.textContent.trim(), rowTop: Math.round(b.top), rowBottom: Math.round(b.bottom),
           paneBottom: Math.round(p.bottom), hitTag: hit ? hit.tagName + '.' + hit.className : null };
})())`);

// 真实鼠标滚轮在面板上滚动
const g = JSON.parse(out.geom);
await wheel(1000, 400, 600);
await sleep(500);
out.afterWheel = await ev("JSON.stringify({scrollTop:$('wsTreePane').scrollTop})");

// 直接设 scrollTop 到底
out.afterSetTop = await ev(`JSON.stringify((() => { const p=$('wsTreePane'); p.scrollTop=1e6;
  return {scrollTop:p.scrollTop, max:p.scrollHeight-p.clientHeight}; })())`);
await sleep(300);

// B) 滚动后真实鼠标点击此时可见的目录行
out.visibleDirNow = await ev(`JSON.stringify((() => {
  const pane=$('wsTreePane'); const p=pane.getBoundingClientRect();
  const rows=[...pane.querySelectorAll('.tree-row')];
  const dir=rows.find(r=>{const b=r.getBoundingClientRect(); return r.textContent.includes('📁') && b.top>=p.top && b.bottom<=p.bottom;});
  if(!dir) return {error:'可视区内没有目录行'};
  const b=dir.getBoundingClientRect();
  return {text:dir.textContent.trim(), cx:Math.round(b.left+b.width/2), cy:Math.round(b.top+b.height/2)};
})())`);
const v = JSON.parse(out.visibleDirNow);
if (typeof v.cx === 'number') {
  await click(v.cx, v.cy);
  await sleep(900);
  out.afterScrollClick = await ev("JSON.stringify({crumb:$('wsCrumb').textContent,rows:document.querySelectorAll('#wsTreePane .tree-row').length})");
}

// C) 点击「⬆ 上级」按钮（真实鼠标）
out.upBtn = await ev(`JSON.stringify((() => { const b=document.querySelector('#rp-ws .ws-nav .mini-btn'); const r=b.getBoundingClientRect();
  return {text:b.textContent.trim(), cx:Math.round(r.left+r.width/2), cy:Math.round(r.top+r.height/2)}; })())`);
const u = JSON.parse(out.upBtn);
await click(u.cx, u.cy);
await sleep(800);
out.afterUp = await ev("JSON.stringify({crumb:$('wsCrumb').textContent,rows:document.querySelectorAll('#wsTreePane .tree-row').length})");

out.errors = await ev("JSON.stringify(window.__jsErrors||[])");
console.log(JSON.stringify(out, null, 1));
ws.close();
