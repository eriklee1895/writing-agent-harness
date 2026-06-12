# Directory Layout

项目还在演进中。当前不要为了整洁强行迁移历史内容，但新内容建议逐步靠近这个 layout。

飞书文档是上游写作入口；内容进入 repo 后，以 Markdown / MDX 作为可追踪、可自动化处理的文本格式。

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
│   ├── inbox/                   # 本地原始输入 scratch，gitignored
│   ├── drafts/                  # 本地写作工作区，gitignored
│   ├── origin/                  # 可追踪 canonical Markdown / MDX
│   ├── blog/                    # 可追踪博客 Markdown / MDX，按一级主题目录归档
│   ├── wechat/                  # 可追踪微信公众号文章、preview、notes 和 metadata
│   └── assets/                  # 跨文章复用 prompt、metadata、manifest
```

## Article Folder

写作初期可以使用自包含本地草稿目录：

```text
content/drafts/YYYY-MM-DD-topic/
├── article.md
├── article.mdx                  # optional, for blog
├── assets/
└── notes.md                     # optional research notes
```

进入可追踪状态后，canonical article 放在：

```text
content/origin/YYYY-MM-DD-topic/
├── article.md
├── article.mdx                  # optional, for blog
├── notes.md                     # optional research notes
└── assets/                      # article-local assets / prompts / metadata / manifests
```

渠道稿可以放在：

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

当前 `content/drafts/` 和 `content/inbox/` 按本地 scratch 处理，不会默认提交。后续新文章可以先进入 `content/drafts/` 写作；当文章需要 repo 追踪、review、渲染或发布交付时，再 promote 到 `content/origin/`。渠道版本从 `content/origin/` 派生到 `content/wechat/` 或 `content/blog/`，并保持同一个 folder slug。渠道稿 frontmatter 用 `source:` 指回 canonical article。

文章目录里的 `assets/` 是 article-local assets；全局 `content/assets/` 只放跨文章复用的 prompt、metadata、manifest 和 reference material。渠道目录可以有自己的 `assets/`；如果图片已在 origin assets 且体积较大，可以用相对路径指回 origin 目录，避免重复二进制文件。

不要为了目录整洁贸然移动用户稿件。只有在用户明确同意迁移、且链接和 assets 路径可验证时，才移动历史文章。
