---
name: seedance-video-gen
description: |
  用火山引擎 Seedance 2.0 生成视频。触发：用户说“生成视频”“把这张图/脚本/文章做成短视频”“做几个视频镜头”“帮我优化 Seedance 提示词”等。支持文生视频、图生视频（首帧/首尾帧）、多模态参考、批量镜头、提示词优化、首帧图生成、查询任务列表、取消/删除任务。

  **Skill 边界**：专注于单次 4-15s 原子视频片段生成；长视频分镜编排（storyboard、shot 串联、首尾帧链式续写）应使用专门的 longform orchestration skill，不在本 skill 范围。Skill 内不引用项目路径；默认输出 `output/`，可通过 `--output-dir` 或 `SEEDANCE_OUTPUT_DIR` env var 覆盖。
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

- `uv` 可用；依赖由脚本 PEP 723 inline metadata 自声明，`uv run` 自动安装。
- 环境变量 `ARK_API_KEY` 已设置；或当前工作目录有 `.env` 文件包含 `ARK_API_KEY=`。
- 可选：`ARK_BASE_URL` 用于自定义网关（默认火山方舟 `https://ark.cn-beijing.volces.com/api/v3`）。

## 快速用法

> **duration 生成视频时长**：取值范围4-15s，根据内容复杂度选择，简单镜头 4–5s，有剧情/对白/多镜头建议 8–15s。

```bash
# 文生视频
uv run scripts/generate_seedance_video.py \
  --prompt "一只橘猫在阳光下缓慢眨眼，微风吹动毛发，镜头轻微推进" \
  --duration 5 --ratio 1:1 --resolution 720p

# 首帧图生视频（带对白和音效的场景，适当加长）
uv run scripts/generate_seedance_video.py \
  --prompt "让人物自然转身看向镜头，保持电影级光影，{你好，好久不见}" \
  --first-frame assets/start-frame.png \
  --duration 8 --ratio 9:16

# 首尾帧
uv run scripts/generate_seedance_video.py \
  --prompt "顺滑的产品外观转场，不出现人物" \
  --first-frame assets/start.png \
  --last-frame assets/end.png \
  --duration 4

# 只创建任务，拿到 task_id（多分镜叙事用长时长）
uv run scripts/generate_seedance_video.py create \
  --prompt "霓虹雨夜街道，摩托车飞驰而过，镜头跟拍穿过雨幕，<引擎轰鸣声>" \
  --duration 10

# 查询已有任务
uv run scripts/generate_seedance_video.py poll \
  --task-id cgt-xxx

# 下载已有视频 URL
uv run scripts/generate_seedance_video.py download \
  --video-url https://example.com/video.mp4

# 列出最近 7 天的任务（按状态筛选）
uv run scripts/generate_seedance_video.py list-tasks \
  --status succeeded --page-size 20

# 按模型 + 多个 task_id 精确搜索
uv run scripts/generate_seedance_video.py list-tasks \
  --model doubao-seedance-2-0-260128 \
  --task-ids cgt-20260606xxxx-xxxx cgt-20260606yyyy-yyyy

# 取消/删除任务（按当前状态不同行为不同，见 references/api-reference.md）
uv run scripts/generate_seedance_video.py cancel-task --task-id cgt-20260606xxxx-xxxx
```

### 批量提交（并行原子 shots）

适合一次性并行提交多个独立 4-15s 视频片段，每个 task 独立生成、独立 task_id。**不是**长视频分镜编排（那是单独的 longform skill 干的事）。

典型场景：
- A/B 测试同一 prompt 的多个变体，挑最好的
- 产品多角度展示（5 个角度一次提交）
- 文章多段落配图（每段独立视频，无剧情关联）
- 批量生成素材备选库

读 JSON 文件，每个 shot 一个 object，可独立覆盖任意参数。

```bash
# 准备 shots.json
cat > /tmp/shots.json << 'EOF'
[
  {"prompt": "产品正面 45 度角特写", "duration": 4, "ratio": "1:1"},
  {"prompt": "产品侧面轮廓", "duration": 4, "ratio": "1:1"},
  {"prompt": "产品俯视角度", "duration": 4, "ratio": "1:1"}
]
EOF

# 一次性并行提交（3 个独立 task）
uv run scripts/generate_seedance_video.py batch-submit \
  --shots-file /tmp/shots.json \
  --model doubao-seedance-2-0-fast-260128 \
  --resolution 480p

# 加 --wait：等所有完成 + 自动下载到指定目录（可选）
uv run scripts/generate_seedance_video.py batch-submit \
  --shots-file /tmp/shots.json --wait --output-dir output/product-shots
```

# 联网搜索（仅纯文本输入，引用当前事件/最新数据）
uv run scripts/generate_seedance_video.py create --enable-web-search \
  --prompt "搜索 2026 年 AI 视频生成最新进展，做 8s 总结短视频" \
  --duration 8 --ratio 9:16
```

## 工作流程

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

4. **执行脚本**
   - 默认使用 `doubao-seedance-2-0-260128`（标准版，支持 1080p 和首尾帧）。
   - 快速预览可用 `doubao-seedance-2-0-fast-260128`（更快、更便宜，但不支持 1080p）。
   - `doubao-seedance-2-0-mini-260615` 在 2026-06-15 ~ 2026-06-22 仅控制台体验中心可调试，**预计 2026-06-22 起支持 API**。

5. **报告结果**
   - 输出目录路径、视频文件路径、`manifest.json` 路径、`task_id`。
   - 如返回 `usage.completion_tokens`，给出大致成本。
   - 提示用户检查生成结果；失败时给出 `manifest.json` 里的错误信息。

## 输出目录

```text
output/YYYY-MM-DD-<slug>/
├── video.mp4
├── manifest.json           # task_id, model, params, video_url, usage, output paths
├── prompt.md               # 最终提示词
└── last-frame.jpg          # 仅当 --return-last-frame
```

## 重要约束

- `duration` 范围 `4–15` 秒，或 `-1` 让模型自适应。
- `resolution`：`480p` / `720p` / `1080p`；**Fast 版和 Mini 版不支持 `1080p`**（脚本会在 client 侧直接拦截）。
- `ratio`：`16:9`、`4:3`、`1:1`、`3:4`、`9:16`、`21:9`、`adaptive`。
- 多模态参考上限：图片 ≤ 9，视频 ≤ 3，音频 ≤ 3，总计 ≤ 12。
- 音频不能单独使用，必须与至少一张图片或一段视频一起传入。
- 首尾帧模式和多模态参考模式**互斥**。
- **联网搜索（`--enable-web-search`）仅纯文本输入**，与 image_url/video_url/audio_url 互斥（脚本会拦截）。
- 本地图片会自动转成 base64 data URL 上传；本地视频/音频由于体积大，目前需要用户先提供可公开访问的 URL。

> 完整参数表、计费、状态机、错误码见 [references/api-reference.md](references/api-reference.md)。

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
| `--priority` | 任务优先级（`0-9`），数值越大越靠前（仅同 Endpoint 内 FIFO 排序） |
| `--enable-web-search` | 联网搜索工具；**仅纯文本输入**，与多模态互斥 |
| `--output-dir` | 输出根目录，默认 `output/`（可被 `SEEDANCE_OUTPUT_DIR` env var 或 `--output-dir` 覆盖） |
| `--poll-interval` | 轮询间隔，默认 20 秒 |
| `--max-wait` | 最大等待秒数，默认 1800 秒（30 分钟） |
| `--dry-run` | 只构建并打印请求，不调用 API |
| `--verbose` | 打印更多调试信息 |

> 完整 4 端点 + 完整请求/响应字段 + 完整分辨率像素表见 [references/api-reference.md](references/api-reference.md)。

## 参考文件

Agent 按需读取，不必全部加载：

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/key-constraints.md` | 30s 速查：能力边界、限制、翻车清单、**实测并发上限** | **每次任务前先读** |
| `references/multimodal-reference.md` | 多模态输入：图片/视频/音频参考详解、编辑/延长、asset:// 协议 | 需要准备参考素材时 |
| `references/prompt-guide.md` | 提示词技巧：公式、分镜写法、运镜/光影词表、情绪外化、音频提示词 | 写 Seedance 提示词时 |
| `references/scene-cookbook.md` | 完整场景示例：教育动画、短剧、产品、竖屏、首帧、编辑、延长 | 需要模板参照时 |
| `references/api-reference.md` | API 端点、参数、状态机、错误码、计费、最低 token 用量、48h 超时、retry 行为 | 调试 API 调用时 |

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
| `GET /tasks/{id}` 返回 404 | 任务 ID 已过 7 天保留期；用 `list-tasks` 找最近 7 天的任务 |
| 脚本拒绝 `--resolution 1080p` | Fast / Mini 不支持 1080p，脚本会硬阻断；改用 720p 或 480p |
| 想批量找历史任务 | `list-tasks --status succeeded --model doubao-seedance-2-0-260128` |
| `--enable-web-search` + 多模态被脚本拒绝 | web_search 仅纯文本输入；如需引用搜索结果，先用纯文本跑一次再以视频为参考续写 |

## 与项目其他 skill 的关系

- 需要首帧/尾帧图时，调用 `article-illustration`。
- 生成后如需剪辑，交给 `article-video-clip`。
- 如需把视频插入微信公众号，走 `wechat-article-renderer` + `wechat-publish-workflow`。
- 最终任务收尾用 `writing-task-closeout`。
