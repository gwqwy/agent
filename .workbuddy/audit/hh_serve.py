"""审计用：把真实 ws_tree 结果嵌进 mock，渲染真实 UI_HTML，供无头浏览器实测右侧文件区。"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(r"E:/文件/编程文件/agent/sahou-harness")
sys.path.insert(0, str(ROOT))
from harness.desktop import DesktopApp, UI_HTML  # noqa: E402

WS = os.environ.get("HH_WS") or r"E://文件//编程文件//agent"


class _H:
    workspace = WS


app = DesktopApp.__new__(DesktopApp)  # 只借用纯函数 ws_tree，不触发 host 依赖
app.host = _H()

trees = {}
queue = [""]
seen = set()
while queue:
    p = queue.pop(0)
    if p in seen:
        continue
    seen.add(p)
    r = app.ws_tree(p)
    trees[p] = r
    if r.get("ok"):
        for e in r["entries"]:
            if e["dir"]:
                nxt = (r["rel"] + "/" + e["name"]) if r["rel"] else e["name"]
                queue.append(nxt)

MOCK = """
const TREES = %s;
window.__jsErrors = [];
window.addEventListener('error', e => window.__jsErrors.push('error: ' + e.message));
window.addEventListener('unhandledrejection', e => window.__jsErrors.push('rejection: ' + (e.reason && e.reason.message || e.reason)));
window.pywebview = { api: {
  ws_tree: async (p) => (TREES[p] || {ok:false, error:'no mock for '+JSON.stringify(p)}),
  status: async () => ({ ok:true, model:'deepseek', models:['deepseek'],
    profile:'p', workspace:%s, workspace_name:'agent', session:'default',
    session_name:'1', shell_permission:'allow', fs_permission:'ask',
    thinking_level:'low', theme:'light', context_window:128000, usage:{} }),
  context_usage: async () => ({ ok:true, used:1000, window:128000, percent:0.8, breakdown:[] }),
  workspaces: async () => ({ ok:true, current:'ws-1', workspaces:[] }),
  sessions: async () => ({ ok:true, current:'default', sessions:[] }),
  session_history: async () => ({ ok:true, session:'default', history:[] }),
  rename_session: async () => ({ ok:true }),
  usage: async () => ({ ok:true, usage:{} }),
  plugins: async () => ({ ok:true, plugins:[] }),
  skills: async () => ({ ok:true, skills:[] }),
  get_models: async () => ({ ok:true, default_model:'deepseek', models:[] }),
  set_theme: async () => ({ ok:true }),
  switch_model: async () => ({ ok:true, model:'deepseek', message:'ok' }),
}};
setTimeout(() => window.dispatchEvent(new Event('pywebviewready')), 20);
""" % (json.dumps(trees, ensure_ascii=False), json.dumps(WS))


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        html = UI_HTML.replace("<script>", "<script>" + MOCK + "</script>\n<script>", 1)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("serving 8766, ws:", WS, "dirs:", len(trees), flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8766), H).serve_forever()
