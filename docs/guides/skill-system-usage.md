# Skill System 使用指南

本文档详细说明如何配置、使用和管理 Hermes Agent / Claude Code / Codex 的 Skill System，包括全局级（user-level）和项目级（project-level）skills 的配置方式、目录结构、复用机制和最佳实践。

**日期:** 2026-06-13  
**基于:** writing-agent-harness 项目实践

---

## 目录

1. [Skill System 概述](#skill-system-概述)
2. [Skill 层级结构](#skill-层级结构)
3. [项目级 Skills 配置](#项目级-skills-配置)
4. [全局级 Skills 配置](#全局级-skills-配置)
5. [Skill 目录结构规范](#skill-目录结构规范)
6. [Skill 复用与共享](#skill-复用与共享)
7. [Skill 创建与开发](#skill-创建与开发)
8. [常见问题与最佳实践](#常见问题与最佳实践)

---

## Skill System 概述

Skill System 是 Agent 的可执行能力层，它把可重复的工作流、检查清单、工具脚本和触发语义封装成独立模块。Skills 可以被 Agent 自动识别和调用，也可以由用户显式触发。

### 核心概念

| 概念 | 说明 |
|------|------|
| **Skill** | 独立的能力模块，包含描述、触发条件、实现代码和参考资料 |
| **Project-level Skills** | 随项目仓库提交的 skills，位于 `.agents/skills/` |
| **User-level Skills** | 用户全局安装的 skills，位于 `~/.agents/skills/` 或 `~/.codex/skills/` |
| **Trigger** | Skill 的触发语义，在 `SKILL.md` 的 frontmatter `description` 中定义 |
| **Metadata** | Skill 的元数据，包括依赖、权限要求等 |

### 支持的 Agent 环境

- **Codex**: 原生支持 `.agents/skills/` 目录
- **Claude Code**: 通过软链接或直接识别 `.agents/skills/`
- **Hermes Agent**: 兼容相同的 skill 结构

---

## Skill 层级结构

Skills 按作用范围分为两个层级，形成互补关系：

```
~/.agents/skills/                    (User-level, 全局通用)
├── tavily-search/
├── imagegen/
├── lark-doc/
└── ...

/path/to/project/.agents/skills/    (Project-level, 项目特定)
├── article-ideation/
├── wechat-article-renderer/
├── polish-article/
└── ...
```

### 层级对比

| 维度 | Project-level Skills | User-level Skills |
|------|---------------------|------------------|
| **位置** | `.agents/skills/` | `~/.agents/skills/` 或 `~/.codex/skills/` |
| **Git 跟踪** | ✅ 是，随项目提交 | ❌ 否，本机配置 |
| **适用范围** | 特定项目 | 所有项目 |
| **示例** | 微信发布、项目特定排版 | 通用搜索、图片生成、飞书文档 |
| **共享方式** | 随 repo clone | `npx skills add` 或手动安装 |

### 加载优先级

当同名 skill 存在时，通常按以下优先级加载（具体取决于 Agent 实现）：

1. Project-level skills (`.agents/skills/`)
2. User-level skills (`~/.agents/skills/`)
3. Built-in skills

---

## 项目级 Skills 配置

项目级 skills 是 writing-agent-harness 的稳定能力边界，随仓库一起版本控制。

### 目录位置

```
your-project/
├── .agents/
│   └── skills/              ← 项目级 skills 目录
│       ├── article-ideation/
│       ├── polish-article/
│       └── ...
├── docs/
├── content/
└── ...
```

### Claude Code 软链接配置（如需要）

根据现有文档，Claude Code 可以通过软链接复用 skills：

```bash
# 在项目根目录执行
mkdir -p claude
ln -s ../.agents/skills claude/skills
```

验证软链接：

```bash
ls -la claude/
# 输出应包含:
# skills -> ../.agents/skills
```

> **注意:** 现代 Claude Code 版本通常能直接识别 `.agents/skills/` 目录，软链接可能不是必需的。

### Git 配置

`.agents/skills/` 目录应该被 Git 跟踪：

```gitignore
# .gitignore 中不应排除 .agents/skills/
# 但应排除临时文件:
.agents/skills/*.zip
.baoyu-skills/
skills-lock.json
```

确认 skills 被跟踪：

```bash
git check-ignore -v .agents/skills/article-ideation/SKILL.md
# 无输出表示未被忽略
```

### 从仓库安装项目 Skills

用户可以通过 `npx skills` 安装你的项目 skills：

```bash
# 安装所有 skills
npx skills add eriklee1895/writing-agent-harness

# 只安装指定 skill
npx skills add eriklee1895/writing-agent-harness --skill article-ideation
```

---

## 全局级 Skills 配置

全局级 skills 用于跨项目的通用能力，不进入项目 Git。

### 安装位置

```bash
# 标准位置
~/.agents/skills/

# Codex 用户也可能使用
~/.codex/skills/
```

如果目录不存在，创建它：

```bash
mkdir -p ~/.agents/skills
```

### 安装全局 Skills

#### 方式 1: 使用 `npx skills`

```bash
# 从 GitHub 安装
npx skills add username/repo

# 示例
npx skills add tavily/tavily-search
```

#### 方式 2: 手动创建

```bash
cd ~/.agents/skills
mkdir my-custom-skill
cd my-custom-skill
touch SKILL.md
# 编辑 SKILL.md...
```

#### 方式 3: 软链接到项目 Skills（不推荐）

如果你想在多个项目间共享某个 skill，可以软链接：

```bash
cd ~/.agents/skills
ln -s /path/to/project/.agents/skills/shared-skill shared-skill
```

> **注意:** 软链接的 skill 在项目外可能无法正常工作，因为它可能依赖项目特定的路径或资源。

### 常用全局 Skills 示例

根据 writing-agent-harness 实践，推荐以下全局 skills：

| Skill | 用途 | 来源 |
|-------|------|------|
| `tavily-search` | Web 搜索、事实查证 | tavily/tavily-search |
| `gpt-image-2` / `seedream-image-gen` | AIGC 位图生成（gpt-image-2 文字渲染 SOTA；seedream 中文/东亚场景） | eriklee1895/erik-agent-skills |
| `seedance-video-gen` | Seedance 2.0 视频生成 | eriklee1895/erik-agent-skills |
| `volcengine-tts` / `seed-audio-gen` / `volcengine-bigmusic-bgm` | 语音合成 / 生成式音频场景 / 无人声配乐 | eriklee1895/erik-agent-skills |
| `markdown-article-to-feishu-doc` | Markdown 转写飞书云文档 | eriklee1895/erik-agent-skills |
| `volcengine-doc-fetcher` | 火山引擎文档抓取 | eriklee1895/erik-agent-skills |
| `lark-doc` | 飞书文档操作 | larksuite/cli |
| `lark-markdown` | 飞书 Markdown 处理 | larksuite/cli |
| `skill-creator` | 创建新 skills | 内置 |

---

## Skill 目录结构规范

每个 skill 应该有清晰的目录结构，以下是 writing-agent-harness 采用的规范。

### 最小结构（简单 Skill）

```
skill-name/
└── SKILL.md                 ← 唯一必需文件
```

### 完整结构（复杂 Skill）

```
skill-name/
├── SKILL.md                 ← Skill 定义（必需）
├── README.md                ← 可选：人类可读文档
├── agents/                  ← Agent 特定配置
│   ├── claude/
│   │   └── ...
│   └── codex/
│       └── ...
├── scripts/                 ← 可执行脚本
│   ├── main.py
│   ├── helper.sh
│   └── ...
├── references/              ← 参考资料
│   ├── style-guide.md
│   ├── api-docs.md
│   └── ...
├── tests/                   ← 测试（可选）
│   ├── test_basic.py
│   └── ...
└── assets/                  ← 静态资源（可选，谨慎提交）
    ├── templates/
    └── ...
```

### `SKILL.md` 格式规范

`SKILL.md` 是 skill 的核心定义文件，使用 YAML frontmatter + Markdown 正文。

#### 基本模板

```markdown
---
name: skill-name
description: |
  一句话描述这个 skill 做什么。
  详细说明触发条件：用户说什么关键词时触发、不触发什么情况。
  Use when: 清晰的英文触发描述（便于跨平台兼容）。
  Do not use when: 什么时候不应该用这个 skill。
metadata:
  requires:
    bins: ["node", "uv"]      # 依赖的二进制工具
    skills: ["lark-doc"]      # 依赖的其他 skills
    env: ["OPENAI_API_KEY"]   # 依赖的环境变量
  permissions:
    network: true             # 是否需要网络
    filesystem: "read-write"  # 文件系统权限
---

# Skill 标题

## Overview

简要概述这个 skill 的能力和目标。

## When To Use

清晰说明什么时候使用这个 skill：

- 用户说什么关键词
- 什么输入场景
- 与其他 skill 的分工边界

## When NOT To Use

明确说明什么时候不应该用这个 skill（避免误用）：

- 什么场景应该用另一个 skill
- 什么情况超出范围

## Workflow

详细描述执行流程：

```
步骤 1 → 步骤 2 → 步骤 3
```

### 1. 第一步

```bash
命令示例
```

### 2. 第二步

说明和代码示例。

## Examples

给出 1-3 个实际使用示例。

## Boundaries

明确 skill 的能力边界：

- ✅ 做什么
- ❌ 不做什么

## Troubleshooting

常见问题排查指南。
```

#### 真实示例：`article-ideation`

```markdown
---
name: article-ideation
description: "把模糊写作灵感打磨成清晰 writing brief 和 outline。Use whenever the user says 我想写一篇/有个想法/帮我理一下/脑暴/选题/文章思路/outline, or provides rough notes before drafting. This skill should run before research/draft/polish when the article angle, thesis, target reader, or structure is not yet clear."
---

# Article Ideation

## Overview

这个 skill 用于写作最早期：把用户的灵感、零散素材、情绪判断或模糊选题，变成可执行的 `writing brief`、`research questions` 和初版 `outline`。

## When To Use

Use this skill before drafting when:
- 用户说"我想写一篇……""我有个想法""帮我理一下思路"
- 用户给了灵感、素材、链接、截图或几段想法，但还没有清晰 thesis
- 文章的 target reader、angle、tone、distribution channel 还不明确

## Workflow

### 1. Restate The Spark

先用自己的话复述用户的灵感，确认理解一致。

### 2. Calibrate The Article

围绕这些维度脑暴和校准：
- `central question`: 这篇文章要回答什么问题？
- `target reader`: 写给谁？
- `thesis`: 作者最想表达的判断是什么？
- ...
```

#### 真实示例：`markdown-article-to-feishu-doc`（带 metadata）

```markdown
---
name: markdown-article-to-feishu-doc
description: |
  把一篇本地 markdown 文档转写成飞书云文档(docx),排版精美、block 结构完整。
  触发:用户说"把 markdown 发到飞书"/"转写到飞书"/"这篇要发飞书";或给了本地 .md 路径。
metadata:
  requires:
    bins: ["lark-cli"]
    skills: ["lark-doc", "lark-whiteboard", "lark-shared"]
---

# markdown-article-to-feishu-doc

把本地 markdown 文章转写成飞书云文档(docx)，保留 frontmatter 元信息、本地图片、Mermaid 图。

## 流程(Code-Act Loop)

```
                preprocess.py
markdown ─────────────────────────► 处理后 markdown + image manifest + title
   │
   ▼
lark-cli docs +create  (空骨架)
   │
   ▼
...
```
```

### `scripts/` 目录约定

- 脚本应该有执行权限：`chmod +x scripts/*.py`
- 使用项目相对路径，不要硬编码绝对路径
- Python 脚本统一使用 `uv run` 执行
- Node.js 脚本直接用 `node` 执行

示例：

```bash
# Python 脚本
uv run scripts/generate_illustration.py --input article.md

# Node.js 脚本
node scripts/render-wechat-article.mjs article.md

# Shell 脚本
bash scripts/precheck.sh
```

### `references/` 目录约定

存放辅助资料，不影响 skill 核心功能：

- 样式指南
- API 文档
- 安装指引
- 支持的语法清单
- 配置示例

---

## Skill 复用与共享

### 项目内 Skill 依赖

一个 skill 可以依赖另一个 skill，在 `metadata.requires.skills` 中声明：

```yaml
metadata:
  requires:
    skills: ["lark-doc", "lark-whiteboard"]
```

在 `SKILL.md` 正文中明确说明委派关系：

```markdown
## 委派关系

- [`lark-doc`](https://github.com/larksuite/cli): docx 创建/更新/fetch/媒体插入
- [`lark-whiteboard`](https://github.com/larksuite/cli): Mermaid 画板处理
```

### 跨项目复用 Skills

#### 方式 1: 通过 Git 子模块（不推荐）

```bash
git submodule add https://github.com/username/shared-skills.git .shared-skills
ln -s ../../.shared-skills/skill-name .agents/skills/skill-name
```

#### 方式 2: 通过 `npx skills`（推荐）

在新环境中安装：

```bash
npx skills add eriklee1895/writing-agent-harness --skill article-ideation
```

#### 方式 3: 手动复制（简单但难同步）

```bash
cp -r ~/project-a/.agents/skills/shared-skill ~/.agents/skills/
# 或
cp -r ~/.agents/skills/shared-skill ~/project-b/.agents/skills/
```

### Skill 版本管理

- Skills 随项目一起版本控制
- 重大变更应该在 Git commit message 中说明
- 可以在 `SKILL.md` 中添加变更日志

---

## Skill 创建与开发

### 什么时候应该创建新 Skill

适合 skill 化的信号：

- ✅ 同类任务预计会重复出现 3 次以上
- ✅ 任务有明确触发语义
- ✅ 已经形成稳定 checklist、输入输出、命令或脚本
- ✅ 只靠文档容易漏步骤，封装成 skill 能显著降低出错率
- ✅ 现有 skill 名称、描述或边界已经承载不下这个能力

不适合 skill 化的情况：

- ❌ 只是一次性偏好或单篇文章特殊处理
- ❌ 规则还没跑通，仍在探索
- ❌ 只是需要在现有 workflow 文档里补一句
- ❌ 可以通过扩展现有 skill 更自然地解决

### 创建新 Skill 步骤

#### 1. 使用 `skill-creator`（如果可用）

```bash
# 调用 skill-creator skill
```

#### 2. 手动创建

```bash
cd .agents/skills
mkdir my-new-skill
cd my-new-skill
touch SKILL.md

# 可选：创建常用子目录
mkdir -p scripts references agents
```

#### 3. 编写 `SKILL.md`

从前文的模板开始，确保：

- `name` 是小写、用连字符分隔
- `description` 包含清晰的中英文触发语义
- 明确说明适用/不适用场景
- 给出可执行的 workflow

#### 4. 添加实现（如需要）

```bash
# 添加脚本
touch scripts/main.py
chmod +x scripts/main.py

# 编辑脚本...
```

#### 5. 本地测试

```bash
# 手动运行脚本测试
uv run scripts/main.py --help

# 或通过 Agent 调用测试
```

#### 6. 更新文档

- 如果是核心 skill，更新 `docs/skills/skills-list.md`
- 添加使用示例到相关 workflow 文档

### Skill 演进规则

当发现 skill 可以优化时：

1. 先判断是文档问题、触发描述问题、workflow 问题，还是脚本实现问题
2. 小修直接改对应 `SKILL.md` 或 reference
3. 影响行为的脚本改动必须运行最小验证
4. 如果是新能力，优先扩展现有 skill；只有边界清晰且复用价值高时，才创建新 skill
5. 保留用户偏好和真实坑点原文

---

## 常见问题与最佳实践

### 常见问题

#### Q: 我的 skill 没有被 Agent 识别？

检查清单：

- [ ] `SKILL.md` 存在于正确位置：`.agents/skills/<skill-name>/SKILL.md`
- [ ] `SKILL.md` 有正确的 YAML frontmatter
- [ ] `name` 字段正确填写
- [ ] 文件权限正常可读
- [ ] 重启 Agent 试试

#### Q: 如何让 skill 同时支持 Codex 和 Claude Code？

- 保持标准的 `SKILL.md` 结构
- 在 `agents/` 子目录中存放特定平台的配置
- 脚本使用跨平台兼容的路径处理

#### Q: 应该把 secrets 放在哪里？

- ❌ 不要放在 `SKILL.md` 或脚本里
- ❌ 不要提交到 Git
- ✅ 放在项目 `.env` 文件（添加到 `.gitignore`）
- ✅ 放在用户环境变量
- ✅ 在 `metadata.requires.env` 中声明需要的环境变量

#### Q: 如何处理 skill 之间的依赖？

- 在 `metadata.requires.skills` 中声明
- 在 `SKILL.md` 正文中明确说明委派关系
- 提供 precheck 脚本验证依赖是否安装

### 最佳实践

#### 1. Skill 命名

- 使用小写字母和连字符：`article-ideation`，不是 `ArticleIdeation` 或 `article_ideation`
- 名称要语义化，不要用代号
- 用名词短语：`wechat-article-renderer`，不是 `render-wechat`

#### 2. 描述撰写

- 同时包含中文和英文触发描述
- 明确说明 "Use when" 和 "Do not use when"
- 给出具体的用户说法示例

#### 3. 脚本编写

- Python 脚本统一用 `uv run`
- Node.js 脚本直接用 `node`
- 使用相对路径，不要硬编码绝对路径
- 在脚本开头添加 shebang 和说明注释
- 提供 `--help` 输出

#### 4. Git 提交

- ✅ 提交 `SKILL.md`、脚本、参考资料
- ✅ 提交 `references/` 下的文档
- ❌ 不要提交 secrets、API keys
- ❌ 不要提交临时文件、构建产物
- ❌ 不要提交大的二进制资源（放 `.local-archive/`）

#### 5. 文档维护

- 每个 skill 自己的 `SKILL.md` 是权威文档
- 项目级 skill 列表在 `docs/skills/skills-list.md` 维护
- Workflow 文档说明 skill 之间的配合

#### 6. 渐进式演进

```
临时想法 → 文档记录 → 改进现有 skill → 创建新 project skill
```

不要过早优化，先跑通几次再沉淀。

---

## 附录

### A. writing-agent-harness 核心 Skills 列表

| Skill | 用途 |
|-------|------|
| `article-ideation` | 把模糊写作灵感打磨成清晰 writing brief 和 outline |
| `polish-article` | 润色和打磨文章写作 |
| `article-readiness-check` | 发布前文章 readiness 检查 |
| `writing-task-closeout` | 写作任务发布后 closeout |
| `wechat-article-renderer` | 从 Markdown 生成微信公众号 HTML preview |
| `wechat-publish-workflow` | 端到端微信公众号发布 runbook |
| `wechat-article-fetcher` | 提取微信公众号文章到结构化 Markdown |
| `wechat-article-publisher` | Playwright 微信公众号发布器 |
| `article-illustration` | 生成文章封面、正文插图 |
| `article-to-notion` | 网页文章（微信/博客/arXiv）抓取、清洗并剪藏到 Notion page/database |
| `notion-cli` | 封装官方 ntn CLI 的 Notion 读写基础 skill（create/read/upload/set-properties 等） |
| `volcengine-web-search` | 火山引擎联网搜索（网页/图片），中文内容与国内信息研究查证 |

### B. 目录速查表

```
项目根目录/
├── .agents/
│   └── skills/              ← 项目级 skills（Git 跟踪）
│       ├── skill-a/
│       │   ├── SKILL.md
│       │   ├── scripts/
│       │   └── references/
│       └── skill-b/
├── docs/
│   ├── skills/
│   │   ├── skills-list.md    ← 项目 skills 列表（canonical）
│   │   └── skills-guide.md   ← Skill 开发规范
│   └── guides/
│       └── skill-system-usage.md  ← 本文档
├── .local-memory/           ← 本机临时记忆（不提交）
├── .local-archive/          ← 本机归档（不提交）
└── ...

用户目录/
└── .agents/
    └── skills/              ← 全局级 skills（不提交）
        ├── skill-x/
        └── skill-y/
```

### C. 相关文档

- [AGENTS.md](../../AGENTS.md) - 项目高频规则和文档路由
- [skills-list.md](../skills/skills-list.md) - 项目级 skills 列表
- [self-evolution.md](../reference/self-evolution.md) - Skill 演进规则
- [prepare-environment.md](../project/prepare-environment.md) - 新环境准备指南
- [directory-layout.md](../project/directory-layout.md) - 项目目录布局规范

---

**文档维护**: 每次新增或修改 skill 后，考虑更新本文档的相关部分。
