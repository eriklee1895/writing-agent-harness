# 2026-06-21 — 火山引擎 BigMusic 端到端跑通 + skill 优化

## TL;DR

`volcengine-bigmusic-bgm` skill 之前因为三个错位**端到端跑不通**，今天一次性
修干净：

1. **Action 错配**：skill 默认调 `GenBGM`（套餐包预付费），但 Erik 的火山引擎
   账号是「按时长计费」订单；错配 → 服务端返 `200028 APINoSource`。修复：默认
   改 `GenBGMForTime`（最终只暴露这一个 Action，`--action` 选项砍掉，避免再被
   误用）。
2. **轮询 Action 错误**：skill 里 `QUERY_ACTION_CANDIDATES = [QueryGenBGM*...]`
   全是猜的，官方真正的轮询 Action 是 `QuerySong`（藏在生成纯音乐文档侧栏，doc
   id `/docs/84992/2100960`）。修复：锁定 `QuerySong`，按文档解析
   `Result.SongDetail.AudioUrl` 和 `Status`（`0/1/2/3` = 等待/处理中/成功/失败）。
3. **文件后缀骗人**：服务端只返 WAV（`Content-Type: video/mp4` 是抖音 vod 默认
   头），但 URL query 里 `mime_type=audio_wav` 是真格式。修复：嗅探 URL + 文件
   magic，自动把 `.mp3` 重写为 `.wav`。

跑通后顺手把 skill 脚本和文档大改：去掉启发式 `extract_audio`（响应形态已经
完全确定）、加 `--format mp3`（ffmpeg 转码）、`--dry-run`、`--timeout`、
`--rewrite` 等。

## 时间线

| 时间 | 事件 |
| --- | --- |
| 11:32 | 第一次调用，返 `200028 APINoSource`。SKILL 误诊为「未开通服务/未配 TOS」。 |
| 11:35 | Erik 截图显示已开通「按时长计费」实例 `Cv_service_AI-music...` 且状态「正式调用」 |
| 11:35 | 拉官方错误码 doc：`200028` 的真实语义是「没有可用资源包」，**与是否开通服务无关** |
| 11:36 | 拉生成纯音乐 doc：发现 `GenBGM`（套餐包）和 `GenBGMForTime`（按时长）**是两个 Action** |
| 11:36 | 改成 `GenBGMForTime` → 拿到 `TaskID` |
| 11:36 | 撞轮询失败：所有 `QueryGenBGM*` Action 名都不存在 |
| 11:37 | 拉 doc 侧栏「查询任务」真实 doc id = `/docs/84992/2100960`，Action = `QuerySong` |
| 11:38 | 改完轮询，端到端跑通，`/tmp/bgm_gentle_60.wav` 落盘（10 MB / 60.000s） |
| 11:40 | 第二个 prompt 撞 `50000001 MusicSimilarityDetectionNotPassed`（版权校验） |
| 11:40 | 切 prompt + `--rewrite` 跑通 ambient / eastern 两条 |
| 11:43 | 重写整个脚本（去掉启发式、加 `--format/--dry-run/--timeout`、改 `QuerySong` 锁定） |
| 11:44 | 跑通 mp3 转码路径（10 MB wav → 1.4 MB mp3） |

## 关键文档证据

- 错误码 doc `/docs/84992/1404675`：`200028 APINoSource = 没有可用资源包`
- 生成纯音乐 doc `/docs/84992/2100970`：明确两个 Action + 30s 短音乐易触发
  版权校验（`50000001`）的警告
- 查询任务 doc `/docs/84992/2100960`：Action=`QuerySong`，请求体 `{"TaskID": "..."}`，
  响应 `Result.SongDetail.AudioUrl`，`Status` 编码 `0/1/2/3`

## Skill 改动清单

**scripts/generate_bgm.py**（整体重写，~555 行）：
- `Action=GenBGMForTime` 写死为唯一提交入口（CLI 不再暴露 `--action` 切换）
- `Action=QuerySong` 写死为唯一轮询入口（替换原 5 个候选名）
- 新增响应解析 `parse_envelope` / `poll_task` 严格按官方 doc 字段名
- 新增 `download_audio` 自动嗅探 wav 后缀
- 新增 `transcode_to_mp3`（ffmpeg libmp3lame 192k） + `--format {wav,mp3}` 选项
- 新增 `--dry-run`、`--timeout`、`--rewrite` 选项
- 删除 `extract_audio` 的 6 种启发式（响应形态已确定，启发式是空想的防御代码）
- 删除 `Genre/Mood/Instrument/Theme` 字段（v5.0 不再支持）
- 错误码表从 5 个扩到 16 个（覆盖 100011/200020-200024/200026/200027/300030/300052/400040/50000001）

**SKILL.md**（重写）：
- 砍掉「同步/异步双形态兼容」「best-effort 候选名」等过时段落
- 明确「默认走按时长计费」「不需要自建 TOS Bucket」两个关键事实
- 「已知坑」按踩中频次重排：`200028` → `50000001` → `QuerySong` 名字 → 后缀骗人
- 加 sub-agent fallback 提示（撞 50000001 时让调用方改写 prompt 重试）
- 改用「接口选型（一句话）」开头表，避免误读

**references/api-links.md**（重写）：
- 补 `QuerySong` 真实 doc id（之前只写"侧栏"，找不到）
- 修正 `200028` 真实语义
- 补 `TosBucket` 可选 + AIGC 场景不需自建桶的说明
- 错误码从 5 个扩到 16 个

## 留给调用方的建议

1. **撞 `50000001` 的标准三步**：
   - 改写 prompt（加 3-5 个具象描述：具体乐器/节拍/参考场景）
   - 加 `--rewrite` 让 BigMusic 自带 LLM 改写
   - 真正无奈才换 `mmx-cli` 走 MiniMax
2. **批量生成时**：`--timeout 120s` 足矣（实测 60s 任务 15-25s 内返回）
3. **混音场景**：默认 wav 进 ffmpeg 混音最稳；mp3 适合做 `<audio>` 标签网页嵌入
4. **签约时**：Erik 账号是按时长，**禁止切到 `GenBGM`**（套餐包），否则 200028

## 还没做（后续可接）

- BGM 与 `video-composer` / `src/worker/orchestrator.py` 接线（SKILL.md 末尾的
  「与 orchestrator 的衔接」段落已写好接线点，但代码未动）
- `TosBucket` CLI 暴露（`--tos-bucket`），目前脚本已支持 `build_request_body`
  参数，只是 CLI 没加 flag
- 批量并行：脚本没有并发安全保证，轮询是单任务；要批量时包一层 asyncio
- 撞版权后的 LLM 改写 sub-agent 实际接入
