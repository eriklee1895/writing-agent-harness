# seed-audio-1.0 官方实践手册对照与多参考/延长能力补测（2026-08-27）

## 背景

Erik 提供字节内部《豆包音频生成模型1.0 实践手册》（飞书 wiki，2026-06 发布），要求对照 seed-audio-gen skill 找可借鉴点。手册是 UI 体验中心向的使用指南，但暴露了几个我们 skill 未覆盖或未实测的能力。

## 实验验证（2026-08-27，真实 API 调用）

| 实验 | 结果 |
|---|---|
| 2 条参考音频 + `<<TGT_SPK1>>/<<TGT_SPK2>>` 绑定 | ✅ 成功，字幕干净无 token 泄漏（37s/24s） |
| 2 条参考音频 + `@音频1/@音频2`（UI 语法） | ✅ 同样成功 |
| 3 条参考音频 + 三个 TGT_SPK | ✅ 成功（5.2s） |
| 4 条参考音频 | CLI 前置拦截（官方上限 1-3 条） |
| 图片参考 `image_data` | ✅ HTTP 200 返回音频（此前有 flag 但从未实测） |
| 图片 + 音频参考混用 | ❌ API `45001001: image reference cannot be mixed with audio or video references`（报错信息还暴露 API 存在 video reference，未文档化） |
| `音频总时长：15秒` 声明 | ✅ 输出精确 15.0s |
| 顶层 `section_id` 字段 | 200 接受但效果不可验证（未知字段可能被静默忽略）→ 不采用 |

## 关键结论

1. **多参考音频绑定语法**：官方 HTTP API 文档（2550782，2026-08-20 更新）明确写的是 **`@音频N`**——「通过 @音频N 引用 references 中对应位置的参考音频，编号从 1 开始……上传顺序须与 @音频N 编号严格对应」。手册后台 demo prompt 里的 `<<TGT_SPK1>>`（"饰演者为"）是内部形式，实测两种都产出干净音频；skill 文档以官方契约 `@音频N` 为准，`<<TGT_SPKN>>` 仅作为可用内部别名备注。最初 prompt-guide 里的 `@Audio1` 是未验证的臆测写法，已废弃。绑定方向（第 N 条参考 → @音频N 的角色）API 文档有书面保证；音色效果仍建议人耳试听确认（测试音频在 `/tmp/seedaudio-doc/exp/out/`）。
2. **官方文档核对的参数契约**（用 volcengine-doc-fetcher 抓 2550782）：参考音频最多 3 条、单条 ≤30s、≤10MB、格式 wav/mp3/pcm/ogg_opus；参考图片最多 1 张、≤10MB、jpeg/png/webp；**图片不能与 audio_data/audio_url/speaker 混用**（speaker 互斥是初版遗漏，已补 CLI 校验）；speaker/audio_data/audio_url 三者互斥；语种官方列 18 个（手册 6 月版写 20 个，多印尼语/瑞典语，guide 已按 API 文档标注差异）；时间轴控制（总时长+人声时间段）为官方明确支持。
3. **音频延长 workflow**：官方文档明确「以此作为参考输入延长音频，可以在多次音频延长中保持音色的高度一致」——即把上一段输出回灌为 `--ref-audio`。不需要 section_id，现有 references 机制即可支撑，补文档即可。
4. **图片参考**：API 已支持（手册 UI 标注「敬请期待」但 API 先行），不能与音频参考或 speaker 混用，已做 CLI 前置校验。
5. **Prompt 工艺增量**（来自官方 6 个成片案例）：角色列表前置 + 风格标签（现代剧/古装剧/播客/译制片）、口音（台湾腔/东北腔/译制腔）、声音处理（电话失真/遥远）、群杂（群体喊声）、非语言词汇（气声/吞口水/磕巴/尖叫/哭腔）、跨角色重叠（"句首和笑声重叠"）、播客毛边感（附和声"对/嗯/是"、吞字、停顿）、配乐器声部具象化（弦乐组/跳音/pad 铺底）。
6. **文本密度机制官方确认**：手册写「若输入的文本较长，为了在有限时间内完成，语速可能会相应加快」——印证我们 400 字台词建议。

## 落地改动（branch `feat/seedaudio-handbook-optimizations`，PR #15）

- CLI：`--ref-audio` 改为可重复（action=append，本地路径/URL 自动检测），最多 3 条；`--speaker` 与 `--ref-audio` 互斥；图片+音频、图片+speaker 混用前置报错（45001001/文档约束）；`--ref-audio-url` 保留为隐藏别名。测试 9 → 15 全过。
- SKILL.md：多参考 Quick Start 示例（`@音频N`）、Reference 表重写（含格式/大小/数量约束）、Long-form Audio Extension 章节、场景速查表加两行。
- prompt-guide：Duration Control 章节（总时长声明 + 时间戳）、`@音频N` 多参考章节（多人多音色/组合参考/一声多角/延长，附 `<<TGT_SPKN>>` 别名备注）、18 语种章节（标注手册 20 语种差异）、导演词汇（角色列表/口音/风格标签/非语言/群杂/电话音效/播客毛边）、Example 5 播客对谈（已实测 23s 成功）。

## 未做

- `section_id` CLI 封装：字段效果不可验证，延长 workflow 用 references 回灌已够。
- video reference：API 报错信息暴露其存在，但无任何文档，不碰。
- 音色克隆效果人耳验证：`@音频N` 绑定顺序有官方文档书面保证，但音色像不像仍建议试听（A_tgt_spk / B_at_yinpin / 015805_0de52c 三个文件可对比）。
- 教训：WebFetch/curl 抓不到火山 JS 文档页时应直接用项目 `volcengine-doc-fetcher` skill（Playwright）；先读官方参数表再定语法，比从 demo 反推更可靠（`@音频N` vs `<<TGT_SPKN>>` 的反复即因此而来）。
