import sys, asyncio, json, time
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent/tests")
from nanoagent.agent import Agent
from nanoagent.llm import LLMResponse, ToolCall
from mocks import MockLLM, text_response

print("="*70)
print("[A] 同步 run 调用 async 工具（如 MCP 工具）会怎样")
from nanoagent.tools import Tool, tool

@tool
async def async_tool(x: str) -> str:
    """异步工具。"""
    return f"async-{x}"

ag = Agent(llm=MockLLM([LLMResponse(content="", tool_calls=[ToolCall(id="c1", name="async_tool", arguments={"x":"hi"})]), text_response("ok")]),
           tools=[async_tool])
r = ag.run("go", session_id="a")
print("  工具结果:", repr(r.tool_calls[0]["result"]))
print("  >>> 是否得到 coroutine 垃圾串:", "coroutine" in r.tool_calls[0]["result"])

print()
print("="*70)
print("[B] arun 并发执行多个 async 工具，确认真正并发（总耗时 < 串行）")
@tool
async def asleep(tag: str, delay: float) -> str:
    """异步睡眠。"""
    import asyncio as _a
    await _a.sleep(delay)
    return f"done-{tag}"

ag2 = Agent(llm=MockLLM([LLMResponse(content="", tool_calls=[
        ToolCall(id=f"c{i}", name="asleep", arguments={"tag":str(i),"delay":0.3}) for i in range(4)]),
        text_response("ok")]), tools=[asleep], max_workers=4)

async def main():
    t0 = time.perf_counter()
    r = await ag2.arun("go", session_id="b")
    dt = time.perf_counter()-t0
    return r, dt
r, dt = asyncio.run(main())
print("  结果顺序:", [x["result"] for x in r.tool_calls])
print(f"  4 个 0.3s 工具总耗时: {dt:.2f}s (>0.9 表示串行，~0.3 表示并发)")

print()
print("="*70)
print("[C] EvalRunner 用例默认 session_id 是否互相隔离（注释称每例独立）")
from nanoagent.evals import EvalRunner, EvalCase
c1 = EvalCase(name="c1"); c2 = EvalCase(name="c2")
print("  c1.session_id =", c1.session_id, " c2.session_id =", c2.session_id)
print("  >>> 默认是否共享同一会话:", c1.session_id == c2.session_id)

print()
print("="*70)
print("[D] Pipeline/Team 是否并发（按代码为顺序，验证时间）")
from nanoagent.multi import Pipeline
class SlowLLM:
    model="m"
    def __init__(self, out): self.out=out
    def chat(self, messages, tools=None):
        time.sleep(0.2); return LLMResponse(content=self.out)
p = Pipeline([Agent(llm=SlowLLM("a")), Agent(llm=SlowLLM("b")), Agent(llm=SlowLLM("c"))])
t0=time.perf_counter(); out=p.run("x"); dt=time.perf_counter()-t0
print("  输出:", out, f"耗时 {dt:.2f}s（顺序 ~0.6s）")
