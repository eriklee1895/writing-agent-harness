# AI Agent Skill 评测体系学习笔记

基于 skill-creator 框架的完整评测方法论，以 `seedance-video-gen` 技能为实战案例。

---

## 一、为什么 Agent Skill 需要评测

Agent skill 不是传统软件——它不提供确定性 API，而是一套**指导 agent 行为的指令和工具**。技能好不好用，无法通过单元测试判断。需要回答两个问题：

1. **功能问题**：有了这个技能，agent 完成任务的质量更高吗？
2. **触发问题**：agent 在正确的时机读了它吗？

skill-creator 为此设计了两层独立的评测体系。

---

## 二、评测体系总览

```
              ┌─────────────────────────────────────┐
              │        skill 评测体系                 │
              │                                     │
              │  ┌─────────────────────────────┐    │
              │  │ 层级一：功能评测 (benchmark) │    │
              │  │ A/B 对比：with vs without    │    │
              │  │ 测"技能是否让 agent 更好"    │    │
              │  └─────────────────────────────┘    │
              │                 │                    │
              │                 ▼                    │
              │  ┌─────────────────────────────┐    │
              │  │ 层级二：触发评测 (trigger)   │    │
              │  │ 测 description 触发准确率     │    │
              │  │ 防误触发 + 防漏触发          │    │
              │  └─────────────────────────────┘    │
              │                 │                    │
              │                 ▼                    │
              │       human review (viewer)          │
              │         迭代 → 收敛                  │
              └─────────────────────────────────────┘
```

---

## 三、层级一：功能评测 (Benchmark)

### 3.1 核心原理

同一个任务，两个 agent，一个带技能一个不带，对比产出。

```
用户任务 prompt ("用 Seedance 生成一段 9:16 的产品广告视频...")
        │
        ├──→ with-skill agent
        │     ├── 读 SKILL.md → 理解工作流程
        │     ├── 读 references/prompt-guide.md → 优化提示词
        │     ├── 执行 uv run generate_seedance_video.py → 调 API
        │     └── 输出：video.mp4 + manifest.json + prompt.md
        │
        └──→ without-skill agent
              ├── 凭通用知识写 Python 调 API
              ├── 自己实现轮询逻辑
              └── 输出：video.mp4 + task_metadata.json（结构不同）
```

**关键设计**：
- 两个 agent **同时启动**（同一批 Agent() 调用），消除时间偏差
- with-skill 读 skill 目录下的 SKILL.md 和 references
- without-skill 不允许读 skill 文件，完全靠自身能力
- 每个 agent 输出到独立目录，互不干扰

### 3.2 Eval 定义 (`evals/evals.json`)

```json
{
  "skill_name": "seedance-video-gen",
  "evals": [
    {
      "id": 1,
      "prompt": "用户自然语言任务描述",
      "expected_output": "人类可读的期望产出",
      "expectations": [
        "可机器验证的断言1",
        "可机器验证的断言2"
      ]
    }
  ]
}
```

**Eval 设计原则**：
- `prompt` 要像真实用户会说的话（带具体参数、场景、上下文）
- `expectations` 必须可机器验证（文件存在、字段值、内容含关键词）
- 覆盖技能的主要能力维度——seedance-video-gen 有 8 条 eval，覆盖文生视频、首帧、批量、教育动画+音频、短剧对白、首尾帧、多模态参考、竖屏社交媒体
- 最好有 3-5 条基础 eval + 2-3 条能力扩展 eval

### 3.3 工作空间结构 (Workspace)

```
seedance-video-workspace/
└── iteration-N/                  # 迭代轮次
    ├── eval-product-ad/          # eval 1
    │   ├── eval_metadata.json    # 描述、断言
    │   ├── with_skill/
    │   │   ├── run-1/
    │   │   │   ├── grading.json  # grader 产出的评分
    │   │   │   ├── timing.json   # token 和耗时
    │   │   │   └── outputs/      # agent 实际产出
    │   │   └── ...
    │   └── without_skill/
    │       └── ...
    ├── eval-first-frame/         # eval 2
    ├── ...
    ├── benchmark.json            # 聚合统计
    └── benchmark.md              # 人类可读的汇总
```

**Workspace 是临时产物**，不应提交 git（含 API 返回的 token/URL 等敏感信息）。

### 3.4 评分 (Grading)

用机械规则检查每个 expectation，不需要 LLM 参与——快、便宜、一致。

```python
def grade_product_ad(outputs_dir: Path) -> list[dict]:
    videos = find_any_mp4(outputs_dir)
    manifest = load_metadata_json(outputs_dir)
    
    return [
        {
            "text": "视频文件 video.mp4 存在且非空",
            "passed": videos[0].stat().st_size > 0,
            "evidence": f"Found {videos[0]} ({videos[0].stat().st_size} bytes)"
        },
        {
            "text": "manifest.json 的 ratio=9:16、duration=5",
            "passed": manifest.get("ratio") == "9:16" and manifest.get("duration") == 5,
            "evidence": json.dumps({...})
        }
    ]
```

输出 `grading.json`：
```json
{
  "expectations": [
    {"text": "...", "passed": true, "evidence": "Found /path/to/video.mp4 (1611175 bytes)"}
  ],
  "summary": {"passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67}
}
```

### 3.5 聚合 (Aggregation)

`aggregate_benchmark.py` 扫描所有 `run-1/grading.json` + `run-1/timing.json`，按 `with_skill` / `without_skill` 分组计算统计量：

```
With Skill:  58% ± 39% pass rate, 224s ± 151s, 45363 ± 28073 tokens
Without:     54% ± 25% pass rate, 154s ± 177s, 29055 ± 31164 tokens
Delta:       +4pp pass rate, +70s time, +16308 tokens
```

**关键指标解读**：
- Pass rate 的 stddev 大 → 技能在不同 eval 上表现差异大（我们的 ±39% 说明有些 eval 100%，有些 0%）
- Time delta 为正 → 技能让 agent 更谨慎、流程更完整（多写 prompt.md、manifest.json）
- Token delta 为正 → 技能本身增加了上下文消耗

### 3.6 seedance-video-gen 的 benchmark 结果

| 迭代 | Eval 数 | With Skill | Without Skill | Delta | 说明 |
|---|---|---|---|---|---|
| iteration-1 | 3 | **100%** | 56% | **+44pp** | 基础用例，优势明显 |
| iteration-3 | 8 | 58% | 54% | +4pp | 新增 5 个复杂用例，gap 缩小 |

**分析**：
- iteration-1 的 3 个基础 eval（文生视频、首帧、批量）with-skill 完胜——有 CLI 脚本和 reference 文档的 agent 不会在 API 参数、轮询逻辑、输出格式上犯错
- iteration-3 新增的 5 个 eval（教育动画+音频、短剧对白、首尾帧、多模态参考、竖屏字幕）gap 缩小——这些用例对 grader 检查更严格（音频、字幕、reference role），with-skill 也没完全做到位
- 真正的技能价值不在 +4pp 的 pass rate，而在**输出一致性**：with-skill 的 manifest.json、prompt.md、目录结构是统一的，without-skill 每次输出格式都不一样

---

## 四、层级二：触发评测 (Trigger Eval)

### 4.1 核心原理

技能再完美，如果 agent 不读也没用。`description` 字段是触发机制的入口。

```python
# run_eval.py 的核心逻辑
for each_eval_query:
    for 3_times:
        临时注册 skill command
        run_claude("-p", query, "--output-format stream-json --include-partial-messages")
        检测 Claude 是否调用了 Skill() 或 Read() 该 skill 文件
    trigger_rate = 触发次数 / 3
    pass = trigger_rate >= 0.5 匹配 should_trigger 标签
```

**关键技巧**：
- Stream event 早期检测——看到 `content_block_start` + `tool_use` 就直接判断，不等完整回复
- 60% train + 40% test 分割——找 `best_description` 时用 test set 避免过拟合
- 每个 query 跑 3 次——因为 LLM 有随机性

### 4.2 Eval 查询设计

需要 20 条查询：~10 条应该触发 + ~10 条不应该触发。

```json
[
  {"query": "用 Seedance 把这个脚本生成一段 5 秒的短视频", "should_trigger": true},
  {"query": "给咖啡做个竖屏广告视频带字幕和音乐", "should_trigger": true},
  
  // 近失案例（看起来像但实际不该触发）
  {"query": "帮我用 ffmpeg 把这段视频裁成 9:16", "should_trigger": false},
  {"query": "帮我生成一张文章封面图，2.35:1", "should_trigger": false}
]
```

**设计要点**：
- Should-trigger 覆盖不同语气、不同复杂度、不同领域
- Should-not-trigger 应该是"近失案例"——看起来像视频生成但实际是视频剪辑/图片生成/翻译
- 不能用 `"写一个 bubble sort"` 这种明显不相关的，对评测没有区分度

### 4.3 我们的 trigger eval 结果分析

```
原始 description:
  precision=100%, recall=0%, test=4/8

12 个 should-trigger 查询 → 0% 触发率 ← all FAIL
8 个 should-not-trigger 查询 → 100% 不触发 ← all PASS
```

**为什么 should-trigger 全部不触发？**

不是因为 description 写得不好——5 轮迭代优化后 recall 仍然是 0%。

根因：Skill 触发机制是这样的——Claude 只在判断**靠自己搞不定**时才查 skill。但 benchmark 里的 eval 查询都是单行文字描述（"用 Seedance 生成一段短视频"），Claude 看到这种请求的第一反应是"我可以直接写个 Python 脚本调 API"，而不是"我要去读那个 Seedance skill"。

真实生产场景：Claude 在一个多步写作任务中，读了一篇长文章、分析了语气、优化了插图，然后需要"把这段文字转成短视频"——这时候 skill 才会自然触发。所以 trigger eval 对复杂的复用型 skill 不是一个好度量。

---

## 五、迭代与人工 Review

### 5.1 Eval Viewer

`generate_review.py` 启动本地 HTTP server，生成一个内嵌所有 outputs 的 HTML。

**两个 tab**：
- **Outputs**：逐条 eval 看 prompt、with-skill 输出、without-skill 输出、grading 结果。下方有反馈文本框
- **Benchmark**：统计表格（mean±stddev、per-eval 明细、delta）

**关键机制**：
- HTML 是自包含的——视频、图片、manifest 全部 base64 内嵌
- 反馈自动保存（每次 focusout 事件），不需要点提交
- "Submit All Reviews" 把 `feedback.json` 下载到本地

### 5.2 迭代循环

```
Draft skill ──→ 跑 benchmark eval ──→ 跑 trigger eval ──→ human review viewer
     ▲                                                              │
     └────────── 读 feedback.json, 修改 skill ←─────────────────────┘
```

停止条件：
- 用户 feedback 全空
- pass rate 不再提升
- 用户说"满意了"

---

## 六、学习要点回顾

| 维度 | 层级一（功能评测） | 层级二（触发评测） |
|---|---|---|
| **测什么** | 技能是否帮助 agent 更好完成任务 | description 是否准确触发 |
| **怎么测** | with/without A/B 对比 | claude -p 单行查询触发率 |
| **验证方式** | 机械规则（文件、字段、内容） | 二进制（触发了/没触发） |
| **成本** | 高（真实 API call、视频生成） | 低（仅 LLM API call） |
| **eval 数量** | 3-8 条 | 20 条 |
| **输出** | benchmark.json + viewer | 触发率 + best_description |
| **什么时候有用** | 技能有可验证输出 | 技能需要精确触发时机 |

### 核心洞察

1. **A/B 测试是评测 agent skill 的最有效方式**——不是因为 agent 不知道怎么做，而是看技能是否让 agent 做得更快、更一致、更少犯错
2. **grading 要机械不要主观**——人工打分慢、贵、不一致；程序检查文件+字段快、便宜、可重复
3. **workspace 是临时产物**——含 API 返回数据，不入 git
4. **trigger eval 对复杂的复用型 skill 不是好度量**——单行查询测不出真实场景的触发需求
5. **iteration 的价值在于发现边缘情况**——iteration-1 的 3 条基础 eval 全是 100%，iteration-3 的 8 条扩展 eval 暴露了首尾帧和多模态参考的薄弱点

---

## 来源

- [skill-creator SKILL.md](file:///Users/eriklee/.claude/skills/skill-creator/SKILL.md)
- [run_eval.py](file:///Users/eriklee/.claude/skills/skill-creator/scripts/run_eval.py)
- [aggregate_benchmark.py](file:///Users/eriklee/.claude/skills/skill-creator/scripts/aggregate_benchmark.py)
- [grader.md](file:///Users/eriklee/.claude/skills/skill-creator/agents/grader.md)
- [seedance-video-gen skill](file:///Users/eriklee/code/my_project/writing-agent-harness/.agents/skills/seedance-video-gen/)
