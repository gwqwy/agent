/* 验证：工具步骤写入正文 + 空回复兜底 */
const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously', url: 'https://localhost/', pretendToBeVisual: true,
  beforeParse(w) {
    w.pywebview = { api: new Proxy({}, { get: (t, name) => (...args) => {
      if (name === 'can_stream') return Promise.resolve({ ok: true, stream: true });
      if (name === 'chat_stream') return Promise.resolve({ ok: true, stream: true, session: 's1' });
      if (name === 'usage') return Promise.resolve({ ok: true, usage: { prompt_tokens: 10, completion_tokens: 5 }, source: 'llm' });
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
  input.value = '写个页面';
  await w.send();
  await wait(100);
  // 模拟工具步骤事件
  w.onAgentEvent({ kind: 'tool', tool: 'write_file', result: '已写入 index.html (28 行)', elapsed_ms: 12, session: 's1' });
  w.onAgentEvent({ kind: 'tool', tool: 'write_file', result: '已写入 styles.css (65 行)', elapsed_ms: 8, session: 's1' });
  // 模拟空回复的 done
  w.onStreamEvent({ kind: 'done', ok: true, reply: '', reasoning: '想了很久',
    tool_calls: [{ name: 'write_file' }, { name: 'write_file' }], model: 'deepseek',
    usage: { prompt_tokens: 100, completion_tokens: 40 }, session: 's1' });
  await wait(150);
  const msgs = [...w.document.querySelectorAll('#thread .msg.bot')];
  const last = msgs[msgs.length - 1];
  console.log('bot 消息数:', msgs.length);
  console.log('工具块存在:', !!last.querySelector('.tool-log'));
  console.log('工具行数:', last.querySelectorAll('.tool-row').length);
  console.log('工具行内容:', [...last.querySelectorAll('.tool-row')].map(r => r.textContent).join(' | '));
  console.log('正文:', (last.querySelector('.md-body') || {}).textContent);
  console.log('思考块:', !!last.querySelector('.reasoning'));
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
