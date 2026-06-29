---
name: seedance-video-gen
description: |
  火山引擎 Seedance 2.0 视频生成。用户说”生成视频””做短视频””把这张图做成视频””图生视频””文生视频””产品广告视频””视频镜头””优化 Seedance 提示词”等时使用；支持文生视频、首帧/首尾帧图生视频、多模态参考（图+视+音组合）、批量并行 shots、任务创建/轮询/下载、任务列表/取消/删除、提示词优化。
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
- 不支持输入含真实人脸的素材（Seedance 限制；预置虚拟人像 `asset://` 与已授权真人素材除外）。
- 本地图片和本地音频会自动转成 base64 data URL 上传；**本地视频不支持 base64**，必须先传到可公开访问的 URL（TOS / S3 / 公网 bucket），或使用 `asset://` 素材 ID。

## 前置条件

- `uv` 可用；依赖由脚本 PEP 723 inline metadata 自声明，`uv run` 自动安装。
- 环境变量 `ARK_API_KEY` 已设置；或当前工作目录有 `.env` 文件包含 `ARK_API_KEY=`。
- 可选：`ARK_BASE_URL` 用于自定义网关（默认火山方舟 `https://ark.cn-beijing.volces.com/api/v3`）。

## 快速用法

> **duration 生成视频时长**：取值范围4-15s，根据内容复杂度选择，简单镜头 4–5s，有剧情/对白/多镜头建议 8–15s。
> **预览 vs 出片**：探索/调参阶段用 fast + 480p/720p 快速迭代，终稿再切 standard + 目标分辨率。
> **默认模型**：省略 `--model` 即走 `doubao-seedance-2-0-260128`（standard 标准版，唯一支持 4k，质量最高）。下方第一个示例显式带 `--model fast` 是「快速预览」用法；第二个「终稿」示例省略 `--model` 即默认 standard。fast/mini 都需主动 opt-in。

```bash
# 文生视频（快速预览，~40% 成本）
uv run scripts/generate_seedance_video.py \
  --model doubao-seedance-2-0-fast-260128 \
  --prompt "一只橘猫在阳光下缓慢眨眼，微风吹动毛发，镜头轻微推进" \
  --duration 5 --ratio 1:1 --resolution 720p

# 文生视频（终稿，1080p）
uv run scripts/generate_seedance_video.py \
  --prompt "一只橘猫在阳光下缓慢眨眼，微风吹动毛发，镜头轻微推进" \
  --duration 5 --ratio 1:1 --resolution 1080p

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

### 联网搜索（仅纯文本输入，引用当前事件/最新数据）

```bash
uv run scripts/generate_seedance_video.py create --enable-web-search \
  --prompt "搜索 2026 年 AI 视频生成最新进展，做 8s 总结短视频" \
  --duration 8 --ratio 9:16
```

> web_search 由模型自主决定调用次数（可能 0 次），会增加生成延迟；只在需要「模型权重外信息」时开启。详细约束见 `references/key-constraints.md`。

## 工作流程

Seedance 视频生成是**强迭代**工作流，不是一次出片。下面是决策启发式，不是固定流水线——根据任务复杂度、用户阶段（探索 / 微调 / 出片）和反馈取舍。

### 判断任务形态

先搞清楚用户处于哪个阶段，这决定你后面投入多少优化：

| 阶段 | 特征 | 策略 |
|---|---|---|
| 探索/脑暴 | 用户自己也不清楚要什么、想看可能性 | fast 模型 + 480p/720p + 短时长（4-5s），一次提交 2-3 个变体，不做首帧图 |
| 调参/迭代 | 已有初版，要修具体问题（换脸/字幕/运镜） | 保留原 prompt，小步修改，用 fast 快速验证；每次只改一个变量 |
| 出片/交付 | 要最终成品 | standard 模型 + 目标分辨率（见下方选择启发式）+ 长时长，参考素材到位 |
| 批量素材 | 多段落独立配图/产品多角度 | batch-submit + fast/mini，并行提交 |

### 模型 / 分辨率 / 时长选择启发式

不要盲目用默认值。按场景挑：

- **模型**：探索/批量/预览 → fast（~40% token 成本、速度相近）；出片 → standard；超大规模备选库 → mini（GA 后）；需要 4k → 只能 standard（并发 1，耐心等）
- **分辨率**：快速预览 → 480p；社媒/微信/草稿 → 720p（默认够用）；最终发布/大屏 → 1080p；有明确 4k 需求且播放器支持 HEVC → 4k
- **时长**：单一动作/产品展示/转场 → 4-5s；有对白/多镜头/情绪铺垫 → 8-12s；复杂叙事 → 12-15s 或拆成多个 task 拼接
- **ratio**：微信视频号/抖音/竖屏短片 → 9:16；文章头图视频/概念片 → 16:9；产品方形展示 → 1:1；电影感宽银幕 → 21:9；首帧图尺寸特殊 → adaptive 让模型判断
- **音频**：对话/旁白/氛围/广告 → 默认生成；纯视觉/后期配音/BGM 另行叠加 → `--no-generate-audio`

### 写提示词：按 shot 复杂度伸缩

- **简单 shot**（4-5s 单一动作/产品/场景）：一句话点明主体+动作+风格即可，不用硬凑运镜/光影/画质
- **中等 shot**（有运镜或氛围要求）：主体 + 动作 + 场景 + 运镜 + 风格
- **复杂 shot**（多人对话/多镜头/长叙事/编辑延长）：完整公式（主体定义 + 分镜时序 + 动作细节 + 光影 + 运镜 + 风格 + 音频 + 约束）
- 提示词技巧、运镜/光影词表、约束模板见 [references/prompt-guide.md](references/prompt-guide.md)，按需翻阅，不是每次必套。
- 参考素材如何绑定、图片/视频/音频组合规则见 [references/multimodal-reference.md](references/multimodal-reference.md)。

### 准备参考素材（可选）

Seedance skill 不负责生成或获取素材——它只消费调用方传入的素材。纯文生视频不需要任何素材，直接跑即可。

当调用方（用户或上层编排 skill）提供素材时：
- 用户直接给的图片/视频/音频 → 直接用，注意比例/分辨率/内容和格式要求
- 本地图片（png/jpg/jpeg/webp/gif/bmp/tiff/heic/heif）和本地 wav/mp3 音频 → 脚本自动转 base64，直接传路径
- 本地视频 → **不支持 base64**，必须先上传公网 URL 或录入 asset:// 素材库再传 URL
- 素材组合规则、绑定语法、编辑/延长模式见 [references/multimodal-reference.md](references/multimodal-reference.md)
- 尾帧、参考视频、参考音频只有在链式续写/动作对齐/音色对齐时才需要；简单 shot 不必凑

### 提交前校验（复杂任务建议）

简单 shot 直接跑；**多参考素材/首尾帧+视频+音频组合/批量 10+ 任务/4k** 这些费钱费时间的请求，先 `--dry-run` 看 payload 是否合理，再真正提交。

### 执行与等待

- 单个 task 4-5 分钟 wall time（含排队）
- **submit 任务（POST /tasks）实测不限流**（普通公司开发账号）：可以一次性 burst 提交几十个 task。并发限制的是**同时 `running` 状态的 task 数量**（普通档实测 20，fast + standard 共享 pool），超出后新任务进 `queued` FIFO 排队，不会报 429。官方文档列出企业 600 / 个人 180 RPM，个人账号未验证
- 4k task 严格串行（running 上限 1，submit 端 RPM 15），耐心等
- 轮询间隔默认 20s 就够，不要开得太频繁
- 需要只拿 task_id 稍后再查：用 `create` 子命令；需要同步等结果：用默认 `generate`

### 迭代是正常的

第一次生成结果不满意很正常。典型迭代模式：
1. 看视频：问题是人/动作/运镜/光影/字幕/音频中哪一个？
2. 对应修正 prompt 或换参考素材（一次只改一个维度）
3. fast 模型快速验证
4. 通过后再用 standard + 目标分辨率出终稿
- 常见问题的 prompt 层解法见 [references/prompt-guide.md](references/prompt-guide.md) 和 [references/key-constraints.md](references/key-constraints.md) 的翻车清单
- 同一 prompt 生成 2-3 次挑最好的，对复杂 shot 是划算的

### 交付

报告用户：输出目录、视频路径、task_id、是否终稿还是预览版。失败时把 `manifest.json` 的 error 字段转成可执行建议（"分辨率参数错了改用 720p"而不是"API 返回 400"）。

需要追溯/复盘/分享终稿时，把最终 prompt 写入输出目录的 `prompt.md`；一次性预览和失败的尝试不必留 artifact。

## 输出目录

```text
output/seedance/YYYY-MM-DD-<slug>/
├── video.mp4
├── manifest.json           # task_id, model, params, video_url, usage, output paths
├── prompt.md               # 最终提示词
└── last-frame.jpg          # 仅当 --return-last-frame
```

## 重要约束

- `duration` 范围 `4–15` 秒，或 `-1` 让模型自适应。
- `resolution`：`480p` / `720p` / `1080p` / `4k`；**默认 `720p`**；**Fast 版和 Mini 版最高 `720p`**（脚本会在 client 侧直接拦截）；**`4k` 仅标准版，输出 10-bit H.265/HEVC**，并发 1、RPM 15。
- `ratio`：`16:9`、`4:3`、`1:1`、`3:4`、`9:16`、`21:9`、`adaptive`；**默认 `16:9`**（脚本 argparse 默认 16:9；实测省略 ratio 时 API 也返回 16:9，官方文档标注的 `adaptive` 与实测不符）。
- 多模态参考单类型上限：图片 ≤ 9，视频 ≤ 3，音频 ≤ 3（官方未明文规定总数硬上限；脚本 client 侧硬限总计 ≤ 12）；实测推荐 **4-5 个素材** 的黄金配比（详见 references）。
- 音频不能单独使用，必须与至少一张图片或一段视频一起传入。
- 首尾帧模式（`first_frame` / `last_frame`）和参考图模式（`reference_image`）**互斥**；首尾帧与 `reference_video`/`reference_audio` 共用未在官方文档明文确认（详见 multimodal-reference.md 的「模式组合规则」）。
- **联网搜索（`--enable-web-search`）仅纯文本输入**，与 image_url/video_url/audio_url 互斥（脚本会拦截）。
- 本地图片（png/jpg/jpeg/webp/gif/bmp/tiff/heic/heif）和本地音频（mp3/wav）会自动转成 base64 data URL 上传；**本地视频不支持 base64**，视频必须以 http(s):// URL 或 `asset://` ID 形式传入，容器仅 MP4/MOV，单文件 ≤ 200 MB。

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
| `--output-dir` | 输出根目录，默认 `output/seedance/`（可被 `SEEDANCE_OUTPUT_DIR` env var 或 `--output-dir` 覆盖） |
| `--poll-interval` | 轮询间隔，默认 20 秒 |
| `--max-wait` | 最大等待秒数，默认 1800 秒（30 分钟） |
| `--dry-run` | 只构建并打印请求，不调用 API |
| `--verbose` | 打印更多调试信息 |

> 完整 4 端点 + 完整请求/响应字段 + 完整分辨率像素表见 [references/api-reference.md](references/api-reference.md)。

## 参考文件

Agent 按需读取，不必全加载。简单任务（文生视频 4-5s、单镜头）直接跑即可，不必先读 reference；复杂任务、遇到错误、准备多模态素材、或要写精细 prompt 时再查。

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/key-constraints.md` | 能力边界、硬限制、翻车清单、并发上限、4k 特殊规则 | 第一次用 / 遇到 API 错误 / 用 4k 或多模态前 / 排查"为什么生成不对" |
| `references/multimodal-reference.md` | 多模态输入：图片/视频/音频怎么传、asset://、编辑/延长模式 | 准备参考素材时 |
| `references/prompt-guide.md` | 提示词公式、运镜/光影/风格词表、音频写法、约束模板、翻车对应解法 | 写 Seedance 提示词 / 生成结果不满意要迭代时 |
| `references/scene-cookbook.md` | 完整场景配方示例（教育、短剧、产品、竖屏、编辑、延长、戏曲、跨模态编辑等）| 需要模板参照 / 不知道某类场景怎么写时 |
| `references/api-reference.md` | API 端点、参数、状态机、错误码、计费、manifest 字段 | 调试 API 调用 / 需要查具体字段含义时 |

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
| 脚本拒绝 `--resolution 1080p`/`4k` | Fast / Mini 最高 720p，脚本会硬阻断；改用 720p 或 480p |
| 脚本拒绝本地视频路径 | 视频不支持 base64；先上传到公网 URL / TOS，或录入 asset:// 素材库 |
| 想批量找历史任务 | `list-tasks --status succeeded --model doubao-seedance-2-0-260128` |
| `--enable-web-search` + 多模态被脚本拒绝 | web_search 仅纯文本输入；如需引用搜索结果，先用纯文本跑一次再以视频为参考续写 |

## 辅助脚本（高级/评测）

| 脚本 | 用途 |
|---|---|
| `scripts/grade_seedance_video.py` | 对 `evals/` 中定义的 eval case 跑出的 outputs 打标，用于 prompt/参数回归测试 |
| `scripts/benchmark_seedance_concurrency.py` | 自适应步进式并发容量测试，测量账号的 running 上限和饱和点 |

正常生产使用不需要跑这两个脚本；调参、跑基准、回归测试时使用。

## 与项目其他 skill 的关系

Seedance 是原子能力 skill：**输入是 prompt + 可选素材 + 参数，输出是视频文件**。它不主动调用其他 skill 准备素材，也不做后期剪辑/发布。

- **上游**（给 Seedance 喂素材的 skill）：
  - 需要首帧/概念图：由调用方自行准备，可用 `article-illustration` / `seedream-image-gen` / `gpt-image-2` 等生图 skill，但具体选择是上层编排的事
  - 需要 BGM/音效/旁白音频：由调用方准备，可用 `volcengine-bigmusic-bgm` / `volcengine-tts`
  - 长视频分镜、多 shot 编排、首尾帧链式续写：应由专门的长视频编排 skill 负责（当前 repo 尚未有），它负责拆 shot、准备素材、调用 Seedance、拼接
- **下游**（消费 Seedance 产出的 video.mp4 的 skill）：
  - 剪辑/拼接/加字幕 → `article-video-clip`
  - 视频插入微信公众号 → `wechat-article-renderer` + `wechat-publish-workflow`
  - 任务收尾归档 → `writing-task-closeout`
