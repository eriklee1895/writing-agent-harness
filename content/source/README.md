# Source Articles

这里放 repo 内可追踪的 canonical Markdown / MDX source package。

`content/drafts/` 是本地写作 scratch；当一篇文章需要 review、渲染、发布或长期保存时，先 promote 到这里，再派生到 `content/wechat/`、`content/blog/` 等渠道目录。

建议结构：

```text
content/source/YYYY-MM-DD-topic/
├── article.md
├── article.mdx                  # optional
├── notes.md                     # optional
├── assets/                      # prompts / metadata / manifests / small source data
└── channels/                    # optional channel-specific adaptations
```

规则：

- `article.md` / `article.mdx` 是跨渠道 canonical source。
- `channels/` 只放确实需要保留的渠道改写或历史发布版本。
- 图片、视频、音频等二进制素材默认放 `.local-archive/` 或外部资产库，不提交 Git。
- 可以提交 prompt、metadata、manifest、sources、notes、CSV 等可追踪文本数据。

当前第一批回填：

- `2026-05-24-wechat-opening`
- `2026-06-04-poniai-research`
- `2026-06-05-cloudflare-vite-astro`
- `2026-06-07-banshengxue`
- `2026-06-08-luolebai-handanxuebu`
