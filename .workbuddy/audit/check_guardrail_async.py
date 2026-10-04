import sys, asyncio
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent/tests")
from nanoagent.agent import Agent
from nanoagent.guardrails import Guardrails, Guardrail, GuardrailViolation, llm_guardrail
from mocks import MockLLM, text_response

print("[A] 异步护栏用于同步 run()")
async def aguard(text):
    """异步护栏。"""
    return None

a = Agent(llm=MockLLM([text_response("ok")]), input_guardrails=[aguard])
try:
    a.run("hi")
    print("  未拦截")
except GuardrailViolation as e:
    print("  GuardrailViolation:", e)
except TypeError as e:
    print("  TypeError（非 fail-closed 语义）:", e)
except Exception as e:
    print("  ", type(e).__name__, e)

print()
print("[B] 异步 agent 用同步 chat 的 LLMGuardrail 是否会整体拒绝（fail-closed）")
class AsyncOnlyLLM:
    model="m"
    async def achat(self, messages, tools=None):
        from nanoagent.llm import LLMResponse
        return LLMResponse(content='{"pass": true, "reason": "ok"}')
g = llm_guardrail(AsyncOnlyLLM(), "判断")
r = g.check("内容")
print("  同步 check 结果:", r)
