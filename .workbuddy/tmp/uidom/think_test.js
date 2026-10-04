const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('page.html', 'utf-8');
const dom = new JSDOM(html, { runScripts:'dangerously', url:'https://localhost/', pretendToBeVisual:true,
  beforeParse(w){ w.pywebview = { api: new Proxy({}, { get: () => () => Promise.resolve({ok:true}) }) }; } });
const w = dom.window;
(async () => {
  w.dispatchEvent(new w.Event('pywebviewready'));
  await new Promise(r => setTimeout(r, 200));
  w.add('看完了。', 'bot', ['模型: x'], '我先读了几个文件…', undefined,
        [{name:'read_file',detail:'   1: hi',ok:true,args:{path:'a.py'}}]);
  const msg = [...w.document.querySelectorAll('#thread .msg.bot')].pop();
  const head = msg.querySelector('.r-head');
  console.log('思考头文案:', head.textContent);
  console.log('有尾部箭头:', !!head.querySelector('.r-caret-end'));
  head.click();
  console.log('展开后 open 类:', msg.querySelector('.reasoning').classList.contains('open'));
  console.log('读数工具分组:', (msg.querySelector('.tg-title') || {}).textContent);
  console.log('旧类残留:', msg.querySelector('.tool-log') ? '有' : '无');
  console.log('__errs:', JSON.stringify(w.__errs || []));
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
