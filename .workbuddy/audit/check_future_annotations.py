import sys, json
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")

print("[A] coding.py 用 from __future__ import annotations，其工具 schema 应保留 int 类型")
from nanoagent.coding import CodingWorkspace
ws = CodingWorkspace(root=r"E:/文件/编程文件/agent/.workbuddy/audit/ws_scratch")
for t in ws.as_tools():
    if t.name in ("read_file", "run_command"):
        print(t.name, "->", json.dumps(t.parameters, ensure_ascii=False))

print()
print("[B] llm.py / memory.py 自身模块的 __future__ 注解")
import nanoagent.coding as c
print("coding 模块 __future__ annotations 生效:", c.__annotations__ if hasattr(c,'__annotations__') else "n/a")
import inspect
sig = inspect.signature(ws.read_file)
for name, p in sig.parameters.items():
    print(f"  {name}: annotation={p.annotation!r} type={type(p.annotation).__name__}")
