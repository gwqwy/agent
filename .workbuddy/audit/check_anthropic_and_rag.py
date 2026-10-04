import sys, json
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
import numpy as np

print("="*70)
print("[A] to_anthropic_messages：工具调用序列转换是否合法 & id 对应")
from nanoagent.anthropic_llm import to_anthropic_messages, parse_sse_event, finalize_stream
msgs = [
    {"role":"system","content":"sys"},
    {"role":"user","content":"hi"},
    {"role":"assistant","content":"","tool_calls":[
        {"id":"t1","type":"function","function":{"name":"f","arguments":'{"a":1}'}},
        {"id":"t2","type":"function","function":{"name":"g","arguments":'{"b":2}'}}]},
    {"role":"tool","tool_call_id":"t1","content":"r1"},
    {"role":"tool","tool_call_id":"t2","content":"r2"},
    {"role":"assistant","content":"final"},
]
system, out = to_anthropic_messages(msgs)
print("  system:", system)
for m in out:
    print("  ", json.dumps(m, ensure_ascii=False))

print()
print("="*70)
print("[B] Anthropic SSE 流：tool_use 的 id/name/args 累积是否正确")
state = {"blocks": {}, "usage": {}}
events = [
    {"type":"message_start","message":{"usage":{"input_tokens":5}}},
    {"type":"content_block_start","index":0,"content_block":{"type":"tool_use","id":"tu1","name":"search"}},
    {"type":"content_block_delta","index":0,"delta":{"type":"input_json_delta","partial_json":'{"q":'}},
    {"type":"content_block_delta","index":0,"delta":{"type":"input_json_delta","partial_json":'"py"}'}},
    {"type":"content_block_start","index":1,"content_block":{"type":"text"}},
    {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"hello"}},
    {"type":"message_delta","usage":{"output_tokens":9}},
]
for e in events:
    parse_sse_event(e, state)
resp = finalize_stream(state)
print("  content:", resp.content, "tool_calls:", [(t.id,t.name,t.arguments) for t in resp.tool_calls], "usage:", resp.usage)

print()
print("="*70)
print("[C] RAG: numpy 与 faiss 后端 top-k / 归一化 / where 过滤一致性")
from nanoagent.rag.store import VectorStore
from nanoagent.rag.faiss_store import FaissVectorStore
rng = np.random.default_rng(0)
X = rng.standard_normal((6, 8)).astype(np.float32)
texts = [f"doc{i}" for i in range(6)]
meta = [{"src":"a"} if i%2==0 else {"src":"b"} for i in range(6)]
ns = VectorStore(); ns.add(texts, X, [dict(m) for m in meta])
try:
    fs = FaissVectorStore(); fs.add(texts, X, [dict(m) for m in meta])
    have_faiss = True
except Exception as e:
    have_faiss = False; print("  faiss 不可用:", e)
q = rng.standard_normal(8).astype(np.float32)
n_hits = ns.search(q, k=3)
print("  numpy top3:", [(h["text"], round(h["score"],4)) for h in n_hits])
if have_faiss:
    f_hits = fs.search(q, k=3)
    print("  faiss top3:", [(h["text"], round(h["score"],4)) for h in f_hits])
    print("  >>> 顺序一致:", [h['text'] for h in n_hits]==[h['text'] for h in f_hits])
    nw = ns.search(q, k=2, where={"src":"b"}); fw = fs.search(q, k=2, where={"src":"b"})
    print("  numpy where=b:", [h['text'] for h in nw])
    print("  faiss where=b:", [h['text'] for h in fw])
    print("  >>> where 一致:", [h['text'] for h in nw]==[h['text'] for h in fw])

print()
print("[D] 零向量查询 / 维度不一致")
zv = np.zeros(8, dtype=np.float32)
print("  numpy 零向量:", ns.search(zv, k=3))
if have_faiss:
    print("  faiss 零向量:", fs.search(zv, k=3))
print("  numpy 维度错:", end=" ")
try: ns.search(np.zeros(3,dtype=np.float32))
except Exception as e: print(type(e).__name__, e)

print()
print("="*70)
print("[E] split_text 边界")
from nanoagent.rag.chunking import split_text
print("  空文本:", split_text(""))
print("  仅换行:", split_text("\n\n\n"))
print("  无分隔符超长(1200):", len(split_text("中"*1200)))
print("  中文短段聚合:", split_text("短句一。\n短句二。\n短句三。", chunk_size=5, overlap=1))
