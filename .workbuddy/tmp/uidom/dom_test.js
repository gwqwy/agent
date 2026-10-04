/* jsdom 复现：stub pywebview api，跑完整发送链，抓取运行时错误。 */
const { JSDOM } = require('jsdom');
const fs = require('fs');

const html = fs.readFileSync('page.html', 'utf-8');
const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'https://localhost/',
  pretendToBeVisual: true,
  beforeParse(window) {
    window.__errs = [];
    window.addEventListener('error', e => errors.push(String(e.message)));
    // stub pywebview api
    const responses = {
      status: { ok: true, model: 'deepseek', models: ['deepseek'],
        shell_permission: 'allow', fs_permission: 'allow', git_permission: 'ask',
        thinking_level: 'off', plan_mode: false, theme: 'light',
        workspace: 'C:/ws', workspace_name: 'ws' },
      sidebar: { ok: true, sessions: [], current: 's-1' },
      session_history: { ok: true, history: [
        { role: 'user', content: '你好' },
        { role: 'assistant', content: '你好！' },
      ] },
      get_ui_prefs: { ok: true, prefs: {} },
      can_stream: { ok: true, stream: true },
      chat_stream: { ok: true, stream: true, session: 's-1' },
      usage: { ok: true, usage: { prompt_tokens: 100, completion_tokens: 20 },
               source: 'llm' },
    };
    const handler = {
      get(target, name) {
        if (name in responses) return () => Promise.resolve(responses[name]);
        return () => Promise.resolve({ ok: true });
      },
    };
    window.pywebview = { api: new Proxy({}, handler) };
  },
});

const { window } = dom;
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  // 触发 pywebviewready 启动链
  window.dispatchEvent(new window.Event('pywebviewready'));
  await wait(300);

  // 模拟用户发送
  const input = window.document.getElementById('input');
  input.value = '测试消息';
  await window.send();
  await wait(200);

  // 模拟流式 done 事件回推
  window.onStreamEvent({ kind: 'done', ok: true, reply: '回复内容',
    reasoning: '', tool_calls: [], model: 'deepseek',
    usage: { prompt_tokens: 100, completion_tokens: 20 }, session: 's-1' });
  await wait(200);

  const thread = window.document.getElementById('thread');
  const msgs = thread.querySelectorAll('.msg');
  console.log('=== 结果 ===');
  console.log('thread 消息数:', msgs.length);
  console.log('send.disabled:', window.document.getElementById('send').disabled);
  console.log('liveBlock 残留:', !!window.liveBlock);
  console.log('hero:', window.document.getElementById('hero').style.display);
  console.log('usageLine:', window.document.getElementById('usageLine').textContent);
  console.log('window.__errs:', JSON.stringify(window.__errs));
  console.log('captured errors:', JSON.stringify(errors));
  for (const m of msgs) console.log('  msg:', m.className, '|', (m.textContent || '').slice(0, 40).replace(/\n/g, ' '));
})().catch(e => { console.error('测试脚本异常:', e); process.exit(1); });
