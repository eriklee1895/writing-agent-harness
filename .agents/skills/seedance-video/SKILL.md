---
name: seedance-video
description: |
  用火山引擎 Seedance 2.0 生成视频。触发：用户说“用 Seedance 生成视频”“把这张图/脚本/文章做成短视频”“做几个视频镜头”“帮我优化 Seedance 提示词”等。支持文生视频、图生视频（首帧/首尾帧）、多模态参考、批量镜头、提示词优化和首帧图生成。
---

# Seedance Video

用火山引擎 Seedance 2.0 把文字、图片或多模态参考生成视频，适合文章短视频、产品广告、概念验证镜头、社交媒体素材。

## 何时使用

- 用户给了一段脚本/描述，要生成视频。
- 用户给了一张图，要做成动态短视频（首帧或首尾帧）。
- 用户想基于文章、产品说明或已有图片生成多个视频镜头。
- 用户想优化 Seedance 提示词、运镜或光影描述。

## 不适用范围

- 不处理视频搜索、版权判断、剪辑后期。
- 不直接发布到任何平台。
- 不支持输入含真实人脸的素材（Seedance 限制）。
- 本地图片会自动转成 base64 data URL 上传；本地视频/音频由于体积大，目前需要用户先提供可公开访问的 URL。

## 前置条件

- `uv` 可用，项目依赖已同步 (`uv sync`)。
- 环境变量 `ARK_API_KEY` 已设置；或当前工作目录有 `.env` 文件包含 `ARK_API_KEY=`。
- 可选：`ARK_BASE_URL` 用于自定义网关（默认火山方舟 `https://ark.cn-beijing.volces.com/api/v3`）。

## 快速用法

```bash
# 文生视频
uv run .agents/skills/seedance-video/scripts/generate_seedance_video.py \
  --prompt "一只橘猫在阳光下缓慢眨眼，微风吹动毛发，镜头轻微推进" \
  --duration 5 --ratio 1:1 --resolution 720p

# 首帧图生视频
uv run .agents/skills/seedance-video/scripts/generate_seedance_video.py \
  --prompt "让人物自然转身看向镜头，保持电影级光影" \
  --first-frame assets/start-frame.png \
  --duration 5 --ratio 9:16

# 首尾帧
uv run .agents/skills/seedance-video/scripts/generate_seedance_video.py \
  --prompt "顺滑的产品外观转场，不出现人物" \
  --first-frame assets/start.png \
  --last-frame assets/end.png \
  --duration 4

# 只创建任务，拿到 task_id
uv run .agents/skills/seedance-video/scripts/generate_seedance_video.py create \
  --prompt "霓虹雨夜街道，摩托车飞驰而过" \
  --duration 5

# 查询已有任务
uv run .agents/skills/seedance-video/scripts/generate_seedance_video.py poll \
  --task-id cgt-xxx

# 下载已有视频 URL
uv run .agents/skills/seedance-video/scripts/generate_seedance_video.py download \
  --video-url https://example.com/video.mp4
```

## Claude 工作流程

1. **理解需求**
   - 确认模式：文生视频 / 首帧 / 首尾帧 / 多模态参考 / 批量镜头。
   - 确认输出比例、分辨率、时长、是否带声音。
   - 如果是批量镜头，确认共用的风格、比例、分辨率。

2. **优化提示词**
   - 读取 `references/prompt-guide.md`。
   - 把用户brief扩展成 Seedance 友好格式：
     **主体 + 动作细节 + 场景环境 + 光影色调 + 镜头运镜 + 视觉风格 + 画质 + 约束条件**。
   - 把最终提示词保存到输出目录的 `prompt.md`。

3. **准备首帧/尾帧（可选）**
   - 如果用户只有概念没有图，调用 `article-illustration` 生成首帧图。
   - 需要尾帧时，同样方式生成。
   - 生成的图片放在输出目录 `assets/` 下，再传给本脚本。

4. **确认费用（涉及真实 API 调用时）**
   - 报告估算：`model × duration × resolution`，以及当前默认计费大约 1 元/秒。
   - 如果用户未明确授权，先 `--dry-run` 预览请求。
   - 如果用户已说“不计成本”“直接跑”，可以跳过单独确认。

5. **执行脚本**
   - 默认使用 `doubao-seedance-2-0-260128`（标准版，支持 1080p 和首尾帧）。
   - 快速预览可用 `doubao-seedance-2-0-fast-260128`（更快、更便宜，但不支持 1080p）。

6. **报告结果**
   - 输出目录路径、视频文件路径、`manifest.json` 路径、`task_id`。
   - 如返回 `usage.completion_tokens`，给出大致成本。
   - 提示用户检查生成结果；失败时给出 `manifest.json` 里的错误信息。

## 输出目录

```text
content/inbox/videos/YYYY-MM-DD-<slug>/
├── video.mp4
├── manifest.json          # task_id, model, params, video_url, usage, output paths
├── prompt.md              # 最终提示词
└── last-frame.jpg         # 仅当 --return-last-frame
```

## 重要约束

- `duration` 范围 `4–15` 秒，或 `-1` 让模型自适应。
- `resolution`：`480p` / `720p` / `1080p`；Fast 版不支持 `1080p`。
- `ratio`：`16:9`、`4:3`、`1:1`、`3:4`、`9:16`、`21:9`、`adaptive`。
- 多模态参考上限：图片 ≤ 9，视频 ≤ 3，音频 ≤ 3，总计 ≤ 12。
- 音频不能单独使用，必须与至少一张图片或一段视频一起传入。
- 首尾帧模式和多模态参考模式**互斥**。
- 本地图片会自动转成 base64 data URL 上传；本地视频/音频由于体积大，目前需要用户先提供可公开访问的 URL。

## 参数速查

| 参数 | 说明 |
|---|---|
| `--prompt, -p` | 文本提示词 |
| `--prompt-file` | 提示词文件路径 |
| `--first-frame` | 首帧本地图片路径 |
| `--last-frame` | 尾帧本地图片路径 |
| `--reference-image` | 多模态参考图（可重复） |
| `--reference-video` | 多模态参考视频（可重复） |
| `--reference-audio` | 多模态参考音频（可重复） |
| `--model` | 模型 ID |
| `--duration` | 时长秒数 |
| `--ratio` | 画面比例 |
| `--resolution` | 分辨率 |
| `--generate-audio` / `--no-generate-audio` | 是否生成音频 |
| `--watermark` / `--no-watermark` | 是否加水印 |
| `--return-last-frame` | 返回尾帧图 |
| `--seed` | 随机种子 |
| `--output-dir` | 输出根目录，默认 `content/inbox/videos/` |
| `--poll-interval` | 轮询间隔，默认 20 秒 |
| `--max-wait` | 最大等待秒数，默认 1800 秒（30 分钟） |
| `--dry-run` | 只构建并打印请求，不调用 API |
| `--verbose` | 打印更多调试信息 |

## 参考文件

Agent 按需读取，不必全部加载：

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/key-constraints.md` | 30s 速查：能力边界、限制、翻车清单 | **每次任务前先读** |
| `references/prompt-guide.md` | 提示词技巧：公式、分镜写法、运镜/光影词表、情绪外化 | 写 Seedance 提示词时 |
| `references/scene-cookbook.md` | 完整场景示例：教育动画、短剧、产品、竖屏、首帧、编辑、延长 | 需要模板参照时 |
| `references/api-reference.md` | API 端点、参数、状态机、错误码、计费 | 调试 API 调用时 |

## 故障排查

| 现象 | 处理 |
|---|---|
| `ARK_API_KEY not found` | 检查环境变量或 `.env` 文件 |
| `400 InvalidParameter` | 检查 `resolution` 与模型是否匹配、`duration` 越界、比例非法 |
| `401` | API Key 无效或权限未开通 Seedance |
| `403` | 内容审核未通过，检查是否含人脸或违规内容 |
| `429` | 限流或余额不足 |
| 任务 `failed` | 查看 `manifest.json` 中的 `error` 字段 |
| 视频 URL 下载失败 | URL 24 小时过期，尽快下载 |

## 与项目其他 skill 的关系

- 需要首帧/尾帧图时，调用 `article-illustration`。
- 生成后如需剪辑，交给 `article-video-clip`。
- 如需把视频插入微信公众号，走 `wechat-article-renderer` + `wechat-publish-workflow`。
- 最终任务收尾用 `writing-task-closeout`。
