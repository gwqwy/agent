# nanoagent 核心源码文件级索引（分片 01）

> 通读范围：nanoagent 包全部源码 + rag 子包 + pyproject.toml + README.md + LICENSE
> 路径基准：工作区根 `E:/文件/编程文件/agent`（下文均以工作区根为基准的相对路径标注）
> 方法：逐文件真实读取 + Grep 交叉验证 import / 被引用关系
> 索引文件数：33

---

### `nanoagent/nanoagent/__init__.py`
- **用途**：包的公开 API 面（public surface），集中 re-export 全部上层能力，并定义版本号。
- **关键内容**：
  - `__version__ = "0.1.0"`
  - `__all__` 列表（约 70 个符号，见下）
  - 模块顶部 docstring 给出模块分层说明（config/llm/tools/agent/memory/tracing/rag/multi/task/guardrails/media/skills/plugins/mcp/bootstrap/manage/cli/server）
- **对外接口**（完整导出清单，按来源分组）：
  - 来自 `agent`：`Agent`, `AgentResult`, `OutputValidationError`
  - 来自 `anthropic_llm`：`AnthropicLLM`, `AsyncAnthropicLLM`
  - 来自 `bootstrap`：`BootstrapReport`, `bootstrap_agent`, `bootstrap_agent_sync`
  - 来自 `browser`：`BrowserWorkspace`
  - 来自 `checkpoints`：`CheckpointBackend`, `InMemoryBackend`, `JsonFileBackend`, `PostgresBackend`, `SQLiteBackend`
  - 来自 `coding`：`CODING_INSTRUCTIONS`, `CodingWorkspace`, `SandboxViolation`
  - 来自 `evals`：`CaseReport`, `EvalCase`, `EvalReport`, `EvalRunner`
  - 来自 `mcp_server`：`create_mcp_server`, `serve_mcp`
  - 来自 `observability`：`export_traces_to_otel`, `trace_report`, `trace_summary`
  - 来自 `guardrails`：`Guardrail`, `GuardrailResult`, `GuardrailViolation`, `Guardrails`, `keyword_guardrail`, `length_guardrail`, `llm_guardrail`, `make_guardrail`, `pattern_guardrail`
  - 来自 `llm`：`AsyncLLM`, `LLM`, `LLMResponse`, `ToolCall`
  - 来自 `memory`：`Memory`, `SummaryMemory`, `estimate_tokens`
  - 来自 `media`：`build_user_content`, `image_part`, `make_png`
  - 来自 `mcp`：`MCPManager`, `MCPServer`
  - 来自 `multi`：`Pipeline`, `Team`, `Workflow`, `WorkflowResult`, `agent_as_tool`
  - 来自 `plugins`：`EventBus`, `Plugin`, `PluginContext`, `PluginManager`, `register_adapter`
  - 来自 `rag`：`KnowledgeBase`, `VectorStore`, `split_text`
  - 来自 `skills`：`Skill`, `SkillRegistry`, `parse_frontmatter`
  - 来自 `task`：`TaskPlanningError`, `TaskResult`, `TaskRunner`, `TodoItem`
  - 来自 `tools`：`Tool`, `ToolRegistry`, `tool`
  - 来自 `tracing`：`Tracer`
- **依赖**（本项目）：agent、anthropic_llm、bootstrap、browser、checkpoints、coding、evals、guardrails、llm、mcp、mcp_server、media、memory、multi、observability、plugins、rag、skills、task、tools、tracing
- **被依赖**：全项目与 examples/tests（几乎所有使用者都 `from nanoagent import ...`）
- **影响范围**：任何新增/删除/改名公开符号都会波及 examples/01~16、tests/*、README 的用法示例，属于最高影响的公共契约文件。
- **备注**：
  - 顶部模块分层 docstring 与真实导出已经不完全同步：docstring 未提及 `anthropic_llm`、`evals`、`checkpoints`、`coding`、`browser`、`observability` 六个模块。
  - `resolve_checkpoint`（checkpoints.py 的工厂）**未**被导出，属内部符号。
  - `FaissVectorStore`、`create_store` 也未被顶层导出（只在 `nanoagent.rag` 命名空间可见）。

---

### `nanoagent/nanoagent/agent.py`
<!-- 2026-09-28 新增：Agent(tool_gate=callback) 工具审批中间层——每次工具执行前调 tool_gate(name, arguments)，None/True 放行、False/字符串拦截（字符串为拒绝原因，fail-closed 含回调异常），同步/异步执行单口（_execute_one/_aexecute_one）统一生效；测试 ToolGateTests。 -->
- **用途**：框架核心——定义 `Agent` 类与 agent loop（组装消息 → 调 LLM → 执行工具并回填 → 循环至终答），是几乎所有上层模块的编排中心。
- **关键内容**：
  - `OutputValidationError(Exception)`：结构化输出重试后仍失败
  - `extract_json(text)`：从模型回答中容错提取 JSON（裸 JSON / ``` 围栏 / 首尾大括号截取）
  - `@dataclass AgentResult`：`content` / `tool_calls` / `iterations` / `usage` / `output` / `reasoning`
  - `class Agent`：`__init__`（name/instructions/model/llm/tools/memory/max_iterations/tracer/parallel_tools/max_workers/response_model/input_guardrails/output_guardrails）
  - 私有方法：`_guard_input` / `_guard_output` / `_aguard_input` / `_aguard_output`、`_build_messages`、`_tool_call_payload`、`_execute_tool_calls`（线程池并行）、`_execute_one`、`_aexecute_tool_calls`（asyncio.gather）、`_aexecute_one`、`_require_async_llm`、`_structure_prompt`、`_try_parse_output`
  - 四个主入口：`run`（生成器无关 非流式）、`run_stream`（yield delta/tool_call/done 事件）、`arun`、`arun_stream`；`run_stream`/`arun_stream` 均接受 `should_stop` 钩子（2026-09-28：每轮开始与每个 delta 之间检查，命中后关闭底层流、不发 done、不落盘、不跑输出护栏——桌面端停止按钮的框架底座）
  - `enable_skills(registry)`：注册 `use_skill` 工具并把技能索引追加进 system prompt
  - `as_tool(name, description)`：把 agent 包装为可被上级 agent 调用的工具函数
- **对外接口**：`Agent`、`AgentResult`、`OutputValidationError`（`extract_json` 虽非 `__all__` 内，但被 task.py / guardrails.py / evals.py / rag/retriever.py 直接导入）
- **依赖**：`guardrails`、`llm`、`media`、`memory`、`tools`、`tracing`
- **被依赖**：`multi.py`、`task.py`、`bootstrap.py`、`cli.py`、`server.py`、`__init__.py`；tests/test_agent.py、test_async_features.py、test_workflow.py 等
- **影响范围**：multi（Pipeline/Team/Workflow）、task（TaskRunner 驱动 Agent）、bootstrap 的装配、cli/server 入口、examples 全部，tests 中绝大多数用例。
- **备注**：
  - 工具执行异常在 `ToolRegistry.execute/aexecute` 内被吞成字符串回填模型（设计如此，但掩盖真实异常类型）。
  - `run_stream` / `arun_stream` 产出的 `AgentResult` 只填 content/tool_calls/iterations，**没有** usage/output/reasoning，与 `run` 的返回不一致。
  - 结构化输出路径用裸 `except Exception`（带 noqa）做一次重试，重试仍失败抛 `OutputValidationError`。
  - parallel_tools 默认开启，要求工具函数线程安全（代码注释已声明）。
  - 2026-09-28 审计修复（N-05）：输出护栏开启时 `run_stream`/`arun_stream` 的事件先缓冲、护栏通过后再统一 yield——否则 delta 已流出，事后拦截拦不回内容。
  - 2026-09-28 补充修复：结构化输出重试那一次 LLM 调用的 usage 现已累加进 `usage_total`（run/arun/arun_stream 三处）；达到 `max_iterations` 上限且 content 为空串时，写入记忆/结构化解析的是明确标记文案而非空串（四条路径）。

---

### `nanoagent/nanoagent/llm.py`
- **用途**：OpenAI 兼容的 LLM 客户端薄封装（同步 `LLM` + 异步 `AsyncLLM`），全框架统一收敛到 `LLMResponse` 数据结构。
- **关键内容**：
  - 常量 `RETRYABLE_STATUS = {429,500,502,503,504}`
  - `_should_retry(exc)`：按 status_code 或异常类名判断可重试
  - `_with_retry(fn, max_retries, backoff)` / `_aretry`：指数退避重试
  - `parse_tool_arguments(raw)`：容错解析工具 JSON 参数
  - `@dataclass ToolCall(id,name,arguments)`、`@dataclass LLMResponse(content,tool_calls,usage,reasoning)`（含 `has_tool_calls` 属性）
  - `class StreamResult`：可迭代文本增量，结束后 `.response` 为完整响应；`close()`（2026-09-28：提前终止，非生成器对象跳过）
  - `class AsyncStreamResult`：`async for` 版；`aclose()` 同上
  - `_accumulate`：usage 累加
  - `class LLM`：`chat` / `chat_stream` / `_consume_stream` / `embeddings`；`__init__` 参数 model/base_url/api_key/temperature/max_tokens/max_retries/retry_backoff/reasoning_effort/context_window，维护 `total_usage`；`reasoning_effort=="off"` 时显式下发 `extra_body={"enable_thinking": false}`（2026-09-27，Qwen/DashScope/vLLM 默认开思考，留空关不掉）
  - `class AsyncLLM`：`achat` / `achat_stream` / `_consume_stream` / `aembeddings`
- **对外接口**：`LLM`、`AsyncLLM`、`LLMResponse`、`ToolCall`、`StreamResult`、`AsyncStreamResult`、`parse_tool_arguments`、`_with_retry`/`_aretry`（内部/测试直接用）
- **依赖**：`config.settings`
- **被依赖**：`agent.py`、`anthropic_llm.py`、`tools.py`（ToolCall）、`bootstrap.py`、`cli.py`、`server.py`、`rag/retriever.py`、`__init__.py`；tests/mocks.py、test_tools.py、test_ecosystem.py 等
- **影响范围**：几乎所有模块；`LLMResponse`/`ToolCall` 是跨模块数据契约，改动会同时波及 anthropic_llm、tools、agent。
- **备注**：
  - `openai` / `AsyncOpenAI` 延迟导入（纯逻辑单测无需安装 openai）。
  - api_key 缺省回退为 `"missing-api-key"`（硬编码占位，非真实密钥）。
  - 读取了 `reasoning_content`（模型支持时非空），是 DeepSeek 等推理模型的兼容点。

---

### `nanoagent/nanoagent/anthropic_llm.py`
- **用途**：Anthropic Messages 协议适配器，让框架可直连 Claude / DeepSeek `/anthropic` 端点，与 OpenAI 版 LLM 平级、Agent 侧零改动。
- **关键内容**：
  - 常量 `DEFAULT_BASE_URL`、`ANTHROPIC_VERSION="2023-06-01"`、`REQUEST_TIMEOUT=600.0`
  - 纯转换函数：`_convert_image_part`、`_convert_user_content`、`to_anthropic_messages`（抽 system、tool→tool_result 归并、tool_calls→tool_use）、`to_anthropic_tools`（parameters→input_schema）、`from_anthropic_response`
  - SSE 解析：`parse_sse_event(event,state)`、`finalize_stream(state)`
  - `build_payload(...)`、`_build_headers(api_key)`
  - `class AnthropicLLM`：`chat` / `chat_stream` / `_consume_stream` / `_post` / `embeddings`（抛 NotImplementedError），支持注入 `transport`（测试）
  - `class AsyncAnthropicLLM`：`achat` / `achat_stream` / `_aconsume_stream` / `aembeddings`（抛 NotImplementedError）
- **对外接口**：`AnthropicLLM`、`AsyncAnthropicLLM`（及测试使用的纯函数 `to_anthropic_messages`、`build_payload`、`parse_sse_event` 等）
- **依赖**：`config.settings`、`llm`（LLMResponse/StreamResult/ToolCall/parse_tool_arguments，另延迟导入 AsyncStreamResult）；第三方 `httpx`
- **被依赖**：`__init__.py`；tests/test_anthropic_llm.py
- **影响范围**：只影响顶层导出与 Anthropic 场景用例；OpenAI 路径不受影响。
- **备注**：不提供 embeddings（协议无此接口），RAG 必须改用 OpenAI 兼容客户端；`_aconsume_stream` 内部延迟导入 `AsyncStreamResult`。

---

### `nanoagent/nanoagent/tools.py`
- **用途**：工具定义与注册——`@tool` 装饰器从类型注解 + docstring 自动生成 JSON Schema，`ToolRegistry` 集中管理执行。
- **关键内容**：
  - `_TYPE_MAP`、`_PRIMITIVES`、`_TOOL_NAME_PATTERN`
  - `sanitize_tool_name(name)`：净化工具名到 OpenAI 兼容字符集，非法时追加 md5 短哈希
  - `_annotation_to_schema(ann)`：类型注解→JSON Schema（支持 Optional/Union/list/dict）
  - `_parse_docstring(fn)`：解析 Google 风格 docstring 的 Args 段
  - `@dataclass Tool`：`to_openai()`、`is_async`、`invoke()`、`arun()`（协程直接 await，普通函数进线程池）
  - `make_tool(fn,name,description)`：从函数构造 Tool，幂等（已包装则复用 `_tool`）
  - `tool(...)`：装饰器，兼容 `@tool` 与 `@tool(name=...)`
  - `class ToolRegistry`：`register` / `get` / `names` / `schemas` / `execute` / `aexecute` / `merge`
- **对外接口**：`Tool`、`ToolRegistry`、`tool`、`make_tool`、`sanitize_tool_name`
- **依赖**：`llm.ToolCall`
- **被依赖**：`agent.py`、`coding.py`、`browser.py`、`mcp.py`、`skills.py`、`plugins.py`、`rag/retriever.py`、`multi.py`、`__init__.py`；tests/test_tools.py、test_parallel.py 等
- **影响范围**：所有带工具的能力（coding/browser/mcp/skills/plugins/rag/agent）都经此层；schema 生成逻辑改动会牵动全部工具。
- **备注**：
  - `ToolRegistry.execute`/`aexecute` 把任意异常转成字符串回填模型（noqa），不向上抛——这是刻意的“让模型自我纠错”设计，但会隐藏异常类型。
  - `sanitize_tool_name` 对中文名会产出 `tool_<hash>` 形式（注释里的示例表述有笔误）。

---

### `nanoagent/nanoagent/memory.py`
- **用途**：会话记忆——多会话消息存储、条数/token 双维裁剪、JSON 持久化，并提供超窗自动摘要的 `SummaryMemory`。
- **关键内容**：
  - `IMAGE_TOKEN_ESTIMATE = 1024`
  - `estimate_tokens(text)`：优先 tiktoken cl100k_base，缺失时零依赖启发式（ASCII 4 字符/token、CJK 1 字符/token）
  - `_heuristic_estimate(text)`：启发式本体（`ord(ch) > 0x2E7F` 计为全角，全角 1 char/token、其余 4 char/token）。
    从 `estimate_tokens` 中拆出，**取值恒定、不随环境变化**，是测试可以放心断言的那一半
  - 模块级 `_TIKTOKEN_ENCODER`（None=未尝试 / False=不可用 / 编码器）
  - `message_tokens(content)`：文本或多模态数组的 token 估算
  - `class Memory`：`max_messages`/`max_tokens`/`persist_path`；`add` / `_trim`（丢最旧）/ `_over_limit` / `_history_tokens` / `tokens` / `history` / `clear` / `sessions` / `save` / `_load`
  - `class SummaryMemory(Memory)`：`DEFAULT_SUMMARY_PROMPT`、`keep_recent`、`_trim`/`_compress`/`_summarize`、`history`（摘要以 system 注入）、`summary`、覆写 `save`/`_load`
- **对外接口**：`Memory`、`SummaryMemory`、`estimate_tokens`、`message_tokens`
- **依赖**：无本项目导入（`_summarize` 内延迟 `from .llm import LLM`）
- **被依赖**：`agent.py`、`bootstrap.py`、`cli.py`、`server.py`、`__init__.py`；tests/test_memory.py、test_summary_memory.py、test_token_memory.py
- **影响范围**：Agent 的记忆出入、cli/server 的会话持久化、SummaryMemory 摘要链路。
- **备注**：`estimate_tokens` 通过 `global _TIKTOKEN_ENCODER` 引用在函数之后定义的模块级变量（运行时正常，但阅读时略显别扭）；`SummaryMemory.__init__` 依赖父类 `_load` 触发时机，故 `_summaries` 先初始化（注释已声明）。
- **⚠️ 环境相关的坑（2026-09-26 修）**：`estimate_tokens` 的**返回值随环境而变**——装了 tiktoken 走精确计数、没装走启发式，同一串文本可得不同数字（`"abcdefgh"` 精确=1 / 启发式=2；`"你好世界"` 精确=5 / 启发式=4）。
  CI 的 `pip install -e .[server,faiss,mcp,tiktoken]` **装了** tiktoken，开发机默认**没装**，于是旧测试出现「本地全绿、CI 挂 2 条」。
  修法：把启发式拆成 `_heuristic_estimate` 供直接断言，并在测试里用 `forced_heuristic()` 上下文管理器把 `_TIKTOKEN_ENCODER` 置 `False` 来锁定路径。
  **今后任何断言具体 token 数的测试都必须先锁定路径**，不要直接断言裸数字。

---

### `nanoagent/nanoagent/config.py`
- **用途**：配置加载——极简 `.env` 解析 + 环境变量读取，`NANOAGENT_*` 优先、`OPENAI_*` 回退。
- **关键内容**：`load_dotenv(path)`、`_lookup(*names)`、`settings()`
- **对外接口**：`settings`、`load_dotenv`
- **依赖**：无本项目导入（stdlib os/pathlib）
- **被依赖**：`llm.py`、`anthropic_llm.py`、`cli.py`、`server.py`、`rag/retriever.py`；examples/14、15、16 直接 `from nanoagent.config import settings`
- **影响范围**：所有模型客户端与 RAG 的配置来源。
- **备注**：`settings()` 每次调用都会重新 `load_dotenv()`（幂等，用 `setdefault` 不覆盖已有环境变量）；`model` 缺省 `"gpt-4o-mini"`、`embedding_model` 缺省 `"text-embedding-3-small"`（硬编码默认值）。

---

### `nanoagent/nanoagent/tracing.py`
- **用途**：最小可用的 JSONL 事件追踪器，把每次 run、LLM 调用、工具调用写成一行一个 JSON。
- **关键内容**：`class Tracer`：`__init__(path,enabled)`、`start_run(agent_name)`、`end_run(status,**extra)`、`log(event_type,**data)`
- **对外接口**：`Tracer`
- **依赖**：无本项目导入（stdlib）
- **被依赖**：`agent.py`、`bootstrap.py`、`cli.py`、`server.py`、`__init__.py`；tests/test_memory.py
- **影响范围**：所有带 tracer 的 Agent 运行；observability 读取的 trace 文件格式由本文件决定。
- **备注（重要不一致）**：`Tracer.log` 写入的事件键是 `"type"`（`record = {"ts":..., "type": event_type}`），但 `observability.py` 读取的是 `event.get("event")`。二者字段名不一致，导致 `trace_summary`/`trace_report`/`export_traces_to_otel` 永远匹配不到 `llm_call`/`tool_call`，统计恒为 0。此外 `run_start`/`run_end` 与 `log` 写入的字段键名也不被 observability 的 `"event"` 匹配。建议后续统一键名。

---

### `nanoagent/nanoagent/observability.py`
- **用途**：trace JSONL 的可视化——生成单文件 HTML 报告，或导出为 OpenTelemetry spans。
- **关键内容**：`load_trace(path)`、`trace_summary(path)`（按 run 分组统计 LLM/工具调用与 token）、`trace_report(path,out_path)`（零依赖 HTML）、`export_traces_to_otel(path,service_name)`（需 opentelemetry-sdk）
- **对外接口**：`trace_report`、`trace_summary`、`load_trace`、`export_traces_to_otel`
- **依赖**：无本项目导入（stdlib + 可选 opentelemetry）
- **被依赖**：`__init__.py`；tests/test_roadmap.py
- **影响范围**：仅 trace 报告/导出功能，与运行时主链路解耦。
- **备注**：与 `tracing.py` 存在 **`event` vs `type` 字段名不一致**（详见 tracing.py 备注），当前统计结果不正确；`export_traces_to_otel` 在缺少 opentelemetry 时抛 ImportError 并给出安装提示。

---

### `nanoagent/nanoagent/multi.py`
- **用途**：多 agent 编排——提供 `Pipeline`（顺序流水线）、`Team`（agent-as-tool 委托）、`Workflow`（计划→开发↔审查→汇总，含反馈回路与 checkpoint 续跑）。
- **关键内容**：
  - `agent_as_tool(agent,name,description)`：`Agent.as_tool` 的独立函数版
  - `class Pipeline`：`run` / `arun`
  - `class Team`：`__init__`（把 members 注册为 leader 工具）、`run` / `arun`
  - `@dataclass WorkflowResult`：task/plan/code/review/summary/rounds/passed
  - `_load_checkpoint(checkpoint)`：从后端读取工作流状态
  - `class Workflow`：`FAIL_MARKER="FAIL"`、`_is_pass`（末行判定 + 兜底整体判定）、`_persist`、`_state`、`run`/`arun`（含 `_resume` 恢复参数）、`resume`/`aresume`（classmethod）
- **对外接口**：`Pipeline`、`Team`、`Workflow`、`WorkflowResult`、`agent_as_tool`
- **依赖**：`agent.Agent`、`tools.tool`；延迟导入 `checkpoints.resolve_checkpoint`
- **被依赖**：`__init__.py`；tests/test_multi.py、test_workflow.py、test_async_features.py；examples/05、08、09、10
- **影响范围**：多 agent 场景与 Workflow checkpoint 续跑。
- **备注**：`checkpoint_path` 参数保留但实际读写走后端（注释说明）；`_persist` 吞 OSError 不打断工作流；`_is_pass` 用“含 PASS/FAIL 文本”的启发式判定通过，可能与真实语义不完全一致。2026-09-28 审计修复（N-07）：checkpoint 在审查通过后落盘，`run/arun` 的 `_resume` 恢复时若 `passed=True` 直接进汇总（`start_round=max_rounds+1`），不再多跑一轮。

---

### `nanoagent/nanoagent/task.py`
- **用途**：`TaskRunner`——把大目标自主拆解成 JSON 任务清单并逐项连续执行（plan-and-execute），全程可 checkpoint 续跑。
- **关键内容**：
  - 状态常量 `STATUS_PENDING/IN_PROGRESS/DONE/SKIPPED`
  - `TaskPlanningError(Exception)`
  - `@dataclass TodoItem(id,title,detail,status,result)`
  - `@dataclass TaskResult(goal,items,summary)`：`done`/`all_done` 属性、`summary_lines()`
  - 提示词常量 `_PLANNING_PROMPT`、`_EXECUTION_PROMPT`、`_SUMMARY_PROMPT`、`ADD_MARKER="[ADD]"`
  - `_render_checklist(items)`
  - `class TaskRunner`：`__init__(agent,max_tasks,checkpoint,on_progress)`、`_persist`/`_load_state`/`_notify`、`_plan_messages`/`_parse_plan`/`_plan`、`_history_text`、`_harvest_adds`（执行中重规划）、`_run_item`/`_summarize`、`_drive`、`run`/`resume`/`arun`/`aresume`
- **对外接口**：`TaskRunner`、`TaskResult`、`TodoItem`、`TaskPlanningError`
- **依赖**：`agent.Agent`、`agent.extract_json`；延迟导入 `checkpoints.resolve_checkpoint`
- **被依赖**：`__init__.py`；tests/test_task.py、test_ecosystem.py；examples/12、16
- **影响范围**：连续任务执行与 checkpoint 续跑；编程 agent 示例依赖它。
- **备注**：
  - 构造参数名为 **`checkpoint`**（后端对象/路径），而 README 示例写作 `checkpoint_path=`——文档与代码不一致（README 行内示例会 TypeError）。
  - 单项执行异常吞成 skipped 不阻断整体（noqa）；`on_progress` 回调异常同样被吞。
  - 规划解析失败会回填重试一次，仍失败抛 `TaskPlanningError`。

---

### `nanoagent/nanoagent/guardrails.py`
- **用途**：输入/输出安全护栏——规则护栏（关键词/长度/正则）+ LLM 判别护栏，全部 fail-closed，四条执行路径（同步/异步 × 输入/输出）覆盖。
- **关键内容**：
  - `GuardrailViolation(Exception)`（携带 guardrail 名与 reason）
  - `@dataclass GuardrailResult(passed,reason,modified_input)`
  - `_coerce(result,name)`：任意返回值归一化
  - `class Guardrail`：`check`/`acheck`、`_fail_closed`、`is_async` 分发
  - `make_guardrail(source)`
  - 内置工厂：`keyword_guardrail`、`length_guardrail`、`pattern_guardrail`
  - `class LLMGuardrail(Guardrail)`：`PROMPT`、`_parse`（延迟导入 `agent.extract_json`）、`_check_sync`/`_check_async`、覆写 `check`/`acheck`；工厂 `llm_guardrail`
  - `class Guardrails`：`input`/`output` 两组、`check_input`/`acheck_input`/`check_output`/`acheck_output`/`is_empty`
- **对外接口**：`Guardrail`、`GuardrailResult`、`GuardrailViolation`、`Guardrails`、`make_guardrail`、`keyword_guardrail`、`length_guardrail`、`pattern_guardrail`、`llm_guardrail`
- **依赖**：无顶层本项目导入；`LLMGuardrail._parse` 延迟 `from .agent import extract_json`（避免与 agent.py 循环依赖）
- **被依赖**：`agent.py`；`__init__.py`；tests/test_guardrails.py；examples/13
- **影响范围**：Agent 的输入/输出过滤；失败时抛 `GuardrailViolation` 且不写记忆。
- **备注**：模块导入了 `json` 但未实际使用（无用导入）；护栏自身异常一律按拦截处理（安全默认，但会掩盖护栏实现 bug）。

---

### `nanoagent/nanoagent/evals.py`
- **用途**：评估体系——`EvalRunner` 跑用例集，支持 contains / regex / LLM-as-judge 三种判分，报告可存档做回归对比。
- **关键内容**：
  - `class EvalResult(score,passed,reason)`：`to_dict`
  - `@dataclass EvalCase(name,question,expect_contains,expect_regex,judge_rubric,judge_threshold,tools,session_id)`
  - `@dataclass CaseReport(...)`：`to_dict`
  - `@dataclass EvalReport(cases)`：`pass_rate`/`total_elapsed_ms`/`summary_text`/`save`
  - `class EvalRunner`：`JUDGE_PROMPT`、`add_case`、`_score_contains`/`_score_regex`/`_score_judge`、`score_case`（多判分器取最低分）、`run_case`（临时注册用例专属工具）、`run`
- **对外接口**：`EvalRunner`、`EvalReport`、`EvalCase`、`CaseReport`
- **依赖**：延迟导入 `tools.ToolRegistry`（run_case）、`agent.extract_json`（_score_judge）
- **被依赖**：`__init__.py`；tests/test_ecosystem.py
- **影响范围**：仅评估链路，与运行时解耦。
- **备注**：`run_case` 会临时替换 `agent.tools` 再还原（finally 保证）；单个用例异常计 0 分不中断整批（noqa）；judge 依赖外部注入 `judge_llm`，缺失时抛 ValueError。

---

### `nanoagent/nanoagent/checkpoints.py`
- **用途**：可插拔 checkpoint 后端——把 Workflow/TaskRunner 的持久化抽象成协议，内置 JSON 文件 / SQLite / 内存 / Postgres 四种实现。
- **关键内容**：
  - `class CheckpointBackend(Protocol)`：`save`/`load`/`delete`/`keys`
  - `class InMemoryBackend`：字典 + 深拷贝
  - `class JsonFileBackend`：目录（每 key 一个 json）或固定 .json 文件
  - `class SQLiteBackend`：stdlib sqlite3，WAL，每次操作独立连接
  - `class PostgresBackend`：可选 psycopg，表结构同 SQLite
  - `resolve_checkpoint(spec)`：字符串/路径 → SQLite（.db/.sqlite）或 JSON 后端，否则原样返回
- **对外接口**：`CheckpointBackend`、`InMemoryBackend`、`JsonFileBackend`、`SQLiteBackend`、`PostgresBackend`、`resolve_checkpoint`（后两者中的 Postgres 进 `__init__`，`resolve_checkpoint` 为内部）
- **依赖**：无本项目导入（stdlib sqlite3 + 可选 psycopg）
- **被依赖**：`multi.py`（延迟）、`task.py`（延迟）、`__init__.py`；tests/test_ecosystem.py
- **影响范围**：Workflow 与 TaskRunner 的续跑能力。
- **备注**：新增后端只需实现同一协议；`resolve_checkpoint` 决定“路径→后端”的自动判别，影响 TaskRunner/Workflow 的传参语义。

---

### `nanoagent/nanoagent/coding.py`
- **用途**：编程工具集 `CodingWorkspace`——把 nanoagent 变成编程 agent（文件读写/编辑/搜索/shell/git/后台进程/子 agent），带路径监狱、确认门、输出限幅三层安全。
- **关键内容**：
  - 常量 `DEFAULT_IGNORES`、`MAX_OUTPUT_CHARS=4000`、`MAX_FILE_CHARS=20000`
  - `SandboxViolation(Exception)`
  - `class CodingWorkspace`：`__init__(root,confirm,auto_approve,ignores,allowed_tools,agent_factory)`
  - 私有：`_safe_path`（路径监狱）、`_display`、`_require_approval`（确认门）、`_truncate`
  - 文件工具：`read_file`/`write_file`/`edit_file`/`file_diff`/`delete_file`/`list_files`/`search_code`
  - Shell：`run_command`
  - Git：`_git`/`git_status`/`git_diff`/`git_commit`
  - 后台进程：`start_process`/`read_process`/`stop_process`
  - `spawn_subagent`（依赖 agent_factory）
  - `as_tools()`（按 `allowed_tools` 白名单产出 Tool 列表）
  - 常量 `CODING_INSTRUCTIONS`
- **对外接口**：`CodingWorkspace`、`CODING_INSTRUCTIONS`、`SandboxViolation`
- **依赖**：`tools.Tool`、`tools.make_tool`
- **被依赖**：`__init__.py`；tests/test_coding.py；examples/16
- **影响范围**：编程 agent 场景与 TaskRunner 配合的文件操作。
- **备注**：`run_command`/`delete_file`/`git_commit`/`start_process`/`stop_process` 默认拒绝（fail-closed），需 `auto_approve=True` 或 `confirm` 回调；`run_command` 用 `shell=True`（有命令注入面，但受确认门保护）。模块导入了 `shutil`、`time` 但未见使用（无用导入）。

---

### `nanoagent/nanoagent/media.py`
- **用途**：多模态消息构造——把图片源（URL/本地文件/bytes/dict）转成 OpenAI 兼容的 `image_url` content parts。
- **关键内容**：
  - `_MAGIC_SIGNATURES`、`_SUFFIX_MIME`、类型别名 `ImageSource`
  - `_sniff_mime(data)`：按文件魔数识别 MIME
  - `image_part(source, detail)`：单图源 → content part
  - `build_user_content(text, images, detail)`：无图返回字符串，有图返回数组
  - `make_png(width,height,rgb,path)`：零依赖生成纯色 PNG（测试/演示）
- **对外接口**：`image_part`、`build_user_content`、`make_png`
- **依赖**：无本项目导入（stdlib base64/struct/zlib/pathlib）
- **被依赖**：`agent.py`、`cli.py`；`browser.py` 延迟导入 `image_part`；`__init__.py`；tests/test_media.py；examples/14
- **影响范围**：多模态输入链路与 cli 的 `/image` 命令。
- **备注**：记忆只持久化文本，图片是单次请求临时输入；多数服务商仅允许图片出现在 user 消息中（docstring 已声明）。

---

### `nanoagent/nanoagent/browser.py`
- **用途**：浏览器自动化工具 `BrowserWorkspace`（computer use 的浏览器子集），基于可选依赖 Playwright，懒启动单页面会话。
- **关键内容**：常量 `MAX_TEXT_CHARS=6000`；`class BrowserWorkspace`：`_ensure_page`、`navigate`/`read_text`/`click`/`fill`/`screenshot`/`get_url`、`as_tools()`（支持 allowed_tools 白名单）、`close()`
- **对外接口**：`BrowserWorkspace`
- **依赖**：`tools.Tool`、`tools.make_tool`；`screenshot` 内延迟 `from .media import image_part`
- **被依赖**：`__init__.py`；tests/test_roadmap.py
- **影响范围**：浏览器工具场景。
- **备注**：需 `pip install nanoagent[browser]` + `playwright install chromium`；`_ensure_page` 懒加载，`close()` 释放资源；`screenshot` 只返回 data URL 前 60 字符（非完整图片）。

---

### `nanoagent/nanoagent/mcp.py`
- **用途**：MCP 客户端——通过官方 SDK 接入 stdio/SSE/Streamable HTTP 三种传输的 MCP 服务器，并把 MCP 工具适配成 nanoagent `Tool`。
- **关键内容**：
  - `mcp_schema_to_nanoagent(mcp_tool)`：兼容 input_schema(2.x)/inputSchema(1.x)；**工具名经 `sanitize_tool_name` 净化**（2026-09-28：`server.tool` 带点号名会被 OpenAI 兼容服务 400），原始名经 `list_tools` → `_bind(raw_name)` 用于转发调用
  - `_unbound_stub`：占位协程（提示必须经 MCPServer 转发）
  - `class MCPServer`：`_finish_connect`、`connect_stdio`/`connect_sse`/`connect_http`（classmethod）、`disconnect`、`list_tools`/`tools`、`call`、`_bind`、`_ensure_connected`
  - `class MCPManager`：`_load`（损坏 JSON 抛 ValueError，不静默当空配置）/`_save`（tmp + os.replace 原子写）、`add`/`remove`/`list`、`connect_all`/`disconnect_all`（mcpServers 通用配置格式）
- **对外接口**：`MCPServer`、`MCPManager`、`mcp_schema_to_nanoagent`
- **依赖**：`tools.Tool`；可选第三方 `mcp`
- **被依赖**：`bootstrap.py`、`manage.py`、`__init__.py`；tests/test_bootstrap.py、test_roadmap.py
- **影响范围**：MCP 工具接入与 `bootstrap` 的 MCP 装配。
- **备注**：MCP 工具是异步工具，只能用于 `arun/arun_stream`；`MCPServer.__init__` 在未安装 mcp 时抛 ImportError；bin 与 1.x/2.x 字段兼容（is_error/isError、input_schema/inputSchema）。2026-09-28：工具名净化后同名冲突由 sanitize 的短哈希后缀兜底；`_load` 损坏时抛 ValueError（bootstrap 会兜底，manage CLI 需自行捕获）。

---

### `nanoagent/nanoagent/mcp_server.py`
- **用途**：反向集成——把 nanoagent Agent 暴露为 MCP 服务器（stdio），供 Claude Code / dsh 等宿主调用。
- **关键内容**：`create_mcp_server(agent,name,session_prefix)`（暴露 `chat`、`list_agent_tools` 两个 MCP 工具）、`serve_mcp(agent,name)`（阻塞运行）
- **对外接口**：`create_mcp_server`、`serve_mcp`
- **依赖**：无本项目导入（延迟导入 `mcp.server.mcpserver.MCPServer`）
- **被依赖**：`__init__.py`；tests/test_roadmap.py；examples/mcp_entry.py
- **影响范围**：对外暴露 Agent 为 MCP 服务的场景。
- **备注**：依赖 mcp SDK；`serve_mcp` 阻塞运行（stdio 子进程宿主模式）。

---

### `nanoagent/nanoagent/skills.py`
- **用途**：Agent Skills——SKILL.md 渐进式披露（索引注入 system prompt，`use_skill` 按需加载全文）。
- **关键内容**：
  - 常量 `SKILL_FILE="SKILL.md"`、`_FRONTMATTER_LINE`
  - `parse_frontmatter(text)`：无 YAML 依赖的 `key: value` frontmatter 解析
  - `@dataclass Skill(name,description,body,path)`：`summary()`
  - `class SkillRegistry`：`add`/`add_file`/`add_dir`、`names`/`get`/`__len__`/`__contains__`、`list_summary`（第一层）、`load`（第二层）、`use_skill_tool()`（缓存，幂等）
- **对外接口**：`Skill`、`SkillRegistry`、`parse_frontmatter`
- **依赖**：`tools.tool`
- **被依赖**：`plugins.py`、`bootstrap.py`、`__init__.py`；tests/test_skills.py、test_ecosystem.py
- **影响范围**：技能体系与插件技能装配；`Agent.enable_skills` 依赖 `list_summary`/`use_skill_tool`。
- **备注**：`add_dir` 对不存在的目录静默返回空列表；`load` 未命中抛 KeyError（`use_skill` 工具内部捕获并返回可用清单）。

---

### `nanoagent/nanoagent/plugins.py`
- **用途**：插件系统——Python 版 mini-Cordis 内核（ctx/effect/disposer/fiber 状态机）+ 多格式适配器（nanoagent/dsh/mcp-only/agent-skills，可扩展）。
- **关键内容**：
  - 状态常量 `PENDING/ACTIVE/FAILED/DISPOSED`、`SKIPPED_TS`、`SKILL_MD`
  - `UnknownFormat(Exception)`
  - `class EventBus`：`on`（返回 disposer）/`emit`（单个 handler 出错不影响其余）
  - 门面 `_ToolsFacade`/`_SkillsFacade`/`_McpFacade`
  - `class PluginContext`：`provide`/`on`/`effect`/`_add_disposer`/`deactivate`（LIFO 回滚，幂等）；`tools`/`skills`/`mcp` 便捷入口
  - `@dataclass Plugin`（name/path/format/state/manifest/ctx/provided/skipped/error；`summary()`）
  - 适配器注册：`register_adapter(name,detector,loader)`、`_ADAPTERS`
  - 内置适配器：`_detect_nanoagent/_load_nanoagent`、`_detect_dsh/_load_dsh`、`_detect_mcp_only/_load_mcp_only`、`_detect_agent_skills/_load_agent_skills`；辅助 `_read_json`/`_looks_like_dsh`
  - `class PluginManager`：`detect_format`、`scan`、`activate`/`activate_all`/`deactivate`/`deactivate_all`、`collect_tools`/`collect_mcp_servers`、`list`
- **对外接口**：`Plugin`、`PluginContext`、`PluginManager`、`EventBus`、`register_adapter`、`UnknownFormat`、状态常量
- **依赖**：`skills.SkillRegistry`、`tools.Tool`；`_ToolsFacade.register` 内延迟 `from .tools import make_tool`
- **被依赖**：`bootstrap.py`、`manage.py`、`__init__.py`；tests/test_plugins.py
- **影响范围**：插件装配、bootstrap 报告、manage CLI 的 install/list。
- **备注**：`_load_dsh` 只消费静态声明（SKILL.md/mcpServers/元信息），TS/JS 代码体记入 `skipped`（Python 运行时无法执行）；`_load_nanoagent` 用 `importlib` 动态加载 `plugin.py` 的 `register(ctx)` 或 `TOOLS`；多数 except 为 noqa 吞异常保证单插件失败不拖垮整体。

---

### `nanoagent/nanoagent/bootstrap.py`
- **用途**：一键装配——扫描 `.nanoagent/` 的 plugins/skills/mcp.json，组装成开箱即用的 Agent 并返回装配报告。
- **关键内容**：
  - `@dataclass BootstrapReport`：plugins/skills/mcp_servers/tools/failed/skipped/config_dir/`_mcp_connections`；`aclose()`（断开 MCP）、`summary()`
  - `async bootstrap_agent(config_dir,*,llm,instructions,memory,tracer,**agent_kwargs) -> (Agent,BootstrapReport)`
  - `bootstrap_agent_sync(...)`：内部 `asyncio.run` 的同步包装
- **对外接口**：`bootstrap_agent`、`bootstrap_agent_sync`、`BootstrapReport`
- **依赖**：`agent.Agent`、`llm.LLM`、`mcp.MCPManager`/`MCPServer`、`memory.Memory`、`plugins.PluginManager`/`ACTIVE`、`skills.SkillRegistry`、`tracing.Tracer`
- **被依赖**：`__init__.py`；tests/test_bootstrap.py；examples/11
- **影响范围**：生态装配入口；插件/MCP/技能目录约定的唯一编排点。
- **备注**：插件激活失败、单个 MCP 连接失败、mcp.json 损坏均记录进 report.failed 而不中断；`BootstrapReport.aclose` 需在收尾时显式 await 断开 MCP。

---

### `nanoagent/nanoagent/manage.py`
- **用途**：插件/技能/MCP 命令行管理（install/remove/list），对齐 dsh plugin 子命令；`python -m nanoagent.manage`。
- **关键内容**：
  - 常量 `DEFAULT_CONFIG=".nanoagent"`
  - 辅助：`_is_url`、`_lookup_registry`、`_resolve_source`、`_unique_dir`、`_fetch`（本地复制或 git clone）
  - 命令处理：`cmd_install_plugin`/`cmd_install_skill`/`cmd_install_mcp`、`cmd_remove_plugin`/`cmd_remove_skill`/`cmd_remove_mcp`、`cmd_list`
  - `build_parser()`、`main(argv)`
- **对外接口**：`main`、`build_parser`（含各 cmd_* 函数）
- **依赖**：`mcp.MCPManager`、`plugins.PluginManager`
- **被依赖**：无包内引用（独立 CLI 入口）；tests 未见直接导入
- **影响范围**：生态安装管理；改动影响 `bootstrap` 扫描到的目录结构约定。
- **备注**：`_lookup_registry` 用标准库 urllib 拉取 JSON 注册表索引；git 来源用浅克隆（--depth 1）；失败即 SystemExit。

---

### `nanoagent/nanoagent/cli.py`
- **用途**：命令行 REPL 聊天入口（`python -m nanoagent.cli`），支持流式输出与 `/image` 多模态输入。
- **关键内容**：
  - 常量 `SESSIONS_FILE`、`TRACE_FILE`、`WELCOME`
  - `parse_args(argv)`、`build_agent(args)`、`repl(agent,session_id)`、`_version()`、`main()`
  - 内置命令：`/new` `/tools` `/sessions` `/save` `/image` `/exit`
- **对外接口**：`main`、`build_agent`、`parse_args`、`repl`
- **依赖**：`agent.Agent`、`config.load_dotenv`/`settings`、`llm.LLM`、`media.image_part`、`memory.Memory`、`tracing.Tracer`；`_version` 延迟 `from . import __version__`
- **被依赖**：无包内引用（独立入口）；tests/test_entry.py 导入 `parse_args`
- **影响范围**：交互式聊天体验；`Parse_args` 单测。
- **备注**：REPL 捕获 KeyboardInterrupt/通用 Exception 不退出；缺 API Key 时 SystemExit(1)；“调用工具”提示含一个扳手符号（源码原文）。

---

### `nanoagent/nanoagent/server.py`
- **用途**：FastAPI 异步 HTTP 服务入口（`/chat`、`/chat/stream`(SSE)、`/sessions`、`/health`），`python -m nanoagent.server`。
- **关键内容**：
  - `SESSIONS_FILE`
  - `class ChatRequest(BaseModel)`（session_id/message）、`class ChatResponse(BaseModel)`（reply/tool_calls/iterations/output）
  - `build_agent()`、`create_app(agent=None)`（含 `/chat`、`/chat/stream`、`/sessions/{id}/clear`、`/sessions`、`/health`）、`_version()`、`__getattr__`（PEP 562 惰性 `app`）
- **对外接口**：`create_app`、`app`（惰性属性）、`build_agent`、`ChatRequest`、`ChatResponse`
- **依赖**：`agent.Agent`、`config.load_dotenv`/`settings`、`llm.AsyncLLM`/`LLM`、`memory.Memory`、`tracing.Tracer`；延迟 `.__version__` 和 fastapi/uvicorn
- **被依赖**：无包内引用（独立入口）；tests/test_entry.py、test_ecosystem.py 导入 `create_app`；examples/06_http_server.py 导入 `app`
- **影响范围**：HTTP 服务能力；SSE 事件格式与 `Agent.arun_stream` 的事件结构强耦合。
- **备注**：`app` 为 PEP 562 惰性属性（2026-09-28 审计修复 N-10d）：import 本模块不再创建 Agent/LLM 客户端/trace 文件，首次 `getattr`（如 `uvicorn nanoagent.server:app`）才构建一次并缓存到模块 globals；导入本身不要求安装 fastapi（`create_app` 内部才延迟导入）。同步 agent 会自动丢线程池避免阻塞事件循环；上游错误统一转 HTTP 502。

---

### `nanoagent/nanoagent/rag/__init__.py`
- **用途**：RAG 子包入口，re-export 分块/向量库/检索能力。
- **关键内容**：`__all__ = ["KnowledgeBase","VectorStore","FaissVectorStore","create_store","split_text"]`
- **对外接口**：`split_text`、`FaissVectorStore`、`KnowledgeBase`、`VectorStore`、`create_store`
- **依赖**：`chunking`、`faiss_store`、`retriever`、`store`
- **被依赖**：`nanoagent/__init__.py`（导出 KnowledgeBase/VectorStore/split_text）；tests/test_faiss.py、test_rag.py；examples/04
- **影响范围**：RAG 公开 API。
- **备注**：顶层 `nanoagent` 只导出了 `KnowledgeBase`/`VectorStore`/`split_text`，未导出 `FaissVectorStore`/`create_store`。

---

### `nanoagent/nanoagent/rag/store.py`
- **用途**：本地向量库 numpy 后端——暴力余弦相似度检索 + JSON 持久化，并提供后端工厂 `create_store`。
- **关键内容**：`class VectorStore`：`add`/`search`（支持 metadata where 过滤）/`save`/`load`、`__len__`；`create_store(backend)`（"numpy"/"faiss"，faiss 未装时抛 ImportError）
- **对外接口**：`VectorStore`、`create_store`
- **依赖**：无本项目导入（numpy）
- **被依赖**：`rag/__init__.py`、`rag/retriever.py`（`VectorStore`/`create_store`）
- **影响范围**：RAG 默认后端；两个后端接口需保持一致。
- **备注**：向量维度不一致会抛 ValueError；JSON 持久化适合中小规模（几千条以内）。

---

### `nanoagent/nanoagent/rag/faiss_store.py`
- **用途**：faiss 向量检索后端，与 numpy 版 `VectorStore` 完全同接口可互换（IndexFlatIP + L2 归一化 = 余弦）。
- **关键内容**：`class FaissVectorStore`：`_ensure_index`、`_normalize`、`add`、`search`（where 过滤时全量召回再筛）、`save`（二进制索引 + `<path>.meta.json`）、`load`、`__len__`
- **对外接口**：`FaissVectorStore`
- **依赖**：无本项目导入（numpy；`faiss` 在 `__init__` 内导入）
- **被依赖**：`rag/__init__.py`；`rag/store.create_store`（延迟）；tests/test_faiss.py
- **影响范围**：大数据量 RAG 场景。
- **备注**：需 `pip install nanoagent[faiss]`；numpy 与 faiss 持久化格式互不兼容，切换后端需重新入库。

---

### `nanoagent/nanoagent/rag/retriever.py`
<!-- 2026-09-28 新增：向量缓存——chunk sha256 → 向量，命中缓存零次 /embeddings；persist 时缓存落盘 <persist>.veccache.json（上限 8000 条，超限整体重建），embedding_cache=False 可关；测试 EmbeddingCacheTests。 -->
- **用途**：知识库 `KnowledgeBase`——embedding 入库 + 检索 + 可选 LLM 重排序，并一键变成 Agent 工具。
- **关键内容**：
  - `class KnowledgeBase`：`EMBED_BATCH=64`（/embeddings 分批上限，2026-09-28 新增）、`__init__(llm,embedding_model,persist_path,backend)`、`_embed`、`add_text`/`add_file`、`query`（k/where/rerank）、`RERANK_PROMPT`、`_llm_rerank`、`_autosave`/`save`、`as_tool(k,name,description)`
- **对外接口**：`KnowledgeBase`
- **依赖**：`..config.settings`、`..llm.LLM`、`..tools.tool`、`.chunking.split_text`、`.store.VectorStore`/`create_store`；`_llm_rerank` 延迟 `from ..agent import extract_json`
- **被依赖**：`rag/__init__.py`、`nanoagent/__init__.py`；tests/test_rag.py、test_roadmap.py、test_faiss.py；examples/04
- **影响范围**：RAG 查询与工具化；依赖 OpenAI 兼容 `/embeddings`。
- **备注**：`query(rerank=True)` 会多一次 LLM 调用；重排解析失败时保守降级为向量序；`persist_path` 与后端绑定。2026-09-28：`_embed` 按 `EMBED_BATCH`（64）分批调用 /embeddings，大文件入库不再受单请求批量/token 上限限制。

---

### `nanoagent/nanoagent/rag/chunking.py`
- **用途**：文本分块——为 RAG 入库做准备，段落聚合 + 超长段落带 overlap 硬切。
- **关键内容**：`split_text(text, chunk_size=500, overlap=80)`；参数校验（chunk_size>0、0<=overlap<chunk_size）
- **对外接口**：`split_text`
- **依赖**：无（纯 stdlib）
- **被依赖**：`rag/__init__.py`、`rag/retriever.py`；tests/test_rag.py（含直接导入）
- **影响范围**：RAG 入库分块质量与召回。
- **备注**：最短依赖文件之一，可单独测试。

---

### `nanoagent/pyproject.toml`
- **用途**：项目打包与依赖声明，定义核心依赖与可选依赖组。
- **关键内容**：
  - `[project]`：name=nanoagent、version=0.1.0、**`license = {text = "MIT"}`**、requires-python>=3.10
  - 核心依赖：openai>=1.30、httpx>=0.27、numpy>=1.26、pydantic>=2.0
  - 可选依赖组：`server`(fastapi/uvicorn)、`faiss`、`mcp`、`tiktoken`、`otel`、`postgres`、`browser`
  - `[build-system]` setuptools；`[tool.setuptools.packages.find] include=["nanoagent*"]`
- **对外接口**：构建/安装契约
- **依赖**：无
- **被依赖**：安装与 CI（.github/workflows）
- **影响范围**：任何新增可选依赖/模块必须同步更新，否则用户安装后 ImportError。
- **备注**：README 的“可选依赖组”与本节一一对应；`anthropic_llm` 依赖的 httpx 已在核心依赖中（注释说明 openai 自带 httpx）。`license` 字段于 2026-09-26 补入，与仓库根的 `LICENSE` 文件配套（此前只有 `sahou-harness` 一侧声明了 license，nanoagent 缺失）。

---

### `nanoagent/README.md`
- **用途**：项目设计意图、模块定位与用法总览，用于核对该包的分层与对外承诺。
- **关键内容**：功能一览表（逐模块对标 Agno/OpenAI Agents SDK/LangGraph 等）、快速开始、30 秒上手、核心用法（多 agent/RAG/摘要记忆/token 限窗/Anthropic/并行工具/Workflow/异步/MCP/结构化输出/checkpoint/TaskRunner/多模态/护栏/trace/插件生态/编程 agent/evals/checkpoint 后端/限流重试/远程 MCP/流式 HTTP）、目录结构、Roadmap、可选依赖组、已知限制、**许可证（MIT，链接到 `LICENSE`）**。
- **对外接口**：文档级契约
- **依赖**：无
- **被依赖**：无代码依赖（但 `pyproject.toml` 的 `readme = "README.md"` 引用它）
- **影响范围**：用户认知与示例一致性。
- **备注（与代码不一致处）**：
  1. 功能表中 `rag/` 行与 `tracing.py` 行排版串在一起（表格行缺失换行）。
  2. TaskRunner 示例使用 `checkpoint_path="task.json"`，但代码构造参数实为 `checkpoint`（README 后文又用了 `checkpoint=`），存在文档漂移。
  3. “已知限制”称 TaskRunner“执行中不重规划”，但 `task.py` 实际支持 `[ADD]` 执行中重规划（`_harvest_adds`），文档滞后。
  4. 顶部模块分层 docstring（见 `__init__.py`）未覆盖全部模块，README 功能表则更完整。

---

### `nanoagent/LICENSE`
- **用途**：仓库的开源许可证正文，**MIT License**，版权人 `Copyright (c) 2026 gwqwy`。
- **关键内容**：MIT 标准全文（授予使用/复制/修改/合并/发布/再许可/销售权；保留版权声明；软件按“原样”提供、不含任何担保）。
- **对外接口**：法律层面的使用许可；GitHub 会据此在仓库页右上角显示 "MIT license" 徽标。
- **依赖**：无。
- **被依赖**：`pyproject.toml` 的 `license = {text = "MIT"}`（声明侧）、`README.md` 的「许可证」段落（引用侧）。两处都只写协议名，不引用文件内容。
- **影响范围**：**改动措辞等于改法律条款**；若日后改为 Apache-2.0 / GPL 等，必须同时改本文件、`pyproject.toml` 的 `license` 字段与 README 段落三处。
- **备注**：2026-09-26 添加。与 `sahou-harness/LICENSE` **内容逐字节相同**（同为 MIT / 同一版权人），但**属独立副本，无自动同步机制**，改一处需手动同步另一处。版权人用的是 GitHub 用户名 `gwqwy`（提交者显示名为 `2339047121`）——若希望改为真实姓名需三处同改。

---

## 依赖关系总览

### 分层结构（由底向上）

- **L0 零内部依赖（叶节点）**：
  - `config.py`、`tracing.py`、`checkpoints.py`、`chunking.py`、`store.py`、`faiss_store.py`、`media.py`、`observability.py`、`mcp_server.py`
  - 这些文件只依赖 stdlib 或第三方，不 import 本项目其他模块（个别仅在方法内做延迟导入，如 `mcp_server` 延迟导入 mcp SDK）。
- **L1 基础能力**：
  - `llm.py` → `config`
  - `anthropic_llm.py` → `config`, `llm`
  - `tools.py` → `llm`（仅 ToolCall）
  - `memory.py` →（无顶层依赖；`_summarize` 延迟 `llm`）
  - `guardrails.py` →（无顶层依赖；`LLMGuardrail._parse` 延迟 `agent.extract_json`，用于打破循环）
- **L2 核心编排**：
  - `agent.py` → `guardrails`, `llm`, `media`, `memory`, `tools`, `tracing`
- **L3 能力扩展（依赖 L1/L2 + 工具层）**：
  - `coding.py` / `browser.py` / `mcp.py` → `tools`
  - `skills.py` → `tools`
  - `rag/retriever.py` → `config`, `llm`, `tools`, `chunking`, `store`（+ 延迟 `agent.extract_json`）
- **L4 多 agent / 任务 / 评估 / 持久化编排**：
  - `multi.py` → `agent`, `tools`（+ 延迟 `checkpoints`）
  - `task.py` → `agent`（+ 延迟 `checkpoints`）
  - `evals.py` →（延迟 `tools`, `agent`）
- **L5 生态装配**：
  - `plugins.py` → `skills`, `tools`
  - `bootstrap.py` → `agent`, `llm`, `mcp`, `memory`, `plugins`, `skills`, `tracing`
- **L6 入口/工具链（无人被包内 import）**：
  - `cli.py` → `agent`, `config`, `llm`, `media`, `memory`, `tracing`
  - `server.py` → `agent`, `config`, `llm`, `memory`, `tracing`
  - `manage.py` → `mcp`, `plugins`
  - `observability.py`（只读 trace）
- **聚合层**：`__init__.py` → 以上全部（公开 API 面）

### 关键耦合关系（按重要性）

1. **`agent.py` → `llm.py` / `tools.py` / `memory.py` / `tracing.py` / `guardrails.py` / `media.py`**：agent loop 的核心六依赖，任一数据结构（尤其 `LLMResponse`/`ToolCall`）变动都会直接改变 loop 行为。
2. **`multi.py` / `task.py` / `bootstrap.py` / `cli.py` / `server.py` → `agent.py`**：Agent 是上层编排/入口的唯一驱动对象，其公开方法（run/arun/run_stream/arun_stream/as_tool/enable_skills）被多处调用。
3. **`coding.py` / `browser.py` / `mcp.py` / `skills.py` / `plugins.py` / `rag/retriever.py` → `tools.py`**：所有“把能力暴露给模型”的模块都收敛到 `Tool`/`make_tool`/`tool` 契约，tools 的 schema 生成与执行语义是共同底座。
4. **`bootstrap.py` → `plugins.py` → `skills.py`**：生态装配链，插件提供的技能目录经 `SkillRegistry.add_dir` 汇总，最终由 `Agent.enable_skills` 注入。
5. **`multi.py` / `task.py` →（延迟）`checkpoints.py`**：两者通过 `resolve_checkpoint` 共享同一持久化后端协议，是续跑能力的共同依赖（用延迟导入避免环）。
6. **`observability.py` ↔ `tracing.py`（数据契约耦合，且当前不一致）**：observability 消费 tracing 产出的 JSONL，但双方对事件字段名（`event` vs `type`）认知不一致，导致统计失效——这是当前最需要修复的隐性耦合。
7. **`mcp.py` ↔ `bootstrap.py` / `manage.py`**：MCP 服务器配置（mcpServers）由 manage 写入、bootstrap 读取连接，二者通过配置文件格式强耦合。
8. **`__init__.py` → 全部模块**：作为公开 API 聚合点，任何模块的重命名/删除都会在此暴露为破坏性变更。

### 循环依赖规避点（延迟导入）

- `guardrails.py` 的 `LLMGuardrail._parse` 延迟导入 `agent.extract_json`
- `rag/retriever.py` 的 `_llm_rerank` 延迟导入 `agent.extract_json`
- `evals.py` 的 `_score_judge` 延迟导入 `agent.extract_json`；`run_case` 延迟导入 `tools.ToolRegistry`
- `multi.py` / `task.py` 延迟导入 `checkpoints.resolve_checkpoint`
- `anthropic_llm.py` 的异步流沿用延迟导入 `llm.AsyncStreamResult`
- `plugins.py` / `memory.py` / `browser.py` 在方法内延迟导入工具/LLM/media


<!-- 第48批 2026-09-30: skills.parse_frontmatter 升级——支持 YAML 块标量(>折叠/|保留/+-.chomping)，嵌套块(metadata:)跳过；修复 description:> 被截成单字符的问题 -->

<!-- 第51批 2026-09-30: skills.SkillRegistry.remove(name)（用户禁用技能）；343 条全绿 -->
