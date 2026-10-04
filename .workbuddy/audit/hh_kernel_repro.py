"""sahou-harness 缺陷复现：内核生命周期 / 事件 / 权限门 / 配置。只读，不改源码。"""
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO = "E:/文件/编程文件/agent/sahou-harness"
sys.path.insert(0, REPO)

from harness.config import Profile, DEFAULT_CONFIG
from harness.kernel import ACTIVE, DISPOSED, FAILED, Harness

OUT = []
def P(*a):
    line = " ".join(str(x) for x in a)
    OUT.append(line)
    print(line, flush=True)

def make_plugin(tmp, name, body):
    p = Path(tmp) / name
    p.mkdir(parents=True, exist_ok=True)
    (p / "plugin.json").write_text(json.dumps({"name": name}), encoding="utf-8")
    (p / "register.py").write_text(body, encoding="utf-8")
    return p

# ---------------------------------------------------------------- A
P("=" * 72)
P("[A] ctx.on 的订阅是否随插件 deactivate 一起回收（文档契约：内核统一 LIFO 回收）")
with tempfile.TemporaryDirectory() as tmp:
    host = Harness()
    seen = []
    plug = make_plugin(tmp, "sub", "def register(ctx):\n"
        "    ctx.on('activate', lambda **kw: seen.append(kw.get('name')))\n"
        "    ctx.provide('svc', 1)\n")
    plug_body = plug / "register.py"
    plug_body.write_text(
        "def register(ctx):\n"
        "    ctx.on('activate', lambda **kw: _SEEN.append(kw.get('name')))\n"
        "    ctx.provide('svc', 1)\n", encoding="utf-8")
    g = {"_SEEN": seen}
    # 让插件模块能拿到 _SEEN：用 builtins 注入
    import builtins
    builtins._SEEN = seen
    host.mount(plug)
    host.activate("sub")
    P("  activate 后 seen =", seen)
    host.deactivate("sub")
    P("  deactivate 后 state =", host.plugins["sub"].state, " services =", host.services)
    seen.clear()
    host.bus.emit("activate", name="other")
    P("  deactivate 之后再 emit('activate') → seen =", seen)
    P("  >>> 已卸载插件的监听器是否仍在触发:", bool(seen))
    del builtins._SEEN

# ---------------------------------------------------------------- B
P("=" * 72)
P("[B] Harness.deactivate 后 services 重建：models 这类嵌套服务是否丢失")
with tempfile.TemporaryDirectory() as tmp:
    host = Harness()
    a = make_plugin(tmp, "a", "def register(ctx):\n"
        "    ctx.provide('models_runtime', {'pool': {}})\n"
        "    ctx.provide('svc_a', 1)\n")
    b = make_plugin(tmp, "b", "def register(ctx):\n"
        "    ctx.models.register('m1', object())\n"
        "    ctx.provide('svc_b', 2)\n")
    c = make_plugin(tmp, "c", "def register(ctx):\n    ctx.provide('svc_c', 3)\n")
    host.mount_all(tmp)
    for n in ("a", "b", "c"):
        host.activate(n)
    P("  激活后 services keys =", sorted(host.services))
    P("  激活后 models =", sorted(host.services.get('models', {})))
    host.deactivate("c")   # 卸载无关插件
    P("  卸载无关插件 c 后 services keys =", sorted(host.services))
    P("  >>> models 是否还在:", 'models' in host.services)
    P("  >>> models_runtime 是否还在:", 'models_runtime' in host.services)
    P("  >>> svc_a/svc_b 是否还在:", host.services.get('svc_a'), host.services.get('svc_b'))

# ---------------------------------------------------------------- C
P("=" * 72)
P("[C] provide 同名重复注册的行为（是否有覆盖告警）")
with tempfile.TemporaryDirectory() as tmp:
    host = Harness()
    p = make_plugin(tmp, "dup", "def register(ctx):\n"
        "    ctx.provide('svc', 'first')\n"
        "    ctx.provide('svc', 'second')\n")
    host.mount(p)
    rec = host.activate("dup")
    ctx = rec.ctx
    P("  ctx.services['svc'] =", ctx.services.get('svc'), " dispoers 数 =", len(ctx._disposers))
    P("  先手动调用第 1 个 disposer（模拟乱序回收）")
    ctx._disposers[0]()
    P("  调用第 1 个 disposer 后 ctx.services =", ctx.services, "（第 2 次注册的服务被第 1 个 disposer 抹掉）")

# ---------------------------------------------------------------- D
P("=" * 72)
P("[D] EventBus 监听器抛异常是否被吞（无任何日志）")
with tempfile.TemporaryDirectory() as tmp:
    host = Harness()
    def boom(**kw):
        raise RuntimeError("监听器内部错误，应当被看见")
    host.bus.on("activate", boom)
    host.bus.on("activate", lambda **kw: OUT.append("  第二个监听器仍被调用"))
    host.mount(make_plugin(tmp, "x", "def register(ctx):\n    pass"))
    host.activate("x")
    P("  >>> 上面是否打印了任何异常信息（没有 = 被静默吞掉）")

# ---------------------------------------------------------------- E
P("=" * 72)
P("[E] 插件 register 抛异常：effect 的 disposer 是否被调用（是否泄漏）")
with tempfile.TemporaryDirectory() as tmp:
    host = Harness()
    import builtins
    log = []
    builtins._LOG = log
    p = make_plugin(tmp, "fail", "def register(ctx):\n"
        "    ctx.effect(lambda: (lambda: _LOG.append('disposed')))\n"
        "    ctx.provide('half', 1)\n"
        "    raise RuntimeError('后半段崩了')\n")
    host.mount(p)
    rec = host.activate("fail")
    P("  state =", rec.state, " error =", rec.error)
    P("  失败插件 effect 的 disposer 是否执行:", log)
    P("  失败插件是否污染全局 services:", host.services)
    del builtins._LOG

# ---------------------------------------------------------------- F
P("=" * 72)
P("[F] 权限门：非 ask/allow/deny 的值是否 fail-open 直接执行")
with tempfile.TemporaryDirectory() as tmp:
    prof = Profile(Path(tmp) / "profiles" / "p")
    prof.save_config({"default_model": "m", "models": [
        {"name": "m", "provider": "openai", "model": "x", "api_key": "k"}],
        "permissions": {"shell": "Ask"}})
    from harness.cli import build_runtime
    import harness.builtins.models.register as mr
    orig = mr._build_llm
    mr._build_llm = lambda entry: type("F", (), {"model": "x", "total_usage": {}})()
    try:
        host = build_runtime(prof, tmp)
    finally:
        mr._build_llm = orig
    tool = next(t for t in host.collect_tools() if t.name == "run_command")
    host.confirm = lambda prompt: (_ for _ in ()).throw(AssertionError("不应询问"))
    for val in ("Ask", "Deny", "deny ", "no", None, 0, True):
        prof.update_config(permissions={"shell": val})
        try:
            r = tool.invoke({"command": "echo BYPASS-" + str(val)})
            P("  permissions.shell =", repr(val), "→", r[:60].replace("\n", " "))
        except AssertionError as e:
            P("  permissions.shell =", repr(val), "→ 触发了确认（安全）")

# ---------------------------------------------------------------- G
P("=" * 72)
P("[G] 配置读取：permissions/其它字段类型异常或缺失时的行为")
with tempfile.TemporaryDirectory() as tmp:
    prof = Profile(Path(tmp) / "p")
    prof.config_path.write_text(json.dumps({"permissions": {"fs": "ask"}}), encoding="utf-8")
    cfg = prof.load_config()
    P("  写入 permissions={'fs':'ask'} 后 load_config()['permissions'] =", cfg["permissions"])
    P("  >>> shell 键是否被默认值丢失（浅合并）:", "shell" not in cfg["permissions"])
    prof.config_path.write_text(json.dumps({"permissions": ["allow"]}), encoding="utf-8")
    try:
        cfg = prof.load_config()
        mode = (cfg.get("permissions") or {}).get("shell", "ask")
        P("  permissions 写成 list 后取 shell →", mode)
    except Exception as exc:
        P("  permissions 写成 list 后崩溃:", type(exc).__name__, exc)
    prof.config_path.write_text("not-json", encoding="utf-8")
    P("  config.json 损坏后 load_config() =", prof.load_config())
    P("  config.json 损坏后 save/update 是否覆盖损坏文件:", prof.update_config(a=1))

# ---------------------------------------------------------------- H
P("=" * 72)
P("[H] 并发 update_config 是否丢更新")
with tempfile.TemporaryDirectory() as tmp:
    prof = Profile(Path(tmp) / "p")
    prof.save_config({"counter": 0})
    def worker():
        for _ in range(40):
            c = prof.load_config()
            time.sleep(0)
            prof.save_config({**c, "counter": c["counter"] + 1})
    ts = [threading.Thread(target=worker) for _ in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    P("  4 线程 x 40 次自增后 counter =", prof.load_config()["counter"], "（期望 160）")

print()
print("\n".join(OUT[:0]))
