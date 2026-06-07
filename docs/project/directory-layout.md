# Directory Layout

项目还在演进中。当前不要为了整洁强行迁移历史内容，但新内容建议逐步靠近这个 layout。

飞书文档是上游写作入口；内容进入 repo 后，以 Markdown / MDX 作为可追踪、可自动化处理的 source。

```text
writing-agent-harness/
├── .agents/skills/              # 项目级 writing/publishing skills
├── docs/                        # 工作流、规范、复盘
│   ├── project/                 # 愿景、目录结构、自动化路线图
│   ├── workflows/               # 可执行流程 runbooks
│   ├── reference/               # skills、visuals 等参考规则
│   ├── retrospectives/          # 真实任务复盘
│   └── superpowers/             # brainstorming specs / writing plans
├── .superpowers/                # generated scratch, preview server output, gitignored
├── content/
│   ├── inbox/                   # 从飞书 / Notion / 剪藏进入的原始内容
│   ├── drafts/                  # Markdown / MDX canonical drafts
│   ├── blog/                    # 未来 Astro/MDX 派生稿，按一级主题目录归档
│   ├── wechat/                  # 微信公众号派生稿和 preview
│   └── assets/                  # 可复用视觉资产
├── 微信公众号/                   # 当前历史微信公众号文章目录，后续可迁移
└── astro_blogs/                 # 未来博客实验区
```

## Article Folder

每篇文章建议使用自包含目录：

```text
content/drafts/YYYY-MM-DD-topic/
├── article.md
├── article.mdx                  # optional, for blog
├── assets/
└── notes.md                     # optional research notes
```

渠道派生稿可以放在：

```text
content/wechat/YYYY-MM-DD-topic/
content/blog/<category>/YYYY-MM-DD-topic/
```

`content/blog/` 当前建议的一级主题目录：

```text
content/blog/
├── ai-agents/                   # agent 框架、runtime、tool use、memory、planning
├── ai-coding/                   # Codex、Claude Code、Cursor、OpenClaw、AI coding workflow
├── industry/                    # 行业追踪、公司/产品事件、AI 基础设施和趋势评论
├── essays/                      # 个人观点、长文思考、非严格技术评论
├── life/                        # 生活随笔、个人感悟
└── investment/                  # 投研、公司研究、市场分析
```

## Migration Rule

当前 `微信公众号/` 是已经跑通的历史文章目录。后续新文章优先进入 `content/drafts/`，再派生到 `content/wechat/` 和 `content/blog/`。

不要为了目录整洁贸然移动用户稿件。只有在用户明确同意迁移、且链接和 assets 路径可验证时，才移动历史文章。
