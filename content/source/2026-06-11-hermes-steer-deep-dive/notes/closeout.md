# Closeout — Hermes steer 深度报告

## Closeout Status
Needs follow-up — content/HTML done & verified; git commit + push to `main` pending user confirm on whether `report.html` (base64) is tracked.

## Published State
- Status: `handoff-only` — 未发布任何渠道(用户决定暂不发微信公众号)。
- URL / appmsgid / platform ID: 无。
- wechatStyle (frontmatter): `agent-flow`(如未来发微信沿用)。

## Deliverables
- Canonical source: `content/source/2026-06-11-hermes-steer-deep-dive/article.md`(中文,带 frontmatter,10 节,4 个 Mermaid,代码逐字核证自 hermes-agent)。
- Self-contained HTML: `content/source/2026-06-11-hermes-steer-deep-dive/report.html`(2.2MB 单文件:粘性导航+scroll-spy、GSAP、内嵌 Inter/JetBrains Mono 字体、4 张内联 SVG 流程图 + 4 张概念插图 base64)。
- Build tooling: `assets/html-build/`(`build.mjs` MD→HTML 构建、`qa.mjs` headless QA、`dedent.mjs`、`verify-tighten.mjs`);`assets/diagrams/`(4 个 `.mmd` 源 + 渲染 SVG + extract/config)。

## Archive
- Local archive: `.local-archive/2026-06-11-hermes-steer-deep-dive/images/` — 4 张 gpt-image-2 插图 PNG + 各自 metadata JSON。
- Tracked provenance: 本文件 + 下方 prompt 清单 + `article.md` 内的 4 个 Mermaid 源。
- Media not committed: 4 张插图 PNG(`*.png` 已被 .gitignore 全局忽略)。
- 重建提示:`report.html` 可由 `cd assets/html-build && npm i && node build.mjs` 重建;build 会从 `assets/` 读插图做 base64 内联,跨机器需先从本 archive 取回 PNG,或按下方 prompt 用 `article-illustration` 重新生成。

## Illustration Provenance
模型 `gpt-image-2`(`article-illustration` skill,`--style-profile flat-tech-infographic --language en --quality high`)。生成两轮:首轮把 `--title` slug 误渲染为标题且多余 legend,加"无标题/无图例"指令重生成,保留第二轮(下列时间戳)。

| 文件(archive) | 用途(正文) | 尺寸 | prompt 要点 |
|---|---|---|---|
| `20260611-200737-hero` | Hero | blog-banner | running tool-call pipeline + STEER 气泡经虚线汇入某个 block 尾部,"append, don't interrupt";off-white 扁平矢量 + 琥珀点缀 |
| `20260611-200915-batch-vs-interrupt` | §1 | doc-hd | HUMAN interrupt-driven 不规则脉冲 vs AGENT batch-driven 均匀方块;右侧三出口 INTERRUPT/QUEUE/STEER |
| `20260611-201102-masquerading` | §4 | doc-hd | SYSTEM PROMPT 信任锚 →"trust ONLY this marker"→ TOOL RESULT(untrusted)尾部 OUT-OF-BAND USER MESSAGE 条;红色 "lookalike = spoof risk" |
| `20260611-201248-two-drains` | §6 | doc-hd | PRE-API DRAIN → API CALL → TOOL EXECUTION(锁,not interrupted)→ POST-TOOL DRAIN 循环;下方 `_pending_steer` thread-safe buffer 虚线接两个 drain |

## Retrospective
- 路径:`/article-ideation` 澄清需求(全新独立、聚焦 Hermes、独立 HTML)→ Workflow 编排(8 并行核证 + 分节起草 + 4 对抗式校验 + 修订)→ 生图/Mermaid → 单文件 HTML 构建 → headless QA → 收尾。
- 首个 Workflow 因单个 draft agent 一次性写整篇 ~8k 字而 stall(180s×6);改为并行分节写 + assemble 后跑通,research 阶段 resume 走缓存。
- 收尾前用户反馈两轮:代码块缩进(verbatim 带原文件深缩进)→ 写 `dedent.mjs` 规整;正文偏啰嗦 → 定向 concision pass −7.7%(对抗式 diff 校验确保 0 代码改动、6/6 来源 URL 不丢);字体不好看(系统回退到宋体)→ 内嵌 Inter+JetBrains Mono、中文留苹方。
- 外部事实 6 条 URL 全部核验(Codex app-server README / developers.openai.com / issue #12329 / Anthropic mitigate-jailbreaks / arXiv 2509.22830 / Simon Willison lethal-trifecta),正文标注日期与 fact/inference/speculation。

## Memory / Skill
- 更新 `single-file-html-report-build-qa`:补 Node(marked+hljs)构建变体、mermaid-cli 经系统 Chrome 预渲染 SVG、puppeteer-core headless QA、GSAP reveal 阈值坑、内嵌 Inter+JBM/中文留苹方的字体方案。
- 更新 `workflow-large-verbatim-write-stalls`:补"长文同样会 stall → 分节写 + assemble"。
- 未新增 skill(本流程未达稳定复用阈值;构建工具已随仓库留存)。

## Git / Task
- 只 stage 本报告目录,绝不 `git add -A`;`.env`/`*.png`/`node_modules`/`qa`/`.local-archive` 均已忽略。
- `report.html`(2.2MB base64)已确认进 git。
- 已合并 merge commit `3c0ecae` 并 push 到 `main`(origin/main 领先一 commit 时先 `git pull --no-rebase` 解决分离,再 push)。
