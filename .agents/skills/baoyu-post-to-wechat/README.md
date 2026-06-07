# baoyu-post-to-wechat

This directory vendors the `baoyu-post-to-wechat` skill from Baoyu's `baoyu-skills` project for this workspace.

- Upstream: https://github.com/JimLiu/baoyu-skills
- Upstream skill path: `skills/baoyu-post-to-wechat/`
- Local path: `.agents/skills/baoyu-post-to-wechat/`
- Local version: see `SKILL.md`

## Local Role

In this repo, `baoyu-post-to-wechat` is kept as a third-party uploader and Chrome CDP / WeChat API reference implementation.

It is not the canonical source for this workspace's article style, layout, or publishing policy. Those local responsibilities live in:

- `.agents/skills/wechat-article-renderer/`
- `.agents/skills/wechat-publish-workflow/`
- `docs/workflows/wechat-writing-publishing.md`

## Acknowledgement

Thanks to Baoyu / JimLiu for publishing and maintaining `baoyu-skills`.

When updating this vendored copy, preserve upstream attribution and keep local changes small and documented. Prefer extracting project-specific behavior into this repo's own skills instead of heavily modifying third-party code in place.

## Do Not Commit Local State

Never commit runtime or account state for this skill:

- `.env`
- `.baoyu-skills/`
- WeChat token / appsecret / appid
- Chrome profile / browser user data
- cookies
- `node_modules/`

Use local config files outside git for credentials and browser state.
