---
title: "Hermes 多层 Skills 路径"
description: "Agent 用久之后，skills 会变成一个小型知识库。Hermes 的多层 skills 路径看起来只是目录收纳，实际是在给 agent 记忆加来源、边界和治理结构。"
author: "Erik"
date: 2026-07-05
slug: hermes-multilevel-skills
cover: "./assets/20260705-163139-hermes-multilevel-skills-cover-cropped.png"
tags:
  - AI Agent
  - Hermes Agent
  - Skills
  - Developer Tools
status: draft
source_checked_at: 2026-07-05
---

# Hermes 多层 Skills 路径

![Hermes 多层 Skills 路径：从混乱的扁平技能堆到有序的分层技能体系](assets/20260705-113735-hermes-multilevel-skills.png)

想象你刚搬到一个新城市，行李只有一只背包：几件衣服、一本护照、一台电脑。东西少的时候，你根本不需要收纳系统，随手一放就能找到。

但住久了，东西会指数级增长。书、锅、数据线、合同、药品、运动装备、朋友送的纪念品……如果全部塞进一个抽屉，每次找东西都要把抽屉翻个底朝天。更糟的是，你经常会问：这件东西是我买的、别人送的、还是上一任房客留下的？

Agent 的 skills，正在经历同样的过程。

## Agent 的技能，为什么会变成"知识库"

刚用 agent 时，skills 很少。可能只有搜索网页、读写文件、跑几个常用命令。你甚至不会意识到它们的存在。

但 agent 一旦进入真实工作流，skills 就开始繁殖：

- 官方自带的通用能力
- 从社区或供应商装的第三方技能
- 你自己写的个人工具
- 某个项目里沉淀下来的专属流程
- 团队共享的发布、运维、合规脚本
- Agent 自己从反复任务里"长"出来的半自动化能力

很快，skills 不再是一两张提示词卡片，而是一个小型知识库。问题是：这个知识库一开始几乎都是平铺的。

```text
arxiv/
research-polymarket/
thirdparty-supabase/
erik-wechat-renderer/
team-prod-deploy/
```

名字越长，说明系统越在努力把"我是谁、我从哪来、我属于谁"塞进一个字符串里。这就像把行李箱、别人的礼物、公司的资产、租房时留下的旧物全部塞进一个抽屉，然后在每个盒子上贴越来越长的标签。

![扁平布局与嵌套布局对比：左侧是长名称的扁平目录，右侧是按来源分类的多层目录树](assets/20260705-112058-flat-vs-nested-skill-directories.png)

Hermes 选择把一部分结构还给文件系统。skills 可以按来源、按任务域、按生命周期分层放置：

```text
skills/
├── official/
├── 3rd/
├── project/
├── personal/
└── team/
```

这听起来一点都不酷。它老派、无聊，也很管用。很多工程系统最后能不能继续维护，靠的往往不是更炫的 abstraction，而是这些让人半年后还能看懂的边界。

## Skill 不只是一张提示词卡片

要理解多层路径的价值，先得理解 Hermes 把 skill 当成什么。

它不是"一个可以被模型读到的 markdown 文件"那么简单。Hermes 把 skill 设计成一个小型 package：入口是 `SKILL.md`，旁边可以带脚本、资料、模板和 assets。需要时，agent 先看到轻量索引（名字、描述、分类），然后再决定是否加载完整内容，必要时才读取支持文件。

![Hermes Skill Package 解剖：SKILL.md 入口与 references、templates、assets、scripts 支持目录，以及渐进加载的三层结构](assets/20260705-112148-hermes-skill-package-anatomy.png)

这种"渐进加载"的设计很关键。就像你不会每次打开图书馆都把所有书搬到桌上，agent 也不会每次启动都把全部 skill 内容塞进上下文。它先看书目，再挑书读。

目录层级参与了书目编排。`skills/research/arxiv/SKILL.md` 不只是文件路径，它在告诉系统：这个 skill 属于 `research` 类别。分类信息会进入 skill 列表，影响展示、排序和查找。

## 多层目录下，名字为什么不带父级

这里有一个很容易误会的地方：skill 名会不会自动变成 `research/arxiv`？

答案是：不会。

Hermes 用的是 frontmatter 里的 `name` 字段，如果没写才退回到当前目录名。父级目录不会拼进 skill 名字，而是进入 `category` 字段。

也就是说，日常调用仍然保持短名字，比如 `/arxiv`；目录层级只负责分类、浏览和消歧。

这个设计很朴素，但很重要。它避免了两种极端：

- 如果名字自动带路径，每次调用都要打长串，体验会变差；
- 如果完全不看路径，同名 skill 多了就会撞车。

Hermes 的折中是：短名字用于调用，完整路径用于恢复。当你同时有两个 `arxiv` skill 时，系统不会替你猜，而是列出所有候选，让你用 `research/arxiv` 这种完整路径明确指出要哪一个。

这比"谁先被扫描到谁赢"安全得多。对普通 CLI，选错是 bug；对能执行命令、写文件、访问账户态的 agent，选错可能是信任边界被悄悄替换。

## 递归扫描的边界

支持多层目录，不是加一个 `**/SKILL.md` 递归 glob 就完了。

每个 skill 包里都有自己的支持目录：references、templates、assets、scripts。这些目录里可能有 markdown，甚至可能有旧的 `SKILL.md`。如果扫描器不懂边界，就会把一个 skill 的素材误注册成另一个 skill。

![Hermes 技能发现边界：递归扫描跳过支持目录，skill_view 先按路径再按名称匹配，同名冲突返回歧义警告](assets/20260705-112250-skill-discovery-boundary.png)

Hermes 在源码里定义了支持目录集合，并明确说明这些目录里的内容是"渐进披露数据"，不是"可发现根"。扫描时，如果一个目录已经是 skill 入口，就不会再把它下面的支持目录当成新的 skill 去注册。

这就像图书馆的分类号：书架上可以分很多层，但目录卡片只对应一本书，不能把手册、附录、参考书也各算成一本独立的书。

## `skills/3rd/` 为什么特别重要

在众多分类方式里，我最喜欢的是按来源分，尤其是 `skills/3rd/`。

按任务分类解决的是"找东西"问题，按来源分类解决的是"信不信任"问题。

一个 skill 可能让 agent 去跑脚本、读文件、调 CLI、访问外部服务。第三方 skill 的风险不只是"写得不够好"，更麻烦的是它可能把不该执行的动作包装成一个看似合理的 workflow。

多层路径不能替代 review、签名、权限隔离或沙箱。但它至少让来源边界可见：这个 skill 是自己写的、项目内生的、官方带的，还是第三方来的，看一眼路径就知道。

这也是为什么 Hermes 社区在讨论 project-local skills。有些 skill 只该出现在特定项目里，不该全局污染。来源边界还有一个空间维度。

## 什么时候该用多层

不是所有 agent 都需要立刻把 skills 分层。东西少的时候，一个抽屉更省心。

| 场景 | 建议 |
| --- | --- |
| 少于 10 个个人 skills | 单层，找得到、看得懂 |
| 有明显任务域 | 按 `research/`、`writing/`、`ops/` 分 |
| 有第三方 skills | 放进 `3rd/<vendor-or-repo>/` |
| 有 agent 自动生成的 skills | 先放 `generated/` 或 `inbox/`，验证后再提升 |
| 团队生产环境 | `team/`、`project/`、`ops/`、`archive/` |
| 多项目共享 | external dirs 或 project-scoped 目录 |

最自然的演进是先从平铺开始：

```text
skills/
├── arxiv/
├── github-code-review/
└── wechat-renderer/
```

等来源复杂了，再拆：

```text
skills/
├── personal/
├── project/
├── 3rd/
├── generated/
└── archive/
```

这不是架构升级，这是一次普通但必要的收纳。东西少的时候一个抽屉够用；东西多了还坚持一个抽屉，最后每次找东西都要靠记忆和运气。

## 标准把问题留给实现

Agent Skills 标准本身没有规定"必须支持多层 skills 目录"。它主要定义的是一个 skill package 内部长什么样，至于目录放哪里、扫描多深、同名怎么处理，属于各个 client 自己的实现选择。

这个边界很合理。标准要保证可移植性，不能把每个 agent 的部署模型都定死。

但这也意味着，一旦某个 client 支持多层目录，就要立刻回答一串 runtime 问题：扫描深度怎么限制？`references/SKILL.md` 算不算 skill？同名是覆盖、并列还是报错？symlink 允不允许？项目里的 skill 是否默认可信？

Hermes 的亮点，不是它第一个想到多层目录，而是它把分类目录、外部目录、支持文件排除、命名冲突拒绝、skill package 支持文件这些细节放进了同一个 runtime。

它的重点不止是找到 skill，而是找到以后怎么不找错。

## 代价

多层路径也会把问题带到台面上。

第一，UI 和命令怎么显示？如果 slash command 仍然是 `/arxiv`，目录路径只在后台存在，分类价值会下降；但如果命令变成 `/research/arxiv`，不同平台的 slash command 规则又不一定支持。

第二，category 目前通常只取第一层。`skills/foundations/runtime/explore-codebase` 在人类看来可能是 `foundations/runtime`，系统列表里可能只呈现 `foundations`。深层治理还需要 metadata 补充。

第三，递归扫描的边界必须长期维护。只要支持 scripts、references、archives、symlinks，就一定会不断遇到"这到底是一个 skill，还是一个 skill 的素材"的问题。

第四，多层路径不能替代安全。第三方 skill 放在 `3rd/` 里，只是让你知道它是第三方，不代表它安全。真正的安全还需要 review、签名、安装来源、权限隔离、执行沙箱和审计日志。

它解决不了所有问题。它的价值在于便宜、直观，而且能先把边界画出来。

## Summary

我喜欢 Hermes 这个设计，不是因为它复杂，而是因为它承认了一个朴素事实：agent 用久之后，skills 会变成一个小型知识库。

一个真正工作的 agent，会有研究 skills、写作 skills、发布 skills、运维 skills、公司内部流程 skills、第三方集成 skills、临时实验 skills、被废弃但还要归档的旧 skills。它们不可能永远挤在一个扁平目录里，靠名字前缀互相礼让。

多层 skills 路径给了系统一个简单的骨架。skill 不再只是"一个可以被模型读到的 markdown 文件"，它有位置、有来源、有边界、有支持文件，也有冲突处理。

这件事很小。小到看起来只是：

```text
skills/research/arxiv/SKILL.md
```

但很多生产系统的分水岭，恰恰藏在这种小事里。

一开始你只是想把桌面收拾干净。后来你发现，收纳方式决定了你还能不能继续工作。

## References

1. Hermes Agent 官方文档，[Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)，访问日期：2026-07-05。
2. Hermes Agent 源码，本地 checkout `7e8f50a14`：tools/skills_tool.py。
3. Hermes Agent 源码：agent/skill_commands.py。
4. Hermes Agent 源码：agent/skill_utils.py。
5. Hermes Agent 源码：tests/tools/test_skills_tool.py。
6. Hermes Agent issue，[Auto-discover project-local skills from working directory](https://github.com/NousResearch/hermes-agent/issues/4667)，访问日期：2026-07-05。
7. OpenAI Codex issue，[Skill discovery recursively registers nested SKILL.md files inside symlinked skill directories](https://github.com/openai/codex/issues/22275)，opened on 2026-05-12，访问日期：2026-07-05。
8. Agent Skills 官方规范，[Specification](https://agentskills.io/specification)，访问日期：2026-07-05。
9. Agent Skills 官方实现指南，[How to add skills support to your agent](https://agentskills.io/client-implementation/adding-skills-support)，访问日期：2026-07-05。
10. Anthropic Claude Code 官方文档，[Extend Claude with skills](https://code.claude.com/docs/en/skills)，访问日期：2026-07-05。
11. OpenAI Developers 官方文档，[Agent Skills - Codex](https://developers.openai.com/codex/skills)，访问日期：2026-07-05。
12. OpenClaw 官方文档，[Skills config](https://docs.openclaw.ai/tools/skills-config)，访问日期：2026-07-05。
