const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const calls = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: (t, name) => (...args) => {
      if (name === 'resolve_approval') calls.push(['resolve', ...args]);
      if (name === 'checkpoints') return Promise.resolve({ ok: true, items: [
        { id: 'ck-1', ts: Date.now() / 1000, label: 'write_file a.txt',
          files: [{ rel: 'a.txt', existed: true }] }] });
      if (name === 'undo_checkpoint') { calls.push(['undo', ...args]);
        return Promise.resolve({ ok: true, restored: 1, deleted: 0 }); }
      return Promise.resolve({ ok: true });
    } }) };
  },
});
const w = dom.window;
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  w.dispatchEvent(new w.Event('pywebviewready'));
  await wait(200);
  // ① shell 审批（后台会话也应弹出：session 不匹配不能被过滤）
  w.onAgentEvent({ kind: 'approval', id: 'r1', approval_kind: 'shell',
    command: 'npm run build', cwd: 'app', session: 'other-session' });
  await wait(50);
  const mask = w.document.getElementById('approveMask');
  console.log('弹窗打开:', mask.classList.contains('open'));
  console.log('标题:', w.document.getElementById('apTitle').textContent);
  console.log('命令:', w.document.querySelector('#apDetail .ap-cmd').textContent);
  console.log('按钮:', [...w.document.querySelectorAll('#approveMask button')].map(b => b.textContent).join(' | '));
  w.approveReply('allow_always');
  await wait(50);
  console.log('回填调用:', JSON.stringify(calls));
  console.log('弹窗关闭:', !mask.classList.contains('open'));
  // ② 写入审批：diff 着色
  w.onAgentEvent({ kind: 'approval', id: 'r2', approval_kind: 'write', path: 'a.py',
    detail: '该文件已存在，将被覆盖',
    diff: '--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-print(1)\n+print(2)' });
  await wait(50);
  console.log('写入标题:', w.document.getElementById('apTitle').textContent);
  console.log('diff 增行:', w.document.querySelectorAll('#apDetail .d-add').length,
              '| 删行:', w.document.querySelectorAll('#apDetail .d-del').length,
              '| 元信息:', w.document.querySelectorAll('#apDetail .d-meta').length);
  w.approveReply('deny');
  await wait(50);
  console.log('全部回填:', JSON.stringify(calls));
  // ③ 撤销入口存在 + 通用页渲染
  console.log('撤销按钮:', w.document.querySelector('[onclick="undoLastChange()"]') ? '存在' : '缺失');
  w.renderGeneral ? null : null;
  w.eval("switchTab('general')");
  await wait(150);
  console.log('检查点行数:', w.document.querySelectorAll('#ckptList .set-row').length);
  console.log('确认开关:', w.document.getElementById('confirmWriteBtn').textContent);
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
