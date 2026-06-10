# Self Evolution

这个 repo 是 Erik 个人高度定制的 `writing-agent-harness`。每一次真实写作、发布、调试和复盘，都应该让 harness 变强一点。

目标不是制造沉重流程，而是把可复用经验及时沉淀成项目 docs、memory 或 project-level skills。

## When To Update

遇到以下情况时，优先考虑更新 repo memory：

- 发现新的渠道限制、平台报错、发布坑点。
- 某个 workflow 跑通了新的步骤，或旧步骤被证明不可靠。
- 找到更好的 prompt、排版规则、检查清单或自动化命令。
- 某个 skill 的描述不准确、命名不清楚、触发条件不对或脚本有 bug。
- 用户明确表达了新的偏好、写作标准、发布边界或工具选择。
- 一次任务结束后，有能复用到下一次的经验。

## Where To Put Knowledge

优先选择最小、最贴近的落点：

- 高频规则：更新 [../../AGENTS.md](../../AGENTS.md)，但保持简短。
- 工作流步骤：更新 `docs/workflows/*.md`。
- 项目愿景、目录结构、自动化路线：更新 `docs/project/*.md`。
- skill 边界、命名、保留/移除理由：更新 [skills.md](skills.md)。
- 图片、封面、正文插图规则：更新 [visuals.md](visuals.md)。
- 真实任务复盘、坑点、错误信息、可验证信号：更新 `docs/retrospectives/*.md`。
- 可执行能力变化：更新对应 `.agents/skills/<name>/SKILL.md`、`references/` 或 `scripts/`。

不要把所有信息都塞进 `AGENTS.md`。`AGENTS.md` 是 router 和高频规则，不是百科全书。

`docs/` 只接收项目技术文档、workflow、复盘和已验证的长期 harness memory；文章草稿、渠道预览和一次性写作 scratch 应放在 `content/*` 或 `.local-memory/`，不要放进 `docs/`。

如果只是临时想法、未判断价值的 todo、本机上下文或一次性 scratch，先放 `.local-memory/`。`.local-memory/` 不入 Git，不是 canonical memory；当内容被验证为可复用时，再迁移到上述项目 docs、`AGENTS.md` 或 `.agents/skills/`。详细规则见 [local-memory.md](local-memory.md)。

## Skill Evolution Rules

当发现 skill 可以优化时：

1. 先判断是文档问题、触发描述问题、workflow 问题，还是脚本实现问题。
2. 小修直接改对应 `SKILL.md` 或 reference。
3. 影响行为的脚本改动必须运行最小验证。
4. 如果是新能力，优先扩展现有 skill；只有边界清晰且复用价值高时，才创建新 skill。
5. 保留用户偏好和真实坑点原文，尤其是中文平台 UI 文案和报错。

## Promote To Project Skill

当一项经验已经从“知识记录”变成“可重复执行能力”时，agent 应主动考虑把它沉淀为 project-level skill。

适合 skill 化的信号：

- 同类任务预计会重复出现 3 次以上。
- 任务有明确触发语义，例如“微信公众号排版”“润色行业分析文章”“生成封面图”。
- 已经形成稳定 checklist、输入输出、命令或脚本。
- 只靠文档容易漏步骤，封装成 skill 能显著降低出错率。
- 现有 skill 名称、描述或边界已经承载不下这个能力。

不适合 skill 化的情况：

- 只是一次性偏好或单篇文章特殊处理。
- 规则还没跑通，仍在探索。
- 只是需要在现有 workflow 文档里补一句。
- 可以通过扩展现有 skill 更自然地解决。

默认顺序：

```text
retrospective / workflow doc -> improve existing skill -> create new project skill
```

创建或修改 skill 时，优先使用 `.agents/skills/<skill-name>/SKILL.md`，必要时配套 `references/` 和 `scripts/`。新 skill 应有清晰触发条件、能力边界、输入输出和验证方式。

## Retrospective Format

复盘文档优先记录可执行信息：

```text
Context: 这次任务是什么
What worked: 哪些步骤可靠
Pitfalls: 遇到的坑、原始报错、失败信号
Fix: 如何解决
Reusable rule: 下次应该怎么做
Open questions: 还没验证的点
```

## Do Not Overfit

- 不要因为一次偶然失败就写成通用规则。
- 不要把临时调试细节升级成长期规范。
- 不要让 docs 变成流水账；只有能复用、能避免下次踩坑、能提高质量的内容才沉淀。
- 不要未经验证就宣称 automation 已经可用。

## Default Habit

每次完成一个写作、排版、发布或工具改进任务后，快速问自己：

```text
这次有没有一个下次也会用到的经验？
应该更新 workflow、retrospective、skill，还是只在最终回复里说明？
```

如果答案是“下次也会用到”，就把它沉淀进 repo。
