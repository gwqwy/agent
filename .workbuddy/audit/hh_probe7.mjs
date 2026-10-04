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
async function setVp(w, h) { await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false }); await sleep(400); }
await send('Runtime.enable'); await send('Page.enable');

const VPS = [[500,450],[620,450],[924,581],[1180,741]];
const out = {};
for (const [w,h] of VPS) {
  await setVp(w, h);
  await send('Page.navigate', { url: URL });
  await sleep(2200);
  const key = `${w}x${h}`;
  const r = {};
  r.before = await ev(`JSON.stringify({innerW:innerWidth,innerH:innerHeight,scrollY:Math.round(scrollY),
    htmlH:document.documentElement.scrollHeight, heroH:Math.round($('hero').getBoundingClientRect().height),
    heroDisplay:getComputedStyle($('hero')).display, mainW:Math.round($('main').getBoundingClientRect().width),
    asideRightTop:Math.round(document.querySelector('aside.right').getBoundingClientRect().top),
    asideRightLeft:Math.round(document.querySelector('aside.right').getBoundingClientRect().left),
    asideRightRight:Math.round(document.querySelector('aside.right').getBoundingClientRect().right)})`);
  await ev("switchPanel('ws')");
  await sleep(700);
  // 真实点击第一个目录行（若其中心在视口内）
  const d = JSON.parse(await ev(`JSON.stringify((() => { const rows=[...document.querySelectorAll('#wsTreePane .tree-row')]; const dir=rows.find(x=>x.textContent.includes('📁'));
    if(!dir) return {error:'no dir'}; const q=dir.getBoundingClientRect();
    return {text:dir.textContent.trim(), cx:Math.round(q.left+q.width/2), cy:Math.round(q.top+q.height/2),
            hit:(document.elementFromPoint(q.left+q.width/2,q.top+q.height/2)||{}).className||null}; })())`));
  r.dirRow = d;
  if (typeof d.cx === 'number' && d.cy > 0 && d.cy < h && d.cx > 0 && d.cx < w) { await click(d.cx, d.cy); await sleep(700); }
  r.afterClickWithoutScrollFix = await ev("JSON.stringify({crumb:$('wsCrumb').textContent, rows:document.querySelectorAll('#wsTreePane .tree-row').length})");
  // 用户/脚本把页面滚回顶部
  await ev("window.scrollTo(0,0)");
  await sleep(400);
  r.afterScrollToTop = await ev("JSON.stringify({scrollY:Math.round(scrollY), asideRightTop:Math.round(document.querySelector('aside.right').getBoundingClientRect().top)})");
  const d2 = JSON.parse(await ev(`JSON.stringify((() => { const rows=[...document.querySelectorAll('#wsTreePane .tree-row')]; const dir=rows.find(x=>x.textContent.includes('📁'));
    if(!dir) return {error:'no dir'}; const q=dir.getBoundingClientRect();
    return {text:dir.textContent.trim(), cx:Math.round(q.left+q.width/2), cy:Math.round(q.top+q.height/2)}; })())`));
  if (typeof d2.cx === 'number' && d2.cy > 0 && d2.cy < h && d2.cx > 0 && d2.cx < w) { await click(d2.cx, d2.cy); await sleep(800); }
  r.afterClickAndScrollFix = await ev("JSON.stringify({crumb:$('wsCrumb').textContent, rows:document.querySelectorAll('#wsTreePane .tree-row').length})");
  out[key] = r;
}
out.errors = await ev("JSON.stringify(window.__jsErrors||[])");
console.log(JSON.stringify(out, null, 1));
ws.close();
