"""审计用：host.workspace 为相对路径 ".(=CLI 默认)" 时，用真实 DesktopApp.ws_tree 预取每层结果，
渲染真实 UI_HTML —— 复现"能看到根目录但点不开任何文件夹"。"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(r"E:/文件/编程文件/agent/sahou-harness")
sys.path.insert(0, str(ROOT))
from harness.desktop import DesktopApp, UI_HTML  # noqa: E402

WS_DIR = r"E:/文件/编程文件/agent"
os.chdir(WS_DIR)                      # 模拟从该目录启动 sha desktop（--workspace 默认 "."）


class _H:
    workspace = "."                   # ← cli.build_runtime 的默认值


app = DesktopApp.__new__(DesktopApp)
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
    print("  ws_tree(%r) -> ok=%s rel=%r err=%r n=%s" % (
        p, r.get("ok"), r.get("rel"), r.get("error"), len(r.get("entries") or [])), flush=True)
    if r.get("ok"):
        for e in r["entries"]:
            if e["dir"]:
                queue.append((r["rel"] + "/" + e["name"]) if r["rel"] else e["name"])
print("  trees =", len(trees), "（相对路径下能被成功展开的层数）", flush=True)

MOCK = """
const TREES = %s;
window.__jsErrors = [];
window.addEventListener('error', e => window.__jsErrors.push('error: ' + e.message));
window.addEventListener('unhandledrejection', e => window.__jsErrors.push('rejection: ' + (e.reason && e.reason.message || e.reason)));
window.pywebview = { api: {
  ws_tree: async (p) => (TREES[p] || {ok:false, error:'no mock for '+JSON.stringify(p)}),
  status: async () => ({ ok:true, model:'deepseek', models:['deepseek'], profile:'p', workspace:%s,
    workspace_name:'agent', session:'default', session_name:'1', shell_permission:'allow',
    fs_permission:'ask', thinking_level:'low', theme:'light', context_window:128000, usage:{} }),
  context_usage: async () => ({ ok:true, used:1, window:128000, percent:0.1, breakdown:[] }),
  workspaces: async () => ({ ok:true, current:'ws-1', workspaces:[] }),
  sessions: async () => ({ ok:true, current:'default', sessions:[] }),
  session_history: async () => ({ ok:true, history:[] }),
  rename_session: async () => ({ ok:true }), usage: async () => ({ ok:true, usage:{} }),
  plugins: async () => ({ ok:true, plugins:[] }), skills: async () => ({ ok:true, skills:[] }),
  get_models: async () => ({ ok:true, default_model:'deepseek', models:[] }),
  set_theme: async () => ({ ok:true }), switch_model: async () => ({ ok:true, model:'x', message:'ok' }),
}};
setTimeout(() => window.dispatchEvent(new Event('pywebviewready')), 20);
""" % (json.dumps(trees, ensure_ascii=False), json.dumps(WS_DIR))


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
    print("serving 8767 (relative workspace), trees:", len(trees), flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8767), H).serve_forever()
