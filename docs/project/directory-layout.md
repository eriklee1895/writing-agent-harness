# Directory Layout

项目还在演进中。当前不要为了整洁强行迁移历史内容，但新内容建议逐步靠近这个 layout。

飞书文档、Notion 笔记和网页剪藏都可以作为上游输入；内容进入 repo 后，以 `content/origin/` 里的 Markdown / MDX 作为可追踪、可自动化处理的 canonical source。

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
│   ├── blog/                    # 可追踪博客 Markdown / MDX 渠道副本（如需本 repo 内留存）
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
content/blog/YYYY-MM-DD-topic/
```

AstroPaper 博客 repo 的 `src/content/posts/YYYY-MM-DD-topic.mdx` 也属于渠道发布副本，应该由 `content/origin/YYYY-MM-DD-topic/` 单向生成；不要把 AstroPaper repo 当成写作源头。

博客分类不建议用物理目录表达。`src/content/posts/` 保持扁平，分类、系列和标签放在 frontmatter：

```yaml
category: "AI Engineering"
series: "Claude Code Notes"
tags:
  - claude-code
  - coding-agent
```

物理目录只用于内容类型边界，例如 `posts/`、`pages/`、`projects/`；不要把 `claude-code`、`codex`、`langchain` 这类会演变的主题写进永久 URL。

## Migration Rule

当前 `content/drafts/` 和 `content/inbox/` 按本地 scratch 处理，不会默认提交。后续新文章可以先进入 `content/drafts/` 写作；当文章需要 repo 追踪、review、渲染或发布交付时，再 promote 到 `content/origin/`。渠道版本从 `content/origin/` 派生到 `content/wechat/`、`content/blog/` 或独立 Astro 博客 repo，并保持同一个 slug。渠道稿 frontmatter 用 `source:` 指回 canonical article。

文章目录里的 `assets/` 是 article-local assets；全局 `content/assets/` 只放跨文章复用的 prompt、metadata、manifest 和 reference material。渠道目录可以有自己的 `assets/`；如果图片已在 origin assets 且体积较大，可以用相对路径指回 origin 目录，避免重复二进制文件。

不要为了目录整洁贸然移动用户稿件。只有在用户明确同意迁移、且链接和 assets 路径可验证时，才移动历史文章。
