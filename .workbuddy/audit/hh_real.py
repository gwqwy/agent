"""审计用：真实 WebView2 窗口内渲染完整 UI_HTML，验证右侧文件区（只读，不改源码）。"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"E:/文件/编程文件/agent/sahou-harness")

import webview  # noqa: E402
from harness.cli import build_runtime  # noqa: E402
from harness.config import Profile  # noqa: E402
from harness.desktop import DesktopApp, UI_HTML  # noqa: E402

WS = r"E:/文件/编程文件/agent"
profile = Profile(Path.home() / ".sahou-harness" / "profiles" / "default")
host = build_runtime(profile, WS)
app = DesktopApp(host)
host.workspace = WS

EARLY = ("<script>window.__jsErrors=[];"
         "window.addEventListener('error',function(e){window.__jsErrors.push('error: '+e.message)});"
         "window.addEventListener('unhandledrejection',function(e){"
         "window.__jsErrors.push('rejection: '+(e.reason&&e.reason.message||e.reason))});</script>")
html = UI_HTML.replace('<html lang="zh">', '<html lang="zh" data-theme="light">', 1)
html = html.replace("<script>", EARLY + "<script>", 1)

window = webview.create_window("审计窗口", html=html, js_api=app, width=1180, height=780, min_size=(940, 620))
app._window = window
result = {"stage": "not-started"}


def js(expr):
    try:
        return window.evaluate_js(expr)
    except Exception as exc:  # noqa: BLE001
        return f"<<evaluate_js 异常: {exc}>>"


def on_loaded():
    try:
        time.sleep(4)
        r = {}
        r["viewport"] = js("JSON.stringify({innerW:window.innerWidth,innerH:window.innerHeight,"
                           "scrollY:window.scrollY,htmlH:document.documentElement.scrollHeight})")
        r["api"] = js("JSON.stringify({has:!!(window.pywebview&&window.pywebview.api),"
                      "ws_tree:typeof (window.pywebview.api||{}).ws_tree})")
        r["switch"] = js("switchPanel('ws'); 'ok'")
        time.sleep(1.2)
        r["geom"] = js("""JSON.stringify((() => {
          const pane=$('wsTreePane'); const b=pane.getBoundingClientRect(); const a=document.querySelector('aside.right').getBoundingClientRect();
          const rows=[...pane.querySelectorAll('.tree-row')];
          return {crumb:$('wsCrumb').textContent, rows:rows.length,
                  asideTop:Math.round(a.top), asideH:Math.round(a.height),
                  paneTop:Math.round(b.top), paneBottom:Math.round(b.bottom),
                  clientH:pane.clientHeight, scrollH:pane.scrollHeight,
                  active:(document.querySelector('.rp-body.active')||{}).id,
                  firstRows:rows.slice(0,5).map(x=>x.textContent.trim())};
        })())""")
        r["click"] = js("""(async () => {
          const rows=[...document.querySelectorAll('#wsTreePane .tree-row')];
          const dir=rows.find(x=>x.textContent.includes('📁'));
          if(!dir) return 'no-dir';
          dir.click();
          await new Promise(r=>setTimeout(r,1200));
          return JSON.stringify({crumb:$('wsCrumb').textContent,
            rows:document.querySelectorAll('#wsTreePane .tree-row').length});
        })()""")
        time.sleep(1.5)
        r["afterClick"] = js("JSON.stringify({crumb:$('wsCrumb').textContent,rows:document.querySelectorAll('#wsTreePane .tree-row').length})")
        r["errors"] = js("JSON.stringify(window.__jsErrors||[])")
        result.clear()
        result.update(r)
        result["stage"] = "ok"
    except Exception as exc:  # noqa: BLE001
        import traceback
        result["stage"] = "crash"
        result["trace"] = traceback.format_exc()
    finally:
        try:
            window.destroy()
        except Exception:
            pass


window.events.loaded += on_loaded
webview.start()
print(json.dumps(result, ensure_ascii=False, indent=1))
