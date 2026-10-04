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
  if (r.result && r.result.exceptionDetails) return 'ERR: ' + ((r.result.exceptionDetails.exception||{}).description || 'unknown');
  return r.result && r.result.result ? r.result.result.value : null;
}
const PROBE = "(() => { var hero=$('hero'); var log=$('log'); var cw=document.querySelector('.composer-wrap');"
  + " var ar=document.querySelector('aside.right'); var main=document.querySelector('main');"
  + " return JSON.stringify({innerH:innerHeight, scrollY:Math.round(scrollY), htmlH:document.documentElement.scrollHeight,"
  + " mainW:Math.round(main.getBoundingClientRect().width), heroDisplay:getComputedStyle(hero).display,"
  + " heroH:Math.round(hero.getBoundingClientRect().height), logH:Math.round(log.getBoundingClientRect().height),"
  + " composerH:Math.round(cw.getBoundingClientRect().height),"
  + " asideTop:Math.round(ar.getBoundingClientRect().top), asideRight:Math.round(ar.getBoundingClientRect().right),"
  + " asideLeft:Math.round(ar.getBoundingClientRect().left)}); })()";
await send('Runtime.enable'); await send('Page.enable');
const VPS = [[1164,741],[1164,620],[1164,581],[1164,520],[1164,470],[940,741],[940,620],[940,581],[800,741],[700,741],[660,741],[620,741],[600,741],[500,741]];
const out = [];
for (const vp of VPS) {
  await send('Emulation.setDeviceMetricsOverride', { width: vp[0], height: vp[1], deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL });
  await sleep(1700);
  const r = await ev(PROBE);
  out.push(vp[0] + 'x' + vp[1] + ' -> ' + (typeof r === 'string' ? r : JSON.stringify(r)));
}
out.push('errors: ' + JSON.stringify(await ev('JSON.stringify(window.__jsErrors||[])')));
console.log(out.join('\n'));
ws.close();
