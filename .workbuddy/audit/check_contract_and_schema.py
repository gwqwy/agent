import sys, json, tempfile, os
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")

print("="*70)
print("[1] 数据契约：tracing 写 'type'，observability 读 'event'")
from nanoagent.tracing import Tracer
from nanoagent.observability import trace_summary, trace_report, load_trace
import pathlib

d = tempfile.mkdtemp()
p = pathlib.Path(d)/"t.jsonl"
t = Tracer(path=p)
t.start_run("a")
t.log("llm_call", usage={"prompt_tokens": 10, "completion_tokens": 5})
t.log("tool_call", tool="calc", arguments={}, result="42")
t.end_run(iterations=1)

raw = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
print("Tracer 实际写出的字段名:", [sorted(e.keys()) for e in raw])
print("字段 'type' 值:", [e.get("type") for e in raw])
print("字段 'event' 存在? :", [("event" in e) for e in raw])
s = trace_summary(p)
print("trace_summary 结果:", json.dumps(s, ensure_ascii=False))
print(">>> llm_calls/tool_calls 是否为 0：", s["runs"])

print()
print("="*70)
print("[2] tools schema：Optional / list[dict] / Enum / 默认值")
from typing import Optional, List
from enum import Enum
from nanoagent.tools import make_tool
class Color(Enum):
    RED="red"; BLUE="blue"
def f(a: Optional[str], b: List[dict], c: Color = Color.RED, d: int = 3, e: "list[int]" = None):
    """测试工具。

    Args:
        a: 参数a
    """
    return ""
tool = make_tool(f)
print(json.dumps(tool.parameters, ensure_ascii=False, indent=2))

print()
print("="*70)
print("[3] Enum 值未被约束（应输出 enum 但实际只是 string）")
print("Color 字段 schema:", tool.parameters["properties"].get("c"))
