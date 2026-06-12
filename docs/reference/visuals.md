# Visuals

生成图片优先使用系统 `$imagegen` skill。不要重建项目重复的 `gpt-image-gen`，除非用户明确要求创建 project-specific fork。

账号信息放在 `.env`。不要打印 secret values。OpenAI 图片相关 key 可能包括：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
```

## Asset Rule

- `docs/` 下的文档图片属于 repo 文档资产，应进入 Git，不要迁移到 `.local-archive/`。
- 单篇文章使用的图片放在对应 article folder 的 `assets/`。
- `index.md` 只引用 `assets/` 中的图片，**不要直接引用 `.local-archive/` 路径**。`.local-archive/` 是收尾归档快照，不是工作引用位置。
- 图片生成阶段不要双写。生成期版本（如 cover v1/v2/v3）保留在 `assets/`；最终版本在 `writing-task-closeout` 时随 `index.md` 一起归档到 `.local-archive/YYYY-MM-DD-<slug>/`。
- 渠道稿可以引用 `content/origin/YYYY-MM-DD-<slug>/assets/` 的 assets，也可以在渠道目录放 channel-specific assets；避免无意义复制大体积图片。
- 跨文章复用素材可以放在 `content/assets/`；不要把单篇文章的一次性素材放到全局 assets。
- 每篇文章建议在 `assets/manifest.json` 中记录图片文件名、alt、prompt、生成参数、归档路径、使用状态，该 manifest 进入 Git 作为 provenance。
- 使用 descriptive alt text。微信公众号 renderer 会把 alt text 转成 caption。
- 避免 `文章配图` 这种 generic caption。

## Video Material

已知视频 URL 的素材摄取使用 `video-material-ingest` skill。

- 视频素材优先放在文章目录的 `assets/media/`。
- 没有文章上下文时放在 `content/inbox/media/YYYY-MM-DD-<slug>/`（`<slug>` 为裸 topic）。
- 每个素材包必须保留 `manifest.json` 和 `sources.md`，用于后续写作、配图、短视频或 HyperFrames 生产前复核。
- `video-material-ingest` 不负责图片 web search；图片搜索、图片生成和最终版权判断仍走独立 workflow。
- 早期直接放在 `content/inbox/` 的裸 `.mp4` 不能直接作为 `article-video-clip --material`；先包装成 `media.ext + manifest.json + sources.md` 的素材包。为避免复制大视频，可以用 `media.mp4` symlink 指向原文件。

## Video Highlight Selection

文章视频高光选择使用 `video-highlight-select` skill 做人工辅助。

- 输入是本地素材包和文章意图，例如“开头抓人”“证明现场感”“承接某一段观点”。
- 输出默认在素材包内的 `highlight-select/`，包含 `contact-sheet.jpg`、`highlight-candidates.md` 和 `highlight-candidates.json`。
- 第一版不自动决定最佳高光；人看 contact sheet 和候选表后确认 `start/end/title/caption/preset`。
- contact sheet 不依赖 FFmpeg `drawtext`。时间信息用 `highlight-candidates.md/json` 里的格子索引表记录，避免不同 FFmpeg build 缺少字体 filter。
- 确认后的候选片段交给 `article-video-clip` 渲染。

## Article Video Clips

文章内插入的视频剪辑使用 `article-video-clip` skill 从本地素材包生成。

- 输入必须优先来自 `video-material-ingest` 的素材包。
- 输出放在文章目录的 `assets/video-clips/<clip-name>/`。
- 第一版只做轻包装：裁片段、横/竖 preset、标题、caption、来源提示。
- `article-video-clip` 不负责微信公众号上传；插入草稿由 `wechat-publish-workflow` 编排。
- 说剪辑 ready 前，至少确认 `final.mp4` 的尺寸、时长、音轨，并检查 `preview-frame.jpg` 不是黑屏或明显越界。

## 微信公众号封面图

尺寸规范（上传压缩后更清晰）：

| 类型 | 标准尺寸 | 比例 | 高清画布 |
|------|----------|------|----------|
| 头条封面（单图文首图） | 900×383px | 2.35:1 | 1080×460px（优选） |
| 次条封面（小图） | 200×200px | 1:1 | — |
| 信息流卡片 | 500×500px | 1:1 | — |

不要用 `1792x1024`（约 1.75:1），`cover-hd` 修正为 `1080x460`（2.35:1）。

> ⚠️ GPT Image API 最宽只支持 `1792x1024`，无法直接生成 2.35:1。`article-illustration` skill 的 `wechat-cover-hd` 预设已内置自动裁剪：生成 `1792x1024` → Pillow 裁剪至 `1080x460`。使用命令：
> ```bash
> uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
>   --size wechat-cover-hd --style-profile auto ...
> ```

- 不要让 image model 直接生成精确中文标题。优先生成干净背景图，再用本地工具 overlay exact text。
- 关键信息要在微信小图预览里仍然可读。

## 正文插图

- 只在图片能帮助理解、传播或渠道呈现时加入。
- 技术文章优先使用简洁信息图、结构图、流程图或有明确语义的插图。
- 散文/随笔不要默认钉死水彩；优先按文章气质选择 `editorial-atmospheric`、`modern-guochao-editorial`、`cinematic-editorial`、`watercolor-illustration` 等风格。
- 移动端优先，避免信息密度过高或文字过多。
- 微信公众号正文图片保存后应上传为 `mmbiz.qpic.cn` URL。
