---
title: "Hermes Agent 核心精华代码 · 一周学习计划"
subtitle: "面向 agent 工程师的可执行源码阅读路线：主循环 / 上下文压缩 / Memory / Skills / Tool dispatch / MoA / Steering"
date: "2026-07-05"
description: "基于 Hermes Agent 当前代码仓，制定一份可实施的一周核心源码学习计划。覆盖主循环、上下文压缩、Memory 管理、Skills 机制、Tool dispatch、MoA、Prompt Caching 与 Mid-turn Steering，提供每日阅读文件、关键函数/类、动手任务与输出要求。"
tags: ["Hermes Agent", "agent engineering", "source code", "learning plan", "context compression", "memory", "skills"]
---

# Hermes Agent 核心精华代码 · 一周学习计划

> 这份计划面向已经会用 Hermes Agent、但想深入其 runtime 实现的 agent 工程师。目标不是读完整套代码，而是抓住最核心的机制：一次 turn 怎么跑起来、上下文太长怎么办、记忆怎么存、技能怎么加载、工具怎么调度、多模型怎么协作、以及用户怎么在中途插话。

---

## 目标读者

- 用过 Hermes CLI / Gateway，见过它跑多轮任务
- 写过 tool use 或 skill，想了解 runtime 怎么承载这些能力
- 想在一周内建立源码层面的心理模型，而不是泛泛读文档

## 学习方法论

1. **先读高层、再进细节**：每天先读仓库里的 origin 文章（如果已有），再对照源码验证
2. **带着问题读代码**：不要通读文件，先定位关键函数，再顺着调用链往外扩
3. **动手做小实验**：改配置、打日志、跑单测、写最小复现，才算真懂
4. **每天写 200 字笔记**：把"我以为是"改成"代码里确实是"

## 前置准备

```bash
# 1. 确认源码位置
ls /Users/eriklee/code/agent/hermes-agent

# 2. 进入虚拟环境
source /Users/eriklee/code/agent/hermes-agent/.venv/bin/activate

# 3. 确认核心包可导入
python -c "import hermes_cli, agent; print('ok')"

# 4. 准备阅读工具：带行号的编辑器/IDE，以及 grep/fzf
```

---

## 整体源码地图

```text
/Users/eriklee/code/agent/hermes-agent/
├── run_agent.py                 # AIAgent 主类、steer 状态、会话入口
├── agent/
│   ├── conversation_loop.py     # ~3,900 行的 turn 执行引擎
│   ├── turn_context.py          # 每 turn 启动前的上下文准备
│   ├── turn_finalizer.py        # turn 收尾、预算、持久化
│   ├── context_engine.py        # ContextEngine ABC
│   ├── context_compressor.py    # 内置压缩引擎 ContextCompressor
│   ├── conversation_compression.py  # 压缩编排与 session 轮转
│   ├── trajectory.py            # 轨迹保存
│   ├── memory_manager.py        # Memory 协调器
│   ├── memory_provider.py       # Memory Provider ABC
│   ├── prompt_caching.py        # Anthropic prompt caching 策略
│   ├── skill_commands.py        # /skill-name 命令发现与调用
│   ├── skill_utils.py           # skill 元数据工具
│   ├── skill_bundles.py         # 多 skill bundle
│   ├── tool_executor.py         # 工具并发/串行执行
│   ├── tool_dispatch_helpers.py # 并行性判断、工具结果封装
│   ├── moa_loop.py              # Mixture of Agents 运行时
│   ├── moa_trace.py             # MoA trace 持久化
│   └── prompt_builder.py        # system prompt / steer marker 构建
├── hermes_cli/
│   ├── moa_cmd.py               # hermes moa 命令
│   └── moa_config.py            # MoA preset 解析
├── tools/
│   ├── registry.py              # 工具自注册表
│   ├── skills_tool.py           # skills_list / skill_view
│   ├── skills_hub.py            # skill hub 状态与 source adapter
│   ├── memory_tool.py           # 内置 MEMORY.md/USER.md 工具
│   └── session_search_tool.py   # 跨会话 FTS5 搜索
└── gateway/                     # 消息网关（可选，Week 2 内容）
```

---

## Day 1 · Agent 主循环与 Turn 生命周期

> 核心问题：一次 user turn 从发消息到返回结果，完整链路是什么？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `run_agent.py:403` | `AIAgent` | 主类，持有状态与配置 |
| `run_agent.py` | `run_conversation()` | 入口转发 |
| `agent/conversation_loop.py:518` | `run_conversation()` | turn 执行引擎主体 |
| `agent/conversation_loop.py:277` | `_restore_or_build_system_prompt()` | system prompt 重建 |
| `agent/turn_context.py:119` | `build_turn_context()` | turn 启动前准备 |
| `agent/turn_context.py:93` | `TurnContext` | 本 turn 上下文数据类 |
| `agent/turn_finalizer.py:30` | `finalize_turn()` | turn 收尾 |

### 学习步骤

1. 在 `run_agent.py` 找到 `AIAgent`，看它持有哪些字段（`_pending_steer`、memory manager、context engine、tool registry）
2. 顺着 `run_conversation()` 进入 `agent/conversation_loop.py:518`
3. 画出一次 turn 的主干流程：
   - 准备 `TurnContext`
   - 构建/恢复 system prompt
   - LLM API 调用
   - tool calls 执行
   - 结果回注
   - finalize
4. 关注 `agent/conversation_loop.py` 中处理续流（continuation）和 failover 的分支

### 动手任务

- [ ] 在 `conversation_loop.py` 的 `run_conversation()` 开头和结尾各加一行日志，跑一次 `hermes -z "hello"`，确认 turn 边界
- [ ] 用 `git grep "def run_conversation"` 确认所有入口

### 今日输出

- 一张 turn 生命周期时序图（Mermaid）
- 200 字笔记：`TurnContext` 和 `finalize_turn` 各自承担了什么

---

## Day 2 · 上下文压缩（Context Compression）

> 核心问题：对话变长后，Hermes 如何在不截断的情况下压缩历史？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `agent/context_engine.py:32` | `ContextEngine` | 可插拔上下文引擎 ABC |
| `agent/context_compressor.py:662` | `ContextCompressor` | 内置压缩引擎 |
| `agent/context_compressor.py:540` | `_summarize_tool_result()` | 工具结果预裁剪 |
| `agent/context_compressor.py:483` | `_strip_historical_media()` | 历史媒体剥离 |
| `agent/conversation_compression.py:435` | `compress_context()` | 压缩编排入口 |
| `agent/conversation_compression.py:154` | `check_compression_model_feasibility()` | 启动探测 |
| `agent/conversation_compression.py:371` | `conversation_history_after_compression()` | 压缩后历史重建 |
| `gateway/run.py:9404` | gateway 会话卫生层 | 85% 阈值安全网 |

### 学习步骤

1. 读 `agent/context_engine.py`，理解 `ContextEngine` ABC 的 5 个生命周期方法
2. 读 `agent/context_compressor.py:662`，理解 4 阶段流水线：
   - 触发判断
   - 保护头尾
   - 中段摘要
   - 结果回写
3. 读 `agent/conversation_compression.py:435`，看压缩失败如何回退
4. 对比仓库已有的 origin 文章 `content/origin/2026-07-01-hermes-context-compression/index.md`，验证自己的理解

### 动手任务

- [ ] 找到 `config.yaml` 中 `context` 相关配置项，尝试把 `threshold_percent` 调到 30%，跑一个长对话观察压缩触发
- [ ] 在 `compress_context()` 中打印压缩前后的 token 数和消息数

### 今日输出

- 一张双层压缩架构图（Gateway 85% vs Agent 50%）
- 200 字笔记：压缩与截断的本质区别是什么

---

## Day 3 · Memory 管理

> 核心问题：Hermes 如何在多轮、多会话之间保持对用户和任务的记忆？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `agent/memory_manager.py:353` | `MemoryManager` | memory 协调器 |
| `agent/memory_manager.py:336` | `build_memory_context_block()` | 把 memory 拼进 system prompt |
| `agent/memory_manager.py:100` | `inject_memory_provider_tools()` | 注入 memory provider 工具 |
| `agent/memory_provider.py:43` | `MemoryProvider` | provider ABC |
| `tools/memory_tool.py:113` | `MemoryStore` | 文件级 memory 存储 |
| `tools/memory_tool.py:959` | `memory_tool()` | agent 可调用入口 |
| `tools/memory_tool.py:1036` | `apply_memory_pending()` | 批量写回磁盘 |
| `tools/session_search_tool.py:619` | `session_search()` | 跨会话 FTS5 搜索 |
| `tools/session_search_tool.py:499` | `_discover()` | 全文检索与去重 |

### 学习步骤

1. 读 `agent/memory_provider.py:43`，列出 provider 必须实现的 8 个方法
2. 读 `agent/memory_manager.py:353`，看它是如何强制"最多一个 external provider"的
3. 读 `tools/memory_tool.py`，理解 `MEMORY.md` / `USER.md` 的读取-修改-写回流程：
   - 启动时加载为只读快照进入 system prompt
   - 运行中通过 `memory_tool(add/replace/remove)` 修改
   - turn 结束时 `apply_memory_pending()` 批量写盘
4. 读 `tools/session_search_tool.py`，理解跨会话召回的三种模式

### 动手任务

- [ ] 找到 `~/.hermes/memory/` 下的 `MEMORY.md` 和 `USER.md`，观察 mid-session 写入后文件何时更新
- [ ] 跑 `hermes -z "search my old sessions for python"`，抓 `session_search` 工具调用日志

### 今日输出

- 一张 memory 数据流图：文件 memory ↔ provider memory ↔ session search
- 200 字笔记：为什么 mid-session memory 写入不刷新当前 system prompt

---

## Day 4 · Skills 机制

> 核心问题：Skills 是怎么被发现、加载、渐进式披露的？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `tools/skills_tool.py:689` | `skills_list()` | 列出所有可用 skill 元数据 |
| `tools/skills_tool.py:864` | `skill_view()` | 加载完整 skill 或指定引用文件 |
| `tools/skills_tool.py:482` | `check_skills_requirements()` | 前置依赖检查 |
| `agent/skill_commands.py:348` | `scan_skill_commands()` | 发现 `/skill-name` 命令 |
| `agent/skill_commands.py:58` | `extract_user_instruction_from_skill_message()` | 从 skill 消息还原用户指令 |
| `agent/skill_commands.py:517` | `build_skill_invocation_message()` | 构造 skill 调用消息 |
| `agent/skill_utils.py:123` | `parse_frontmatter()` | YAML frontmatter 解析 |
| `agent/skill_utils.py:499` | `get_all_skills_dirs()` | 发现 skill 目录 |
| `agent/skill_bundles.py:195` | `get_skill_bundles()` | 多 skill bundle |
| `tools/skills_hub.py:424` | `SkillSource` | skill hub source adapter ABC |

### 学习步骤

1. 读 `tools/skills_tool.py:689`，理解 `skills_list()` 的三层渐进式披露：
   - Level 0：只返回元数据（~3k tokens）
   - Level 1：`skill_view(name)` 加载完整 `SKILL.md`
   - Level 2：`skill_view(name, path)` 加载指定 reference/script
2. 读 `agent/skill_utils.py`，看目录扫描如何支持多层路径（`category/skill-name/SKILL.md`）
3. 读 `agent/skill_commands.py`，理解 `/skill-name` 命令如何被注册成用户消息
4. 读 `tools/skills_hub.py:424`，看 hub source adapter 如何支持 GitHub / ClawHub / LobeHub

### 动手任务

- [ ] 在 `~/.hermes/skills/` 下新建一个两层路径的测试 skill（如 `test/myskill/SKILL.md`），跑 `hermes -z "/myskill say hi"` 验证发现
- [ ] 用 `python -c "from tools.skills_tool import skills_list; print(skills_list())"` 看返回结构

### 今日输出

- 一张 skill 发现与加载流程图
- 200 字笔记：多层路径下 skill name 为什么不含父级目录

---

## Day 5 · Tool Dispatch 与执行

> 核心问题：一次 LLM 返回多个 tool call 时，Hermes 怎么决定串行还是并发？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `agent/tool_executor.py:306` | `execute_tool_calls_concurrent()` | 并发批量执行 |
| `agent/tool_executor.py:965` | `execute_tool_calls_sequential()` | 串行执行 |
| `agent/tool_executor.py:54` | `_budget_for_agent()` | 工具结果预算 |
| `agent/tool_dispatch_helpers.py:104` | `_should_parallelize_tool_batch()` | 并行判定 |
| `agent/tool_dispatch_helpers.py:80` | `_is_destructive_command()` | 破坏性命令启发式 |
| `agent/tool_dispatch_helpers.py:167` | `_paths_overlap()` | 路径独立性检查 |
| `agent/tool_dispatch_helpers.py:361` | `make_tool_result_message()` | 构造 tool result 消息 |
| `tools/registry.py:208` | `ToolRegistry` | 工具自注册表 |
| `tools/registry.py:58` | `discover_builtin_tools()` | 自动发现工具模块 |

### 学习步骤

1. 读 `tools/registry.py`，理解工具如何自注册（模块导入时注册）
2. 读 `agent/tool_dispatch_helpers.py:104`，理解并行判定规则：
   - 是否包含破坏性命令
   - 路径是否重叠
   - provider/工具级别的并发限制
3. 读 `agent/tool_executor.py:306` 和 `:965`，对比并发与串行两条路径
4. 关注 `make_tool_result_message()` 和 `_maybe_wrap_untrusted()` 对 delimiter injection 的防护

### 动手任务

- [ ] 构造一个同时读两个不相关文件的 turn，观察是否被判定为并行
- [ ] 构造一个先读后写同一文件的 turn，观察是否被强制串行
- [ ] 在 `_should_parallelize_tool_batch()` 中加日志，打印判定依据

### 今日输出

- 一张 tool dispatch 决策树
- 200 字笔记：Hermes 为什么不在所有场景下无脑并发

---

## Day 6 · MoA 与 Prompt Caching

> 核心问题：Hermes 如何把 Mixture of Agents 做进 agent loop？prompt caching 又怎么省钱？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `agent/moa_loop.py:571` | `aggregate_moa_context()` | MoA 聚合逻辑 |
| `agent/moa_loop.py:336` | `_run_references_parallel()` | reference 并行执行 |
| `agent/moa_loop.py:220` | `_run_reference()` | 单个 reference 调用 |
| `agent/moa_loop.py:1041` | `MoAClient` | client facade |
| `agent/moa_trace.py:97` | `save_moa_turn()` | trace 持久化 |
| `hermes_cli/moa_cmd.py:79` | `cmd_moa()` | `hermes moa` CLI |
| `hermes_cli/moa_config.py:151` | `normalize_moa_config()` | 配置规范化 |
| `hermes_cli/moa_config.py:11` | `DEFAULT_MOA_PRESET_NAME` | 默认 preset |
| `agent/prompt_caching.py:84` | `apply_anthropic_cache_control()` | cache 标记入口 |
| `agent/prompt_caching.py:15` | `_apply_cache_marker()` | 给消息加 cache_control |

### 学习步骤

1. 读 `hermes_cli/moa_config.py`，理解 preset 结构：references + aggregator
2. 读 `agent/moa_loop.py:571`，看 `aggregate_moa_context()` 如何收集 reference 输出并构造 aggregator prompt
3. 读 `agent/moa_loop.py:336`，看失败隔离（单个 reference 挂了怎么办）
4. 读 `agent/prompt_caching.py:84`，理解 `system_and_3` 策略：
   - system prompt 1 个 breakpoint
   - 历史消息中最多 3 个 breakpoint
   - 为什么压缩前必须冻结 system prompt

### 动手任务

- [ ] 跑 `hermes moa list` 看现有 preset
- [ ] 跑 `hermes -z "explain quantum computing" --provider moa -m default`，抓 trace 输出
- [ ] 在 `apply_anthropic_cache_control()` 中打印每个 breakpoint 的位置

### 今日输出

- 一张 MoA pipeline 图：proposers → aggregator → verdict
- 200 字笔记：prompt caching 与上下文压缩的协同关系

---

## Day 7 · Mid-turn Steering 与全局串讲

> 核心问题：用户如何在 agent 正在跑工具时插话？Hermes 如何保证 role alternation 不被破坏？

### 必读源码

| 文件 | 关键符号 | 说明 |
|---|---|---|
| `run_agent.py:2730` | `steer()` | 接收用户 steer |
| `run_agent.py:2766` | `_drain_pending_steer()` | 取出并清空 pending steer |
| `run_agent.py:3042` | `_apply_pending_steer_to_tool_results()` | 注入 tool results |
| `agent/prompt_builder.py:595` | `format_steer_marker()` | 包装 steer marker |
| `agent/prompt_builder.py:600` | `STEER_CHANNEL_NOTE` | system prompt 中的 steer 说明 |
| `agent/conversation_loop.py` | pre-API-call drain | 四个 drain 点 |

### 学习步骤

1. 读 `run_agent.py:2730`，看 `steer()` 如何用 `threading.Lock` 保护 `_pending_steer`
2. 读 `agent/prompt_builder.py:595`，理解 marker 格式和 `STEER_CHANNEL_NOTE`
3. 读 `agent/conversation_loop.py`，找到 pre-API、tool 批次后、leftover 等 4 个 drain 点
4. 对比仓库已有的 origin 文章 `content/origin/2026-06-11-hermes-steer-deep-dive/index.md`，验证 Codex vs Hermes 的路线差异

### 动手任务

- [ ] 启动一次长任务（如批量文件处理），在运行中发送新消息，观察 steer 被注入到哪一条 tool result
- [ ] 在 `format_steer_marker()` 中打印 steer 文本和最终 marker

### 今日输出

- 一张 steer 注入时序图
- 300 字笔记：Hermes 选择"追加到 tool result"而不是新增 user message 的 trade-off

---

## 每日 Checklist

| 时间 | 任务 | 是否完成 |
|---|---|---|
| 每天开始前 | 读对应 origin 文章（如有），建立预期 | ☐ |
| 每天上午 | 按模块读源码，定位关键函数 | ☐ |
| 每天下午 | 完成一个动手实验 | ☐ |
| 每天结束前 | 写笔记/画图，提交到本地 git | ☐ |

---

## 动手实验清单（整周）

- [ ] **日志埋点**：在 `run_conversation()`、`compress_context()`、`memory_tool()`、`steer()` 加日志，跑一条完整 trace
- [ ] **配置实验**：调整 `context.threshold_percent`，观察压缩触发时机
- [ ] **skill 实验**：手写一个两层路径 skill，测试 `/skill-name` 调用
- [ ] **并发实验**：构造路径相关/无关的 tool batch，验证并行判定
- [ ] **MoA 实验**：跑 `hermes moa configure` 建一个自定义 preset
- [ ] **steer 实验**：长任务运行中插话，观察响应行为

---

## 关键源码索引表

| 主题 | 核心文件 | 关键类/函数 |
|---|---|---|
| 主循环 | `run_agent.py`, `agent/conversation_loop.py` | `AIAgent`, `run_conversation()`, `TurnContext`, `finalize_turn()` |
| 上下文压缩 | `agent/context_engine.py`, `agent/context_compressor.py`, `agent/conversation_compression.py` | `ContextEngine`, `ContextCompressor`, `compress_context()` |
| Memory | `agent/memory_manager.py`, `agent/memory_provider.py`, `tools/memory_tool.py`, `tools/session_search_tool.py` | `MemoryManager`, `MemoryProvider`, `MemoryStore`, `session_search()` |
| Skills | `tools/skills_tool.py`, `agent/skill_commands.py`, `agent/skill_utils.py`, `tools/skills_hub.py` | `skills_list()`, `skill_view()`, `scan_skill_commands()`, `SkillSource` |
| Tool dispatch | `agent/tool_executor.py`, `agent/tool_dispatch_helpers.py`, `tools/registry.py` | `execute_tool_calls_concurrent()`, `_should_parallelize_tool_batch()`, `ToolRegistry` |
| MoA | `agent/moa_loop.py`, `agent/moa_trace.py`, `hermes_cli/moa_config.py` | `aggregate_moa_context()`, `MoAClient`, `normalize_moa_config()` |
| Prompt caching | `agent/prompt_caching.py` | `apply_anthropic_cache_control()` |
| Steering | `run_agent.py`, `agent/prompt_builder.py`, `agent/conversation_loop.py` | `steer()`, `format_steer_marker()`, `STEER_CHANNEL_NOTE` |

---

## 延伸阅读（仓库内已沉淀）

- [Hermes Agent 上下文压缩机制 · 深度拆解](../2026-07-01-hermes-context-compression/index.md)
- [Hermes Agent Skill System 原理深度解析](../2026-06-15-hermes-skill-system/index.md)
- [Hermes 多层 Skills 路径](../2026-07-05-hermes-multilevel-skills/index.md)
- [Steer：让 Agent 边跑边转向](../2026-06-11-hermes-steer-deep-dive/index.md)
- [Mixture of Agents 揭秘：Hermes Agent 让三个模型围坐开会](../2026-07-05-hermes-agent-moa/index.md)
- [Hermes Agent 自进化原理拆解](../2026-06-12-hermes-agent-self-evolution/index.md)

---

## 一周后你应能回答的问题

1. 一次 user turn 从输入到输出的完整数据流是什么？
2. `ContextCompressor` 为什么选择保护头尾、压缩中段？
3. `MEMORY.md` 的读取和写入在生命周期上有什么不同？
4. `skills_list()` 和 `skill_view()` 的 token 成本差异有多大？
5. Hermes 用什么规则决定 tool batch 并行还是串行？
6. MoA 在 Hermes 里为什么被设计成"一个 model"？
7. prompt caching 最多几个 breakpoint？为什么压缩不能破坏 system prompt？
8. `steer()` 为什么不新增一条 user message，而是追加到 tool result？

---

*本计划基于 Hermes Agent 代码仓 2026-07 快照制定。源码行号可能随版本漂移，建议结合当前代码验证。*
