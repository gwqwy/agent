const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const calls = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: (t, name) => (...args) => {
      if (name === 'can_stream') return Promise.resolve({ ok: true, stream: true });
      if (name === 'chat_stream') { calls.push(args[0]); return Promise.resolve({ ok: true, stream: true, session: args[1] || 's1' }); }
      if (name === 'subagents') return Promise.resolve({ ok: true, items: [
        { ts: Date.now() / 1000, sub_session: 'sub-abc', task: '压测子任务', ok: true,
          output: '结论：测试通过', elapsed_ms: 3200, steps: ['write_file', 'run_command'] }] });
      if (name === 'usage') return Promise.resolve({ ok: true, usage: {}, source: 'llm' });
      if (name === 'sessions') return Promise.resolve({ ok: true, current: 'default', sessions: [
        { id: 'default', name: '会话一', ws: 'w1', updated: 1, pinned: false, done: false, order: 0 }] });
      if (name === 'workspaces') return Promise.resolve({ ok: true, current: 'w1',
        workspaces: [{ id: 'w1', name: '测试', path: 'C:/ws' }] });
      if (name === 'session_history') return Promise.resolve({ ok: true, history: [] });
      return Promise.resolve({ ok: true });
    } }) };
  },
});
const w = dom.window;
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  w.dispatchEvent(new w.Event('pywebviewready'));
  await wait(250);
  const input = w.document.getElementById('input');
  // 第一条：正常发出（busy）
  input.value = '第一条';
  await w.send();
  await wait(80);
  console.log('派发调用:', JSON.stringify(calls), '| busy:', w.eval('JSON.stringify([...busySessions])'));
  // 第二条：忙碌中发送 → 入队
  input.value = '第二条';
  await w.send();
  await wait(80);
  console.log('排队后派发调用:', JSON.stringify(calls), '| 队列:', w.eval("(queueBySession.get('default')||[]).length"),
              '| 徽标:', w.document.getElementById('queueBadge').textContent);
  // 本轮结束 → 自动发送排队消息
  w.onStreamEvent({ kind: 'done', ok: true, reply: '收到第一条', reasoning: '',
    tool_calls: [], model: 'deepseek', usage: {}, session: 'default' });
  await wait(200);
  console.log('完成后派发调用:', JSON.stringify(calls));
  console.log('队列已清空:', w.eval("!(queueBySession.get('default')||[]).length"), '| 徽标:', JSON.stringify(w.document.getElementById('queueBadge').style.display));
  // 子 agent 事件 + 面板
  w.onStreamEvent({ kind: 'done', ok: true, reply: 'x', reasoning: '', tool_calls: [], model: 'deepseek', usage: {}, session: 'default' });
  await wait(50);
  w.eval("onAgentEvent") && w.onAgentEvent({ kind: 'subagent', phase: 'start', task: '做个小实验', session: 'default' });
  await wait(30);
  console.log('live 区子agent步骤:', [...w.document.querySelectorAll('#thread .step .s-text')].map(e => e.textContent).join(' / '));
  w.eval("switchPanel('sub')");
  await wait(150);
  console.log('子agent面板行数:', w.document.querySelectorAll('#subPane .sub-row').length);
  console.log('面板首个任务:', (w.document.querySelector('#subPane .sub-task') || {}).textContent);
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
