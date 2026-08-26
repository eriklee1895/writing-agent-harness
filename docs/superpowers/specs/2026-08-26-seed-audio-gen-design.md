# seed-audio-gen skill 设计文档

**日期**：2026-08-26
**状态**：设计已确认，待实现
**前置调研**：[docs/retrospectives/2026-08-26-seedaudio-1.0-probe.md](../../retrospectives/2026-08-26-seedaudio-1.0-probe.md)（四轮 30 用例实测 + 6-agent 联网调研）

## 背景与动机

火山引擎 2026-06-23 发布「豆包音频生成模型 1.0」（`seed-audio-1.0`），是 LLM 驱动的**生成式音频大模型**，非传统 TTS。一次调用（非流式）从自然语言场景描述生成最长 120 秒成品音频，可含人声、BGM、音效、环境音混合。

实测（30 用例）确认它与现用 `seed-tts-2.0`（确定性 TTS）是不同范式，各有不可替代场景：

- **seed-audio 强项**：人声+音效+BGM 混合成品、多角色对话、音色克隆、情感/时间轴精细控制
- **seed-audio 弱项**：纯旁白（慢 11 倍、贵 14 倍）、verbatim 逐字（靠 prompt 非 API 保证）、精确时长 BGM、实时对话、SSML 精确控制

需要一个独立 skill 让 agent 能正确路由到 seed-audio，同时避免被误用到弱项场景。

## 设计决策

### 1. 单 skill，不拆分

**决策**：一个 `seed-audio-gen` skill，不拆成 `seedaudio-bgm-gen`/`seedaudio-effect-gen` + `seedaudio-tts-gen`。

**理由**：
- seed-audio 的纯人声/BGM/音效/混合成品全部走**同一个 API 端点**（`/api/v3/tts/create`）、同一套鉴权（`X-Api-Key`）、同一个 body 结构（`{model, text_prompt, references, audio_config}`）。区别只在 `text_prompt` 内容——这是「靠 prompt 文档路由」的场景，不是「靠代码分裂」的场景。
- 拆成两个 skill 会产生两份调用同一端点的代码、两份鉴权逻辑、两份 audio_config 处理——重复且无收益。
- 纯 BGM 场景的正确工具是 `volcengine-bigmusic-bgm`（专用音乐模型、时长精确、按时长计费），seed-audio 的 BGM 总是和「人声+音效」混合出成品，不存在独立纯 BGM 高频需求（用户确认「音效总是伴随人声」）。

对照 [[multi-tier-model-skill-dont-split]]：Seedream Pro/Lite 不拆是因严格子集+代码共享；seed-audio 不拆是因同一端点+靠 prompt 区分，结论同但理由不同。

### 2. 单向提示，不互指耦合

**决策**：只在 `seed-audio-gen` 的 SKILL.md 说明自己的不足 + 更优替代，不要求 `volcengine-tts`/`volcengine-bigmusic-bgm` 回指。

**理由**：
- `volcengine-tts` 和 `seed-audio-gen` 经常独立使用，互指会造成耦合，违反 skill 自包含原则。
- `volcengine-tts` 和 `volcengine-bigmusic-bgm` 不改动、不回指，独立使用完全不受影响。
- agent 路由靠各 skill 的 SKILL.md description 实现，不靠 skill 间硬依赖。

### 3. skill 命名 `seed-audio-gen`

**决策**：skill 名 `seed-audio-gen`（带横杠，忠实官方模型名 `seed-audio-1.0`）。

**理由**：
- 官方模型名就是 `seed-audio-1.0`（带横杠），skill 名应忠实原始名称，便于用户提到「seed-audio」时准确触发。
- `-gen` 表达生成式（非 TTS），避免 `seed-audio-tts` 误导成 TTS（seed-audio 最大的坑是被误当 TTS 用：贵、慢、改写风险）。
- 和 `seedance-video-gen`/`seedream-image-gen` 形成「火山模型→产物→gen」模式，但前者连写因其官方名连写，seed-audio 带横杠因其官方名带横杠——忠实原始名称优先于风格统一。

### 4. CLI 参数设计

**输入（prompt）**：
| 参数 | 必填 | 说明 |
|---|---|---|
| `<prompt>` (positional) | 是 | `text_prompt`，自然语言场景描述，≤3000 字符 |

**参考资源（互斥组）**：
| 参数 | 说明 |
|---|---|
| `--speaker <id>` | 音色 ID，复用 seed-tts-2.0 的 `_bigtts`/`_tob` 音色 |
| `--ref-audio <path>` | 本地参考音频路径，CLI 自动 base64（≤30s、≤10MB） |
| `--ref-audio-url <url>` | 远端参考音频 URL |
| `--ref-image <path>` | 本地参考图片路径，CLI 自动 base64（≤10MB） |
| `--ref-image-url <url>` | 远端参考图片 URL |

> `speaker`/`ref-audio`/`ref-audio-url` 三选一互斥（API 约束）；图片不能与音频参考混用。

**输出配置（audio_config）**：
| 参数 | 默认 | 说明 |
|---|---|---|
| `--model` | `seed-audio-1.0` | 模型版本；开放字符串，预留 2.0（发布后改默认值即可，不硬编码白名单） |
| `--format` | `mp3` | wav/mp3/pcm/ogg_opus |
| `--sample-rate` | `48000` | 8000/16000/24000/32000/44100/48000 |
| `--speech-rate` | `0` | [-50,100]，100=2x，-50=0.5x |
| `--loudness-rate` | `0` | [-50,100] |
| `--pitch-rate` | `0` | [-12,12] 半音 |
| `--subtitle` | off | `enable_subtitle`，返回句+词级 ms 时间戳 |

**水印（watermark）**：
| 参数 | 说明 |
|---|---|
| `--watermark` | AIGC 显式水印（音频结尾节奏标识） |
| `--watermark-meta` | 隐式 meta 水印（header 元数据） |

**通用**：
| 参数 | 说明 |
|---|---|
| `-o, --output-dir` | 输出目录，默认 `./seedaudio-output/` |
| `--batch <json>` | batch 模式，JSON 数组，每项可 override 参数 |
| `--concurrency` | batch 并发数，默认 3 |
| `--list-speakers` | 读本地音色表输出（见决策 6） |

**刻意不暴露的参数**：`--context`/`--latex`/`--ssml`——这些是 seed-tts-2.0 的能力，seed-audio 全部用 `text_prompt` 自然语言表达，有这些 flag 反而误导。

### 5. prompt 超长报错（选 B）

**决策**：`text_prompt` > 3000 字符时报错拒绝（不截断），带可执行 hint。

**报错格式**：
```
ERROR 45001116: text_prompt length 3600 exceeds maximum of 3000 chars.
Hint: split your prompt into multiple calls, or shorten the scene description.
Each call generates up to 120s of audio. 人声播报字数建议中文控制在 400 字以内.
```

**新增提示**：官方建议人声播报字数中文控制在 400 字以内（虽硬上限 3000，但人声段过长效果下降）。

### 5b. 计费细节（官方公开文档 补充）

来自官方公开文档：
- 按时长精确至秒，折算为**分钟**计费
- **按模型原始输出时长计费（`original_duration`），倍速不影响计费时长**——即 `speech_rate` 调速不改变计费
- 接口直接传参考音频**不涉及音色费用**（`audio_data` 克隆免费）
- 注册固定音色按**音色槽位**计费（`_tob` 复刻音色的费用来源）

这印证了 batch 成本预估用 `original_duration` 而非 `duration` 是对的（倍速后 `duration` 变但 `original_duration` 不变，计费按后者）。

**理由**：seed-audio 生成的是成品音频，静默截断 prompt 会导致内容缺失而不自知——比让用户/agent 显式分段危险。报错信息含明确错误码+数值+可执行 hint+时长预算，让 agent 感知后能自动拆段自愈（对照 [[skill-edits-verify-documented-examples]]：让错误信息承载足够语义让调用方自愈）。

### 6. 音色表本地化（选 B）

**决策**：把完整音色表预拉成本地 reference，`--list-speakers` 读本地不调 API。

**数据源**：ListSpeakers API 返回的 444 条 JSON（244 `_bigtts` + 200 `_tob`）。

**收录范围**：444 条全收（含 `_tob` ICL 音色）。`_tob` 是 2.0 体系预置音色（文档页第一类下），seed-audio 的 `references[].speaker` 官方明确支持复刻音色，有声书/广播剧场景需要这些人设音色。每条标注 `type: "bigtts"` vs `type: "icl"` 以便查询区分。

**产出**：
- `references/speakers.json`：444 条完整结构化数据（全部 18 字段：VoiceType/Name/Gender/Age/Categories/Description/TrialURL/Languages/Heat/Status 等）
- `references/speakers.md`：人类可读速查表，按场景分组，突出 Description + TrialURL + Heat
- `--list-speakers`：读 JSON，支持 `--filter scene=视频配音`、`--filter lang=ja`、`--sort heat`

**不调 ListSpeakers API 的理由**：该接口走火山 AK/SK 鉴权（非 `X-Api-Key`），要求 skill 配置两套 key（`VOLC_SPEECH_API_KEY` + `VOLC_ACCESSKEY`/`VOLC_SECRETKEY`），鉴权耦合。音色表本地化后，日常合成只需 `VOLC_SPEECH_API_KEY` 一套 key。

**更新机制**：`scripts/refresh-speakers.py`（PEP 723，用 AK/SK 调 ListSpeakers）放 seed-audio-gen，低频手动跑。SKILL.md 标注「音色表截至 2026-08-26，444 个，需更新时跑 refresh-speakers.py」。

**顺带修正 volcengine-tts**：现有 `references/volcengine-speakers.md` 只有 115 个、缺 329 个，用同一份 444 条数据更新它。这是独立改动，分开提交。

### 7. 输出结构与 meta sidecar

**决策**：每个音频带 `.meta.json` sidecar，含 CDN URL（标注时效）。

**meta 结构**：
```json
{
  "audio_file": "seedaudio-output/xxx.mp3",
  "duration": 9.3,
  "original_duration": 9.3,
  "url": "https://lf3-speech-sign.bytednsdoc.com/...",
  "fetched_at": "2026-08-26T01:51:38+08:00",
  "url_expires_at": "2026-08-26T03:51:38+08:00",
  "subtitle": {...},
  "log_id": "...",
  "model": "seed-audio-1.0",
  "text_prompt": "...",
  "estimated_cost_yuan": 0.16
}
```

**CDN URL 处理**：API 返回 2h 有效 CDN URL，存进 meta 带 `fetched_at` + `url_expires_at`。本地 `audio_file` 是永久主存储，URL 是「方便的临时副本」，下游读 `url_expires_at` 过期则回退本地文件。

### 8. batch 模式带成本预估

**决策**：batch 结果每项带 `original_duration_s`，总结带 `total_duration_seconds` + `estimated_cost_yuan`。

**理由**：seed-audio 按秒计费（1 元/分钟），batch 跑 10 个 60s 场景 = 10 元，比 volcengine-tts batch 贵约 100 倍。成本预估让用户/agent 跑完立刻知道花费，避免失控。

**batch 总结结构**：
```json
{
  "results": [...],
  "total_duration_seconds": 120.5,
  "estimated_cost_yuan": 2.01,
  "success_count": 8,
  "fail_count": 2
}
```

## 文件结构

```
.agents/skills/seed-audio-gen/
  SKILL.md                          # 触发描述 + 能力边界 + When NOT to use
  scripts/
    seed-audio-gen.py               # 主 CLI（PEP 723，单句 + batch）
    refresh-speakers.py             # 音色表更新脚本（低频，用 AK/SK）
  references/
    seedaudio-prompt-guide.md       # 场景语法、时间轴、@音频N、音色选择
    speakers.json                   # 444 条完整音色数据
    speakers.md                     # 人类可读音色速查表
```

### prompt-guide.md 必须收录的语法

来自官方公开文档的实测语法：

**时间戳控制**（7.20 升级，100ms 粒度）：
```
广告播音员语速慢地说道：[2.7s:5.7s]"美丽的旅程，值得一个璀璨的开始。"
广告播音员继续介绍：[6.6s:18.9s]"Pocara面霜，专为年轻肌肤定制的第一瓶高端养护..."
```
`[开始s:结束s]"台词"` 格式，直接在 prompt 里控制每段语音的起止时间。配合场景音效描述（"句首伴随一声水声流过的特效音"）实现影视级时间编排。

**场景元素结构**：BGM 描述 + 角色定义（性别/年龄/嗓音/语速/语气）+ 时间戳台词 + 音效描述，一条 prompt 统一编排。

## 待核实项（实现前需确认）

**接口端点与参数命名差异**：

两个官方文档参数命名不一致，需在实现前核实当前可用版本：

| 来源 | model 值 | 文本字段 | 配置字段 |
|---|---|---|---|
| API 文档 2550782（我实测用） | `seed-audio-1.0` | `text_prompt` | `audio_config` |
| 飞书 官方文档 | `doubao-seed-audio-1-0` | `text` | `audio_setting`/`voice_setting` |

我实测（30 用例）用的是 2550782 版本（`openspeech.bytedance.com/api/v3/tts/create` + `model: seed-audio-1.0` + `text_prompt`），全部成功。wiki 写的可能是方舟端点（`ark.cn-beijing`）的命名。**以实测可用的 openspeech 端点为准，wiki 的命名作为参考记录在 prompt-guide 里**。实现时先按实测版本，若后续方舟端点开放再适配。

**采样率默认值**：API 文档说 wav 默认 40000、mp3 默认 44100；wiki 说默认 40K。我 spec 写的 48000（实测用 48000 成功）。保持 48000 作为 CLI 默认（最高音质），不强行对齐文档默认。

**项目主页**：`https://seed.bytedance.com/seedaudio1_0`（放进 reference）

## SKILL.md 触发描述

> 生成式音频创作：从自然语言场景描述一次生成「人声+音效+BGM」成品音频（最长120s），支持时间戳精准控制（100ms粒度）、音色克隆、多角色对话、20语种。适合有声书/广播剧/影视配音/游戏音效/广告/视频片头——把 TTS+BGM+音效+混音的多步流程压成一次调用。不适用纯旁白（用 volcengine-tts，快11倍便宜14倍）或纯BGM（用 volcengine-bigmusic-bgm，时长精确）或实时对话（用双向流式TTS）。

**适用场景洞察**（来自官方公开文档）：
- 有声书：把值得升级的 10-20% 场景（章节序幕、战斗、情绪高峰）从朗读升级到剧感
- 游戏配音：一次 prompt 生成对白+环境音+音乐床，击中 pre-prod/原型/LiveOps 三大节点
- 创作者平台：参考音色（品牌音/达人音/IP音）是付费墙，seed-audio 的克隆+一致性是关键
- 视频出海：多语种/跨语种生成匹配多语言诉求

## 不在本次范围

- seed-audio-2.0 适配（`--model` 已预留，发布后改默认值 + SKILL.md 一行）
- 长内容跨段音色一致性（`section_id`）的 CLI 封装——实测未覆盖，后续按需加
- 参考图片生成模式——实测未覆盖（A 系列只测了 speaker/audio ref），后续按需加

## 验证标准

- CLI 单句模式生成音频 + meta sidecar
- batch 模式带成本预估
- `--list-speakers` 本地查询（filter/sort）
- prompt 超长报错带可执行 hint
- 参考音频 base64 上传克隆
- SKILL.md 的 When NOT to use 单向提示更优选择
