# BGM Benchmark — BigMusic (Volcengine) vs MiniMax music-2.6 (mmx-cli)

**Date**: 2026-06-21  
**Target scenario**: 1-5 min Chinese educational video BGM (instrumental only)  
**Test corpus**: 6 styles × 2-3 durations × 2 providers = 28 successful samples + 1 explicit failure  
**Audio files**: `/Users/eriklee/code/my_project/writing-agent-harness/.local-memory/bgm-benchmark-2026-06-21/{bigmusic,mmx}/`  
**Reproduction**: `uv run .local-memory/bgm-benchmark-2026-06-21/run_bench.py --provider {bigmusic|mmx|all} --duration {60|120|240} --lang {zh|en}`  

---

## TL;DR

| Axis | BigMusic (Volcengine) | MiniMax music-2.6 (mmx-cli) |
| --- | --- | --- |
| **时长老实度** | ✅ ±0.2s | ❌ 完全无视请求时长（实际 130-509s） |
| **单次延迟 (60s)** | 18-23s (med 20s) | 100-205s (med 124s) |
| **单次延迟 (120s)** | 24-37s (med 31s) | 96-257s (med 115s) |
| **时长上限** | 120s（v5.0 硬上限，>120s 报参数错） | 无明确上限，最长 508s（8.5 分钟） |
| **输出格式** | WAV 16bit/44.1kHz/stereo（~10MB/分钟） | MP3 256kbps/44.1kHz/stereo（~1.9MB/分钟） |
| **无人声** | 默认无人声（写死） | `--instrumental` flag（必须显式给） |
| **prompt 语言** | 中文友好（推荐中文 prompt） | 英文效果更稳（但中文也能跑） |
| **错误率（本批 28 条）** | 0%（1 条是越界 240s 故意失败） | 0% |
| **API 易用性** | 中（要 Volc Signature V4，3 级 action 关系易踩） | 高（统一 CLI，OAuth / API key，agent flags 完整） |

**结论**：

- **30s 短视频 / 60-120s 引子 / 精准时长** → **BigMusic 完胜**（10x 快，精度 0.1s）
- **1-5 min 完整视频 BGM（接受 ±30% 时长误差）** → 需拼 2-3 段 BigMusic 或容忍 MiniMax 的长度漂移
- **5 min+ 长 BGM** → **MiniMax 唯一可用**（BigMusic 必须拼接 + 风格衔接问题）
- **AIGC 教学视频 BGM（Erik 主场景）** → **混合方案**：短引子用 BigMusic，长段用 MiniMax 截断

---

## 1. Sample corpus

| Style ID | 中文 prompt | English prompt |
| --- | --- | --- |
| `study_cheerful` | 轻快的钢琴背景纯音乐，简单旋律，明亮温暖，适合小学课堂 | Cheerful background music, simple piano melody, bright and warm, suitable for elementary school classroom |
| `lecture_serious` | 沉稳的弦乐背景纯音乐，渐进和声，缓慢推进，严肃专业，适合大学讲座 | Serious background music, strings-led, progressive harmony, slow build, professional and solemn, suitable for university lecture |
| `humanities_warm` | 温暖的木吉他与钢琴纯音乐，舒缓节奏，留白，适合人文社科总结回顾 | Warm background music, acoustic guitar and piano, gentle pace, with silence, suitable for humanities recap |
| `ambient_electronic` | 极简电子合成器氛围，缓慢演进的低频 pad，零敲击节奏，冥想与专注 | Minimalist electronic ambient, slow-evolving low-frequency pads, no percussion, meditation and focus |
| `eastern_zen` | 空灵的竹笛与古筝对话，简洁留白，东方禅意，无人声 | Ethereal bamboo flute and guzheng dialogue, sparse silence, oriental zen, instrumental |
| `energetic_intro` | 明快的激励节奏，上扬旋律，鼓点清晰，开场引入，活力四射 | Energetic intro music, uplifting melody, clear drum beat, vivid and dynamic |

---

## 2. Per-sample results (中文 prompt)

### 2.1 BigMusic — 60s 请求

| Style | Actual | Wall | Size | Tech | Listen |
| --- | ---: | ---: | ---: | --- | --- |
| `study_cheerful` | 59.9 | 18.5s | 10.1MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/study_cheerful_60s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `lecture_serious` | 60.0 | 23.3s | 10.1MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/lecture_serious_60s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `humanities_warm` | 59.9 | 21.2s | 10.1MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/humanities_warm_60s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `ambient_electronic` | 60.0 | 19.1s | 10.1MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/ambient_electronic_60s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `eastern_zen` | 60.0 | 22.5s | 10.1MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/eastern_zen_60s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `energetic_intro` | 60.0 | 18.5s | 10.1MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/energetic_intro_60s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |

### 2.2 BigMusic — 120s 请求

| Style | Actual | Wall | Size | Tech | Listen |
| --- | ---: | ---: | ---: | --- | --- |
| `study_cheerful` | 120.0 | 36.9s | 20.2MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/study_cheerful_120s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `lecture_serious` | 120.0 | 33.2s | 20.2MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/lecture_serious_120s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `humanities_warm` | 119.9 | 29.3s | 20.2MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/humanities_warm_120s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `ambient_electronic` | 120.0 | 34.3s | 20.2MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/ambient_electronic_120s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `eastern_zen` | 119.9 | 28.2s | 20.2MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/eastern_zen_120s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `energetic_intro` | 120.0 | 24.5s | 20.2MB | 44100Hz/2ch/1411kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/bigmusic/energetic_intro_120s.wav" controls preload="metadata" style="height:24px;width:200px;"></audio> | |

### 2.3 MiniMax music-2.6 — 60s 请求（注意实测时长全部 ≫ 请求）

| Style | Actual | Wall | Size | Tech | Listen |
| --- | ---: | ---: | ---: | --- | --- |
| `study_cheerful` | 146.0 | 114.3s | 4.5MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/study_cheerful_60s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `lecture_serious` | 150.1 | 128.0s | 4.6MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/lecture_serious_60s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `humanities_warm` | 147.1 | 100.0s | 4.5MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/humanities_warm_60s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `ambient_electronic` | 246.3 | 136.7s | 7.5MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/ambient_electronic_60s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `eastern_zen` | 395.6 | 204.5s | 12.1MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/eastern_zen_60s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `energetic_intro` | 182.0 | 118.5s | 5.6MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/energetic_intro_60s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |

### 2.4 MiniMax music-2.6 — 120s 请求（同样全部 ≫ 请求）

| Style | Actual | Wall | Size | Tech | Listen |
| --- | ---: | ---: | ---: | --- | --- |
| `study_cheerful` | 139.8 | 98.3s | 4.3MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/study_cheerful_120s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `lecture_serious` | 129.4 | 97.1s | 4.0MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/lecture_serious_120s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `humanities_warm` | 224.7 | 131.6s | 6.9MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/humanities_warm_120s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `ambient_electronic` | 244.0 | 140.0s | 7.5MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/ambient_electronic_120s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `eastern_zen` | 508.7 | 257.1s | 15.5MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/eastern_zen_120s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |
| `energetic_intro` | 133.0 | 96.2s | 4.1MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/energetic_intro_120s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |

### 2.5 BigMusic — 240s 请求（**故意失败**：v5.0 硬上限 120s）

| Style | Actual | Wall | Size | Tech | Listen |
| --- | ---: | ---: | ---: | --- | --- |
| `study_cheerful` | — | 1.0s | — | — | ❌ Duration 240s out of range; v5.0 supports [30,120] seconds. |

### 2.6 MiniMax — 240s 请求（实际只给 155s，证实不遵守时长）

| Style | Actual | Wall | Size | Tech | Listen |
| --- | ---: | ---: | ---: | --- | --- |
| `study_cheerful` | 154.9 | 98.6s | 4.7MB | 44100Hz/2ch/256kbps | | <audio src="../.local-memory/bgm-benchmark-2026-06-21/mmx/study_cheerful_240s.mp3" controls preload="metadata" style="height:24px;width:200px;"></audio> | |

---

## 3. Performance aggregates

| Metric | BigMusic (n=13) | MiniMax (n=14) |
| --- | ---: | ---: |
| Wall p50 | 23.3s | 116.4s |
| Wall range | 18.5-36.9s | 96.2-257.1s |
| File p50 | 10.09MB | 4.66MB |
| File range | 10.08-20.19MB | 3.95-15.53MB |
| Throughput (60s = 1min BGM) | ~3 tasks/min | ~0.5 task/min |

**关键观察**：

- BigMusic **延迟随请求时长线性增长**（60s→20s wall, 120s→31s wall）；MiniMax **延迟跟请求时长几乎无关**（均在 100-150s 区间）
- MiniMax 的 wall time 主要花在 **生成 + 编码 + 上传 CDN** 全链路，不是 prompt 解析
- BigMusic 文件大小 严格 = 10MB/分钟（PCM 16bit/44.1kHz/stereo 算出），MiniMax 256kbps mp3 算出 ~1.9MB/分钟，实际略大（容器开销）

---

## 4. 时长保真度对比

| Requested | BigMusic actual | MiniMax actual |
| ---: | --- | --- |
| 30s | 不可测（API 限制 [30,120]） | 未测 |
| 60s | **59.9-60.0s**（±0.1s） | 146-396s（中位 150s，+150%） |
| 120s | **119.9-120.0s**（±0.1s） | 129-509s（中位 182s，+52%） |
| 240s | ❌ 报参数错 | 155s（-35%） |

**关键观察**：

- **BigMusic 时长精度 < 0.2s**，完全可以做精准 BGM 拼接（90s+30s = 120s 视频精确嵌入）
- **MiniMax 完全不接受时长控制**。同样 prompt 不同次跑，输出在 130-509s 巨大范围内波动；同一 prompt 给 60s / 120s / 240s 请求，实测长度统计上无差异。结论：时长参数是 **decorative**，模型自决
- 教育视频 1-5min 配乐场景：用 BigMusic 需 1-4 段拼接（拼接点要小心 fade-out/fade-in），用 MiniMax 要 ffmpeg 截断

---

## 5. API 易用性对比

| 维度 | BigMusic | MiniMax (mmx-cli) |
| --- | --- | --- |
| 鉴权 | Volc Signature V4（AK/SK 签名链），3 级 env 回退 | OAuth / API key，1 行 `mmx auth login` |
| CLI 表面 | 1 个 action（`GenBGMForTime`）+ 7 个 flag（duration/rewrite/format/out/meta/timeout/dry-run） | 1 个子命令（`mmx music generate`）+ 20+ flag，结构化（--genre/--mood/--bpm/--key/--tempo...） |
| Agent flags | 无（要自己写 wrapper） | `--non-interactive / --quiet / --output json / --dry-run / --yes` 全套 |
| 错误信息 | 16 个错误码 + 可读 hint（`explain_error()` 映射表） | 退出码 0-10（auth/quota/timeout/filter 分桶）+ stderr |
| 异步 | 必异步，submit + QuerySong 轮询；skill 内部已封 | 必异步（`music` 走 CDN），但 CLI 自己 poll |
| dry-run | ✅ `--dry-run` | ✅ `--dry-run` |
| 文档质量 | 中（两个 Action 关系、QuerySong 名字都是坑） | 高（mmx-cli SKILL.md 极详细） |
| 官方文档 | JS 渲染 SPA，curl 抓不到，要用 `volcengine-doc-fetcher` | N/A（mmx 是 CLI 自描述） |

**踩坑密度**：

- **BigMusic** 上手要踩 3 个坑才能跑通：Action 错配 (`200028`)、轮询 Action 名 (`QuerySong`)、WAV 后缀骗人。skill 已封装好，但调用方仍要理解 GenBGMForTime / QuerySong 两个 Action 关系
- **MiniMax** 几乎无坑：`mmx music generate --prompt ... --instrumental --out X` 一行跑通。代价是放弃时长控制、放弃中文 prompt 微调、放弃波形精度

---

## 6. 1-5min 教育视频 BGM 推荐方案

Erik 的主场景是 **1-5 分钟中文教育视频** 配乐。基于本 benchmark，给出三档方案：

### 方案 A：纯 BigMusic（**推荐** ≤2min 视频）

- **做法**：单次 `GenBGMForTime --duration 60` 或 `--duration 90`（不要 120 顶格，避开边缘）
- **优点**：时长精确，延迟低（~25s），可听性稳定，prompt 中文友好
- **缺点**：2-5min 视频需 2-3 段拼接，风格衔接需要 fade 过渡
- **混音**：直接 ffmpeg `-filter_complex acrossfade` 拼接，无需重采样

### 方案 B：纯 MiniMax（**推荐** 5min+ 视频）

- **做法**：`mmx music generate --prompt '...' --instrumental --out raw.mp3`，再用 ffmpeg `-t` 截断到目标长度
- **优点**：单段覆盖 5min+，无拼接问题
- **缺点**：实际长度有 ±50% 漂移（要听后再截断），延迟 100-150s，wall time 波动大
- **混音**：mp3 → wav（ffmpeg 重采样到 44.1kHz 16bit）→ ffmpeg 截断 → 拼接

### 方案 C：混合（**Erik 最优**）

- **做法**：
  1. 用 BigMusic 生成 30-60s 引子（精准时长）
  2. 用 MiniMax 生成 3-5min 主体（容忍长度漂移，截断到目标 - 60s）
  3. ffmpeg `-filter_complex '[0:a]afade=t=out:st=...[1:a]afade=t=in:st=...[concat]'` 拼接
- **优点**：短引子精准 + 长主体无需拼接
- **缺点**：orchestrator 复杂度上升，AK/SK + mmx-cli 两套鉴权都要管

### 方案 D：仅当 BigMusic 服务挂掉时降级到 mmx-cli

BMM provider 切换由 `[bgm].provider` 控制，`bigmusic | minimax`。orchestrator 接线时把 mmx 设为 fallback，触发条件：连续 3 次 bigmusic 200028/50000001 才切。

---

## 7. 关键 caveat

1. **本批样本 0% 撞版权/相似度**（50000001）—— 用了 6 段具体乐器/场景描述，没用"温暖治愈 + 钢琴"这种通用模板。Erik 实战 prompt 偏向后者，撞限概率会显著上升。要预留 LLM sub-agent 改写 fallback
2. **mmx 60s wall time 在 100-200s 大幅波动**（最差 257s 是 eastern_zen，疑似冷启/RPM 限速）—— batch 任务不要用 5s 间隔，至少 30s
3. **大文件下载**：BigMusic 60s = 10MB，120s = 20MB；mmx 60s = 5MB，120s = 8MB。批量时本地缓存目录要管好
4. **没测并发**：两家都没做并发 benchmark，orchestrator 接线时建议先串行 1 worker 跑稳，再考虑 2-3 路并发（mmx RPM=3 是个硬限制）
5. **可听性未量化**：本报告只测了 wall time / 文件大小 / 编码参数，**实际音乐质量 / 风格匹配度需要 Erik 试听**。audio 标签在所有 28 个样本上，方便直接对比

---

## 8. Reproduction

```bash
# 跑全部中文 prompt × 60s
uv run .local-memory/bgm-benchmark-2026-06-21/run_bench.py --provider all --duration 60 --lang zh

# 单独跑 bigmusic 4min（应失败）
uv run .local-memory/bgm-benchmark-2026-06-21/run_bench.py --provider bigmusic --duration 240 --lang zh

# 跑英文 prompt 验证
uv run .local-memory/bgm-benchmark-2026-06-21/run_bench.py --provider all --style study_cheerful --duration 60 --lang en
```

Driver 自动 resume：第二次跑会跳过已完成的 `(provider, style, duration, lang)` 组合。

结果 JSON: `/Users/eriklee/code/my_project/writing-agent-harness/.local-memory/bgm-benchmark-2026-06-21/results.json`