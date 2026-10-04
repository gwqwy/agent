import sys, os, tempfile, shutil
sys.path.insert(0, r"E:/文件/编程文件/agent/nanoagent")
from nanoagent.coding import CodingWorkspace, SandboxViolation
from pathlib import Path

base = Path(r"E:/文件/编程文件/agent/.workbuddy/audit/glob_ws")
if base.exists(): shutil.rmtree(base)
root = base / "sandbox"; root.mkdir(parents=True)
(root / "inside.txt").write_text("inside-secret", encoding="utf-8")
# 工作区外文件
(base / "outside_secret.txt").write_text("OUTSIDE-LEAKED-CONTENT", encoding="utf-8")

ws = CodingWorkspace(root=root)
print("root =", ws.root)
print()
print("[1] _safe_path 对 '../outside_secret.txt' 是否拒绝：")
try:
    ws.read_file("../outside_secret.txt")
    print("   未被拒绝（读到了）")
except SandboxViolation as e:
    print("   SandboxViolation:", e)
except FileNotFoundError as e:
    print("   FileNotFoundError:", e)

print()
print("[2] list_files(pattern='../*') 是否越界列出：")
try:
    out = ws.list_files(pattern="../*")
    print("   返回:", repr(out))
except Exception as e:
    print("   异常:", type(e).__name__, e)

print()
print("[3] list_files(pattern='../../*')：")
try:
    out = ws.list_files(pattern="../../*")
    print("   返回:", repr(out)[:400])
except Exception as e:
    print("   异常:", type(e).__name__, e)

print()
print("[4] search_code(query='OUTSIDE', pattern='../*.txt') 是否读到界外内容：")
try:
    out = ws.search_code(query="OUTSIDE", pattern="../*.txt")
    print("   返回:", repr(out))
except Exception as e:
    print("   异常:", type(e).__name__, e)

print()
print("[5] list_files 绝对 glob 尝试:")
try:
    out = ws.list_files(pattern="E:/文件/编程文件/agent/.workbuddy/audit/glob_ws/*.txt")
    print("   返回:", repr(out)[:300])
except Exception as e:
    print("   异常:", type(e).__name__, e)
