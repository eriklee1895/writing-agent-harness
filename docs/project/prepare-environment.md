# Prepare Environment

本文记录在新机器或新 agent 环境中运行 `writing-agent-harness` 时需要准备的本机能力。

原则：repo 内只提交 project-specific skills、docs、source 和可复现配置；个人账号态、API keys、浏览器登录态、user-level skills 不进入 repo。

## Required Runtime

- Git + Git LFS
  - 本 repo 使用 Git LFS 管理图片、视频、音频和设计源文件。
  - clone 后应确保执行过 `git lfs install`，并能正常拉取 LFS objects。
- Node.js
  - `wechat-article-renderer` 和 preview server 使用 Node.js 脚本。
- uv
  - Python 脚本统一使用 `uv run`。
  - `article-illustration` 依赖 Python runtime 和对应环境。

## Optional Runtime

- Bun
  - `baoyu-post-to-wechat` 的 CDP 上传器脚本使用 Bun，或通过 `npx -y bun` 临时运行。
- Chrome / Chromium
  - 微信公众号草稿箱同步依赖 browser / CDP 模式。
- OpenAI API key
  - 图片生成、部分 AI 辅助脚本可能需要。
  - 真实 key 放在本机环境变量或本地 `.env`，不要提交。
- WeChat Official Account 登录态
  - 草稿箱同步需要浏览器登录态。
  - 最终发布 / 群发仍需要 human final review。

## User-Level Agent Skills

项目级 skills 随 repo 提交，位于：

```text
.agents/skills/
```

这些 skills 是 repo 的稳定能力边界，例如：

- `article-ideation`
- `polish-article`
- `article-illustration`
- `wechat-article-renderer`
- `wechat-publish-workflow`
- `baoyu-post-to-wechat`

有些 workflow 还会使用本机安装的 user-level skills。它们通常位于：

```text
~/.agents/skills/
~/.codex/skills/
```

常见例子：

- `tavily-search` / `tavily-research`: web research、current facts 查证。
- `imagegen`: 系统级图片生成能力。
- `openai-docs`: OpenAI API / Codex / ChatGPT 相关官方文档查询。

这些 user-level skills 不随 repo 提交。README 和 runbooks 不应假设 clone 本 repo 后自动拥有这些能力；如果某个任务需要它们，agent 应先检查本机是否存在，缺失时说明 fallback。

## Local Secrets And State

以下内容必须留在本机，不进入 Git：

- `.env`
- API keys / tokens / cookies
- browser profiles 和 WeChat 登录态
- `.claude/settings.local.json`、`.claude/worktrees/` 等 agent/editor 本机状态
- `output/` 生成产物
- `.superpowers/` scratch
- `.venv/`、`node_modules/` 等依赖目录

对应规则见根目录 `.gitignore`。

## Quick Verification

```bash
git lfs version
node --version
uv --version
bun --version   # optional
```

渲染微信公众号 preview：

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs \
  content/drafts/YYYY-MM-DD-topic/article.md --style impact-rational
```

生成插图：

```bash
uv run .agents/skills/article-illustration/scripts/generate_doc_illustration.py \
  --title "插画标题" --brief "描述" \
  --style-profile watercolor-illustration --size wechat-cover-hd
```
