# 工作区文件索引（FILE_INDEX）

> **工作区**：`E:\文件\编程文件\agent`　|　**主题**：Agent + 中文编程语言
> **索引规模**：**338 条条目**（含 33 条通配聚合）/ 覆盖 **900/907** 个候选文件（99.2%）（自动统计）
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

## 5. 全量文件速查表

> 列为：`文件` | `用途` | `关键依赖` | `改动波及`（均截断，完整字段见第 7 节对应分片）。
> 通配条目（`*`）代表一整组同类文件。

### 5.1 工作区根 —— 环境、资产与构建产物（50 条）

| 文件 | 用途 | 关键依赖 | 改动波及 |
|---|---|---|---|
| `*.log` | 聚合条目，覆盖根目录残留的安装/运行日志。 | 无。 | 无。 |
| `.aoci/*` | AOCI（仓库认知索引系统）的运行资产目录——baseline、治理配置、账本、事务历史、scope 变更审批工件与 verify 历史。 | 由 aoci CLI/MCP 服务读写，不手工编辑。 | 损坏会触发 AOCI 恢复流程；不要手工改动。 |
| `.audit_tmp/*` | 外部审计报告核对（2026-09-26/27）的**临时**判定与复现脚本目录：`AUDIT_VERDICT.md`（26 条声明的逐条判定：已修复/仍存在/部分成立 + 修复批… | 无。 | 无（不入 git）。 |
| `.mimosa/*` | Agent 运行时（ZCode/WorkBuddy）的 **hook 状态目录**——会话状态、续跑基线、锁。 | 无。 | 删除会丢失会话续跑状态。 |
| `.workbuddy/*` | WorkBuddy/本 Agent 的项目侧数据——记忆、索引构建产物。 | 无。 | `memory/` 丢失会失去跨会话项目上下文。 |
| `.workbuddy/file-index/build_index.py` | 本索引体系的**构建器**——解析分片 → 归一化 JSON → 覆盖度比对 → 生成 `FILE_INDEX.md`。 | 仅标准库（`json/os/re/fnmatch/pathlib`）。 | 改字段名约定或分片格式需同步本脚本；`ROOT` 为硬编码绝对路径，迁移目录需改。 |
| `.workbuddy/file-index/query.py` | 索引**检索器**——按关键词/路径查文件的用途、依赖、被依赖、影响范围。 | `file-index.json`。 | JSON 结构变更需同步。 |
| `.zcode/plans/*.md` | ZCode 会话产出的**计划文档**（plan 模式的落盘结果）。 | 无。 | 无。 |
| `.zcodeignore` | ZCode 工作区的**搜索忽略规则**，只影响 `@` 文件候选 / Command Center / 文件树搜索，不影响文件浏览与 Agent 访问。 | 无（纯配置）。 | 改动会改变未来会话中文件搜索的可达范围；**不要当作 `.gitignore` 手工大改**，否则与同步机制冲突。 |
| `FILE_INDEX.md` | 本索引体系的**主入口**——工作区总览、全局依赖、全量速查表、变更影响矩阵、风险清单与明细分片导航。 | `.workbuddy/file-index/parts/*.md`（明细来源）。 | 明细变化后需重跑 `build_index.py` 重新生成。 |
| `nanoagent/.env` | nanoagent 运行期**真实环境变量文件**（OpenAI 兼容服务的 base_url / api_key / model）。 | 被 `nanoagent/config.py` 的 `settings()` 读取（python-dotenv）。 | 改 model/base_url 会影响全部联网示例行为。 |
| `nanoagent/.env.example` | 配置模板，列出可用的 OpenAI 兼容服务端点。 | 无。 | 新增配置项时需同步更新本文件与 `config.py`。 |
| `nanoagent/.github/workflows/ci.yml` | nanoagent 的 GitHub Actions CI。 | `pyproject.toml` 的 extras 定义。 | 新增可选依赖或测试入口变更需同步；extras 名写错会直接导致 CI 失败。 |
| `nanoagent/.gitignore` | nanoagent 的 Git 忽略规则（第三批工程卫生新增）。 | 无。 | 新增生成物目录时需同步。 |
| `nanoagent/.nanoagent/*` | nanoagent 插件/技能生态的**默认约定目录**（对应 `bootstrap.py` 的 `config_dir`），同时是示例记忆与 checkpoint 的落盘位置。 | 无。 | 向其中放入 `plugin.py` / dsh 插件包 / `SKILL.md` 即被自动装配。 |
| `nanoagent/build/*` | setuptools 的**构建中间产物**——`pip install -e .` 时拷入的 `build/lib/nanoagent/**` 源码副本。 | 由打包流程生成。 | 无。 |
| `sahou-harness/.gitignore` | sahou-harness 的 Git 忽略规则（第三批工程卫生新增）。 | 无。 | 新增生成物目录时需同步。 |
| `sahou-harness/_diag/*` | 为排查"右侧文件区无法展开/点击"而临时搭建的**诊断工装**，不属于产品代码。 | `harness.desktop`、`harness.config`、本机 Edge/pywebview。 | 无。 |
| `sahou-harness/assets/sha.ico` | 桌面端与打包程序的 **Windows 图标**。 | 由 `make_icon.py` 生成。 | 换图标需重跑 `make_icon.py` 并重新打包。 |
| `sahou-harness/build_pyi/*` | PyInstaller **打包中间产物**——分析结果、EXE/PKG 结构、字节码归档与警告/交叉引用报告。 | `build_pyi/*.spec`（`sha.spec` / `ShaDesktop.spec`）。 | 无（重新打包会重建）。 |
| `sahou-harness/dist/*` | PyInstaller 产出的**可执行文件**——`sha.exe`（CLI）与 `ShaDesktop.exe`（桌面端）。 | 由 `build_exe.py` + `build_pyi/*.spec` 生成。 | 改任何 harness 源码后必须重新打包**，否则分发物仍是旧代码。 |
| `sahou/.gitattributes` | 换行符强制统一为 LF** 的关键配置（真·基础设施，不是可选美化）。 | 无。 | 改动或删除会直接让全套一致性测试在 Windows 上失败**（CRLF 检出破坏 heredoc 期望块比对）。 |
| `sahou/.gitignore` | sahou 的 Git 忽略规则。 | 无。 | 新增生成物目录时需同步，避免污染提交。 |
| `sahou/LICENSE` | sahou 项目的开源许可证。 | 无。 | 换证需同步编辑器扩展目录内的副本。 |
| `sahou/assets/*` | 项目品牌图标与 Logo 的矢量源文件（`icon.svg` / `logo.svg` / `sahou-icon.svg` / `sahou-logo.svg`）。 | 无。 | 改图标需重跑 `genicon.py` 刷新扩展图标。 |
| `sahou/cmd/sahouwasm/stones/*/main.saho` | wasm 运行时的内嵌标准库副本**——与 `sahou/stones/` 内容完全一致（18 个包，已逐包 md5 校验相同）。 | 由 `cmd/sahouwasm/stones.go` 通过 `go:embed` 注入。 | 修改 `stones/` 任一包后必须手工同步本目录**，否则"原生跑"与"浏览器跑"行为不一致。 |
| `sahou/editors/sync-shared.js` | 把 `editors/shared/language.json`（编辑器元数据唯一事实来源）**同步**到各编辑器集成的 `data/language.json`。 | `editors/shared/language.json`。 | 新增编辑器集成需在此加目标路径。 |
| `sahou/editors/tools/genicon.py` | 把图标 SVG 的"数据流水线"设计**栅格化**为 VS Code 市场要求的 PNG 图标。 | `editors/vscode/sahou/icons/saho.svg`（几何基准）。 | 改图标设计需同步改本脚本的几何常量。 |
| `sahou/editors/tools/packvsix.py` | 打包 VS Code 扩展**——把 `editors/vscode/sahou/` 组装成 `sahou-language-<版本>.vsix`。 | `editors/vscode/sahou/`、模板 `sahou-language-0.3.0.vsix`。 | 强依赖模板 vsix 存在**；若删掉 0.3.0 产物则打包脚本失效。 |
| `sahou/editors/vscode/sahou-language-*.vsix` | 历史发布的**扩展打包产物**（0.1.0 ~ 1.0.0）。 | 由 `packvsix.py` 或 vsce 生成。 | 删除全部旧 vsix 会让打包脚本失效。 |
| `sahou/editors/vscode/sahou/.vscodeignore` | 扩展打包忽略规则，决定哪些文件不进入 vsix。 | 无。 | 漏写规则会让开发文件被打进发布物。 |
| `sahou/editors/vscode/sahou/LICENSE` | 扩展的许可证副本（打包时映射为 `LICENSE.txt`）。 | `sahou/LICENSE`。 | 改根 LICENSE 需同步本副本。 |
| `sahou/editors/vscode/sahou/data/language.json` | 扩展用的语言元数据**副本**（由 `sync-shared.js` 从 `editors/shared/language.json` 同步）。 | `editors/shared/language.json`。 | 勿手改**，会被下次同步覆盖；应改 shared 版本再同步。 |
| `sahou/editors/vscode/sahou/extension.js` | VS Code 扩展主代码。 | `sahou.exe`（CLI 与 LSP）、`data/language.json`。 | 改 LSP 协议（`internal/lsp/lsp.go`）需同步本文件的客户端解析。 |
| `sahou/editors/vscode/sahou/icons/*` | 扩展图标资源（SVG 源 + `genicon.py` 生成的 PNG，+ 文件图标主题用图标）。 | `assets/*.svg`（品牌源）。 | 换图标需重跑 `genicon.py`。 |
| `sahou/examples/*/sahou.wasm` | 示例页面目录内的 **`sahou.wasm` 副本**（`响应式/`、`在线体验/` 各一份）。 | 由 `cmd/sahouwasm` 构建。 | 重新构建 wasm 后必须同步这两份副本**，否则页面跑的仍是旧解释器。 |
| `sahou/examples/*/wasm_exec.js` | 示例页面目录内的 **`wasm_exec.js` 副本**（`响应式/`、`在线体验/` 各一份）。 | Go 工具链版本。 | 升级 Go 后必须三个副本一起替换**（根目录 + 两个示例目录）。 |
| `sahou/examples/网页/favicon.svg` | 示例网页的站点图标。 | 无。 | 无。 |
| `sahou/examples/计数器.js` | `sahou build` 对 `计数器.saho` 的**转译产物示例**（JS）。 | `examples/计数器.saho`。 | 改转译器后此文件内容会变；它是"转译输出长什么样"的活样例。 |
| `sahou/sahou.*` | sahou 的**构建产物**——Windows 可执行解释器（`sahou.exe`）与 WASM 运行时（`sahou.wasm`）。 | 由 `sahou/main.go` / `sahou/cmd/sahouwasm/main.go` 构建。 | 改任何 Go 源码后必须重新构建**，否则测试跑的是旧二进制（典型的"改了没生效"陷阱）。 |
| `sahou/tests/cases/*.err` | 负向用例（`9xx`，7 个）的**期望报错信息快照**。 | `internal/errs/errs.go` 的错误文案与 `internal/interp` 的报错路径。 | 改错误信息文案会直接打破这些快照**——这是"错误信息即契约"的显式体现。 |
| `sahou/tests/cases/*.out` | 正向用例（`0xx`，19 个）的**期望 stdout 快照**，由 `tests/run.sh` 做字节级比对。 | `sahou.exe` 的实际输出。 | 任何影响正常输出的改动（内建函数、数值格式化、字符串化）都必须同步这些快照**；换行符差异也会导致失败（见 `.git… |
| `sahou/tests/domstub.js` | `sahou build` 产物（JS）的 **Node 测试桩**——模拟最小 DOM，验证 `页面/page` 模块（CJS 版）。 | 无（零依赖桩）。 | `页面/page` 模块用到的新 DOM API 需在本桩补齐，否则 Node 侧测试会失败。 |
| `sahou/tests/domstub.mjs` | 同上的 **ESM 版** DOM 测试桩。 | 无。 | 与 `domstub.js` 需同步维护。 |
| `sahou/tests/modproject/*` | 模块与包管理测试工程**——多文件 import 的验证夹具。 | sahou 模块解析（`internal/interp` 的 `loadModule`）。 | 改模块查找/引入语义需同步期望快照。 |
| `sahou/tests/pack.sh` | 打包单文件 exe** 的回归脚本——验证 `sahou 打包` 能把 `.saho` 编译成独立可执行文件并正常运行。 | `sahou.exe`、`sahou/main.go` 的 `packApp()`。 | 改打包逻辑（内嵌工程生成、`go build` 调用）需同步。 |
| `sahou/tests/playground_check.mjs` | 在线体验页等价测试**——在 Node 里加载 `sahou.wasm`，调用与页面同一入口的全局 `__sahou_run(src)`。 | `sahou/wasm_exec.js`、`sahou/sahou.wasm`。 | 改 wasm 入口或 stones 内嵌逻辑需同步。 |
| `sahou/tests/wasm_reactive.mjs` | WASM 响应式回归测试**——`sahou.wasm` 在 Node 里直接解释 `.saho`，验证格子联动（`格子`）。 | `sahou.wasm`、`wasm_exec.js`。 | 改 `internal/interp/reactive.go` 或 `uimod` 需同步。 |
| `sahou/wasm_exec.js` | Go 官方 **WASM 运行时胶水脚本**（`wasm_exec.js`），浏览器/Node 加载 `sahou.wasm` 必需。 | 与 Go 工具链版本绑定（随 `go` 版本变化）。 | 升级 Go 版本后必须用 `go env GOROOT` 下的同名文件替换所有副本**，否则 wasm 加载失败。 |
| `sahou/留言板.db` | 全栈示例（examples/留言板.saho）运行时生成的嵌入式数据库文件。 | 由留言板示例运行时创建。 | 无。 |

### 5.2 nanoagent —— 轻量 Python Agent 框架（79 条）

| 文件 | 用途 | 关键依赖 | 改动波及 |
|---|---|---|---|
| `nanoagent/LICENSE` | 仓库的开源许可证正文，**MIT License**，版权人 `Copyright (c) 2026 gwqwy`。 | 无。 | 改动措辞等于改法律条款**；若日后改为 Apache-2.0 / GPL 等，必须同时改本文件、`pyproject.… |
| `nanoagent/README.md` | 项目设计意图、模块定位与用法总览，用于核对该包的分层与对外承诺。 | 无 | 用户认知与示例一致性。 |
| `nanoagent/examples/01_simple_chat.py` | 最简单的对话 agent，演示 `Agent.run` 单轮问答。 | `nanoagent.Agent`。 | `Agent` 构造签名、`AgentResult.{content,iterations,usage}` 变更时需同… |
| `nanoagent/examples/02_custom_tools.py` | 用 `@tool` 装饰器定义工具，演示模型自主调用。 | `nanoagent.Agent`、`nanoagent.tool`。 | `tool` 装饰器 schema 生成、`tool_calls` 结构变更时需同步。 |
| `nanoagent/examples/03_memory_sessions.py` | 多会话记忆 + 滑动窗口 + JSON 持久化恢复。 | `nanoagent.Agent`、`nanoagent.Memory`。 | `Memory` 构造参数与 `save()` 返回变更时需同步。 |
| `nanoagent/examples/04_rag.py` | RAG 知识库入库并把检索注册成工具。 | `nanoagent.Agent`、`nanoagent.KnowledgeBase`。 | `KnowledgeBase` 接口、`as_tool()` 工具名变更时需同步。 |
| `nanoagent/examples/05_multi_agent.py` | 多 agent 编排两种范式。 | `nanoagent.Agent/Pipeline/Team`。 | `multi.py` 的 Pipeline/Team 接口变更时需同步。 |
| `nanoagent/examples/06_http_server.py` | 把 agent 发布为 HTTP 服务。 | `uvicorn`、`nanoagent.server.app`。 | `server.py` 的 `app` 导出与路由变更时需同步。 |
| `nanoagent/examples/07_parallel_and_summary.py` | 并行工具执行 + 摘要记忆。 | `nanoagent.Agent/SummaryMemory/tool`。 | 并行执行与摘要压缩逻辑变更时需同步。 |
| `nanoagent/examples/08_workflow.py` | 框架级 Workflow 四角色反馈回路（纯 LLM，无工具）。 | `nanoagent.Agent/Workflow`。 | `multi.py` Workflow 的 PASS 判定与会话隔离变更时需同步。 |
| `nanoagent/examples/09_workflow_with_tools.py` | 工具版工作流，程序员真实读写文件、审查员只读；文件工具做路径越界防护。 | `nanoagent.Agent/Workflow/tool`、`pathlib.Path`。 | 改动本示例的 `_safe_path` 或三个文件工具会直接破坏 `test_workflow_tools.py`。 |
| `nanoagent/examples/10_async_workflow.py` | 异步工作流 + 结构化输出 + checkpoint。 | `nanoagent.Agent/AsyncLLM/Workflow`、`nanoagent.memory.Memory`、`pydant… | 异步 loop、结构化输出校验、checkpoint 落盘/续跑变更时需同步。 |
| `nanoagent/examples/11_plugins.py` | 插件/技能/MCP 一键装配（对齐 dsh）。 | `nanoagent.bootstrap_agent`、`nanoagent.tool`。 | `bootstrap.py`、`plugins.py`、`skills.py` 的装配协议变更时需同步。 |
| `nanoagent/examples/12_task_runner.py` | TaskRunner 自主拆解目标并逐项连续完成。 | `nanoagent.Agent/TaskRunner`、`nanoagent.llm.LLMResponse`。 | `task.py` 规划解析、progress 回调、checkpoint 变更时需同步。 |
| `nanoagent/examples/13_guardrails.py` | 输入/输出安全护栏。 | `nanoagent.Agent/GuardrailResult/GuardrailViolation/*_guardrail`、`nan… | `guardrails.py` 的归一化与四路径集成变更时需同步。 |
| `nanoagent/examples/14_multimodal.py` | 给 agent 发图片（多模态）。 | `nanoagent.Agent/make_png`、`nanoagent.config.settings`。 | `media.py` 的 `image_part/build_user_content` 变更时需同步。 |
| `nanoagent/examples/15_anthropic_llm.py` | Anthropic 协议适配，同一套 Agent 直连 Anthropic 兼容端点。 | `nanoagent.Agent/AnthropicLLM/AsyncLLM/tool`、`nanoagent.config.settin… | `anthropic_llm.py` 协议转换、SSE 解析、工具块转换变更时需同步。 |
| `nanoagent/examples/16_coding_agent.py` | 编程 agent 完整配方。 | `nanoagent.Agent/CODING_INSTRUCTIONS/CodingWorkspace/TaskRunner`、`nan… | `coding.py` 工具集、`task.py` 变更时需同步。 |
| `nanoagent/examples/mcp_entry.py` | MCP 接入入口，让编辑器（Claude Code / Cursor / VS Code / dsh）调用 nanoagent。 | `nanoagent.Agent/serve_mcp`。 | `mcp_server.py` 的 `serve_mcp/create_mcp_server` 变更时需同步。 |
| `nanoagent/nanoagent/__init__.py` | 包的公开 API 面（public surface），集中 re-export 全部上层能力，并定义版本号。 | （本项目）：agent、anthropic_llm、bootstrap、browser、checkpoints、coding、evals、… | 任何新增/删除/改名公开符号都会波及 examples/01~16、tests/*、README 的用法示例，属于最高… |
| `nanoagent/nanoagent/agent.py` | 框架核心——定义 `Agent` 类与 agent loop（组装消息 → 调 LLM → 执行工具并回填 → 循环至终答），是几乎所有上层模块的编排中心。 | `guardrails`、`llm`、`media`、`memory`、`tools`、`tracing` | multi（Pipeline/Team/Workflow）、task（TaskRunner 驱动 Agent）、boo… |
| `nanoagent/nanoagent/anthropic_llm.py` | Anthropic Messages 协议适配器，让框架可直连 Claude / DeepSeek `/anthropic` 端点，与 OpenAI 版 LLM 平级、Agent… | `config.settings`、`llm`（LLMResponse/StreamResult/ToolCall/parse_tool_… | 只影响顶层导出与 Anthropic 场景用例；OpenAI 路径不受影响。 |
| `nanoagent/nanoagent/bootstrap.py` | 一键装配——扫描 `.nanoagent/` 的 plugins/skills/mcp.json，组装成开箱即用的 Agent 并返回装配报告。 | `agent.Agent`、`llm.LLM`、`mcp.MCPManager`/`MCPServer`、`memory.Memory`、… | 生态装配入口；插件/MCP/技能目录约定的唯一编排点。 |
| `nanoagent/nanoagent/browser.py` | 浏览器自动化工具 `BrowserWorkspace`（computer use 的浏览器子集），基于可选依赖 Playwright，懒启动单页面会话。 | `tools.Tool`、`tools.make_tool`；`screenshot` 内延迟 `from .media import i… | 浏览器工具场景。 |
| `nanoagent/nanoagent/checkpoints.py` | 可插拔 checkpoint 后端——把 Workflow/TaskRunner 的持久化抽象成协议，内置 JSON 文件 / SQLite / 内存 / Postgres 四种… | 无本项目导入（stdlib sqlite3 + 可选 psycopg） | Workflow 与 TaskRunner 的续跑能力。 |
| `nanoagent/nanoagent/cli.py` | 命令行 REPL 聊天入口（`python -m nanoagent.cli`），支持流式输出与 `/image` 多模态输入。 | `agent.Agent`、`config.load_dotenv`/`settings`、`llm.LLM`、`media.image_… | 交互式聊天体验；`Parse_args` 单测。 |
| `nanoagent/nanoagent/coding.py` | 编程工具集 `CodingWorkspace`——把 nanoagent 变成编程 agent（文件读写/编辑/搜索/shell/git/后台进程/子 agent），带路径监狱、… | `tools.Tool`、`tools.make_tool` | 编程 agent 场景与 TaskRunner 配合的文件操作。 |
| `nanoagent/nanoagent/config.py` | 配置加载——极简 `.env` 解析 + 环境变量读取，`NANOAGENT_*` 优先、`OPENAI_*` 回退。 | 无本项目导入（stdlib os/pathlib） | 所有模型客户端与 RAG 的配置来源。 |
| `nanoagent/nanoagent/evals.py` | 评估体系——`EvalRunner` 跑用例集，支持 contains / regex / LLM-as-judge 三种判分，报告可存档做回归对比。 | 延迟导入 `tools.ToolRegistry`（run_case）、`agent.extract_json`（_score_judge） | 仅评估链路，与运行时解耦。 |
| `nanoagent/nanoagent/guardrails.py` | 输入/输出安全护栏——规则护栏（关键词/长度/正则）+ LLM 判别护栏，全部 fail-closed，四条执行路径（同步/异步 × 输入/输出）覆盖。 | 无顶层本项目导入；`LLMGuardrail._parse` 延迟 `from .agent import extract_json`（避… | Agent 的输入/输出过滤；失败时抛 `GuardrailViolation` 且不写记忆。 |
| `nanoagent/nanoagent/llm.py` | OpenAI 兼容的 LLM 客户端薄封装（同步 `LLM` + 异步 `AsyncLLM`），全框架统一收敛到 `LLMResponse` 数据结构。 | `config.settings` | 几乎所有模块；`LLMResponse`/`ToolCall` 是跨模块数据契约，改动会同时波及 anthropic_… |
| `nanoagent/nanoagent/manage.py` | 插件/技能/MCP 命令行管理（install/remove/list），对齐 dsh plugin 子命令；`python -m nanoagent.manage`。 | `mcp.MCPManager`、`plugins.PluginManager` | 生态安装管理；改动影响 `bootstrap` 扫描到的目录结构约定。 |
| `nanoagent/nanoagent/mcp.py` | MCP 客户端——通过官方 SDK 接入 stdio/SSE/Streamable HTTP 三种传输的 MCP 服务器，并把 MCP 工具适配成 nanoagent `Tool… | `tools.Tool`；可选第三方 `mcp` | MCP 工具接入与 `bootstrap` 的 MCP 装配。 |
| `nanoagent/nanoagent/mcp_server.py` | 反向集成——把 nanoagent Agent 暴露为 MCP 服务器（stdio），供 Claude Code / dsh 等宿主调用。 | 无本项目导入（延迟导入 `mcp.server.mcpserver.MCPServer`） | 对外暴露 Agent 为 MCP 服务的场景。 |
| `nanoagent/nanoagent/media.py` | 多模态消息构造——把图片源（URL/本地文件/bytes/dict）转成 OpenAI 兼容的 `image_url` content parts。 | 无本项目导入（stdlib base64/struct/zlib/pathlib） | 多模态输入链路与 cli 的 `/image` 命令。 |
| `nanoagent/nanoagent/memory.py` | 会话记忆——多会话消息存储、条数/token 双维裁剪、JSON 持久化，并提供超窗自动摘要的 `SummaryMemory`。 | 无本项目导入（`_summarize` 内延迟 `from .llm import LLM`） | Agent 的记忆出入、cli/server 的会话持久化、SummaryMemory 摘要链路。 |
| `nanoagent/nanoagent/multi.py` | 多 agent 编排——提供 `Pipeline`（顺序流水线）、`Team`（agent-as-tool 委托）、`Workflow`（计划→开发↔审查→汇总，含反馈回路与 c… | `agent.Agent`、`tools.tool`；延迟导入 `checkpoints.resolve_checkpoint` | 多 agent 场景与 Workflow checkpoint 续跑。 |
| `nanoagent/nanoagent/observability.py` | trace JSONL 的可视化——生成单文件 HTML 报告，或导出为 OpenTelemetry spans。 | 无本项目导入（stdlib + 可选 opentelemetry） | 仅 trace 报告/导出功能，与运行时主链路解耦。 |
| `nanoagent/nanoagent/plugins.py` | 插件系统——Python 版 mini-Cordis 内核（ctx/effect/disposer/fiber 状态机）+ 多格式适配器（nanoagent/dsh/mcp-on… | `skills.SkillRegistry`、`tools.Tool`；`_ToolsFacade.register` 内延迟 `from… | 插件装配、bootstrap 报告、manage CLI 的 install/list。 |
| `nanoagent/nanoagent/rag/__init__.py` | RAG 子包入口，re-export 分块/向量库/检索能力。 | `chunking`、`faiss_store`、`retriever`、`store` | RAG 公开 API。 |
| `nanoagent/nanoagent/rag/chunking.py` | 文本分块——为 RAG 入库做准备，段落聚合 + 超长段落带 overlap 硬切。 | 无（纯 stdlib） | RAG 入库分块质量与召回。 |
| `nanoagent/nanoagent/rag/faiss_store.py` | faiss 向量检索后端，与 numpy 版 `VectorStore` 完全同接口可互换（IndexFlatIP + L2 归一化 = 余弦）。 | 无本项目导入（numpy；`faiss` 在 `__init__` 内导入） | 大数据量 RAG 场景。 |
| `nanoagent/nanoagent/rag/retriever.py` | 知识库 `KnowledgeBase`——embedding 入库 + 检索 + 可选 LLM 重排序，并一键变成 Agent 工具。 | `..config.settings`、`..llm.LLM`、`..tools.tool`、`.chunking.split_text`… | RAG 查询与工具化；依赖 OpenAI 兼容 `/embeddings`。 |
| `nanoagent/nanoagent/rag/store.py` | 本地向量库 numpy 后端——暴力余弦相似度检索 + JSON 持久化，并提供后端工厂 `create_store`。 | 无本项目导入（numpy） | RAG 默认后端；两个后端接口需保持一致。 |
| `nanoagent/nanoagent/server.py` | FastAPI 异步 HTTP 服务入口（`/chat`、`/chat/stream`(SSE)、`/sessions`、`/health`），`python -m nanoag… | `agent.Agent`、`config.load_dotenv`/`settings`、`llm.AsyncLLM`/`LLM`、`m… | HTTP 服务能力；SSE 事件格式与 `Agent.arun_stream` 的事件结构强耦合。 |
| `nanoagent/nanoagent/skills.py` | Agent Skills——SKILL.md 渐进式披露（索引注入 system prompt，`use_skill` 按需加载全文）。 | `tools.tool` | 技能体系与插件技能装配；`Agent.enable_skills` 依赖 `list_summary`/`use_sk… |
| `nanoagent/nanoagent/task.py` | `TaskRunner`——把大目标自主拆解成 JSON 任务清单并逐项连续执行（plan-and-execute），全程可 checkpoint 续跑。 | `agent.Agent`、`agent.extract_json`；延迟导入 `checkpoints.resolve_checkpoi… | 连续任务执行与 checkpoint 续跑；编程 agent 示例依赖它。 |
| `nanoagent/nanoagent/tools.py` | 工具定义与注册——`@tool` 装饰器从类型注解 + docstring 自动生成 JSON Schema，`ToolRegistry` 集中管理执行。 | `llm.ToolCall` | 所有带工具的能力（coding/browser/mcp/skills/plugins/rag/agent）都经此层；s… |
| `nanoagent/nanoagent/tracing.py` | 最小可用的 JSONL 事件追踪器，把每次 run、LLM 调用、工具调用写成一行一个 JSON。 | 无本项目导入（stdlib） | 所有带 tracer 的 Agent 运行；observability 读取的 trace 文件格式由本文件决定。 |
| `nanoagent/pyproject.toml` | 项目打包与依赖声明，定义核心依赖与可选依赖组。 | 无 | 任何新增可选依赖/模块必须同步更新，否则用户安装后 ImportError。 |
| `nanoagent/run_all_tests.py` | 一键跑全量测试。 | `unittest`、`sys`。 | 路径硬编码，迁移目录后需改第 4、7 行。 |
| `nanoagent/tests/__init__.py` | 空文件，将 `tests` 标记为 Python 包以支持 `from tests.mocks import ...`。 | 无。 | 不应删除，否则包导入失败。 |
| `nanoagent/tests/mcp_echo_server.py` | 测试用 MCP 服务器（echo / add 两个工具，stdio 传输，mcp 2.x API）。 | `mcp.server.mcpserver.MCPServer`（第三方，顶层导入）。 | `mcp.py` 客户端适配逻辑变更时需同步。 |
| `nanoagent/tests/mocks.py` | 测试共享的 Mock LLM 与响应工厂。 | `nanoagent.llm.LLMResponse/ToolCall`。 | 改动 MockLLM 行为会影响全测试套；`LLMResponse/ToolCall` 字段变更需同步。 |
| `nanoagent/tests/test_agent.py` | 测 `agent.py`（agent loop）。 | `nanoagent.agent.Agent`、`nanoagent.memory.Memory`、`nanoagent.tools.to… | `agent.py` loop/流式/记忆写入行为变更时需同步。 |
| `nanoagent/tests/test_anthropic_llm.py` | 测 `anthropic_llm.py`（协议转换 / SSE 解析 / MockTransport 端到端）。 | `nanoagent.anthropic_llm`（`AnthropicLLM/AsyncAnthropicLLM/finalize_st… | `anthropic_llm.py` 任何协议细节变更都需同步。 |
| `nanoagent/tests/test_async_features.py` | 测异步 agent loop、结构化输出、Workflow checkpoint、MCP 适配/集成。 | `nanoagent.agent.Agent/OutputValidationError/extract_json`、`nanoagent… | `agent.py` 异步路径、`multi.py` checkpoint、`mcp.py` 适配变更时需同步。 |
| `nanoagent/tests/test_audit_fixes.py` | 第二批审计修复（2026-09-27，提交 23094b2）的回归用例：N-03 MCP 握手失败回滚 transport 与 disconnect 双层异常、N-06 stre… | `tests.mocks`；mock LLM 离线运行。 |  |
| `nanoagent/tests/test_bootstrap.py` | 测 `bootstrap.py` 与 `mcp.py` 的 `MCPManager`。 | `nanoagent.bootstrap.{bootstrap_agent,bootstrap_agent_sync}`、`nanoage… | `bootstrap.py` 装配协议、`mcp.py` MCPManager 变更时需同步。 |
| `nanoagent/tests/test_coding.py` | 测 `coding.py`（路径监狱、文件工具、搜索、确认门、Agent 集成）。 | `nanoagent.agent.Agent`、`nanoagent.coding.{CODING_INSTRUCTIONS,Coding… | `coding.py` 任何工具/确认门/沙箱逻辑变更都需同步。 |
| `nanoagent/tests/test_ecosystem.py` | 测最后批次新能力：`evals.py`、`checkpoints.py`、`task.py`（重规划）、`server.py`（SSE 端点）、`llm.py`（重试）。 | `nanoagent.agent.Agent`、`nanoagent.checkpoints.*`、`nanoagent.evals.Ev… | 对应五个模块变更时需同步。 |
| `nanoagent/tests/test_entry.py` | 入口冒烟测试（CLI 参数解析 + HTTP 应用路由）。 | `nanoagent.agent.Agent`、`nanoagent.cli.parse_args`、`nanoagent.memory.… | `cli.py` 参数、`server.py` 路由变更时需同步。 |
| `nanoagent/tests/test_faiss.py` | 测 `rag/faiss_store.py` 并与 `rag/store.py` 的 numpy 后端做一致性对比。 | `nanoagent.rag.{FaissVectorStore,VectorStore,create_store,KnowledgeBa… | 两个 store 后端接口变更时需同步。 |
| `nanoagent/tests/test_guardrails.py` | 测 `guardrails.py` 及与 `agent.py` 的四路径集成。 | `nanoagent.agent.Agent`、`nanoagent.guardrails.*`、`nanoagent.llm.LLMRe… | `guardrails.py` 与 `agent.py` 护栏集成点变更时需同步。 |
| `nanoagent/tests/test_manage.py` | 测 `manage.py` 的技能移除命令（N-20 修复的回归用例）。 | `nanoagent.manage.cmd_remove_skill`、`argparse.Namespace`。 | `manage.py` 的 `remove-skill` 逻辑变更时需同步。 |
| `nanoagent/tests/test_media.py` | 测 `media.py` 及 `agent.py` 的图片参数与记忆行为。 | `nanoagent.agent.Agent`、`nanoagent.media.{build_user_content,image_pa… | `media.py` 编码/嗅探逻辑、`Agent.run(images=...)` 契约变更时需同步。 |
| `nanoagent/tests/test_memory.py` | 测 `memory.py`（滑动窗口/持久化）与 `tracing.py`（JSONL trace）。 | `nanoagent.memory.Memory`、`nanoagent.tracing.Tracer`。 | `memory.py`/`tracing.py` 变更时需同步。 |
| `nanoagent/tests/test_multi.py` | 测 `multi.py`（agent-as-tool 委托、Pipeline、Team）。 | `nanoagent.agent.Agent`、`nanoagent.memory.Memory`、`nanoagent.multi.{P… | `multi.py` 编排逻辑变更时需同步。 |
| `nanoagent/tests/test_parallel.py` | 测 `agent.py` 的并行工具执行。 | `nanoagent.agent.Agent`、`nanoagent.llm.ToolCall`、`nanoagent.memory.Me… | `agent.py` 的 `_execute_tool_calls`、线程池、顺序保持逻辑变更时需同步。 |
| `nanoagent/tests/test_plugins.py` | 测 `plugins.py`（mini-Cordis 内核、格式探测/适配、PluginManager 生命周期）。 | `nanoagent.plugins.*`、`nanoagent.tools.{Tool,tool}`。 | `plugins.py` 内核/适配器/manifest 探测变更时需同步。 |
| `nanoagent/tests/test_rag.py` | 测 `rag/`（分块、向量库余弦检索、KnowledgeBase 工具化）。 | `nanoagent.rag.{KnowledgeBase,VectorStore,split_text}`、`nanoagent.rag… | `rag/chunking.py`、`rag/store.py`、`rag/__init__.py`、`rag/ret… |
| `nanoagent/tests/test_roadmap.py` | Roadmap 批次测试：`mcp_server.py`、`observability.py`、`rag/retriever.py`（重排序）、`browser.py`。 | `nanoagent.agent.Agent`、`nanoagent.observability.{trace_report,trace_… | 对应四模块变更时需同步。 |
| `nanoagent/tests/test_skills.py` | 测 `skills.py`（frontmatter 解析、注册表、渐进式披露、enable_skills）。 | `nanoagent.agent.Agent`、`nanoagent.skills.{Skill,SkillRegistry,parse_… | `skills.py` 解析与注册逻辑变更时需同步。 |
| `nanoagent/tests/test_summary_memory.py` | 测 `memory.py` 的 `SummaryMemory`（触发时机、摘要注入、滚动压缩、持久化）。 | `nanoagent.llm.LLMResponse`、`nanoagent.memory.SummaryMemory`、`tests.m… | `SummaryMemory` 压缩时机与 prompt 组装变更时需同步。 |
| `nanoagent/tests/test_task.py` | 测 `task.py`（规划解析、逐项推进、checkpoint 续跑、异常隔离、异步）。 | `nanoagent.agent.Agent`、`nanoagent.task.{TaskPlanningError,TaskRunner… | `task.py` 规划/执行/持久化逻辑变更时需同步。 |
| `nanoagent/tests/test_token_memory.py` | 测 `memory.py` 的 token 化上下文管理。 | `nanoagent.memory.{Memory,SummaryMemory,_heuristic_estimate,estimate_… | `memory.py` 的 token 估算与自动压缩逻辑变更时需同步。 |
| `nanoagent/tests/test_tools.py` | 测 `tools.py`（schema 生成、docstring 解析、注册表执行、工具名净化）。 | `nanoagent.llm.ToolCall`、`nanoagent.tools.{ToolRegistry,make_tool,san… | `tools.py` schema/净化/执行逻辑变更时需同步。 |
| `nanoagent/tests/test_workflow.py` | 测 `multi.py` 的 `Workflow`（反馈回路、PASS 判定、轮次上限、会话隔离）。 | `nanoagent.agent.Agent`、`nanoagent.memory.Memory`、`nanoagent.multi.{W… | `multi.py` 的 `_is_pass`、会话隔离、角色校验变更时需同步。 |
| `nanoagent/tests/test_workflow_tools.py` | 测 **examples/09** 文件工具的安全（路径越界防护）。 | `importlib.util` 动态加载 `examples/09_workflow_with_tools.py`；运行时把模块的 `W… | 被测对象是示例文件本身**，改动 `examples/09_workflow_with_tools.py` 的 `_s… |

### 5.3 sahou —— 「卅」中文编程语言（Go 工具链）（152 条）

| 文件 | 用途 | 关键依赖 | 改动波及 |
|---|---|---|---|
| `sahou/.github/workflows/ci.yml` | CI 工作流（84 行）。 | `tests/*.sh`、`cmd/sahouwasm`、`stonesfs.go`（内嵌需 wasm）。 | 新增测试脚本/构建步骤需同步本文件与 `.vscode/tasks.json`、`docs/README.md`。 |
| `sahou/.github/workflows/release.yml` | 自动发版工作流（123 行）。 | `CHANGELOG.md`、`sahou.exe` 构建、`editors/vscode/sahou-language-<版本>.vsi… | 发版逻辑/冒烟断言/CHANGELOG 格式变更需同步本文件与 `CHANGELOG.md`、`发布清单.md`。 |
| `sahou/.vscode/tasks.json` | 仓库级 VS Code 任务（31 行）。 | `sahou.exe`、`tests/*.sh`。 | 改测试脚本列表需同步此任务（注意此处**未含** `pack.sh`/`fullstack.sh`/`app.sh`/… |
| `sahou/CHANGELOG.md` | 版本更新说明；Release 工作流按同名小节自动提取。 |  |  |
| `sahou/README.md` | 项目对外说明（定位、能力表、仓库结构、构建测试、版本）。 |  |  |
| `sahou/ast.go` | 以缩进文本打印 AST（`sahou ast` 调试命令）。 | `parser`。 | 仅 `sahou ast` 输出格式。 |
| `sahou/cmd/sahouwasm/main.go` | 浏览器直跑版入口（sahou.wasm），直接解释执行 `.saho`。 | `errs`、`interp`（+ syscall/js）。 | 浏览器解释执行、在线体验、`serve` 壳页。 |
| `sahou/cmd/sahouwasm/stones.go` | 把 wasm 版内嵌 stones 注入 `stonesrc.FS`。 |  |  |
| `sahou/docs/00-设计决策简报.md` | 语言设计的唯一事实来源（Single Source of Truth）**，146 行。明确声明所有其他文档（总览、规范、教程、编译器设计）必须与本文件保持一致，冲突以本文件为准。 | 无（顶层事实来源，不 import 任何文档）。 | 改动 D1–D10 任一条，需同步几乎全套文档 + `editors/shared/language.json` +… |
| `sahou/docs/01-语言设计总览.md` | 把 `00` 简报的结论展开、讲清动机与示例（434 行）。面向：决策者 / 教育者。 | 链接 `00`。正文示例遵循简报第 3 节。 | 改动定位/哲学/对照表；若 `00` 的 D1–D10 或基线示例改动，本章须同步（尤其第 6 节示例速查）。 |
| `sahou/docs/02-语言规范.md` | 语言的可实现规范——词法 / 语法（EBNF）/ 语义 / 标准库 / 报错（1305 行）。面向：**实现者**。 | 引用 `00` 简报；正文提到 `tests/cases` 快照。 | 改关键字表（2.6）需同步 `00` D2、`01` D2、`11` 附录 B、`12`、`editors/share… |
| `sahou/docs/03-入门教程.md` | 零基础渐进教程（1656 行）。面向：**初学者**。 | 链接 `00`；正文示例遵循简报基准写法。 | 作用域规则（"函数内赋值只有函数局域变量"）在 5.3/8.3/10 反复出现，若规范 5.3 改动须全章同步；语法写… |
| `sahou/docs/04-编译器技术设计.md` | Go 解释器/转译器的技术设计（3935 行，最长的实现文档）。面向：**实现者**。 | 引用 `00`、`02` 的 EBNF 与语义；引用 `internal/*` 包设计。 | 实现结构变化（新增包、AST 节点、内置函数）需同步 `README` 实现结构表、`05`/`08` 的转译分节；报… |
| `sahou/docs/05-前端后端扩展设计.md` | v1.1 后端 + v1.5 前端的扩展落地设计（642 行）。面向：实现者 / 决策者。 | 链接 `00`、`02`、`04`。 | `网络`/`页面` API 改动需同步 `06`/`07`/`11`/`14`/`15` 与 `internal/in… |
| `sahou/docs/06-网络模块教程.md` | 后端入门的渐进教程（1110 行）。面向：**初学者**（前置 `03`）。 | 前置 `03`；语义依据 `02`、`05` §2。 | `网络` 字典键名、报错文案变更需同步 `05` §2.3–2.6、`11` 第 13 章、`examples/待办服… |
| `sahou/docs/07-前端模块教程.md` | 前端入门的渐进教程（1149 行）。面向：**初学者**（前置 `03`、`06`）。 | 前置 `03`、`06`；依据 `02` v1、`05` §3。 | `页面` API 变更需同步 `05` §3.5、`11` 第 14 章、`tests/build.sh`、`test… |
| `sahou/docs/08-模块与包管理.md` | v2 模块系统的正式落地文档，把 `05` 的 E2 待决项逐条定案（826 行）。面向：实现者 / 决策者。 | 链接 `00`（D9）、`05`（E2）、`02`（v1 语义底座）。 | 语法/解析顺序变更需同步 `02`（2.6 关键字）、`09`、`11` 第 11 章、`editors/shared… |
| `sahou/docs/09-标准库模块.md` | 说明语言自带的标准库模块有哪些、里面有什么（1147 行）。面向：初学者 / 实现者。 | `08`（其后续）、`02`（v1）、`03`。 | 模块成员变更需同步 `editors/shared/language.json` modules、`syntaxes`… |
| `sahou/docs/10-纯sahou标准库包.md` | 介绍 `stones/` 下十八个纯 sahou 标准库包（73 行，最简短的一章）。面向：**初学者**。 | 引用 `09`（宿主原语）、`08`（包管理）。 | 十八包任一 API 增删改，须同步本章表格 + `editors/shared/language.json` ston… |
| `sahou/docs/11-用户手册.md` | 主教材**式的完整学习手册（7647 行，是单章最长的文档）。面向：**初学者（主教材）**。 | 覆盖 `02`（规范）、`03`（入门）、`06`/`07`（前端后端）、`08`/`09`（模块）、`12`/`13`（管道/响应式）等… | 因其覆盖面最广，任何语言级变更（关键字、内置函数、作用域、语法）都应在此同步**；改附录 A/B 需与 `02` 6.… |
| `sahou/docs/12-管道编程.md` | v3 管道（数据流水线）的专题文档（782 行）。面向：初学者 / 实现者。 | `02`（语义）；提到 stones 包 `列表工具`（`过滤/变换/归约`）为示例。 | `->`/`它` 语义变更需同步 `02`、`11` 第 16 章、`editors/shared/language.… |
| `sahou/docs/13-响应式计算模型.md` | v4 响应式格子与 卅.wasm 直接运行的专题文档（92 行，简短）。面向：初学者 / 实现者。 | `02`；`examples/响应式/价格计算.saho`、`响应式/价格计算.html`。 | 格子语义/绑定 API 变更需同步 `11` 第 17 章、`02`、`examples/响应式/`、`tests/w… |
| `sahou/docs/14-全栈开发.md` | v1.6 全栈专题（表单/会话/静态文件/网页渲染/数据库）（198 行）。面向：初学者 / 实现者。 | `05`、`02`（附 SQL 方言）；`examples/留言板.saho`；`tests/fullstack.sh`。 | 请求字典键/数据库 SQL 子集变更需同步 `02` 附 SQL 方言、`examples/留言板.saho`、`te… |
| `sahou/docs/15-应用开发.md` | v1.7/v1.8 应用开发专题（后端写法 / 写页面 / 桌面 / 手机端）（191 行）。面向：初学者 / 实现者。 | `05`、`07`（转译 JS）；`examples/{桌面应用,手机应用,原生窗口,写页面演示}.saho`；`tests/app.sh… | 应用模块成员变更需同步 `editors/shared/language.json` modules、`example… |
| `sahou/docs/16-功能清单与路线图.md` | 待办功能的唯一清单**，每个版本从这里"领活"（97 行）。面向：全体 / 实现者。 | 引用 `00`（决策）、`04`（性能）、`13`（格子）、`editors/shared/language.json`（L1/T1）。 | 实施任一条目后须回本文件改状态标记，并同步被其"涉及面"列出的文件（如 F1 涉及 internal/transpil… |
| `sahou/docs/README.md` | 整个 sahou 项目的总入口与文档索引页（118 行）。 | 链接 `00`–`16` 各分章与 `../editors/VS_CODE接入指南.md`。 | 改动版本状态、实现结构、命令清单需同步 `04-编译器技术设计.md`（结构）、`CHANGELOG.md`、`.gi… |
| `sahou/docs/build合集.mjs` | 重新生成 `docs/卅语言文档合集.md` 的构建脚本（零依赖 Node，55 行）。 | 读取同目录 18 个分篇 Markdown。 | 新增/删除分章时须同步 `files` 数组与卷首"总目录/怎么读"。 |
| `sahou/docs/卅语言文档合集.md` | `docs/` 分篇文档的**合订本（整合版）**，21658 行 / 约 875 KB，供"一本在手"的完整阅读。**不是事实来源**。 | 正文 = `README.md` + `00`–`16` 的逐字拼接。 | 不要手工编辑正文**；改分章后运行 `node docs/build合集.mjs` 重新生成。 |
| `sahou/docs/发布清单.md` | GitHub 发布操作清单（内部备忘，49 行）。面向：项目维护者。 | 涉及 `LICENSE`、`assets/`、`go.mod`、`tests/wasm.sh`、`CHANGELOG.md` 相关流程。 | 仓库改名/模块路径变更时按本文件步骤执行。 |
| `sahou/editors/README.md` | 编辑器生态总说明（44 行）。面向：编辑器插件开发者。 | `shared/language.json`、`sync-shared.js`、`vscode/sahou/`、`tools/genico… | 新增编辑器/改共享数据流程需同步本文件、`sync-shared.js` targets、`docs/README.m… |
| `sahou/editors/VS_CODE接入指南.md` | 面向普通 VS Code 用户的接入指南（238 行）。面向：VS Code 用户。 | `vscode/sahou/` 各文件、`sahou lsp`、`.vscode/tasks.json`。 | 扩展设置项/命令/诊断行为变更需同步本文件。 |
| `sahou/editors/shared/language.json` | 编辑器元数据的唯一事实来源**（104 行）。面向：所有编辑器集成。 | 与 `docs/00`、`02` 同源（人工维护）。 | 关键字/内置函数/模块/stones 任一变更，须改本文件并运行 `sync-shared.js` 同步到各编辑器目录… |
| `sahou/editors/vscode/sahou/CHANGELOG.md` | VS Code 扩展更新说明（66 行）。 | 与 `docs/` 版本演进对应。 | 扩展每次变更须追加条目；版本号与语言本体同步（当前扩展 1.0.0 = 语言 v1.0.0）。 |
| `sahou/editors/vscode/sahou/language-configuration.json` | 编辑器基础行为配置（76 行）。 | 无。 | 新增块关键字（如新循环/条件关键字）需同步折叠标记；关键字表变更需与之保持一致。 |
| `sahou/editors/vscode/sahou/package.json` | VS Code 扩展清单（132 行）。 | 同目录 `extension.js`、`syntaxes/`、`snippets/`、`saho-icon-theme.json`、`ic… | 命令/设置/键位变更需同步 `extension.js`、`VS_CODE接入指南.md`、`CHANGELOG.md… |
| `sahou/editors/vscode/sahou/saho-icon-theme.json` | VS Code 文件图标主题定义（16 行）。 | `icons/saho-file.svg`。 | 增删文件类型关联需同步。 |
| `sahou/editors/vscode/sahou/snippets/sahou.json` | VS Code 代码片段（114 行，15 个片段）。 | 无（静态片段）。 | 语法/API 写法变更需同步片段（如关键字改名）。 |
| `sahou/editors/vscode/sahou/syntaxes/sahou.tmLanguage.json` | TextMate 语法高亮定义（143 行）。面向：VS Code 用户 / 新编辑器参考。 | 数据口径应来自 `shared/language.json`（但此处为**手工维护的正则列表**，非自动生成）。 | 关键字/内置函数/模块名变更需手工同步此正则**（无生成器，属漂移风险点）。 |
| `sahou/examples/pkgdemo/演示.js` | `pkgdemo/演示.saho` 经 `sahou build` 生成的 JS（保留入库）。 | 由 `演示.saho` 生成。 | 重新 build 覆盖。 |
| `sahou/examples/pkgdemo/演示.saho` | 覆盖全部十八个 stones 包**的演示（在 `examples/pkgdemo/` 子目录里"向上查找"到仓库根的 `stones/`）。 | `stones/` 十八包（向上查找）；`随机` 模块。 | 任一 stones 包 API 变动都可能导致本示例输出变化**，进而影响 `tests/packages.sh` 期… |
| `sahou/examples/乘法表.saho` | 九九乘法表，`00` 简报第 3 节的**基准示例一**。 | 无（纯核心）。 | 作为基准示例，修改它意味着改动语言"标准写法"**，牵动几乎全部文档与快照。 |
| `sahou/examples/入门演示.saho` | 语言核心特性总览演示。 | 核心内置。 | 改语言核心语义需复核本示例；因其被 `build.sh` 与 `release.yml` 依赖，改动需保证可跑通。 |
| `sahou/examples/写页面演示.saho` | v4.2 纯代码写页面（`应用.写页面` 控件 + 事件）的完整可运行示例——"乘法小测"。 | `应用` 模块、`随机` 模块、`页面` 模块 API（`写页面`）。 | `应用.写页面` 控件/事件 API 变更需同步本示例、`15`、`editors/shared/language.j… |
| `sahou/examples/原生窗口.saho` | v1.8 原生窗口（WebView2）示例。 | `网页` 模块、`应用` 模块（`原生窗口`）、`写入文件`。 | `应用.原生窗口` 签名变更需同步本示例与 `15`。 |
| `sahou/examples/响应式/价格计算.html` | 响应式计算器的宿主页（`sahou.wasm` 直接解释 `.saho`）。 | `价格计算.saho`（源码）、`sahou.wasm`（运行时，`tests/wasm.sh` 复制）、`wasm_exec.js`。 | 改元素 `id` 需同步 `价格计算.saho`。 |
| `sahou/examples/响应式/价格计算.saho` | v4 响应式格子示例（改输入 → 结果自动更新，无事件代码）。 | `页面` 模块；`格子` 语法；`响应式/价格计算.html`（宿主）。 | 格子语义/`绑输入/绑定` 变更需同步本示例、`13`、`11` 第 17 章、`tests/wasm_reactiv… |
| `sahou/examples/在线体验/index.html` | 浏览器在线 playground（左写 卅、右看输出，`卅.wasm` 直接解释）。 | `sahou.wasm`（同目录，12.9 MB 运行时副本）、`wasm_exec.js`；`../网页/favicon.svg`。 | `__sahou_run` 接口变更需同步本页 + `cmd/sahouwasm`。 |
| `sahou/examples/小猫.saho` | `00` 简报第 3 节的**基准示例二**（字典代替对象）。 | 核心。 | 基准示例，改动牵动文档与快照。 |
| `sahou/examples/待办服务.saho` | v1.1 网络模块的内存待办 REST 服务。 | `网络` 模块。 | `网络` API 变更需同步本示例、`05`、`06`、`11`、`tests/net.sh`。 |
| `sahou/examples/成绩.saho` | `00` 简报第 3 节的**基准示例三**（尝试/接住与抛出）。 | 核心。 | 基准示例，改动牵动文档与快照。 |
| `sahou/examples/手机应用.saho` | v1.7 手机端示例（局域网 + 添加到主屏幕）。 | `网页`、`应用` 模块。 | `应用.手机` 签名变更需同步本示例与 `15`。 |
| `sahou/examples/桌面应用.saho` | v1.7 桌面应用示例（浏览器壳）。 | `网页`、`应用` 模块。 | `应用.窗口` 签名变更需同步本示例与 `15`。 |
| `sahou/examples/猜数字.saho` | 入门综合项目——猜数字游戏（**模拟猜测列表、不读键盘**，便于自动测试）。 | 核心。 | 若 `03` §11 或 break 语义变更需同步。 |
| `sahou/examples/留言板.saho` | v1.6 全栈综合示例（数据库存留言 + 会话记名字 + 网页渲染 + 表单提交）。 | `数据库`、`网页`、`网络` 模块；`写入文件` 间接。 | 数据库/网页/会话 API 变更需同步本示例、`14`、`tests/fullstack.sh`。 |
| `sahou/examples/网页/index.html` | `网页/演示.saho` 的宿主页面（含计数器/待办/随机金句三个卡片）。 | `演示.js`（构建产物）、`favicon.svg`。 | 改元素 `id`/结构需同步 `演示.saho`。 |
| `sahou/examples/网页/演示.saho` | `sahou build` 转译前端的大型演示（计数器 + 待办清单 + 随机金句），源码用**花括号风格**块。 | `页面`、`随机` 模块；`网页/index.html`（宿主页面）。 | `页面` API 变更需同步本示例 + 宿主 `index.html`。 |
| `sahou/examples/计数器.html` | 计数器页面的宿主 HTML（`<script src="计数器.js">`）。 | `计数器.js`（构建产物）。 | 改元素 `id` 需同步 `计数器.saho`。 |
| `sahou/examples/计数器.saho` | v1.5 前端计数器页面（`页面` 模块 DOM + 事件即函数值）。 | `页面/page` 模块。 | `页面` API 变更需同步本示例、`计数器.html`、`计数器.js`（产物）、`05`/`07`/`11`、`t… |
| `sahou/examples/通讯录.saho` | 命令行通讯录（字典 + 函数 + 文件读写 + 手工拼 JSON）。 | 核心 + 文件内置函数。 | 文件内置函数行为变更需复核。 |
| `sahou/go.mod` | Go 模块定义。 |  |  |
| `sahou/go.sum` | 依赖校验和锁定。 |  |  |
| `sahou/internal/encodesrc/encodesrc.go` | 读源文件并归一为 UTF-8（识别 BOM/UTF-16；非法 UTF-8 给双语提示）。 | os、unicode/utf16、unicode/utf8。 | 所有读源路径（run/build/pack/format/dump/module/lsp 补全）。 |
| `sahou/internal/errs/errs.go` | 双语错误体系（报错即教学）。 | fmt、strings。 | 所有错误文案与退出码；`Exit>=0` 语义贯穿 `in.Run`、`系统.退出`。 |
| `sahou/internal/format/format.go` | 保守格式化（只重排缩进、去行尾空白、压缩空行，不改记号）。 | `lexer`（`KeyWords`）。 | `sahou 格式`；缩进单位 4 空格。 |
| `sahou/internal/interp/appmod.go` | 应用模块 应用/app（桌面窗口 / 手机端 / 打开浏览器 / 写页面转发）。 | `errs`（+ net/http、os/exec、runtime 等）。 | 桌面/手机端本地静态服务、原生窗口入口（依赖 `nativewin_*`）；`app.sh`。 |
| `sahou/internal/interp/bench_test.go` | 解释器基准测试（`go test ./internal/interp -bench .`）。 |  |  |
| `sahou/internal/interp/builtins.go` | 内置函数注册表与实现（30 个含 1 别名），列表/字典成员函数，编辑器补全元数据。 | `encodesrc`、`errs`、`lexer`、`parser`、`stonesrc`。 | 全部内置函数行为、参数绑定、成员方法；补全元数据影响 LSP 与 VS Code 扩展。 |
| `sahou/internal/interp/dbmod.go` | 内置数据库 数据库/db（纯 Go 嵌入式 SQL + JSON 原子落盘）。 | `errs`（+ encoding/json、sort、sync 等）。 | 数据库/全栈能力；JSON 存储格式（`列/自增/行`，数用字符串保精度）；`fullstack.sh`、`分发版自检… |
| `sahou/internal/interp/dbmod_test.go` | 数据库单元测试（自增、聚合、原子落盘重开）。 |  |  |
| `sahou/internal/interp/env.go` | 词法作用域环境（函数作用域 + 顶层）。 | 无本包外依赖（同包 `Value`）。 | 作用域语义（读沿链、写仅当前层，遮蔽不写外层）。 |
| `sahou/internal/interp/htmlmod.go` | 服务端模板渲染模块 网页/html。 | `errs`。 | 模板渲染与转义（防注入）；`fullstack.sh`、`app.sh`、`分发版自检.saho`。 |
| `sahou/internal/interp/interp.go` | 树遍历求值器主引擎：控制流信号、语句/表达式求值、管道、模块加载、赋值、调用。 | `encodesrc`、`errs`、`lexer`、`parser`、`stonesrc`。 | 语言全部运行时语义（作用域、错误传播、模块、管道、响应式、调用链）；改动会波及几乎全部 cases 与 shell 测… |
| `sahou/internal/interp/nativewin_other.go` | 非 Windows 平台的原生窗口降级（改用浏览器 + 事件桥）。 | net/net/http、strings、sync、fmt。 | Linux/macOS 桌面窗口与 `写页面` 事件能力（经浏览器事件桥）。 |
| `sahou/internal/interp/nativewin_windows.go` | Windows 原生窗口实现（WebView2）。 | `github.com/jchv/go-webview2`（+ fmt）。 | Windows 桌面原生窗口；非 Windows 编译时本文件被排除。 |
| `sahou/internal/interp/netmod.go` | 网络模块 HTTP 服务端/客户端 + JSON + 会话；并作为全部模块的**级联注册器**。 | `errs`（+ net/http、encoding/json 等）。间接依赖同包 page/html/db/app/test。 | 网络/后端能力、会话、表单/上传、JSON；网络相关 shell 测试。 |
| `sahou/internal/interp/numbers_alias.go` | 数值内部承载的类型别名。 | `math/big`。 | 极小，仅别名可用性。 |
| `sahou/internal/interp/pagemod_js.go` | 页面模块浏览器宿主版（`syscall/js` 操作 DOM）+ 响应式绑定。 | `errs`（+ syscall/js）。 | 浏览器直跑（sahou.wasm）DOM/事件/响应式；`wasm.sh`。 |
| `sahou/internal/interp/pagemod_std.go` | 页面模块服务端/其它宿主版（全部成员返回"只能在浏览器里用"提示）。 | `errs`。 | 本地解释器里 `页面.*` 的降级行为。 |
| `sahou/internal/interp/reactive.go` | v4 响应式计算模型（格子/依赖图/观察者）。 | `errs`、`lexer`、`parser`。 | 格子/响应式语义、REPL 共享 Globals、浏览器绑定。 |
| `sahou/internal/interp/stdmod.go` | 标准库模块 随机/时间/数学/编码/系统 + 模块构造基础设施。 | `errs`（+ 标准库 math/rand、time、encoding/base64、net/url 等）。 | 五个内置标准库模块；转译器 `transpile.go` 需镜像同名成员（`__saho_std_*`）。 |
| `sahou/internal/interp/stdmod_test.go` | 标准库单元测试（hex 与百分号解码）。 |  |  |
| `sahou/internal/interp/testmod.go` | 测试模块 测试/assert（用户程序单元测试）。 | `errs`（+ fmt、math/big、sync）。 | 用户级断言能力；`测试.汇总` 返回值（失败数或空值）。 |
| `sahou/internal/interp/uimod.go` | 纯代码构造图形界面（`应用.写页面`）：页面/控件模型 + HTML 生成 + 事件派发/镜像同步。 | `errs`（+ encoding/json）。 | `写页面` 全链路、原生窗口事件桥、`095_page_builder` 快照、`uimod_test.go`。 |
| `sahou/internal/interp/uimod_test.go` | 写页面无窗口路径测试（构造/到HTML/事件派发/镜像同步/参数校验）。 |  |  |
| `sahou/internal/interp/value.go` | 值模型、显示/转换、深度相等、数值辅助。 | `fmt`、`math/big`、`strings`、`errs`、`parser`。 | 所有值语义（数=精确 `*big.Rat`、字典有序、显示规则、深度相等）；改动波及全部模块与 cases。 |
| `sahou/internal/lexer/lexer.go` | 把源码切成记号；缩进仅排版；括号深度 0 才产生换行记号；双语关键字归一化。 | `errs`。 | 整个语言前端；改动波及 parser/transpile/format/lsp 及全部 cases 测试。 |
| `sahou/internal/lsp/lsp.go` | `sahou lsp` 语言服务器（stdio JSON-RPC）：诊断 + 补全 + 悬停 + 跳转定义 + 重命名。 | `errs`、`interp`、`lexer`、`parser`、`stonesrc`（+ encoding/json 等）。 | 编辑器诊断/补全/悬停；VS Code 扩展依赖。 |
| `sahou/internal/lsp/lsp_test.go` | LSP 跳转定义/重命名的 Go 单元测试（批41 新增）。 | `internal/lsp`。 | 改 `lsp.go` 跳转/重命名逻辑后必须保持全绿。 |
| `sahou/internal/parser/parser.go` | AST 定义 + 递归下降语法分析器。 | `errs`、`lexer`。 | 整个语言语法；新增语句/表达式会波及 interp、transpile、lsp、format 及 cases。 |
| `sahou/internal/stonesrc/stonesrc.go` | exe 自带 stones 包的唯一存放处（编译期 embed 注入 `FS`）。 | io/fs、sort、strings。 | 离线标准库包能力（18 包）、serve 运行时、补全与悬停数据。 |
| `sahou/internal/transpile/rt.js` | 转译产物的 JS 运行时（`__saho_*` 辅助函数集合）。 |  |  |
| `sahou/internal/transpile/transpile.go` | sahou → JavaScript 转译器（复用 lexer/parser/AST 代码生成后端，**不 import interp**）。 | `errs`、`lexer`、`parser`、`stonesrc`（+ embed rt.js）。 | 浏览器部署、转译语义与解释器一致性、响应式格子 JS 运行时（`rt.js`）。 |
| `sahou/main.go` | 卅命令行入口，解析子命令并驱动 lexer → parser → interp / transpile / lsp / format / 打包 / stones 管理 / 静态服… | `encodesrc`、`errs`、`format`、`interp`、`lexer`、`lsp`、`parser`、`stonesrc… | 全部 CLI 子命令、REPL、打包产物、serve 页壳；改动会波及所有 shell 测试。 |
| `sahou/stones/中文数字/main.saho` | 整数（0–9999 亿）与中文数字文本互转。 | 核心内置函数（`取/包含/文本/取整` 等）。 | API 变更需同步 `docs/10` 表、`language.json`、`pkgdemo/演示.saho`、`te… |
| `sahou/stones/几何库/main.saho` | 基础几何计算（面积/周长/距离）。 | 内置 `数学`（`圆周率`）、`平方根`。 | 同 stones 通用（文档表/编辑器元数据/示例/测试/双副本）。 |
| `sahou/stones/分数库/main.saho` | 精确分数运算，分数以 `[分子, 分母]` 表示。 | 内置 `数学.向下取整`（v0.3 后不再用取整 hack）。 | 同 stones 通用。 |
| `sahou/stones/单位换算/main.saho` | 长度/重量/数据大小/温度换算。 | 核心内置（`包含/连接/列表`）。 | 同 stones 通用。 |
| `sahou/stones/密码库/main.saho` | 经典手工密码（凯撒/摩斯/栅栏）。 | 核心内置（`位置/取/分割/连接/转大写` 等）。 | 同 stones 通用。 |
| `sahou/stones/数列库/main.saho` | 经典数列（看得见过程）。 | 内置 `数学.向下取整`。 | 同 stones 通用。 |
| `sahou/stones/文本库/main.saho` | 文本处理工具。 | 核心内置。 | 同 stones 通用。 |
| `sahou/stones/日期库/main.saho` | 公历日期计算（不依赖时间模块，双端可用）。 | 内置 `数学.向下取整`。 | 同 stones 通用。 |
| `sahou/stones/时长库/main.saho` | 秒数 ↔ 时分秒（与日期库成对）。 | 内置 `数学.向下取整`。 | 同 stones 通用。 |
| `sahou/stones/游戏库/main.saho` | 课堂游戏随机工具。 | 内置 `随机` 模块（`随机.数`）。 | 同 stones 通用。 |
| `sahou/stones/矩阵库/main.saho` | 矩阵基础运算，矩阵用"列表的列表"（按行存放）。 | 核心内置。 | 同 stones 通用。 |
| `sahou/stones/算术库/main.saho` | 精确整数算法。 | 核心内置（`平方根` 等）。 | 同 stones 通用。 |
| `sahou/stones/算法库/main.saho` | 教科书式排序/查找/递归经典（"看得见过程"）。 | 核心内置；v0.3 新增 `汉诺塔/八皇后`（递归回溯）。 | 同 stones 通用；改八皇后需保持"92 解"断言（`tests/packages.sh`）。 |
| `sahou/stones/统计库/main.saho` | 基础统计量（**总体口径**，除以 n）。 | 核心内置（`排序/求和/最大值/最小值/平方根`）。 | 同 stones 通用。 |
| `sahou/stones/罗马数字/main.saho` | 1–3999 的数 ↔ 罗马数字文本（标准减法形式）。 | 核心内置。 | 同 stones 通用。 |
| `sahou/stones/进制库/main.saho` | 2–36 进制互转。 | 核心内置（`位置/取/转大写/转小写`）。 | 同 stones 通用。 |
| `sahou/stones/逻辑库/main.saho` | 逻辑运算与真值表。 | 核心内置（`并且/或者/非`）。 | 同 stones 通用。 |
| `sahou/stones/集合运算/main.saho` | 以列表实现集合运算（去重、保序）。 | 核心内置（`包含`）。 | 同 stones 通用。 |
| `sahou/stonesfs.go` | 把 `stones/` 与 wasm 运行时（`wasm_exec.js`、`sahou.wasm`）embed 进可执行文件，并在 `init` 注入 `stonesrc.FS… | `embed`、`io/fs`、`stonesrc`。 | 发布版 exe 的自带库与 serve 运行时；不影响 `打包` 生成的 exe（该产物复制 `internal/`+… |
| `sahou/tests/app.sh` | 应用与后端写法回归。 |  |  |
| `sahou/tests/build.sh` | 转译器一致性测试。 |  |  |
| `sahou/tests/cases/010_numbers.saho` | 数值语义（精确有理数、真除法、取余、优先级、`+` 字符串/列表重载、`*` 重复）。 | （语言）：核心 arith/index。 **被依赖**：`run.sh`、`build.sh`。 **影响范围**：interp.ari… |  |
| `sahou/tests/cases/020_strings.saho` | 字符串插值/转义与文本内置（长度/转大写/修剪/分割/替换/包含）。 |  | lexer.lexString/scanInterp + builtins 文本函数。 **备注**：`分隔: ";"… |
| `sahou/tests/cases/030_lists_dicts.saho` | 列表/字典成员与全局函数、有序字典、下标/成员赋值。 |  | interp memberValue/indexValue/assignTo + builtins 容器函数。 |
| `sahou/tests/cases/040_control.saho` | 控制流（如果/又如/否则、当、for 于 列表/文本/字典）。 |  | interp.execStmt 控制流分支。 |
| `sahou/tests/cases/050_functions.saho` | 函数/匿名函数/一等函数/递归/作用域遮蔽/循环变量作用域。 |  | callSahou/Env 作用域。 |
| `sahou/tests/cases/060_errors.saho` | 尝试/接住（除零、抛出、转换错误、跨函数抛出）。 |  | execTry/errorSig 传播。 |
| `sahou/tests/cases/070_builtins2.saho` | 类型名与数学内置（类型/文本转数/数(真)/四舍五入(含负位)/平方根/绝对值/深度包含）。 |  | biType/biNum/biRound/biSqrt/biAbs/biContains + TypeEnName。 |
| `sahou/tests/cases/080_fullwidth.saho` | 全角符号自动按半角处理（引号/括号/逗号/句点/惊叹号）。 |  | lexer.fullwidth 归一化。 |
| `sahou/tests/cases/090_semi_quotes.saho` | 分号作语句结束符 + 全角引号 + 花括号块 + 分号。 |  | lexer.lexOp（`;`→NL）与 lexString（全角引号）。 |
| `sahou/tests/cases/092_closure_dict.saho` | 作用域语义（函数读外层、赋值新建局部、共享状态用字典）。 |  | Env/闭包/字典可变性。 |
| `sahou/tests/cases/093_pipeline.saho` | 数据管道 `->`（裸函数、匿名函数、带参调用、`它` 隐式、链式）。 |  | interp.evalPipe/callStepFn + transpile.pipe。 |
| `sahou/tests/cases/094_pipeline_arrow.saho` | 全角箭头 `→` 与 `->` 等价（词法归一）。 |  | lexer（`→`→PIPE）。 |
| `sahou/tests/cases/095_page_builder.saho` | 纯代码写页面 + `到HTML` 快照（标签/输入框/行/按钮事件/下拉）。 |  | uimod.buildHTML/html。 |
| `sahou/tests/cases/096_multiline_dict.saho` | 多行字典/列表字面量（尾逗号、闭括号独立成行、空字典）。 |  | parser.dictLit/listLit + lexer（花括号不抑制换行）。 |
| `sahou/tests/cases/097_builtin_shadow.saho` | 参数名与内置函数同名（函数内遮蔽内置；赋值/重定义内置则报错）。 |  | Env 遮蔽 + interp/transpile 的 declared 语义一致性。 |
| `sahou/tests/cases/098_default_params.saho` | 用户函数默认参数（限不可变字面量，排末尾；位置/命名/覆盖）。 |  | parser.paramList + interp.callSahou + transpile.paramListJS。 |
| `sahou/tests/cases/099_cells.saho` | 格子（响应式）：依赖变化自动重算（解释器与转译一致）。 |  | reactive.go + transpile.collectCells/`__saho_cell`。 ## test… |
| `sahou/tests/cases/900_undef.saho` |  |  | eval Ident + errs 文案。 |
| `sahou/tests/cases/901_noend.saho` |  |  | parser.expectEnd 文案。 |
| `sahou/tests/cases/902_chain.saho` |  |  | parser.cmpExpr。 |
| `sahou/tests/cases/903_addtype.saho` |  |  | interp.arith/badOpMsg。 |
| `sahou/tests/cases/904_key.saho` |  |  | interp.memberValue + DidYouMean。 |
| `sahou/tests/cases/905_negidx.saho` |  |  | interp.indexValue。 |
| `sahou/tests/cases/906_builtin.saho` |  |  | interp.assignTo（内置名不可改）+ transpile.stmt。 ## tests —— 其它 |
| `sahou/tests/fullstack.sh` | 全栈端到端回归。 |  |  |
| `sahou/tests/modproject/主程序.saho` | 模块系统测试主程序。 | `算术.saho`、内置 `网络/net`。 **被依赖**：`modules.sh`。 **影响范围**：模块导出/双语引入。 |  |
| `sahou/tests/modproject/期望.txt` | `主程序.saho` 的期望输出快照。 | — **被依赖**：`modules.sh`。 **影响范围**：模块运行 + JSON 序列化。 --- ## 依赖关系总览 |  |
| `sahou/tests/modproject/算术.saho` | 模块导出语义（顶层名字即导出）。 | （模块作用域）。 **被依赖**：`主程序.saho`。 **影响范围**：loadModuleFrom 的导出表。 |  |
| `sahou/tests/modules.sh` | 模块系统 + stones 流程回归。 |  |  |
| `sahou/tests/net.sh` | 网络模块回归。 |  |  |
| `sahou/tests/packages.sh` | stones 标准库包回归。 |  |  |
| `sahou/tests/run.sh` | 核心一致性测试（cases 快照 diff + 负向用例退出码/子串）。 |  |  |
| `sahou/tests/run_all.sh` | 全量回归总闸。 |  |  |
| `sahou/tests/share_codec.mjs` | 在线体验页分享链接编解码的回归测试（批41 新增，Node 直跑）。 | 无（零依赖 Node）。 | 改 `examples/在线体验/index.html` 的分享编解码后必须重跑。 |
| `sahou/tests/stdlib.sh` | 标准库模块回归（随机/时间/数学/编码/系统）。 |  |  |
| `sahou/tests/test.saho` | 手工玩具脚本。 | （语言）：内置 print 全角归一。 **被依赖**：人工。 **影响范围**：无自动回归。 **备注**：验证全角括号可读性。 |  |
| `sahou/tests/wasm.sh` | WASM 直跑回归。 |  |  |
| `sahou/分发版自检.saho` | 发行版冒烟自检脚本（数据库自增 + 网页渲染）。 |  |  |

### 5.4 sahou-harness —— 「一切皆插件」的 agent harness（57 条）

| 文件 | 用途 | 关键依赖 | 改动波及 |
|---|---|---|---|
| `sahou-harness/.github/workflows/ci.yml` | GitHub Actions 测试工作流（2026-09-26 新增，此前本仓库没有 CI）。 | `actions/checkout@v4`、`actions/setup-python@v5`、`nanoagent`（GitHub 直装… | 改安装方式（如 nanoagent 发布到 PyPI）时需同步；nanoagent 远端 `main` 若坏，本仓 C… |
| `sahou-harness/CHANGELOG.md` | Keep a Changelog 格式的变更记录；「未发布」段记录 A–F 批次与 2026-09-27 功能扩展（三插件/多模态）。 |  |  |
| `sahou-harness/LICENSE` | 仓库的开源许可证正文，**MIT License**，版权人 `Copyright (c) 2026 gwqwy`。 | 无。 | 改协议需三处同改（本文件 + `pyproject.toml` + README）。 |
| `sahou-harness/MANIFEST.in` | sdist 打包清单补充——确保 13+ 份内置插件 `plugin.json`、`py.typed`、LICENSE 等非 .py 文件进包。 |  |  |
| `sahou-harness/README.md` | 项目说明文档，讲清"一切皆插件"的架构、桌面端形态、快速开始、插件写法与测试方式。 | 无。 | 改动不影响运行时；但描述若与代码不一致会误导使用者（例如插件数量、命令名）。 |
| `sahou-harness/docs/architecture.md` | 架构文档——微内核/生命周期/拓扑激活/服务冲突/权限模型/目录职责/写插件指南；插件数与内置插件一览随代码同步（当前 16 个）。 |  |  |
| `sahou-harness/docs/长程任务架构-功能规划.md` | 功能规划报告（2026-09-27，依据用户提供的 5 张长程任务方法论图）——方法论总结 + 现状对照 + 可添加功能清单 F1~F8 + 实施顺序。 |  |  |
| `sahou-harness/harness/__init__.py` | 包级文档与版本号。 | 无。 | 改 `__version__` 仅影响元信息展示。 |
| `sahou-harness/harness/__main__.py` | `python -m harness` 入口。 | `.cli`。 | `main()` 签名变化会波及此处。 |
| `sahou-harness/harness/approvals.py` | shell/写文件的统一审批门（Ask/allow/deny + 会话内批准记忆 + 命令白名单 + 审计日志）。 | 标准库（json/time/fnmatch/pathlib）。 | 改放行/拒绝语义会波及全部写路径测试（ShellApprovalTests/ApprovalGateTests）。 |
| `sahou-harness/harness/bootstrap.py` | 工程脚手架（2026-09-27 长程任务 F5）——Bootstrap 工作流前 4 步的确定性部分，CLI `sha bootstrap` 与桌面端 `bootstrap_p… | 标准库 subprocess/pathlib。 | 会向用户工作区写文件并 git 提交——只新增不覆盖是硬约定。 |
| `sahou-harness/harness/builtins/browser/*` | browser 插件（2026-09-27 功能6）——`fetch_url(url, max_chars)` 抓网页转纯文本。 | 延迟导入 `httpx`（openai 既有依赖）、`html`/`re`/`urllib.parse`。 | 给模型的联网能力面；白名单配置错误会意外放行/拦死。 |
| `sahou-harness/harness/builtins/chat_loop/plugin.json` | chat_loop 插件清单。 | 无。 | 改 `name` 会改变 `sha status` 显示与主机内 `host.plugins` 键名、`tests/t… |
| `sahou-harness/harness/builtins/chat_loop/register.py` | 对话循环插件——懒构建 nanoagent `Agent`（等其它插件工具聚合后再建），并桥接步骤事件到桌面端。 | 延迟导入 `nanoagent`（`Agent`/`Memory`/`SkillRegistry`）、`subprocess`/`path… | 对话主链路；`ask` 返回结构被 `repl`、desktop `chat`、测试共同消费；`_EventTrace… |
| `sahou-harness/harness/builtins/guardrails/*` | guardrails 插件（批次 E）——从 config 的 `guardrails` 段构建输入/输出护栏，服务名 `guardrails`。 |  |  |
| `sahou-harness/harness/builtins/knowledge/*` | knowledge 插件（RAG）——`index_knowledge`/`search_knowledge` 工具 + `host.service("knowledge")`… | 延迟导入 `nanoagent.rag.KnowledgeBase`；`harness.workspace`（safe_path/iter… | 工具 schema 与服务签名变更波及 agent 能力、桌面知识库面板与测试；`index.npz` 文件格式由 n… |
| `sahou-harness/harness/builtins/mcp_client/plugin.json` | mcp_client 插件清单。 | 无。 | 注意 `tests/test_harness.py` 的 `test_builtin_plugins_all_acti… |
| `sahou-harness/harness/builtins/mcp_client/register.py` | MCP 客户端插件——连接配置里的 MCP 服务器，工具并入 agent 工具集，连接以 effect 管理。 | 标准库 `asyncio` / `typing`；延迟导入 `nanoagent.mcp.MCPServer`；经 `ctx.host.p… | MCP 工具接入与连接生命周期；配置字段 `mcpServers`（`url`/`type`/`headers`/`c… |
| `sahou-harness/harness/builtins/models/plugin.json` | models 插件清单。 | 无。 | 同 chat_loop，改 name 影响状态断言。 |
| `sahou-harness/harness/builtins/models/register.py` | 模型提供者插件——从配置构建多模型池，提供 `models_runtime` 服务与自主切换工具。 | 延迟导入 `nanoagent.AnthropicLLM`/`nanoagent.LLM`；经 `ctx.host` 使用 `profil… | 整个模型层；`runtime` 是单一可变字典，热重建（desktop `_rebuild_pool`）直接改其 `p… |
| `sahou-harness/harness/builtins/notifications/*` | notifications 插件（2026-09-27 功能4）——`notify(message, title)` 向配置的 webhook POST JSON。 | 延迟导入 `httpx`；`ctx.on` 的 disposer 由内核账本管理。 | 外发网络副作用；url 配错只让 notify 返回可读错误，不影响对话。 |
| `sahou-harness/harness/builtins/repl/plugin.json` | repl 插件清单。 | 无。 | 同前述。 |
| `sahou-harness/harness/builtins/repl/register.py` | REPL 插件——终端交互界面（UI 本身也是插件，可整体替换）。 | 经 `ctx.host` 使用 `service("ask"/"new_session"/"models_runtime")`、`host… | CLI 默认界面；`host.harness` 属性访问依赖 `Context.host` 指向 `Harness`… |
| `sahou-harness/harness/builtins/scheduler/*` | scheduler 插件（2026-09-27 功能5）——定时任务到点用独立 agent 执行提示词。 | `harness.schedule_store`（绝对导入）；`host.service("models_runtime"/"guardr… | 常驻线程生命周期；激活即启动，卸载必须 join 成功。 |
| `sahou-harness/harness/builtins/skills/plugin.json` | skills 插件清单。 | 无。 | 同前述。 |
| `sahou-harness/harness/builtins/skills/register.py` | 技能插件——声明 profile 的 `skills/` 目录为技能源。 | 标准库 `pathlib.Path`；经 `ctx.host.profile.root`。 | 技能来源之一；`or True` 恒真分支是刻意的（消除 is_dir 判断），修改需谨慎。 |
| `sahou-harness/harness/builtins/subagent/*` | subagent 插件（批次 E）——`spawn_subagent` 子 agent（复用主模型与工具，剪掉递归工具）。 |  |  |
| `sahou-harness/harness/builtins/tools_fs/plugin.json` | tools_fs 插件清单。 | 无。 | 同前述。 |
| `sahou-harness/harness/builtins/tools_fs/register.py` | 文件工具插件——提供带工作区路径监狱的读写/列文件工具，并实现 `permissions.fs` 权限门。 | 标准库 `pathlib.Path`；经 `ctx.host` 使用 `workspace`、`profile.load_config`、… | 文件读写安全边界；改 `_safe` 会波及越狱测试与桌面工作区热切换；权限门语义被 `set_permission(… |
| `sahou-harness/harness/builtins/tools_git/*` | tools_git 插件（2026-09-27 长程任务 F4）——受限 git：`git_status`/`git_diff`/`git_log`（只读，deny 时全拒）+… | `harness.config.permission_mode`；标准库 subprocess。 | agent 获得了**写仓库**的能力——权限门与测试门的实现改动直接改变安全边界。 |
| `sahou-harness/harness/builtins/tools_search/*` | tools_search 插件（批次 E）——`search_text` 全工作区 grep 式检索（glob/正则/上限），工具安全依赖 `harness.workspace`。 |  |  |
| `sahou-harness/harness/builtins/tools_shell/plugin.json` | tools_shell 插件清单。 | 无。 | 同前述。 |
| `sahou-harness/harness/builtins/tools_shell/register.py` | Shell 工具插件——在工作区执行命令，受 `permissions.shell` 权限门控制。 | 标准库 `subprocess`；经 `ctx.host` 使用 `profile.load_config`、`confirm`、`wor… | 命令执行安全；桌面端右侧"终端"页直接复用它，因此权限门语义同时约束 CLI 与桌面。 |
| `sahou-harness/harness/builtins/tools_todo/*` | tools_todo 插件——**TODO.md 工作区任务索引**（2026-09-27 长程任务架构 F1 重写：原纯内存态 → 持久化 `<工作区>/TODO.md`，Ma… |  |  |
| `sahou-harness/harness/builtins/tracing/*` | tracing 插件（批次 E）——按天 JSONL 追踪，服务 `tracing.new_tracer`，`sha trace` 读摘要。 |  |  |
| `sahou-harness/harness/builtins/workflow/*` | 分任务执行工作流内置件（Manus 式）：plugin.json 声明 + register.py 执行器。 | `workflow_store`、`chat_loop._max_iterations`、`schedule_store.write_ba… | 改执行语义需同步 WorkflowStoreTests 与看板刷新。 |
| `sahou-harness/harness/checkpoints.py` | 写文件/编辑前的检查点（快照 + 撤销）。 | 标准库。 | 撤销语义变更会波及写路径测试。 |
| `sahou-harness/harness/cli.py` | 命令行入口（`sha` 命令），组装运行时并按子命令分派。 | 标准库 `argparse` / `sys` / `pathlib`；本项目 `.config.Profile`、`.kernel.Har… | `build_runtime` 是所有测试与桌面端的装配点，改动会波及全部测试与 desktop；子命令/参数名是 C… |
| `sahou-harness/harness/config.py` | JSON 配置与 profile 隔离目录管理（不使用 .env）。 | 标准库 `json` / `pathlib` / `typing`；`shutil` 延迟导入。 | 配置字段是"隐式契约"——`models`/`default_model`/`permissions.{shell,f… |
| `sahou-harness/harness/desktop.py` | 桌面端——pywebview 原生窗口（Windows 为 WebView2），`DesktopApp` 为进程内 js_api 后端，内嵌单页 `UI_HTML` 作渲染层，页… | 标准库 `hashlib` / `ipaddress` / `json` / `re` / `threading` / `time` /… | 桌面端所有交互行为、模型/插件/技能/工作区/权限/会话的加载路径；改动 `ws_tree`/`chat`/`stat… |
| `sahou-harness/harness/exporter.py` | 会话导出与用量统计——CLI `sha export/usage` 与桌面端「📤 导出会话 / 🗂 导出全部 / 📈 用量图表」共用的唯一实现（2026-09-27）。 | `harness.config.Profile`；标准库 zipfile / datetime（延迟导入）。 | 导出 Markdown 格式、zip 结构或 usage.jsonl 字段变更会同时影响 CLI 与桌面端展示。 |
| `sahou-harness/harness/kernel.py` | 微内核——Host 宿主 + 插件上下文 + 生命周期状态机（对齐 DeepSeek Harness 的 Cordis 模型）。 | 标准库 `importlib.util` / `sys` / `uuid` / `dataclasses` / `pathlib` / `… | 内核 API 变更会同时波及 7 个内置插件、`cli.py`、`desktop.py`（经 `host.servic… |
| `sahou-harness/harness/loader.py` | 插件发现与装载——读取 `plugin.json` 清单 + 以文件路径动态执行 `register.py` 的 `register(ctx)`。 | 标准库 `importlib.util` / `json` / `sys` / `uuid` / `pathlib` / `typing`。 | 加载策略变更直接影响所有插件（含用户安装的）；模块名冲突/清理、相对导入（插件无法 `from .` 自身目录）都受此… |
| `sahou-harness/harness/notifications.py` | 通知中心存储层（profile 内 notifications.json，推送/未读/已读/容量上限）。 | 标准库。 | JSON 结构变更需同步桌面端渲染。 |
| `sahou-harness/harness/procutil.py` | subprocess 辅助（2026-09-27）——抑制 GUI（--noconsole）进程里 spawn 控制台程序时的黑色 conhost 窗口闪现。 | 标准库 subprocess。 | 新增任何 subprocess 调用都必须传 `creationflags=CREATE_NO_WINDOW`，否则… |
| `sahou-harness/harness/py.typed` | PEP 561 标记文件（空文件），让下游 mypy 认 harness 包带类型注解。 |  |  |
| `sahou-harness/harness/remote.py` | 手机/浏览器远程访问服务（线程化 HTTP，只读会话列表 + 发消息，配对码鉴权）。 | 标准库 http.server/hmac/secrets。 | 安全敏感面——不暴露文件与命令；改路由须保持白名单最小化。 |
| `sahou-harness/harness/schedule_store.py` | 定时任务的存储层（2026-09-27 功能5）——scheduler 插件与 `sha schedule` CLI 共用的 tasks.json 读写/校验。 | `harness.config.atomic_write_text`。 | 任务文件格式变更会同时影响插件与 CLI。 |
| `sahou-harness/harness/snippets.py` | 快捷指令（常用提示词片段）存储层（2026-09-27 第六批）——桌面端 ⚡ 菜单与 REPL `/snip` 共用，存 profile config.json 的 `snip… | `harness.config.Profile.mutate_config`（同一把锁内的读-改-写）。 | `snippets` 键结构变更会同时影响桌面端菜单与 REPL 命令。 |
| `sahou-harness/harness/workflow_store.py` | 工作流文件存储层（`<profile>/workflows/<id>.json`，内置件与桌面端共用）。 | `config.Profile/atomic_write_text`。 | JSON 形状变更需同步看板渲染与续跑语义。 |
| `sahou-harness/harness/workspace.py` | 工作区路径监狱与文件遍历——所有文件类插件共用的唯一实现（防止越界判定散落各插件）。 | 标准库 pathlib/collections.abc。 | 任何越界判定收紧/放宽都直接改变工具安全边界。 |
| `sahou-harness/pyproject.toml` | 打包元数据与入口声明。 | `nanoagent >= 0.1.0`、`pywebview >= 5.0`（可选）。 | 改入口名会打断 `sha` 命令、`sha.exe`、`ShaDesktop.exe`；改 `requires-pyt… |
| `sahou-harness/tests/test_desktop.py` | 桌面端进程内 API 的单元测试（不依赖真实窗口）。 | 标准库 `os` / `sys` / `tempfile` / `unittest` / `pathlib` / `shutil` / `… | 桌面端任意 API 方法签名/返回结构变更都会波及；尤其是 `ws_tree`（`test_ws_tree_lists… |
| `sahou-harness/tests/test_harness.py` | 内核生命周期、插件装载、模型切换、权限门、端到端对话的离线单元测试。 | 标准库 `json` / `os` / `sys` / `tempfile` / `unittest` / `pathlib`；`harn… | 内核/插件/配置任一契约变更都会使此文件失败；`test_builtin_plugins_all_activate`… |
| `sahou-harness/tests/test_new_plugins.py` | 功能4-7 的回归测试（2026-09-27）：通知 webhook / 定时任务 / fetch_url / 多模态图片输入。 | `test_harness`（build_host/make_profile/patch_model_build）；`harness.sc… | 三个新插件与 chat_loop images 参数的契约变更都会波及。 |
| `sahou-harness/tests/test_safety.py` | 安全机制专项测试（审批门 + 检查点）。 | `harness.approvals`、`harness.checkpoints`。 | 改审批/检查点行为后必须全绿。 |
| `sahou-harness/tools/*` | 开发/打包/测试辅助脚本的统一目录（2026-09-26 批次 F 从仓库根 `git mv` 进来；7 个文件：`build_exe.py` / `run_tests.py`… | `harness.cli` / `harness.desktop.UI_HTML` / `test_harness`；外部 PyInsta… | 打包产物与测试入口；UI_HTML 的 DOM/JS 契约变更需同步 serve_ui_preview 的 MOCK。 |

## 6. 覆盖度报告

- 磁盘候选文件（已排除 `.git` / `.venv` / `__pycache__` / `node_modules`，含构建产物）：**907**
- 索引条目：**338**（含 33 条通配聚合条目）
- 覆盖磁盘文件：**900**（99.2%）
- 未覆盖：**7**　幽灵条目：**0**

未覆盖清单：

- `.gitattributes`
- `.gitignore`
- `AGENTS.md`
- `README.md`
- `aoci.code.txt`
- `aoci.meta.txt`
- `aoci.txt`

## 7. 明细索引导航（全字段）

| 分片 | 覆盖范围 | 条目数 |
|---|---|---|
| `parts/01-nanoagent-core.md` | nanoagent · 核心源码 | 33 |
| `parts/02-nanoagent-tests-examples.md` | nanoagent · 测试 / 示例 / 打包元数据 | 46 |
| `parts/03-sahou-compiler.md` | sahou · 编译器、内建模块与测试脚本 | 80 |
| `parts/04-sahou-docs-eco.md` | sahou · 文档、stones 标准库、示例、编辑器 | 72 |
| `parts/05-sahou-harness.md` | sahou-harness · 微内核、桌面端、插件、打包 | 57 |
| `parts/06-workspace-and-assets.md` | 工作区根 / 资产 / 构建产物 / 补充条目 | 51 |

每个条目含完整字段：用途 / 关键内容 / 对外接口 / 依赖 / 被依赖 / 影响范围 / 备注。
