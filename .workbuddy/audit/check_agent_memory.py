import sys, time, json, asyncio
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
from nanoagent.agent import Agent
from nanoagent.memory import Memory, SummaryMemory
from nanoagent.llm import LLMResponse, ToolCall
from nanoagent.tools import tool

# 复用测试里的 MockLLM
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent/tests")
from mocks import MockLLM, text_response, tool_response

print("="*70)
print("[A] 工具并行执行：结果顺序与 tool_call_id 对应 + 结果非阻塞")
@tool
def slow(tag: str, delay: float) -> str:
    """慢工具。"""
    time.sleep(delay)
    return f"done-{tag}"

agent = Agent(llm=MockLLM([
    LLMResponse(content="", tool_calls=[
        ToolCall(id="c1", name="slow", arguments={"tag":"A","delay":0.3}),
        ToolCall(id="c2", name="slow", arguments={"tag":"B","delay":0.05}),
        ToolCall(id="c3", name="slow", arguments={"tag":"C","delay":0.1}),
    ]),
    text_response("final"),
]), tools=[slow], parallel_tools=True)
r = agent.run("go", session_id="s1")
print("  tool_calls 记录:", [(x["arguments"]["tag"], x["result"]) for x in r.tool_calls])
msgs = agent.llm.calls[-1]["messages"]
roles = [(m["role"], m.get("tool_call_id"), (m.get("content") or "")[:12]) for m in msgs if m["role"] in ("tool","assistant")]
print("  回填消息:", roles)

print()
print("="*70)
print("[B] 同一 agent 连续 run 两次：第二轮 messages 是否含第一轮历史（且无污染）")
agent2 = Agent(llm=MockLLM([text_response("第一次"), text_response("第二次")]),
               memory=Memory(max_messages=50))
agent2.run("你好", session_id="d")
agent2.run("再说一次", session_id="d")
m2 = agent2.llm.calls[-1]["messages"]
print("  第二轮发给模型的 roles:", [x["role"] for x in m2])
print("  内容:", [x.get("content") for x in m2])

print()
print("="*70)
print("[C] SummaryMemory 仅在 max_tokens 触发时是否裁剪（keep_recent 保护导致 no-op）")
class FakeSum:
    model="m"
    def chat(self, messages, tools=None):
        return LLMResponse(content="摘要内容")
sm = SummaryMemory(max_messages=100, keep_recent=6, max_tokens=50, llm=FakeSum())
for i in range(8):
    sm.add("s", "user", "x"*40)   # 每条约10-40 token
    sm.add("s", "assistant", "y"*40)
print("  tokens:", sm.tokens("s"), " 配置上限:", sm.max_tokens)
print("  历史条数:", len(sm.history("s")), " 摘要:", repr(sm.summary("s"))[:40])
print("  >>> 是否仍超 token 上限:", sm.tokens("s") > sm.max_tokens)

print()
print("="*70)
print("[D] Memory 滑动窗口裁剪后消息是否合法（是否会留下孤立 tool 消息）")
mm = Memory(max_messages=3)
for i in range(6):
    mm.add("t", "user", f"u{i}")
    mm.add("t", "assistant", f"a{i}")
print("  历史:", [(m["role"], m["content"]) for m in mm.history("t")])
