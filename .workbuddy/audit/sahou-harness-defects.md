# sahou-harness 缺陷审计报告

审计时间：2026-09-26　审计对象：`E:/文件/编程文件/agent/sahou-harness`（微内核「一切皆插件」agent harness，执行引擎复用 nanoagent）
审计方式：全文阅读 + 真实运行复现（Python 3.14 / .venv 3.14 + 无头 Edge(CDP) 驱动器）。**未修改任何源码**。
复现脚本与原始输出：`E:/文件/编程文件/agent/.workbuddy/audit/`（`hh_*` 前缀；`probe_out*.json` 为真实输出）

## 概览

- 审计文件数：**36**（harness 7 个模块全文；builtins 7 插件 ×（plugin.json+register.py）；tests 2；根脚本 7；pyproject/README；nanoagent 接缝 4（tools/llm/skills/mcp + agent/memory 关键片段））
- 缺陷数：**29**（**P0 × 3**，**P1 × 6**，**P2 × 20**）
- 测试基线：`python -m unittest discover tests` → **Ran 41 tests OK**（全绿，但见「测试盲区」——上面 3 个 P0 一个都没被覆盖）
- 一句话总评：**微内核骨架（ctx/effect/状态机）确实能跑通，`effect` 的失败回滚也真的生效；但内核把「订阅回收」「嵌套服务重建」两处做漏了，权限门是 fail-open 的字符串比较，配置层是「无声吞掉一切」的读写模型，而那个「已知未解决」的右侧文件区 bug 根因不在前端——是后端 `ws_tree` 用未 resolve 的 root 去比对已 resolve 的 target，只要工作区是相对路径（CLI 默认值 `.`）就永远返回「路径越出工作区」。**

---

## P0 严重

### H-01 shell/文件写入权限门 fail-open：非 `ask/allow/deny` 的任何值都直接放行

- **位置**：`harness/builtins/tools_shell/register.py:18-25`、`harness/builtins/tools_fs/register.py:44-52`
- **类型**：安全 / 访问控制绕过（fail-open）
- **现象**：权限门是「等值比较 + 无 else 分支」：
  ```python
  mode = (config.get("permissions") or {}).get("shell", "ask")
  if mode == "deny":  return "错误：…被权限配置拒绝"
  if mode == "ask":   …确认…
  # 没有 else：任何第三种取值都直接执行
  ```
  因此 `permissions.shell = "Ask" | "Deny" | "deny "（尾随空格）| "no" | null | 0 | true` 等**任何非规范值都不会过门**，命令无条件执行；`permissions.fs` 同理（写文件不受任何确认）。
- **复现/证据**（`hh_kernel_repro.py` 段 [F]，真实运行输出）：
  ```
  permissions.shell = 'Ask'   → [exit 0] BYPASS-Ask
  permissions.shell = 'Deny'  → [exit 0] BYPASS-Deny
  permissions.shell = 'deny ' → [exit 0] BYPASS-deny
  permissions.shell = 'no'    → [exit 0] BYPASS-no
  permissions.shell = None    → [exit 0] BYPASS-None
  permissions.shell = 0       → [exit 0] BYPASS-0
  permissions.shell = True    → [exit 0] BYPASS-True
  ```
  （测试里 `host.confirm` 被替换成「一旦被调用就抛 AssertionError」，上面 7 次都没有触发确认。）
- **根因**：把「用户可手改的 JSON 字段」当作枚举白名单来做等值判断，既没有 `else: deny` 的 fail-closed 兜底，也没有在 `Profile.load_config()` 层做取值校验；`config.PERMISSION_MODES` 只在桌面端 `set_permission` 用了一次，管不到配置文件。
- **修复建议**：把判定改成白名单 + 默认拒绝：`if mode not in ("allow",): 走 ask/deny 分支`（即 `mode == "allow"` 才放行，其余一律要求确认或拒绝）；并在 `Profile.load_config()` 里对 `permissions.{shell,fs}` 做归一化（非法值回落 `"ask"`）与告警。

### H-02 桌面端右侧文件区在「相对工作区」下彻底无法展开（＝用户报告的 bug）

- **位置**：`harness/desktop.py:531,533,534`（`ws_tree`）＋ `harness/cli.py:32,43`（`host.workspace = args.workspace`，默认 `"."`）＋ `harness/desktop.py:2075-2077`（仅当配置里有可用 `workspace` 才覆盖）
- **类型**：功能失效（核心功能完全不可用）
- **现象**：工作区是相对路径时，右侧「工作区」页**能列出根目录，但点任何文件夹都只显示 `路径越出工作区`，永远无法逐层展开**——与用户描述逐字吻合。
- **复现/证据**（端到端，真实 `DesktopApp.ws_tree` + 真实 `UI_HTML` + 无头 Edge 真鼠标点击，`hh_serve_rel.py` / `hh_probe9.mjs` / `probe_out9.json`）：
  ```json
  "step1_root": {"crumb":"📁 /（工作区根目录）","rows":7,
                 "paneText":"📁nanoagent📁sahou📁sahou-harness📄FILE_INDEX.md…"},
  "clickedDir": {"text":"📁nanoagent","cx":1000,"cy":141},
  "step2_afterRealClick": {"crumb":"/","rows":0,"paneText":"路径越出工作区"},
  "errors": "[]"
  ```
  即：根目录 7 项正常渲染 → 点击第一个目录 → 面板只剩错误文案 `路径越出工作区`，行数 0，且**无任何 JS 报错**。后端单元级证据（`hh_repro2.py` 段 [M]）：
  ```
  workspace = 'C:/…/tmp…/ws/'      → ws_tree()      = ok=True,  entries=[sub]
  workspace = 'ws'（相对）          → ws_tree('sub') = ok=False, error='路径越出工作区'
  ```
- **根因**：见【专项】章节（一句话：`root` 未 `resolve()` 而 `target` 已 `resolve()`，`relative_to` 必然抛 `ValueError`）。
- **修复建议**：`desktop.py:531` 改为 `root = Path(ws).resolve()`；并在 `cli.build_runtime` 把 `workspace` 规范成绝对路径。

### H-03 配置层并发写丢更新 + 半写文件被静默当作默认配置（可静默丢失全部模型与 API Key）

- **位置**：`harness/config.py:51-58`（`load_config`）、`60-63`（`save_config`）、`65-69`（`update_config`）
- **类型**：数据丢失 / 并发
- **现象**：`save_config` 用 `Path.write_text` 直接截断写入（无临时文件 + `os.replace`、无锁、无 fsync）；`update_config` 是「读—改—写」。桌面端每个 `window.pywebview.api.*` 调用都在**独立线程**执行，多个调用（`set_permission` / `set_thinking` / `_touch_session` / `_register_workspace` 都没有持锁）并发时：(1) 丢更新；(2) 读到被截断的空文件 → `load_config` 静默回退 `DEFAULT_CONFIG` → **下一次写回就把用户的 models/api_key/workspaces 全部抹掉**。
- **复现/证据**（`hh_kernel_repro.py` 段 [H]，真实运行输出）：
  ```
  4 线程 x 40 次「读-改-写」自增后 counter = 41 （期望 160）
  期间线程抛 KeyError: 'counter'   ← 说明有线程读到了被截断/空白的 config.json
  ```
  以及段 [G]：`config.json` 写成 `not-json` 后 `load_config()` 返回 `{'default_model':'', 'models':[], 'permissions':{'shell':'ask'}}`（**没有异常、没有告警**），紧接着 `update_config(a=1)` 就把这个默认值落盘覆盖了原文件。
- **根因**：非原子写 + 无锁的读改写 + 解析失败静默容错（三者叠加会把「瞬时损坏」放大成「永久数据丢失」）。
- **修复建议**：`save_config` 先写同目录临时文件再 `os.replace`；`update_config` 加 `threading.Lock`（或 profile 级 RLock）；`load_config` 解析失败时**抛出/记录并备份原文件**，绝不静默回落默认值。

---

## P1 中等

### H-04 `ctx.on` 订阅不随插件卸载回收 —— 已卸载插件的监听器仍在触发

- **位置**：`harness/kernel.py:132-134`（`Context.on`）、`harness/kernel.py:105-119`（`Context.__init__` 未把 `on` 的 disposer 记账）、`harness/kernel.py:33-42`（`EventBus.on` 明明返回了 disposer）
- **类型**：资源泄漏 / 生命周期契约违背
- **现象**：`Context.on(event, handler)` 直接 `return self.bus.on(event, handler)`，**返回的 disposer 没有被塞进 `self._disposers`**；`Context.__init__` 也没有像它自己承诺的那样把「订阅」纳入账本。于是插件 `deactivate()` 时 `_disposers` 里根本没有这条订阅，监听器永久留在 `EventBus._handlers` 上。这与模块头部文档（`kernel.py:6`）「effect(fn) 注册的资源必须返回 disposer，deactivate 时按 LIFO 回滚」直接冲突——插件作者只要用更自然的 `ctx.on` 就会踩坑，而用 `ctx.effect(lambda: bus.on(...))` 才正确。
- **复现/证据**（`hh_kernel_repro.py` 段 [A]，真实运行输出）：
  ```
  activate 后 seen = ['sub']
  deactivate 后 state = DISPOSED  services = {}
  deactivate 之后再 emit('activate') → seen = ['other']
  >>> 已卸载插件的监听器是否仍在触发: True
  ```
  注意 `seen` 从 `['sub']` 变成 `['other']`——**第一个元素 'sub' 是已卸载插件的监听器，它还在向同一个列表写**。
- **根因**：`Context.on` 只是转发，没有 `self._disposers.append(disposer)`；内核把「订阅」当成 `EventBus` 的职责，但 `EventBus` 只负责返回 disposer，回收责任在 `Context`。
- **修复建议**：
  ```python
  def on(self, event, handler):
      dispose = self.bus.on(event, handler)
      self._disposers.append(dispose)
      return dispose
  ```

### H-05 `Harness.deactivate` 重建服务表时丢掉 `models` 嵌套注册表

- **位置**：`harness/kernel.py:261-264`（重建循环）对比 `harness/kernel.py:242-245`（激活时注册）
- **类型**：状态丢失 / 内核契约不闭合
- **现象**：`activate()` 除了 `self.services.update(ctx.services)`，还会**额外**把模型池写进 `services["models"]`（`244-245`：`self.services.setdefault("models", {})[model_name] = llm`）。但 `deactivate()` 只做 `self.services.update(plugin.ctx.services)` 来重建，**没有重建 `services["models"]`**。结果是：只要卸载/移除**任意一个**插件，`host.service("models")` 就凭空消失，直到进程重启。
- **复现/证据**（`hh_kernel_repro.py` 段 [B]，真实运行输出）：
  ```
  激活后 services keys = ['models', 'models_runtime', 'svc_a', 'svc_b', 'svc_c']
  激活后 models = ['m1']
  卸载无关插件 c 后 services keys = ['models_runtime', 'svc_a', 'svc_b']
  >>> models 是否还在: False
  >>> models_runtime 是否还在: True
  ```
- **根因**：激活与卸载两条路径对服务表的构造逻辑不对称（`activate` 有两段注册，`deactivate` 的重建只有一段）。
- **修复建议**：把「按 ctx 聚合服务」抽成一个私有方法，激活/卸载共用；在其中补上
  ```python
  for model_name, llm in plugin.ctx.models_map.items():
      self.services.setdefault("models", {})[model_name] = llm
  ```
- **影响备注**：当前 `models` 插件把模型池放在 `models_runtime`（一个普通服务）里，`services["models"]` 暂无消费方，因此尚未炸；但它是内核公开的服务契约，任何按 `service("models")` 取工具的插件都会断。

### H-06 `install_plugin` 热激活用「目录名」当插件名 → 静默失败却返回 `ok: true`

- **位置**：`harness/desktop.py:649-656`（`self.host.activate(dest.name)`），对比 `harness/kernel.py:189`（`mount` 用的是 `load_manifest(path).get("name")`）
- **类型**：功能失效 + 错误信息弱化
- **现象**：`install_plugin` 先 `self.host.mount(dest)`（`mount` 以 **`plugin.json` 里的 name** 登记记录，如 `cool-name`），紧接着却 `self.host.activate(dest.name)`（用的是**复制后目录名**，如 `my-plugin-dir`）。两者不一致时 `activate` 抛 `KeyError: 插件 'my-plugin-dir' 不存在`，被 `except Exception` 捕获后只写成 `note`，函数**仍然返回 `{"ok": True}`**。前端 `desktop.py:1749-1750` 只在 `res.ok` 为真时显示 `res.name + note`，用户看到「已安装」的绿色提示，实际插件从未激活。
- **复现/证据**（`hh_repro2.py` 段 [K]，真实运行输出）：
  ```
  install_plugin 返回: {'ok': True, 'name': 'my-plugin-dir',
                        'note': '热激活失败（重启后生效）: "插件 \'my-plugin-dir\' 不存在"'}
  插件是否真的热激活（services 里有无 cool）: False
  host.plugins 键: [... 'cool-name' ...]        ← 记录以 manifest name 登记
  ```
- **根因**：`mount` 与 `activate` 对「插件标识」的口径不一致（manifest name vs 目录名），且 `activate` 的失败被降级成 note 而非错误。
- **修复建议**：`record = self.host.mount(dest); self.host.activate(record.name)`；`except` 时返回 `{"ok": False, "reason": ...}` 或至少把 note 升级为 `error` 字段，让前端红色提示。

### H-07 `load_config` 浅合并 + 无类型校验：`permissions` 会丢键、写成 list 直接崩

- **位置**：`harness/config.py:51-58`（`load_config`）；消费点 `harness/builtins/tools_shell/register.py:19`、`harness/builtins/tools_fs/register.py:46`、`harness/desktop.py:177-178`
- **类型**：配置健壮性（数据损坏 / 崩溃）
- **现象**：`config = dict(DEFAULT_CONFIG); config.update(data)` 是**顶层浅合并**——只要用户的 `config.json` 里 `permissions` 是 `{"fs":"ask"}`，默认的 `{"shell":"ask"}` 会被**整体替换**，`shell` 键消失；下游 `.get("shell","ask")` 用默认值兜住，但一旦用户显式设了别的键（如只想改 fs），shell 的「用户显式意图」就丢了。更糟的是 `permissions` 被写成非 dict（如 `[]`）时没有任何校验，`(config.get("permissions") or {}).get(...)` 直接 `AttributeError` 崩溃。`load_config` 对解析失败也只是静默回落 `DEFAULT_CONFIG`（与 H-03 同源）。
- **复现/证据**（`hh_kernel_repro.py` 段 [G]，真实运行输出）：
  ```
  写入 permissions={'fs':'ask'} 后 load_config()['permissions'] = {'fs': 'ask'}
  >>> shell 键是否被默认值丢失（浅合并）: True
  permissions 写成 list 后崩溃: AttributeError 'list' object has no attribute 'get'
  ```
- **根因**：无 schema / 无深合并 / 无类型归一化，把「用户可手改的 JSON」当可信结构用。
- **修复建议**：`load_config` 返回前做归一化——`permissions` 必须是 `dict`，否则回落默认并告警；`permissions` 内部与 `DEFAULT_CONFIG` 做**深合并**；`models` 必须是 `list`；非法则记录警告（可配合 H-03 的「不静默」策略）。

### H-08 REPL 插件引用不存在的 `host.harness` → `/plugins` 与未知命令必抛 `AttributeError`

- **位置**：`harness/builtins/repl/register.py:16`（`print_help`）、`:28`（`/plugins` 分支）、`:38`（`commands = host.harness.collect_commands()`）
- **类型**：功能失效（REPL 命令不可用）
- **现象**：`host` 就是 `Harness` 实例本身（`ctx.host`，见 `kernel.py:221`），它**没有** `harness` 属性。正确写法是 `host.collect_commands()` / `host.list()`（`kernel.py:283`、`kernel.py:294`）。因此：
  - 输入 `/plugins` → `AttributeError: 'Harness' object has no attribute 'harness'`；
  - 输入任何**未知**命令 → 走到 `:42` 的 `print_help()` → 同样抛错。
  REPL 主循环（`:59-65`）用 `except Exception as exc: print(f"[出错] {exc}")` 兜住，所以表现为「永远打不出插件列表 / 永远打不出帮助」，而不是崩溃退出——更难排查。
- **复现/证据**（`hh_repro2.py` 段 [I]，真实运行输出 + 静态确证）：
  ```
  build_runtime 是否成功 → state: {'chat_loop':'ACTIVE', ..., 'repl':'ACTIVE'}
  Harness 是否有 harness 属性: False
  正确写法应是 host.collect_commands / host.list（Harness 自身）
  ```
  静态：`kernel.py:294 def list(self)`、`kernel.py:283 def collect_commands(self)` 都直接挂在 `Harness` 上。
- **根因**：把 `ctx.host` 误当成「还有一层 `.harness` 的包装对象」，与实际内核 API 不符（疑似从其它架构迁移时的残留写法）。
- **修复建议**：删掉全部 `.harness`——`:16` 与 `:38` 改 `host.collect_commands()`，`:28` 改 `host.list()`。

### H-09 桌面端 `status()/usage()/context_usage()`：AnthropicLLM 用量恒空，且每次轮询都触发懒构建副作用

- **位置**：`harness/desktop.py:162-167`（`status`）、`482-488`（`usage`）、`490-510`（`context_usage`）；接线对方 `harness/builtins/models/register.py:12-16`
- **类型**：接线不匹配（属性缺失）+ 副作用
- **现象（属性缺失，可确证）**：`desktop.py:167/487` 用 `getattr(llm, "total_usage", {})` 取用量、`181/499` 用 `getattr(llm, "context_window", 0)` 取窗口。但 `nanoagent.LLM` 有这两个属性，**`nanoagent.AnthropicLLM` 没有**（`nanoagent/nanoagent/anthropic_llm.py:255-273` 的 `__init__` 只设了 `model/base_url/api_key/temperature/max_tokens`）。于是只要是 `provider: anthropic` 的模型：`status().usage` 与 `usage()` 恒为 `{}`，UI 用量条永远为空；`context_window` 恒 0，`context_usage` 落回写死的 `128000`，与实际模型窗口不符。`models/register.py:12-16` 的 anthropic 分支也确实没传 `context_window`。
- **现象（副作用）**：`status()` 是前端 `refreshStatus()` 的高频轮询入口，它每次都会 `self.host.service("agent_factory")()`。首次调用会**真正构造 nanoagent `Agent`**（读 profile 的 sessions、扫 skills 目录、聚合全部工具），把「查看状态」变成一次有 IO 的构建；`context_usage()` 同源。
- **证据**：
  - `grep` 确证 `nanoagent/nanoagent/llm.py:136-138` 有 `reasoning_effort/context_window/total_usage`，而 `AnthropicLLM.__init__` 无对应赋值（`anthropic_llm.py:255-273`，已全文阅读）。
  - `desktop.py:163-166` 与 `484-486` 的 `try/except` 明确以「未配置模型时静默」为目的，说明作者知道这里会构建。
- **根因**：把「取 llm 元数据」和「构建 agent」耦合在一个高频只读接口里；同时假设 provider 实现都暴露与 `LLM` 相同的属性面，未做适配层。
- **修复建议**：(1) 让 handler 缓存 agent 引用（或让 `status` 只读 `models_runtime`，不触碰 factory）；(2) 对 `total_usage/context_window` 用「LLM 与 AnthropicLLM 的共同能力」——建议在 models 插件构建时归一化，给 AnthropicLLM 实例补 `total_usage={}`、`context_window=<按模型推断或可配置>`，或在 `_build_llm` 里为两种 provider 都显式传入 `context_window`。

---

## P2 轻微

1. **`EventBus.emit` 静默吞掉监听器异常**（`harness/kernel.py:44-49`）。`except Exception: pass` 连日志都没有——插件监听器坏了宿主完全无感。证据（`hh_kernel_repro.py` 段 [D]）：抛异常的监听器执行后，控制台**没有任何异常信息**。建议 `logging.exception` 或至少 `emit("error", ...)` 回灌（注意别递归）。
2. **`loader.run_register` 泄漏 `sys.modules`**（`harness/loader.py:32-35`）。用 uuid 命名模块塞进 `sys.modules` 但**从不清理**。证据（`hh_repro2.py` 段 [L]）：反复激活/卸载一个插件后，`sys.modules` 中 `harness_plugin_*` 模块数 `24 → 25`。桌面端「移除→重装→热激活」会让模块表单调膨胀。建议 defer 里 `sys.modules.pop(module_name, None)`（或统一用一次性的模块命名空间对象）。
3. **`load_manifest` 对损坏 `plugin.json` 静默回落目录名**（`harness/loader.py:21-23`）。证据（段 [L]）：`plugin.json` 写入 `{ 这不是 json` 后 `mount` 得到 `name='badjson'`、`manifest={'name':'badjson'}`，**无任何告警**。插件作者会以为清单生效了。建议 `except` 时记录 warning 并在 `PluginRecord.skipped` 标注 `bad-manifest`。
4. **`skills/register.py:11` 恒真判断**：`if profile_skills.is_dir() or True:` —— `or True` 使条件永真，`is_dir()` 成了死代码。虽不影响行为（本意就是「目录不存在也声明」），但会误导读者以为有分支。建议删掉 `if` 直接用注释说明。
5. **`renderCards` 单引号上下文未转义 `'`**（`harness/desktop.py:1700`）：`onchange="editing.default_model='${esc(m.name)}'"`。`esc()`（`:1241-1244`）只转义 `& < > "`，**不转义单引号**；而这里 JS 字符串用的是单引号。模型名里出现 `'`（如 `o'brien`）会截断字符串、破坏该 `onchange` 表达式，默认模型选择失效。同函数 `:1684/1691/1695/1697` 的 `value="${esc(...)}"` 在双引号属性内是安全的，仅 `:1700` 有问题。建议改用 `JSON.stringify` 注入或给 `esc` 加 `'` 转义。
6. **`md()` 粗体正则对 `***`/相邻标记错配**（`harness/desktop.py:1245-1250`）。`/\*\*([^*\n]+)\*\*/g` 遇到 `***粗体***` 或 `a**b**c**d` 会错切；且 `<code>` 内文本仍会被后续粗体替换波及。纯展示问题，建议加边界或先保护 code 段。
7. **技能 token 分项估算口径错误**（`harness/desktop.py:510`）：`estimate_tokens(getattr(agent, "_skills_marker", ""))`。nanoagent 里 `_skills_marker` 是字面常量 `"# 可用技能"`（`nanoagent/nanoagent/agent.py:104`），真正追加的技能摘要在 `enable_skills()`（`agent.py:604-606`）里被拼进 `instructions`。因此「技能」分项恒为 ~4 tokens，真实技能文本被并进「系统提示词」。建议改为按 `instructions` 中 marker 之后的部分估算，或让 `enable_skills` 暴露技能摘要。
8. **`get_models()` 原样回传明文 API Key**（`harness/desktop.py:403-406`）：直接 `return {"models": config.get("models")}`，把含 `api_key` 的完整条目送给前端 JS，再由 `:1697` 填进 `<input type="password">`。本地窗口风险有限，但任何注入到 DOM 的脚本/扩展都能直读密钥。建议后端返回时对 `api_key` 做掩码（如 `sk-***ab`），保存时前端空值即「保持原值」。
9. **`_rebuild_pool` 早退导致「配置已落盘、运行时仍是旧池」**（`harness/desktop.py:458-464`）：循环内 `except: return f"模型 {name} 构建失败: {exc}"` 直接返回，而 `runtime["pool"]/["order"]/["current"]` 的赋值在**循环之后**，于是部分失败的保存会把 config 写成功（`save_models` 已 `update_config`）却完全不更新运行时池，直到重启才一致。`ok` 仍为 `True`。建议逐条容错（跳过坏模型）并把 pool 更新移到 try 外层，返回结构化 warning 列表。
10. **`AnthropicLLM` 缺 `total_usage`/`context_window`**（`nanoagent/nanoagent/anthropic_llm.py:255-273`）。与 H-09 同源，但可独立修复：给该类补上与 `LLM` 一致的两个属性，避免所有下游 `getattr` 恒取默认。
11. **`_confirm` 最长阻塞 1 小时**（`harness/desktop.py:144`）：`for _ in range(36000): ... time.sleep(0.1)`。若用户不点对话框也不关窗口，js_api 线程被占用 1 小时；且轮询期间每个 `evaluate_js` 都是一次跨进程调用。建议改用事件/`Promise` 或指数退避 + 总超时（如 120s）。
12. **`review()` 固定 `encoding="utf-8"` 读 git 输出**（`harness/desktop.py:570-572`）：Windows 中文版 git 的 `status` 输出常为 GBK，`errors="replace"` 只能保证不抛异常、结果会变乱码。建议 `encoding=locale.getpreferredencoding(False)`（或 `git -c core.quotepath=false` + 探测）。
13. **`run_terminal` 未捕获 `tool.invoke` 异常**（`harness/desktop.py:554-560`）：`tool.invoke(...)` 一旦抛错（如超时之外的 OSError），会以未捕获异常形态越过 js_api 边界，前端只能拿到 reject。建议 `try/except` 返回 `{"ok": False, "output": ...}`。
14. **`remove_plugin` 静默吞掉卸载失败**（`harness/desktop.py:658-664`）：`try: self.host.deactivate(name) except Exception: pass` 后**仍然** `profile.remove_plugin(name)` 删目录。若 `deactivate` 中途抛错（disposer 未跑完），会留下「目录已删但连接/线程未回收」的半状态。建议区分「未激活」与「卸载出错」，后者返回错误。
15. **`cli.main` 的 `plugin add` 未捕获 `FileNotFoundError`**（`harness/cli.py:88-90`）：`profile.install_plugin` 对不存在目录 `raise FileNotFoundError`（`config.py:77-78`），这里没有 try → 用户看到的是未处理异常栈而非友好提示。建议 `except OSError as exc: print(...); return 1`。
16. **`model use <不存在>` 退出码恒 0**（`harness/cli.py:106-110`）：`set_current` 返回「错误：没有模型 'ghost'」被 `print` 后仍 `return 0`，脚本无法据此判断失败。建议检测 `message.startswith("错误")` 时 `return 1`。
17. **`chat` 未包装 LLM 异常**（`harness/cli.py:142-146`）：`ui(args.message)` 只捕获 `KeyboardInterrupt`。实测（本会话）：在未配置模型/密钥无效时 `sha chat -m "你好"` 直接冒泡 `openai.AuthenticationError: 401`，并以未处理异常退出。建议捕获 `Exception` 打印中文错误并 `return 1`。
18. **打包/测试脚本硬编码绝对路径**：`run_tests.py:5-6`（两处 `sys.path.insert(0, r"E:/文件/编程文件/agent/sahou-harness...")`）、`smoke_desktop.py:7`（`ROOT = Path(r"E:/文件/编程文件/agent/sahou-harness")`）。换机器/换目录立即失效。建议统一用 `Path(__file__).resolve().parent`。
19. **`serve_ui_preview.py` 的 mock 只返回一层固定 4 项**（`serve_ui_preview.py:94-99`）：`ws_tree` mock 无论传什么 `p` 都回同样的 4 条，且 `rel: p || ''`。因此**逐层展开这条链路从未被任何自动化验证**——这正是 H-02 能长期存活的直接原因之一。建议 mock 改为按 `p` 返回不同层级（或直接接入真实 `DesktopApp.ws_tree`）。
20. **`mcp_client` 反复建/关事件循环**（`harness/builtins/mcp_client/register.py:21-27, 38, 40, 43`）：连接阶段每个服务器/工具各调一次 `asyncio.run`（各自新建并关闭一个 loop），卸载时 `disconnect_all` 又对每个 server 单独 `asyncio.run(server.disconnect())`。同一 MCP session 对象跨多个 loop 复用，在 asyncio/_anyio 底层易触发「attached to a different loop」。建议用一个常驻 loop（或 `asyncio.run` 一次包住整个 connect/disconnect 事务）。

> 附：`make_icon.py:30` 使用 `font.getsize("卅")`，该 API 自 Pillow 9.2 起弃用、10.0 起移除，且字体名 `msyhbd.ttc/msyh.ttc/simhei.ttf/simsun.ttc` 依赖 Windows 系统字体。**本环境未安装 PIL（`ModuleNotFoundError: No module named 'PIL'`），无法实跑验证**，故不计数，仅作版本兼容风险提示。

---

## 【专项】桌面端右侧文件区无法展开/点击 —— 根因分析

### 结论（一句话）

**主因是后端 `DesktopApp.ws_tree` 的 `root` 没有 `resolve()`，而 `target` 已 `resolve()`**：只要 `host.workspace` 是**相对路径**（CLI 默认 `--workspace "."`，且 profile 尚无有效绝对 `workspace` 时桌面端不会覆盖它），点任意子目录都会让 `target.relative_to(root)` 抛 `ValueError` → 返回「路径越出工作区」→ 前端 `loadWsTree()` 把面板换成这行错误文案（行数归零），于是「无法向下展开、无法打开文件夹」。前端的事件绑定、`esc()`、`wsPath`、async 时序**全部正常**，已用真鼠标点击逐一排除。

### 根因（精确到行）

后端 `harness/desktop.py:526-552`：

```python
528  ws = str(getattr(self.host, "workspace", "") or "")
531  root = Path(ws)                                    # ← 未 resolve（相对则仍是相对）
532  try:
533      target = (root / subpath).resolve() if str(subpath) else root   # ← 真子路径时 target 变绝对
534      target.relative_to(root)                        # ← 绝对 relative_to 相对 → ValueError
535  except ValueError:
536      return {"ok": False, "error": "路径越出工作区"}
```

- `subpath == ""`（首次加载）：`target = root`，`root.relative_to(root)` 恒成立 → **根目录永远能列出**（对应用户看到的「上层列表是好的」）。
- `subpath == "sub"` 且 `workspace` 为相对（如 `"."` 或 `"ws"`）：`target = Path(".").joinpath("sub").resolve()` 是**绝对**路径，`root = Path(".")` 是**相对**路径 → `Path.relative_to` 要求同类型，抛 `ValueError: '…' is not in the subpath of '.'` → 落入 `536` 返回「路径越出工作区」。

`workspace` 为什么会是相对路径：

- `harness/cli.py:43` `--workspace` 默认 `"."`；`harness/cli.py:32` `host.workspace = workspace` **未规范化**。
- `harness/desktop.py:2075-2077`：仅当 `profile.load_config()["workspace"]` 存在且 `is_dir()` 时才覆盖：`if saved_ws and Path(saved_ws).is_dir(): host.workspace = saved_ws`。
- 因此**新 profile / 首次从终端用相对路径启动 `sha desktop`** 时 `host.workspace = "."`，直接触发该 bug。这也解释了为什么它在开发机（已用 GUI 选过绝对工作区、配置里有绝对 `workspace`）不出现、而在用户机器上稳定复现。

### 端到端证据（真实后端 + 真实 `UI_HTML` + 无头 Edge 真鼠标点击）

`hh_serve_rel.py`（`host.workspace = "."`）+ `hh_probe9.mjs` → `probe_out9.json`：

```json
"step1_root":           {"crumb":"📁 /（工作区根目录）", "rows":7, "paneText":"📁nanoagent📁sahou📁sahou-harness📄FILE_INDEX.md…"},
"clickedDir":           {"text":"📁nanoagent", "cx":1000, "cy":141},
"step2_afterRealClick": {"crumb":"/", "rows":0, "paneText":"路径越出工作区"},
"errors": "[]"
```

对应后端单元级证据（`hh_repro2.py` 段 [M]，同一次运行）：

```
workspace = 'C:/Users/find/AppData/Local/Temp/tmp.../ws/' → ws_tree('sub') = {'ok': True, 'rel': 'sub', ...}
workspace = 'ws'（相对）                                   → ws_tree('sub') = {'ok': False, 'error': '路径越出工作区'}
```

### 前端取证：排除「前端事件/渲染坏了」

同一套无头 Edge + CDP 真实事件探针（`hh_probe*.mjs`，`probe_out*.json`）已确认：

| 检查 | 结果 | 说明 |
|---|---|---|
| `dupIds` | `[]` | 无重复 id，`$()` 取元素不会错拿 |
| 标签页真实点击 `switchPanel('ws')` | `activeAfterTabClick = "rp-ws"` | 标签切换正常 |
| 目录行中心命中 | `dirRow.hitIsSelf = true` | 无遮罩/无元素遮挡 |
| 绝对工作区下真实点击目录 | `afterDirClick.crumb = "📁 alpha"` | **点击机制本身工作**（问题在相对工作区） |
| `window.onerror` / `errors` | `[]` | 无全局 JS 报错 |

→ `loadWsTree()`（`desktop.py:1910-1936`）、目录行 `row.onclick`（**`desktop.py:1932`**）、`wsUp()`（`:1937-1942`）、`wsPath`（`:1897`）逻辑均正确；`esc()`（`:1241`）在文本节点上下文安全。**用户描述的「无法展开/无法点击」= 后端把每次下钻都判成越界。**

### 次因（潜伏，非本次主因）：右侧面板的高度链在最小窗口尺寸附近已溢出

`harness/desktop.py` 的布局：`html,body{height:100%}`（`:700`）+ `.app{height:100vh}`（`:708`）+ `#hero{flex:1}`（`:755`，未设 `min-height:0`）+ `aside.right{width:360px}`（`:891`）。视口扫描（`hh_probe8.mjs` → `probe_out8.txt`）：

```
940x620 -> htmlH:639  (innerH:620)   ← pywebview min_size=(940,620) 客户区 ~924x581，已溢出
700x741 -> htmlH:947  mainW:80
660x741 -> scrollY:366 htmlH:1107 asideTop:-366 asideRight:660   ← 右侧栏被顶出可视区
errors: "[]"
```

即：在**最小窗口尺寸**附近页面内容已高于视口（`#hero` 的固定内容撑爆 `flex:1`）；视口继续变窄时 `aside.right` 的 `top` 变为负、跑到视口之外，鼠标点击自然落空。**说明**：本会话环境无法创建 WebView2 窗口（官方 `smoke_desktop.py` 输出 `SMOKE RESULT: timeout`，自写 `hh_real.py` 输出 `stage: not-started`），故以上窄视口数据来自无头 Edge + `Emulation.setDeviceMetricsOverride` 的**模拟**，可低于 pywebview 的 `min_size`，属「模拟桌面端、非像素级复现」；真实窗口中此路径主要受 DPI 缩放/客户区尺寸影响，为**次要风险**，不是本次「无法展开」的原因。

### 最小修复方案（只描述，不改代码）

1. **必改（根因）**：`harness/desktop.py:531` → `root = Path(ws).resolve()`。
   （`533` 之后 `target.relative_to(root)` 两边同为绝对路径，判定即正确。）
2. **加固**：`harness/cli.py:32` → `host.workspace = str(Path(workspace).resolve())`，让内核里 `workspace` 恒为绝对路径（`tools_fs` 已自行 `_workspace()` resolve，但 `ws_tree`/`run_terminal`/`review` 直接读 `host.workspace`）。
3. **顺手**：`desktop.py:551` `target.relative_to(root).as_posix()` 同样受益于 1；`desktop.py:2075-2077` 可在覆盖后统一 `host.workspace = str(Path(saved_ws).resolve())`。
4. **前端（次因，可选）**：给 `#hero` 加 `min-height:0`（或 `body{overflow:auto}`），并在 `.rp-pane`（`:907`）保留 `min-height:0` 已有；避免窄客户区时右栏被顶出。

### 验证方法

- **单测（最小）**：构造 `app = DesktopApp.__new__(DesktopApp)` 后设 `app.host.workspace = "ws"`（相对），断言 `app.ws_tree("sub")["ok"] is True`，且 `app.ws_tree("..")["ok"] is False`（越界仍要拦）。补一个「绝对路径」对照组即可锁死回归。
- **集成**：`hh_serve_rel.py`（已入库工作区，端口 8767）+ `hh_probe9.mjs`，断言 `step2_afterRealClick.rows > 0` 且 `paneText` 不含「路径越出工作区」。
- **端到端手测**：删除 `~/.sahou-harness/profiles/default/config.json` 里的 `workspace` 字段（或全新 profile），从终端 `cd` 到项目目录执行 `sha desktop`，点右侧「工作区」页里的任意文件夹——修复前必现「路径越出工作区」，修复后应正常逐层进入。

---

## 已验证「不是问题」的怀疑点

以下都在审计中被怀疑过，但用**真实运行**证伪（或证明确实正确），列出以免后续重复怀疑：

1. **`effect` 的 disposer 在插件 `FAILED` 时确实会执行，且不污染全局服务表**（`hh_kernel_repro.py` 段 [E]）：
   ```
   state = FAILED  error = RuntimeError: 后半段崩了
   失败插件 effect 的 disposer 是否执行: ['disposed']
   失败插件是否污染全局 services: {}
   ```
   `Harness.activate`（`kernel.py:224-230`）的 `ctx.deactivate()` + `record.ctx=None` 是对的实现——**内核这块是干净的**。
2. **`ws_tree` 后端在绝对工作区下完全正常，包括带尾随分隔符**（段 [M]）：`workspace='…\ws\'` 时 `ws_tree()` 与 `ws_tree('sub')` 均 `ok=True`。问题只在**相对** `workspace`（H-02）。
3. **路径监狱能拦住绝对路径与 `..` glob**（段 [J]）：`read_file("C:/Windows/win.ini")` → `ValueError: 路径越出工作区`；`list_files("../*")` → `（无匹配文件）`（Python 3.13+ `Path.glob` 本身已拒绝 `..`，属双重保险）；`write_file("../escape.txt")` 在 `test_desktop.py:229-230` 亦被拦。→ 逃逸方向**不成立**（真正的问题是反方向的 fail-open，即 H-01）。
4. **符号链接逃逸未能证实**：本环境 `link.symlink_to(outside, target_is_directory=True)` 虽返回成功，但随后 `read_file("link_out/secret.txt")` 抛 `FileNotFoundError`（段 [J]），**未能构造出成功逃逸的样本**。注：`_safe`（`tools_fs/register.py:16-24`）用 `resolved.parents` 判定，理论上 `resolve()` 会跟随软链从而拦住向外的软链——此点**保留为开放项**，未见反例。
5. **前端右侧面板无重复 id、无遮罩、无全局报错**（见【专项】表格）：`dupIds: []`、`dirRow.hitIsSelf: true`、`window.onerror/errors: []`。→ 「前端渲染中断 / 被遮挡」的假设**不成立**。
6. **`loadWsTree` 的 async/await 与 `pywebview.api` 时序正常**：在**绝对工作区**下真实点击目录后 `crumb` 变为 `📁 alpha`（成功进入）。→ 时序假设**不成立**。
7. **`esc()` 在文本节点上下文是安全的**（`desktop.py:1241-1244` 转义 `& < > "`）：树行、插件行、技能行的名字都放进文本节点/双引号属性，无破绽。唯一的例外是 `:1700` 的单引号 JS 字符串（已列 P2 #5）。
8. **`build_exe.py` 无需额外 `--hidden-import anthropic/httpx`**：`nanoagent.anthropic_llm` 在**模块顶层** `import httpx`，且构建命令有 `--collect-submodules nanoagent`，PyInstaller 的静态分析会自然收集 `httpx`。→ 打包缺依赖的假设**不成立**。
9. **同名 `provide` 的 LIFO 回收顺序是正确的**：`Context.deactivate`（`kernel.py:145-150`）从列表**尾部**弹出，因此后注册的 disposer 先跑、弹掉的是自己那版服务。段 [C] 观察到「手动乱序调用第 1 个 disposer 会误删第 2 版服务」只在**人为乱序**这一非现实路径下发生——正常卸载不会。
10. **`tools_shell` 用 `shell=True` 本身不是「注入漏洞」**：`command` 的语义就是「完整命令行」，来自模型/用户是本设计的预期（`desktop.py:554-560` 的终端也直接把用户输入当命令行）。真正的缺陷是权限门 fail-open（H-01），而非拼接方式。
11. **`_validate_url` 的 SSRF 防护有效**：`test_desktop.py:262-282` 覆盖 `localhost/127.0.0.1/192.168./10./169.254./[::1]/非 http`，均被拒。
12. **`remove_skill` 的越界防护有效**：`desktop.py:621-629` 用 `is_relative_to` 校验，`test_desktop.py:458-459` 的 `../../escape` 被拒。

---

## 测试盲区

现有测试基线：`python -m unittest discover tests` → **Ran 41 tests OK**（12.9s）。但**三个 P0 一个都没有被覆盖**，且多个 P1 所在路径完全没测到。根因是测试构造方式系统性地绕开了缺陷条件：

### 1. 直接掩盖 P0 的构造

| 缺陷 | 相关测试 | 为什么没抓到 |
|---|---|---|
| **H-01 权限门 fail-open** | `test_harness.py:179-193 test_shell_permission_gate`、`test_desktop.py:154-167 test_permission_roundtrip_shell_and_fs` | 只测 `allow`/`ask`/`deny`/**`set_permission` 的白名单**；被测工具本身从没喂过 `"Ask"`/`"deny "`/`None`/`0` 等非法值。 |
| **H-02 `ws_tree` 相对工作区** | `test_desktop.py:384-405 test_ws_tree_lists_and_jails` | 首先调用 `app.set_workspace(ws)`，而 `set_workspace` 会 `Path(path).resolve()`（`desktop.py:201`）把工作区变成**绝对路径** → 永远走不到 `root` 未 resolve 的分支。测试越界只测了 `"../.."`。 |
| **H-03 配置并发丢更新/半写** | `test_harness.py:249-254 test_config_roundtrip` | 单线程读改写一次；无并发、无损坏 JSON、无「解析失败后写回」的用例。 |

### 2. 覆盖盲区（有代码、无测试）

- **REPL 插件零测试**：没有任何用例调用 `host.service("ui")` 或执行 `/plugins`，因此 `host.harness` 的 `AttributeError`（H-08）从未暴露。
- **`ctx.on` / `EventBus` 订阅回收零测试**：`test_harness.py:133-140 test_events_emit` 只断言「emit 能触发」，**不检查卸载后监听器是否被移除**（H-04 因此漏网）。
- **`Harness.deactivate` 的服务表重建零测试**：没有「卸载一个插件后其它服务仍在」的断言（H-05 漏网）。
- **`install_plugin` 只在目录名 == manifest name 时测过**（`test_desktop.py:237-249`、`test_harness.py:237-247`，都建 `my-plugin` 目录 + `{"name":"my-plugin"}`）→ H-06 漏网。
- **`AnthropicLLM` 路径零测试**：`patch_model_build`（`test_harness.py:57-73`）**把 `nanoagent.LLM` 整个换掉**，测试里所有 provider（含 `anthropic`）都变成 `FakeLLM`；而 `FakeLLM`（`:21-34`）没有 `context_window`，于是 `test_desktop.py:148` 反而把「128000 默认值」断言成了**期望行为**，恰好掩盖了 AnthropicLLM 缺属性（H-09 / P2 #10）。
- **`desktop.py` 的 HTML/CSS/JS 零自动化**：`UI_HTML`（2089 行里的渲染层）没有任何 DOM/端到端测试；唯一的可视化途径 `serve_ui_preview.py` 用**手写 mock**（`ws_tree` 只回一层固定 4 项，`:94-99`），既不能验证逐层展开、也不接真实后端。
- **无并发测试**：`_register_workspace`/`set_permission`/`set_thinking`/`_touch_session` 都是「读-改-写 config」，测试全部串行调用，H-03 与 P2 #9 类问题不可见。
- **`_confirm` 的真实时序零测试**：`test_desktop.py:187-195 test_confirm_via_in_page_dialog` 用 `FakeWindow` 直接喂 `__dialogResult`，不经过 `evaluate_js`/真实 `showDialog`/`pywebviewready` 时序。
- **`cleanup` 类行为零测试**：卸载/失败/重装后的 `sys.modules`、事件监听器、MCP 连接回收都没有断言（P2 #2、H-04、P2 #20）。

### 3. 「只验证不崩」型断言

- `test_builtin_plugins_all_activate`（`test_harness.py:144-151`）只断言 6 个内置插件 `ACTIVE`，不校验它们**提供了什么**、提供物是否可用。
- `test_status_and_get_models`（`test_desktop.py:40-51`）只断言字段存在，不校验 `usage`/`context_window` 对真实 provider 是否有值。
- `test_plugin_install_and_remove`（`test_desktop.py:237-249`）只断言名字出现在列表里，不校验 `install_plugin` 返回的 `note` 是否其实是失败。
- `test_chat_error_returned_not_raised`（`test_desktop.py:69-80`）验证「错误被返回而非抛出」——方向正确，但同类健壮性只覆盖了 `chat` 一个入口，`run_terminal`/`review`/`install_plugin` 未覆盖。

### 4. 建议的补测清单（按性价比排序）

1. `ws_tree`：相对 `workspace` 下 `ws_tree("sub")` 必须 `ok`；`ws_tree("..")` 必须 `ok=False`。（锁 H-02）
2. 权限门参数化：`["allow","ask","deny","Ask","Deny","deny ","no","",None,0,True]` 全矩阵，断言仅 `allow` 直通、`ask` 走 confirm、其余 deny。（锁 H-01）
3. `update_config` 并发 N 线程自增 + 损坏 JSON 后不覆盖原文件。（锁 H-03）
4. `ctx.on` 卸载后 `bus` 中 handler 数归零；`Harness.deactivate` 后 `service("models")` 仍在。（锁 H-04/H-05）
5. `install_plugin` 目录名 ≠ manifest name 时 `ok` 与真实激活状态一致（锁 H-06）。
6. 用真实 `DesktopApp.ws_tree` 替换 `serve_ui_preview.py` 的 mock，并加一个「点目录 → 行数 > 0」的 headless 用例（补前端零覆盖）。
7. 给 `models/register.py` 的 anthropic 分支加一个「构建后 `llm.context_window`/`total_usage` 存在」的断言（锁 H-09/P2 #10）。

---

*报告结束。所有 `hh_*.py` / `hh_probe*.mjs` 复现脚本与 `probe_out*.json` 原始输出保留在 `E:/文件/编程文件/agent/.workbuddy/audit/`；审计过程未修改 `sahou-harness` 任何源码。*
