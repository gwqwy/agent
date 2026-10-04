#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作区文件索引构建器（南京路径硬编码为本工作区，迁移目录需改 ROOT）。

职责：
  1. 解析 .workbuddy/file-index/parts/*.md 分片（明细来源，唯一事实来源）
  2. 归一化为结构化条目 -> .workbuddy/file-index/file-index.json
  3. 与磁盘真实文件清单比对覆盖度，暴露"未收录 / 幽灵"文件
  4. 生成工作区根目录 FILE_INDEX.md（主索引：总览 + 全量速查表 + 明细分片导航）

用法：
  python build_index.py            # 构建 json + FILE_INDEX.md
  python build_index.py --check    # 只做覆盖度检查，不写文件
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\文件\编程文件\agent")
IDXDIR = ROOT / ".workbuddy" / "file-index"
PARTS = IDXDIR / "parts"
OUT_MD = ROOT / "FILE_INDEX.md"
OUT_JSON = IDXDIR / "file-index.json"
MASTER_HEADER = IDXDIR / "_master_header.md"

PART_META = [
    ("01-nanoagent-core.md", "nanoagent", "nanoagent · 核心源码", 1),
    ("02-nanoagent-tests-examples.md", "nanoagent", "nanoagent · 测试 / 示例 / 打包元数据", 2),
    ("03-sahou-compiler.md", "sahou", "sahou · 编译器、内建模块与测试脚本", 3),
    ("04-sahou-docs-eco.md", "sahou", "sahou · 文档、stones 标准库、示例、编辑器", 4),
    ("05-sahou-harness.md", "sahou-harness", "sahou-harness · 微内核、桌面端、插件、打包", 5),
    ("06-workspace-and-assets.md", "workspace", "工作区根 / 资产 / 构建产物 / 补充条目", 6),
]

PROJECT_LABEL = {
    "nanoagent": "nanoagent —— 轻量 Python Agent 框架",
    "sahou": "sahou —— 「卅」中文编程语言（Go 工具链）",
    "sahou-harness": "sahou-harness —— 「一切皆插件」的 agent harness",
    "workspace": "工作区根 —— 环境、资产与构建产物",
}

_EXT = (
    r"py|go|md|json|toml|txt|sh|saho|js|mjs|html|css|yml|yaml|spec|mod|sum|"
    r"out|err|log|cfg|ini|svg|vsix|db|ico|env|example|wasm|"
    r"gitignore|gitattributes|vscodeignore|zcodeignore|typed|in"
)
ENTRY_RE = re.compile(
    r"^[\w\-./\u4e00-\u9fa5*]*(?:\*|\.(?:" + _EXT + r")|/(?:LICENSE|NOTICE|PKG-INFO))$"
)
# 无反引号时的"前导路径"抽取：遇到空白或左括号即停止
LEAD_PATH_RE = re.compile(r"^[^\s（(]+")
HEAD_RE = re.compile(r"^###\s+(.*)$")
# 允许的"标题尾部残料"：仅分隔符/括号，或整体被括号包裹
SEP_CHARS = set(" /、，,（）()·-—*：:")
FIELD_RE = re.compile(r"^-\s+\*\*(?P<key>[^*]+?)\*\*\s*[:：]?\s*(?P<val>.*)$")

KEY_ALIASES = {
    "用途": "purpose",
    "关键内容": "key_content",
    "关键内容（导出api）": "key_content",
    "关键内容（导出API）": "key_content",
    "关键内容（导出）": "key_content",
    "对外接口": "api",
    "导出接口": "api",
    "依赖": "deps",
    "被依赖": "used_by",
    "影响范围": "impact",
    "备注": "notes",
}

SKIP_DIRS = {
    ".git", ".venv", "__pycache__", "node_modules", ".mimosa", ".zcode",
    "edgeprofile", "logs",
    # 缓存/构建产物目录（2026-09-27 增补：ruff/mypy/打包/egg-info 的本地缓存）
    ".ruff_cache", ".mypy_cache", ".pytest_cache", "build", "dist",
    "sahou_harness.egg-info", "nanoagent.egg-info",
}
SKIP_FILE_SUFFIX = (".pyc",)


def split_head(title: str):
    """从 ### 标题中抽出「文件路径」与「尾部残料」。

    规则：优先取第一个反引号内容，否则取前导路径 token（遇空白/左括号停止）。
    仅当残料为空、纯分隔符、或整体被括号包裹时，才认为这是一条文件条目
    （用于排除 `### 6.4 loader.py 如何发现并加载插件` 这类小节标题）。
    """
    bt = re.search(r"`([^`]+)`", title)
    if bt:
        cand = bt.group(1).strip().strip("`")
        rest = title.replace(bt.group(0), "", 1)
    else:
        m = LEAD_PATH_RE.match(title)
        if not m:
            return None, None
        cand = m.group(0)
        rest = title[len(cand):]
    rest = rest.replace("`", "").strip()
    rest_ok = (
        rest == ""
        or set(rest) <= SEP_CHARS
        or (rest.startswith(("（", "(")) and rest.endswith(("）", ")")))
    )
    if not rest_ok:
        return None, None
    return cand, rest


def parse_part(path: Path):
    entries, cur = [], None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = HEAD_RE.match(raw)
        if m:
            cand, _rest = split_head(m.group(1).strip())
            if cand and ENTRY_RE.match(cand):
                if cur:
                    entries.append(cur)
                cur = {"path": cand, "fields": {}}
            else:
                if cur:
                    entries.append(cur)
                    cur = None
            continue
        if cur is not None:
            fm = FIELD_RE.match(raw)
            if fm:
                norm = KEY_ALIASES.get(fm.group("key").strip())
                if norm:
                    cur["fields"].setdefault(norm, []).append(fm.group("val").strip())
                    cur["_last"] = norm
                else:
                    cur["fields"].setdefault("other", []).append(
                        f"**{fm.group('key').strip()}**：{fm.group('val').strip()}")
                    cur["_last"] = "other"
            elif raw.strip() and cur.get("_last"):
                cur["fields"][cur["_last"]].append(raw.strip())
    if cur:
        entries.append(cur)
    return entries


def norm_path(p: str) -> str:
    p = p.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p


def collect_disk():
    disk = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel = Path(dirpath).relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        for fn in filenames:
            if fn.endswith(SKIP_FILE_SUFFIX):
                continue
            rp = (rel / fn).as_posix() if str(rel) != "." else fn
            disk.add(rp)
    return disk


def oneline(s: str, limit: int = 0) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s.replace("|", "／")).strip()
    s = re.sub(r"^\*\*", "", s)
    if limit and len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return s


def main() -> int:
    check_only = "--check" in sys.argv
    raw_all, part_stats = [], []

    for fname, proj, label, order in PART_META:
        f = PARTS / fname
        if not f.exists():
            print(f"[WARN] 缺少分片：{fname}")
            continue
        kept = []
        for e in parse_part(f):
            fields = {k: "\n".join(v).strip() for k, v in e["fields"].items()}
            kept.append({
                "path": norm_path(e["path"]),
                "project": proj,
                "purpose": fields.get("purpose", ""),
                "key_content": fields.get("key_content", ""),
                "api": fields.get("api", ""),
                "deps": fields.get("deps", ""),
                "used_by": fields.get("used_by", ""),
                "impact": fields.get("impact", ""),
                "notes": fields.get("notes", ""),
                "extra": fields.get("other", ""),
                "part": fname,
            })
        raw_all.extend(kept)
        part_stats.append({"file": fname, "project": proj, "label": label,
                           "count": len(kept), "order": order})
        print(f"[OK] {fname:34} 条目 {len(kept):3d}  <- {label}")

    by_path = {}
    for e in raw_all:
        score = sum(len(e.get(k, "")) for k in
                    ("purpose", "key_content", "api", "deps", "used_by", "impact", "notes"))
        e["_score"] = score
        if e["path"] not in by_path or score > by_path[e["path"]]["_score"]:
            by_path[e["path"]] = e
    entries = sorted(by_path.values(), key=lambda x: (x["project"], x["path"]))

    # ---- 覆盖度 ----
    disk = collect_disk()
    patterns = [e["path"] for e in entries if "*" in e["path"]]
    indexed = {e["path"] for e in entries if "*" not in e["path"]}
    matched, missing = set(), []
    for d in sorted(disk):
        if d in indexed or any(fnmatch.fnmatch(d, p) for p in patterns):
            matched.add(d)
        else:
            missing.append(d)
    ghost = sorted(p for p in indexed if p not in disk)

    total = len(disk)
    print()
    print(f"磁盘候选文件（过滤 .git/.venv/缓存）: {total}")
    print(f"索引条目（含通配，去重后）        : {len(entries)}  （其中通配条目 {len(patterns)}）")
    print(f"  覆盖磁盘文件                    : {len(matched)}  ({len(matched)/max(total,1)*100:.1f}%)")
    print(f"  未覆盖                          : {len(missing)}")
    print(f"  幽灵条目（索引有磁盘无）        : {len(ghost)}")
    for g in ghost:
        print("  !", g)
    for m in missing:
        print("  +", m)

    if check_only:
        return 0

    payload = {
        "generated_by": "build_index.py",
        "root": str(ROOT),
        "total_entries": len(entries),
        "parts": part_stats,
        "coverage": {"disk_files": total, "indexed": len(entries),
                     "matched": len(matched), "missing": missing, "ghost": ghost},
        "entries": [{k: v for k, v in e.items() if k != "_score"} for e in entries],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[WRITE] {OUT_JSON}")

    # ---- 生成 FILE_INDEX.md ----
    header = MASTER_HEADER.read_text(encoding="utf-8") if MASTER_HEADER.exists() else ""
    stats = (f"**{len(entries)} 条条目**（含 {len(patterns)} 条通配聚合）/ "
             f"覆盖 **{len(matched)}/{total}** 个候选文件（{len(matched)/max(total,1)*100:.1f}%）")
    header = header.replace("<!--STATS-->", stats)
    lines = [header.rstrip(), ""]

    lines += ["## 5. 全量文件速查表", "",
              "> 列为：`文件` | `用途` | `关键依赖` | `改动波及`（均截断，完整字段见第 7 节对应分片）。",
              "> 通配条目（`*`）代表一整组同类文件。", ""]
    for proj in ("workspace", "nanoagent", "sahou", "sahou-harness"):
        grp = [e for e in entries if e["project"] == proj]
        if not grp:
            continue
        lines += [f"### 5.{'1234'[('workspace','nanoagent','sahou','sahou-harness').index(proj)]} "
                  f"{PROJECT_LABEL[proj]}（{len(grp)} 条）", "",
                  "| 文件 | 用途 | 关键依赖 | 改动波及 |",
                  "|---|---|---|---|"]
        for e in grp:
            p = f"`{e['path']}`"
            lines.append("| {} | {} | {} | {} |".format(
                p, oneline(e["purpose"], 90), oneline(e["deps"], 70), oneline(e["impact"], 60)))
        lines.append("")

    lines += ["## 6. 覆盖度报告", "",
              f"- 磁盘候选文件（已排除 `.git` / `.venv` / `__pycache__` / `node_modules`，含构建产物）：**{total}**",
              f"- 索引条目：**{len(entries)}**（含 {len(patterns)} 条通配聚合条目）",
              f"- 覆盖磁盘文件：**{len(matched)}**（{len(matched)/max(total,1)*100:.1f}%）",
              f"- 未覆盖：**{len(missing)}**　幽灵条目：**{len(ghost)}**", ""]
    if missing:
        lines += ["未覆盖清单：", ""] + [f"- `{m}`" for m in missing] + [""]
    if ghost:
        lines += ["幽灵条目（索引记录但磁盘不存在，需核对）：", ""] + [f"- `{g}`" for g in ghost] + [""]

    lines += ["## 7. 明细索引导航（全字段）", "",
              "| 分片 | 覆盖范围 | 条目数 |", "|---|---|---|"]
    for ps in sorted(part_stats, key=lambda x: x["order"]):
        lines.append(f"| `parts/{ps['file']}` | {ps['label']} | {ps['count']} |")
    lines += ["", "每个条目含完整字段：用途 / 关键内容 / 对外接口 / 依赖 / 被依赖 / 影响范围 / 备注。", ""]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[WRITE] {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
