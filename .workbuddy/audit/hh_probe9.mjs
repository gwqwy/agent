const PORT = 9333;
const URL = process.argv[2];
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function pickTarget() {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch('http://127.0.0.1:' + PORT + '/json/list'); const l = await r.json();
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
function send(m, p) { const mid = ++id; return new Promise(r => { pending.set(mid, r); ws.send(JSON.stringify({ id: mid, method: m, params: p || {} })); }); }
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result && r.result.exceptionDetails) return 'ERR: ' + ((r.result.exceptionDetails.exception||{}).description || 'x');
  return r.result && r.result.result ? r.result.result.value : null;
}
async function click(x, y) {
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1180, height: 780, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: URL });
await sleep(2500);
const out = {};
await ev("switchPanel('ws')");
await sleep(800);
out.step1_root = await ev("JSON.stringify({crumb:$('wsCrumb').textContent, rows:document.querySelectorAll('#wsTreePane .tree-row').length, paneText:$('wsTreePane').textContent.slice(0,120)})");
const d = JSON.parse(await ev("JSON.stringify((() => { var rows=[...document.querySelectorAll('#wsTreePane .tree-row')]; var dir=rows.find(x=>x.textContent.includes('📁')); if(!dir) return {error:'no dir'}; var q=dir.getBoundingClientRect(); return {text:dir.textContent.trim(), cx:Math.round(q.left+q.width/2), cy:Math.round(q.top+q.height/2)}; })())"));
out.clickedDir = d;
if (typeof d.cx === 'number') { await click(d.cx, d.cy); await sleep(900); }
out.step2_afterRealClick = await ev("JSON.stringify({crumb:$('wsCrumb').textContent, rows:document.querySelectorAll('#wsTreePane .tree-row').length, paneText:$('wsTreePane').textContent.slice(0,200)})");
out.step3_afterJsClick = await ev("(async () => { var rows=[...document.querySelectorAll('#wsTreePane .tree-row')]; if(!rows.length) return 'no rows'; rows[0].click(); await new Promise(r=>setTimeout(r,800)); return JSON.stringify({crumb:$('wsCrumb').textContent, rows:document.querySelectorAll('#wsTreePane .tree-row').length, paneText:$('wsTreePane').textContent.slice(0,160)}); })()");
out.errors = await ev("JSON.stringify(window.__jsErrors||[])");
console.log(JSON.stringify(out, null, 1));
ws.close();
