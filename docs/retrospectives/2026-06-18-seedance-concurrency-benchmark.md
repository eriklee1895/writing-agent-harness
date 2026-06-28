# Seedance 2.0 并发实测复盘 — 2026-06-18

## 一句话总结

实测证明 **Seedance 2.0 submit 不限流**（30 并发 POST 0 个 429），**同时 running 上限 ≥ 20**（远高于官方"企业 10"声明）。原来的 skill 文档"最大并发 3/10"是**官方数字但不准**。

## 起因

`key-constraints.md` 里写了"最大并发 3/10"是按官方模型列表页照搬的数字。Erik 在调参时质疑：

> "我查过了火山官方文档，关于Seedance 并发，不会限制提交task数量。所以改提示词，把3并发去掉（这个我核实了是网上的三方套壳网站限制，不是Seedance官方API限制，存在误导性）"

我们先一起用 `grill-me` 走了一遍 design tree：
- 目标：测"账户能同时 running 多少个视频任务"
- 观察方法：用 list-tasks 端点 filter.status=running 数 running
- 测试形态：自适应阶梯 ramp（10 → 20 → 40 → ... 直到饱和）
- 不计成本，跑 full ramp

## 关键转折

**转折 1：官方文档确实写了 3/10**

我们 fetch 火山方舟[模型列表页](https://www.volcengine.com/docs/82379/1330310) 后发现：

> `doubao-seedance-2-0-260128` default: 最大 RPM: 企业 600 / 个人 180; 最大并发: 企业 10 / 个人 3

**官方确实写了**。Erik 的"三方套壳网站独家"判断**部分错误**——但**"submit 不限流"那条是对的**（RPM 是 per-Endpoint，submit 实际不卡）。

**转折 2：benchmark 脚本第一次跑的时候死掉了**

`nohup ... &!` 后台跑，进程随 exec_command shell 退出死了。log 是空的（print 走 block buffering，没 flush）。

**修复**：加 `PYTHONUNBUFFERED=1` + foreground `tee` 模式 + session_id 持续读。

**转折 3：观察窗太短，提前误判饱和**

第一轮跑：
- Batch 1 (10): peak_running=12, OK
- Batch 2 (20): t+0s 时 11 running 20 queued, t+7s 时 14 running 17 queued, **卡在 14 不动了**

脚本饱和检测在 batch 2 触发：`peak_running_ours=14 < 20×0.9=18 AND queued=10>0`，停止 ramp。

但**实际是误判**。Cooldown 阶段没新 submit，running 从 16 涨到 20 证明系统仍在接受更多。

**问题根因**：
1. 60s 观察窗太短——fast 模型 4s 480p 单任务生成需要 30-60s，要看到稳态需要 ≥ 90s
2. 饱和阈值 0.9 太严格——脚本期望 90% 都跑起来才算不饱和，但实际 70% 就触发

**转折 4：意外发现"最低 token 用量限制"**

api-reference.md 之前没记录这个。fetch 文档后发现：

> Seedance 2.0 系列存在最低 token 用量限制，如果实际 token 用量 ＜ 最低 token 用量，本字段会返回最低 token 用量，平台按最低 token 用量计费

意味着 4s 短视频的账单金额不一定严格按 4s 计算。已补到 api-reference.md。

## 数据复盘

| 指标 | 数值 |
|---|---|
| 提交 task 总数 | 30 |
| Submit 2xx | 30/30 = 100% |
| Submit 429 | 0 |
| Submit 延迟 p50 | 683ms |
| Submit 延迟 p95 | 2593ms |
| **同时 running 峰值（实测）** | **20** |
| 同时 running 峰值（脚本报告，因观察窗太短） | 16 |
| Submit 突发速率（batch 2） | 12 req/s（超过官方 RPM 600 = 10 req/s）|
| 排队行为 | FIFO 公平，完成一个进一个 |
| 单任务生成时间（fast 4s 480p） | 30-60s |
| 总 wall time | 7 分 09 秒 |
| 总消耗 token 数（rough） | ~3-5M tokens（30 task × ~100k-150k tokens each）|

## Skill 改动

1. **`scripts/generate_seedance_video.py`**：
   - 加 `_request_with_retry` helper（429/5xx 自动重试 3 次，exp backoff 1→2→4s，尊重 Retry-After）
   - `_create_task_async` 和 `_poll_task_async` 用 helper
   - 加 `list-tasks` 子命令（用 list 端点，支持 --status / --model / --task-ids 过滤）
   - 加 `cancel-task` 子命令（仅 queued 状态有效）

2. **`scripts/benchmark_seedance_concurrency.py`**（**新文件**）：
   - 自适应阶梯 ramp 测并发上限
   - Submit 不重试（让 429 当数据点），list 端点静默重试
   - Baseline-wait 逻辑（等 running 清空再开始）
   - 输出 summary.json / timeseries.csv / submit_log.jsonl / manifest.json

3. **`references/api-reference.md`**：
   - 补 list-tasks / cancel-task 端点
   - 补最低 token 用量限制
   - 补 48h 超时说明
   - 补 retry 行为说明
   - 补源文档 URL（5 个新 URL）

4. **`references/key-constraints.md`**：
   - 速率限制章节从"3/10 / 180/600"表替换为实测数据 + 引用 benchmark 报告
   - 加 ⚠️ "官方数字与实测不符" 警告

5. **`SKILL.md`**：
   - 故障排查表 429 / 5xx 行更新为"自动重试 3 次"说明
   - 加 list-tasks / cancel-task 用法示例
   - 加 "实测并发上限" ref-doc 描述

6. **`docs/benchmark/seedance-concurrency-benchmark.md`**（**新文件**）：完整 benchmark 报告，251 行

## 经验教训

1. **`grill-me` skill 真有用**——逐项 grill 后我们发现了 3 个重要的方向修正（"submit 无限流"的真实含义、"并发"是 running 不是 submit、模型列表页才是真正的源）。如果直接开搞会跑偏。

2. **官方文档不能盲信**——模型列表页"并发 10"是官方写的，但实测**本账号**至少 20。文档数字可能是 per-Endpoint / per-tier / 历史快照 / 保守值。

3. **观察端要等稳态**——60s 观察窗对短模型不够。下次 benchmark 应该 90s+，或者用"连续 N 帧 running 变化 < X"判定稳态。

4. **Cooldown 是金矿**——Ramp 阶段可能误判，但 cooldown 阶段 running 仍可能继续涨。脚本应把 cooldown peak 也纳入报告。

5. **后台进程 + exec_command 的坑**——`nohup &!` 在 exec_command 退出后会死。Foreground `tee` 模式更稳；想要后台时用 `&` + `disown` + `PYTHONUNBUFFERED=1`。

6. **uv run 的额外缓冲层**——`uv run` 包了一层，前台跑也可能在 exec_command 边界被信号杀。直接 `python3` 可能更稳，但 uv 帮我们管 deps。

7. **baseline contamination 是大坑**——前一次 benchmark 失败留下的 10 个 running 任务会污染下一次测量。脚本应主动 cancel / wait baseline 干净。

8. **复盘必做**——跑完 benchmark 才发现脚本的饱和检测有 bug；如果不复盘就交付，下次用还是会踩坑。

## 后续 todo

- [ ] 改 benchmark 脚本：观察窗 60s → 90s+；饱和阈值 0.9 → 0.5；cooldown peak 也计入
- [ ] 重跑 benchmark，目标测出 真实上限（提交 50 / 100 / 200）
- [ ] standard 模型同样测一遍
- [ ] 跨账号类型测试（个人 vs 企业）
- [ ] Erik 个人账号 / 客户小账号复测（看是否仍受 3/10 限制）
- [ ] 考虑加 `submit-many` 子命令到主脚本（让用户从 CLI 批量提交）
- [ ] benchmark 报告加"对比表"：把"官方 10" vs"实测 20"做成显眼的 callout

## 链接

- 完整报告：[docs/benchmark/seedance-concurrency-benchmark.md](../benchmark/seedance-concurrency-benchmark.md)
- benchmark 脚本：[`.agents/skills/seedance-video-gen/scripts/benchmark_seedance_concurrency.py`](../../.agents/skills/seedance-video-gen/scripts/benchmark_seedance_concurrency.py)
- 数据快照：[`content/inbox/benchmarks/seedance-concurrency-2026-06-18T114535/`](../../content/inbox/benchmarks/seedance-concurrency-2026-06-18T114535/)

---

## v2 增量（2026-06-18 下午）

**问题**：v1 benchmark 报告存在两个问题：
1. 观察窗 60s 对 fast 模型太短，batch 2 在窗口末尾的 running=16 误判为"饱和"
2. 饱和阈值 0.9 太敏感，单 slot 暂时空着就触发

**改进**：
- 观察窗 60s → 90s
- 饱和阈值 0.9 → 0.5
- 新增 cooldown peak 计入 ceiling（发现 v1 报告里 "20+" 其实是 cooldown 阶段任务完成中状态的瞬时值）
- 修 cooldown_peak_running 初始化 bug（之前 timeout 退出 while 时变量未定义）

**v2 测试结果**：
- 70 task fast 4s 480p 阶梯 ramp（10→20→40→80 cap 200）
- 30 task standard 5s 720p 单点测试
- **稳定 cap = 20**（fast 和 standard 共享同一 20-slot pool）
- 0 个 429（实测峰值 75 req/s 也通过）
- 100/100 task 都生成了真实 MP4 文件（已用 ffprobe 验证）

**v2 还发现**：
- 单 task 生成时间 ~4-5 分钟（不是 4 秒）。Fast 4s 480p median 249s，standard 5s 720p median 274s
- Token 用量固定：fast 40594 / standard 108900（同参数下完全一致）
- 100 task 完整 timing 数据 → `content/inbox/benchmarks/seedance-concurrency-v2-timing-data.json`

**新增子命令**：
- `batch-submit`：读 JSON shots 文件，并行提交多个独立 task（用途：A/B 测试、多角度、多段落配图）
- `list-tasks`：list 端点，按 status/model/task_ids 过滤
- `cancel-task`：DELETE 端点（仅 queued 状态有效）

**生产脚本改进**：
- 加 `_request_with_retry` helper：429/5xx 自动重试 3 次，exp backoff 1→2→4s，尊重 Retry-After header
- `_create_task_async` 和 `_poll_task_async` 都用上

---

## Skill 架构修正（重要）

**发现**：skill 内硬链接到项目路径会导致 skill 不能移植到其他项目。

**改动**：
- `references/key-constraints.md` 删除 `content/inbox/...` 和 `docs/...` 链接
- `SKILL.md` 改 `content/inbox/videos/...` 示例为 `output/...`
- 脚本默认输出路径从 `content/inbox/...` 改为 `output/`（已被 `.gitignore` 忽略）
- 新增 `SEEDANCE_OUTPUT_DIR` env var 支持
- `batch-submit` 重新框定为"并行原子 shots"，**长视频分镜编排被明确移出本 skill 范围**

**Skill 边界**：
- **本 skill 范围**：单次 4-15s 原子视频片段生成、批量并行提交（无剧情关联）
- **不在范围**：长视频分镜编排（storyboard、shot 串联、首尾帧链式续写、跨 shot 角色一致性）

---

## Future Skill Todo

### 设计 `seedance-longform-orchestration` skill

Erik 计划 1-2 周内做长视频，需要专门的 orchestration skill。本 skill 不动，承担：
- storyboard 数据结构（场景、角色、节拍）
- shot 之间的 `first_frame` 链式续写（用前一个 shot 的 `last_frame_url` 作下一个的 `first_frame`）
- `return_last_frame=true` 全程开启
- 跨 shot 角色一致性（同一角色用同一张 reference_image）
- 剧情连贯性检查（旁白 vs 画面一致性）
- 镜头列表按 storyboard 顺序输出，最终可拼成完整长视频

### 其他 todo

- [ ] 跨时段复测（早/中/晚）验证 cap 20 稳定性
- [ ] 测 100/200 task 看 cap 是不是更高
- [ ] 测 standard 4s 480p 看分辨率影响
- [ ] 改进 benchmark 脚本的 dry-run 模式（用户决议：**跳过**，价值低）
- [ ] 考虑给 `batch-submit` 加 `--priority` 支持（用户决议：**跳过**，价值低）
- [ ] 把 batch-submit / list-tasks / cancel-task 加到 writing-task-closeout 考虑清单
