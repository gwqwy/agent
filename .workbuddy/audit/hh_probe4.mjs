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
async function setViewport(w, h) {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await sleep(400);
}
await send('Runtime.enable'); await send('Page.enable');
await setViewport(1180, 780);
await send('Page.navigate', { url: URL });
await sleep(2500);
const out = {};

// 重复 id 扫描
out.dupIds = await ev(`JSON.stringify((() => {
  const seen = {}, dup = [];
  document.querySelectorAll('[id]').forEach(el => { seen[el.id] = (seen[el.id]||0)+1; });
  for (const k in seen) if (seen[k] > 1) dup.push(k + ' x' + seen[k]);
  return dup;
})())`);

async function scenario(w, h, label) {
  const r = {};
  await setViewport(w, h);
  await ev("document.body.classList.remove('panel-hidden'); document.documentElement.dataset.theme='light';");
  // 回到根
  await ev("switchPanel('ws')");
  await sleep(700);
  // 真实鼠标点击「工作区」标签
  const tab = JSON.parse(await ev(`JSON.stringify((() => { const b=[...document.querySelectorAll('.rp-tab')].find(x=>x.dataset.rp==='ws'); const q=b.getBoundingClientRect();
    return {cx:Math.round(q.left+q.width/2), cy:Math.round(q.top+q.height/2), hit:(document.elementFromPoint(q.left+q.width/2,q.top+q.height/2)||{}).textContent}; })())`));
  await click(tab.cx, tab.cy);
  await sleep(700);
  r.tabClick = { tabHit: tab.hit, activeAfterTabClick: await ev("(document.querySelector('.rp-body.active')||{}).id") };
  r.rows = await ev("document.querySelectorAll('#wsTreePane .tree-row').length");
  // 真实点击第一行目录
  const d = JSON.parse(await ev(`JSON.stringify((() => { const rows=[...document.querySelectorAll('#wsTreePane .tree-row')]; const dir=rows.find(x=>x.textContent.includes('📁'));
    if(!dir) return {error:'no dir'}; const q=dir.getBoundingClientRect(); const hit=document.elementFromPoint(q.left+q.width/2,q.top+q.height/2);
    return {text:dir.textContent.trim(), cx:Math.round(q.left+q.width/2), cy:Math.round(q.top+q.height/2), hitIsSelf: hit? (hit===dir||dir.contains(hit)):false}; })())`));
  r.dirRow = d;
  if (typeof d.cx === 'number') { await click(d.cx, d.cy); await sleep(800); }
  r.afterDirClick = await ev("JSON.stringify({crumb:$('wsCrumb').textContent, rows:document.querySelectorAll('#wsTreePane .tree-row').length})");
  r.paneBox = await ev(`JSON.stringify((() => { const p=$('wsTreePane'); const b=p.getBoundingClientRect(); const a=document.querySelector('aside.right').getBoundingClientRect();
    return {paneH:Math.round(b.height), paneTop:Math.round(b.top), paneBottom:Math.round(b.bottom), asideH:Math.round(a.height), asideTop:Math.round(a.top), clientH:p.clientHeight, scrollH:p.scrollHeight}; })())`);
  out[label] = r;
}

await scenario(1180, 780, "vp_1180x780");
await scenario(1180, 621, "vp_1180x621");
await scenario(941, 621, "vp_941x621");
await scenario(1180, 400, "vp_1180x400");

out.errors = await ev("JSON.stringify(window.__jsErrors||[])");
console.log(JSON.stringify(out, null, 1));
ws.close();
