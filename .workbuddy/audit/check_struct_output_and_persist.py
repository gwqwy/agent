import sys, os, json, tempfile
from pathlib import Path
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent/tests")
from nanoagent.agent import Agent, OutputValidationError
from nanoagent.llm import LLMResponse
from nanoagent.memory import Memory
from mocks import MockLLM, text_response
from pydantic import BaseModel

print("="*70)
print("[A] 结构化输出：首次非 JSON，第二次修正 —— 消息序列与结果")
class Out(BaseModel):
    name: str
    age: int
ag = Agent(llm=MockLLM([text_response("不是 JSON 的回答"), text_response('{"name":"Tom","age":3}')]),
           response_model=Out)
r = ag.run("给我结构化", session_id="o")
print("  output:", r.output)
print("  第二次调用带 tools 吗:", ag.llm.calls[-1]["tools"])
print("  第二次调用消息 roles:", [m["role"] for m in ag.llm.calls[-1]["messages"]])

print()
print("[B] 结构化输出：两次都失败 → 抛 OutputValidationError？")
ag2 = Agent(llm=MockLLM([text_response("bad"), text_response("still bad")]), response_model=Out)
try:
    ag2.run("x", session_id="o2")
    print("  未抛异常（不符合预期）")
except OutputValidationError as e:
    print("  OutputValidationError:", str(e)[:80])
except Exception as e:
    print("  其他异常:", type(e).__name__, e)

print()
print("="*70)
print("[C] Memory 持久化：损坏文件是否静默丢历史")
d = Path(tempfile.mkdtemp())
pf = d/"mem.json"
m = Memory(persist_path=pf)
m.add("s","user","你好"); m.add("s","assistant","你好呀"); m.save()
print("  正常保存后加载:", Memory(persist_path=pf).history("s"))
pf.write_text('{"s": [{"role": "user"', encoding="utf-8")  # 截断的损坏文件
m2 = Memory(persist_path=pf)
print("  损坏文件加载 history:", m2.history("s"), "（静默变空，无告警）")

print()
print("="*70)
print("[D] Memory.save 是否原子（非原子写，崩溃会损坏文件）")
import inspect
src = inspect.getsource(Memory.save)
print("  save 用 write_text 直接覆盖:", "write_text" in src, "；有无临时文件/rename:", ("tmp" in src or "rename" in src or "os.replace" in src))

print()
print("="*70)
print("[E] 配置优先级：真实环境变量 vs .env（setdefault 意味真实 env 优先）")
os.environ["NANOAGENT_MODEL"] = "ENV_MODEL"
os.chdir(r"E:/文件/编程文件/agent/nanoagent")  # 让 .env 可见
from nanoagent.config import settings, load_dotenv
load_dotenv(".env")
print("  环境变量 NANOAGENT_MODEL=ENV_MODEL，.env 里是 deepseek-flash")
print("  settings()['model'] =", settings()["model"], "（ENV 优先则正确）")

print()
print("="*70)
print("[F] config.settings 缺字段：无 .env 时是否给默认值（不崩）")
os.environ.pop("NANOAGENT_BASE_URL", None)
import importlib, nanoagent.config as cfg
print("  settings keys:", list(cfg.settings().keys()))
