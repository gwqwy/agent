# 工作区长期记忆：E:\文件\编程文件\agent

三个互相关联的项目，围绕「Agent + 中文编程语言」展开。

## 1. nanoagent/ — 从零手写的轻量 Python Agent 框架
- 定位：可读懂的教学级 agent 框架，依赖极少，每个模块独立可读。
- 源码在 `nanoagent/nanoagent/`，约 26 个模块：llm / anthropic_llm / tools / agent /
  memory / tracing / rag/ / mcp / mcp_server / observability / multi / task / guardrails /
  skills / plugins / bootstrap / manage / media / coding / evals / checkpoints / cli / server / browser。
- 核心：agent loop（LLM→工具→回填→循环），run/arun 双轨，工具并行，response_model 结构化输出。
- 对标：Agno / OpenAI Agents SDK / LangGraph / PydanticAI / promptfoo / LangSmith。
- `examples/` 有 01–16 渐进式示例；`tests/` 314 条 unittest（mock LLM，离线可跑；MCP/FastAPI 缺失时跳过，未装 tiktoken 时另有 1 条条件跳过）。
- ⚠️ **测试的环境依赖**：`estimate_tokens` 取值**随环境而变**（CI 装了 tiktoken 走 cl100k_base 精确计数，开发机默认没装走启发式，同一串可得不同数字）。断言具体 token 数的用例必须先用 `tests/test_token_memory.py` 里的 `forced_heuristic()` 锁定路径，否则会出现「本地绿、CI 红」。跑测试最好两个环境各来一遍（有/无 tiktoken）。
- 设计思想对齐 DeepSeek Harness 的「一切皆插件」（mini-Cordis：ctx/effect/disposer + 格式适配器）。
- 已 `pip install -e` 装进工作区根 `.venv`（Python 3.14.0）。
- 非独立 git 仓库（无 .git）。

## 2. sahou/ — 「卅」中文入门编程语言（Go 实现的解释器/工具链）
- 读音 sa，源文件后缀 `.saho`，双语关键字（中文/英文可混用），当前版本 v0.3.0。
- 单一数值类型用 big.Rat（有理数，0.1+0.2 精确）；23 个关键字、30 个内置函数、11 个标准库模块。
- 能写：CLI、网站后端、浏览器页面（转译 JS 或 sahou.wasm 直跑）、桌面/原生窗口（WebView2）、
  手机端局域网页面、`sahou 打包` 单文件 exe、纯 Go 内嵌 SQL 数据库。
- 结构：`internal/`（lexer/parser/interp/format/lsp/transpile/stonesrc/errs/encodesrc）、
  `cmd/sahouwasm/`、`stones/`（18 个纯 saho 标准库包）、`docs/`（00–16 全套中文文档）、
  `tests/`（run.sh/net.sh/build.sh/modules.sh/stdlib.sh/packages.sh/wasm.sh/fullstack.sh/app.sh/pack.sh，bash + Git Bash）。
- 构建：`go build -o sahou.exe .`（需 Go 1.23+），唯一第三方依赖 go-webview2（无 CGO，仅 Windows 原生窗口）。
- 已有构建产物 sahou.exe（25MB）/ sahou.wasm（13MB）。
- git 仓库：origin = https://github.com/gwqwy/sahou.git（有 CI + release workflow）。

## 3. sahou-harness/ — 「一切皆插件」的 agent harness（Python）
- 架构参考 DeepSeek Harness（Cordis 微内核 / Everything is a Plugin），执行引擎复用 nanoagent。
- 配置走 JSON，不用 .env。profile 隔离目录 `~/.sahou-harness/profiles/<名>/`。
- `harness/`：kernel.py（微内核：ctx.provide/on/effect，状态机 PENDING→ACTIVE→FAILED/DISPOSED）、
  cli.py（sha 命令）、config.py、loader.py、workspace.py（路径监狱+safe_image）、
  schedule_store.py（定时任务存储层）、desktop.py（pywebview 桌面端，非 Electron）、
  builtins/（**16 个**内置插件：chat_loop / models / tools_fs / tools_search / tools_shell /
  tools_todo / skills / mcp_client / guardrails / tracing / subagent / knowledge /
  browser / notifications / scheduler / repl）。
- CLI：`sha`（REPL）/ `sha desktop` / `sha chat -m` / `sha init` / `sha plugin add|list|remove|new|reload` /
  `sha model list|use|add|remove` / `sha schedule add|list|remove` / `sha export|usage|roundtable|trace|sessions` / `sha status`。
- 能力：模型池 + 自主 switch_model、SKILL.md 技能、MCP 接入、Shell 三级权限门+审计、
  流式/护栏/追踪/子agent/RAG、**多模态图片输入**（ask images 参数 / REPL /image / 桌面端📎+粘贴路径）、
  webhook 通知、定时任务、fetch_url 网页抓取。
- 测试 142 条（test_harness/test_desktop/test_new_plugins），全离线；ruff/mypy 双清零；有 CI。
- 开发脚本在 `tools/`（run_tests.py 是测试唯一正规入口）；`serve_ui_preview.py` 已随迁。
- 运行时 profile：`~/.sahou-harness/profiles/default/`，model=deepseek-flash，
  workspace=E:\文件\编程文件\agent，theme=light，thinking=low。

## 环境约定
- 根目录 `.venv`（Python 3.14.0）已装：nanoagent(editable)、faiss-cpu、fastapi、mcp、openai、numpy、
  opentelemetry、pywin32、python-dotenv 等。
- `.mimosa/` 是 hook 状态目录；`.zcodeignore` 是 ZCode 搜索忽略规则（勿当作 .gitignore 改）。
- 用户偏好：简体中文交流。
- **推送一律不代劳**：`git push` 由用户自己在 IDE 里执行（本机 credential.helper 是 IDE 专有的
  `helper-selector`，非交互 shell 用不了）。AI 只负责把待推命令列出来；
  用户明确说过「请你不要推送」——即使环境允许也不要尝试，除非用户当次明确要求。
- **提交（commit）也不要代劳**（2026-09-27 用户指示「请不要提交」）：AI 完成改动后停在工作区，
  既不 commit 也不 push；若已误提交，用 `git reset --soft HEAD~1` 撤销（改动保留在工作区）。

## 文件索引体系（改动任何文件前先查它）
- 主索引 `FILE_INDEX.md`（工作区根）；明细分片 `.workbuddy/file-index/parts/01..06-*.md`（唯一事实来源）。
- 检索：`.venv/Scripts/python.exe .workbuddy/file-index/query.py <关键词> --full`
  （另有 `--used-by` 看影响面 / `--deps` / `--path` / `--missing` / `--json`）。
- 重建：`.venv/Scripts/python.exe .workbuddy/file-index/build_index.py`（加 `--check` 只检查）。
  目标状态：未覆盖 0、幽灵 0。分片条目格式见 `parts/` 现有条目（`### \`路径\`` + 7 个 `- **字段**：`）。
- 第 1–4 章（总览/依赖/影响矩阵/风险）源在 `.workbuddy/file-index/_master_header.md`，
  第 5–7 章为生成内容，**不要直接改**。
- 已固化为用户级技能 `~/.workbuddy/skills/workspace-file-index/`。

## 缺陷审计结论（2026-09-26 审计，**全部缺陷已修复**——保留作知识沉淀）
- 总报告原为工作区根 `DEFECT_AUDIT.md`，**2026-09-26 已被用户删除**；**明细分片与复现脚本仍在** `.workbuddy/audit/`；外部审计核对判定在 `.audit_tmp/AUDIT_VERDICT.md`；`FILE_INDEX.md` §4 保留精简版风险清单。
- 规模：nanoagent P0×2/P1×6/P2×15；sahou-harness P0×3/P1×6/P2×20。**测试基线全绿（302 + 41），但 5 个 P0 全未被覆盖。**
- **带 bug 的代码不能当成"正确参考"照抄**。已知 P0（均已实测复现）：
  1. `desktop.py:531` `root = Path(ws)` 漏 `.resolve()` → 相对工作区下右侧文件区无法展开（用户报的 bug）。修 3 行。
  2. `tools_shell/register.py:18-25` 与 `tools_fs/register.py:44-52` 权限门 fail-open（等值比较无 else）→
     非规范值 `"Deny"/None/0/True` 全部放行；且默认 `permissions` 无 `fs` 键 → 写文件默认无门控。
  3. `coding.py:211/234`（`list_files`/`search_code`）把模型可控 glob 直接给 `Path.glob`，`"../*"` 越狱；
     **`sahou-harness/builtins/tools_fs/register.py` 的 `list_files` 同样写法**。
  4. `harness/config.py:51-69` 配置非原子写 + 无锁 + 解析失败静默回默认 → 可静默抹掉 models/api_key。
  5. `nanoagent/tracing.py:46` 写 `"type"` 而 `observability.py:44,131` 读 `"event"` → 可观测性统计恒为 0。
- **N-03 最值得先修**：`tools.py:47-71` 不解析字符串注解，凡 `from __future__ import annotations`
  的模块（nanoagent 28/30、harness 5/13）其工具 `int/float/bool/list` 参数全退化成 `string`，
  模型照 schema 传值会崩（实测 `read_file(start_line="2")` → TypeError）。**改一处修好两项目全部工具。**
- 其他要点：`ctx.on()` 的 disposer 未入账本 → 卸载后幽灵监听器仍在触发（nanoagent plugins.py 与
  harness kernel.py **同源缺陷**）；`Harness.deactivate` 丢 `services["models"]`；
  REPL 引用不存在的 `host.harness`（应为 `host.collect_commands()`）；`AnthropicLLM` 缺
  `total_usage`/`context_window`；同步 `Agent.run` 调异步工具返回 coroutine 垃圾串。
- ~~两项目都不是 git 仓库，改动无法回滚~~ → **2026-09-26 更正：两者现在都是独立 git 仓库**
  （remote 名 `nanoagent` / `sahou-harness`，**不是 `origin`**），均已推送到 GitHub 并配了 CI；改动可回滚，动手前先看 `git status`。

## 已知环境陷阱（踩过）
- 无头 Edge/Chrome 在本沙箱**起不来**（`--headless` 老新两种均失败）；验证前端要么用 pywebview
  `evaluate_js`，要么用 Node + CDP 探针。
- `sahou-harness/tests/` 无 `__init__.py`：**加 `-t .` 会让 discover 报 "Start directory is not importable"**；
  不加 `-t` 就正常（top-level 默认等于 start dir，`from test_harness import ...` 才解析得到）。
  正确命令：`python -m unittest discover -s tests -p "test_*.py"`（README 里写的 `python -m unittest discover tests` 同样可用，实测 52 条 OK）。
  `python run_tests.py` 也行 —— 它用 `Path(__file__).resolve().parent` 定位，**并没有硬编码绝对路径**。
  （2026-09-26 更正：此前记作"`discover -s tests` 会报错、必须用 run_tests.py"，方向是反的。）
- 跑浏览器会生成数百 MB 的 profile 垃圾，务必落到 `.workbuddy/` 下并及时清理。
