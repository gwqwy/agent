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
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: URL });
await sleep(3000);
const out = {};
out.view = await ev(`JSON.stringify({innerW:innerWidth, innerH:innerHeight, dpr:devicePixelRatio,
  scrollY:scrollY, docScrollTop:document.scrollingElement.scrollTop,
  htmlH:document.documentElement.scrollHeight, bodyH:document.body.scrollHeight,
  compat:document.compatMode, visualH:window.visualViewport&&Math.round(window.visualViewport.height)})`);
await ev("switchPanel('ws')");
await sleep(900);
out.boxes = await ev(`JSON.stringify((() => {
  const g=(s)=>{const el=document.querySelector(s); if(!el) return null; const r=el.getBoundingClientRect();
    return {top:Math.round(r.top),bottom:Math.round(r.bottom),h:Math.round(r.height)};};
  return {app:g('.app'), asideRight:g('aside.right'), rpWs:g('#rp-ws'), pane:g('#wsTreePane'),
          main:g('main'), log:g('#log'), composer:g('.composer-wrap'), hero:g('#hero'),
          rows:document.querySelectorAll('#wsTreePane .tree-row').length,
          crumb:$('wsCrumb').textContent};
})())`);
out.errors = await ev("JSON.stringify(window.__jsErrors||[])");
console.log(JSON.stringify(out, null, 1));
ws.close();
