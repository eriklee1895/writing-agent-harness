# Content

这里是未来文章内容的目标工作区。当前历史文章还保留在原目录中，不需要强行迁移。

建议新文章先进入 canonical draft：

```text
content/drafts/YYYY-MM-DD-topic/
├── article.md
├── article.mdx
├── assets/
└── notes.md
```

目录含义：

- `inbox/`: 飞书导出、网页剪藏、临时素材和未整理输入。
- `drafts/`: Markdown / MDX canonical drafts。
- `blog/`: 未来 Astro / Cloudflare Pages 的博客派生稿，按一级主题目录归档。
- `wechat/`: 微信公众号派生稿、HTML preview 和发布相关文件。
- `assets/`: 可复用视觉资产。单篇文章专属图片优先放在文章目录自己的 `assets/`。

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
