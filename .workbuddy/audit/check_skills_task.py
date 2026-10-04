import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent/tests")

print("="*70)
print("[A] parse_frontmatter 边界")
from nanoagent.skills import parse_frontmatter
cases = {
  "标准": "---\nname: foo\ndescription: 做某事\n---\n正文",
  "CRLF": "---\r\nname: bar\r\ndescription: d\r\n---\r\n正文",
  "描述含冒号": "---\nname: x\ndescription: a: b\n---\n正文",
  "缺收尾": "---\nname: y\n正文没有结束分隔",
  "多行描述": "---\nname: z\ndescription: line1\n  line2\n---\n正文",
}
for k,v in cases.items():
    meta, body = parse_frontmatter(v)
    print(f"  {k}: meta={meta} body={body!r}")

print()
print("="*70)
print("[B] SkillRegistry 名字来源 & use_skill 未知技能处理")
from nanoagent.skills import SkillRegistry, Skill
d = Path(tempfile.mkdtemp())
sk = d/"myskill"; sk.mkdir()
(sk/"SKILL.md").write_text("no frontmatter here", encoding="utf-8")
from nanoagent.skills import SkillRegistry
r = SkillRegistry(); loaded = r.add_dir(d)
print("  无 name 的技能名:", r.names())
print("  load 未知:", end=" ")
try: r.load("nope")
except KeyError as e: print("KeyError", e)

print()
print("="*70)
print("[C] TaskRunner 的 [ADD] 重规划与 max_tasks 上限")
from nanoagent.task import TaskRunner, TodoItem
items = [TodoItem(id=1, title="t1")]
raw = "结果\n[ADD] 新任务A\n[ADD] 新任务B\n[ADD] 新任务A\n"
added = TaskRunner._harvest_adds(raw, items, max_tasks=2)
print("  max_tasks=2 时收割:", [(i.id, i.title) for i in added], "（应不超过上限，且去重）")
added2 = TaskRunner._harvest_adds("[ADD] 只有一条", items, max_tasks=10)
print("  正常收割:", [(i.id, i.title) for i in added2])

print()
print("="*70)
print("[D] checkpoints：.json 固定单文件下不同 key 是否互相覆盖")
from nanoagent.checkpoints import JsonFileBackend, resolve_checkpoint
p = Path(tempfile.mkdtemp())/"cp.json"
b = JsonFileBackend(p)
b.save("task", {"goal":"g","items":[]})
b.save("workflow", {"task":"t","plan":"p"})
print("  keys():", b.keys())
print("  load('task'):", b.load("task"), "  <- 被 workflow 覆盖了")
print("  load('workflow'):", b.load("workflow"))

print()
print("="*70)
print("[E] Workflow._is_pass 判定边界")
from nanoagent.multi import Workflow
class Dummy: pass
w = Workflow.__new__(Workflow)
w.FAIL_MARKER="FAIL"; w.pass_marker="PASS"
for s in ["问题清单：无\nPASS", "结论\nNOT PASS", "都在中间 PASS\n末尾无标记", "末尾 FAIL 但整体 PASS\nFAIL", "PASS FAIL\nPASS"]:
    print(f"  {s!r} -> {w._is_pass(s)}")
