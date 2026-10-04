import sys
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
from nanoagent.plugins import PluginContext, EventBus

print("[1] ctx.on() 返回的 disposer 是否被 effect 账本追踪（deactivate 后 handler 是否移除）")
bus = EventBus()
seen = []
ctx = PluginContext("p", bus=bus)
d = ctx.on("tick", lambda **kw: seen.append(kw))
print("  on() 返回 disposer:", d)
print("  账本长度（_disposers）:", len(ctx._disposers))
bus.emit("tick", n=1)
print("  emit 后 handler 调用次数:", len(seen))
ctx.deactivate()
print("  deactivate 后账本长度:", len(ctx._disposers))
bus.emit("tick", n=2)
print("  deactivate 后再 emit，handler 调用次数:", len(seen), "（若为2说明 handler 未被清理）")

print()
print("[2] ctx.provide() 的 disposer 是否被追踪：")
c2 = PluginContext("q")
c2.provide("svc", object())
print("  provide 后账本长度:", len(c2._disposers), "services:", list(c2.services))
c2.deactivate()
print("  deactivate 后 services:", list(c2.services), "（应为空）")

print()
print("[3] effect(fn) 返回 None 时不记录，返回 disposer 时记录：")
c3 = PluginContext("r")
called = []
c3.effect(lambda: None)
print("  返回 None 后账本:", len(c3._disposers))
c3.effect(lambda: (lambda: called.append(1)))
print("  返回 disposer 后账本:", len(c3._disposers))
c3.deactivate()
print("  disposer 被执行次数:", len(called))
