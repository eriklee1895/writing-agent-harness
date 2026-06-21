---
name: volcengine-bigmusic-bgm
description: |
  使用火山引擎 BigMusic (Seed-Music) 生成 AIGC 视频/文章配乐（无人声纯音乐）。
  触发：BGM provider=bigmusic 时由 video-composer / final compose 调用，
  或用户说"生成 BGM / 背景音乐 / 配乐 / 视频音乐"。
  根据中文风格描述 + 时长生成乐器纯音乐（无人声），走按时长计费入口。
---

# BigMusic BGM Generate（火山引擎 GenBGM）

为 AIGC 视频/文章配乐场景生成无人声纯音乐。**走「按时长计费」入口**，
**不要求自建 TOS Bucket**（服务端复用共享桶并通过签名 URL 直接下发）。

## 接口（一个）

```
Action=GenBGMForTime    # 按时长后付费
service=imagination
region=cn-beijing
OpenAPI Version=2024-08-12
音乐模型 Version=v5.0
```

鉴权为火山引擎 Signature V4（HMAC-SHA256），使用 `VOLC_ACCESSKEY` / `VOLC_SECRETKEY`。

> 历史背景：火山引擎把同一个服务拆成两个 Action 入口——「按时长计费」
> （`GenBGMForTime`）和「套餐包计费」（`GenBGM`），**入口不互通**，调错会被
> 服务端以 `200028 没有可用资源包` 拒掉。Erik 账号是按时长，本 skill **只
> 走 `GenBGMForTime`**，不考虑套餐包路径。

这是与 `mmx-cli`（MiniMax）并列的 **BGM provider**，由 `configs/default.toml`
的 `[bgm].provider` 切换（`bigmusic` | `minimax`）。

> 文档索引见 [`references/api-links.md`](references/api-links.md)。

## 输入

| 参数 | 说明 |
| --- | --- |
| `text`（必填） | 中文风格描述，如 `"关于星空的背景纯音乐，钢琴加吉他"` |
| `--duration` | 时长（秒），v5.0 ∈ **[30, 120]**，**默认 60**（避开版权校验阈值） |
| `--rewrite` | 启用 `EnableInputRewrite`，让模型改写/扩写 prompt（撞 50000001 时强烈建议） |
| `--format` | `wav`（默认，无损 ~10 MB/分钟）\| `mp3`（ffmpeg 转码 ~1.4 MB/分钟） |
| `--out` | 输出路径，**后缀会按真实格式重写**（服务端固定返 wav） |
| `--meta` | 额外写 `<audio>.meta.json`（请求体 / log_id / audio_url） |
| `--timeout` | 轮询超时秒数，默认 300s（60s 任务实测 ~20s 内返回） |
| `--dry-run` | 只打印请求体，不真发请求 |

> v5.0 不再支持 `Genre / Mood / Instrument / Theme` 等结构化枚举；风格完全
> 由中文 `Text` 描述驱动。

## 输出

stdout 一段 JSON：

```json
{
  "audio_file": "/tmp/bgm.wav",
  "duration": 60,
  "log_id": "20260621...",
  "action": "GenBGMForTime",
  "request_body": { "Text": "...", "Duration": 60, "Version": "v5.0", "EnableInputRewrite": false },
  "source": "url",
  "audio_url": "https://v3-default.douyinvod.com/.../tos-cn-v-bfc035/...",
  "error": null
}
```

失败时 `audio_file=null`、`error` 含可读错误码提示，退出码 1。

## 使用方法

```bash
# 基本（按时长计费，60s 避开版权校验）
uv run scripts/generate_bgm.py \
    "轻柔的钢琴与吉他，纯音乐，温暖治愈" \
    --duration 60 --out /tmp/bgm_gentle.wav

# 撞版权/相似度（50000001）时：开启 rewrite 重试
uv run scripts/generate_bgm.py \
    "电子合成器主导的极简氛围，零敲击节奏，冥想与专注" \
    --duration 60 --rewrite --out /tmp/bgm_ambient.wav

# 需要 mp3 输出（ffmpeg 转码，~1.4 MB/分钟）
uv run scripts/generate_bgm.py \
    "空灵的竹笛与古筝对话，东方禅意" \
    --duration 60 --format mp3 --out /tmp/bgm.mp3

# 本地预演（不发请求）
uv run scripts/generate_bgm.py "..." --dry-run
```

## 响应形态与服务端行为

- 提交 → 服务端返 `Result.TaskID`（**不是同步音频 URL**）
- 轮询 `Action=QuerySong` 请求体 `{"TaskID": "..."}`，**响应 `Status` 含义**：
  - `0` 等待 / `1` 处理中 / **`2` 成功** / `3` 失败
  - 成功：`Result.SongDetail.AudioUrl` 拿临时下载 URL
  - 失败：`Result.FailureReason.{Code,Msg}` 拿错误码
- 临时 URL 由 `l=...` 签名参数保护，**默认 1 年有效**（官方文档原话）
- **真实格式是 WAV**（`Content-Type: video/mp4` 是抖音 vod 默认头误导）
  —— 文件头 `RIFF ... WAVE` / PCM 16bit / 44.1kHz / 立体声，脚本会自动重写后缀
- **`TosBucket` 是可选字段**，服务端没要求；AIGC 即取即用场景**不要自建桶**，
  让服务端复用 `tos-cn-v-*` 共享桶即可

## 已知坑（按踩中频次排序）

1. **`200028 APINoSource`** — 没可用资源包。**两种可能**：
   - Action 错配（用了 `GenBGM` 套餐包入口）—— 不会出现，本 skill 写死
     `GenBGMForTime`
   - 「按时长计费」开关没在控制台勾上 —— 查开通页面
2. **`50000001 MusicSimilarityDetectionNotPassed`（次常见）** — 版权/相似度
   校验失败：
   - 30 秒短 prompt 触发率显著高于 60s+ → 至少 60s
   - 描述越通用越易撞参考曲（"温暖治愈 + 钢琴" 这种模板描述尤其容易）
   - 规避三连：**丰富 Text（具体乐器/情绪/场景/节奏）**、**`--rewrite` 让模型改写**、
     **撞限后让调用方用 sub-agent 改写 prompt 重试**（见下）
3. **轮询 Action 是 `QuerySong`**（隐藏在文档侧栏，doc id `/docs/84992/2100960`），
   **不是** `QueryGenBGM*`。请求体字段是 `TaskID`（驼峰大写）。
4. **文件后缀骗人**：服务端只返 wav，URL query 里 `mime_type=audio_wav` 才是
   真格式，`Content-Type: video/mp4` 不要信。脚本嗅探后会自动把 `.mp3` 重写为 `.wav`。
5. **轮询超时默认 300s**（60s 任务实测 ~20s）。如需批量并行降超时到 120s。
6. **MP3 不是原生输出**。需要 mp3 时用 `--format mp3`（ffmpeg 192k），但
   默认值是 wav，因为无损保真且不依赖 ffmpeg。

## 撞 `50000001` 时的 sub-agent 改写 fallback

当脚本返回 `[50000001] MusicSimilarityDetectionNotPassed`，**不要立刻放弃**：
1. 改写 prompt：增加 3-5 个具象描述（具体乐器、节拍、参考场景），避免"温暖治愈
   / 轻柔舒缓"这种易撞模板
2. 加 `--rewrite` 让 BigMusic 自带的 LLM 改写
3. 同时切换风格标签：把"温暖治愈"换成"空灵悠远 / 极简电子 / 城市爵士"等
4. 真正无奈才换 provider（`mmx-cli` 走 MiniMax Music）

## 情绪/风格 prompt 模板

| 风格 | 推荐描述 | 适用场景 |
| --- | --- | --- |
| 轻快学习 | 轻快钢琴 + 简单旋律，明亮温暖 | 小学课程、轻松话题 |
| 沉稳专业 | 弦乐主导，渐进和声，缓慢推进 | 高中/大学专业课 |
| 温暖人文 | 木吉他 + 钢琴，舒缓节奏，留白 | 总结、回顾、人物故事 |
| 引入激励 | 明快节奏，上扬旋律，鼓点清晰 | 开场、激励片段 |
| 极简电子 | 合成器 + 低频 pad，零敲击，缓慢演化 | 冥想、专注、解说配乐 |
| 东方禅意 | 竹笛 + 古筝 + 留白，东方五声音阶 | 文化、文旅、东方美学 |

## 前置条件

- `uv` 可用（脚本为 PEP-723 inline-deps，无需改仓库依赖）
- `ffmpeg`（仅 `--format mp3` 需要）
- 环境变量 `VOLC_ACCESSKEY` / `VOLC_SECRETKEY`
  （三级回退：env → CWD `.env` → `~/.volcengine.env`）
- 火山引擎账号已开通「音视频理解与处理 / AI 生成音乐大模型」并勾选**按时长计费**
- **不需要**配置 TOS 存储（共享桶 + 签名 URL 直接拉）

## 与 orchestrator 的衔接（待接线）

BGM 目前未接入 `src/worker/orchestrator.py`。建议接线点：**final compose 阶段**，
即 `compose.sh` 产出无声/纯人声成片后、最终上传前，调用本 skill 生成 BGM，再用
`scripts/mix_audio.sh <video> <narration> <bgm> <out>`（旁白 100% + BGM
`[bgm].volume`）混音。provider 由 `[bgm].provider` 决定走本 skill 还是 `mmx-cli`。
