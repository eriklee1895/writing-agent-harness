# Skill System 原理与实现深度分析

本文档从架构设计、加载机制、触发匹配、执行模型等角度深入分析 Hermes Agent / Claude Code / Codex 的 Skill System 原理。

**日期:** 2026-06-13  
**基于:** writing-agent-harness 项目实践与源码分析

---

## 目录

1. [Skill System 架构设计](#skill-system-架构设计)
2. [Skill 加载与发现机制](#skill-加载与发现机制)
3. [触发语义匹配原理](#触发语义匹配原理)
4. [Skill 执行模型](#skill-执行模型)
5. [元数据与依赖管理](#元数据与依赖管理)
6. [多 Agent 兼容性设计](#多-agent-兼容性设计)
7. [演进路径与设计决策](#演进路径与设计决策)

---

## Skill System 架构设计

### 核心理念

Skill System 采用"约定优于配置"的设计哲学，通过标准化的目录结构和文件格式实现跨 Agent 兼容。

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Codex      │  │ Claude Code  │  │  Hermes Agent    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼──────────────────┼───────────────────┼────────────┘
          │                  │                   │
          ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Skill Runtime Layer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Skill Loader  │  Trigger Matcher  │  Executor         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                  │                   │
          ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Skill Storage Layer                        │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │  User-level      │  │     Project-level               │  │
│  │  ~/.agents/      │  │  .agents/skills/                │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **约定优于配置**: 标准目录结构、标准文件命名、标准 frontmatter 格式
2. **分层设计**: Storage → Runtime → Agent，每层职责清晰
3. **向后兼容**: 旧格式的 skill 仍然可以加载
4. **渐进式增强**: 可以从简单的 `SKILL.md` 开始，逐步添加脚本和参考资料

---

## Skill 加载与发现机制

### 发现路径

Agent 按以下顺序搜索 skills：

```
1. 项目级: .agents/skills/
2. 用户级: ~/.agents/skills/
3. 用户级: ~/.codex/skills/ (Codex 兼容)
4. 内置: 随 Agent 预装的 skills
```

### 目录遍历算法

伪代码：

```python
def discover_skills(search_paths):
    skills = {}
    for path in search_paths:
        if not exists(path):
            continue
        for skill_dir in listdir(path):
            skill_path = join(path, skill_dir)
            if isdir(skill_path) and exists(join(skill_path, "SKILL.md")):
                skill = load_skill(skill_path)
                if skill.name not in skills:  # 先发现的优先级高
                    skills[skill.name] = skill
    return skills

def load_skill(skill_dir):
    skill_md = join(skill_dir, "SKILL.md")
    frontmatter, content = parse_skill_md(skill_md)
    return Skill(
        name=frontmatter["name"],
        description=frontmatter.get("description", ""),
        metadata=frontmatter.get("metadata", {}),
        content=content,
        dir=skill_dir,
        # 延迟加载其他资源
    )
```

### SKILL.md 解析

`SKILL.md` 使用 YAML frontmatter + Markdown 正文的双段格式：

```
┌─────────────────────────────────┐
│  ---                            │  ← YAML frontmatter 开始
│  name: article-ideation         │
│  description: "..."             │
│  metadata:                      │
│    requires:                    │
│      skills: ["..."]            │
│  ---                            │  ← YAML frontmatter 结束
│                                 │
│  # Article Ideation             │  ← Markdown 正文开始
│  ...                            │
└─────────────────────────────────┘
```

解析过程：

1. 读取文件内容
2. 分割 frontmatter 和正文：寻找 `---` 分隔符
3. 解析 YAML frontmatter
4. 保留 Markdown 正文供 Agent 阅读

---

## 触发语义匹配原理

### 触发描述格式

触发语义在 `SKILL.md` 的 frontmatter `description` 字段中定义，采用混合语言格式：

```yaml
description: |
  中文触发语义：用户说什么关键词时触发。
  更多中文说明。
  Use when: user says X, Y, or Z; or provides A, B, C.
  Do not use when: situation P, Q, R; use another-skill instead.
```

### 匹配策略（推测）

基于观察，Agent 可能采用以下匹配策略：

```
输入用户消息
    │
    ▼
┌─────────────────────────────────────┐
│  预处理: 分词、去停用词             │
└──────────────────┬──────────────────┘
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
┌───────────┐  语义相似度   ┌───────────────┐
│  关键词   │──────────────▶│   LLM 判断    │
│  匹配     │               │  (更智能)     │
└───────────┘               └───────┬───────┘
                                   │
                          ┌────────▼────────┐
                          │  合并候选集    │
                          │  排序+去重     │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  选择 top N    │
                          │  供用户确认    │
                          └─────────────────┘
```

### writing-agent-harness 的触发示例

| Skill | 触发关键词示例 |
|-------|---------------|
| `article-ideation` | "我想写一篇"、"有个想法"、"帮我理一下"、"脑暴"、"选题"、"文章思路"、"outline" |
| `polish-article` | "润色"、"打磨"、"改改"、"提升文笔" |
| `wechat-article-renderer` | "排版"、"美化"、"生成预览"、"微信公众号" |
| `markdown-article-to-lark-doc` | "发到飞书"、"转写到飞书"、"这篇要发飞书" |

---

## Skill 执行模型

### Skill 调用流程

```
用户请求
    │
    ▼
┌─────────────────────────────────┐
│  1. 触发匹配                    │
│     识别应该调用哪个 skill      │
└──────────────┬──────────────────┘
               │
    ┌──────────▼──────────┐
    │  2. 前置检查        │
    │     - 依赖检查      │
    │     - 权限检查      │
    │     - 环境检查      │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  3. 加载 Skill      │
    │     读取 SKILL.md   │
    │     理解能力边界    │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  4. 执行 Workflow   │
    │     - 读参考资料    │
    │     - 运行脚本      │
    │     - 调用工具      │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  5. 结果处理        │
    │     - 输出给用户    │
    │     - 移交下一个    │
    │       skill         │
    └─────────────────────┘
```

### 路径变量：`{baseDir}`

Skill 可以在文档中使用 `{baseDir}` 引用 skill 目录：

```markdown
node {baseDir}/scripts/render-wechat-article.mjs /path/to/article.md
```

运行时替换为：

```
node /path/to/project/.agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs /path/to/article.md
```

### 脚本执行环境

- **工作目录**: 通常是项目根目录
- **PATH**: 包含系统 PATH 和可能的 Node/Python 虚拟环境
- **环境变量**: 继承用户环境，加上项目 `.env`（如果有）

---

## 元数据与依赖管理

### metadata 结构

```yaml
metadata:
  requires:
    bins: ["node", "uv", "lark-cli"]      # 依赖的二进制工具
    skills: ["lark-doc", "lark-shared"]   # 依赖的其他 skills
    env: ["OPENAI_API_KEY", "LARK_TOKEN"] # 依赖的环境变量
    files: ["config.json"]                # 依赖的文件
  permissions:
    network: true             # 是否需要网络访问
    filesystem: "read-write"  # 文件系统权限: "read" | "read-write" | "none"
    browser: false            # 是否需要浏览器控制
  resource:
    cpu: "low"                # CPU 需求: "low" | "medium" | "high"
    memory: "medium"          # 内存需求
```

### 依赖检查流程

```python
def check_dependencies(skill):
    # 检查二进制工具
    for bin in skill.metadata.get("requires", {}).get("bins", []):
        if not find_in_path(bin):
            return Failure(f"Missing required binary: {bin}")

    # 检查依赖的 skills
    for skill_name in skill.metadata.get("requires", {}).get("skills", []):
        if not skill_loaded(skill_name):
            return Failure(f"Missing required skill: {skill_name}")

    # 检查环境变量
    for env in skill.metadata.get("requires", {}).get("env", []):
        if env not in os.environ:
            return Failure(f"Missing required env var: {env}")

    return Success()
```

---

## 多 Agent 兼容性设计

### agents/ 目录的作用

```
skill-name/
├── SKILL.md
├── agents/
│   ├── claude/          ← Claude Code 特定配置
│   │   ├── config.json
│   │   └── ...
│   ├── codex/           ← Codex 特定配置
│   │   ├── manifest.json
│   │   └── ...
│   └── hermes/          ← Hermes Agent 特定配置
│       └── ...
└── ...
```

这种设计允许：

- 核心逻辑共享（`SKILL.md`、`scripts/`）
- Agent 特定配置分离（`agents/<agent>/`）
- 渐进式支持新 Agent

### 兼容层实现（概念）

```python
class Skill:
    def __init__(self, dir):
        self.dir = dir
        self.core = self.load_core()
        self.agent_config = self.load_agent_config()

    def load_core(self):
        return parse_skill_md(join(self.dir, "SKILL.md"))

    def load_agent_config(self):
        agent_name = current_agent_name()  # "claude", "codex", "hermes"
        config_path = join(self.dir, "agents", agent_name)
        if exists(config_path):
            return load_config(config_path)
        return {}
```

---

## 演进路径与设计决策

### 从文档到 Skill 的演进

writing-agent-harness 采用渐进式演进策略：

```
阶段 1: 文档记录
    ↓
    记录 workflow 步骤、检查清单
    用户手动按步骤执行

阶段 2: 脚本自动化
    ↓
    把重复步骤写成脚本
    文档说明如何调用脚本

阶段 3: 封装为 Skill
    ↓
    添加 SKILL.md
    定义触发语义
    Agent 可以自动调用
```

### 关键设计决策

#### 决策 1: Markdown 优先，代码可选

**原因**:
- 降低入门门槛：一个 `SKILL.md` 就是一个 skill
- 人类可读：Agent 和人都能理解 skill 做什么
- 渐进式增强：可以先写文档，再逐步添加脚本

**对比**:

| 方案 | 优点 | 缺点 |
|------|------|------|
| 纯 Markdown | 简单、易读 | 自动化能力有限 |
| 纯代码 | 自动化强 | 难理解、难维护 |
| **Markdown + 可选代码** | **平衡灵活** | **需要约定** | ← 选择

#### 决策 2: Project-level 与 User-level 分离

**原因**:
- 项目特定能力随项目走
- 通用能力不重复安装
- Secrets 和个人配置不进入 Git

**边界划分**:

| 能力类型 | 位置 | 示例 |
|---------|------|------|
| 项目特定 | `.agents/skills/` | 微信发布、项目排版 |
| 全局通用 | `~/.agents/skills/` | 搜索、图片生成 |
| 个人配置 | `~/.agents/config/` | API keys、偏好 |

#### 决策 3: 软链接 vs 直接识别

**演变**:

```
早期: 需要软链接
    .agents/skills/ → claude/skills/

现在: 直接识别
    Claude Code 原生支持 .agents/skills/
```

**向后兼容**: 软链接方式仍然支持。

#### 决策 4: 不使用付费 md2wechat API

**原因**:
- 成本考虑
- 可控性：自己的 renderer 可以完全控制样式
- 可定制：可以根据项目需求调整

---

## 附录：Skill System 与类似系统对比

### 与 GitHub Actions 对比

| 特性 | Skill System | GitHub Actions |
|------|-------------|----------------|
| **定位** | Agent 能力扩展 | CI/CD 自动化 |
| **触发** | 自然语言匹配 | 事件（push、PR、schedule） |
| **执行环境** | 本地机器 | 云端 Runner |
| **配置语言** | Markdown + YAML frontmatter | YAML |
| **交互性** | 高（与用户对话） | 低（主要是日志） |

### 与 npm 包对比

| 特性 | Skill System | npm |
|------|-------------|-----|
| **定位** | Agent 能力模块 | JavaScript 库 |
| **分发** | Git 或 `npx skills` | npm registry |
| **依赖** | `metadata.requires.skills` | `package.json` dependencies |
| **执行** | Agent 调用 | `node require()` |
| **文档** | `SKILL.md`（同时是代码） | `README.md`（独立文档） |

---

## 总结

Skill System 的设计体现了以下智慧：

1. **简单性**: 从一个 `SKILL.md` 文件开始
2. **灵活性**: 可以逐步添加脚本和参考资料
3. **兼容性**: 支持多个 Agent 环境
4. **实用性**: 解决真实的自动化需求

writing-agent-harness 项目通过 Skill System 成功把写作、排版、发布等工作流变成可重复、可共享的能力模块。
