# 2026-06-08 Video Material Workflow 复盘

## Context

这次任务是在“邯郸学步 / 落了白”文章素材中，测试新建的 `video-material-ingest`、`video-highlight-select` 和 `article-video-clip` 能否支持微信公众号文章里的视频素材再包装。

目标不是做高级自动剪辑，而是先跑通第一版稳定链路：

```text
已知视频素材
-> 本地可追溯素材包
-> 人工辅助高光选择
-> 指定片段
-> ffmpeg 裁切/转码
-> HyperFrames 轻包装
-> article-ready final.mp4
```

## What Worked

- `content/inbox/` 里的视频素材可以用 `ffprobe` 快速检查分辨率、时长和音视频轨。
- `video-highlight-select` 能从标准素材包生成 contact sheet、时间索引表、候选片段表和 `article-video-clip` handoff 命令。
- `article-video-clip` 的 dry-run 能正确规划输出目录和命令链路。
- 真实剪辑链路跑通后，产物包括：
  - `final.mp4`
  - `preview-frame.jpg`
  - `clip-manifest.json`
  - `notes.md`
  - `hyperframes/index.html`
- 实测输出为 1920x1080、约 8 秒、h264 + aac，保留音轨。
- 输出在 `content/drafts/**` 下，当前 `.gitignore` 会忽略，不会把视频素材提交到 Git。
- 另用 inbox 裸 `.mp4` 包装了一个竖屏测试素材 `邯郸学步六朝版 [BV16krGBqETJ].mp4`，验证 `video-highlight-select` 对 9:16 素材也能生成可用 contact sheet 和候选表。

## Pitfalls

### 1. 裸 mp4 不是标准素材包

`content/inbox/` 里已有很多早期直接下载的裸 `.mp4`，但 `article-video-clip` 当前要求输入是 `video-material-ingest` package：

```text
assets/media/<slug>/
├── media.ext
├── manifest.json
└── sources.md
```

直接把 `content/inbox` 作为 `--material` 会失败：

```text
No media file found in /Users/eriklee/code/my_project/writing-agent-harness/content/inbox
```

临时验证方式是创建一个文章内素材包，用 `media.mp4` symlink 指向 inbox 原视频，并补最小 `manifest.json` / `sources.md`。这避免复制大视频，也符合 `article-video-clip` 的输入边界。

### 2. HyperFrames CLI contract 会变化

第一次真实渲染失败在 `npx hyperframes lint .`。核心错误包括：

```text
missing_timeline_registry: Missing `window.__timelines` registration.
video_missing_muted: <video> has data-start but is not muted. Mark audible videos with data-has-audio="true".
media_missing_id: <video> has data-start but no id attribute.
root_composition_missing_data_start: Root composition "root" is missing data-start.
```

原因是 `article-video-clip` 生成的 HyperFrames HTML 模板没有满足当前 CLI 的 lint contract。

### 3. FFmpeg optional filters 不能假设存在

Homebrew regular `ffmpeg` 即使版本很新，也可能没有编译 `drawtext`。真实命令会失败：

```text
No such filter: 'drawtext'
```

所以 `video-highlight-select` 不应依赖 `drawtext` 在 contact sheet 上烧时间码。更稳的方式是生成纯 `contact-sheet.jpg`，再在 `highlight-candidates.md/json` 里保存格子编号到近似时间点的索引表。

## Fix

已更新 `article-video-clip` 脚本模板：

- root composition 增加 `id="root"`、`data-start="0"`、真实 `data-duration`。
- video 增加稳定 `id="source-video"` 和 `data-has-audio="true"`，继续保留原素材声音。
- overlay/title/caption/source 增加稳定 id 和 `clip` class。
- 注册 paused GSAP timeline：

```js
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
window.__timelines["root"] = tl;
```

并新增回归测试覆盖该 HyperFrames lint contract。

已新增 `video-highlight-select`：

- 生成 `highlight-select/contact-sheet.jpg`。
- 生成 `highlight-candidates.md` 和 `highlight-candidates.json`。
- 记录 source metadata、media metadata、文章意图、候选片段和 handoff 命令。
- 保持 human-in-the-loop，不宣称自动选出最佳高光。

## Reusable Rules

- 文章视频剪辑前，先确认素材是否是标准 `video-material-ingest` package。裸 `.mp4` 需要先包装或迁移成 package。
- 对旧 inbox 视频，不要复制大文件；优先用 symlink 创建 `media.mp4`，再补 `manifest.json` 和 `sources.md`。
- `article-video-clip` 每次真实输出前先跑 `--dry-run`。
- `video-highlight-select` 的 contact sheet 不应依赖 FFmpeg `drawtext`。Homebrew regular `ffmpeg` 可能没有该 filter；使用纯 contact sheet + 时间索引表更稳。
- `video-highlight-select` 适合先服务人工选片；文章场景里的“高光”应由人根据段落意图确认，而不是短期追求自动算法。
- HyperFrames 模板变化后，必须跑：

```bash
node --test .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
npx hyperframes lint .
npx hyperframes inspect .
```

- 说剪辑 ready 前，至少用 `ffprobe` 确认最终视频尺寸、时长和音轨，并检查 `preview-frame.jpg` 不是黑屏。
- 视频上传到微信公众号草稿箱不是 `article-video-clip` 的职责，应由 `wechat-publish-workflow` 编排。

## Open Questions

- 是否给 `video-material-ingest` 增加“裸 mp4 包装成标准 package”的本地迁移命令。
- 是否让 `article-video-clip` 接受 `--material-file <mp4>` 并自动生成临时 package。
- 是否用 Pillow/ImageMagick 给 contact sheet 做后处理编号，而不是引入 `ffmpeg-full`。
- 后续 WeChat video upload via CDP 开始实现时，再决定是否建立根级 Bun workspace。
