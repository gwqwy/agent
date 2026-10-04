#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作区文件索引检索器。

改动/查找某个文件前先跑它，快速定位目标文件与其关联影响范围。

用法示例：
  python query.py desktop              # 关键词检索（路径/用途/关键内容/依赖/备注）
  python query.py 文件区 --project sahou-harness
  python query.py ws_tree --full       # 输出完整字段（含影响范围、备注）
  python query.py --deps nanoagent/nanoagent/agent.py      # 它依赖谁
  python query.py --used-by nanoagent/nanoagent/tools.py   # 谁依赖它（反向影响面）
  python query.py --path agent.py      # 仅按路径匹配
  python query.py --missing            # 查看索引未覆盖的文件
  python query.py --json desktop       # 机读输出
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IDX = Path(__file__).resolve().parent / "file-index.json"


def load():
    if not IDX.exists():
        sys.exit(f"未找到索引：{IDX}\n请先运行 build_index.py")
    return json.loads(IDX.read_text(encoding="utf-8"))


def hit(e, kw, field):
    hay = {
        "path": e["path"],
        "purpose": e["purpose"],
        "key": e["key_content"],
        "deps": e["deps"],
        "notes": e["notes"],
    }
    if field and field != "all":
        hay = {field: hay.get(field, "")}
    blob = " ".join(hay.values()).lower()
    return all(k.lower() in blob for k in kw)


def show(e, full):
    print("=" * 78)
    print(f"【{e['path']}】  ({e['project']})")
    print(f"  用途    : {e['purpose'] or '—'}")
    if e.get("key_content"):
        print(f"  关键内容: {e['key_content']}")
    if e.get("api"):
        print(f"  对外接口: {e['api']}")
    if full:
        if e.get("deps"):
            print(f"  依赖    : {e['deps']}")
        if e.get("used_by"):
            print(f"  被依赖  : {e['used_by']}")
        if e.get("impact"):
            print(f"  影响范围: {e['impact']}")
        if e.get("notes"):
            print(f"  备注    : {e['notes']}")
        if e.get("extra"):
            print(f"  其它    : {e['extra']}")
    else:
        if e.get("deps"):
            print(f"  依赖    : {e['deps'][:160]}")
        if e.get("impact"):
            print(f"  影响范围: {e['impact'][:160]}")


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True, description="工作区文件索引检索器")
    ap.add_argument("keywords", nargs="*", help="关键词（多个为 AND）")
    ap.add_argument("--field", default="all",
                    choices=["all", "path", "purpose", "key", "deps", "notes"])
    ap.add_argument("--project", default=None,
                    choices=["workspace", "nanoagent", "sahou", "sahou-harness"])
    ap.add_argument("--full", action="store_true", help="输出完整字段")
    ap.add_argument("--path", default=None, help="按路径子串精确定位")
    ap.add_argument("--deps", default=None, help="查看该文件依赖了谁")
    ap.add_argument("--used-by", dest="used_by", default=None, help="查看谁依赖该文件")
    ap.add_argument("--missing", action="store_true", help="列出索引未覆盖的文件")
    ap.add_argument("--json", action="store_true", help="机读输出")
    ap.add_argument("--limit", type=int, default=25)
    a = ap.parse_args()

    data = load()
    entries = data["entries"]

    if a.missing:
        cov = data["coverage"]
        print(f"磁盘 {cov['disk_files']} / 索引 {cov['indexed']} / 覆盖 {cov['matched']}")
        for m in cov["missing"]:
            print("  未覆盖:", m)
        for g in cov["ghost"]:
            print("  幽灵  :", g)
        return 0

    def find(path_sub):
        for e in entries:
            if e["path"] == path_sub or e["path"].endswith("/" + path_sub):
                return e
        return None

    if a.path:
        sel = [e for e in entries if a.path.lower() in e["path"].lower()]
    elif a.deps or a.used_by:
        target = find(a.deps or a.used_by)
        if not target:
            sys.exit(f"索引中找不到：{a.deps or a.used_by}")
        key = "deps" if a.deps else "used_by"
        sel = [target]
        print(f"### {key} —— 目标：{target['path']}")
        print(target[key] or "（索引未记录）")
        print("\n--- 反向关联：被索引中提及该文件的条目 ---")
        needle = Path(target["path"]).name
        rel = [e for e in entries if e is not target and needle in (e["deps"] + e["used_by"])]
        for e in rel[: a.limit]:
            print(f"  · {e['path']}")
        return 0
    elif a.keywords:
        sel = [e for e in entries if hit(e, a.keywords, a.field)]
    else:
        ap.print_help()
        return 0

    if a.project:
        sel = [e for e in sel if e["project"] == a.project]

    sel.sort(key=lambda e: (e["project"], e["path"]))
    if a.json:
        print(json.dumps(sel, ensure_ascii=False, indent=2))
        return 0

    print(f"命中 {len(sel)} 条（共 {len(entries)} 条索引）\n")
    for e in sel[: a.limit]:
        show(e, a.full)
    if len(sel) > a.limit:
        print(f"\n… 另有 {len(sel) - a.limit} 条，可加 --limit 或收窄关键词")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
