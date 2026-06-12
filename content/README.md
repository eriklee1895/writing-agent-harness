# Content

这里是文章内容工作区。`content/inbox/` 和 `content/drafts/` 当前按本地 scratch 处理，默认不提交；可追踪 canonical source 放在 `content/origin/`，渠道稿放在 `content/wechat/` 和 `content/blog/`。

建议新文章先进入本地 draft：

```text
content/drafts/YYYY-MM-DD-topic/
├── article.md
├── article.mdx
├── assets/
└── notes.md
```

目录含义：

- `inbox/`: 飞书导出、网页剪藏、临时素材和未整理输入，gitignored。
- `drafts/`: 本地 Markdown / MDX 写作工作区，gitignored。
- `origin/`: 可追踪 canonical Markdown / MDX article package，跨渠道共用。
- `blog/`: 可追踪博客 Markdown / MDX，未来供 Astro / Cloudflare Pages 使用，按一级主题目录归档。
- `wechat/`: 可追踪微信公众号文章、HTML preview、notes 和发布相关 metadata。
- `assets/`: 可复用 prompt、metadata、manifest。写作内容的二进制图片/视频默认放 `.local-archive/` 或外部资产库；`docs/` 下的文档图片例外，应进入 Git。

Canonical article package 建议使用：

```text
content/origin/YYYY-MM-DD-topic/
├── article.md
├── article.mdx
├── notes.md
└── assets/
```

同一篇文章跨 `origin` / `wechat` / `blog` 使用同一个 folder slug；渠道稿 frontmatter 用 `source:` 指回 canonical article。

博客派生稿建议使用：

```text
content/blog/<category>/YYYY-MM-DD-topic/
├── article.md
├── article.mdx
├── assets/
└── notes.md
```

当前建议的博客一级主题：

- `ai-agents/`: agent 框架、agent runtime、tool use、memory、planning、multi-agent 等。
- `ai-coding/`: Codex、Claude Code、Cursor、OpenClaw、代码协作、AI coding workflow 等。
- `industry/`: 行业追踪、公司/产品事件、AI 基础设施和趋势评论。
- `essays/`: 个人观点、长文思考、非严格技术评论。
- `life/`: 生活随笔、个人感悟。
- `investment/`: 投研、公司研究、市场分析。
