# 02 · nanoagent 测试、示例与打包文件 — 文件级索引

> 范围：`nanoagent/examples/`（17 个 .py）、`nanoagent/tests/`（26 个文件）、`nanoagent/run_all_tests.py`、`nanoagent/nanoagent.egg-info/*`。
> 级别：very thorough（逐一真实读取）。
> 文件总数：**47**（examples 17 + tests 26 + run_all_tests.py 1 + egg-info 3）。
> 说明：examples 实际为 17 个文件（`01_simple_chat.py` ~ `16_coding_agent.py` 共 16 个 + `mcp_entry.py`）。

---

## 一、examples 学习路径总表（序号 → 主题 → 演示模块）

| 序号 | 文件 | 主题 | 演示/对应源码模块 | 层级 |
|------|------|------|------------------|------|
| 01 | `01_simple_chat.py` | 最简对话 | `agent.py`（Agent.run） | 入门 |
| 02 | `02_custom_tools.py` | 自定义工具 | `tools.py`（@tool） | 入门 |
| 03 | `03_memory_sessions.py` | 会话记忆 | `memory.py`（Memory） | 入门 |
| 04 | `04_rag.py` | RAG 知识库 | `rag/`（KnowledgeBase） | 入门 |
| 05 | `05_multi_agent.py` | 多 agent 编排 | `multi.py`（Pipeline/Team） | 入门 |
| 06 | `06_http_server.py` | HTTP 发布 | `server.py` | 入门 |
| 07 | `07_parallel_and_summary.py` | 并行工具 + 摘要记忆 | `agent.py` + `memory.py`（SummaryMemory） | 进阶 |
| 08 | `08_workflow.py` | 工作流（纯 LLM） | `multi.py`（Workflow） | 进阶 |
| 09 | `09_workflow_with_tools.py` | 工具版工作流 + 路径监狱 | `multi.py` + `tools.py` | 进阶 |
| 10 | `10_async_workflow.py` | 异步工作流 + 结构化输出 + checkpoint | `llm.py`(AsyncLLM)、`checkpoints.py` | 进阶 |
| 11 | `11_plugins.py` | 插件/技能/MCP 一键装配 | `bootstrap.py`、`plugins.py`、`skills.py`、`mcp.py` | 进阶 |
| 12 | `12_task_runner.py` | 自主拆解任务 | `task.py`（TaskRunner） | 进阶 |
| 13 | `13_guardrails.py` | 输入/输出安全护栏 | `guardrails.py` | 进阶 |
| 14 | `14_multimodal.py` | 多模态图片 | `media.py` | 进阶 |
| 15 | `15_anthropic_llm.py` ★ | **Anthropic 协议适配** | `anthropic_llm.py`（AnthropicLLM） | 高级 |
| 16 | `16_coding_agent.py` ★ | **编程 agent 完整配方** | `coding.py` + `task.py` | 高级 |
| — | `mcp_entry.py` | MCP 服务端入口 | `mcp_server.py`（serve_mcp） | 集成 |

★ = 进阶示例：`15_anthropic_llm.py` 展示协议层零改动切换；`16_coding_agent.py` 展示 CodingWorkspace + CODING_INSTRUCTIONS + TaskRunner 的组合配方。

---

## 二、examples 逐文件索引

### `nanoagent/examples/01_simple_chat.py`
- **用途**：最简单的对话 agent，演示 `Agent.run` 单轮问答。
- **关键内容**：`Agent(name, instructions)` 构造；`agent.run("...")` 打印 `result.content` / `result.iterations` / `result.usage`。
- **依赖**：`nanoagent.Agent`。
- **被依赖**：无。
- **影响范围**：`Agent` 构造签名、`AgentResult.{content,iterations,usage}` 变更时需同步。
- **备注**：需 `.env` 配置 OpenAI 兼容服务；真实联网示例。

### `nanoagent/examples/02_custom_tools.py`
- **用途**：用 `@tool` 装饰器定义工具，演示模型自主调用。
- **关键内容**：`calculator`（字符白名单 + `eval`）、`get_weather`（假数据）；打印 `result.tool_calls`。
- **依赖**：`nanoagent.Agent`、`nanoagent.tool`。
- **被依赖**：无。
- **影响范围**：`tool` 装饰器 schema 生成、`tool_calls` 结构变更时需同步。
- **备注**：`eval` 已做字符白名单（`# noqa: S307`）；对应 `tools.py`。

### `nanoagent/examples/03_memory_sessions.py`
- **用途**：多会话记忆 + 滑动窗口 + JSON 持久化恢复。
- **关键内容**：`Memory(max_messages=20, persist_path=".nanoagent/example-03.json")`；`session_id` 隔离；`memory.save()`。
- **依赖**：`nanoagent.Agent`、`nanoagent.Memory`。
- **被依赖**：无。
- **影响范围**：`Memory` 构造参数与 `save()` 返回变更时需同步。
- **备注**：写入 `.nanoagent/` 目录。

### `nanoagent/examples/04_rag.py`
- **用途**：RAG 知识库入库并把检索注册成工具。
- **关键内容**：`KnowledgeBase(persist_path=...)`、`kb.add_text(metadata=...)`、`kb.store`、`kb.as_tool()`。
- **依赖**：`nanoagent.Agent`、`nanoagent.KnowledgeBase`。
- **被依赖**：无。
- **影响范围**：`KnowledgeBase` 接口、`as_tool()` 工具名变更时需同步。
- **备注**：需要服务的 `/embeddings` 接口可用。

### `nanoagent/examples/05_multi_agent.py`
- **用途**：多 agent 编排两种范式。
- **关键内容**：`Pipeline([researcher, writer])`（固定流水线）、`Team(leader, [member...])`（handoff 委托）。
- **依赖**：`nanoagent.Agent/Pipeline/Team`。
- **被依赖**：无。
- **影响范围**：`multi.py` 的 Pipeline/Team 接口变更时需同步。
- **备注**：需真实模型。

### `nanoagent/examples/06_http_server.py`
- **用途**：把 agent 发布为 HTTP 服务。
- **关键内容**：`uvicorn.run(app, host="127.0.0.1", port=8000)`；`from nanoagent.server import app`；`POST /chat`。
- **依赖**：`uvicorn`、`nanoagent.server.app`。
- **被依赖**：无。
- **影响范围**：`server.py` 的 `app` 导出与路由变更时需同步。
- **备注**：需要 `server` extra（fastapi/uvicorn）。

### `nanoagent/examples/07_parallel_and_summary.py`
- **用途**：并行工具执行 + 摘要记忆。
- **关键内容**：`parallel_tools=True`、`max_workers=4`；`SummaryMemory(max_messages=8, keep_recent=2)`；`memory.summary/history`。
- **依赖**：`nanoagent.Agent/SummaryMemory/tool`。
- **被依赖**：无。
- **影响范围**：并行执行与摘要压缩逻辑变更时需同步。
- **备注**：`slow_search`/`slow_calculator` 内 `time.sleep(0.5)` 演示并发省时。

### `nanoagent/examples/08_workflow.py`
- **用途**：框架级 Workflow 四角色反馈回路（纯 LLM，无工具）。
- **关键内容**：`Workflow(planner, coder, reviewer, summarizer, max_rounds=3)`；`result.{review,rounds,passed,summary}`。
- **依赖**：`nanoagent.Agent/Workflow`。
- **被依赖**：无。
- **影响范围**：`multi.py` Workflow 的 PASS 判定与会话隔离变更时需同步。
- **备注**：审查员以最后一行 PASS/FAIL 驱动回路。

### `nanoagent/examples/09_workflow_with_tools.py`
- **用途**：工具版工作流，程序员真实读写文件、审查员只读；文件工具做路径越界防护。
- **关键内容**：`_safe_path()` 路径监狱；`write_file/read_file/list_files`；`WORKSPACE = examples/workflow_workspace`；程序员与审查员权限按职责分配。
- **依赖**：`nanoagent.Agent/Workflow/tool`、`pathlib.Path`。
- **被依赖**：**是** —— `tests/test_workflow_tools.py` 通过 importlib 加载本文件并测 `_safe_path`。
- **影响范围**：改动本示例的 `_safe_path` 或三个文件工具会直接破坏 `test_workflow_tools.py`。
- **备注**：examples 中唯一被测试直接引用的文件。

### `nanoagent/examples/10_async_workflow.py`
- **用途**：异步工作流 + 结构化输出 + checkpoint。
- **关键内容**：`Workflow.arun`、`Agent(llm=AsyncLLM())`、`response_model=DeliveryReport(BaseModel)`、`checkpoint_path=".nanoagent/example-10-checkpoint.json"`、`Workflow.resume`。
- **依赖**：`nanoagent.Agent/AsyncLLM/Workflow`、`nanoagent.memory.Memory`、`pydantic`。
- **被依赖**：无。
- **影响范围**：异步 loop、结构化输出校验、checkpoint 落盘/续跑变更时需同步。
- **备注**：进阶；对应 `test_async_features.py` 的异步/结构化/checkpoint 用例。

### `nanoagent/examples/11_plugins.py`
- **用途**：插件/技能/MCP 一键装配（对齐 dsh）。
- **关键内容**：在临时目录手工搭 `.nanoagent` 生态（原生插件 `plugin.py` + dsh 插件包 + 散装 `SKILL.md`）；`await bootstrap_agent(config_dir, llm=None)`；`report.summary()`；`agent.skills.list_summary()/load()`；`report.aclose()`。
- **依赖**：`nanoagent.bootstrap_agent`、`nanoagent.tool`。
- **被依赖**：无。
- **影响范围**：`bootstrap.py`、`plugins.py`、`skills.py` 的装配协议变更时需同步。
- **备注**：`llm=None` 不真调模型，离线可跑；进阶。

### `nanoagent/examples/12_task_runner.py`
- **用途**：TaskRunner 自主拆解目标并逐项连续完成。
- **关键内容**：`ScriptedLLM`（脚本化模型，规划→执行→汇总）；`TaskRunner(agent, checkpoint="task_demo.json", on_progress=...)`；`result.summary_lines()`。
- **依赖**：`nanoagent.Agent/TaskRunner`、`nanoagent.llm.LLMResponse`。
- **被依赖**：无。
- **影响范围**：`task.py` 规划解析、progress 回调、checkpoint 变更时需同步。
- **备注**：**离线可跑**（用 ScriptedLLM 不调真实模型）。

### `nanoagent/examples/13_guardrails.py`
- **用途**：输入/输出安全护栏。
- **关键内容**：`RecordingLLM`/`JudgeLLM` 离线模型；`keyword_guardrail/length_guardrail/pattern_guardrail/llm_guardrail`；输入护栏可改写 `modified_input`；违规抛 `GuardrailViolation`；fail-closed。
- **依赖**：`nanoagent.Agent/GuardrailResult/GuardrailViolation/*_guardrail`、`nanoagent.llm.LLMResponse`。
- **被依赖**：无。
- **影响范围**：`guardrails.py` 的归一化与四路径集成变更时需同步。
- **备注**：注意 `JudgeLLM` 类定义在 `main()` 之后（运行时已定义，正常）。

### `nanoagent/examples/14_multimodal.py`
- **用途**：给 agent 发图片（多模态）。
- **关键内容**：`images=[path]`、`image_detail="low"`；`make_png()` 零依赖生成 PNG；本地文件/bytes 自动 base64；`nanoagent.config.settings()`。
- **依赖**：`nanoagent.Agent/make_png`、`nanoagent.config.settings`。
- **被依赖**：无。
- **影响范围**：`media.py` 的 `image_part/build_user_content` 变更时需同步。
- **备注**：**需真实视觉模型**；未配 api_key 时 `SystemExit`。

### `nanoagent/examples/15_anthropic_llm.py`
- **用途**：Anthropic 协议适配，同一套 Agent 直连 Anthropic 兼容端点。
- **关键内容**：`AnthropicLLM(base_url="https://api.deepseek.com/anthropic", model, api_key, max_tokens=2048)`；普通对话 / 工具调用（tool_use/tool_result）/ SSE 流式（`run_stream`）。
- **依赖**：`nanoagent.Agent/AnthropicLLM/AsyncLLM/tool`、`nanoagent.config.settings`。
- **被依赖**：无。
- **影响范围**：`anthropic_llm.py` 协议转换、SSE 解析、工具块转换变更时需同步。
- **备注**：**进阶**；需要真实 key；对应 `test_anthropic_llm.py`。

### `nanoagent/examples/16_coding_agent.py`
- **用途**：编程 agent 完整配方。
- **关键内容**：`CodingWorkspace("./examples/coding_workspace", auto_approve=True).as_tools()`；`CODING_INSTRUCTIONS`；`TaskRunner(agent, max_tasks=6, on_progress=...)`；用 `run_command` 跑 unittest。
- **依赖**：`nanoagent.Agent/CODING_INSTRUCTIONS/CodingWorkspace/TaskRunner`、`nanoagent.config.settings`、`sys`。
- **被依赖**：无。
- **影响范围**：`coding.py` 工具集、`task.py` 变更时需同步。
- **备注**：**进阶**；需真实模型；对应 `test_coding.py`。

### `nanoagent/examples/mcp_entry.py`
- **用途**：MCP 接入入口，让编辑器（Claude Code / Cursor / VS Code / dsh）调用 nanoagent。
- **关键内容**：`Agent(name="nanoagent", instructions=...)`；`serve_mcp(agent)` stdio 阻塞。
- **依赖**：`nanoagent.Agent/serve_mcp`。
- **被依赖**：无。
- **影响范围**：`mcp_server.py` 的 `serve_mcp/create_mcp_server` 变更时需同步。
- **备注**：需先配好 `.env`；对应 `test_roadmap.py` 的 McpServerTests。

---

## 三、tests 支撑文件索引

### `nanoagent/tests/__init__.py`
- **用途**：空文件，将 `tests` 标记为 Python 包以支持 `from tests.mocks import ...`。
- **关键内容**：无内容（0 字节）。
- **依赖**：无。
- **被依赖**：所有以 `from tests.mocks import ...` 的测试文件。
- **影响范围**：不应删除，否则包导入失败。
- **备注**：空文件。

### `nanoagent/tests/mocks.py`
- **用途**：测试共享的 Mock LLM 与响应工厂。
- **关键内容**：`MockLLM`（`chat/chat_stream/achat/achat_stream` 依次吐预设响应并记录 `calls`）、`AsyncMockStream`、`_MockStream`、`text_response()`、`tool_response()`、`assistant_tool_message()`。
- **依赖**：`nanoagent.llm.LLMResponse/ToolCall`。
- **被依赖**：几乎所有测试文件（22 个 test_*.py 中大多数）。
- **影响范围**：改动 MockLLM 行为会影响全测试套；`LLMResponse/ToolCall` 字段变更需同步。
- **备注**：响应耗尽会 `raise AssertionError`，可用来断言调用次数。

### `nanoagent/tests/mcp_echo_server.py`
- **用途**：测试用 MCP 服务器（echo / add 两个工具，stdio 传输，mcp 2.x API）。
- **关键内容**：`MCPServer("nanoagent-test-server")`，`@mcp.tool()` 的 `echo`/`add`，`mcp.run()`。
- **依赖**：`mcp.server.mcpserver.MCPServer`（第三方，顶层导入）。
- **被依赖**：`test_async_features.py`、`test_bootstrap.py` 以子进程方式拉起。
- **影响范围**：`mcp.py` 客户端适配逻辑变更时需同步。
- **备注**：**仅在安装 mcp 时可用**；未安装则引用它的 skipUnless 测试跳过。

---

## 四、tests 测试文件逐文件索引

### `nanoagent/tests/test_agent.py`
- **用途**：测 `agent.py`（agent loop）。
- **关键内容**：`AgentLoopTests`（`test_direct_answer_without_tools`、`test_tool_call_then_final_answer`、`test_unknown_tool_returns_error_to_model`、`test_max_iterations_stops_loop`、`test_memory_records_user_and_final`、`test_history_passed_to_llm`）；`AgentStreamTests`（`test_stream_events`、`test_stream_with_tool_call`）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.memory.Memory`、`nanoagent.tools.tool`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`agent.py` loop/流式/记忆写入行为变更时需同步。
- **备注**：全离线（MockLLM），无 skip 逻辑。

### `nanoagent/tests/test_anthropic_llm.py`
- **用途**：测 `anthropic_llm.py`（协议转换 / SSE 解析 / MockTransport 端到端）。
- **关键内容**：`MessageConversionTests`（system 顶层化、tool_result 合并、多模态转换、tools schema）、`ResponseParsingTests`、`SSEParseTests.test_full_stream_assembly`、`MockTransportTests`（含 `test_agent_end_to_end_with_tools`）、`AsyncMockTransportTests`（IsolatedAsyncio）。
- **依赖**：`nanoagent.anthropic_llm`（`AnthropicLLM/AsyncAnthropicLLM/finalize_stream/from_anthropic_response/parse_sse_event/to_anthropic_messages/to_anthropic_tools`）、`nanoagent.agent.Agent`、`nanoagent.llm.LLMResponse`、`httpx`。
- **被依赖**：无。
- **影响范围**：`anthropic_llm.py` 任何协议细节变更都需同步。
- **备注**：用 `httpx.MockTransport` **完全离线**；无 skip。

### `nanoagent/tests/test_async_features.py`
- **用途**：测异步 agent loop、结构化输出、Workflow checkpoint、MCP 适配/集成。
- **关键内容**：`AsyncAgentTests`（`test_arun_direct_answer`、混合同步/异步工具、`test_arun_parallel_faster_than_serial`、流式、`test_multi_arun`）；`StructuredOutputTests`（`response_model` + 重试 + `extract_json`）；`CheckpointTests`（落盘/续跑）；`McpAdapterTests`；`McpIntegrationTests`。
- **依赖**：`nanoagent.agent.Agent/OutputValidationError/extract_json`、`nanoagent.llm`、`nanoagent.memory.Memory`、`nanoagent.multi.{Pipeline,Team,Workflow}`、`nanoagent.tools.tool`、`nanoagent.mcp.{MCPServer,mcp_schema_to_nanoagent}`（try）、`pydantic`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`agent.py` 异步路径、`multi.py` checkpoint、`mcp.py` 适配变更时需同步。
- **备注**：`HAS_MCP = False` 时 `McpAdapterTests`/`McpIntegrationTests` 用 `@skipUnless(HAS_MCP, "需要安装 mcp")` 跳过；MCP 集成会真实拉起 `mcp_echo_server.py` 子进程。

### `nanoagent/tests/test_bootstrap.py`
- **用途**：测 `bootstrap.py` 与 `mcp.py` 的 `MCPManager`。
- **关键内容**：`MCPManagerConfigTests`（add/remove/list 持久化往返、校验、非法配置报错）；`BootstrapTests`（端到端装配、空目录、非法 mcp.json 记为 failed）；`BootstrapMcpTests`（连接 MCP、connect_all/disconnect_all）。
- **依赖**：`nanoagent.bootstrap.{bootstrap_agent,bootstrap_agent_sync}`、`nanoagent.mcp.MCPManager`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`bootstrap.py` 装配协议、`mcp.py` MCPManager 变更时需同步。
- **备注**：`HAS_MCP` try-import 守卫；`BootstrapMcpTests` 整体 `@skipUnless(HAS_MCP, "需要安装 mcp")`。

### `nanoagent/tests/test_coding.py`
- **用途**：测 `coding.py`（路径监狱、文件工具、搜索、确认门、Agent 集成）。
- **关键内容**：`SandboxTests`（越界拒绝、`sub/..` 落回内部放行）、`FileToolTests`（读写/行号/范围编辑/diff/删除）、`BrowseSearchTests`、`ApprovalGateTests`（默认拒绝/确认回调/auto_approve/超时/cwd）、`GitAndProcessTests`（git init 提交流程、后台进程生命周期、spawn_subagent）、`AgentIntegrationTests`（工具集名与白名单）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.coding.{CODING_INSTRUCTIONS,CodingWorkspace,SandboxViolation}`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`coding.py` 任何工具/确认门/沙箱逻辑变更都需同步。
- **备注**：平台相关（`dir /b` vs `ls`）；`test_git_commit_flow` 依赖系统 `git`；后台进程/超时用真实子进程。

### `nanoagent/tests/test_manage.py`
- **用途**：测 `manage.py` 的技能移除命令（N-20 修复的回归用例）。
- **关键内容**：`RemoveSkillTests`——`remove-skill` 对 `skills/<name>/` 目录、`skills/<name>.md` 单文件、`skills/<name>` 无扩展单文件三种形态均可移除；对不存在名字抛 `SystemExit`。
- **依赖**：`nanoagent.manage.cmd_remove_skill`、`argparse.Namespace`。
- **被依赖**：无。
- **影响范围**：`manage.py` 的 `remove-skill` 逻辑变更时需同步。
- **备注**：新增于修复轮次（原审计指出 `manage.py` 的 CLI 子命令零覆盖）。

### `nanoagent/tests/test_ecosystem.py`
- **用途**：测最后批次新能力：`evals.py`、`checkpoints.py`、`task.py`（重规划）、`server.py`（SSE 端点）、`llm.py`（重试）。
- **关键内容**：`EvalsTests`（contains/regex/judge 打分、案例隔离、临时工具、报告保存）；`CheckpointBackendTests`（JsonFile/SQLite/InMemory/resolve_checkpoint）；`CheckpointWiringTests`（TaskRunner + 后端）；`ReplanningTests`（[ADD] 追加/去重/上限/剥离）；`SSEEndpointTests`（`/chat/stream`、空消息 400）；`LLMRetryTests`（`_with_retry` 退避与不可重试）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.checkpoints.*`、`nanoagent.evals.EvalRunner`、`nanoagent.task.{TaskRunner,TodoItem}`、`nanoagent.server.create_app`（方法内导入）、`nanoagent.llm._with_retry`、`fastapi.testclient`（方法内导入）、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：对应五个模块变更时需同步。
- **备注**：**`SSEEndpointTests` 在方法内 `import fastapi.testclient` 但无 skip 守卫**——缺 fastapi 时会报错而非跳过（与 `test_entry.py` 的 skipUnless 不同）。

### `nanoagent/tests/test_entry.py`
- **用途**：入口冒烟测试（CLI 参数解析 + HTTP 应用路由）。
- **关键内容**：`CliArgsTests`（默认值/覆盖）；`ServerAppTests`（`/chat`、空消息 400、`/health`、`/sessions`、`/sessions/{id}/clear`）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.cli.parse_args`、`nanoagent.memory.Memory`、`nanoagent.server.create_app`（try）、`fastapi.testclient`（try）、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`cli.py` 参数、`server.py` 路由变更时需同步。
- **备注**：`HAS_FASTAPI` try-import；`ServerAppTests` 用 `@skipUnless(HAS_FASTAPI, "需要安装 server extra")` 跳过。

### `nanoagent/tests/test_faiss.py`
- **用途**：测 `rag/faiss_store.py` 并与 `rag/store.py` 的 numpy 后端做一致性对比。
- **关键内容**：`FaissStoreTests`（余弦排序、维度/形状校验、空库、零范数、save/load、缺文件报错）；`BackendConsistencyTests`（`create_store` 工厂、双后端结果一致、KnowledgeBase backend 参数）。
- **依赖**：`nanoagent.rag.{FaissVectorStore,VectorStore,create_store,KnowledgeBase}`、`numpy`、`faiss`（try）。
- **被依赖**：无。
- **影响范围**：两个 store 后端接口变更时需同步。
- **备注**：`HAS_FAISS` try-import；两个测试类均 `@skipUnless(HAS_FAISS, ...)` 跳过；`import numpy` 为顶层硬依赖。

### `nanoagent/tests/test_guardrails.py`
- **用途**：测 `guardrails.py` 及与 `agent.py` 的四路径集成。
- **关键内容**：`CoerceTests`（返回值归一化、非法类型 fail-closed、异常 fail-closed、需 callable）；`BuiltinGuardrailTests`（keyword/length/pattern）；`LLMGuardrailTests`（判别 + 坏 JSON fail-closed）；`AgentSyncIntegrationTests`（输入拦截/改写、输出拦截、流式、无护栏 noop）；`AgentAsyncIntegrationTests`（异步输入/输出、协程护栏、异步 LLM 护栏、异步流）；`GuardrailsExecutorTests`（顺序改写链、`acheck_input`）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.guardrails.*`、`nanoagent.llm.LLMResponse`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`guardrails.py` 与 `agent.py` 护栏集成点变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_media.py`
- **用途**：测 `media.py` 及 `agent.py` 的图片参数与记忆行为。
- **关键内容**：`ImagePartTests`（URL/data URL 透传、文件转 base64 且按魔数嗅探 MIME、扩展名兜底、bytes、未知 bytes 拒绝、detail、dict 透传、非法类型）；`BuildUserContentTests`；`AgentMultimodalTests`（多模态消息、纯文本保持、图片不进记忆、detail 透传、流式）；`AgentMultimodalAsyncTests`；`MakePngTests`。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.media.{build_user_content,image_part,make_png}`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`media.py` 编码/嗅探逻辑、`Agent.run(images=...)` 契约变更时需同步。
- **备注**：全离线；用最小 PNG/JPEG 魔数构造 bytes。

### `nanoagent/tests/test_memory.py`
- **用途**：测 `memory.py`（滑动窗口/持久化）与 `tracing.py`（JSONL trace）。
- **关键内容**：`MemoryTests`（history 为副本且无 ts、窗口裁剪、持久化往返、损坏文件容错、clear）；`TracerTests`（禁用为 noop、事件写 JSONL 且同 run 共 run_id、path=None 禁用）。
- **依赖**：`nanoagent.memory.Memory`、`nanoagent.tracing.Tracer`。
- **被依赖**：无。
- **影响范围**：`memory.py`/`tracing.py` 变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_multi.py`
- **用途**：测 `multi.py`（agent-as-tool 委托、Pipeline、Team）。
- **关键内容**：`AgentAsToolTests`（委托返回子 agent 回复、写入子会话）；`PipelineTests`（输出逐级流转、空流水线拒绝）；`TeamTests`（成员注册为 leader 工具、schema 注入、空成员拒绝）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.memory.Memory`、`nanoagent.multi.{Pipeline,Team,agent_as_tool}`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`multi.py` 编排逻辑变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_parallel.py`
- **用途**：测 `agent.py` 的并行工具执行。
- **关键内容**：`ParallelExecutionTests`（`test_parallel_faster_than_serial`、`test_serial_when_disabled`、`test_order_preserved_with_error_isolation`、`test_invalid_max_workers_rejected`、`test_full_loop_with_parallel_tools`）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.llm.ToolCall`、`nanoagent.memory.Memory`、`nanoagent.tools.tool`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`agent.py` 的 `_execute_tool_calls`、线程池、顺序保持逻辑变更时需同步。
- **备注**：用 `time.sleep` 实测并发省时；断言带时间阈值，CI 慢机可能敏感。

### `nanoagent/tests/test_plugins.py`
- **用途**：测 `plugins.py`（mini-Cordis 内核、格式探测/适配、PluginManager 生命周期）。
- **关键内容**：`EventBusTests`（订阅/退订、异常隔离）；`PluginContextTests`（provide/dispose、effect LIFO、幂等、facade 注册去重）；`PluginManagerFormatTests`（nanoagent 原生、dsh 包、mcp-only、agent-skills、未知格式不拖垮、重名后缀、坏插件记 failed、自定义适配器、二次激活幂等、list/detect）。
- **依赖**：`nanoagent.plugins.*`、`nanoagent.tools.{Tool,tool}`。
- **被依赖**：无。
- **影响范围**：`plugins.py` 内核/适配器/manifest 探测变更时需同步。
- **备注**：`test_custom_adapter_via_register_adapter` 会临时注册并清理 `_ADAPTERS`；全离线。

### `nanoagent/tests/test_rag.py`
- **用途**：测 `rag/`（分块、向量库余弦检索、KnowledgeBase 工具化）。
- **关键内容**：`ChunkingTests`（短段落合并、长段落重叠硬切、空文本、非法参数、export alias 同一函数）；`VectorStoreTests`（排序、维度校验、空库、零范数、save/load）；`KnowledgeBaseTests`（用 `FakeEmbedLLM` 桩替换 embedding：add/query、多 chunk、空库、as_tool、add 自动保存）。
- **依赖**：`nanoagent.rag.{KnowledgeBase,VectorStore,split_text}`、`nanoagent.rag.chunking.split_text`、`numpy`。
- **被依赖**：无。
- **影响范围**：`rag/chunking.py`、`rag/store.py`、`rag/__init__.py`、`rag/retriever.py` 变更时需同步。
- **备注**：`import numpy` 顶层硬依赖；embedding 用桩，**离线可跑**；无 skip。

### `nanoagent/tests/test_roadmap.py`
- **用途**：Roadmap 批次测试：`mcp_server.py`、`observability.py`、`rag/retriever.py`（重排序）、`browser.py`。
- **关键内容**：`McpServerTests`（`create_mcp_server` 暴露 `chat`/`list_agent_tools` 并经 stdio 客户端端到端调用）；`TraceObservabilityTests`（`trace_summary`、`trace_report` 生成 HTML、`export_traces_to_otel` 优雅降级）；`RagRerankTests`（LLM 重排序成功 + 坏 JSON 降级为向量序）；`BrowserTests`（navigate 需 playwright、拒绝非 http、`as_tools` 名称）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.observability.{trace_report,trace_summary,export_traces_to_otel}`、`nanoagent.rag.retriever.KnowledgeBase`、`nanoagent.BrowserWorkspace`、`nanoagent.mcp.MCPServer`（方法内）、`mcp`（try）、`playwright`（try）、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：对应四模块变更时需同步。
- **备注**：`HAS_MCP`/`HAS_PLAYWRIGHT` try-import；`McpServerTests` 内用 `self.skipTest("需要安装 mcp")`；`BrowserTests` 内 try/except ImportError 自适配；`test_otel_export_or_graceful` 允许 ImportError 视为通过。

### `nanoagent/tests/test_skills.py`
- **用途**：测 `skills.py`（frontmatter 解析、注册表、渐进式披露、enable_skills）。
- **关键内容**：`FrontmatterTests`（带/不带 frontmatter、未闭合、引号与冒号值）；`SkillRegistryTests`（add/summary、目录名回退、add_dir 递归与缺失静默、load 未知列可用、load 返回正文）；`EnableSkillsTests`（注册 use_skill 与索引、幂等、agent loop 调用技能、未知技能返回错误、工具缓存幂等）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.skills.{Skill,SkillRegistry,parse_frontmatter}`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`skills.py` 解析与注册逻辑变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_summary_memory.py`
- **用途**：测 `memory.py` 的 `SummaryMemory`（触发时机、摘要注入、滚动压缩、持久化）。
- **关键内容**：`SummaryMemoryTests`（阈值下不压缩、溢出压缩、history 首条注入摘要、滚动摘要包含旧摘要、持久化往返、兼容旧格式、clear 清摘要、非法 keep_recent）。
- **依赖**：`nanoagent.llm.LLMResponse`、`nanoagent.memory.SummaryMemory`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`SummaryMemory` 压缩时机与 prompt 组装变更时需同步。
- **备注**：自建 `_CounterLLM` 桩；离线；无 skip。

### `nanoagent/tests/test_task.py`
- **用途**：测 `task.py`（规划解析、逐项推进、checkpoint 续跑、异常隔离、异步）。
- **关键内容**：`PlanningTests`（端到端、dict 包裹容错、坏 JSON 重试、最终失败抛 `TaskPlanningError`、max_tasks 截断）；`ExecutionTests`（连续性上下文、单项异常记 skipped、on_progress 序列、执行期工具可用）；`CheckpointTests`（落盘、续跑不重规划、缺文件报错）；`AsyncTaskTests`（`arun`/`aresume`）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.task.{TaskPlanningError,TaskRunner,TodoItem}`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`task.py` 规划/执行/持久化逻辑变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_audit_fixes.py`
- **用途**：第二批审计修复（2026-09-27，提交 23094b2）的回归用例：N-03 MCP 握手失败回滚 transport 与 disconnect 双层异常、N-06 stream_options include_usage、N-10e _accumulate 进程锁 + Memory.add 实例锁、N-10f anthropic error 事件记 state。
- **依赖**：`tests.mocks`；mock LLM 离线运行。
- **被依赖**：`run_tests.py`/CI discover。
- **备注**：随修复新增，nanoagent 测试 320→324（后续 Roundtable 等 +4 至 328）。

### `nanoagent/tests/test_token_memory.py`
- **用途**：测 `memory.py` 的 token 化上下文管理。
- **关键内容**：`HeuristicEstimateTests`（启发式本体：ASCII≈4 字符/token、CJK≈1 字/token、混合、空串）；`EstimateDispatchTests`（无 tiktoken 时回退启发式、**有 tiktoken 时必须真走精确路径**、多模态图片计 1024）；`TokenWindowTests`（按 token 预算淘汰、条数上限、双限并用、单条超限清空、参数校验）；`SummaryAutoCompactTests`（token 超限自动压缩、预算内不压缩）。
- **依赖**：`nanoagent.memory.{Memory,SummaryMemory,_heuristic_estimate,estimate_tokens,message_tokens}`、`nanoagent.memory._TIKTOKEN_ENCODER`（经 `forced_heuristic()` 打桩）、`nanoagent.llm.LLMResponse`、可选第三方 `tiktoken`。
- **被依赖**：无。
- **影响范围**：`memory.py` 的 token 估算与自动压缩逻辑变更时需同步。
- **备注**：自建计数桩 LLM；离线；**含 1 条条件 skip**（未装 tiktoken 时跳过 `test_prefers_tiktoken_when_available`）。
  2026-09-26 修：原 `EstimateTests` 直接断言裸 token 数，在装了 tiktoken 的 CI 上必挂而本地（未装）看不出来，属"看环境脸色"的脆弱测试。
  现改为用 `forced_heuristic()` 锁定路径 + 把启发式拆成 `_heuristic_estimate` 直接断言；有/无 tiktoken 两种环境各 314 条全绿。

### `nanoagent/tests/test_tools.py`
- **用途**：测 `tools.py`（schema 生成、docstring 解析、注册表执行、工具名净化）。
- **关键内容**：`ToolNameSanitizeTests`（ASCII 保留、非法字符加哈希、中文名确定性且不冲突、make_tool 应用净化、注册表去冲突）；`ToolSchemaTests`（注解生成、docstring 描述、Optional/容器类型、name/description 覆盖、缺 docstring 兜底）；`ToolRegistryTests`（注册执行、未知工具报错、异常转字符串、非字符串 JSON 序列化、OpenAI schema、普通函数注册）。
- **依赖**：`nanoagent.llm.ToolCall`、`nanoagent.tools.{ToolRegistry,make_tool,sanitize_tool_name,tool}`。
- **被依赖**：无。
- **影响范围**：`tools.py` schema/净化/执行逻辑变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_workflow.py`
- **用途**：测 `multi.py` 的 `Workflow`（反馈回路、PASS 判定、轮次上限、会话隔离）。
- **关键内容**：`WorkflowTests`（首轮 PASS、FAIL→PASS 回路、max_rounds 耗尽、结果结构、跨 run 会话隔离）；`PassDetectionTests`（末行 PASS/FAIL、无标记回退、同时出现保守判失败、空审查失败）；`WorkflowValidationTests`（非 Agent 角色 TypeError、非法 max_rounds ValueError）。
- **依赖**：`nanoagent.agent.Agent`、`nanoagent.memory.Memory`、`nanoagent.multi.{Workflow,WorkflowResult}`、`tests.mocks`。
- **被依赖**：无。
- **影响范围**：`multi.py` 的 `_is_pass`、会话隔离、角色校验变更时需同步。
- **备注**：全离线；无 skip。

### `nanoagent/tests/test_workflow_tools.py`
- **用途**：测 **examples/09** 文件工具的安全（路径越界防护）。
- **关键内容**：`WorkspaceJailTests`（读写往返、子目录、缺文件列现有、`../` 与 `sub/../../` 越界拒绝、绝对路径拒绝、`sub/..` 落回内部放行）。
- **依赖**：`importlib.util` 动态加载 `examples/09_workflow_with_tools.py`；运行时把模块的 `WORKSPACE` 替换到临时目录。
- **被依赖**：无。
- **影响范围**：**被测对象是示例文件本身**，改动 `examples/09_workflow_with_tools.py` 的 `_safe_path`/`write_file`/`read_file`/`list_files` 必须同步本测试。
- **备注**：示例模块 `__main__` 块有保护不会执行；全离线；无 skip。

---

## 五、打包与运行辅助文件索引

### `nanoagent/run_all_tests.py`
- **用途**：一键跑全量测试。
- **关键内容**：硬编码 `sys.path.insert(0, r"E:\文件\编程文件\agent\nanoagent")`；`unittest.TestLoader().discover(...)`；`TextTestRunner` 输出；退出码按成功与否。
- **依赖**：`unittest`、`sys`。
- **被依赖**：CI / 手动。
- **影响范围**：路径硬编码，迁移目录后需改第 4、7 行。
- **备注**：**路径为绝对硬编码**，非可移植脚本。

### 注：nanoagent/nanoagent.egg-info/ 目录为 editable 安装的元数据，已列入索引 SKIP_DIRS（缓存/产物），不再逐文件建条目。


## 六、测试覆盖矩阵（源码模块 → 对应测试文件 → 覆盖状态）

| 源码模块 | 对应测试文件 | 覆盖状态 |
|----------|-------------|----------|
| `agent.py` | test_agent / test_async_features / test_parallel / test_guardrails / test_media / test_coding / test_task / test_multi / test_workflow | 充分 |
| `anthropic_llm.py` | test_anthropic_llm.py | 充分（含异步、SSE、端到端） |
| `bootstrap.py` | test_bootstrap.py | 充分 |
| `browser.py` | test_roadmap.py（BrowserTests） | **部分**（依赖 playwright） |
| `checkpoints.py` | test_ecosystem.py | 充分 |
| `cli.py` | test_entry.py（CliArgsTests） | **部分**（仅 `parse_args`；未测 `main` 循环） |
| `coding.py` | test_coding.py | 充分 |
| `config.py` | 无 | **未覆盖** |
| `evals.py` | test_ecosystem.py | 充分 |
| `guardrails.py` | test_guardrails.py | 充分 |
| `llm.py` | test_ecosystem.py（LLMRetryTests）+ 间接 | **部分**（`LLM/AsyncLLM` HTTP 客户端无直测） |
| `manage.py` | 无 | **未覆盖** |
| `mcp.py` | test_async_features / test_bootstrap / test_roadmap | 充分（缺 mcp 时跳过） |
| `mcp_server.py` | test_roadmap.py（McpServerTests） | **部分**（依赖 mcp） |
| `media.py` | test_media.py | 充分 |
| `memory.py` | test_memory / test_summary_memory / test_token_memory | 充分 |
| `multi.py` | test_multi / test_workflow / test_async_features | 充分 |
| `observability.py` | test_roadmap.py（TraceObservabilityTests） | 充分（OTel 缺失时降级） |
| `plugins.py` | test_plugins.py、test_bootstrap.py | 充分 |
| `server.py` | test_entry.py、test_ecosystem.py | 充分（缺 fastapi 时 test_entry 跳过） |
| `skills.py` | test_skills.py | 充分 |
| `task.py` | test_task.py、test_ecosystem.py（ReplanningTests） | 充分 |
| `tools.py` | test_tools.py | 充分 |
| `tracing.py` | test_memory.py（TracerTests） | 充分 |
| `rag/*` | test_rag.py、test_faiss.py | 充分 / **faiss 部分**（缺 faiss 跳过） |

**完全没有测试覆盖的源码模块**：
1. `nanoagent/nanoagent/config.py`
2. `nanoagent/nanoagent/manage.py`

**仅部分/间接覆盖（存在风险）**：
- `llm.py`：仅 `_with_retry` 有直测，`LLM`/`AsyncLLM` 真实 HTTP 路径无直测（测试统一用 MockLLM/httpx.MockTransport 替代）。
- `cli.py`：仅参数解析被覆盖，`main()` 交互循环未测。
- `browser.py`、`mcp_server.py`、`rag/faiss_store.py`：核心逻辑有覆盖，但可选依赖缺失时整体跳过。

**无 skip 守卫但依赖额外包的测试**：`test_ecosystem.py::SSEEndpointTests` 在方法内导入 `fastapi.testclient`，缺 fastapi 时直接报错；`test_faiss.py` / `test_rag.py` 顶层 `import numpy` 为硬依赖。

---

## 七、关键交叉验证结论

- **有"缺依赖则跳过"逻辑的测试文件**：`test_async_features.py`（mcp）、`test_bootstrap.py`（mcp）、`test_entry.py`（fastapi）、`test_faiss.py`（faiss）、`test_roadmap.py`（mcp / playwright）。均通过 `try: import X / except ImportError: HAS_X=False` + `@unittest.skipUnless(...)` 或方法内 `skipTest` 实现。
- **离线可跑（不需联网/真实模型）的测试与示例**：全部 tests 文件（MockLLM / httpx.MockTransport）；示例中的 `12_task_runner.py`、`13_guardrails.py`、`11_plugins.py`（`llm=None`）。
- **需要真实模型/key 的示例**：01、02、03、04、05、07、08、09、10、14、15、16 及 `mcp_entry.py`。
- **示例与测试的唯一直连**：`examples/09_workflow_with_tools.py` ← `tests/test_workflow_tools.py`。
