# nanoagent 缺陷审计报告

## 概览
- 审计范围：`nanoagent/nanoagent/` 下全部 30 个 py 文件（含 `rag/` 子包）+ `tests/`、`run_all_tests.py`、`pyproject.toml`、`.env`。
- 审计方式：逐文件静态阅读 + 编写 8 个临时复现脚本（`.workbuddy/audit/check_*.py`）用 `E:/文件/编程文件/agent/.venv/Scripts/python.exe`（Python 3.14.0）实跑验证。基线：`run_all_tests.py` 全量 302 个测试全部通过（`OK`）。
- 缺陷计数：**P0 ×2，P1 ×6，P2 ×15**（另有若干「已验证不是问题」与「怀疑待验证」）。
- 一句话总评：框架结构清晰、工程完成度高，但存在 **一个可越狱的沙箱逃逸（P0）** 和一个 **让整个可观测性功能静默失效的数据契约断裂（P0）**；工具 schema 生成在 `from __future__ import annotations` 下全面退化、同步路径调用异步工具会静默返回 coroutine 垃圾串，是两处影响面很大的正确性问题。

> 说明：每条 P0/P1 均附真实运行输出。脚本位于 `E:/文件/编程文件/agent/.workbuddy/audit/`。

---

## P0 严重（会导致数据错误/崩溃/安全问题）

### N-01 工作区沙箱可被 glob 模式 `../` 越狱，任意读取工作区外的文件
- **位置**：`nanoagent/coding.py:211`（`list_files`）、`nanoagent/coding.py:234`（`search_code`）
- **类型**：安全（路径穿越 / 沙箱逃逸）
- **现象**：`CodingWorkspace` 号称「路径监狱」，`_safe_path` 确实拒绝了 `../`。但 `list_files`/`search_code` 把模型可控的 `pattern` 直接传给 `self.root.glob(pattern)`，而 `pathlib.Path.glob` **允许模式中包含 `..`**。模型只需传入 `pattern="../*"`、`"../../*"`、`"../*.txt"` 即可列出并读取工作区外的任意文件内容（例如 `.env`、私钥、上级目录源码），完全绕过 `_safe_path` 的检查。`search_code` 会把越界文件的**内容**回给模型，是真正的数据泄露。
- **复现/证据**：脚本 `check_glob_escape.py`（工作区 `glob_ws/sandbox`，界外文件 `glob_ws/outside_secret.txt` 内容 `OUTSIDE-LEAKED-CONTENT`）：
  ```
  [1] _safe_path 对 '../outside_secret.txt' ：SandboxViolation: 路径越出工作区   ← 正常拦截
  [2] list_files(pattern='../*')          返回: '../outside_secret.txt'          ← 越界
  [3] list_files(pattern='../../*')       返回: '../../check_contract_and_schema.py\n../../check_future_annotations.py\n../../check_glob_escape.py'
  [4] search_code(query='OUTSIDE', pattern='../*.txt')
        返回: '../outside_secret.txt:1: OUTSIDE-LEAKED-CONTENT'                ← 内容泄露
  [5] list_files(绝对模式) → NotImplementedError（绝对模式被 pathlib 拒绝，但相对 ../ 可以）
  ```
  代码：
  ```python
  # coding.py:204-217
  def list_files(self, pattern: str = "**/*") -> str:
      for path in sorted(self.root.glob(pattern)):   # ← pattern 未做任何约束
          if not path.is_file(): continue
          if any(part in self.ignores for part in path.parts): continue
          matches.append(self._display(path))
  # coding.py:219-246  search_code 同样直接 self.root.glob(pattern)
  ```
- **根因**：`_safe_path` 只保护单文件读写类工具；glob 类工具误以为「以 root 为基准调用 glob 就不会越界」，但 `Path.glob('../*')` 会向上一级展开。`..` 字符串本身不含任何 `ignores` 词，也不会被过滤。
- **修复建议**：在 `list_files`/`search_code` 内对匹配结果逐个调用 `self._safe_path(path)`；或先校验 pattern：`if ".." in Path(pattern).parts or Path(pattern).is_absolute(): raise SandboxViolation`。若允许工作区内 `sub/../a.py`，则改为对每个命中项 `self._safe_path(path)` 兜底（推荐，最稳）。

---

### N-02 Trace 写入字段 `type` 与可观测性读取字段 `event` 不一致，全部统计/报告静默失效
- **位置**：写入 `nanoagent/tracing.py:46`；读取 `nanoagent/observability.py:44,74,77,131,134`
- **类型**：数据契约断裂（跨模块字段名不一致）
- **现象**：`Tracer.log()` 写入的每条 JSONL 记录里事件类型字段名是 **`"type"`**：
  ```python
  # tracing.py:46
  record = {"ts": ..., "type": event_type}     # ← "type"
  ```
  而 `observability.py` 全部按 **`event`** 读取：`kind = event.get("event")`。结果是：
  - `trace_summary()` 里 `llm_calls/tool_calls/prompt_tokens/completion_tokens` **恒为 0**；
  - `trace_report()` HTML 的「事件」列恒为空；
  - `export_traces_to_otel()` 每个 span 都被命名成 `nanoagent.event`（拿不到真实事件类型）。
  即 **Tracer 真实产出的 trace 文件，可观测性模块读不懂**，功能整体静默失效（不报错）。
- **复现/证据**：脚本 `check_contract_and_schema.py`：
  ```
  Tracer 实际写出的字段名: [['agent','run_id','ts','type'], ['run_id','ts','type','usage'], ...]
  字段 'type' 值: ['run_start','llm_call','tool_call','run_end']
  字段 'event' 存在? : [False, False, False, False]
  trace_summary 结果: {"runs": {"4fbd...": {"llm_calls": 0, "tool_calls": 0,
                       "prompt_tokens": 0, "completion_tokens": 0, "tools": []}}, "total_events": 4}
  ```
  即 `total_events` 正确（4），但所有按事件类型聚合的指标全为 0。
- **根因**：`tracing.py` 与 `observability.py` 由两套命名约定写成，且没有真正打通测试（见「测试盲区」——`test_roadmap.py` 手写 `"event"` 键，从不喂 `Tracer` 产物）。
- **修复建议**：统一字段名。最小改动是在 `tracing.py:46` 改为 `"event": event_type`，并同步 `observability.py` 中所有 `"event"`（本就用 `event`，无需改）；同时 grep 全仓 `"type"`/`"event"` 的使用点，并把 `tests/test_roadmap.py` 的用例改成「用 `Tracer` 真实写文件 → `trace_summary`」以防回归。

---

## P1 中等

### N-03 工具 schema 在 `from __future__ import annotations` 下彻底退化为 string
- **位置**：`nanoagent/tools.py:47-71`（`_annotation_to_schema`）、`tools.py:153`
- **类型**：工具系统 / 数据契约
- **现象**：`make_tool` 直接读取 `inspect.signature(fn).parameters[...].annotation`，但 **当定义模块使用了 `from __future__ import annotations`（PEP 563，极其常见）时，注解是字符串**（如 `'int'`）。`_annotation_to_schema` 对字符串实例不满足 `isinstance(ann, type)`，于是统一返回 `{"type": "string"}`。**nanoagent 自己的 `coding.py`、`browser.py`、`memory.py` 等模块都用了该 future import**，所以 `CodingWorkspace` 全部工具的 `int/float/bool` 参数都被声明成 `string`。
- **复现/证据**：脚本 `check_future_annotations.py`：
  ```
  read_file -> {"properties": {"path": {"type":"string"},
                               "start_line": {"type":"string"},   ← 源码里是 int
                               "end_line":   {"type":"string"}}}
  run_command -> {"timeout": {"type": "string"}}                 ← 源码里是 int
  inspect: start_line annotation='int' type=str
  ```
  连同样板 `e: "list[int]"` 也变成 `{"type":"string"}`（`check_contract_and_schema.py`）。
  后果：模型被告知 `timeout/start_line` 是字符串，很可能传 `"60"`，`subprocess.run(timeout="60")` 抛 `TypeError`（`run_command` 只捕获 `TimeoutExpired`，`TypeError` 落到 `ToolRegistry.execute` 的兜底 except 变成错误串）→ 工具静默失败。
- **根因**：未解析字符串注解。`inspect.signature(fn)` 默认 `eval_str=False`；`typing.get_type_hints(fn)` 才会解析前向引用。
- **修复建议**：在 `make_tool` 里改用 `typing.get_type_hints(fn, include_extras=True)`（并 try/except 回退到 `param.annotation`）来获得已解析的注解；或在 `_annotation_to_schema` 开头对 `isinstance(ann, str)` 做 `eval`/映射处理（不推荐 eval）。同时为 `Enum` 输出 `{"type":"string","enum":[...]}`。

### N-04 同步 `Agent.run` 调用异步工具（如 MCP 工具）会静默返回 coroutine 垃圾串
- **位置**：`nanoagent/tools.py:129-130`（`Tool.invoke`）、`tools.py:206-220`（`ToolRegistry.execute`）；触发方 `nanoagent/mcp.py`（MCP 工具是 async）、`bootstrap.py:129-136`（默认 `LLM()` 同步 + MCP 工具）
- **类型**：工具系统 / 数据错误
- **现象**：`Tool.invoke` 直接 `self.func(**arguments)`。若该工具是协程函数，调用只返回一个 **coroutine 对象**（且从未 await）。`execute` 随后 `json.dumps(result, default=str)` 把它序列化成 `"<coroutine object ...>"` 字符串回填给模型，并抛 `RuntimeWarning: coroutine ... was never awaited`。模型收到的是无意义字符串而非工具结果。`MCPServer._bind` 生成的就是 async 工具，若用户按 `bootstrap` 默认（同步 `LLM()`）调用 `agent.run`，MCP 工具会静默失效。
- **复现/证据**：脚本 `check_async_and_misc.py`：
  ```
  [A] 同步 run 调用 async 工具
      工具结果: '"<coroutine object async_tool at 0x000000002FAA1CC0>"'
      >>> 是否得到 coroutine 垃圾串: True
      RuntimeWarning: coroutine 'async_tool' was never awaited   (agent.py:187)
  ```
- **根因**：`invoke` 未检查 `is_async`；框架对「同步路径遇到协程工具」无检测、无报错。
- **修复建议**：`Tool.invoke` 中检测 `inspect.isawaitable(result)` 时，要么抛明确异常（`RuntimeError("该工具是异步工具，请用 arun/arun_stream")`），要么用 `asyncio.run` 兜底（注意在已有事件循环中会二次报错）。`ToolRegistry.execute` 同理。

### N-05 Workflow 审查判定：末行 `NOT PASS` 会被误判为通过
- **位置**：`nanoagent/multi.py:151-161`（`Workflow._is_pass`）
- **类型**：逻辑错误
- **现象**：`_is_pass` 用**子串包含**判断：`if self.pass_marker in last: return True`。当 `pass_marker="PASS"` 时，末行只要包含 `PASS` 即通过，于是 `NOT PASS`、`COMPASS`、`PASSED?` 等都被判为通过。审查员若用 `NOT PASS` 表达不通过（模型常见措辞），反馈回路的打回会被错误地跳过，工作流直接认为通过并进入汇总。
- **复现/证据**：脚本 `check_skills_task.py`：
  ```
  '结论\nNOT PASS' -> True     ← 应为 False
  'PASS FAIL\nPASS' -> True
  '末尾 FAIL 但整体 PASS\nFAIL' -> False
  ```
- **根因**：仅做 `in` 子串匹配，未做词边界/否定词判断。
- **修复建议**：判定末行标记时使用词边界正则，并先判否定：`if re.search(r'(?<![A-Za-z])FAIL(?![A-Za-z])', last): return False`；`PASS` 同理用 `\bPASS\b` 且排除前置 `NOT`/`NO`。或要求审查员输出结构化 JSON 而非自由文本标记。

### N-06 `SummaryMemory` 的 token 上限形同虚设（keep_recent 保护导致裁剪 no-op）
- **位置**：`nanoagent/memory.py:75-80`（`_over_limit`）、`memory.py:177-184`（`SummaryMemory._trim`）
- **类型**：边界 / 状态
- **现象**：`_over_limit` 只要「条数>max_messages **或** token>max_tokens」就触发 `_trim`；但 `SummaryMemory._trim` 仅在 `len(history) > keep_recent` 时才压缩，否则直接返回。于是当历史条数 ≤ `keep_recent` 而 token 已超 `max_tokens` 时，每次都触发但每次都不裁剪，**token 会永久超过配置上限**，上下文可能撑爆模型窗口。
- **复现/证据**：脚本 `check_agent_memory.py`（`max_messages=100, keep_recent=6, max_tokens=50`）：
  ```
  tokens: 60  配置上限: 50
  历史条数: 7  摘要: '摘要内容'
  >>> 是否仍超 token 上限: True
  ```
- **根因**：`_trim` 只按条数裁剪，忽略了 token 维度；`keep_recent` 下限使 token 触发无法收敛。
- **修复建议**：`SummaryMemory._trim` 在 token 超限时也应继续压缩，至少把最旧的 `history` 元素并入摘要（而非丢弃），直到 `_history_tokens` 回落；或让 `_over_limit`/`_trim` 在压缩后重新评估 token 并强制多轮压缩。

### N-07 插件 `ctx.on()` 注册的事件处理器在 `deactivate()` 后不会被清理（disposer 未入账本）
- **位置**：`nanoagent/plugins.py:160-162`（`PluginContext.on`），对比 `plugins.py:150-158`（`provide` 会入账本）、`plugins.py:164-168`（`effect` 会入账本）
- **类型**：资源泄漏 / 生命周期
- **现象**：`EventBus.on()` 返回的 disposer 被 `PluginContext.on` **直接返回但未 append 到 `_disposers`**。`deactivate()` 按账本 LIFO 回滚，因此**通过 `ctx.on` 订阅的处理器永远不会被取消订阅**。插件卸载后其 handler 仍会随宿主 `emit`（activate/deactivate/error）被调用，导致悬空引用、重复副作用、内存泄漏，与模块文档宣称的「dsh 的 ctx.effect 资源必须 LIFO 回滚」语义不符。
- **复现/证据**：脚本 `check_plugins_dispose.py`：
  ```
  [1] on() 返回 disposer: <function ...>
      账本长度（_disposers）: 0
      emit 后 handler 调用次数: 1
      deactivate 后账本长度: 0
      deactivate 后再 emit，handler 调用次数: 2   ← handler 未被清理
  [2] provide() 的 disposer 被正常追踪，deactivate 后 services 清空
  ```
- **根因**：`on` 忘记了 `self._add_disposer(disposer)`。
- **修复建议**：`def on(self, event, handler): d = self.bus.on(event, handler); self._disposers.append(d); return d`。

### N-08 `EvalRunner` 用例默认共用同一会话，注释与行为不符，用例间记忆互相污染
- **位置**：`nanoagent/evals.py:52`
- **类型**：状态污染 / 数据契约
- **现象**：`EvalCase.session_id` 默认值是常量 `"eval"`，注释却写「每个用例用独立会话，互不污染」。`EvalRunner.run_case` 直接用 `agent.run(case.question, session_id=case.session_id)`。多个 `add_case(...)` 未显式指定 `session_id` 时会共用 `"eval"` 会话，**前一个用例的对话历史会进入后一个用例的 prompt**，评估结果被污染（且顺序敏感、不可复现）。
- **复现/证据**：脚本 `check_async_and_misc.py`：
  ```
  c1.session_id = eval   c2.session_id = eval
  >>> 默认是否共享同一会话: True
  ```
- **根因**：默认值应是每例唯一（如 `field(default_factory=lambda: f"eval-{uuid4().hex[:8]}")`），而不是固定串。
- **修复建议**：把 `EvalCase.session_id` 改为 `field(default_factory=...)` 生成唯一会话；或在 `add_case`/`run_case` 中以 `f"eval-{case.name}"` 覆盖，确保每例隔离。

---

## P2 轻微 / 代码质量

- **N-09 记忆持久化非原子写、损坏后静默清空**：`memory.py:123/230` 用 `write_text` 直接覆盖目标文件，写一半崩溃会留下半截 JSON；`_load`（`memory.py:128-138/235-248`）捕获 `JSONDecodeError` 后 `return`，**静默丢失全部历史且无任何告警**（脚本 `check_struct_output_and_persist.py` 已验证：截断文件 → `history()` 返回 `[]`）。建议：写临时文件 + `os.replace` 原子替换；解析失败时抛错或至少 `logging.warning`。
- **N-10 `JsonFileBackend` 固定单文件下不同 key 互相覆盖**：`checkpoints.py:56-66`，当 `path` 以 `.json` 结尾时 `_path(key)` 恒返回同一文件，`save("task",...)` 与 `save("workflow",...)` 会互相覆盖，`keys()` 只返回文件名 stem（脚本 `check_skills_task.py` 验证：`load('task')` 读到了 workflow 的内容）。Workflow 与 TaskRunner 共用同一个 `checkpoint="*.json"` 时会读到错的状态并触发校验错误。
- **N-11 Enum/Literal 类型未生成约束**：`tools.py:47-71`，`Enum` 参数只得到 `{"type":"string"}`，无 `enum` 列表（脚本验证）；`typing.Literal[...]` 同样退化为 string。模型易传非法值，虽会被兜底 except 变成错误串，但浪费调用。
- **N-12 Anthropic 客户端无重试且 httpx client 从不关闭**：`anthropic_llm.py:270/331` 创建 `httpx.Client/AsyncClient` 后无 `close()`/`aclose()`；`_post`/`achat`（`:279-283,336-342`）对网络错误无重试（对比 `llm.py` 的 `_with_retry`）。每实例化一个客户端就泄漏一个连接池。
- **N-13 `image_part` dict 源的两个小问题**：`media.py:55-79`，传入 dict 且 `detail` 非空但该 dict 没有 `image_url` 键时 `part["image_url"]["detail"]` 抛 `KeyError`；且 `dict(source)` 是浅拷贝，会给调用方原始嵌套 dict 写入 `detail`。
- **N-14 HTTP 服务无鉴权**：`server.py:67-138`，`/chat`、`/chat/stream`、`/sessions`、`/sessions/{id}/clear` 全部无任何认证/授权。默认 `uvicorn.run(host="127.0.0.1")`（未绑 0.0.0.0，尚可），但同机任意进程可读改所有会话。若用户自行改 `--host 0.0.0.0` 将直接裸奔。
- **N-15 Tracer 并发写与 run_id 归属**：并行工具时多线程同时 `Tracer.log` 以追加模式写同一文件（`tracing.py:50-55`），Windows 下存在交错风险，坏行会被 `load_trace` 静默跳过；另外 `Agent.run`（同步）的结构化解析/`structure_retry` 日志发生在 `try/finally` **之后**（`agent.py:298 vs 300-317`），此时 `run_id` 已置 None，这些事件缺少 run_id 归属（`arun` 把结构化逻辑放在 try 内，行为不一致）。
- **N-16 `browser.py` Playwright 同步 API 在工具并行线程中不安全**：`browser.py:36-47` 用 `sync_playwright()` 懒启动，页面对象跨线程复用；而 `Agent` 默认 `parallel_tools=True` 会把工具丢进 `ThreadPoolExecutor`（`agent.py:181-183`），Playwright 同步对象要求同一线程使用，多工具并行会报线程错误。
- **N-17 `spawn_subagent` 与后台进程共用 `_next_pid`**：`coding.py:335-346` 与 `coding.py:407-408` 都自增 `self._next_pid`，进程编号与子代理会话编号混用，编号含义混乱（`subagent-N` 可能与进程 `#N` 冲突观感）。
- **N-18 插件模块常驻 `sys.modules`**：`plugins.py:248-251` 成功加载后不清理 `sys.modules[module_name]`（仅在失败时 pop），重复扫描/热加载会持续累积模块对象。
- **N-19 流式结果缺字段**：`agent.py:401` 的 `run_stream` 与 `agent.py:587-592` 的 `arun_stream` 返回的 `AgentResult` 未填充 `usage` 与 `reasoning`（与 `run/arun` 不一致），依赖用量统计的调用方在流式路径拿到空值。
- **N-20 `manage` 的 remove-skill 只处理目录**：`manage.py:141-147` 要求 `target.is_dir()`，而 `cmd_install_skill`（`:108-119`）对单 md 文件会建目录，但用户手动放入单文件技能时无法用该命令移除。
- **N-21 `start_process` 日志文件句柄泄漏**：`coding.py:338-346` 打开日志文件存入 `_process_files`，只有 `stop_process`（`:386-389`）会关闭；若进程自行退出且从不调用 stop，句柄与文件一直保留。
- **N-22 `Memory` 无法表示工具调用历史（设计局限）**：`agent.py:319-321/398-400` 只把 `user_input` 与最终 `final_content` 写入记忆，`assistant.tool_calls`/`role=tool` 消息从不进入 `Memory`。多轮对话中模型看不到上一轮的工具交互（会重复调用工具或丢失事实）。
- **N-23 VectorStore.load 不做形状/长度校验**：`rag/store.py:93-105` 直接接受文件内容，`metadata` 短于 `texts` 时，带 `where` 的 `search` 在 `self.metadata[i].get(...)`（`:68`）处可能 `IndexError`。

---

## 已验证「不是问题」的怀疑点（避免重复排查）

1. **工具并行结果顺序 / tool_call_id 对应**：`agent._execute_tool_calls` 用 `[future.result() for future in futures]` 按提交顺序取回，`zip(response.tool_calls, results)` 配对，实测 3 个乱序耗时的工具结果与 `c1/c2/c3` 一一对应（`check_agent_memory.py` [A]）。**正确**。
2. **`arun` 是否真并发**：4 个各 sleep 0.3s 的 async 工具经 `arun` 总耗时 0.30s（串行应 ~1.2s）。**真并发**（`check_async_and_misc.py` [B]）。
3. **`Pipeline`/`Team` 是否并发**：按设计为顺序执行（3×0.2s → 0.60s），并非竞态或漏 await。**符合设计**。
4. **`Memory` 滑窗裁剪是否会拆散 tool_call/tool_result**：不会——因为 `Memory` 根本不存储 tool 消息（只存 user/assistant 文本），且 `history()` 返回副本。实测窗口裁剪后仅剩完整的 user/assistant 对（`check_agent_memory.py` [D]）。**该风险不成立**（但反向问题是 N-22）。
5. **同一 agent 连续 `run` 两次是否污染**：第二轮 messages = `[system, user(你好), assistant(第一次), user(再说一次)]`，无残留、确定性一致。**无污染**（`check_agent_memory.py` [B]）。
6. **`_with_retry` 是否重试 4xx**：`_should_retry` 对非 `{429,500,502,503,504}` 的状态码返回 False，4xx 直接抛出；仅对连接/超时类异常按类型名重试。**未误重试 4xx**。
7. **`config` 环境变量 vs `.env` 优先级**：`.env` 用 `os.environ.setdefault` 写入，真实环境变量优先；缺字段时 `settings()` 返回默认值不崩（`check_struct_output_and_persist.py` [E][F]）。**优先级正确**。
8. **RAG numpy 与 faiss 后端一致性**：top-k 排序、分数、`where` 过滤、零向量查询返回 `[]`、维度不一致报 `ValueError` 全部一致（`check_anthropic_and_rag.py` [C][D]）。**一致**。
9. **`split_text` 边界**：空文本/仅换行 → `[]`；无分隔符 1200 中文字 → 3 块；短中文段落按 chunk_size 聚合。**正常**。
10. **Anthropic 消息转换与 SSE 解析**：`to_anthropic_messages` 正确把连续 tool 结果归并为一条 user(tool_result blocks) 且 id 对应；`parse_sse_event`/`finalize_stream` 正确累积 `tool_use` 的 id/name/partial_json（`check_anthropic_and_rag.py` [A][B]）。**正确**。
11. **护栏 fail-closed**：`_coerce` 遇到不支持返回类型抛 `TypeError` 会被 `Guardrail.check` 的 `except` 转成拦截；异步护栏用于同步路径抛清晰 `TypeError`；异步 llm 用于同步 `LLMGuardrail.check` 时因无 `.chat` 被 fail-closed 拦下。**符合安全默认**。
12. **危险命令/注入面**：全仓无 `eval/exec`；`shell=True` 仅 `coding.py` 两处且都在 `_require_approval`（默认 fail-closed）之后；无 `fcntl/SIGKILL/os.fork` 等 Unix-only 调用（Windows 分支用 `taskkill /T`）；`server` 默认绑定 `127.0.0.1`。**未发现额外注入/可移植性问题**。
13. **`Agent.run` 结构化输出重试**：首次非 JSON 会以「无 tools 的追问」让模型重写，成功后 `output` 正确；两次都失败抛 `OutputValidationError`（`check_struct_output_and_persist.py` [A][B]）。**正确**。

---

## 测试盲区

**已存在但属于「伪测试」/规避了真实路径的用例：**
- `tests/test_roadmap.py:70-102` `TraceObservabilityTests`：**手写** `{"run_id":"r1","event":"llm_call",...}` 直接喂 `trace_summary/trace_report`，**从不经过 `Tracer`**。因此它验证的是 observability 自己的字段名，完全掩盖了 N-02（`Tracer` 写 `type`）。这是最典型的「测了 A 却宣称测了 A+B」。
- `tests/test_tools.py`、`tests/test_async_features.py`（schema 断言部分）：测试文件均**未使用 `from __future__ import annotations`**，因此永远走不到 N-03 的字符串注解分支；所有 `int/array/number` 断言都建立在「无 future import」这一非真实条件下。
- `tests/test_coding.py:109-120`：只测 `list_files("**/*")`、`search_code("**/*.py")` 的正常模式，**没有测 `..` 越界**（N-01）。

**完全无测试覆盖的模块/行为：**
- `observability.py` 的真实 Tracer→report→OTel 链路（见上）。
- `server.py` 的鉴权/限流（仅有 200 响应 smoke）；`cli.py`；`manage.py` 的 CLI 子命令。
- `evals.py` 的会话隔离与 judge 失败路径的边界（未验证 session 是否独立）。
- `memory.py` 的持久化损坏恢复与原子性；`SummaryMemory` 的 token 上限收敛。
- `plugins.py` 的 disposer 回滚正确性（`ctx.on` 泄漏无断言）。
- `browser.py` 的多线程并发调用。
- `checkpoints.JsonFileBackend` 单文件多 key 行为。
- 同步 `run` 遇到异步工具（N-04）无任何测试。

**「只验证不崩」型断言：**
- `tests/test_roadmap.py` 的 `test_otel_export_or_graceful`：`except ImportError: pass`，未安装 otel 时该用例实际上什么都没验证。
- `tests/test_roadmap.py` `BrowserTests`：未装 Playwright 时退化为「确认抛 ImportError」，对真实浏览器行为零覆盖。
- `test_roadmap.py::RagRerankTests` 只断言 `len(hits)==2`（不崩），未断言重排后的实际顺序是否符合预期。

---

## 怀疑待验证（未取得确凿证据，不计入 P0/P1）

1. **`Tracer` 并行写文件在 Windows 上的交错概率**：需要构造高并发 + 长 JSON 行才可能复现坏行，本次未稳定复现。
2. **`coding.is_async` 工具与 `parallel_tools` 的线程安全**：若用户注册非线程安全工具（如复用同一 Playwright/sqlite 连接），并发执行可能出错，属使用者责任，未在本仓默认工具中发现确证。
3. **`AnthropicLLM` 流式对非 `data:` 行（如 `event:` 行）的忽略是否会在某些代理下丢事件**：当前只处理 `data:` 前缀行，标准 SSE 兼容，但自定义网关若不发 `data:` 前缀会静默丢内容，未验证具体网关行为。
4. **`plugins._detect_dsh` 与 `_detect_agent_skills` 的适配器探测顺序对同时含多项声明的包的选择**：仅逻辑推演，未构造多格式混合包验证。
