# Skill 开发指南

本项目 skills 的开发和维护规范。这些规则来自实际踩坑经验，确保 skills 在不同机器、不同 runtime 下都能正常工作。

## Python 脚本规范

项目 skill 中的 Python 脚本必须使用 PEP 723 inline metadata 自声明依赖：

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
```

- **shebang**：`#!/usr/bin/env -S uv run`（不含绝对路径、不含 `--script`）
- **requires-python**：`>=3.12`
- **调用方式**：`uv run scripts/xxx.py`（不加中间 `python`，不加绝对路径）
- **新建脚本**：从 [`template/script.py`](../../template/script.py) 复制模板
- **测试文件**（`test_*.py`）：不走 PEP 723，继续用项目 `pyproject.toml` dev dependency
- **Playwright 脚本**：加 PEP 723 声明 `playwright`，但 SKILL.md 需注明 `playwright install` 系统依赖

### 为什么用 PEP 723

- `uv run script.py` 自动创建隔离环境，只用脚本声明的依赖，忽略项目 `pyproject.toml`
- 不管在哪里运行（本机、另一台机器、CI），只要有 uv 就能跑
- 不污染系统 Python 环境，不依赖 pip/poetry

## 路径引用规范

在 SKILL.md 中引用脚本、文档等文件时，**必须使用相对 SKILL.md 的路径**：

```markdown
## Quick start

```bash
uv run scripts/search.py "query" --json
```

See [the reference guide](references/setup.md) for details.
```

- ✅ `scripts/search.py`
- ✅ `references/xxx.md`
- ❌ `~/.claude/skills/volcengine-web-search/scripts/search.py`（依赖本机 symlink 结构）
- ❌ `.agents/skills/volcengine-web-search/scripts/search.py`（绑定安装层级）
- ❌ `/absolute/path/to/scripts/search.py`（不可移植）
- ❌ `${CLAUDE_SKILL_DIR}/scripts/search.py`（绑定特定 runtime）

**注意**：`references/` 子目录下的文档引用脚本时，路径基准同样是 **skill root**（SKILL.md 所在目录），不是 references 目录自身。例如 `references/sample-prompts.md` 中应写 `scripts/xxx.py`，而非 `../scripts/xxx.py`。

### 依据

[Agent Skills 开放标准](https://agentskills.io/specification)明确规定：

> When referencing other files in your skill, use relative paths from the skill root.

[Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) 进一步说明：

> script execution paths (in code blocks) are relative to the **skill directory root**, because the agent runs commands from there.

## 脚本接口设计

Agent 通过读取 stdout/stderr 和 `--help` 输出来理解脚本接口。以下规则让脚本对 agent 更友好：

### --help

`--help` 是 agent 自学脚本接口的主要途径。包含：

- 简要描述
- 所有可用 flag
- 用法示例
- 错误码说明（如适用）

### --json 结构化输出

提供 `--json` flag 输出结构化 JSON，agent 可编程解析。默认输出保持人类友好。

### 避免交互式 prompt

Agent 在非交互 shell 中运行，无法响应 TTY prompt。所有输入通过 CLI flag、环境变量或 stdin 传递。

```
# Bad: 会 hang 住
$ python scripts/deploy.py
Target environment: _

# Good: 明确的错误提示
$ python scripts/deploy.py
Error: --env is required. Options: development, staging, production.
```

### stdout vs stderr

- **stdout**：数据输出（结构化 JSON 或格式化文本）
- **stderr**：诊断信息、进度提示、警告

### 错误信息

错误信息要具体——说明什么错了、期望什么、怎么修正：

```
Error: --format must be one of: json, csv, table.
       Received: "xml"
```

不要写 `Error: invalid input` 这种无信息量的提示。

## SKILL.md 写作原则

### 给默认值，不给菜单

多个工具或方案可选时，选一个默认，备选简单提一句，不要罗列成等价的菜单：

```markdown
<!-- ❌ 选项太多，agent 需要额外决策 -->
你可以用 pypdf、pdfplumber、PyMuPDF、pdf2image 来提取 PDF 文本...

<!-- ✅ 明确默认，备选只在必要时提及 -->
使用 pdfplumber 提取文本。扫描件用 pdf2image + pytesseract。
```

### Gotchas：记录反直觉的坑

当 agent 踩坑后，把纠正加入 SKILL.md 的 Gotchas 段。这是 skill 中价值最高的内容——不是通用建议，而是对 agent 会犯的错误的提前纠正：

```markdown
## Gotchas

- `users` 表使用软删除，查询必须加 `WHERE deleted_at IS NULL`。
- 用户 ID 在数据库是 `user_id`，在认证服务是 `uid`，在计费 API 是 `accountId`——三者是同一个值。
- `/health` 返回 200 只代表 web server 在跑，不代表数据库通。用 `/ready` 检查全链路。
```


## 现有 Skills 列表

项目级 skills 完整列表见 [skills-list.md](skills-list.md)。

## 参考

- [Agent Skills Specification](https://agentskills.io/specification)
- [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts)
- [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices)
- [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
- [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
