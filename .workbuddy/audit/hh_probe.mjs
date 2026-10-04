const PORT = 9333;
const URL = process.argv[2] || 'http://127.0.0.1:8766/';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function pickTarget() {
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await r.json();
      const page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page;
    } catch {}
    await sleep(250);
  }
  throw new Error('devtools 不可达');
}

const page = await pickTarget();
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let id = 0;
const pending = new Map();
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
function send(method, params = {}) {
  const mid = ++id;
  return new Promise((res) => { pending.set(mid, res); ws.send(JSON.stringify({ id: mid, method, params })); });
}
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result && r.result.exceptionDetails) return { __error: JSON.stringify(r.result.exceptionDetails).slice(0, 400) };
  return r.result && r.result.result ? r.result.result.value : null;
}
async function click(x, y) {
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}

await send('Runtime.enable');
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1180, height: 780, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: URL });
await sleep(2500);

const out = {};
out.viewport = await ev("JSON.stringify({innerH:window.innerHeight,innerW:window.innerWidth,scrollY:window.scrollY,docScrollTop:(document.scrollingElement||{}).scrollTop,htmlH:document.documentElement.scrollHeight,bodyH:document.body.scrollHeight,dpr:window.devicePixelRatio})");
out.jsErrorsAtStart = await ev("JSON.stringify(window.__jsErrors||[])");
out.hasApi = await ev("!!(window.pywebview && window.pywebview.api)");

// 切到「工作区」标签
await ev("switchPanel('ws')");
await sleep(900);

out.panel = await ev(`JSON.stringify((() => {
  const g = (el) => { if (!el) return null; const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return { display:s.display, overflowY:s.overflowY, height:Math.round(r.height), top:Math.round(r.top),
             minHeight:s.minHeight, flex:s.flex, position:s.position }; };
  const pane = $('wsTreePane');
  return {
    asideRight: g(document.querySelector('aside.right')),
    body: g(document.querySelector('body')),
    rpWs: g($('rp-ws')),
    wsNav: g(document.querySelector('#rp-ws .ws-nav')),
    pane: g(pane),
    paneClient: pane ? pane.clientHeight : null,
    paneScroll: pane ? pane.scrollHeight : null,
    paneCanScroll: pane ? pane.scrollHeight > pane.clientHeight : null,
    activeBodyId: (document.querySelector('.rp-body.active')||{}).id,
    crumb: $('wsCrumb') ? $('wsCrumb').textContent : null,
    disabledTabs: [...document.querySelectorAll('.rp-tab')].map(b => b.dataset.rp + ':' + b.classList.contains('active')),
    rowCount: document.querySelectorAll('#wsTreePane .tree-row').length
  };
})())`);

out.rows = await ev(`JSON.stringify([...document.querySelectorAll('#wsTreePane .tree-row')].map((r,i) => {
  const b = r.getBoundingClientRect();
  return { i, text: r.textContent.trim(), onclick: typeof r.onclick,
           y: Math.round(b.top), h: Math.round(b.height), w: Math.round(b.width),
           pointerEvents: getComputedStyle(r).pointerEvents };
}))`);

out.firstDirHitTest = await ev(`JSON.stringify((() => {
  const rows = [...document.querySelectorAll('#wsTreePane .tree-row')];
  const dir = rows.find(r => r.textContent.includes('📁'));
  if (!dir) return { error: '未找到目录行' };
  const b = dir.getBoundingClientRect();
  const cx = b.left + b.width / 2, cy = b.top + b.height / 2;
  const hit = document.elementFromPoint(cx, cy);
  return { text: dir.textContent.trim(), cx: Math.round(cx), cy: Math.round(cy),
           hitTag: hit ? hit.tagName : null, hitClass: hit ? hit.className : null,
           hitIsSelfOrChild: hit ? (hit === dir || dir.contains(hit)) : false };
})())`);

// 真实鼠标点击第一个目录行
const info = JSON.parse(out.firstDirHitTest || '{}');
if (typeof info.cx === 'number') {
  await click(info.cx, info.cy);
  await sleep(900);
  out.afterRealClick = await ev(`JSON.stringify({
    crumb: $('wsCrumb').textContent,
    rowCount: document.querySelectorAll('#wsTreePane .tree-row').length,
    firstRows: [...document.querySelectorAll('#wsTreePane .tree-row')].slice(0,6).map(r=>r.textContent.trim())
  })`);
}

// 若真实点击无效，再用 JS .click() 验证事件本身
out.afterJsClick = await ev(`(async () => {
  const rows = [...document.querySelectorAll('#wsTreePane .tree-row')];
  const dir = rows.find(r => r.textContent.includes('📁'));
  if (!dir) return JSON.stringify({ error: '未找到目录行' });
  dir.click();
  await new Promise(r => setTimeout(r, 800));
  return JSON.stringify({ crumb: $('wsCrumb').textContent,
    rowCount: document.querySelectorAll('#wsTreePane .tree-row').length });
})()`);

// 滚动到底部，检查最后一行是否落入可视区并可点
out.scrollBottom = await ev(`JSON.stringify((() => {
  const pane = $('wsTreePane');
  pane.scrollTop = pane.scrollHeight;
  const rows = [...pane.querySelectorAll('.tree-row')];
  const last = rows[rows.length - 1];
  const b = last.getBoundingClientRect();
  const paneRect = pane.getBoundingClientRect();
  const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
  return { scrollTop: pane.scrollTop, scrollHeight: pane.scrollHeight, clientHeight: pane.clientHeight,
           lastRowY: Math.round(b.top), lastRowBottom: Math.round(b.bottom),
           paneTop: Math.round(paneRect.top), paneBottom: Math.round(paneRect.bottom),
           lastRowVisible: b.top >= paneRect.top && b.bottom <= paneRect.bottom,
           hitTag: hit ? hit.tagName + '.' + hit.className : null };
})())`);

// 监听 activate 服务、事件总线等无关；页面错误复查
out.jsErrorsAtEnd = await ev("JSON.stringify(window.__jsErrors||[])");

console.log(JSON.stringify(out, null, 1));
ws.close();
