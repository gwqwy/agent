# sahou-harness 文件级索引（very thorough 通读）

> 工作区根：`E:/文件/编程文件/agent`
> 目标模块：`sahou-harness/`（"一切皆插件"的 agent harness）
> 本索引覆盖 42 个真实读取的文件（跳过 `__pycache__/`、`dist/`、`build_pyi/sha/`、`build_pyi/ShaDesktop/` 等构建产物目录）。

---

## 0. 模块速览

`sahou-harness` 是一个微内核（mini-Cordis / "Everything is a Plugin"）的 agent harness：

- **内核零业务逻辑**：对话、模型、工具、技能、MCP、UI 全部由插件提供。
- **执行引擎复用 nanoagent**（`Agent` / `LLM` / `Memory` / `SkillRegistry` / `MCPServer` / `tools`）。
- **两种前端形态**：CLI（`cli.py` + `repl` 插件）与桌面端（`desktop.py` + pywebview，无 HTTP、无 Electron）。
- **配置不使用 .env**：全部走 profile 目录下的 `config.json`。

顶层目录速览：

| 路径 | 作用 |
| --- | --- |
| `harness/` | 核心包（kernel / loader / config / cli / desktop + 7 个内置插件） |
| `tests/` | 离线单元测试（假模型，不需要 API Key） |
| `.github/` | CI 工作流（2026-09-26 新增；nanoagent 从 GitHub 直装） |
| `build_pyi/` | PyInstaller 的 spec 与构建产物 |
| `dist/` | 已打包的 `sha.exe` / `ShaDesktop.exe` |
| `assets/` | 图标 `sha.ico` |
| `_diag/` | 临时诊断脚本与产物（可清理） |

---

## 1. 顶层文件

### `sahou-harness/README.md`
- **用途**：项目说明文档，讲清"一切皆插件"的架构、桌面端形态、快速开始、插件写法与测试方式。
- **关键内容**：架构图（sha CLI → Harness 微内核 → 7 插件 → profile 隔离目录）；桌面端能力清单（对话、模型可视化设置、当前模型下拉、插件管理、Shell 权限门）；与 DeepSeek Harness / nanoagent 的关系说明。
- **对外接口**：无（纯文档）。
- **依赖**：无。
- **被依赖**：`pyproject.toml` 的 `readme` 字段；无代码引用。
- **影响范围**：改动不影响运行时；但描述若与代码不一致会误导使用者（例如插件数量、命令名）。
- **备注**：README 里插件清单为 chat_loop / models / tools_fs / tools_shell / skills / mcp_client / repl，与实际 `builtins/` 下的 7 个目录一致。2026-09-26 在文末补了「许可证（MIT，链接 `LICENSE`）」段落。

### `sahou-harness/pyproject.toml`
- **用途**：打包元数据与入口声明。
- **关键内容**：`name=sahou-harness`、`version=0.1.0`、**`license = {text = "MIT"}`**、`requires-python>=3.10`；运行依赖 `nanoagent>=0.1.0`；可选依赖 `desktop=["pywebview>=5.0"]`；入口脚本 `sha = "harness.cli:main"`；setuptools 打包 `harness*`。
- **对外接口**：`sha` 命令；`sahou-harness[desktop]` 扩展。
- **依赖**：`nanoagent >= 0.1.0`、`pywebview >= 5.0`（可选）。
- **被依赖**：安装/分发流程；`build_exe.py` 隐含假定包名与入口。
- **影响范围**：改入口名会打断 `sha` 命令、`sha.exe`、`ShaDesktop.exe`；改 `requires-python` 会影响可用语法（代码用到 `X | Y` 联合类型、`str.removesuffix`、`Path.is_relative_to`）。
- **备注**：仓库未启用 `[tool.setuptools.package-data]`，内置插件以数据文件形式被打包是 `build_exe.py` 手工用 `--add-data` 处理的，这是个易错点（见 `build_exe.py`）。`license` 字段早于 `LICENSE` 文件存在——即元数据先声明了 MIT、正文文件一直缺失，2026-09-26 才补齐。

### `sahou-harness/LICENSE`
- **用途**：仓库的开源许可证正文，**MIT License**，版权人 `Copyright (c) 2026 gwqwy`。
- **关键内容**：MIT 标准全文（与 `nanoagent/LICENSE` **逐字节相同**）。
- **对外接口**：法律层面的使用许可；GitHub 仓库页会显示 "MIT license" 徽标。
- **依赖**：无。
- **被依赖**：`pyproject.toml` 的 `license = {text = "MIT"}`、`README.md` 的「许可证」段落（均只写协议名，不引用文件内容）。
- **影响范围**：改协议需三处同改（本文件 + `pyproject.toml` + README）。
- **备注**：2026-09-26 添加，此前该仓库**声明了 MIT 却没有许可证正文**。与 `nanoagent/LICENSE` 是两份独立副本，**无自动同步**。本仓库的 `main` 是无历史分支（见 `推送说明.md`），加文件后正常 `git add -A && git commit && git push` 即可，**不要 `git push --all`**。

### 注：sahou-harness 根目录的 run_tests.py 已移至 tools/（见第 5 节聚合条目）

### `sahou-harness/CHANGELOG.md`
- **用途**：Keep a Changelog 格式的变更记录；「未发布」段记录 A–F 批次与 2026-09-27 功能扩展（三插件/多模态）。
- **备注**：随显著变更人工更新；README 顶部有链接。

### `sahou-harness/MANIFEST.in`
- **用途**：sdist 打包清单补充——确保 13+ 份内置插件 `plugin.json`、`py.typed`、LICENSE 等非 .py 文件进包。
- **关键内容**：`recursive-include harness/builtins */plugin.json`（批次 F 打包缺陷修复的配套，与 `pyproject.toml [tool.setuptools.package-data]` 双保险）；wheel 已实测 13 份清单在内。
- **备注**：新增内置插件目录会被通配自动覆盖，无需逐个登记。

### `sahou-harness/docs/architecture.md`
- **用途**：架构文档——微内核/生命周期/拓扑激活/服务冲突/权限模型/目录职责/写插件指南；插件数与内置插件一览随代码同步（当前 16 个）。
- **备注**：新增插件/核心模块时需同步第 6 节「目录职责」。

### `sahou-harness/docs/长程任务架构-功能规划.md`
- **用途**：功能规划报告（2026-09-27，依据用户提供的 5 张长程任务方法论图）——方法论总结 + 现状对照 + 可添加功能清单 F1~F8 + 实施顺序。
- **关键内容**：F1 TODO.md 工作区任务索引（tools_todo 纯内存态是最大缺口，P0）；F2 三原则准则注入系统提示词（P0）；F3 新会话自动恢复（读 TODO+git log，P0）；F4 受限 git 工具 tools_git + 测试门（P1）；F5 /bootstrap 脚手架命令（P1）；F6 一键无状态重置（P1，依赖 F1/F3）；F7 子代理只读模式（P2）；F8 会话完成归档标记（P2）。
- **备注**：纯规划文档，尚未实现；动工时按第三节清单逐项建 TaskList。

### `sahou-harness/harness/py.typed`
- **用途**：PEP 561 标记文件（空文件），让下游 mypy 认 harness 包带类型注解。
- **备注**：经 `pyproject.toml` package-data 进 wheel。

### `sahou-harness/.github/workflows/ci.yml`
- **用途**：GitHub Actions 测试工作流（2026-09-26 新增，此前本仓库没有 CI）。
- **关键内容**：触发于 push 到 `main`/`master` 与 PR；`ubuntu-latest`；矩阵 `python-version: ["3.10","3.12","3.14"]`；步骤 = checkout → setup-python → Install → Run tests。
- **安装顺序（关键）**：先 `pip install "git+https://github.com/gwqwy/nanoagent.git"`，再 `pip install -e .`。
  **顺序不能反**，也不能只写 `-e .` —— `nanoagent>=0.1.0` 尚未发布到 PyPI，pip 解析不到会直接失败。
- **刻意不装 desktop extra**：pywebview 在 Linux 需要 GTK/WebKit 系统库，而 `tests/test_desktop.py` 用的是 `FakeWindow` 假窗口，`harness/desktop.py` 里的 `import webview` 也都在函数内延迟导入，本就不需要真实窗口。
- **测试命令**：`python -m unittest discover -s tests -p "test_*.py"`。**不要加 `-t .`** —— `tests/` 没有 `__init__.py`，加了会报 `Start directory is not importable`（已实测；不加则 top-level 默认等于 start dir，`from test_harness import ...` 才能解析）。
- **依赖**：`actions/checkout@v4`、`actions/setup-python@v5`、`nanoagent`（GitHub 直装）。
- **被依赖**：无。
- **影响范围**：改安装方式（如 nanoagent 发布到 PyPI）时需同步；nanoagent 远端 `main` 若坏，本仓 CI 会连带变红（有意为之，暴露真实耦合）。
- **备注**：结构与 Python 矩阵对齐 `nanoagent/.github/workflows/ci.yml`，便于两仓统一维护。

---

## 2. harness 核心包

### `sahou-harness/harness/__init__.py`
- **用途**：包级文档与版本号。
- **关键内容**：模块 docstring 描述分层（kernel / loader / config / builtins / cli）；`__version__ = "0.1.0"`。
- **对外接口**：`__version__`。
- **依赖**：无。
- **被依赖**：无显式引用（仅作为包标识被 `import harness` 触发）。
- **影响范围**：改 `__version__` 仅影响元信息展示。
- **备注**：与 `pyproject.toml` 的版本需人工保持一致（无自动同步）。

### `sahou-harness/harness/__main__.py`
- **用途**：`python -m harness` 入口。
- **关键内容**：`from .cli import main`；`raise SystemExit(main())`。
- **对外接口**：`python -m harness`。
- **依赖**：`.cli`。
- **被依赖**：无。
- **影响范围**：`main()` 签名变化会波及此处。
- **备注**：极薄封装。

### `sahou-harness/harness/kernel.py`
- **用途**：微内核——Host 宿主 + 插件上下文 + 生命周期状态机（对齐 DeepSeek Harness 的 Cordis 模型）。
- **关键内容**：
  - 状态常量：`PENDING` / `ACTIVE` / `FAILED` / `DISPOSED`。
  - `EventBus`：`on(event, handler) -> disposer`、`emit(event, **payload)`（单个 handler 异常被吞，不阻断宿主）。
  - 子注册器：`_Tools.register`（借 nanoagent `make_tool` 包装函数为 Tool）、`_Skills.add_dir`、`_Models.register`、`_Commands.register`。
  - `Context`：字段 `plugin_name/bus/host/services/tools_list/skill_dirs/models_map/commands_map/skipped/_disposers`；三原语 `provide(name, service)`、`on(event, handler)`、`effect(fn)`；`deactivate()` 做 LIFO 回滚且幂等。快捷入口 `ctx.tools` / `ctx.skills` / `ctx.models` / `ctx.commands`。
  - `PluginRecord`（dataclass）：`name/path/state/manifest/ctx/provided/skipped/error` + `summary()`。
  - `Harness`：`mount` / `mount_all` / `activate` / `activate_all` / `deactivate` / `collect_tools` / `collect_skill_dirs` / `collect_commands` / `service` / `list`；字段 `bus/plugins/services/profile/confirm`。
- **对外接口**：`PENDING`、`ACTIVE`、`FAILED`、`DISPOSED`、`EventBus`、`Context`、`PluginRecord`、`Harness`。
- **依赖**：标准库 `importlib.util` / `sys` / `uuid` / `dataclasses` / `pathlib` / `typing`；延迟导入 `nanoagent.tools.Tool/make_tool`（仅在 `_Tools.register` 内）；延迟导入 `loader.load_manifest` / `loader.run_register`。
- **被依赖**：`cli.py`（`from .kernel import Harness`）、`tests/test_harness.py`、`_diag/server.py`；`loader` 被 kernel 反向调用。
- **影响范围**：内核 API 变更会同时波及 7 个内置插件、`cli.py`、`desktop.py`（经 `host.service/collect_tools/list`）、全部测试；状态机语义变更影响 `desktop.plugins()` 与 `sha status`。
- **备注**：`deactivate()` 会整体重建 `self.services`（仅从仍 ACTIVE 的插件聚合），因此卸载一个插件会让早先 `provide` 但已失效的条目一起消失，这是刻意的"以活跃状态重建"策略。`activate` 对已 ACTIVE 是幂等 no-op，但不会刷新 `provides`。

### `sahou-harness/harness/loader.py`
- **用途**：插件发现与装载——读取 `plugin.json` 清单 + 以文件路径动态执行 `register.py` 的 `register(ctx)`。
- **关键内容**：`load_manifest(path)`（缺失/坏 JSON 回落为 `{"name": <目录名>}`）；`run_register(record, ctx)`（以唯一模块名 `harness_plugin_<name>_<uuid8>` 载入，执行后取 `register` 回调；兼容模块级 `TOOLS` 列表；两者都无则记 `skipped`）。2026-09-28 修复：register.py **直接 `exec(compile(源码))` 而不走 `spec.loader.exec_module`**——后者读 `__pycache__` 字节码缓存，同一秒内改写 register.py（大小不变）会命中旧缓存，热重载拿到旧代码（`test_reload_picks_up_new_code` 曾因此失败）。
- **对外接口**：`load_manifest`、`run_register`。
- **依赖**：标准库 `importlib.util` / `json` / `sys` / `uuid` / `pathlib` / `typing`。
- **被依赖**：`kernel.Harness.mount`（`load_manifest`）、`kernel.Harness.activate`（`run_register`）。
- **影响范围**：加载策略变更直接影响所有插件（含用户安装的）；模块名冲突/清理、相对导入（插件无法 `from .` 自身目录）都受此处约束。
- **备注**：以文件路径加载意味着插件 `register.py` 不能使用包内相对导入；`sys.modules` 中同名模块在 exec 失败时会 pop 清理。`load_manifest` 被 `mount` 调用两次（一次定名、一次存清单），属小冗余。
### `sahou-harness/harness/config.py`
- **用途**：JSON 配置与 profile 隔离目录管理（不使用 .env）。
- **关键内容**：`DEFAULT_CONFIG`（`default_model` / `models` / `permissions.shell=ask`）；`CONFIG_EXAMPLE`；`Profile` 类——根目录/`config_path`/`plugins_dir`/`sessions_dir`、`_ensure()` 自动建目录与首份配置、`load_config()`（坏文件备份后抛 ConfigError，不回落默认）、`save_config()`、`update_config(**changes)`、`mutate_config(mutator)`、`install_plugin(source)`（copytree，重名加序号后缀）、`remove_plugin(name)`、`save_session/load_session/session_ids/delete_session`（删除走 `_safe_session_file` 白名单，防穿越）、`_backup_broken_config`。
- **对外接口**：`DEFAULT_CONFIG`、`CONFIG_EXAMPLE`、`Profile`。
- **依赖**：标准库 `json` / `pathlib` / `typing`；`shutil` 延迟导入。
- **被依赖**：`cli.py`、`exporter.py`、`tests/test_harness.py`、`tests/test_desktop.py`、`_diag/server.py`、`_diag/probe_real.py`；运行时所有插件经 `host.profile` 间接依赖。
- **影响范围**：配置字段是"隐式契约"——`models`/`default_model`/`permissions.{shell,fs}`/`mcpServers`/`thinking_level`/`theme`/`workspace`/`current_workspace`/`workspaces`/`sessions_meta`/`ui_prefs`/`notifications`/`browser`/`knowledge`/`guardrails`/`schedule` 被 models、tools_shell、tools_fs、mcp_client、desktop、scheduler、knowledge 共同读写。改字段名会连锁波及这些文件与测试。
- **备注**：`load_config` 只做浅合并，嵌套对象（如 `permissions`）由调用方自行拷贝后回写；`install_plugin` 不做内容校验，`plugin.json` 合法性在装载阶段才暴露；`sessions_meta` 里"只命名过、没消息"的会话没有对应文件（桌面端删除逻辑须两者都容忍）。

### `sahou-harness/harness/cli.py`
- **用途**：命令行入口（`sha` 命令），组装运行时并按子命令分派。
- **关键内容**：
  - `BUILTINS_DIR`（指向 `harness/builtins`）；`INSTRUCTIONS_EXTRA=""`（未使用占位）。
  - `build_runtime(profile, workspace) -> Harness`：建宿主、注入 profile/workspace、`mount_all(BUILTINS_DIR)` + `mount_all(profile.plugins_dir)`、`activate_all()`。
  - `_make_parser()`：子命令 `chat(-m)`、`desktop`、`init`、`status`、`plugin {add/list/remove}`、`model {list/use}`、`skill {list}`；全局 `--profile` / `--workspace` / `--home`。
  - `main(argv)`：`init` 仅建 profile；`plugin` 走 install/list/remove；其余先 `build_runtime`；`model` 读 `models_runtime` 服务；`skill` 用 nanoagent `SkillRegistry`；`status` 打印插件状态；`desktop` 调 `desktop.run`；默认 `chat` 调 `ui` 服务（`None`→交互，字符串→单次）。
- **对外接口**：`main`、`build_runtime`、`BUILTINS_DIR`、`INSTRUCTIONS_EXTRA`。
- **依赖**：标准库 `argparse` / `sys` / `pathlib`；本项目 `.config.Profile`、`.kernel.Harness`；延迟导入 `.desktop.run`、`nanoagent.skills.SkillRegistry`。
- **被依赖**：`__main__.py`、`launcher_sha.py`、`launcher_desktop.py`、`tests/test_harness.py`、`tests/test_desktop.py`、`_diag/launch_desktop.py`、`_diag/probe_real.py`、`smoke_desktop.py`（经 tests）。
- **影响范围**：`build_runtime` 是所有测试与桌面端的装配点，改动会波及全部测试与 desktop；子命令/参数名是 CLI 公共契约；`--home` 默认 `~/.sahou-harness`。
- **备注**：`desktop` 命令先 `build_runtime` 再交给 pywebview，因此桌面端与 CLI 共享同一 profile 与插件运行时；`model use` 在服务存在时调用 `runtime["set"]` 并同时写配置，重复但无害。

### `sahou-harness/harness/desktop.py`
<!-- 2026-09-28 第四十一批补充：agent_memory/save_agent_memory（🧠 记忆面板，memory.md 注入由 chat_loop 负责）、checkpoint_diff(cid)（时间线 🔍 diff：留底旧内容 vs 当前，unified diff + 新建文件预览）、_usage_budget_warning（config.usage_budget 超额告警，chat 与流式 worker 双路径携带 budget_warning）、export_profile/import_profile（zip 白名单成员+穿越拦截+config.pre-import.json 留底）；通用→数据新增 📦 备份/📂 恢复行；流式 worker 推送前跑 run_hooks 并把 budget_warning 并入 final_payload；loadCheckpoints 行加 🔍 diff 按钮；rp-mem 标签（TAB_LABELS/RP_TAB_ORDER_DEFAULT/switchPanel 联动）。 -->
<!-- 2026-09-28 第四十二批：右缘悬停自动展开（#rpEdgeHit 10px 热区 + body.rp-peek 浮层态：面板隐藏时鼠标移到右缘临时浮层展开、移开 250ms 收回，不挤动主内容；togglePanel 清 peek 态）；回答排版 v2（.md-h 层级拉开/h1 底线/h2 竖条/h3 强调色、ul/ol/li 标记色+normal 空白、blockquote 竖条+微底、a 链接下划线、hr 轻量、行高 1.7）；check_ui_js 探针扩展列表/引用/链接/hr/标题结构断言。 -->
<!-- 2026-09-28 第四十三批（用户反馈）：第四十二批右缘悬停已**回退**；改为 .rp-tabs 滚轮横滚（initTabsWheel：deltaY→scrollLeft，Shift 原生不叠加）；回复样式 v3（行内 code 强调色、md() 任务清单 - [ ]/[x] → ☐/☑ .task/.task.done、fence-lang 强调色、表头 2px 底线、meta 虚线分隔）；辅助对话修复——auxInit 回放透传 m.reasoning 重建思考块、面板顶部 #auxModelSel 模型下拉（auxInit 从 get_models 填充），chat 增加 model 参数→chat_loop 新服务 ask_with（指定≠当前模型走 build_agent_with 一次性 agent，落盘+计用量；等于当前走全局 ask），测试 test_ask_with_custom_model。 -->
<!-- 2026-09-28 第四十四批（agent 双仓全量）：desktop 新增 get_persona/save_persona（🧠 上半区，persona.md 由 chat_loop._compose_instructions 注入；工作区级 AGENT.md 同样注入）、mcp_test（现场连接列工具，独立线程 asyncio.run，90s 超时）、adopt_compare（切模型+问答落盘+new_session 回放）、schedule_add（⏰ ＋表单）、session_delete_message/session_truncate（✂ 手术，_visible_pos 可见序号换算）、ws_search（复用 search_text 工具，结果可发 agent）、export_session_html（exporter.export_session_html 单文件转义渲染）、cleanup_sessions（sessions_keep_days/keep_count，boot 调用）；save_models 保留 price_in/price_out（元/百万 token），usage_daily 带 prices→cost；前端：对比卡片采用按钮、starter prompts、草稿按会话保存恢复、md 图片白名单（data:/工作区路径→image_preview 换 data URL）、✂ 手术按钮、MCP 测试按钮、定时表单、ws 搜索行、模型单价输入、用量金额提示、导出 HTML 行。 -->
<!-- 2026-09-28 第四十五批（模式系统）：chat_loop 新增 PRESET_MODES（默认/计划/快速回答/只读分析）与 _resolve_mode（预设+config.user_modes 解析，查不到回默认）——_compose_instructions 追加模式提示词、get_agent 按 disable_tools 置 tools=[]；desktop 新增 get_modes/set_mode/save_user_modes（名称唯一、不可覆盖预设、删当前模式回默认）；UI：composer 🎯 modeSel 下拉（refreshModeSel 由 refreshStatus 联动、planBtn on 态）、设置 🎭 模式页（presetModeList 只读 + modeCards 新建/编辑，loadModes/addModeCard/renderModeCards/saveModes）、📋 计划按钮改接 set_mode（计划⇄默认）；测试 ModeSystemTests×2。 -->
<!-- 2026-09-28 第四十六批：新增「安全研究」预设模式（PRESET_MODES 两处同步：chat_loop 附加提示词 + desktop.PRESET_MODES 列表）——声明已授权安全工作语境（防御分析/授权渗透测试/CTF/样本分析），payload 优先教学级+防御视角，未授权请求拒绝，**明示不改变服务商安全策略**（语境声明，非越狱开关）；测试 test_security_research_preset。 -->
<!-- 2026-09-28 第四十七批（输入区 UI）：composer-row 由禁止换行改自动换行收纳（row-gap 6px），发送/停止 margin-left:auto 锚定行尾（不再溢出输入框外），composer 内 select 收缩 64–150px 省略号；「◧ 侧栏」按钮从按钮行移除——左上品牌 logo（#brandLogo）即侧栏开关（hover 微抬/点击 toggleSide，toggleSide 对 sideBtn 判空安全）。 -->
- **用途**：桌面端——pywebview 原生窗口（Windows 为 WebView2），`DesktopApp` 为进程内 js_api 后端，内嵌单页 `UI_HTML` 作渲染层，页面经 `window.pywebview.api.*` 调用后端（无 HTTP、无浏览器）。
- **关键内容**（详见第 5 节专项拆解）：模块级 `_validate_url` / `_fetch_text` / `_parse_market`；常量 `THINKING_LEVELS` / `PERMISSION_MODES` / `THEME_MODES` / `MARKET_URL`；`DesktopApp` 类——会话（chat/chat_stream 流式/sessions/new/rename/delete_session/session_history/**search_sessions/set_session_pin/regenerate_last/edit_message_resend**）、界面偏好（get/set_ui_prefs → `config.ui_prefs`，含强调色/字体/提示音/通知）、导出（export_session/export_all_sessions/usage_daily → exporter）、知识库（knowledge_status/pick_index/clear/sources/remove_source → host.service("knowledge")）、快捷指令（snippets_list/save/delete → harness.snippets）、多模态（pick_image/check_image）、模型/插件/技能/工作区/权限/市场/终端/审查；`UI_HTML`（CSS/HTML/JS：设置弹窗两栏化——`.set-nav` 左导航（能力：模型/插件/技能/市场；界面：外观/通用/用量）+ `.set-content` 独立滚动、外观 pane（主题seg/强调色色板/字体）、通用 pane（开关行+数据行）、用量 pane（stat 卡+折线）、流式 onStreamEvent——rAF 批量渲染+流式期间实时 md()+智能吸底 nearBottom+生成中光标、思考卡片可交互（▶旋转指示/轮数/淡入）、思考三点 bounce 动画、双拖拽手柄（侧栏+右面板）、工作区条显隐、📚 知识库标签+来源管理、📈 用量折线图、`dialogChoose` 列表对话框 + 新会话向导、块级 Markdown 渲染 `md()`、消息操作条（复制/编辑/重新生成+`updateRegenVisibility`）、★置顶、拖拽文件入窗、浏览器多标签（brTabs/brFrames 池）、⚡快捷指令菜单、完成提示音/通知、标签页显隐 + `#tabMenu` 栏内下拉找回）；`run()` 建窗并 `webview.start()`。
- **对外接口**：`DesktopApp`、`UI_HTML`、`run`、`_validate_url`、`_fetch_text`、`_parse_market`、`THINKING_LEVELS`、`PERMISSION_MODES`、`THEME_MODES`、`MARKET_URL`。
- **依赖**：标准库 `hashlib` / `ipaddress` / `json` / `re` / `threading` / `time` / `urllib.request` / `pathlib` / `typing` / `urllib.parse`；本项目 `.exporter`（延迟）；延迟导入 `webview`（pywebview）、`nanoagent.memory.estimate_tokens`、`nanoagent.skills.SkillRegistry`、`.builtins.models.register._build_llm`。
- **被依赖**：`cli.py`（`from .desktop import run`）、`tests/test_desktop.py`、`serve_ui_preview.py`、`smoke_desktop.py`、`_diag/server.py`、`_diag/probe_real.py`。
- **影响范围**：桌面端所有交互行为、模型/插件/技能/工作区/权限/会话的加载路径；改动 `ws_tree`/`chat`/`status` 等会同时影响 UI 与 `tests/test_desktop.py`；`UI_HTML` 与后端方法名是紧耦合契约（JS 里硬编码方法名）。
- **备注**：js_api 每次调用一个线程，`chat` 用 `_lock`（RLock）串行化；流式走独立 `onStreamEvent` 通道；`_confirm`/`dialogConfirm` 通过 `evaluate_js` + 轮询 `window.__dialogResult` 实现确认对话框（无窗口时 fail-closed）；界面偏好持久化是 localStorage（try/catch 包装）+ `config.ui_prefs` 双通道（pywebview `html=` 模式 localStorage 可能因 opaque origin 不可用）；`_fetch_text`/`open_url` 有 SSRF 防护（`_validate_url`）。风险：`UI_HTML` 是巨型字符串常量，无模板/前端构建/语法检查，JS 语法错误只能在运行时暴露（可用 `.audit_tmp/check_ui_js.py` 做 node --check + md() 冒烟）。2026-09-28 四项 UI 修复：① `selectSession` 回放透传 `m.reasoning`（配合 chat_loop 落盘）重建思考块；② 子 agent 面板 `remove_subagents(ids)` + 每行 × / 🗑 清空（`removeSubagent`/`clearSubagents`）；③ `main` 补 `background:var(--panel)` 会话区与两侧同底色；④ `md()` 支持 md 表格（索引式主循环 + `isMdTableSep`/`renderMdTable`：`\|` 转义、对齐、列数补齐，`.md-table` 样式在 pre-wrap 下恢复 normal 空白）。同日新增：**停止按钮**（`stop_stream(sid)` 置 `_cancel_sessions` → worker 经 `should_stop` 透传 nanoagent，中途停止补发 `cancelled` done、部分内容不落盘；前端 `stopBtn` + `stopReq` 丢弃残余 delta）；**会话自动起名**（`_maybe_auto_title`：默认命名（「会话 」前缀）且 `config.auto_title≠false` 时，用当前模型一次调用起 ≤12 字标题，chat 在锁外调用、流式在 worker 收尾后调用）；**MCP 可视化管理**（`mcp_servers()` 掩码回显 / `save_mcp(list)` 校验+掩码还原原值+`update_config(mcpServers)`+`host.reload("mcp_client")` 热重连+`reset_agent`；设置弹窗新增 🔗 MCP 页 `renderMcpCards`/`saveMcp`，headers/env 走 JSON）。同日第二批：`ws_files`/`ws_file_text`（@引用）、`apply_code`（走 write_file 门）、`knowledge_query`（试检索）、`schedules`/`schedule_toggle`/`schedule_remove`（⏰ 面板）；UI 代码块工具条（data-code 属性）、@补全弹窗、kbq 查询行、sched 标签。同日第四十批：**`compare_models(message,a,b)`**（⚖ 并答对比：build_agent_with 临时 agent 双线程并行，纯对话不落盘不计用量，`.cmp-grid` 卡片 UI，compareFlow 对话框选对手）；**`branch_session(sid,index)`**（⎇ 分支：按可见消息过滤换算下标，复制历史前缀成新会话、原名+⎇、工作区继承，bot 消息操作条回放时出现分支按钮）。

---

## 3. 内置插件（`harness/builtins/`，16 个）

### `sahou-harness/harness/builtins/chat_loop/plugin.json`
- **用途**：chat_loop 插件清单。
- **关键内容**：`name="chat_loop"`，`description` 说明"用 nanoagent Agent 组装执行引擎"。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`（运行时读取）。
- **影响范围**：改 `name` 会改变 `sha status` 显示与主机内 `host.plugins` 键名、`tests/test_harness.py` 的断言。
- **备注**：仅 name 被内核使用，description 仅供展示。

### `sahou-harness/harness/builtins/chat_loop/register.py`
- **用途**：对话循环插件——懒构建 nanoagent `Agent`（等其它插件工具聚合后再建），并桥接步骤事件到桌面端。
- **关键内容**：`INSTRUCTIONS`（中文编程助手系统提示）；**`LONGRUN_GUIDELINES`（F2 长程执行准则：原子粒度/串行/TDD 默认失败/绿了才提交/进度写 TODO.md；`config.longrun.guidelines=false` 关）与 `_recovery_context(host)`（F3 新会话恢复：TODO.md 未完成项 + git log -5，utf8→gbk 兜底，皆空返回空串；`config.longrun.recovery=false` 关）——get_agent 里 config 读一次后按开关拼进 instructions**；`_EventTracer`（包装 nanoagent tracer，把 `llm_call`/`tool_call` 通过 `host.emit_agent_event` 实时推送，`llm` 事件带 reasoning 摘要与待调用工具名，`tool` 事件带工具名/耗时/结果首部）；`register(ctx)` 内部——`state`（agent 与 session_id 状态）、`get_agent()`（从 `models_runtime.pool` 取当前 llm，装配 `SkillRegistry`（插件技能目录 + `profile/skills`）、`Memory` 并按 session 回放历史、`Agent(..., tools=host.collect_tools(), memory=)`、`enable_skills`）、`ask(message, session_id, images)`（识别异步工具决定 `arun`/`run`，保存会话，返回 reply/reasoning/tool_calls/model/usage）、`new_session()`；最后 `provide("agent_factory"/"ask"/"new_session")`。
- **对外接口**：`register`；提供的服务 `agent_factory`、`ask`、`new_session`；`INSTRUCTIONS`、`LONGRUN_GUIDELINES`；`_EventTracer`。
- **依赖**：延迟导入 `nanoagent`（`Agent`/`Memory`/`SkillRegistry`）、`subprocess`/`pathlib`（_recovery_context）；经 `ctx.host` 使用 `profile`、`collect_skill_dirs`、`collect_tools`、`service("models_runtime")`、`emit_agent_event`。
- **被依赖**：`repl` 插件（取 `ask`/`new_session` 服务）、`desktop.DesktopApp.chat`（取 `ask`）、`models.register.set_current`（取 `agent_factory` 同步 llm）、`desktop._rebuild_pool`（取 `agent_factory`）、`status`/`usage`/`context_usage`。
- **影响范围**：对话主链路；`ask` 返回结构被 `repl`、desktop `chat`、测试共同消费；`_EventTracer` 是 "kernel→UI 实时步骤" 的唯一通道（经 `host.emit_agent_event`）。
- **备注**：Agent 懒构建（首次 `ask` 或 `agent_factory()` 才建），因此 `models` 插件先激活也行；切换模型/新会话都靠 `state["agent"]=None` 触发重建；`ask` 每次结束保存会话历史；**模块级没有 `from pathlib import Path`（原文件在函数内导入）——新函数要用 Path 必须自己本地导入**（2026-09-27 实测踩坑）。2026-09-28：ask/ask_stream 落盘前经模块级 `_attach_reasoning(history, reasoning)` 把思考过程附到最后一条 assistant 消息（Memory.history 返回副本，不污染内存）——会话回放（二次进入）能重建「深度思考」折叠块；桌面端 `selectSession` 已透传 `m.reasoning`。同日：`ask_stream`/`_stream_events` 透传 `should_stop` 给 nanoagent `run_stream`（停止按钮底座）；新增 `reset_agent` 服务（只清 agent 不动会话 id，MCP/工具集变更后刷新用）。同日第四十批：指令/技能装配抽为 `_compose_instructions`/`_build_skills_registry`（与 `build_agent_with` 共用），新增 `build_agent_with(llm, session_id, tools=None)` 服务——并答对比的临时 agent 底座（tools=[] 即纯对话，不绑 state、不挂 tracer）。

### `sahou-harness/harness/builtins/models/plugin.json`
- **用途**：models 插件清单。
- **关键内容**：`name="models"`，描述多模型池与自主/手动切换。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`、`tests/test_harness.py`。
- **影响范围**：同 chat_loop，改 name 影响状态断言。
- **备注**：无。

### `sahou-harness/harness/builtins/models/register.py`
- **用途**：模型提供者插件——从配置构建多模型池，提供 `models_runtime` 服务与自主切换工具。
- **关键内容**：`_build_llm(entry)`（provider=anthropic→`AnthropicLLM`，否则 openai 兼容 `LLM`；缺 model/api_key 抛错）；`register(ctx)`——遍历 `config["models"]` 构建 `pool`/`order`，`set_current(name)`（未知名返回错误串，否则更新 `runtime["current"]`、`update_config(default_model=name)` 持久化、同步既有 agent 的 `llm`），组装可变服务 `runtime={pool,order,current,set}`，应用 `thinking_level`→`reasoning_effort`，`provide("models_runtime", runtime)`；注册工具 `list_models` / `switch_model`；注册命令 `model`（`/model`）。
- **对外接口**：`register`；导出的服务 `models_runtime`；工具 `list_models`、`switch_model`；命令 `model`；内部 `_build_llm`（被 desktop 复用）。
- **依赖**：延迟导入 `nanoagent.AnthropicLLM`/`nanoagent.LLM`；经 `ctx.host` 使用 `profile` 与 `service("agent_factory")`。
- **被依赖**：`chat_loop.get_agent`（读 pool/current）、`desktop.status/switch_model/_rebuild_pool`（读 runtime、调用 `_build_llm`）、`cli.main`（`model list/use`）、`repl`（`/status` 读 current）。
- **影响范围**：整个模型层；`runtime` 是单一可变字典，热重建（desktop `_rebuild_pool`）直接改其 `pool/order/current`；工具 schema 变更影响 agent 能力与测试（`switch_model` 断言）。
- **备注**：`_build_llm` 是 desktop 热重建的复用点（desktop 直接 `from .builtins.models.register import _build_llm`），形成 desktop→插件模块的反向耦合；`thinking_level="off"` 时不设置 effort。

### `sahou-harness/harness/builtins/tools_fs/plugin.json`
- **用途**：tools_fs 插件清单。
- **关键内容**：`name="tools_fs"`，描述工作区路径监狱。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`、`tests/test_harness.py`。
- **影响范围**：同前述。
- **备注**：无。

### `sahou-harness/harness/builtins/tools_fs/register.py`
- **用途**：文件工具插件——提供带工作区路径监狱的读写/列文件工具，并实现 `permissions.fs` 权限门。
- **关键内容**：`_workspace()`（每次调用动态读 `host.workspace`，支持桌面热切换）；`_safe(path, must_exist)`（解析并校验不越出工作区，可选存在性）；`read_file`（带行号、截断 8000）；`write_file`（`permissions.fs`=deny→拒绝；=ask→`host.confirm` 确认，无回调或拒绝则拒；写前自动建父目录）；`list_files(pattern="**/*")`（glob，忽略 `__pycache__/.git/node_modules/.venv`）；注册三工具。
- **对外接口**：`register`；工具 `read_file`、`write_file`、`list_files`。
- **依赖**：标准库 `pathlib.Path`；经 `ctx.host` 使用 `workspace`、`profile.load_config`、`confirm`。
- **被依赖**：`chat_loop`（工具聚合）、`desktop.run_terminal`（间接）、`tests/test_harness.py::test_workspace_jail_in_tools_fs`、`tests/test_desktop.py` 的 fs 权限门与热切换用例。
- **影响范围**：文件读写安全边界；改 `_safe` 会波及越狱测试与桌面工作区热切换；权限门语义被 `set_permission("fs", ...)` 驱动。
- **备注**：读取不受权限门限制，仅写入受限（符合 README 描述）；`write_file` 返回 "已写入 X（N 行）" 字符串被测试断言（`test_tool_call_roundtrip`）。

### `sahou-harness/harness/builtins/tools_shell/plugin.json`
- **用途**：tools_shell 插件清单。
- **关键内容**：`name="tools_shell"`，描述权限门。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`、`tests/test_harness.py`。
- **影响范围**：同前述。
- **备注**：无。

### `sahou-harness/harness/builtins/tools_shell/register.py`
- **用途**：Shell 工具插件——在工作区执行命令，受 `permissions.shell` 权限门控制。
- **关键内容**：`run_command(command, timeout=60)`——读配置取 `shell` 模式（deny→拒；ask→`host.confirm`，无回调或拒则拒）；`subprocess.run(shell=True, cwd=host.workspace, capture_output/text, timeout, encoding)`；处理 `FileNotFoundError`/`TimeoutExpired`；输出截断 4000 并附 exit code；注册工具 `run_command`。
- **对外接口**：`register`；工具 `run_command`。
- **依赖**：标准库 `subprocess`；经 `ctx.host` 使用 `profile.load_config`、`confirm`、`workspace`。
- **被依赖**：`chat_loop` 工具聚合、`desktop.run_terminal`（按名查找 `run_command` 复用权限门）、`tests/test_harness.py::test_shell_permission_gate`、`tests/test_desktop.py::test_terminal_reuses_shell_gate`。
- **影响范围**：命令执行安全；桌面端右侧"终端"页直接复用它，因此权限门语义同时约束 CLI 与桌面。
- **备注**：`shell=True` + `cwd=host.workspace`；无窗口（CLI/桌面无窗）时 ask 一律 fail-closed；返回串包含 "拒绝" 字样被测试依赖。

### `sahou-harness/harness/builtins/skills/plugin.json`
- **用途**：skills 插件清单。
- **关键内容**：`name="skills"`，描述 SKILL.md 渐进式披露。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`、`tests/test_harness.py`。
- **影响范围**：同前述。
- **备注**：无。

### `sahou-harness/harness/builtins/skills/register.py`
- **用途**：技能插件——声明 profile 的 `skills/` 目录为技能源。
- **关键内容**：`register(ctx)`：`ctx.skills.add_dir(str(profile/skills))`；用 `if profile_skills.is_dir() or True` 保证目录不存在也声明（用户放入 SKILL.md 后重启即生效）。
- **对外接口**：`register`（无工具/服务，仅声明技能目录）。
- **依赖**：标准库 `pathlib.Path`；经 `ctx.host.profile.root`。
- **被依赖**：`chat_loop.get_agent`（`host.collect_skill_dirs()` 汇总后建 SkillRegistry）、`cli.main` 的 `skill list`、`desktop.skills()`。
- **影响范围**：技能来源之一；`or True` 恒真分支是刻意的（消除 is_dir 判断），修改需谨慎。
- **备注**：`or True` 使 `if` 恒真，属"有意保留但易被误读"的写法。

### `sahou-harness/harness/builtins/mcp_client/plugin.json`
- **用途**：mcp_client 插件清单。
- **关键内容**：`name="mcp_client"`，描述 stdio/SSE/HTTP 接入。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`。
- **影响范围**：注意 `tests/test_harness.py` 的 `test_builtin_plugins_all_activate` 并未断言 `mcp_client`（因其在无 `mcpServers` 时 `register` 直接 return，但仍会被激活——它没有 skip：见备注）。
- **备注**：无 server 时 `register` 提前 return，插件仍处于 ACTIVE。

### `sahou-harness/harness/builtins/mcp_client/register.py`
- **用途**：MCP 客户端插件——连接配置里的 MCP 服务器，工具并入 agent 工具集，连接以 effect 管理。
- **关键内容**：读 `config["mcpServers"]`，无则 return；`disconnect_all()`（对每个连接 `asyncio.run(server.disconnect())`）；`connect_all()`（按 `url` 判定 HTTP/SSE、否则 stdio 建连，收集 `server.tools()`，单服务器失败记入 `ctx.skipped`，注册工具，返回 `dispose`）；`ctx.effect(connect_all)` 确保卸载自动断开。
- **对外接口**：`register`；动态注册的 MCP 工具（名字由服务器决定）。
- **依赖**：标准库 `asyncio` / `typing`；延迟导入 `nanoagent.mcp.MCPServer`；经 `ctx.host.profile`。
- **被依赖**：`chat_loop` 工具聚合；卸载路径由 `kernel.Context.deactivate` 的 LIFO disposer 驱动。
- **影响范围**：MCP 工具接入与连接生命周期；配置字段 `mcpServers`（`url`/`type`/`headers`/`command`/`args`/`env`）。
- **备注**：`ctx.effect` 的典型用法示例（disposer 由内核 LIFO 管理）；`asyncio.run` 在同步 register 中反复建事件循环，连接较多时开销较高；`ctx.skipped` 记录失败但不使插件 FAILED。

### `sahou-harness/harness/builtins/repl/plugin.json`
- **用途**：repl 插件清单。
- **关键内容**：`name="repl"`，描述终端交互界面。
- **对外接口**：`name`、`description`。
- **依赖**：无。
- **被依赖**：`kernel.load_manifest`、`tests/test_harness.py`（断言 `ui` 服务）。
- **影响范围**：同前述。
- **备注**：无。

### `sahou-harness/harness/builtins/repl/register.py`
- **用途**：REPL 插件——终端交互界面（UI 本身也是插件，可整体替换）。
- **关键内容**：`register(ctx)` 内 `run_ui(once_message)`：取 `ask`/`new_session` 服务；`print_help`/`run_command` 处理 `/exit` `/new` `/sessions` `/resume` `/usage` `/image` `/reload` `/plugins` `/status` **`/snip`（2026-09-27：list/add/del/按名发送快捷指令，走 harness.snippets）** 与其它插件注册的斜杠命令；一次性模式直接 `ask(message, session_id)` 打印 reply；交互循环读取输入、`/` 开头走命令、否则 `ask`；最后 `ctx.provide("ui", run_ui)`。
- **对外接口**：`register`；服务 `ui`（签名 `run_ui(once_message: str | None)`）。
- **依赖**：经 `ctx.host` 使用 `service("ask"/"new_session"/"models_runtime")`、`host.harness.collect_commands()/list()`（注意用的是 `host.harness`）。
- **被依赖**：`cli.main`（默认 chat 路径取 `ui` 服务，`None`→交互、字符串→单次）。
- **影响范围**：CLI 默认界面；`host.harness` 属性访问依赖 `Context.host` 指向 `Harness` 且有 `harness` 属性——**这是一个潜在风险点**：`Harness` 未定义 `harness` 属性，`/plugins` 与 `/model` 帮助路径可能 `AttributeError`（仅在实际进入该分支时才触发）。
- **备注**：`session_id` 固定 `"default"`；`/exit` 用 `raise SystemExit` 再捕获优雅退出。

### `sahou-harness/harness/builtins/browser/*`
- **用途**：browser 插件（2026-09-27 功能6）——`fetch_url(url, max_chars)` 抓网页转纯文本。
- **关键内容**：仅 http/https；可选 `config.browser.allowed_domains` 白名单（精确或子域后缀）；httpx Client GET（15s 超时、跟随重定向、5MB 上限）；HTML 去标签（script/style/noscript 剔除、块级标签转行、实体解码、相邻重复行折叠）；超时/非 2xx/超限返回可读中文错误。
- **对外接口**：工具 `fetch_url`（schema：url / max_chars=8000，上限 50000）。
- **依赖**：延迟导入 `httpx`（openai 既有依赖）、`html`/`re`/`urllib.parse`。
- **被依赖**：`tests/test_new_plugins.py::BrowserTests`（本地 http.server 当页面）。
- **影响范围**：给模型的联网能力面；白名单配置错误会意外放行/拦死。
- **备注**：用 `with httpx.Client(...)` 保证连接关闭（首版直接 `httpx.get` 留 ResourceWarning）。

### `sahou-harness/harness/builtins/notifications/*`
- **用途**：notifications 插件（2026-09-27 功能4）——`notify(message, title)` 向配置的 webhook POST JSON。
- **关键内容**：config `notifications.url` 必填（缺省→`ctx.skipped` 记 `not-configured` 并缺席）；载荷 `{title, message, source, ts}`（正文截断 4000 字符）；`on_error=true` 时 `ctx.on("error", ...)` 订阅宿主错误事件推送告警（推送失败只吞不炸）；`timeout` 可配（1~60s，默认 10）。
- **对外接口**：工具 `notify`；服务 `notify`。
- **依赖**：延迟导入 `httpx`；`ctx.on` 的 disposer 由内核账本管理。
- **被依赖**：`tests/test_new_plugins.py::NotificationTests`（本地 ThreadingHTTPServer 收 POST）。
- **影响范围**：外发网络副作用；url 配错只让 notify 返回可读错误，不影响对话。
- **备注**：消息截断与 2xx 判定都在插件内完成。

### `sahou-harness/harness/builtins/scheduler/*`
- **用途**：scheduler 插件（2026-09-27 功能5）——定时任务到点用独立 agent 执行提示词。
- **关键内容**：daemon worker 线程每秒 tick、每轮重新读 `tasks.json`（CLI 增删即时生效）；到期判定在 `schedule_store.due_tasks`；**每个任务新建独立 Agent**（全新 Memory + collect_tools + skills，不复用主界面 agent——防串味与状态竞争）；单线程串行执行（副作用不可重入）；结果/失败都追加写 `scheduled/<名>.log`，并回写 `last_run` 与 `runs` 摘要；`ctx.effect(_start)` 启动线程、返回 stop disposer（LIFO 回滚，join 5s）。
- **对外接口**：无工具/服务（纯后台效果插件）。
- **依赖**：`harness.schedule_store`（绝对导入）；`host.service("models_runtime"/"guardrails")`、`host.collect_tools()/collect_skill_dirs()`。
- **被依赖**：`tests/test_new_plugins.py::SchedulerPluginTests`（间隔 1s 端到端触发）。
- **影响范围**：常驻线程生命周期；激活即启动，卸载必须 join 成功。
- **备注**：读盘失败按空列表处理，坏任务（间隔非法）被 `due_tasks` 跳过不拖垮调度。

### `sahou-harness/harness/builtins/guardrails/*`
- **用途**：guardrails 插件（批次 E）——从 config 的 `guardrails` 段构建输入/输出护栏，服务名 `guardrails`。
- **备注**：批次 E 聚合补账条目（此前漏索引）；细节见 register.py 头注释与 `tests/test_harness.py`。

### `sahou-harness/harness/builtins/tools_search/*`
- **用途**：tools_search 插件（批次 E）——`search_text` 全工作区 grep 式检索（glob/正则/上限），工具安全依赖 `harness.workspace`。
- **备注**：批次 E 聚合补账条目。

### `sahou-harness/harness/builtins/tools_todo/*`
- **用途**：tools_todo 插件——**TODO.md 工作区任务索引**（2026-09-27 长程任务架构 F1 重写：原纯内存态 → 持久化 `<工作区>/TODO.md`，Markdown 勾选格式 `- [ ]/- [~]/- [x]/- [-]`，人可读、Git 可跟踪、跨会话不丢）。
- **关键内容**：`_parse_md`（容错解析手写文件，`——` 后为 detail）、`_render`（兼容旧格式 `[ ] 1. 标题` + 进度行）、`_render_md`（写盘格式，含 `# TODO` 头）；`todo_write`（整单覆盖，STATUS_ALIASES 中英文状态别名，MAX_ITEMS=50）、`todo_read`；`ctx.provide("todos", {path})`。
- **备注**：桌面端「✅ 任务」面板经 `DesktopApp.todo_content` 直接读同一文件；新会话恢复（chat_loop._recovery_context）也读它——**它是无状态重置闭环的数据地基**。

### `sahou-harness/harness/builtins/tools_git/*`
- **用途**：tools_git 插件（2026-09-27 长程任务 F4）——受限 git：`git_status`/`git_diff`/`git_log`（只读，deny 时全拒）+ `git_add`/`git_commit`（走 `permissions.git = ask/allow/deny` 门，ask 经 host.confirm fail-closed）。
- **关键内容**：白名单五操作，**无 push/reset/checkout**；`git.test_command` 提交测试门（shell=True 跑，非零拒绝并回显输出尾部 1500 字）；commit 顺序 = 空消息 → 暂存区检查（`diff --cached --quiet`）→ 权限门 → 测试门 → 提交（只提交已暂存，不 `-a`）；`_decode` utf8→gbk 兜底；`/git` 命令查权限与测试门。
- **对外接口**：工具 `git_status`/`git_diff`/`git_log`/`git_add`/`git_commit`；命令 `git`。
- **依赖**：`harness.config.permission_mode`；标准库 subprocess。
- **被依赖**：desktop 权限菜单（GIT 提交分区）、`tests/test_new_plugins.py::ToolsGitTests`。
- **影响范围**：agent 获得了**写仓库**的能力——权限门与测试门的实现改动直接改变安全边界。
- **备注**：新增 `permissions.*` 键必须同步 `_normalize_permissions`（本次就踩了 H-07 同类静默丢弃）。

### `sahou-harness/harness/builtins/tracing/*`
- **用途**：tracing 插件（批次 E）——按天 JSONL 追踪，服务 `tracing.new_tracer`，`sha trace` 读摘要。
- **备注**：批次 E 聚合补账条目。

### `sahou-harness/harness/builtins/subagent/*`
- **用途**：subagent 插件（批次 E）——`spawn_subagent` 子 agent（复用主模型与工具，剪掉递归工具）。
- **备注**：批次 E 聚合补账条目。2026-09-28：`_record` 给每条记录加 `id`（uuid 短哈希）——桌面端「子 agent」面板支持按行移除（`remove_subagents(ids)` 过滤 + tmp 原子替换重写 jsonl）与 🗑 清空全部（ids 为空 → unlink）；旧版无 id 记录只能整表清空。同日第二批：desktop 新增 `ws_files(limit)`（扁平清单，@补全数据源）/`ws_file_text(path,max_chars)`（原文读取，监狱+截断）/`apply_code(path,content)`（走 write_file 工具：权限门+checkpoint）/`knowledge_query(query,k)`（试检索，直接调 search_knowledge 工具）/`schedules()`/`schedule_toggle(name,enabled)`/`schedule_remove(name)`（复用 schedule_store）；UI：代码块工具条（复制/应用到文件，原文存 `data-code` 属性防流式重渲染膨胀）、📚 知识库试检索行、⏰ 定时面板新标签（列表/启停/移除）、@补全弹窗（`atState`+方向键/Tab 选择，发送时 `expandAtRefs` 展开最多 3 个文件×12k 字符）。

### `sahou-harness/harness/builtins/knowledge/*`
- **用途**：knowledge 插件（RAG）——`index_knowledge`/`search_knowledge` 工具 + `host.service("knowledge")` 宿主服务，基于 nanoagent.rag（numpy/faiss 双后端，OpenAI 兼容 /embeddings，KB 惰性构建）。
- **关键内容**：`TEXT_SUFFIXES`/`MAX_INDEX_FILES=200`；`_kb()`（惰性建 KnowledgeBase，persist_path=`<profile>/knowledge/index.npz`）；`search_knowledge(query,k)`；`index_knowledge(path)`（工作区内，走 safe_path 监狱）；`_index_target(target, kb)`（工具与服务共用的索引实现）；`index_absolute(path)`（**仅供桌面端**：用户亲自选的目录，允许工作区外，不注册进 ctx.tools，不构成绕过监狱的通道）；`clear_knowledge()`（删 `index.npz*` 并重置内存库）；`status()`（不强制构建 KB——空库/磁盘 JSON 数 chunks/faiss 记 -1）；**`knowledge_sources()`（按 metadata.source 汇总来源片段数，内存库优先否则读持久化索引）/ `knowledge_remove_source(name)`（按 source 过滤重建 store，其余来源保留并 kb.save() 落盘；无可删报「错误：」前缀）**；`ctx.provide("knowledge", {status,index,index_absolute,clear,sources,remove_source})`；命令 `knowledge`。
- **对外接口**：工具 `index_knowledge`、`search_knowledge`；服务 `knowledge`；命令 `knowledge`；常量 `TEXT_SUFFIXES`、`MAX_INDEX_FILES`。
- **依赖**：延迟导入 `nanoagent.rag.KnowledgeBase`；`harness.workspace`（safe_path/iter_files/read_text_file/relative）。
- **被依赖**：desktop（knowledge_status/pick_index/clear 经 host.service）、`tests/test_new_plugins.py::KnowledgeServiceTests`。
- **影响范围**：工具 schema 与服务签名变更波及 agent 能力、桌面知识库面板与测试；`index.npz` 文件格式由 nanoagent.rag 决定。
- **备注**：插件由 loader 以合成模块名加载，只能绝对导入；`enabled=false` 时缺席（status 可见）。

---

## 4. 测试

### `sahou-harness/harness/workspace.py`
- **用途**：工作区路径监狱与文件遍历——所有文件类插件共用的唯一实现（防止越界判定散落各插件）。
- **关键内容**：`safe_path`（解析+越界判定）、`guard_pattern`（glob 不得含 `..`/绝对路径）、`iter_files`（跳过 IGNORED_PARTS）、`relative`、`read_text_file`（二进制/超大返回 None）；2026-09-27 新增 `safe_image` / `safe_images`（多模态图片源校验：URL 放行、本地路径须在监狱内且扩展名 ∈ png/jpg/jpeg/gif/webp）。
- **对外接口**：`safe_path`、`guard_pattern`、`iter_files`、`relative`、`read_text_file`、`safe_image`、`safe_images`。
- **依赖**：标准库 pathlib/collections.abc。
- **被依赖**：tools_fs、tools_search、chat_loop（图片校验）、repl（/image）、desktop（check_image）、scheduler 间接。
- **影响范围**：任何越界判定收紧/放宽都直接改变工具安全边界。
- **备注**：`workspace_root` 每次动态读 `host.workspace`（支持桌面热切换）。

### `sahou-harness/harness/schedule_store.py`
- **用途**：定时任务的存储层（2026-09-27 功能5）——scheduler 插件与 `sha schedule` CLI 共用的 tasks.json 读写/校验。
- **关键内容**：`tasks_path`/`load_tasks`/`save_tasks`（原子写）；`add_task`/`remove_task`（重名拒绝）；`set_task_enabled(profile,name,enabled)`（pause/resume：只翻 enabled 不动 last_run）；`TASK_NAME_RE` 白名单（中英文/数字/._-，禁路径分隔符——对齐 H-04 教训，任务名即日志文件名）；`validate_every`（1 秒~30 天）；`due_tasks(tasks, now)` 纯函数（enabled 且 now-last_run>=every，坏间隔跳过）；`ScheduleError`。
- **对外接口**：`add_task`、`remove_task`、`set_task_enabled`、`load_tasks`、`save_tasks`、`due_tasks`、`ScheduleError`。
- **依赖**：`harness.config.atomic_write_text`。
- **被依赖**：`harness/builtins/scheduler/register.py`、`harness/cli.py::_schedule`、`tests/test_new_plugins.py::ScheduleStoreTests`。
- **影响范围**：任务文件格式变更会同时影响插件与 CLI。
- **备注**：损坏的 tasks.json 读作空列表（调度线程不崩），不静默回写；worker 每轮 tick 重读盘，pause/resume 对运行中的 harness 立即生效。

### `sahou-harness/harness/bootstrap.py`
- **用途**：工程脚手架（2026-09-27 长程任务 F5）——Bootstrap 工作流前 4 步的确定性部分，CLI `sha bootstrap` 与桌面端 `bootstrap_project` 共用。
- **关键内容**：`run_bootstrap(workspace, goal)`——只增量创建 `src/tests/docs`、`.gitignore`、README（有目标且不存在时），git init + add -A + 基线提交（`chore: 工程基线` 或目标前 60 字）；commit 失败不算整体失败（脚手架已就绪，错误带回）。TODO.md 的原子任务拆解交 agent（调用方再发一轮对话）。
- **对外接口**：`run_bootstrap`、`GITIGNORE`。
- **依赖**：标准库 subprocess/pathlib。
- **被依赖**：`harness/cli.py::main(bootstrap 分支)`、`harness/desktop.py::bootstrap_project`、`tests/test_new_plugins.py::BootstrapTests`。
- **影响范围**：会向用户工作区写文件并 git 提交——只新增不覆盖是硬约定。
- **备注**：桌面端在脚手架成功后用当前会话让 agent 生成 TODO.md（走 F1 的 todo_write）。

### `sahou-harness/harness/procutil.py`
- **用途**：subprocess 辅助（2026-09-27）——抑制 GUI（--noconsole）进程里 spawn 控制台程序时的黑色 conhost 窗口闪现。
- **关键内容**：`CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)`（非 Windows 为 0）；子进程照常运行、输出照常被管道捕获，只是不显示窗口。
- **对外接口**：`CREATE_NO_WINDOW`。
- **依赖**：标准库 subprocess。
- **被依赖**：chat_loop（_recovery_context）、tools_git（×2）、tools_shell（Popen）、desktop（_git_run/review/market clone）、bootstrap、config（插件 git 克隆）。
- **影响范围**：新增任何 subprocess 调用都必须传 `creationflags=CREATE_NO_WINDOW`，否则 GUI 下闪黑窗。
- **备注**：根因是 Windows 对无控制台父进程的子进程临时分配 conhost；2026-09-27 修复「每次启动黑窗闪现」。

### `sahou-harness/harness/exporter.py`
- **用途**：会话导出与用量统计——CLI `sha export/usage` 与桌面端「📤 导出会话 / 🗂 导出全部 / 📈 用量图表」共用的唯一实现（2026-09-27）。
- **关键内容**：`usage_records(profile)`（读 `<profile>/usage.jsonl`，坏行跳过）；`session_markdown(profile, sid, include_usage=True)` 纯函数（生成 Markdown 全文不落盘，空会话抛 FileNotFoundError）；`export_session_markdown(...)` 写 `<out_dir>/<sid>.md`；`export_all_sessions_zip(profile, out_path)`（每会话一个 md + index.md 目录打包 zip，空会话跳过，全空抛 ValueError）；`usage_daily(profile, days=30)`（按本地日聚合，空档天补齐 → [{day, calls, prompt, completion, total}]）。
- **对外接口**：`usage_records`、`session_markdown`、`export_session_markdown`、`export_all_sessions_zip`、`usage_daily`、`ROLE_LABELS`。
- **依赖**：`harness.config.Profile`；标准库 zipfile / datetime（延迟导入）。
- **被依赖**：`harness/cli.py::_export_sessions/_usage_summary`、`harness/desktop.py::export_session/export_all_sessions/usage_daily`、`tests/test_harness.py::ExportUsageTests`、`tests/test_desktop.py::Batch11FeatureTests`。
- **影响范围**：导出 Markdown 格式、zip 结构或 usage.jsonl 字段变更会同时影响 CLI 与桌面端展示。
- **备注**：从 cli.py 的重复实现重构而来；会话加载复用 `profile.load_session`（自带 id 白名单）。

### `sahou-harness/harness/snippets.py`
- **用途**：快捷指令（常用提示词片段）存储层（2026-09-27 第六批）——桌面端 ⚡ 菜单与 REPL `/snip` 共用，存 profile config.json 的 `snippets` 键。
- **关键内容**：`snippets_list(profile)`（读+规整，坏配置按空处理）；`snippets_save(profile, name, text)`（同名覆盖；mutate_config 内校验上限 MAX_SNIPPETS=100，超限 ValueError 不落盘）；`snippets_delete(profile, name)`（幂等）；名称/文本截断 MAX_NAME=60 / MAX_TEXT=8000；`_normalize` 去残缺去重。
- **对外接口**：`snippets_list`、`snippets_save`、`snippets_delete`、常量。
- **依赖**：`harness.config.Profile.mutate_config`（同一把锁内的读-改-写）。
- **被依赖**：`harness/desktop.py::snippets_list/save/delete`、`harness/builtins/repl/register.py::run_snip`、`tests/test_desktop.py::Batch11FeatureTests`。
- **影响范围**：`snippets` 键结构变更会同时影响桌面端菜单与 REPL 命令。
- **备注**：不自己碰文件，全部走 Profile 锁；上限校验在 mutator 内抛 ValueError 以保证原子性。

### `sahou-harness/tests/test_harness.py`
- **用途**：内核生命周期、插件装载、模型切换、权限门、端到端对话的离线单元测试。
- **关键内容**：`FakeLLM`（可脚本化 `chat`，带 `total_usage`）；`make_profile` / `build_host` / `patch_model_build`（替换 `nanoagent.LLM` 为 FakeLLM）；测试类 `KernelTests`（mount→activate→dispose 生命周期、effect LIFO 且幂等、失败插件不拖垮其它、事件 emit）、`BuiltinPluginsTests`（内置插件全激活、工具聚合含 read/write/run/switch、模型切换持久化并更新 agent、shell 权限门、tools_fs 工作区越狱）、`EndToEndTests`（单次 chat 使用假模型、工具调用往返写文件）、`ProfileTests`（插件安装/移除、配置往返）。
- **对外接口**：`FakeLLM`、`make_profile`、`build_host`、`patch_model_build`（被 `test_desktop.py` 与 `smoke_desktop.py` 复用）。
- **依赖**：标准库 `json` / `os` / `sys` / `tempfile` / `unittest` / `pathlib`；`harness.config.Profile`、`harness.kernel`、`nanoagent.llm.LLMResponse`；延迟导入 `harness.cli`、`nanoagent`、`nanoagent.tools.Tool`。
- **被依赖**：`tests/test_desktop.py`（`from test_harness import build_host, make_profile, patch_model_build`）、`smoke_desktop.py`、`run_tests.py`（discover）。
- **影响范围**：内核/插件/配置任一契约变更都会使此文件失败；`test_builtin_plugins_all_activate` 断言 6 个插件名 ACTIVE（不含 mcp_client/repl 之外——实际列出 chat_loop/models/tools_fs/tools_shell/skills/repl）。
- **备注**：全部离线（假模型），无需 API Key；`patch_model_build` patch 的是 `nanoagent.LLM` 包属性，依赖 models 插件运行期 `from nanoagent import LLM` 的写法。

### `sahou-harness/tests/test_desktop.py`
- **用途**：桌面端进程内 API 的单元测试（不依赖真实窗口）。
- **关键内容**：`FakeWindow`（模拟 `evaluate_js` 轮询对话框）；`DesktopApiTests` 覆盖——status/get_models、chat 往返+reasoning+会话持久化、chat 错误不抛、会话切换回放、会话重命名与 meta、**会话删除（文件+meta 清理、删当前自动切换、meta-only 会话可删、穿越 id 拒绝）**、ui_prefs 往返与校验、导出会话到 `<工作区>/exports`、流式（can_stream/delta+done/错误转 done）、save_models 校验+热重建+switch_model、thinking 级别应用到 pool、usage/context_usage、权限往返 shell/fs、fs 写权限门（ask 无确认拒绝/allow 写入）、页内确认对话框、工作区注册与重命名、工作区热切换更新监狱、choose_workspace 无窗口、插件安装/移除、主题持久化与校验、`_validate_url` 阻断私网/非 http、`_parse_market`、市场缓存/取错误/拒不安全 URL/克隆安装、`ws_tree` 列出与越狱、终端复用 shell 门、review 需 git、技能安装/列出/移除、chat 步骤事件。
- **对外接口**：`FakeWindow`、`DesktopApiTests`。
- **依赖**：标准库 `os` / `sys` / `tempfile` / `unittest` / `pathlib` / `shutil` / `subprocess` / `unittest.mock`；`test_harness`（build_host/make_profile/patch_model_build）；延迟导入 `harness.desktop`、`harness.cli`、`nanoagent.llm`。
- **被依赖**：`run_tests.py`（discover）。
- **影响范围**：桌面端任意 API 方法签名/返回结构变更都会波及；尤其是 `ws_tree`（`test_ws_tree_lists_and_jails`）与 chat 事件（`test_chat_emits_step_events`）。
- **备注**：`test_ws_tree_lists_and_jails` 精确断言"点开头条目被隐藏、目录排前、rel 用 posix"——是排查右侧文件区 bug 时最相关的既有回归网。

### `sahou-harness/tests/test_new_plugins.py`
- **用途**：功能4-7 的回归测试（2026-09-27）：通知 webhook / 定时任务 / fetch_url / 多模态图片输入。
- **关键内容**：`_Recorder`（本地 ThreadingHTTPServer，类属性收 POST/GET）；`NotificationTests`（未配置缺席 / POST 载荷断言 / error 事件推送）；`ScheduleStoreTests`（增删校验、due_tasks 纯函数、pause/resume）；`KnowledgeServiceTests`（knowledge 服务：空库 status、index_absolute 路径守卫、clear）；`SchedulerPluginTests`（间隔 1s 端到端：15s 内日志落盘 + last_run/runs 回写）；`BrowserTests`（HTML→文本、实体解码、script 剔除、重复行折叠、拒非 http、404 可读、域名白名单）；`MultimodalTests`（safe_image 监狱、CapturingLLM 验证多模态 content 数组、越界图片 ValueError、URL 透传）。
- **对外接口**：无（测试）。
- **依赖**：`test_harness`（build_host/make_profile/patch_model_build）；`harness.schedule_store`、`harness.workspace`；`nanoagent.llm.LLMResponse`、`nanoagent.media.make_png`。
- **被依赖**：`run_tests.py`（discover）。
- **影响范围**：三个新插件与 chat_loop images 参数的契约变更都会波及。
- **备注**：`Tool.invoke` 是 `invoke(arguments: dict)`——不是 kwargs（曾在此翻车）；全部离线。

---

## 5. 打包与工具脚本（已收敛到 `tools/`）

### `sahou-harness/tools/*`
- **用途**：开发/打包/测试辅助脚本的统一目录（2026-09-26 批次 F 从仓库根 `git mv` 进来；7 个文件：`build_exe.py` / `run_tests.py` / `launcher_sha.py` / `launcher_desktop.py` / `make_icon.py` / `serve_ui_preview.py` / `smoke_desktop.py`）。
- **关键内容**：`build_exe.py`（PyInstaller 打包 sha.exe / ShaDesktop.exe，`--add-data harness/builtins` 是内置插件进 exe 的命门）；`run_tests.py`（unittest discover，测试唯一正规入口）；`launcher_sha.py`/`launcher_desktop.py`（exe 控制台/无控制台入口）；`make_icon.py`（生成 assets/sha.ico，Pillow，font.getsize 有弃用风险）；`serve_ui_preview.py`（浏览器 + 有状态 mock 预览 UI_HTML，8642 端口）；`smoke_desktop.py`（真开 pywebview 窗口冒烟 status 桥接）。脚本内 ROOT 一律 `Path(__file__).resolve().parent.parent`（git mv 时已改，无硬编码绝对路径）。
- **对外接口**：`python tools/<脚本>.py`。
- **依赖**：`harness.cli` / `harness.desktop.UI_HTML` / `test_harness`；外部 PyInstaller / Pillow / webview。
- **被依赖**：CI（run_tests.py）、打包流程（build_exe.py、launcher_*）。
- **影响范围**：打包产物与测试入口；UI_HTML 的 DOM/JS 契约变更需同步 serve_ui_preview 的 MOCK。
- **备注**：旧的 `build_pyi/*.spec`（生成物、硬编码绝对路径）与 `_diag/*`（6 个诊断临时产物）已随批次 F 清理从磁盘删除，对应条目同步移除；仓库根同名脚本条目已废弃（位置变更为 tools/）。


### 6.1 `Harness` 宿主 API

`Harness`（kernel.py:173-295）是宿主编排者，本身不含业务逻辑：

| 方法 | 行号 | 语义 |
| --- | --- | --- |
| `mount(path, name=None)` | 184-198 | 装载一个插件目录（**不激活**）；用 `loader.load_manifest` 定名，重名自动加 `-2/-3...` 后缀，登记 `PluginRecord(state=PENDING)`。 |
| `mount_all(directory)` | 200-208 | 扫描目录下含 `plugin.json` 或 `register.py` 的子目录并逐个 `mount`（按名排序）。 |
| `activate(name)` | 211-247 | 建 `Context` → `loader.run_register` → 成功则 `state=ACTIVE` 并聚合 `provided`；失败则 `ctx.deactivate()` 回滚、`state=FAILED`、记 `error`、`bus.emit("error")`，**不外抛**。 |
| `activate_all()` | 249-250 | 对当前全部插件 `activate`。 |
| `deactivate(name)` | 252-266 | `ctx.deactivate()`（LIFO 回滚）→ `state=DISPOSED` → **从仍 ACTIVE 的插件重建整个 `self.services`** → `bus.emit("deactivate")`。 |
| `collect_tools()` | 269-274 | 汇总全部 ACTIVE 插件的 `tools_list`。 |
| `collect_skill_dirs()` | 276-281 | 汇总 ACTIVE 插件的技能目录。 |
| `collect_commands()` | 283-289 | 汇总 ACTIVE 插件的斜杠命令表。 |
| `service(name, default=None)` | 291-292 | 从服务注册表取名。 |
| `list()` | 294-295 | 返回全部 `PluginRecord.summary()`。 |

宿主字段：`bus`（`EventBus`）、`plugins`（name→`PluginRecord`）、`services`（服务注册表）、`profile`（运行时由 cli 注入）、`confirm`（权限确认回调，REPL/桌面端注入）。另外 cli/desktop 会动态挂 `workspace`、`emit_agent_event` 等属性。

### 6.2 `Context` 三原语（`ctx.provide` / `ctx.on` / `ctx.effect`）

`Context`（kernel.py:99-150）是插件与宿主交互的**唯一边界**：

| 原语 | 行号 | 语义 |
| --- | --- | --- |
| `provide(name, service)` | 122-130 | 把服务写入 `ctx.services[name]`，同时把"移除该服务"作为 disposer 推入账本；返回该 disposer。 |
| `on(event, handler)` | 132-134 | 委托 `bus.on` 订阅宿主事件（`activate`/`deactivate`/`error`），返回退订 disposer。 |
| `effect(fn)` | 136-140 | 执行 `fn()`，若其返回 disposer 则记入账本（对齐 dsh 的 `ctx.effect`）——用于"注册即产生副作用、卸载需回收"的资源（典型：`mcp_client` 的连接）。 |
| `deactivate()` | 143-150 | **LIFO** 弹出并执行全部 disposer，异常被吞，**幂等**（重复调用为空操作）。 |

因 `provide`/`effect`/`on` 都会把 disposer 记入同一个 `_disposers` 账本，`activate` 失败时一次 `ctx.deactivate()` 即可把所有已产生的副作用全部回滚。

### 6.3 插件状态机

- `PENDING`（code 21）：已 `mount`，未 `activate`。
- `ACTIVE`（22）：`run_register` 成功；`ctx` 非空；参与 `services/tools/skills/commands` 聚合。
- `FAILED`（23）：`run_register` 抛异常；`ctx` 置空；`error` 记录异常串；**不拖垮其它插件**（`activate` 不外抛）。
- `DISPOSED`（24）：`deactivate` 后；`provided` 清空；`ctx` 置空；`desktop.plugins()` 会过滤掉 DISPOSED 的插件。

状态转移：`PENDING →[activate成功]→ ACTIVE →[deactivate]→ DISPOSED`；`PENDING →[activate失败]→ FAILED`。注意 `activate` 对已 ACTIVE 是 no-op；对 FAILED/DISPOSED 再次 `activate` 会重新建 ctx 并尝试。`deactivate` 后若再 `activate` 同名插件，`plugins` 字典中仍是同一条 record（name 未变），会重新装载。

### 6.4 `loader.py` 如何发现并加载插件

1. **发现**：`Harness.mount_all(dir)` 遍历子目录，只要含 `plugin.json` **或** `register.py` 即视为插件；`mount` 调 `load_manifest` 读清单，缺失/坏 JSON 时回落到 `{"name": <目录名>}`。
2. **定名**：`name` 取参数 > `manifest["name"]` > 目录名；重名加 `-N` 后缀。
3. **装载（激活时）**：`run_register(record, ctx)`：
   - 无 `register.py` → 直接 return；
   - 用 `importlib.util.spec_from_file_location("harness_plugin_<name>_<uuid8>", register.py)` 以**唯一模块名**从文件路径加载（因此插件不能用包内相对导入）；
   - `sys.modules[module_name]=module` 后 `exec_module`；exec 失败则 `pop` 清理并向上抛（由 `Harness.activate` 捕获为 FAILED）；
   - 取模块级 `register` 可调用对象并调用 `register(ctx)`；
   - 兼容模块级 `TOOLS` 列表，逐个 `ctx.tools.register`；
   - 若既无 `register` 又未注册任何工具 → `ctx.skipped.append("no-entry: ...")`。
4. **聚合**：`activate` 从 `ctx` 收集 `tools/services/models/commands` 写入 `record.provided`，并把服务合入 `self.services`（**后激活者覆盖同名服务**）。

---

## 7. `desktop.py` 专项拆解

文件共 **2089 行**，分为三大块：后端 `DesktopApp`（纯 Python，可离线测试）、渲染层 `UI_HTML`（CSS+HTML+JS 单页常量）、窗口入口 `run()`。

### 7.1 段落结构（行号区间）

| 区间 | 内容 |
| --- | --- |
| 1-9 | 模块 docstring（形态/用法） |
| 11-22 | import（hashlib/ipaddress/json/re/threading/time/urllib/pathlib/typing/urlparse） |
| 24-28 | 常量 `THINKING_LEVELS` / `PERMISSION_MODES` / `THEME_MODES` / `MARKET_URL` |
| 31-50 | `_validate_url`（SSRF 防护） |
| 53-57 | `_fetch_text`（带 UA 的 urllib 取文） |
| 60-76 | `_parse_market`（解析 awesome-dsh-plugin README） |
| 84-664 | `class DesktopApp`（**后端 API 层**） |
| 672-2055 | `UI_HTML = r"""..."""`（**渲染层**，一个巨型字符串常量） |
| ├ 673-1052 | `<style>...</style>`（**CSS**，第 673 行起，`</style></head><body>` 在 1053） |
| ├ 1054-1231 | `<body>` 的 **HTML 结构**（1054-1164 主布局：左 aside/中 main/右 aside.right；1166-1231 对话框与设置弹窗） |
| └ 1233-2055 | `<script>...</script>`（**JS**，第 1233 行起，`</script></body></html>` 在 2055） |
| 2063-2089 | `def run(host, title, width, height)`（建窗 + `webview.start()`） |

### 7.2 后端 API 方法清单（`DesktopApp`，行号）

内部辅助：`__init__`(87)、`_ws_id`(97, static)、`_config`(101)、`_current_ws`(104)、`_register_workspace`(108)、`_touch_session`(122)、`_confirm`(133)、`_push_event`(392)、`_rebuild_pool`(443)、`_profile_skills_dir`(583)。

公开 js_api 方法（30 个）：

| # | 方法 | 行号 | 作用 |
| --- | --- | --- | --- |
| 1 | `status` | 155 | 汇总模型/工作区/会话/权限/思考级别/主题/上下文窗口/用量 |
| 2 | `set_permission` | 185 | 设置 `permissions.shell` / `permissions.fs` |
| 3 | `set_workspace` | 197 | 切换工作区并登记到 `workspaces`、置 `current_workspace` |
| 4 | `choose_workspace` | 211 | 原生文件夹选择对话框后切换 |
| 5 | `rename_workspace` | 225 | 重命名当前工作区条目 |
| 6 | `workspaces` | 239 | 列出工作区与当前 id |
| 7 | `set_thinking` | 247 | 设置思考级别并同步到 pool 的 `reasoning_effort` |
| 8 | `set_theme` | 258 | 设置主题（dark/light/system） |
| 9 | `open_url` | 264 | 系统浏览器打开链接（先 `_validate_url`） |
| 10 | `market_list` | 276 | 拉取插件市场（10 分钟缓存，`force` 可刷） |
| 11 | `market_install` | 294 | 浅克隆市场仓库到临时目录再本地安装 |
| 12 | `sessions` | 326 | 列出会话（合并 `sessions_meta` 与磁盘历史） |
| 13 | `session_history` | 342 | 读取某会话的 user/assistant 历史 |
| 14 | `new_session` | 347 | 新建会话（调用 `new_session` 服务重建 agent） |
| 15 | `rename_session` | 356 | 重命名会话并更新时间戳 |
| 16 | `chat` | 369 | 调 `ask` 服务执行一轮对话（`_lock` 串行；挂 `_push_event`） |
| 17 | `get_models` | 403 | 读配置中的模型与默认模型 |
| 18 | `save_models` | 408 | 校验并保存模型列表，保存后 `_rebuild_pool()` 热重建 |
| 19 | `switch_model` | 434 | 调 `models_runtime["set"]` 切换当前模型 |
| 20 | `usage` | 482 | 返回 agent llm 的累计 token 用量 |
| 21 | `context_usage` | 490 | 估算上下文占用（消息/系统工具/技能/系统提示词） |
| 22 | `ws_tree` | 526 | **右侧工作区树**：列目录内容（见 7.3） |
| 23 | `run_terminal` | 554 | 复用 `run_command` 工具执行命令（含权限门） |
| 24 | `review` | 562 | git status + git diff |
| 25 | `skills` | 586 | 列出技能（区分 profile 安装 / 插件自带） |
| 26 | `install_skill` | 606 | 复制技能目录到 profile（同名覆盖） |
| 27 | `remove_skill` | 621 | 移除 profile 安装的技能（防越狱） |
| 28 | `plugins` | 632 | 列出插件（过滤 DISPOSED） |
| 29 | `install_plugin` | 644 | 安装并热激活外部插件 |
| 30 | `remove_plugin` | 658 | 卸载并删除插件目录 |

### 7.3 右侧文件区 / 工作区树实现定位（**排查重点**）

**HTML 结构**（`UI_HTML` 内）：
- 右侧栏容器：`<aside class="right" id="rightPanel">` — **第 1110-1163 行**。
- 标签栏按钮：`data-rp="ws"` 的 `<button … onclick="switchPanel('ws')">📁 工作区</button>` — **第 1113 行**。
- 工作区 tab 面板：`<div class="rp-body" id="rp-ws">` — **第 1129-1136 行**；内部含 `.ws-nav`（上级按钮 `wsUp()` 第 1131、路径 `#wsCrumb` 第 1132、刷新按钮 `loadWsTree()` 第 1133）与滚动容器 **`<div class="rp-pane" id="wsTreePane"></div>` — 第 1135 行**（文件行渲染进这里）。

**CSS**：
- 右侧栏：`aside.right`（`width:360px; flex-direction:column`）— 891-894；`body.panel-hidden aside.right { display:none }`—894。
- 面板体/滚动：`.rp-body`（`display:none`，`.active` 时 `display:flex; flex-direction:column`）— 905-906；`.rp-pane { flex:1; overflow-y:auto }` — 907。
- 路径栏：`.ws-nav` / `.crumb` / `.mini-btn` — 911-918。
- 文件行：`.tree-row`（`display:flex; cursor:pointer`）— 919-924。

**JS 函数**（`<script>` 内）：
- `togglePanel()` — **第 1899-1902 行**：切换 `body.panel-hidden`（收起/展开整个右侧栏）。
- `switchPanel(name)` — **第 1903-1908 行**：切换 `.rp-tab`/`.rp-body` 的 active；**当 `name==='ws'` 时调用 `loadWsTree()`（第 1906 行）**。这是"点开工作区页"的唯一入口。
- `loadWsTree()` — **第 1910-1936 行**：`await api().ws_tree(wsPath)`（1911）→ 失败显示错误（1913-1917）→ `wsPath = res.rel || ''`（1918）→ 更新 `#wsCrumb`（1919）→ 清空 pane（1920）→ 空目录提示（1921-1924）→ 逐条 `res.entries` 生成 `.tree-row`（1926-1934），**目录行在第 1932 行绑定点击**：
  ```js
  if (e.dir) row.onclick = () => { wsPath = wsPath ? wsPath + '/' + e.name : e.name; loadWsTree(); };
  ```
  即"点击文件夹 → 把 `wsPath` 拼成子路径 → 重新 `loadWsTree()`"。文件行（`e.dir` 为假）**不绑定 onclick**（仅显示，无操作）。
- `wsUp()` — **第 1937-1942 行**：`wsPath` 去掉最后一段后 `loadWsTree()`。
- 状态变量：`let wsPath = ''` — **第 1897 行**（模块级闭包变量，`loadWsTree`/`wsUp`/点击回调共用）。

**后端**：
- `DesktopApp.ws_tree(subpath="")` — **第 526-552 行**：工作区为空→`{"ok":false,"error":"未选择工作区"}`（528-530）；`target=(root/subpath).resolve()` 并 `target.relative_to(root)` 越界校验（532-536）；非目录→错误（537-538）；`iterdir()` 按"目录优先 + 名称小写"排序、**跳过点开头条目**（541-544）；每项含 `name/dir/size/mtime`（545-548）；返回 `{"ok":true,"rel":<posix相对路径>,"entries":[...]}`（551-552）。
- `_ws_id`(97) / `_register_workspace`(108) / `set_workspace`(197) / `workspaces`(239) / `rename_workspace`(225) 支撑左侧栏"项目"分组与工作区切换。

**UI 与 kernel 的对接位置**：
- `__init__` 第 94 行：`host.confirm = self._confirm` — 把桌面确认对话框注册为内核的 `host.confirm`（供 tools_shell / tools_fs 权限门调用）。
- `status` 第 164 行：`self.host.service("agent_factory")()`；第 156 行 `host.service("models_runtime")`。
- `chat` 第 377 行：`self.host.service("ask")`；第 380 行：`self.host.emit_agent_event = self._push_event`（把内核/tracer 事件桥到页面 `window.onAgentEvent`，见第 392-400 行与 JS 第 1553 行 `onAgentEvent`）。
- `_rebuild_pool` 第 446 行：`from .builtins.models.register import _build_llm`；第 448/471 行读 `models_runtime`/`agent_factory` 服务。
- `plugins`/`install_plugin`/`remove_plugin` 直接调 `host.list()`/`host.mount`/`host.activate`/`host.deactivate`（第 632-664 行）。
- `run()` 第 2083-2087 行：`webview.create_window(title, html=html, js_api=app, ...)` 把 `DesktopApp` 实例注入为 js_api，并回填 `app._window`。

**该 bug 的排查提示（只读观察，未改码）**：
1. 展开入口只有 `switchPanel('ws')` → `loadWsTree()`（1906）与行点击回调（1932）两条，二者都读写同一个闭包变量 `wsPath`（1897）。
2. 点击回调依赖 `row.onclick`（1932）；`row.innerHTML` 内是 `<span>`，事件会冒泡到 `row`，正常应可触发。可重点验证 **`elementFromPoint` 命中的是否真是 `.tree-row`**（`probe_real.py` 第 93-102 行正是查这个），排除有透明遮罩层拦截。
3. `loadWsTree` 每次会把 `wsPath` 重置为后端返回的 `res.rel`（1918）；若后端 `ws_tree` 对拼接路径（`"a/b"`）返回 `ok:false`（例如 `Path(root/subpath)` 解析/越界/非目录），页面就停在错误提示而不展开。
4. `wsPath` 拼接用 `'/'`（1932），后端用 `Path(root)/subpath`（533），Windows 下forward slash 可解析，但要确认 `target.relative_to(root)`（534）不因大小写/符号链接/相对路径差异抛 `ValueError` → 直接走 `路径越出工作区` 分支。
5. 事件监听 `document.addEventListener('mousedown', …)`（1422-1430）只处理三个下拉菜单的关闭，**不在** `#wsTreePane` 上，理论上不拦截点击；但可顺带确认它未意外吞掉事件。

### 7.4 JS 段落索引（便于定位）

| 行号 | 内容 |
| --- | --- |
| 1234-1235 | `api()` / `$()` 简写 |
| 1241-1263 | `esc` / `md` / `fmtTokens` / `relTime` |
| 1266-1300 | `showDialog` / `_closeDialog` / `dialogPrompt`（含 `window.__dialogResult`，与后端 `_confirm` 联动） |
| 1302-1316 | 主题 `applyTheme` / `cycleTheme` |
| 1319-1372 | 消息渲染 `copyText`/`fallbackCopy`/`add`/`showHeroIfEmpty` |
| 1375-1461 | `refreshStatus` / `renderPerm` / `pickPerm` / `toggleCtxCard` / `refreshUsage` |
| 1463-1547 | 侧栏 `refreshSidebar` / `selectSession` / `newSessionFlow` |
| 1553-1596 | 实时步骤 `onAgentEvent` / `showLiveBlock` / `removeLiveBlock` |
| 1599-1642 | `setBusy` / `send`（+ input/modelSel/thinkSel 监听） |
| 1647-1752 | 设置弹窗 `openSettings`/`switchTab`/`loadModels`/`renderCards`/`addCard`/`saveSettings`/`loadPlugins`/`installPlugin` |
| 1755-1791 | 工作区下拉 `renderWsMenu`/`toggleWsMenu`/`chooseWorkspace` |
| 1797-1857 | 市场 `loadMarket`/`renderMarket`/`marketInstall` |
| 1860-1894 | 技能 `loadSkills`/`installSkill` |
| 1899-1955 | **右侧面板** `togglePanel`/`switchPanel`/`loadWsTree`/`wsUp`/`termRun` |
| 1957-1982 | 浏览器 `brGo`/`brExternal`；审查 `loadReview` |
| 1988-2043 | 辅助对话 `auxSend`/`auxAdd`/`auxInit`（+ 各输入框回车监听） |
| 2046-2054 | 启动：`pywebviewready` → `refreshStatus`/`refreshSidebar`/回放历史/`auxInit` |

---

## 8. 插件接口契约

### 8.1 七个内置插件对照表

| 插件 | provide 的服务 | 监听的事件 | 提供的工具 | 提供的命令 | 技能目录 |
| --- | --- | --- | --- | --- | --- |
| `chat_loop` | `agent_factory`、`ask`、`new_session` | 无（自身经 `host.emit_agent_event` 向外推事件） | 无（只是工具消费者） | 无 | 无（消费 skills 的目录） |
| `models` | `models_runtime`（可变 dict：`pool`/`order`/`current`/`set`） | 无 | `list_models`、`switch_model` | `model`（`/model [名称]`） | 无 |
| `tools_fs` | 无 | 无 | `read_file`、`write_file`、`list_files` | 无 | 无 |
| `tools_shell` | 无 | 无 | `run_command` | 无 | 无 |
| `skills` | 无 | 无 | 无 | 无 | 声明 `profile/skills`（`ctx.skills.add_dir`） |
| `mcp_client` | 无 | 无 | 动态（来自各 MCP 服务器的工具） | 无 | 无 |
| `repl` | `ui`（`run_ui(once_message)`） | 无 | 无 | 读取全部插件命令（不自注册命令） | 无 |

补充说明：
- **事件**：内核目前只 `emit` 三种：`activate`、`deactivate`、`error`（`kernel.py` 229/246/265）。7 个内置插件**均未使用 `ctx.on` 订阅**（`on` 是给外部插件预留的能力）。
- **工具名**由 nanoagent `make_tool` 从函数名派生（下划线命名）。
- `mcp_client` 在无 `mcpServers` 时提前返回，不 provide/注册任何东西，但仍为 ACTIVE。

### 8.2 `plugin.json` 字段含义

| 字段 | 位置 | 含义 | 是否必需 | 被谁读取 |
| --- | --- | --- | --- | --- |
| `name` | 插件根目录 `plugin.json` | 插件标识；决定 `host.plugins` 键名、`sha status` 显示名、重名后缀基准 | 否（缺失回落目录名） | `loader.load_manifest` → `Harness.mount` |
| `description` | 同上 | 人类可读描述；当前仅作元信息 | 否 | `load_manifest` 原样保留在 `record.manifest`，无代码消费 |

说明：内核目前**只消费 `name`**；`description` 展示但未被任何逻辑读取。`loader.mount_all` 的发现条件是"含 `plugin.json` **或** `register.py`"，因此 `plugin.json` 不是硬性必需。

### 8.3 插件契约（`register.py`）

- 必须导出模块级 `register(ctx)` 可调用对象，或在模块级提供 `TOOLS` 列表；两者都无则记 `skipped`。
- `ctx` 提供：三原语 `provide`/`on`/`effect`，以及聚合入口 `ctx.tools`/`ctx.skills`/`ctx.models`/`ctx.commands`，还有 `ctx.host`（指向 `Harness` 宿主，可访问 `profile`/`workspace`/`confirm`/`service()`/`collect_*()`）与 `ctx.skipped`（记录非致命跳过原因）。
- 任何注册到 `effect` 的资源**必须返回 disposer**；`provide`/`on`/`tools.register` 产生的可回收项由内核统一在 `deactivate` 时 LIFO 回收。
- `register` 抛异常 → 该插件 FAILED，但不影响其它插件。

---

## 9. `serve_ui_preview.py` 与 `smoke_desktop.py` 的差异；`_diag/` 脚本用途与可清理性

### 9.1 两个脚本的用途差异

| 维度 | `serve_ui_preview.py` | `smoke_desktop.py` |
| --- | --- | --- |
| 目的 | **看视觉**：在浏览器里渲染完整 UI，便于截图/检查样式与布局 | **验桥接**：真开 pywebview 原生窗口，确认 `UI_HTML` ↔ `DesktopApp` 的 js_api 链路可用 |
| 后端 | **全 mock**（`MOCK` 里手写 `window.pywebview.api`，返回假数据） | **真实** `DesktopApp`（但用 `patch_model_build` 的 **假模型**，离线） |
| 运行环境 | 普通浏览器 + 本地 HTTP 服务（`127.0.0.1:8642`） | 真实 WebView2 原生窗口（需 pywebview） |
| 验证内容 | 布局/主题/交互流（不验证真实数据） | 启动 + `status()` 调用返回值（`OK:` 前缀即通过），随后自动关窗 |
| 与 bug 排查 | **不足**：mock 的 `ws_tree` 只返回一层固定数据（见 `serve_ui_preview.py` 第 94-99 行），无法复现逐层展开问题 | 只冒烟 `status`，**不点文件区**，也不足以定位该 bug |

结论：两者都不是排查"右侧文件区无法展开"的有效工具——真正对口的是 `_diag/server.py`（真实多层 `ws_tree` 的浏览器 mock）配 `_diag/probe.mjs`，或 `_diag/probe_real.py`（真实窗口 + 真实 `ws_tree`）。

### 9.2 `_diag/` 各文件用途与可清理性

| 文件 | 用途 | 临时产物？ | 能否清理 |
| --- | --- | --- | --- |
| `server.py` | 用真实 `DesktopApp.ws_tree` 预抓多层目录树，注入 mock 渲染完整 UI，供无头浏览器实测 | 是（临时诊断） | **可清理**；排查期间建议保留 |
| `probe.mjs` | Node CDP（9333）无头浏览器脚本：打开工作区页并模拟点击目录行，比对 crumb/行数 | 是 | **可清理**；与 `server.py` 配套 |
| `probe_real.py` | 真实 WebView2 窗口诊断脚本，分 7 步检查文件区并可捕获初始化期 JS 错误 | 是 | **可清理**；最贴近运行时，排查时价值最高 |
| `launch_desktop.py` | 带 WebView2 远程调试端口（9335）启动真实桌面端 | 是 | **可清理** |
| `probe_out.txt` | `probe_real.py` 的一次输出（显示 `Main window failed to start`） | 是（日志） | **可清理** |
| `server.log` | `_diag/server.py` 的运行日志（`serving on 8765, dirs: 115`） | 是（日志） | **可清理** |
| `edge.log` | 0 字节空日志 | 是（空） | **可清理** |
| `edgeprofile/` | Edge 用户数据目录（大型二进制产物） | 是（缓存） | **可清理**（按任务要求已跳过，未纳入索引） |

说明：`_diag/` 整体是临时诊断目录，**不参与产品运行**，全部可安全删除；若仍在排查右侧文件区 bug，建议暂时保留 `server.py` + `probe.mjs` + `probe_real.py` 三个脚本。

---

## 10. 依赖关系总览

### 10.1 模块分层

```
                    ┌─────────────────────────────────────────────┐
   入口层           │ __main__.py   launcher_sha.py  launcher_desktop.py │
                    └───────────────┬─────────────────────────────┘
                                    │
   装配/CLI 层      ┌───────────────▼─────────────┐
                    │ cli.py  (build_runtime/main) │◄── tests / _diag / smoke
                    └───────────────┬─────────────┘
                                    │ 组装
   微内核层         ┌───────────────▼──────────────────────┐
                    │ kernel.py (Harness/Context/EventBus) │◄──── loader.py
                    │ 状态机 PENDING→ACTIVE→FAILED/DISPOSED │      (load_manifest/run_register)
                    └───────┬─────────────────┬────────────┘
                            │ profile          │ services/tools/skills
   基础设施层       ┌───────▼──────┐   ┌───────▼───────────────────────────┐
                    │ config.py    │   │ builtins/ 7 插件（全部是 ctx 消费者）│
                    │ (Profile)    │   └───────┬───────────────────────────┘
                    └──────────────┘           │ 复用
   执行引擎(外部)   ┌──────────────────────────▼───────────────────────────┐
                    │ nanoagent: Agent/LLM/AnthropicLLM/Memory/            │
                    │ SkillRegistry/MCPServer/tools( Tool, make_tool )     │
                    └──────────────────────────────────────────────────────┘

   桌面端           desktop.py ──(host.service/collect_tools/emit_agent_event)──► kernel/插件
                    desktop.py ──(UI_HTML ↔ DesktopApp js_api)──► 渲染层
                    desktop.py ──(.builtins.models.register._build_llm)──► models 插件（反向耦合）
```

### 10.2 依赖矩阵（被依赖 → 消费者）

| 模块 | 直接消费者 |
| --- | --- |
| `kernel.py` | `cli.py`、`loader.py`（被 kernel 反向调用）、`desktop.py`（经 host 对象）、`tests/test_harness.py`、`_diag/server.py` |
| `loader.py` | 仅 `kernel.Harness.mount/activate`（内部） |
| `config.py`（`Profile`） | `cli.py`、`desktop.py`、`tests/test_harness.py`、`_diag/server.py`、`_diag/probe_real.py`；运行时全部插件经 `ctx.host.profile` |
| `cli.py` | `__main__.py`、两个 launcher、`tests/*`、`_diag/launch_desktop.py`、`_diag/probe_real.py` |
| `desktop.py` | `cli.py`（`desktop` 子命令）、`tests/test_desktop.py`、`serve_ui_preview.py`、`smoke_desktop.py`、`_diag/*` |
| `chat_loop` 服务 | `repl`、`desktop.chat/status/context_usage/usage`、`models.set_current`、`cli` |
| `models` 服务/`_build_llm` | `chat_loop`、`desktop.*`、`cli`、`repl` |
| `tools_fs` 工具 | `chat_loop` 聚合、`desktop`（间接）、测试 |
| `tools_shell` 工具 | `chat_loop` 聚合、`desktop.run_terminal`、测试 |
| `skills` 目录 | `chat_loop`、`cli skill list`、`desktop.skills` |
| `mcp_client` 工具 | `chat_loop` 聚合 |
| `repl` 服务 `ui` | `cli.main`（默认 chat） |

### 10.3 关键耦合与风险

1. **配置字段 = 隐式契约**（最高耦合）：`config.json` 的 `models`/`default_model`/`permissions.{shell,fs}`/`mcpServers`/`thinking_level`/`theme`/`workspace`/`current_workspace`/`workspaces`/`sessions_meta` 被 `config`、`models`、`tools_shell`、`tools_fs`、`mcp_client`、`desktop`、`cli` 跨模块共同读写；任何字段重命名都是全局破坏性变更。
2. **服务名 = 隐式契约**：`agent_factory`、`ask`、`new_session`、`models_runtime`、`ui` 是插件间唯一解耦通道；`models_runtime` 是**可变 dict**，桌面端 `_rebuild_pool` 直接改其内部字段（desktop→插件内部结构的强耦合）。
3. **`desktop.py` → `models` 插件的反向依赖**：`_rebuild_pool` 直接导入 `builtins.models.register._build_llm`；若把 models 插件替换成外部实现，桌面端热重建会失效。
4. **`repl` 用了未定义的 `host.harness`**：`repl.register.py` 第 16/22/28/38 行访问 `host.harness.collect_commands()/list()`，而 `Harness` 无 `harness` 属性——`/plugins` 与帮助文本路径存在 `AttributeError` 风险（`kernel` 与 `repl` 的契约不一致）。这是当前代码里可确认的接口裂缝。
5. **`desktop.py` 的 `UI_HTML` 是巨型字符串**：JS 里硬编码了后端方法名与 DOM id（如 `#wsTreePane`、`loadWsTree`、`onAgentEvent`、`window.__dialogResult`），与 Python 侧 `_confirm`/`_push_event` 通过字符串协议耦合；任何一侧改名都会静默失效（无编译期检查）。
6. **`loader.py` 按文件路径加载插件**：插件 `register.py` 不能用相对导入；打包时必须把 `harness/builtins` 作为数据文件随包（`build_exe.py` 的 `--add-data`、spec 的 `datas`），否则内置插件全部加载不到。
7. **线程模型**：桌面端 js_api 每调用一线程，`DesktopApp.chat` 用 `RLock` 串行；`_confirm` 用 `evaluate_js` + 0.1s 轮询 `window.__dialogResult`（最长约 1 小时）；`_fetch_text`/`open_url`/`market_install` 有 SSRF 防护（`_validate_url` 拒绝本地/私有/保留地址）。
8. **打包脚本重复 + 路径写死**：`build_exe.py` 与 `build_pyi/*.spec` 功能重叠；spec、`run_tests.py`、`_diag/*`、`smoke_desktop.py` 均硬编码 `E:/文件/编程文件/agent/...` 绝对路径，换机/换目录即失效。
9. **`build_pyi/sha/`、`build_pyi/ShaDesktop/`、`dist/`、`assets/sha.ico`、`__pycache__/`** 均为生成物，不属于源码依赖；`_diag/edgeprofile/` 为临时缓存。

---

## 附：本次索引覆盖清单（42 个文件）

顶层（4）：`README.md`、`pyproject.toml`、`LICENSE`、`run_tests.py`
harness 核心（7）：`harness/__init__.py`、`__main__.py`、`kernel.py`、`cli.py`、`config.py`、`loader.py`、`desktop.py`
内置插件（14）：`builtins/{chat_loop,models,tools_fs,tools_shell,skills,mcp_client,repl}/{plugin.json,register.py}`
测试（2）：`tests/test_harness.py`、`tests/test_desktop.py`
CI（1）：`.github/workflows/ci.yml`
打包与工具（8）：`build_exe.py`、`build_pyi/sha.spec`、`build_pyi/ShaDesktop.spec`、`launcher_sha.py`、`launcher_desktop.py`、`make_icon.py`、`smoke_desktop.py`、`serve_ui_preview.py`
`_diag/`（6）：`server.py`、`probe.mjs`、`probe_real.py`、`launch_desktop.py`、`probe_out.txt`、`server.log`

> 已跳过（按任务要求）：`_diag/edgeprofile/`、`_diag/edge.log`(空,附带提及)、`dist/`、`build_pyi/sha/`、`build_pyi/ShaDesktop/`、`__pycache__/`、`assets/sha.ico`。

<!-- 第48批 2026-09-30: 安装 SkillHub CLI(~/.skillhub + ~/.local/bin/skillhub.cmd)与 @user_a730098d/pentest 技能到 ZCode(~/.zcode/skills/pentest)和默认 profile skills；重建 dist -->

<!-- 第49批 2026-09-30: 技能内置进 exe——build_exe.py 把 default profile skills 打包为 bundled_skills；skills 内置件新增 seed_bundled_skills（首启播种缺失技能、永不覆盖已有、失败静默）；新增 BundledSkillsSeedTests，harness 227 条全绿；重建 dist -->

<!-- 第50批 2026-09-30: 安装本地技能 app-vuln-hunt(F:\1\.dsh\skills)到 ZCode(~/.zcode/skills)与默认 profile skills；重建 dist，exe 内置池含 pentest-src + app-vuln-hunt，陌生环境冒烟通过 -->

<!-- 第51批 2026-09-30: 十二项功能——ask_user 问答工具+卡片、技能禁用开关、SkillHub 市场进设置页、追踪查看器(tab-trace)、Profile 每日自动备份(~/.sahou-harness/backups keep-N)、本地模型一键接入(Ollama/LM Studio 探测)、上下文水位条+context_length、一键 SummaryMemory 自动压缩(按窗口55%推导)、定时任务结果回流(schedule_store.session+write_back_result+busy跳过)、后台会话chip、Alt拖拽入KB、search_knowledge 引用溯源；models 透传 context_length→llm.context_window；harness 235 条全绿；重建 dist -->

<!-- 第52批 2026-09-30: 四处界面修复——context_usage 跟随界面会话(切会话水位条变化，agent记忆口径/磁盘估算双路径)、sideFloat 悬浮按钮(侧栏收起后可再打开)、rp-tabs 标签区内滚(+与收起钉右缘)、composer-row 移出输入框下方；235 条全绿；重建 dist -->

<!-- 第53批 2026-09-30: 移除 📋 计划按钮(与模式预设「计划」重复，入口统一到🎯下拉)；右栏改「▦ 面板⌄」大行菜单样式(打开标签页/当前标签名/收起后右缘竖排悬浮入口)，标签条+拖拽排序+隐藏标签+滚轮横滚退场(rpHidden 字段保留兼容)；235 条全绿；重建 dist -->

<!-- 第54批 2026-09-30: 移除输入框上方水位条(#ctxBar/refreshCtxBar 全清，…容量卡片保留)；面板入口改为右上角常驻 ▣(#panelTop，紧贴系统标题栏下方，取代右缘竖排 panelFloat)；frameless 自绘标题栏经评估放弃(winforms 无 NCHITTEST 会丢拖边缩放)；235 条全绿；重建 dist -->

<!-- 第55批 2026-09-30: 右栏头部改回原标签条(恢复 11 小标签+拖拽排序+右键移动/隐藏+悬停✕+＋找回+滚轮横滚)，撤下第53批的「▦ 面板⌄」大行菜单；移除标签条最右 ✕ 关闭按钮(面板显隐由右上角 ▣/Ctrl+J 承担)；235 条全绿；重建 dist -->

<!-- 第56批 2026-09-30: frameless 自绘标题栏（▣ 面板/—/□/✕ 与最小化同排，拖拽移动+双击最大化，tbDrag=pywebview-drag-region），窗口创建后 SetWindowLong 补 WS_THICKFRAME 保住拖边缩放/贴靠，js_api win_minimize/win_toggle_max/win_close（win_state 事件同步 ❐）；按钮行 UI 统一：modeSel 胶囊化(自绘箭头/计划态高亮)、cmpBtn 入图标组；.app 高度 calc(100vh-37px)、toast 下移；235 条全绿；重建 dist -->

<!-- 第57批 2026-09-30: 修 frameless 引入的拖拽/点击失效——pywebview easy_drag 默认 True 会全窗口 mousedown 挂窗口跟手监听，改 easy_drag=False（拖拽区仍走 #tbDrag）；「…」容量卡片新增「本轮对话」分节（输入/输出 tokens、缓存命中率、tok/s），移除底部 #usageLine/.composer-foot；235 条全绿；重建 dist -->

<!-- 第58批 2026-09-30: 工具明细移到回答下方(add() 卡片后置+live 块文本在前)；max_iterations 可配置(config.max_iterations 1~200 默认10，chat_loop/辅助/定时三处统一，通用页设置行 get/set_max_iterations，修 0 or 10 吞 0)；工具明细「写入/编辑·文件」行点击→切换 ws 面板 previewWsFile(rel,rel) 预览；236 条全绿；重建 dist -->

<!-- 第59批 2026-09-30: 十一项功能——定时任务钟点制(kind=daily/at="HH:MM"，本地时区错过补跑，面板新建表单)；窗口置顶(📌 win_toggle_top)+全局热键(Ctrl+Alt+Space 唤起，_global_hotkey_loop 线程级 RegisterHotKey，hotkey_enabled 开关，desktop 入口启动避免测试竞态)；通知中心(harness/notifications.py + notifications.json 上限50，🔔未读角标弹层)；消息收藏夹(favorites.json，★ 收藏 + ⭐ 面板跳转高亮)；KB 自动重索引(元数据 path+mtime，auto_reindex_minutes 默认10)；「知识库问答」预设模式；模型测速(models_ping)；git 智能提交(git_prepare_commit/git_do_commit)；MCP 五个预设模板；快捷指令 {{占位符}} 填参(insertSnippet)；回复字号三档(--msg-size)；241 条全绿；重建 dist -->

<!-- 第60批 2026-09-30: 十项功能——远程访问(harness/remote.py：HTTP+配对码+手机页，remote_status/remote_save，默认127.0.0.1)；记忆沉淀建议(chat_loop._maybe_distill 默认关(显式 enabled=true)，memory_suggest.json，🧠 面板采纳/丢弃，memory_accept/discard_suggestion)；会话历史编辑器(✎ 改→session_edit_text+删除)；工具黑白名单(disabled_tools，tools_list/set_tool_enabled)；截图提问(📷 screenshot_capture System.Drawing+前端框选裁剪cropShot)；docx/xlsx/pptx 拖入(drop_extract)；网络代理(set_proxy→环境变量)；单实例锁(desktop.lock+PID)；技能新建(create_skill 模板)；启动自检(self_check)；248 条全绿；重建 dist -->

<!-- 第61批 2026-09-30: 取消工具循环上限——nanoagent max_iterations=None（_iter_rounds 生成器，4 处循环替换，should_stop 仍可中止）；harness 默认无上限（_max_iterations 缺省/0/负/非法→None，1~200 显式安全阀），desktop set/get_max_iterations 0=无上限，通用页描述更新；344+248 全绿；重建 dist（需先关闭运行中的 ShaDesktop.exe 解锁） -->

<!-- 第62批 2026-09-30: 工具摘要落盘（chat_loop _attach_tools：ask/ask_stream/ask_with 三处，轻量视图 name+args摘要+result首300+ok 附到末条 assistant），前端 reviveTools 回放还原「更改/运行命令/工具调用」分组；切会话联动工作区（currentWsPath 全局 + selectSession 比较 sessions_meta.ws 后 switchWorkspace）；249+344 全绿；重建 dist -->

<!-- 第63批 2026-09-30: 分任务执行工作流（Manus 式）——新内置件 workflow（规划 3~8 子任务→串行独立 agent 执行（带前序结果摘要），每步落盘断点续跑，暂停/继续/停止，完成综合答复回流会话+通知中心）；workflow_store.py 纯存取层（next_pending_index 视中断遗留 running 为待重跑，mark_interrupted 启动兜底）；右栏 🧩 看板（2.5s 轮询）+ composer 🧩 按钮（当前输入作大任务）；desktop workflow_list/get/create/pause/resume/stop/delete；251 条全绿；重建 dist -->

<!-- 第64批 2026-10-13: 四处运行时缺陷修复（工作流看板删除 NameError=import 漏 delete_workflow；远程访问 POST 必崩=make_handler 从未注入 Handler.app；Git 智能提交 ValueError=_git_run 二元组被按三元组解包×4；office 预览恒失败=路径 str 传给收 bytes 的 _docx/_xlsx/_pptx_text）+ ruff 39→0 / mypy 25→0 双清零 + 历史批次模块补交入库（approvals/bootstrap/checkpoints/exporter/notifications/procutil/remote/snippets/workflow_store/builtins/tools_git/builtins/workflow/tests/test_safety.py/docs 规划）；251 条全绿；重建 dist -->

## 批64 补交入库的模块条目（2026-10-13）

### sahou-harness/harness/approvals.py
- **用途**：shell/写文件的统一审批门（Ask/allow/deny + 会话内批准记忆 + 命令白名单 + 审计日志）。
- **关键内容**：确认通道回调；白名单命中即放行（glob 归一化，`echo   hi` 与 `echo hi` 等价）；`echo hi` 获批 ≠ `echo hi && rm` 获批（不做前缀推断）；无确认通道时 fail-closed 并留档；allow 值会写入白名单；审计可关。
- **依赖**：标准库（json/time/fnmatch/pathlib）。
- **被依赖**：`tools_shell`、`tools_fs`、`desktop.py`（terminal/写文件门）、`tests/test_safety.py`。
- **影响范围**：改放行/拒绝语义会波及全部写路径测试（ShellApprovalTests/ApprovalGateTests）。
- **备注**：deny 优先于白名单与记忆。

### sahou-harness/harness/checkpoints.py
- **用途**：写文件/编辑前的检查点（快照 + 撤销）。
- **关键内容**：写前快照入栈；undo 恢复；与 desktop apply_code/write 门联动。
- **依赖**：标准库。
- **被依赖**：`desktop.py`（apply_code 等）、`tests/test_safety.py`（CheckpointTests）。
- **影响范围**：撤销语义变更会波及写路径测试。
- **备注**：快照只存被改文件。

### sahou-harness/harness/notifications.py
- **用途**：通知中心存储层（profile 内 notifications.json，推送/未读/已读/容量上限）。
- **关键内容**：`push_notification`（超上限丢弃最旧）、`load_notifications`、`mark_read`、`unread_count`。
- **依赖**：标准库。
- **被依赖**：`desktop.py` 通知面板、`builtins/notifications`、`builtins/workflow`（完成推送）、`builtins/scheduler`。
- **影响范围**：JSON 结构变更需同步桌面端渲染。
- **备注**：MAX_NOTIFICATIONS 限量。

### sahou-harness/harness/remote.py
- **用途**：手机/浏览器远程访问服务（线程化 HTTP，只读会话列表 + 发消息，配对码鉴权）。
- **关键内容**：`remote_config`（默认关、绑 127.0.0.1、随机 token 常驻 config.remote）；`check_token`（SHA-256 + 常数时比较）；`make_handler(app)`（闭包注入 `Handler.app`，仅暴露 sessions/history/send）；`RemoteServer`（start/stop 幂等，64KB 请求体上限）。
- **依赖**：标准库 http.server/hmac/secrets。
- **被依赖**：`desktop.py`（设置页开关）。
- **影响范围**：安全敏感面——不暴露文件与命令；改路由须保持白名单最小化。
- **备注**：批64 修复了 Handler.app 从未注入导致的 POST 必崩。

### sahou-harness/harness/workflow_store.py
- **用途**：工作流文件存储层（`<profile>/workflows/<id>.json`，内置件与桌面端共用）。
- **关键内容**：`new_workflow`（规划校验，空规划拒绝）、`load/save`（原子落盘）、`delete_workflow`（id 白名单防路径逃逸）、`list_workflows`（新的在前精简视图）、`active_workflow`（running/paused 占用执行通道）、`next_pending_index`（遗留 running 视为待重跑）、`mark_interrupted`（启动兜底）、`summary_text`（回流/通知摘要）。
- **依赖**：`config.Profile/atomic_write_text`。
- **被依赖**：`builtins/workflow`、`desktop.py` 工作流看板、`tests/test_new_plugins.py`（WorkflowStoreTests）。
- **影响范围**：JSON 形状变更需同步看板渲染与续跑语义。
- **备注**：纯函数 profile 进出，离线可测。

### sahou-harness/harness/builtins/workflow/*（通配）
- **用途**：分任务执行工作流内置件（Manus 式）：plugin.json 声明 + register.py 执行器。
- **关键内容**：单次模型调用规划 3~8 子任务（解析失败兜底单步）；每步全新 agent 串行执行（携带前序结果摘要）；执行通道全局仅一条；暂停/继续/停止；完成后综合答复经 schedule_store 回流发起会话 + 通知中心。
- **依赖**：`workflow_store`、`chat_loop._max_iterations`、`schedule_store.write_back_result`、`notifications`。
- **被依赖**：`desktop.py` 🧩 看板（workflow_list/get/create/pause/resume/stop/delete）。
- **影响范围**：改执行语义需同步 WorkflowStoreTests 与看板刷新。
- **备注**：批64 修复 delete 动作 NameError（import 漏 delete_workflow）。

### sahou-harness/tests/test_safety.py
- **用途**：安全机制专项测试（审批门 + 检查点）。
- **关键内容**：ApprovalGateTests（confirm_write 强制审批、无通道 fail-closed、shell allow 写白名单、ask 拒绝路径、diff 送审批者）；CheckpointTests（write 建检查点可撤销、edit_file 检查点恢复）。
- **依赖**：`harness.approvals`、`harness.checkpoints`。
- **被依赖**：`tools/run_tests.py` 全量入口。
- **影响范围**：改审批/检查点行为后必须全绿。
- **备注**：全离线（临时目录 profile）。
