# 工作区文件索引（FILE_INDEX）

> **工作区**：`E:\文件\编程文件\agent`　|　**主题**：Agent + 中文编程语言
> **索引规模**：<!--STATS-->（自动统计）
> **明细来源**：`.workbuddy/file-index/parts/*.md`（六份分片，全字段）　|　**机读索引**：`.workbuddy/file-index/file-index.json`
> **重新生成**：`python .workbuddy/file-index/build_index.py`
> **本文件第 1–4 章为手工维护**（源：`.workbuddy/file-index/_master_header.md`），第 5–7 章为自动生成——**不要直接改速查表**。

---

## 0. 怎么用这份索引

改动或查找任何文件前，**先定位、再动手**：

```bash
# 关键词检索（跨路径/用途/关键内容/依赖/备注）
python .workbuddy/file-index/query.py desktop --full

# 改某个文件前：它的影响面有多大？
python .workbuddy/file-index/query.py --used-by nanoagent/nanoagent/tools.py

# 它依赖了谁？
python .workbuddy/file-index/query.py --deps sahou-harness/harness/desktop.py

# 按项目过滤 / 机读输出
python .workbuddy/file-index/query.py 文件区 --project sahou-harness
python .workbuddy/file-index/query.py --json ws_tree
```

工作流约定：**检索索引 → 读第 3 章判断波及范围 → 改文件 → 同步改分片（`parts/*.md`）→ 重跑 `build_index.py`**。
索引与实际不符时，以**代码为准**，并顺手修分片——索引的价值全在准确性。

---

## 1. 工作区总览

三个项目围绕同一条主线咬合：**「用中文编程语言（卅）写东西」+「用 Agent 干活」**。

| 项目 | 语言 | 定位 | 规模 | 版本控制 |
|---|---|---|---|---|
| `nanoagent/` | Python | 从零手写的**轻量 Agent 框架**，可读懂的教学级实现 | 25 个核心模块 + `rag/` 子包 5 个 + 17 个示例 + 24 个测试文件（314 条用例） | ✅ 本地 git → `github.com/gwqwy/nanoagent`（分支 `main`，带历史）· MIT · CI |
| `sahou/` | Go | 「卅」**中文入门编程语言**的完整工具链（解释器/转译器/LSP/格式化/打包） | `internal/` 9 个包 + 18 个纯 saho 标准库包 + 17 篇中文文档 + 10 套 bash 回归脚本 | ✅ `github.com/gwqwy/sahou` |
| `sahou-harness/` | Python | 「**一切皆插件**」的 agent harness，执行引擎复用 nanoagent | 微内核 + 7 个内置插件 + 2089 行桌面端 + PyInstaller 打包 | ✅ 本地 git → `github.com/gwqwy/sahou-harness`（分支 `main`，无历史）· MIT · CI |

> **推送方式：工作区直推。** `nanoagent/` 与 `sahou-harness/` **自身就是 Git 仓库**（remote 名叫 `nanoagent` /
> `sahou-harness`，**不是 `origin`**），改完代码 `git add -A && git commit && git push <remote> main:main` 即可，
> 不存在「副本同步」问题。两仓库均已成功推送到 GitHub，且**都已配 CI**（`.github/workflows/ci.yml`，
> Python 3.10/3.12/3.14 矩阵）。
> 注意 harness 的 `main` 是**无历史分支**（旧历史 99.6 MB 含 `build_pyi/` 构建垃圾，另存本地 `master`），
> **不要 `git push --all`**（会把 `master` 的垃圾分支一起推上去）。
> 完整推送流程已沉淀为技能 `github-publish-prep`（此前的根目录 `推送说明.md` 已于 2026-09-26 被删除，要点都在本节与技能里）。
>
> **坑：`git commit --amend` 会让本地与远端分叉。** 若提交已推送过又 amend 了（哪怕只改提交信息），
> 新旧 commit 的 SHA 不同，Git 视作两条无关历史 → 推送报 `! [rejected] ... (non-fast-forward)`，
> 提示"your current branch is behind its remote counterpart"。这不是内容冲突，**不要盲目 merge**：
> 先 `git fetch` 看差异，本地那份若是废掉的旧副本，`git reset --hard <remote>/main` 即可对齐。
> 两个仓库均已配置 MIT 许可证（`LICENSE` + `pyproject.toml` 的 `license` 字段 + README 段落）。
>
> **2026-09-26 工作区根清理**：用户删除了 `DEFECT_AUDIT.md`、`推送说明.md` 及根目录 `*.log` 残留
> （索引曾因此报 2 条幽灵，已同步移除对应条目）。
> 审计报告虽删，但**明细与复现脚本仍在** `.workbuddy/audit/`（`nanoagent-defects.md`、`sahou-harness-defects.md`、
> `check_*.py`、`hh_*.py`），`FILE_INDEX.md` §4 仍保留精简版风险清单。

三者关系：`sahou-harness` 把 `nanoagent` 当作**执行引擎**（agent loop 直接复用），再套一层 Cordis 式微内核与桌面 UI；`sahou` 则是另一条独立主线（语言工具链），它与前两者的交集是**命名与理念**（harness 的 CLI 也叫 `sha`），代码层面不互相 import。

关键环境约定：
- 工作区根 `.venv`（Python 3.14.0）已 editable 安装 `nanoagent`，并预装 `faiss-cpu / fastapi / mcp / openai / numpy / opentelemetry / pywin32`。
  2026-09-26 又装了 **`tiktoken`**（连带 `regex / requests / charset_normalizer / urllib3`），目的是让**本地环境与 CI 一致**
  ——CI 装了 tiktoken 走精确 token 计数、本地没装走启发式，曾导致「本地绿、CI 红」；装了之后两边同构。
- **【用户要求·范围限定（2026-09-28 起，长期有效）】**：只修改 **nanoagent 与 sahou-harness**（两者统称「agent」）；
  **sahou 语言主线冻结**——不改动其源码/文档/测试/产物，除非用户明确点名要改 sahou。
  重建分发软件的约定只覆盖 harness（dist/*.exe）；sahou 的 exe/wasm 不再因例行改动重建。
- `sahou` 构建：`go build -o sahou.exe .`（需 Go 1.23+），唯一第三方依赖 `go-webview2`（无 CGO）。
- **【用户要求·每次代码改动后必须重新构建分发软件】（2026-09-28 起）**：
  - 改了 harness 任何源码（含其依赖的 nanoagent）→ 跑 `sahou-harness/tools/build_exe.py` 重建 `dist/sha.exe` + `dist/ShaDesktop.exe`，并冒烟 `sha.exe --version`；
  - 改了 sahou 任何 Go 源码 → `go build -o sahou.exe .` + `set GOOS=js&& set GOARCH=wasm&& go build -o sahou.wasm ./cmd/sahouwasm`，并同步 `examples/响应式/`、`examples/在线体验/` 两份 wasm 副本；
  - 构建/同步放在提交测试之后、收尾汇报之前。
- `sahou-harness` 运行时 profile 在 `~/.sahou-harness/profiles/<名>/`（JSON 配置，**不用 `.env`**）。
- `.mimosa/` 是 hook 状态目录、`.zcodeignore` 是搜索忽略规则（**不要当 `.gitignore` 手改**）——两者都不要清理。

---

## 2. 全局依赖关系（跨项目）

```
                        ┌──────────────────────────────────────────┐
                        │  工作区根 .venv (Python 3.14.0)          │
                        │  nanoagent(editable) + faiss/fastapi/mcp │
                        └───────────────────┬──────────────────────┘
                                            │ 安装
        ┌───────────────────────────────────┴──────────────────────────────┐
        │                                                                  │
┌───────▼────────────────────────┐                       ┌─────────────────▼──────────────────┐
│ nanoagent/  （Agent 框架）     │                       │ sahou-harness/（harness，Python）  │
│                                │  执行引擎复用          │                                    │
│ __init__.py ← 公开 API 面       │◄──────────────────────┤ builtins/chat_loop 直接调 Agent     │
│   │                            │                       │ kernel.py  微内核 ctx.provide/on   │
│   ├─ llm.py ── LLMResponse ──┐ │                       │ cli.py      sha 命令族             │
│   ├─ tools.py ─ Tool/schema ─┤ │                       │ desktop.py  pywebview UI（2089 行） │
│   ├─ memory.py ─ 窗口/摘要    │ │                       │ loader.py   插件发现                │
│   ├─ agent.py  ← 编排中枢 ────┘ │                       │ __init__.py ← 唯一对外 API 面       │
│   │   ▲                        │                       └────────────────────────────────────┘
│   │   │ 被驱动                  │
│   ├─ multi.py（Pipeline/Team/Workflow）                                    
│   ├─ task.py（TaskRunner）─────────────────┐                
│   ├─ guardrails.py / media.py / tracing.py │ 统一复用
│   ├─ bootstrap.py → plugins.py → skills.py │ checkpoints.resolve_checkpoint
│   ├─ coding.py / browser.py / mcp.py       │
│   ├─ evals.py / observability.py           │
│   └─ cli.py / server.py / manage.py ───────┘
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ sahou/（卅语言工具链，Go，独立主线）                                 │
│                                                                      │
│  main.go（子命令分派）                                               │
│    ├─ run/repl   → lexer.Tokenize → parser.Parse → interp.Run        │
│    ├─ build      → transpile.Build → JS                              │
│    ├─ 打包/pack  → 生成临时 Go 工程 → go build → 单文件 exe          │
│    ├─ fmt        → format.Source（仅缩进重排）                       │
│    ├─ lsp        → lsp.Run（stdio JSON-RPC，补全复用 interp）        │
│    └─ tokens/ast → dump（ast.go）                                    │
│                                                                      │
│  共享契约（改一处必须五处同步）：                                     │
│    parser 的 AST 类型 ← lexer / interp / transpile / ast.go         │
│    value.go 的数值语义（big.Rat）← builtins.go ←→ transpile.builtinJS│
│    stonesrc.FS ← stonesfs.go(本地 embed) / cmd/sahouwasm/stones.go   │
│                                                                      │
│  stones/（18 个纯 saho 标准库）═══手工同步═══> cmd/sahouwasm/stones/  │
└──────────────────────────────────────────────────────────────────────┘
```

### nanoagent 内部分层（越靠下越底层，无内部依赖）

| 层 | 模块 |
|---|---|
| L0 叶子 | `config.py`、`tracing.py`、`errs`（Go 侧对应物） |
| L1 基础能力 | `llm.py`、`tools.py`、`memory.py`、`anthropic_llm.py` |
| L2 核心编排 | `agent.py`（**唯一中枢**） |
| L3 能力扩展 | `coding.py`、`browser.py`、`mcp.py`、`mcp_server.py`、`skills.py`、`plugins.py`、`media.py`、`guardrails.py`、`rag/*` |
| L4 编排/任务/持久化 | `multi.py`、`task.py`、`evals.py`、`checkpoints.py`、`observability.py` |
| L5 生态装配 | `bootstrap.py`、`manage.py` |
| L6 入口 | `cli.py`、`server.py` |

### sahou 包级依赖方向

```
main.go ─┬─> internal/encodesrc（读文件·编码嗅探）
         ├─> internal/lexer ──> internal/parser（AST 定义在此）
         ├─> internal/interp ──> internal/errs
         │        └─ stonesrc.FS（模块解析三方汇合点）<── stonesfs.go / cmd/sahouwasm/stones.go
         ├─> internal/transpile（镜像 interp 的内置函数语义）
         ├─> internal/format（不解析 AST，纯行级重排）
         └─> internal/lsp（诊断走 lexer+parser，补全走 interp 的 Completion*）
```

---

## 3. 变更影响矩阵（改之前先看这张表）

### 3.1 高频改动 → 必须同步的位置

| 你想改的东西 | 必须同步修改 | 验证方式 |
|---|---|---|
| `nanoagent/tools.py` 的 `Tool` / schema 契约 | `coding.py`、`browser.py`、`mcp.py`、`skills.py`、`plugins.py`、`rag/retriever.py`、`multi.py` + 多数测试 | `run_all_tests.py` |
| `nanoagent/agent.py`（loop / 流式 / 记忆写入） | `multi.py`、`task.py`、`bootstrap.py`、`cli.py`、`server.py` + 9 个 test 文件 | 同上 |
| `nanoagent/llm.py` 的 `LLMResponse` / `ToolCall` | `tools.py`、`anthropic_llm.py`、`memory.py`、`tests/mocks.py`（跨模块数据契约） | 同上 |
| `nanoagent/skills.py` / `plugins.py` 装配协议 | `bootstrap.py`、`manage.py`、`examples/11_plugins.py` | `test_skills.py` / `test_plugins.py` / `test_bootstrap.py` |
| `nanoagent/mcp.py` 配置格式 | `bootstrap.py`（读 `mcpServers`）、`~/.sahou-harness` 的 mcp 配置 | `test_bootstrap.py` |
| `nanoagent/*` 的测试支撑文件 | 注意 `nanoagent/build/lib/nanoagent/*` 是**副本**，改它不生效 | 改完确认路径 |
| `sahou` 的 AST 节点定义（`internal/parser`） | `lexer` / `interp` / `transpile` / 顶层 `ast.go` —— **五处同步** | `go build ./...` + `tests/run.sh` |
| `sahou` 数值语义（`interp/value.go`，big.Rat） | `builtins.go` 与 `transpile.go` 的 `builtinJS` 镜像 | `tests/run.sh` |
| `sahou` 内建函数/错误文案 | `tests/cases/*.out`（正向输出）、`*.err`（错误信息）**字节级快照** | `tests/run.sh` |
| `sahou/internal/interp` 的 `loadModule` | `transpile.collectModules`、`lsp`、`stonesrc` 三处模块解析 | `tests/modules.sh` / `packages.sh` |
| `sahou/stones/` 任一标准库包 | **手工同步** `sahou/cmd/sahouwasm/stones/`（18 包已 md5 一致，无同步脚本） | `tests/stdlib.sh` / `wasm.sh` |
| `sahou/editors/shared/language.json` | **必须跑** `node editors/sync-shared.js` 刷新 `vscode/sahou/data/language.json` | 手动检查副本 |
| `sahou` 任何 Go 源码 | **必须重新构建** `sahou.exe` / `sahou.wasm`，否则测试跑的是旧二进制 | `tests/build.sh` |
| `sahou` 的 Go 版本升级 | `wasm_exec.js` **三份副本**（根 + `examples/响应式/` + `examples/在线体验/`） | `tests/wasm.sh` |
| `sahou` 的 `页面/page` 模块用到的 DOM API | `tests/domstub.js` 与 `tests/domstub.mjs`（CJS/ESM 双副本） | `tests/fullstack.sh` |
| `sahou/.gitattributes`（LF 强制） | **不要动**——碰它会让 Windows 上全套快照比对失败 | `tests/run_all.sh` |
| `sahou-harness/harness/kernel.py` 的 `Context` API | 7 个内置插件的 `register.py`（`ctx.provide/on/effect` 契约） | `run_tests.py` |
| `sahou-harness/harness/cli.py` / `config.py`（profile 结构） | `desktop.py`、plugins、`~/.sahou-harness/profiles/*/config.json` | `tests/test_harness.py` |
| `sahou-harness` 任何源码 | **必须重新打包** `dist/sha.exe` / `ShaDesktop.exe`，否则分发物是旧代码 | `build_exe.py` |
| `nanoagent/examples/09_workflow_with_tools.py` 的 `_safe_path` | `nanoagent/tests/test_workflow_tools.py`（**唯一被测试直接引用的示例**） | `test_workflow_tools.py` |

### 3.2 常见任务 → 从哪个文件开始看

| 任务 | 起点文件 |
|---|---|
| 改 agent 循环 / 工具执行顺序 | `nanoagent/nanoagent/agent.py` |
| 加一个工具 | `nanoagent/nanoagent/tools.py`（`@tool`）→ `examples/02_custom_tools.py` |
| 接一家新模型厂商 | `nanoagent/nanoagent/anthropic_llm.py`（协议适配范式）→ `examples/15` |
| 上下文太长 / 记忆策略 | `nanoagent/nanoagent/memory.py`（窗口 / token / 摘要） |
| 多 agent 编排 | `nanoagent/nanoagent/multi.py`（Pipeline / Team / Workflow） |
| 让 agent 自主拆解长任务 | `nanoagent/nanoagent/task.py`（TaskRunner + checkpoint） |
| 装插件 / 技能 / MCP | `nanoagent/nanoagent/bootstrap.py` → `plugins.py` → `skills.py` |
| 发布成 HTTP 服务 | `nanoagent/nanoagent/server.py`（含 SSE 端点） |
| 语言语法/关键字 | `sahou/docs/02-语言规范.md` → `sahou/internal/lexer/lexer.go` |
| 加一个内置函数 | `sahou/internal/interp/builtins.go` + `transpile` 镜像 + `tests/cases` |
| 加一个标准库包（stones） | `sahou/stones/<新包>/main.saho` + 同步 `cmd/sahouwasm/stones/` + 文档 `10-纯sahou标准库包.md` |
| 网页 / UI 能力 | `sahou/internal/interp/uimod.go`、`pagemod_js.go`、`reactive.go` |
| 网络 / 数据库 | `sahou/internal/interp/netmod.go`、`dbmod.go` |
| 编辑器语言支持 | `sahou/editors/shared/language.json` → `sync-shared.js` → `extension.js` |
| harness 桌面端 UI | `sahou-harness/harness/desktop.py`（HTML/CSS/JS 全在一个文件） |
| harness 插件机制 | `sahou-harness/harness/kernel.py` + `loader.py` |

---

## 4. 已知问题与风险清单

按"改代码前必须知道"的优先级排列。

> **✅ 修复状态（2026-09-26 第二轮）**：本章列出的全部缺陷（N-01～N-23、H-01～H-09、P2 各项）**均已修复并补回归用例**，明细见 `DEFECT_AUDIT.md` §8「修复执行记录」。
> 两项目全量测试全绿：**nanoagent 312 条 / sahou-harness 48 条**（相对审计基线 302 / 41 各新增 10 / 7 条）。
> 下方各条保留**原始缺陷描述**作为知识沉淀（"为什么曾经是错的"），条目内的「修复：」为该条的落点。

### 4.1 真实缺陷（已修复，保留描述供参考）

> **完整缺陷审计报告：`DEFECT_AUDIT.md`（工作区根）** —— 2026-09-26 全量审计，含每条的真实复现输出。
> 明细：`.workbuddy/audit/nanoagent-defects.md`（P0×2/P1×6/P2×15）、`.workbuddy/audit/sahou-harness-defects.md`（P0×3/P1×6/P2×20）
> 审计时测试基线：nanoagent 302 条全绿、sahou-harness 41 条全绿 —— **5 个 P0 全部未被覆盖**（该测试盲区已在修复轮次补齐，见 `DEFECT_AUDIT.md` §8）。

**P0（已全部实测复现，已修复）**

1. **[H-02] 桌面端右侧文件区无法展开 = `desktop.py:531` 漏写 `.resolve()`（用户报的 bug，已定根因）**
   `root = Path(ws)` 未 resolve 而 `target = (root/subpath).resolve()` 已 resolve → `target.relative_to(root)` 在**相对工作区**下必抛 `ValueError` → 一律返回「路径越出工作区」。
   触发条件：`host.workspace` 为相对路径。`cli.py:43` 的 `--workspace` 默认就是 `"."`，`desktop.py:2076` 仅在 config 已有有效 `workspace` 时才覆盖 → **新 profile ／ 终端 `sha desktop` 必现**；开发机因 config 存了绝对路径而不复现。
   **前端是清白的**（已用无头 Edge 真鼠标点击排除：无重复 id、无遮挡 `hitIsSelf=true`、绝对工作区下点击正常、`window.onerror` 为空）。
   修复：`desktop.py:531` → `root = Path(ws).resolve()`；加固 `cli.py:32` 与 `desktop.py:2077`。回归测试：相对工作区下 `ws_tree("sub")["ok"] is True` 且 `ws_tree("..")["ok"] is False`。
   关联：`desktop.py:526-552`、`cli.py:32,43`。

2. **[H-01] 权限门 fail-open（安全）**
   `tools_shell/register.py:18-25`、`tools_fs/register.py:44-52` 是「等值比较 + 无 else」→ `permissions.shell` 取 `"Deny"/"deny␣"/"no"/"AsK"/"ALLOW"/None/0/True` 等**9 种非规范值全部绕过确认门并执行命令**；仅 `ask`/`deny` 受控。
   另一处：`config.py:18,28` 的默认 `permissions` **只有 `shell` 没有 `fs`**，而 `tools_fs` 读 `.get("fs","allow")` → **默认配置下写文件无门控**。
   修复：改白名单 + 默认拒绝（`mode != "allow"` 一律走 ask/deny）；`load_config()` 归一化非法值并告警。

3. **[N-01] 工作区沙箱可被 glob `../` 越狱（安全，两项目共有）**
   `nanoagent/coding.py:211`（`list_files`）与 `:234`（`search_code`）把模型可控 `pattern` 直接交给 `self.root.glob(pattern)`，`pathlib` 允许模式含 `..` → 传 `"../*"`、`"../*.txt"` 即可**列出并读出工作区外文件内容**，绕过 `_safe_path`。
   **`sahou-harness` 的 `tools_fs/register.py` 的 `list_files` 有同样写法**，建议一并修。
   修复：对每个命中项调 `self._safe_path(path)` 兜底。

4. **[H-03] 配置非原子写 + 损坏后静默回落默认值（数据丢失）**
   `harness/config.py:51-69`：`save_config` 直接 `write_text` 截断写（无原子替换/无锁），`update_config` 是读-改-写，桌面端每个 js_api 调用都在独立线程 → 实测 4 线程 ×40 自增只得 14（期望 160）。
   更严重：config.json 损坏一次 → `load_config()` **静默**返回 `DEFAULT_CONFIG`（不抛异常、不告警）→ **下次写回就把用户的 models/api_key/workspaces 全抹掉**。
   修复：临时文件 + `os.replace`；`update_config` 加锁；解析失败**必须抛错或备份原文件告警**。

5. **[N-02] trace 写 `"type"` 读 `"event"` → 可观测性整体静默失效**
   `tracing.py:46` 写 `"type"`，`observability.py:44,74,131,134` 读 `event.get("event")` → `trace_summary` 的 llm/tool/token 统计**恒为 0**、`trace_report` 事件列恒空、OTel span 全叫 `nanoagent.event`。
   被 `tests/test_roadmap.py:70-102` 掩盖：该测试**手写** `{"event":"llm_call"}` 直接喂 `trace_summary`，从不经过 `Tracer`。
   修复：`tracing.py:46` 改 `"event": event_type`；测试改为「用 `Tracer` 真实写文件 → 读回」。

6. **[N-03] 工具 schema 在 `from __future__ import annotations` 下类型全错**
   `tools.py:47-71` 不解析字符串注解 → 凡用 future import 的模块，`int/float/bool/list` **全部退化成 `string`**。
   **影响面：nanoagent 30 个模块里 28 个中招**（含 `coding.py`、`browser.py`），harness 的 `tools_shell`/`tools_fs` 也全中。实测 `coding.py` 的 `read_file(start_line/end_line)`、`edit_file(replace_all)`、`run_command(timeout)` 数值/布尔参数全变 string；模型照 schema 传 `"2"` → `TypeError: unsupported operand type(s) for -: 'str' and 'int'`（coding 工具直接崩）。
   修复：用 `typing.get_type_hints(fn, include_extras=True)` 解析，或对注解字符串做映射表 + 处理 `X|None`/`Optional[X]`/`List[X]`。**改一处，修好两项目全部工具。**

**P1（要点，详情见 `DEFECT_AUDIT.md` §2.2 / §3.2）**

7. **[H-04 = N-07] `ctx.on()` 的 disposer 未入账本** → 插件卸载后**幽灵监听器仍在触发**（实测触发计数 1→3）。两套 mini-Cordis 内核同源缺陷。修复：`on()` 内 `self._disposers.append(dispose)`。
8. **[H-05] `Harness.deactivate` 重建服务表时丢掉 `services["models"]`** → 卸载任意插件后 `service("models")` 消失（实测）。`kernel.py:261-264` vs `242-245` 不对称。
9. **[H-08] REPL 引用不存在的 `host.harness`** → `/plugins` 与**未知命令必抛 `AttributeError`**（实测）。`builtins/repl/register.py:19,36`，应为 `host.collect_commands()` / `host.list()`。
10. **[H-09 / P2#10] `AnthropicLLM` 缺 `total_usage`/`context_window`** → 桌面端用量/上下文对 Anthropic 恒空；被 `test_desktop.py:148` 用 `FakeLLM` 断言成「期望行为」而掩盖。
11. **[N-04] 同步 `Agent.run` 调异步工具静默返回 coroutine 垃圾串**（MCP 工具必中）。
12. **[N-05] Workflow 审查把末行 `NOT PASS` 误判为通过**（含 `PASS` 子串）。
13. **[N-06] `SummaryMemory` 的 token 上限形同虚设**（`keep_recent` 保护导致裁剪 no-op）。
14. **[N-08] `EvalRunner` 用例默认共用 session**，用例间记忆互相污染。
15. **[N-16] `browser.py` 的 Playwright 同步 API 在 `ThreadPoolExecutor` 中跨线程使用** → 并行工具必报线程错误（`agent.py:181-183` 默认 `parallel_tools=True`）。
16. **[H-06] `install_plugin` 热激活用目录名当插件名** → 静默失败却返回 `ok: true`。
17. **[H-07] `load_config` 浅合并 + 无类型校验**：`permissions` 丢键、写成 list 直接崩。

### 4.2 安全与合规

3. **API Key 明文落盘**
   - `nanoagent/.env` 内含**真实可用的 API Key 明文**（`NANOAGENT_API_KEY=sk-4fd5…`）。
   - `~/.sahou-harness/profiles/default/config.json` 同为明文密钥，且其 `workspace` 指向本工作区、权限为 `shell: allow` / `fs: ask`。
   建议：改用环境变量注入；若仓库要公开，先轮换密钥。

### 4.3 一致性隐患（"改了一处忘了另一处"）

4. **多副本无同步机制**（全部靠手工，且已确认当前内容一致）：
   - `sahou/stones/*` ↔ `sahou/cmd/sahouwasm/stones/*`（18 个包，md5 全一致）
   - `sahou/wasm_exec.js` ↔ `examples/响应式/` ↔ `examples/在线体验/`（3 份）
   - `sahou/tests/domstub.js` ↔ `domstub.mjs`（CJS/ESM）
   - `sahou/LICENSE` ↔ `editors/vscode/sahou/LICENSE`
   - `sahou/assets/*.svg` ↔ `editors/vscode/sahou/icons/*`
   - `editors/vscode/sahou/data/language.json`（有 `sync-shared.js` 可同步，但需**记得跑**）
5. **构建产物与源码解耦**：`sahou.exe` / `sahou.wasm` / `dist/*.exe` 都在库里，改源码不重建 = 测试与分发跑的是旧代码。这是本项目最容易踩的坑。
6. **`nanoagent/build/lib/nanoagent/*` 是 setuptools 副本**，在里面改代码不会生效。

### 4.4 测试覆盖盲区

> **2026-09-26 审计结论：5 个 P0 一个都没被覆盖，且 343 条测试全绿。** 测试构造方式系统性地绕开了缺陷触发条件 —— 详见 `DEFECT_AUDIT.md` §6 的「缺陷 → 相关测试 → 为什么没抓到」对照表。最典型的三种：
> - **测试用规范值**：权限门只测 `allow/ask/deny`，从不喂 `"Deny"`/`None`/`0`（H-01 漏网）
> - **测试提前把条件消掉了**：`test_ws_tree_lists_and_jails` 先调 `set_workspace` 把工作区 `resolve()` 成绝对，永远不会走到未 resolve 的分支（H-02 漏网）
> - **测试自己造数据绕过生产代码**：`test_roadmap.py` 手写 `{"event":...}` 喂 `trace_summary`，从不经过 `Tracer`（N-02 漏网）
>
> 其余：`serve_ui_preview.py` 的 mock `ws_tree` 只回一层固定 4 项 → 逐层展开从未被自动化验证；REPL 插件、`ctx.on` 回收、`deactivate` 服务表重建、`AnthropicLLM` 真实路径、并发 config 读写**全部零测试**。

7. **完全无测试**：`nanoagent/nanoagent/config.py`、`nanoagent/nanoagent/manage.py`、`sahou-harness` 的 REPL 插件。
8. **仅部分覆盖**：`llm.py`（只测了 `_with_retry`，真实 HTTP 路径全靠 Mock）、`cli.py`（只测 `parse_args`，交互循环未测）、`browser.py` / `mcp_server.py` / `rag/faiss_store.py`（可选依赖缺失即整体跳过）。
9. **跳过守卫不一致**：`tests/test_ecosystem.py::SSEEndpointTests` 在方法内 `import fastapi.testclient` 却**没有 skip 守卫**，缺 fastapi 时直接报错而非跳过；`test_faiss.py` / `test_rag.py` 顶层 `import numpy` 为硬依赖。
10. **「只验证不崩」型断言**：`test_otel_export_or_graceful`（未装 otel 时 `except ImportError: pass`，实际什么都没验证）、`test_builtin_plugins_all_activate`（只断言 6 个插件 ACTIVE，不校验提供物可用）、`RagRerankTests`（只断言 `len(hits)==2`）。
11. **测试入口双坑**：`sahou-harness/tests/` 无 `__init__.py`，`python -m unittest discover` 直接报 `Start directory is not importable`，必须走 `run_tests.py`；而 `run_all_tests.py`/`run_tests.py`/`smoke_desktop.py` 都把 `sys.path` 写成**绝对路径硬编码**，换机器即失效。
12. `nanoagent/na_test_out.log` 里的 3 个 error 是历史遗留（缺 `mcp`/`fastapi`）——根 `.venv` 已装齐，2026-09-26 复跑 **302 条全绿**。

### 4.5 文档漂移

11. `nanoagent/README.md` 与代码不一致：README 写 `TaskRunner(..., checkpoint_path=...)`，实际参数名是 `checkpoint`；README"已知限制"称 TaskRunner 不支持执行中重规划，但 `task.py` 的 `_harvest_adds` **实际支持** `[ADD]` 重规划。
12. `sahou/docs/` 存在多口径漂移（stones 包数、关键字/内置函数数量、合集文档篇数在不同章节写法不一）；`docs/卅语言文档合集.md` 是 `docs/build合集.mjs` 由 18 篇分章**自动拼接**而成（2 万余行），**它明确声明不是事实来源**——冲突时以 `00-设计决策简报.md`（唯一事实来源）与各分篇为准。
13. `sahou-harness/README.md` 的插件契约描述与 `kernel.py` 实际 API 需要人工核对（桌面端章节尤其）。

### 4.6 工程卫生

14. **`nanoagent/` 与 `sahou-harness/` 都不是 git 仓库**——没有任何版本保护，误改无法回滚，也无法用 `git log/blame` 追溯「哪次改动引入的缺陷」。建议各自 `git init`。工作区里唯一的 git 仓库是 `sahou/`。
15. **绝对路径硬编码**（换机器/换目录即失效）：`nanoagent/run_all_tests.py`、`sahou-harness/run_tests.py:5-6`、`sahou-harness/smoke_desktop.py:7`。应统一改 `Path(__file__).resolve().parent`。
16. 可清理项：`nanoagent/build/`、`nanoagent/x.db`、各级 `*.log`、`sahou-harness/build_pyi/`（含两个约 98 KB 的 `xref-*.html`）、`sahou-harness/_diag/`（临时诊断工装）。
    **但要保留** `sahou/editors/vscode/sahou-language-0.3.0.vsix`——`editors/tools/packvsix.py` 以它为 manifest 模板，删了打包脚本就失效（见 §3.1）。
17. **`.workbuddy/audit/` 是 2026-09-26 审计的复现脚本与原始输出**（`check_*.py` / `hh_*.py` / `probe_out*.json`，共 223 KB）。**建议保留**：它们就是上述 P0/P1 的证据，重跑即可复核；审计期间产生的 454 MB Edge profile 垃圾已清理。
18. `sahou-harness/_diag/`（含 `server.py`/`probe*.py`）是上一轮排查 H-02 时的开发工装，**已被本轮审计取代**，可清理。
