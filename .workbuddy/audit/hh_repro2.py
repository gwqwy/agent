"""sahou-harness 缺陷复现 2：repl/工具逃逸/插件安装/loader/CLI/desktop。只读。"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = "E:/文件/编程文件/agent/sahou-harness"
sys.path.insert(0, REPO)
from harness.kernel import Harness
from harness.config import Profile

def P(*a):
    print(" ".join(str(x) for x in a), flush=True)

def make_plugin(tmp, name, body, manifest=None):
    p = Path(tmp) / name
    p.mkdir(parents=True, exist_ok=True)
    if manifest is not False:
        (p / "plugin.json").write_text(json.dumps(manifest or {"name": name}), encoding="utf-8")
    (p / "register.py").write_text(body, encoding="utf-8")
    return p

P("=" * 72)
P("[I] repl 插件里 host.harness 是否存在（/plugins 与未知命令帮助）")
with tempfile.TemporaryDirectory() as tmp:
    prof = Profile(Path(tmp) / "p")
    import harness.builtins.models.register as mr
    orig = mr._build_llm
    mr._build_llm = lambda entry: type("F", (), {"model": "x", "total_usage": {}})()
    try:
        from harness.cli import build_runtime
        host = build_runtime(prof, tmp)
    finally:
        mr._build_llm = orig
    P("  build_runtime 是否成功（需要模型配置）→ state:", {p["name"]: p["state"] for p in host.list()})
    P("  Harness 是否有 harness 属性:", hasattr(host, "harness"))
    P("  正确写法应是 host.collect_commands / host.list（Harness 自身）")

P("=" * 72)
P("[J] tools_fs 路径监狱：glob 穿越 / 符号链接逃逸")
with tempfile.TemporaryDirectory() as tmp:
    ws = Path(tmp) / "ws"; ws.mkdir()
    outside = Path(tmp) / "outside"; outside.mkdir()
    (outside / "secret.txt").write_text("SECRET", encoding="utf-8")
    prof = Profile(Path(tmp) / "p")
    import harness.builtins.models.register as mr
    orig = mr._build_llm
    mr._build_llm = lambda entry: type("F", (), {"model": "x", "total_usage": {}})()
    try:
        from harness.cli import build_runtime
        host = build_runtime(prof, str(ws))
    finally:
        mr._build_llm = orig
    tools = {t.name: t for t in host.collect_tools()}
    P("  list_files('../*') =", repr(tools["list_files"].invoke({"pattern": "../*"})))
    P("  list_files('**/*.txt') =", repr(tools["list_files"].invoke({"pattern": "**/*.txt"})))
    # 符号链接逃逸（Windows 需要权限，失败则记录）
    link = ws / "link_out"
    try:
        link.symlink_to(outside, target_is_directory=True)
        P("  已创建目录符号链接 ws/link_out -> outside")
        P("  read_file('link_out/secret.txt') =", repr(tools["read_file"].invoke({"path": "link_out/secret.txt"})[:80]))
        P("  write_file('link_out/x.txt') =", repr(tools["write_file"].invoke({"path": "link_out/x.txt", "content": "x"})[:80]))
    except (OSError, NotImplementedError) as exc:
        P("  无法创建符号链接（Windows 权限）:", type(exc).__name__, exc)
    try:
        tools["read_file"].invoke({"path": "C:/Windows/win.ini"})
        P("  read_file 绝对路径 C:/Windows/win.ini → 未拦截（危险）")
    except Exception as exc:
        P("  read_file 绝对路径被拦截:", type(exc).__name__, str(exc)[:60])

P("=" * 72)
P("[K] 外部插件目录名与 plugin.json name 不一致时 install_plugin 的热激活")
with tempfile.TemporaryDirectory() as tmp:
    prof = Profile(Path(tmp) / "p")
    import harness.builtins.models.register as mr
    orig = mr._build_llm
    mr._build_llm = lambda entry: type("F", (), {"model": "x", "total_usage": {}})()
    try:
        from harness.cli import build_runtime
        host = build_runtime(prof, str(tmp))
    finally:
        mr._build_llm = orig
    from harness.desktop import DesktopApp
    app = DesktopApp(host)
    src = Path(tmp) / "my-plugin-dir"
    src.mkdir()
    (src / "plugin.json").write_text(json.dumps({"name": "cool-name"}), encoding="utf-8")
    (src / "register.py").write_text("def register(ctx):\n    ctx.provide('cool', 1)\n", encoding="utf-8")
    res = app.install_plugin(str(src))
    P("  install_plugin 返回:", res)
    P("  插件是否真的热激活（services 里有无 cool）:", "cool" in host.services)
    P("  host.plugins 键:", sorted(host.plugins))

P("=" * 72)
P("[L] loader：模块泄漏 / plugin.json 损坏/字段缺失")
with tempfile.TemporaryDirectory() as tmp:
    host = Harness()
    p = make_plugin(tmp, "leak", "def register(ctx):\n    ctx.provide('x', 1)\n")
    host.mount(p)
    for i in range(3):
        host.activate("leak")     # 幂等：只建一次 ctx
        host.deactivate("leak")   # DISPOSED
    before = [m for m in sys.modules if m.startswith("harness_plugin_")]
    P("  sys.modules 中 harness_plugin_* 模块数:", len(before))
    host.activate("leak")         # DISPOSED 后再次激活会再执行一次 register
    rec = host.plugins["leak"]
    P("  反复激活+卸载后 state:", rec.state, " 模块数:", len([m for m in sys.modules if m.startswith('harness_plugin_')]))
    bad = Path(tmp) / "badjson"
    bad.mkdir()
    (bad / "badjson" / "x").parent.mkdir(parents=True, exist_ok=True)
    (bad / "plugin.json").write_text("{ 这不是 json", encoding="utf-8")
    (bad / "register.py").write_text("def register(ctx):\n    ctx.provide('y', 1)\n", encoding="utf-8")
    r = host.mount(bad)
    P("  损坏 plugin.json 的插件 mount 结果 name =", r.name, " manifest =", r.manifest)
    noentry = Path(tmp) / "noentry"
    noentry.mkdir()
    (noentry / "register.py").write_text("VALUE = 1\n", encoding="utf-8")
    r2 = host.mount(noentry)
    rec2 = host.activate(r2.name)
    P("  register.py 无入口插件:", rec2.state, " skipped =", rec2.skipped)

P("=" * 72)
P("[M] DesktopApp.ws_tree 的 root 未 resolve：workspace 带尾随分隔符/相对路径时")
with tempfile.TemporaryDirectory() as tmp:
    from harness.desktop import DesktopApp
    ws = Path(tmp) / "ws"; (ws / "sub").mkdir(parents=True)
    (ws / "sub" / "a.txt").write_text("x", encoding="utf-8")
    class H:
        workspace = str(ws) + os.sep           # 尾随分隔符
    app = DesktopApp.__new__(DesktopApp); app.host = H()
    P("  workspace =", repr(H.workspace))
    P("  ws_tree() =", app.ws_tree())
    P("  ws_tree('sub') =", app.ws_tree("sub"))
    class H2:
        workspace = "ws"                        # 相对路径（cwd 不匹配）
    app2 = DesktopApp.__new__(DesktopApp); app2.host = H2()
    P("  相对 workspace ws_tree('sub') =", app2.ws_tree("sub"))

P("=" * 72)
P("[N] run_terminal 在未设置工作区时的表现")
with tempfile.TemporaryDirectory() as tmp:
    from harness.desktop import DesktopApp, _validate_url
    class H:
        workspace = ""
        def collect_tools(self): return []
    app = DesktopApp.__new__(DesktopApp); app.host = H()
    P("  collect_tools 为空时 run_terminal =", app.run_terminal("echo hi"))
