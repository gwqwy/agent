const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: (t, name) => (...args) => {
      if (name === 'can_stream') return Promise.resolve({ ok: true, stream: true });
      if (name === 'chat_stream') return Promise.resolve({ ok: true, stream: true, session: 'default' });
      if (name === 'usage') return Promise.resolve({ ok: true, usage: {}, source: 'llm' });
      return Promise.resolve({ ok: true });
    } }) };
  },
});
const w = dom.window;
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  w.dispatchEvent(new w.Event('pywebviewready'));
  await wait(200);
  const input = w.document.getElementById('input');
  input.value = '改 11 处';
  await w.send();
  await wait(80);
  // 模拟一轮工具：3 个编辑（1 个失败）+ 2 条命令（1 个失败）
  w.onAgentEvent({ kind: 'tool', tool: 'edit_file', elapsed_ms: 12,
    args: { path: 'components/pay-panel.vue', old: 'hover-class="none"', new: 'btn-press' },
    result: '已修改 components/pay-panel.vue（替换 1 处，行数 40 → 40，+1 -1）' });
  w.onAgentEvent({ kind: 'tool', tool: 'edit_file', elapsed_ms: 9,
    args: { path: 'pages/order/create.vue' },
    result: '已修改 pages/order/create.vue（替换 1 处，行数 30 → 30，+1 -1）' });
  w.onAgentEvent({ kind: 'tool', tool: 'write_file', elapsed_ms: 5,
    args: { path: 'pages/pkger/hall.vue', lines: 12 },
    result: '已写入 pages/pkger/hall.vue（12 行，+12 -0）' });
  w.onAgentEvent({ kind: 'tool', tool: 'run_command', elapsed_ms: 800,
    args: { command: 'npm run build' }, result: '错误：命令未获人工确认，已拒绝执行' });
  w.onAgentEvent({ kind: 'tool', tool: 'run_command', elapsed_ms: 30,
    args: { command: 'git status --short' }, result: '' });
  w.onStreamEvent({ kind: 'done', ok: true, reply: '改完了。', reasoning: '',
    tool_calls: [], model: 'deepseek', usage: {}, session: 'default' });

  await wait(150);
  const msg = [...w.document.querySelectorAll('#thread .msg.bot')].pop();
  const groups = [...msg.querySelectorAll('.tgroup')];
  console.log('分组数:', groups.length);
  groups.forEach(g => {
    console.log('  ' + g.querySelector('.tg-title').textContent +
      ' | 失败标记: ' + (g.querySelector('.tg-bad') ? g.querySelector('.tg-bad').textContent : '无'));
  });
  const editGroup = groups[0];
  console.log('默认折叠:', !editGroup.classList.contains('open'));
  editGroup.querySelector('.tgroup-head').click();
  console.log('点击后展开:', editGroup.classList.contains('open'));
  const rows = [...editGroup.querySelectorAll('.trow')];
  console.log('更改行数:', rows.length);
  rows.forEach(r => console.log('   ' + r.textContent));
  const cmdRows = [...groups[1].querySelectorAll('.trow')];
  console.log('命令行:', cmdRows.map(r => r.textContent).join(' || '));
  console.log('失败行标红类:', groups[1].querySelectorAll('.trow.bad').length);
  console.log('思考块:', !!msg.querySelector('.reasoning'), '| 标题:',
    (msg.querySelector('.r-title') || {}).textContent);
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
