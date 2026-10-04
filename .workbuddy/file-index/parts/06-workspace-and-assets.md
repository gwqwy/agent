# 06 · 工作区根 / 资产 / 构建产物 / 补充条目 — 文件级索引

> 范围：前五个分片未覆盖的剩余文件——工作区根级配置与日志、各项目内的资产、编辑器工具链、构建产物与运行期残留。
> 说明：本分片大量使用 `*` 通配条目聚合"同类且无需逐文件描述"的文件（测试用例、stones 副本、打包产物等）。

---

## 一、工作区根（`E:/文件/编程文件/agent/`）

### `.zcodeignore`
- **用途**：ZCode 工作区的**搜索忽略规则**，只影响 `@` 文件候选 / Command Center / 文件树搜索，不影响文件浏览与 Agent 访问。
- **关键内容**：语法同 `.gitignore`；文件被显式分成两段——上半段由设置页「从 .gitignore 同步」自动重写，下半段为手工补充。已忽略 `.git/`、`node_modules/`、`.venv/` 等。
- **依赖**：无（纯配置）。
- **被依赖**：ZCode 工具链读取。
- **影响范围**：改动会改变未来会话中文件搜索的可达范围；**不要当作 `.gitignore` 手工大改**，否则与同步机制冲突。
- **备注**：与 `.gitignore` 不自动双向同步，属已知设计。

### `FILE_INDEX.md`
- **用途**：本索引体系的**主入口**——工作区总览、全局依赖、全量速查表、变更影响矩阵、风险清单与明细分片导航。
- **关键内容**：由 `.workbuddy/file-index/build_index.py` 生成（头部总览为手工维护的 `_master_header.md`）。
- **依赖**：`.workbuddy/file-index/parts/*.md`（明细来源）。
- **被依赖**：后续会话改动文件前应先查它。
- **影响范围**：明细变化后需重跑 `build_index.py` 重新生成。
- **备注**：**手工勿直接改"速查表"章节**，会被下次生成覆盖；总览/矩阵/风险章节在 `_master_header.md` 里维护。

### `*.log`（工作区根，通配）
- **用途**：聚合条目，覆盖根目录残留的安装/运行日志。
- **关键内容**：pip 与工具链输出。
- **依赖**：无。
- **被依赖**：无。
- **影响范围**：无。
- **备注**：2026-09-26 用户清理了根目录的 `pip_faiss.log`、`pip_out.log`，**当前根目录已无 `*.log` 文件**，此条作为通配占位保留（各项目内部的 `_diag/*.log`、`.workbuddy/audit/*.log` 另有条目覆盖）。可随时清理，不属于源码。

### `.mimosa/*`（通配）
- **用途**：Agent 运行时（ZCode/WorkBuddy）的 **hook 状态目录**——会话状态、续跑基线、锁。
- **关键内容**：`hook-state/sess_<id>.json`、`*.continue.json`、`*.lock/owner.json`、`*.baseline/*.source`。
- **依赖**：无。
- **被依赖**：运行时 hook 机制读取。
- **影响范围**：删除会丢失会话续跑状态。
- **备注**：**不要清理**；非项目源码。

### `.zcode/plans/*.md`（通配）
- **用途**：ZCode 会话产出的**计划文档**（plan 模式的落盘结果）。
- **关键内容**：按 `plan-sess_<会话id>.md` 命名。
- **依赖**：无。
- **被依赖**：无。
- **影响范围**：无。
- **备注**：可作历史线索保留。

### `.workbuddy/*`（通配）
- **用途**：WorkBuddy/本 Agent 的项目侧数据——记忆、索引构建产物。
- **关键内容**：`memory/MEMORY.md`（项目长期记忆）、`memory/YYYY-MM-DD.md`（每日工作日志）、`file-index/`（本索引体系）、`SOUL/IDENTITY/USER.md` 相关。
- **依赖**：无。
- **被依赖**：后续会话读记忆；`build_index.py` 读 `parts/`。
- **影响范围**：`memory/` 丢失会失去跨会话项目上下文。
- **备注**：**约定不可删除**（系统级约束）。

### `.workbuddy/file-index/build_index.py`
- **用途**：本索引体系的**构建器**——解析分片 → 归一化 JSON → 覆盖度比对 → 生成 `FILE_INDEX.md`。
- **关键内容**：`parse_part()`（按 `### \`路径\`` + `- **字段**：` 解析）、`collect_disk()`（磁盘清单，排除 `.git/.venv/__pycache__`）、`oneline()`、`main()`；支持 `--check` 只做覆盖度检查。
- **依赖**：仅标准库（`json/os/re/fnmatch/pathlib`）。
- **被依赖**：`FILE_INDEX.md`（由其生成）。
- **影响范围**：改字段名约定或分片格式需同步本脚本；`ROOT` 为硬编码绝对路径，迁移目录需改。
- **备注**：通配条目（含 `*`）在覆盖度比对时按 `fnmatch` 匹配。

### `.workbuddy/file-index/query.py`
- **用途**：索引**检索器**——按关键词/路径查文件的用途、依赖、被依赖、影响范围。
- **关键内容**：`query()` 支持关键词、`--deps`/`--used-by` 反向查、`--project` 过滤、`--part` 查看分片明细。
- **依赖**：`file-index.json`。
- **被依赖**：人/Agent 的日常查找。
- **影响范围**：JSON 结构变更需同步。
- **备注**：改动任一文件前先跑它定位关联影响面。

---

## 二、nanoagent 补充

### `nanoagent/.env`
- **用途**：nanoagent 运行期**真实环境变量文件**（OpenAI 兼容服务的 base_url / api_key / model）。
- **关键内容**：`NANOAGENT_BASE_URL`、`NANOAGENT_API_KEY`（**明文真实密钥**）、`NANOAGENT_MODEL=deepseek-flash`、`NANOAGENT_EMBEDDING_MODEL`。
- **依赖**：被 `nanoagent/config.py` 的 `settings()` 读取（python-dotenv）。
- **被依赖**：所有需要真实模型的示例与 `cli.py` / `server.py`。
- **影响范围**：改 model/base_url 会影响全部联网示例行为。
- **备注**：**风险项——真实 API Key 明文落盘**；若该仓库将公开或纳入版本控制，务必改用环境变量注入或加入忽略列表。

### `nanoagent/.env.example`
- **用途**：配置模板，列出可用的 OpenAI 兼容服务端点。
- **关键内容**：智谱 GLM / DeepSeek / Kimi / 通义千问 / Ollama 的 base_url 对照；四个 `NANOAGENT_*` 变量名。
- **依赖**：无。
- **被依赖**：新用户复制为 `.env`。
- **影响范围**：新增配置项时需同步更新本文件与 `config.py`。
- **备注**：与 `.env` 的变量名必须保持一致。

### `nanoagent/.github/workflows/ci.yml`
- **用途**：nanoagent 的 GitHub Actions CI。
- **关键内容**：push/PR 触发；Python 矩阵 `3.10 / 3.12 / 3.14`；`pip install -e .[server,faiss,mcp,tiktoken]` 后跑测试。
- **依赖**：`pyproject.toml` 的 extras 定义。
- **被依赖**：CI 本身。
- **影响范围**：新增可选依赖或测试入口变更需同步；extras 名写错会直接导致 CI 失败。
- **备注**：矩阵内**未装 `playwright`/`otel`/`psycopg`**，故相关测试在 CI 中走"跳过"分支。

### `nanoagent/build/*`（通配）
- **用途**：setuptools 的**构建中间产物**——`pip install -e .` 时拷入的 `build/lib/nanoagent/**` 源码副本。
- **关键内容**：与 `nanoagent/nanoagent/` 同名同结构的 36 个文件副本。
- **依赖**：由打包流程生成。
- **被依赖**：无（editable 安装后以源目录为准）。
- **影响范围**：无。
- **备注**：**可安全删除**；正因为是副本，若在这里改代码不会生效——排查"改了没反应"时先确认改的是源目录而非 `build/lib`。

### `nanoagent/.nanoagent/*`（目录约定）
- **用途**：nanoagent 插件/技能生态的**默认约定目录**（对应 `bootstrap.py` 的 `config_dir`），同时是示例记忆与 checkpoint 的落盘位置。
- **关键内容**：当前为**空目录**——生态装配约定已建立但尚未放入实际插件/技能。
- **依赖**：无。
- **被依赖**：`bootstrap_agent(config_dir)` 会扫描它。
- **影响范围**：向其中放入 `plugin.py` / dsh 插件包 / `SKILL.md` 即被自动装配。
- **备注**：示例 03/10 的记忆与 checkpoint 也写入 `.nanoagent/`（`example-03.json` 等）。

---

### `.audit_tmp/*`（通配）
- **用途**：外部审计报告核对（2026-09-26/27）的**临时**判定与复现脚本目录：`AUDIT_VERDICT.md`（26 条声明的逐条判定：已修复/仍存在/部分成立 + 修复批次建议）与 `verify_*.py` 复现脚本（P0 修复时的依据）。
- **关键内容**：判定结论已沉淀进记忆与提交历史；P0/H 批次修复完成后仅作留证。
- **依赖**：无。
- **被依赖**：无（人工查阅）。
- **影响范围**：无（不入 git）。
- **备注**：可在全部审计修复项收尾并经用户确认后清理。

---

## 三、sahou 补充

### `sahou/.gitattributes`
- **用途**：**换行符强制统一为 LF** 的关键配置（真·基础设施，不是可选美化）。
- **关键内容**：`* text=auto eol=lf`；`*.png/*.vsix/*.exe/*.wasm/*.db binary`。
- **依赖**：无。
- **被依赖**：`tests/*.sh` 快照字节比对、Windows 上的 bash 脚本执行。
- **影响范围**：**改动或删除会直接让全套一致性测试在 Windows 上失败**（CRLF 检出破坏 heredoc 期望块比对）。
- **备注**：文件内注释已写明理由，务必保留。

### `sahou/.gitignore`
- **用途**：sahou 的 Git 忽略规则。
- **关键内容**：忽略 `sahou.exe~`、`*.db`、`应用页面/`、`tests/.tmp_app/`、`分发版/`、`.mimosa/`、`__pycache__/`。
- **依赖**：无。
- **被依赖**：Git。
- **影响范围**：新增生成物目录时需同步，避免污染提交。
- **备注**：注意 **`sahou.exe` 与 `sahou.wasm` 当前并未被忽略**（工作区里它们是未提交改动）。

### `nanoagent/.gitignore`
- **用途**：nanoagent 的 Git 忽略规则（第三批工程卫生新增）。
- **关键内容**：忽略 `__pycache__/`、`*.py[cod]`、`*.egg-info/`、`build/`、`dist/`、`.env`、`.env.local`、`*.log`、`*.db`、`.nanoagent/`。
- **依赖**：无。
- **被依赖**：Git。
- **影响范围**：新增生成物目录时需同步。
- **备注**：`.env`（含明文 API Key）已被排除，确认未被跟踪；`.env.example` 应保留在库中作模板。

### `sahou-harness/.gitignore`
- **用途**：sahou-harness 的 Git 忽略规则（第三批工程卫生新增）。
- **关键内容**：忽略 `__pycache__/`、`*.py[cod]`、`build/`、`build_pyi/`、`dist/`、`_diag/`、`*.log`、`*.db`、`*.zip`。
- **依赖**：无。
- **被依赖**：Git。
- **影响范围**：新增生成物目录时需同步。
- **备注**：`build_pyi/` 原被逐文件提交（18 个中间产物、含 87MB 二进制），现已取消跟踪并整目录忽略；`dist/*.exe` 为交付物，保留但同样被 `dist/` 忽略。

### `sahou/LICENSE`
- **用途**：sahou 项目的开源许可证。
- **关键内容**：许可证正文。
- **依赖**：无。
- **被依赖**：`editors/vscode/sahou/LICENSE` 的源（打包时映射为 `LICENSE.txt`）。
- **影响范围**：换证需同步编辑器扩展目录内的副本。
- **备注**：与 `editors/vscode/sahou/LICENSE` 存在**副本关系，需手工同步**。

### `sahou/wasm_exec.js`
- **用途**：Go 官方 **WASM 运行时胶水脚本**（`wasm_exec.js`），浏览器/Node 加载 `sahou.wasm` 必需。
- **关键内容**：`Go` 类、`go.importObject`、`go.run(instance)`；全局 `__sahou_run` 由 sahou 的 wasm 侧注册。
- **依赖**：与 Go 工具链版本绑定（随 `go` 版本变化）。
- **被依赖**：`sahou/examples/在线体验/index.html`、`examples/响应式/*.html`（各有副本）、`tests/playground_check.mjs`、`tests/wasm_reactive.mjs`。
- **影响范围**：**升级 Go 版本后必须用 `go env GOROOT` 下的同名文件替换所有副本**，否则 wasm 加载失败。
- **备注**：项目内**存在多份副本**（示例目录各一份），无自动同步脚本。

### `sahou/assets/*`（通配）
- **用途**：项目品牌图标与 Logo 的矢量源文件（`icon.svg` / `logo.svg` / `sahou-icon.svg` / `sahou-logo.svg`）。
- **关键内容**：SVG 矢量图。
- **依赖**：无。
- **被依赖**：`editors/tools/genicon.py` 以图标 SVG 为源栅格化出 PNG。
- **影响范围**：改图标需重跑 `genicon.py` 刷新扩展图标。
- **备注**：与 `editors/vscode/sahou/icons/` 下的 SVG 存在**副本关系**。

### `sahou/sahou.*`（通配）
- **用途**：sahou 的**构建产物**——Windows 可执行解释器（`sahou.exe`）与 WASM 运行时（`sahou.wasm`）。
- **关键内容**：`sahou.exe`（≈25 MB，由 `go build -o sahou.exe .`）、`sahou.wasm`（≈13 MB，由 `cmd/sahouwasm` 构建）。
- **依赖**：由 `sahou/main.go` / `sahou/cmd/sahouwasm/main.go` 构建。
- **被依赖**：`tests/*.sh` 全套回归脚本、示例页面、在线体验页。
- **影响范围**：**改任何 Go 源码后必须重新构建**，否则测试跑的是旧二进制（典型的"改了没生效"陷阱）。
- **备注**：git 中当前为未提交状态；`tests/build.sh` 负责重建。

### `sahou/cmd/sahouwasm/stones/*/main.saho`（通配）
- **用途**：**wasm 运行时的内嵌标准库副本**——与 `sahou/stones/` 内容完全一致（18 个包，已逐包 md5 校验相同）。
- **关键内容**：与 `sahou/stones/` 同名同内容的 18 个 `main.saho`。
- **依赖**：由 `cmd/sahouwasm/stones.go` 通过 `go:embed` 注入。
- **被依赖**：`sahou.wasm` 中"浏览器免安装 `用 "包名" 引入`"的能力。
- **影响范围**：**修改 `stones/` 任一包后必须手工同步本目录**，否则"原生跑"与"浏览器跑"行为不一致。
- **备注**：**双副本无自动同步脚本，是明确的一致性风险点**。另注意目录名含中文，部分工具链需注意编码。

### `sahou/editors/sync-shared.js`
- **用途**：把 `editors/shared/language.json`（编辑器元数据唯一事实来源）**同步**到各编辑器集成的 `data/language.json`。
- **关键内容**：`targets = [vscode/sahou/data/language.json]`；零依赖 `fs`+`path`，顺带做 JSON 合法性校验。
- **依赖**：`editors/shared/language.json`。
- **被依赖**：无（人工执行 `node editors/sync-shared.js`）。
- **影响范围**：新增编辑器集成需在此加目标路径。
- **备注**：**改 `shared/language.json` 后必须跑它**，否则扩展读到的仍是旧副本。

### `sahou/editors/tools/genicon.py`
- **用途**：把图标 SVG 的"数据流水线"设计**栅格化**为 VS Code 市场要求的 PNG 图标。
- **关键内容**：纯标准库（`math/zlib/struct`）实现 4×SS 超采样抗锯齿、与 SVG 逐点对应的渐变圆角方块 + 管道 + 石子 + 箭头几何。
- **依赖**：`editors/vscode/sahou/icons/saho.svg`（几何基准）。
- **被依赖**：无（人工执行）。
- **影响范围**：改图标设计需同步改本脚本的几何常量。
- **备注**：`python editors/tools/genicon.py` → 生成 `sahou-128.png` / `sahou-256.png`。

### `sahou/editors/tools/packvsix.py`
- **用途**：**打包 VS Code 扩展**——把 `editors/vscode/sahou/` 组装成 `sahou-language-<版本>.vsix`。
- **关键内容**：以旧 vsix（0.3.0）内的 `extension.vsixmanifest` 为模板只替换版本号，复制 `[Content_Types].xml`，按映射改名（`CHANGELOG.md→changelog.md`、`LICENSE→LICENSE.txt`）。
- **依赖**：`editors/vscode/sahou/`、模板 `sahou-language-0.3.0.vsix`。
- **被依赖**：无（人工执行 `python editors/tools/packvsix.py <version>`）。
- **影响范围**：**强依赖模板 vsix 存在**；若删掉 0.3.0 产物则打包脚本失效。
- **备注**：绕开 vsce/npm 的零依赖打包方式。

### `sahou/editors/vscode/sahou/extension.js`
- **用途**：VS Code 扩展主代码。
- **关键内容**：命令 `sahou.run` / `sahou.build` / `sahou.repl`；**内置极简 LSP 客户端**（启动 `sahou lsp` 子进程、推送诊断、转发补全请求——v0.2 起支持 `用 "…` 包名与 `名字.` 成员补全）；静态元数据来自 `./data/language.json`。仅用 `vscode` API + `child_process`，无 npm 依赖。
- **依赖**：`sahou.exe`（CLI 与 LSP）、`data/language.json`。
- **被依赖**：`package.json` 的命令/激活声明。
- **影响范围**：改 LSP 协议（`internal/lsp/lsp.go`）需同步本文件的客户端解析。
- **备注**：客户端与服务端的**补全/诊断协议是隐式契约，跨语言（JS ↔ Go）易漂移**。

### `sahou/editors/vscode/sahou/data/language.json`
- **用途**：扩展用的语言元数据**副本**（由 `sync-shared.js` 从 `editors/shared/language.json` 同步）。
- **关键内容**：关键字 / 内置函数 / 模块 / stones 包清单。
- **依赖**：`editors/shared/language.json`。
- **被依赖**：`extension.js`（补全兜底与悬停文档）。
- **影响范围**：**勿手改**，会被下次同步覆盖；应改 shared 版本再同步。
- **备注**：发布 vsix 时只能带目录内文件，故必须保留副本。

### `sahou/editors/vscode/sahou/icons/*`（通配）
- **用途**：扩展图标资源（SVG 源 + `genicon.py` 生成的 PNG，+ 文件图标主题用图标）。
- **关键内容**：`saho.svg`、`saho-file.svg`、`sahou-128.png`、`sahou-256.png`。
- **依赖**：`assets/*.svg`（品牌源）。
- **被依赖**：`package.json` 的 `icon` 字段、`saho-icon-theme.json`。
- **影响范围**：换图标需重跑 `genicon.py`。
- **备注**：PNG 为二进制产物。

### `sahou/editors/vscode/sahou/.vscodeignore`
- **用途**：扩展打包忽略规则，决定哪些文件不进入 vsix。
- **关键内容**：glob 规则列表。
- **依赖**：无。
- **被依赖**：`packvsix.py` / vsce 打包。
- **影响范围**：漏写规则会让开发文件被打进发布物。
- **备注**：与扩展目录内 `LICENSE` 同属"编辑器集成目录内的附属文件"。

### `sahou/editors/vscode/sahou/LICENSE`
- **用途**：扩展的许可证副本（打包时映射为 `LICENSE.txt`）。
- **关键内容**：根 `sahou/LICENSE` 的副本。
- **依赖**：`sahou/LICENSE`。
- **被依赖**：`packvsix.py`。
- **影响范围**：改根 LICENSE 需同步本副本。
- **备注**：副本关系，需手工同步。

### `sahou/editors/vscode/sahou-language-*.vsix`（通配，10 个）
- **用途**：历史发布的**扩展打包产物**（0.1.0 ~ 1.0.0）。
- **关键内容**：各版本的 vsix（zip 结构）。
- **依赖**：由 `packvsix.py` 或 vsce 生成。
- **被依赖**：0.3.0 被 `packvsix.py` 当作 manifest 模板（**唯一硬依赖**）。
- **影响范围**：删除全部旧 vsix 会让打包脚本失效。
- **备注**：二进制产物；建议保留 0.3.0。

### `sahou/tests/domstub.js`
- **用途**：`sahou build` 产物（JS）的 **Node 测试桩**——模拟最小 DOM，验证 `页面/page` 模块（CJS 版）。
- **关键内容**：`makeEl(tag,id)` 返回带 `__saho_element` 标记、`setAttribute/getAttribute/appendChild/removeChild`、`listeners` 的元素对象。
- **依赖**：无（零依赖桩）。
- **被依赖**：`tests/fullstack.sh` 等跑 build 产物时的 DOM 环境。
- **影响范围**：`页面/page` 模块用到的新 DOM API 需在本桩补齐，否则 Node 侧测试会失败。
- **备注**：**与 `.mjs` 版为手工同步的双副本**。

### `sahou/tests/domstub.mjs`
- **用途**：同上的 **ESM 版** DOM 测试桩。
- **关键内容**：以 `export function makeEl(...)` 导出，元素 `parentNode` 命名与 CJS 版略有差异。
- **依赖**：无。
- **被依赖**：ESM 形态的 build 产物测试。
- **影响范围**：与 `domstub.js` 需同步维护。
- **备注**：双副本之一，改动务必两边都改。

### `sahou/tests/playground_check.mjs`
- **用途**：**在线体验页等价测试**——在 Node 里加载 `sahou.wasm`，调用与页面同一入口的全局 `__sahou_run(src)`。
- **关键内容**：设 `globalThis.__SAHO_PLAYGROUND = true` → 载入 `wasm_exec.js` → `WebAssembly.instantiate(sahou.wasm)`；`check(name,got,want)` 断言 wasm 内嵌 stones（浏览器免安装 `用 "包名" 引入`）。
- **依赖**：`sahou/wasm_exec.js`、`sahou/sahou.wasm`。
- **被依赖**：`tests/wasm.sh`。
- **影响范围**：改 wasm 入口或 stones 内嵌逻辑需同步。
- **备注**：依赖 wasm 产物已构建。

### `sahou/tests/wasm_reactive.mjs`
- **用途**：**WASM 响应式回归测试**——`sahou.wasm` 在 Node 里直接解释 `.saho`，验证格子联动（`格子`）。
- **关键内容**：手工造 `document.querySelector` 桩与 `#单价/#数量/#总价/#提示` 元素、`dispatch()` 触发事件；注入 `__SAHO_SOURCE` 源码后断言联动结果。
- **依赖**：`sahou.wasm`、`wasm_exec.js`。
- **被依赖**：`tests/wasm.sh`。
- **影响范围**：改 `internal/interp/reactive.go` 或 `uimod` 需同步。
- **备注**：`ROOT` 用 `decodeURI` 处理中文路径，编码相关改动需谨慎。

### `sahou/tests/pack.sh`
- **用途**：**打包单文件 exe** 的回归脚本——验证 `sahou 打包` 能把 `.saho` 编译成独立可执行文件并正常运行。
- **关键内容**：调用 `sahou 打包|pack <f.saho> -o <out.exe>`，随后执行产物并比对输出。
- **依赖**：`sahou.exe`、`sahou/main.go` 的 `packApp()`。
- **被依赖**：`tests/run_all.sh`。
- **影响范围**：改打包逻辑（内嵌工程生成、`go build` 调用）需同步。
- **备注**：依赖本机 Go 工具链与网络（`go mod tidy` 可能拉包）。

### `sahou/examples/计数器.js`
- **用途**：`sahou build` 对 `计数器.saho` 的**转译产物示例**（JS）。
- **关键内容**：由 `internal/transpile` 生成的等价 JS。
- **依赖**：`examples/计数器.saho`。
- **被依赖**：`examples/计数器.html`。
- **影响范围**：改转译器后此文件内容会变；它是"转译输出长什么样"的活样例。
- **备注**：生成物，宜与 `.saho` 源一同查看。

### `sahou/examples/网页/favicon.svg`
- **用途**：示例网页的站点图标。
- **关键内容**：SVG 图标。
- **依赖**：无。
- **被依赖**：`examples/网页/index.html`。
- **影响范围**：无。
- **备注**：静态资源。

### `sahou/examples/*/wasm_exec.js`（通配）
- **用途**：示例页面目录内的 **`wasm_exec.js` 副本**（`响应式/`、`在线体验/` 各一份）。
- **关键内容**：与 `sahou/wasm_exec.js` 同源的 Go WASM 胶水脚本。
- **依赖**：Go 工具链版本。
- **被依赖**：对应目录的 `index.html`（同目录引用）。
- **影响范围**：**升级 Go 后必须三个副本一起替换**（根目录 + 两个示例目录）。
- **备注**：多副本无同步脚本，是明确的一致性风险点。

### `sahou/examples/*/sahou.wasm`（通配）
- **用途**：示例页面目录内的 **`sahou.wasm` 副本**（`响应式/`、`在线体验/` 各一份）。
- **关键内容**：与 `sahou/sahou.wasm` 同源的 WASM 运行时。
- **依赖**：由 `cmd/sahouwasm` 构建。
- **被依赖**：对应目录 `index.html` 的在线执行能力。
- **影响范围**：**重新构建 wasm 后必须同步这两份副本**，否则页面跑的仍是旧解释器。
- **备注**：多副本无同步脚本；文件较大。

### `sahou/tests/modproject/*`（通配）
- **用途**：**模块与包管理测试工程**——多文件 import 的验证夹具。
- **关键内容**：`主程序.saho`（入口）、`算术.saho`（被引入的模块）、`期望.txt`（stdout 快照：`42 / 42 / 2 / {"ok":true}`）。
- **依赖**：sahou 模块解析（`internal/interp` 的 `loadModule`）。
- **被依赖**：`tests/modules.sh`、`tests/packages.sh`。
- **影响范围**：改模块查找/引入语义需同步期望快照。
- **备注**：`期望.txt` 为字节比对基准。

### `sahou/tests/cases/*.out`（通配）
- **用途**：正向用例（`0xx`，19 个）的**期望 stdout 快照**，由 `tests/run.sh` 做字节级比对。
- **关键内容**：与同名 `.saho` 一一对应：`010_numbers`、`020_strings`、`030_lists_dicts`、`040_control`、`050_functions`、`060_errors`、`070_builtins2`、`080_fullwidth`、`090_semi_quotes`、`092_closure_dict`、`093_pipeline`、`094_pipeline_arrow`、`095_page_builder`、`096_multiline_dict`、`097_builtin_shadow`、`098_default_params`、`099_cells`。
- **依赖**：`sahou.exe` 的实际输出。
- **被依赖**：`tests/run.sh`、`tests/run_all.sh`。
- **影响范围**：**任何影响正常输出的改动（内建函数、数值格式化、字符串化）都必须同步这些快照**；换行符差异也会导致失败（见 `.gitattributes`）。
- **备注**：字节比对，用 `--update` 式手工重生成需谨慎，避免把 bug 固化进快照。

### `sahou/tests/cases/*.err`（通配）
- **用途**：负向用例（`9xx`，7 个）的**期望报错信息快照**。
- **关键内容**：`900_undef`（未定义标识符）、`901_noend`（缺结束标记）、`902_chain`（链式调用错误）、`903_addtype`（类型相加错误）、`904_key`（键错误）、`905_negidx`（负索引）、`906_builtin`（内建误用）。
- **依赖**：`internal/errs/errs.go` 的错误文案与 `internal/interp` 的报错路径。
- **被依赖**：`tests/run.sh`。
- **影响范围**：**改错误信息文案会直接打破这些快照**——这是"错误信息即契约"的显式体现。
- **备注**：新增负向用例建议续编 `907+`。

---

## 四、sahou-harness 补充

### `sahou-harness/build_pyi/*`（通配）
- **用途**：PyInstaller **打包中间产物**——分析结果、EXE/PKG 结构、字节码归档与警告/交叉引用报告。
- **关键内容**：`sha/`、`ShaDesktop/` 两套：`Analysis-00.toc`、`EXE-00.toc`、`PKG-00.toc`、`PYZ-00.pyz(.toc)`、`base_library.zip`、`*.pkg`、`warn-*.txt`、`xref-*.html`。
- **依赖**：`build_pyi/*.spec`（`sha.spec` / `ShaDesktop.spec`）。
- **被依赖**：无。
- **影响范围**：无（重新打包会重建）。
- **备注**：**体积大（`xref-*.html` 各约 98 KB）且非源码，可安全清理**；`warn-*.txt` 在排查"打包后缺模块"时有用。

### `sahou-harness/dist/*`（通配）
- **用途**：PyInstaller 产出的**可执行文件**——`sha.exe`（CLI）与 `ShaDesktop.exe`（桌面端）。
- **关键内容**：两个打包后的独立可执行程序。
- **依赖**：由 `build_exe.py` + `build_pyi/*.spec` 生成。
- **被依赖**：最终用户分发。
- **影响范围**：**改任何 harness 源码后必须重新打包**，否则分发物仍是旧代码。
- **备注**：二进制产物；仓库内是否保留由 `.gitignore` 决定。

### `sahou-harness/assets/sha.ico`
- **用途**：桌面端与打包程序的 **Windows 图标**。
- **关键内容**：ICO 图标文件。
- **依赖**：由 `make_icon.py` 生成。
- **被依赖**：`sha.spec` / `ShaDesktop.spec` 的图标配置、`desktop.py` 窗口图标。
- **影响范围**：换图标需重跑 `make_icon.py` 并重新打包。
- **备注**：二进制产物。

### `sahou-harness/_diag/*`（通配 —— **临时诊断脚本，非正式代码**）
- **用途**：为排查"右侧文件区无法展开/点击"而临时搭建的**诊断工装**，不属于产品代码。
- **关键内容**：
  - `server.py`：注入 mock `pywebview.api` 的本地预览服务（8765 端口）。
  - `probe.mjs`：Node + CDP 探针，试图连无头 Edge 检查文件区 DOM。
  - `probe_real.py`：用 pywebview 的 `evaluate_js` 在**真实窗口**里执行探针脚本。
  - `launch_desktop.py`：带 `--remote-debugging-port=9335` 启动真实桌面端。
  - `edge.log`、`server.log`、`probe_out.txt`：诊断输出。
  - `edgeprofile/`：无头浏览器临时 profile。
- **依赖**：`harness.desktop`、`harness.config`、本机 Edge/pywebview。
- **被依赖**：无。
- **影响范围**：无。
- **备注**：**均为一次性排查产物，可整体删除**；若保留，注意 `edgeprofile/` 体积与 `probe_out.txt` 中的环境信息。
