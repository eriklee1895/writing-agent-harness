---
name: erik-blog-publish-workflow
description: "Publish finalized articles from Erik Lee's writing-agent-harness content/origin directory to Erik Lee's personal Astro blog repo eriklee-blog. Use only for Erik's local blog workflow: syncing Markdown/MDX, assets, taxonomy metadata, build checks, git commits/branches, and Cloudflare Pages deployment handoff."
---

# Erik Blog Publish Workflow

## Overview

This skill is specific to Erik Lee's personal blog pipeline:

```text
writing-agent-harness/content/origin/YYYY-MM-DD-<slug>/
  -> /Users/eriklee/code/my_project/eriklee-blog/src/content/posts/
  -> GitHub
  -> Cloudflare Pages
```

Do not treat this as a generic blog publishing skill. It depends on Erik's local repo layout, Astro blog taxonomy, asset conventions, and Cloudflare Pages deployment setup.

## Publish Boundary

`git push origin main` in `eriklee-blog` is a public publish action because Cloudflare Pages auto-deploys `main`.

Default behavior:

- Safe without extra confirmation: inspect, sync, validate, build, commit on a feature branch, push a feature branch.
- Requires explicit user confirmation: pushing directly to `main`, merging into `main`, or changing Cloudflare/GitHub deployment settings.
- Never publish unfinished drafts. If article readiness is unclear, run `article-readiness-check` first.

## Standard Workflow

1. Identify the origin article.
   - Prefer `content/origin/YYYY-MM-DD-<slug>/index.md`.
   - If the user asks to publish all completed origin articles, run batch sync only after confirming that all selected origin directories are formal finished稿件.
2. Check both repos before editing:

   ```bash
   git status --short
   git -C /Users/eriklee/code/my_project/eriklee-blog status --short
   ```

   Preserve unrelated user changes. Do not stage unrelated files, especially untracked origin articles.
3. Sync one article to the blog repo:

   ```bash
   uv run scripts/sync_origin_to_blog.py \
     content/origin/YYYY-MM-DD-<slug> \
     --blog-root /Users/eriklee/code/my_project/eriklee-blog \
     --extension mdx \
     --published
   ```

   For batch sync, use `--all` only when the user explicitly wants a full import/resync:

   ```bash
   uv run scripts/sync_origin_to_blog.py \
     content/origin \
     --blog-root /Users/eriklee/code/my_project/eriklee-blog \
     --extension mdx \
     --published \
     --all
   ```

4. Validate generated blog content:
   - Destination file exists under `/Users/eriklee/code/my_project/eriklee-blog/src/content/posts/`.
   - Frontmatter has `title`, `description`, `pubDatetime`, `category`, `tags`, and preferably `series`/`type` when applicable.
   - No `Image pending` remains.
   - Referenced local assets exist under `src/content/posts/assets/<slug>/`.
   - Do not overwrite manually edited blog files without checking the diff.
5. Build the blog:

   ```bash
   cd /Users/eriklee/code/my_project/eriklee-blog
   npm run build
   ```

6. Verify key local routes from `dist/` or a dev server:
   - `/posts/`
   - `/posts/<slug>/`
   - relevant `/categories/<category>/`
   - relevant `/series/<series>/`
   - `/rss.xml`
   - `/search/`
   - `/498a4fb724cd8c54f51efd9a721539e1.txt` when deployment/verification files may be affected
7. Commit intentionally in the blog repo.
   - Use a specific commit message, e.g. `Publish <article-title> to blog`.
   - If working on taxonomy/sidebar/native Astro changes, prefer a feature branch.
8. Push only according to the publish boundary:
   - Feature branch: okay when useful for preview/review.
   - `main`: ask for explicit publish confirmation first unless the user already said to publish directly.
9. After Cloudflare deploys, verify the public URL with `curl` or browser:

   ```bash
   curl -I https://eriklee-blog.pages.dev/posts/<slug>/
   ```

   If the new content is not visible yet, wait and retry; Cloudflare Pages may need a minute.

## Taxonomy Rules

The blog sidebar depends on frontmatter. Preserve or infer these fields:

- `category`: one primary bucket, shown in the sidebar.
- `series`: optional learning/research sequence.
- `tags`: flexible secondary labels.
- `type`: article shape, default `技术笔记`.

Common display taxonomy:

- `AI Engineering` -> `AI 工程`
- `AI Frontier` -> `AI 前沿`
- `Web & AI Tooling` -> `Web 与 AI 工具链`
- `Culture & Media` -> `文化与媒介`
- `Writing System` -> `写作系统`
- `Hermes Notes` -> `Hermes 笔记`
- `Codex Notes` -> `Codex 笔记`
- `Claude Code Notes` -> `Claude Code 笔记`
- `TanStack Notes` -> `TanStack 笔记`
- `CopilotKit Notes` -> `CopilotKit 笔记`

Do not physically categorize files into folders. Keep blog posts flat under `src/content/posts/`; use frontmatter for virtual organization.

## Gotchas

- Use `scripts/sync_origin_to_blog.py` as the current `origin -> eriklee-blog` adapter. Ignore older notes or shells that mention the historical `sync_origin_to_astropaper.py` name.
- Do not run `git add .` in either repo. It can accidentally stage unrelated origin drafts, local assets, or generated files.
- Do not delete user edits in `eriklee-blog` while syncing. Read diffs first.
- Cloudflare Pages previews may build feature branches, but production uses `main`.
- Blog publishing is less visibly dangerous than WeChat publishing, but `push main` still makes content public.
