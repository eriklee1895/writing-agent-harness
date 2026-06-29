# 中国朝代兴衰史系列海报 — 生图技术案例

**日期**：2026-06-28
**模型**：gpt-image-2（gpt-image-2-2026-04-21 via ofox gateway）
**产出**：7 张 1024×1792 竖版历史信息海报（秦、汉、唐、宋、元、明、清）
**输出目录**：[`content/assets/`](../../content/assets/)（`*-dynasty-rise-fall-poster.png` + 同名 `.json` prompt 元数据）
**编排方式**：唐朝手写 prompt 单张验证 → Workflow 多 agent 并行生成剩余 6 张
**总耗时**：唐朝 ~45s（单张）；其余 6 张 workflow 并行 ~28 分钟（含 research + generation，12 agents / 602k tokens）

---

## TL;DR

本次系列海报验证了 4 个可复用的生图技术模式：

| 模式 | 核心要点 | 可复用到 |
|------|---------|---------|
| **情绪弧配色法** | palette 绑定叙事阶段（兴→盛→衰→亡），而非平铺一套颜色 | 人物传记、公司史、产品生命周期、文明演进等任何带时间线的叙事信息图 |
| **Workflow 主题系列并行** | Phase 1 并行 research agent 输出结构化 prompt JSON → Phase 2 并行 generation agent 调 API | 任何"同风格系列 N 张图"批量生产场景 |
| **gpt-image-2 密集中文排版** | `--quality high` + `--text` 包 verbatim 中文 + 分 band 描述文字位置和字号层级 | 中文海报、信息图、课件配图、书单卡片等文字密集场景 |
| **Scaffolding preset 实战验证** | 全系列未使用任何 preset 调色板，仅保留竖版分栏+印鉴边框结构约束，inspiration 完全让位于历史题材 | 验证了 [[scaffold-presets-win-strong-style-conflicts]] 的设计在真实生产场景成立 |

---

## 产出总览

| 朝代 | 文件 | 年代 | 阶段 | 色系弧线 | 核心意象 |
|------|------|------|------|----------|---------|
| 秦 | [qin-...png](../../content/assets/qin-dynasty-rise-fall-poster.png) | 221–207 BC | 3段 | 玄黑→朱砂赤→铁青灰 | 青铜鼎/秦律竹简→长城兵马俑→断戟残碑血月 |
| 汉 | [han-...png](../../content/assets/han-dynasty-rise-fall-poster.png) | 202 BC–220 AD | 4段 | 赤红→琥珀→墨绿→灰白 | 马踏飞燕/丝路驼队→破裂铜鼎→白马书生→残汉旗枯树 |
| 唐 | [tang-...png](../../content/assets/tang-dynasty-rise-fall-poster.png) | 618–907 | 4段 | 金/朱红→翠绿→青铜→墨蓝 | 牡丹→丝路骆驼→断剑/杜甫→枯树 |
| 宋 | [song-...png](../../content/assets/song-dynasty-rise-fall-poster.png) | 960–1279 | 3段 | 朱红→烟雨青→墨蓝海 | 汝窑天青瓶→烟雨钓翁→崖山海战断桨 |
| 元 | [yuan-...png](../../content/assets/yuan-dynasty-rise-fall-poster.png) | 1271–1368 | 3段 | 铁马红→元青花蓝→烟尘灰 | 忽必烈白马→元杂剧戏台/青花瓷→残玉红巾 |
| 明 | [ming-...png](../../content/assets/ming-dynasty-rise-fall-poster.png) | 1368–1644 | 4段 | 宫墙红→青花蓝→铜褐→雪白 | 紫禁城/郑和宝船→青花手卷→断剑忧臣→雪中梅树 |
| 清 | [qing-...png](../../content/assets/qing-dynasty-rise-fall-poster.png) | 1644–1912 | 4段 | 八旗红→帝王蓝→烟褐→灰黑 | 八旗入关→乾隆龙椅/四库全书→鸦片战争硝烟→枯树孤影民国旗 |

---

## 技术 1：情绪弧配色法（Emotion-Arc Color Design）

### 核心思路

传统信息图用一套固定调色板，画面平、缺乏叙事张力。情绪弧配色法要求：

1. **先划分叙事阶段**（rise / peak / decline / fall），每个阶段绑定一个情绪关键词。
2. **每个阶段独立配色**，色相随叙事从暖→冷、饱和度从高→低、明度从明→暗。
3. **每个阶段有专属意象（motif）**，用物而非文字传达阶段情绪。
4. **整体用统一的背景纹理串联**（本次是 aged rice-paper 宣纸纹理），避免分 band 后像拼接。

### 秦朝案例（3段弧）

| 阶段 | 情绪 | 主色 | 辅色 | motif |
|------|------|------|------|-------|
| 统一（rise） | 肃杀/建制 | 玄黑（水德） | 朱砂红、金 | 青铜鼎、秦律竹简 |
| 扩张（peak） | 雄浑/铁血 | 朱砂赤（最饱和） | 青铜金、陶土色 | 万里长城、兵马俑 |
| 衰亡（fall） | 萧瑟/覆灭 | 铁青灰 | 褪色青铜、暗影靛蓝 | 断戟、残碑、枯树、血月 |

prompt 中对配色的描述不是平的色块列表，而是带情绪动词的渐变：

> - Band 1（rise）: "deep black with rich cinnabar-red undertones and gold accents"
> - Band 2（peak）: "intense cinnabar-vermilion red with burnished bronze-gold accents and subtle terracotta earth tones — **the most saturated band**"
> - Band 3（fall）: "cools dramatically to desaturated cold iron-gray and dark slate with touches of faded ash-bronze and shadowed indigo, with falling embers or drifting ash in the air"

注意 "the most saturated band" 和 "cools dramatically" 这种**向模型明确指示情绪走向**的词——模型对 "cooldown"、"desaturate"、"most saturated"、"faded" 这类色彩情绪词响应很好。

### 可复用模板

```
Band N (<phase_name>): background <color_direction> with <mood_keyword>; <saturation_instruction>;
Left: <emblem_color> with <text_color> characters '<label>'; date; subtitle banner; bullets.
Right: <motif_description> in <style_note>.
```

适用场景扩展：
- **产品生命周期**：launch（明亮品牌色）→ growth（饱和色 + 扩张意象）→ maturity（稳重灰调）→ decline（冷灰 + 退场意象）
- **人物传记**：少年（嫩绿/晨曦）→ 壮年（饱和暖色系）→ 中年转折（降饱和）→ 晚年（冷灰/暮色）
- **公司兴衰**：创业（车库冷光）→ 巅峰（饱和品牌色 + 摩天楼）→ 危机（暗红 + 断裂元素）→ 结局（冷灰）

---

## 技术 2：Workflow 多 agent 并行编排主题系列

### 为什么需要 workflow

单张唐朝海报手写 prompt 花了约 10 分钟构思。如果剩下 6 张都手写，需要 1 小时+ 且质量不稳定（人会疲劳）。用 Workflow 做 fan-out 可以：

1. **并行研究**：每个朝代一个 research agent，同时查找历史阶段、事件、人物、motif、当朝代表色。
2. **共享风格参考**：把唐朝海报作为 reference image 传给每个 agent，确保视觉语言统一（宣纸纹理、圆徽记、金边分割线、底部红印）。
3. **结构化输出**：research agent 输出 JSON（phases / color_arc / verbatim_text / full_prompt），generation agent 直接消费，避免 prompt 漂移。

### Workflow 结构

```
phase("Research") → parallel(6 × research_agent)
  输入：tang-dynasty-rise-fall-poster.png（风格参考）+ 朝代名 + 风格约束
  输出：{phases: [...], color_arc: {...}, verbatim_text: "...", prompt: "..."}

phase("Generate") → parallel(6 × generation_agent)
  输入：research agent 输出的 prompt
  执行：uv run scripts/gpt_image_2.py generate --size 1024x1792 --quality high
  输出：png 到 content/assets/
```

总 agent 数：12（6 research + 6 generation），总 token ~602k，总耗时 ~28 分钟（generation 是瓶颈，每个 ~3-4 分钟串行因为 API 并发限制）。

### 关键经验

1. **先做样板再批量**：唐朝海报作为 gold standard 先验证单张效果，确认风格 direction 正确后再批量。不要 6 张一起试错。
2. **Research agent 的 prompt 要给足历史约束**：明确要求用历史学家共识的阶段划分，不要 AI 编史；提供"输出必须包含的字段"（phases 数组、每个 phase 的颜色/年份/motif/bullet points），避免输出不可消费的自由文本。
3. **Generation agent 要继承 .env 环境变量**：sub-agent shell 默认不继承 OPENAI_API_KEY，在 generation prompt 里要明确写 `cd <project_root> && set -a && source ./.env && set +a && uv run ...`。
4. **图片输出路径提前约定**：统一 `content/assets/<dynasty>-dynasty-rise-fall-poster.png`，避免 agent 各自发挥写到 `output/` 或临时目录。

### Research agent prompt 骨架（示意）

```
你是一位中国历史信息图设计师。请为<朝代>（<英文年代>）设计一张兴衰史海报。

参考图片（唐朝海报）定义了视觉风格：宣纸底纹、顶部大标题、
分阶段横向色块、左侧圆徽记 + 右侧motif、底部红印亡国年份。

请输出 JSON：
{
  "dynasty": "<中文朝代名>",
  "english_name": "...",
  "period": "<年代范围>",
  "fall_year": "<亡国年份>",
  "phases": [
    {
      "label": "<阶段名，如'统一'>",
      "years": "<年份范围>",
      "subtitle": "<4字副标题>",
      "colors": "<背景色/辅色/文字色描述>",
      "mood": "<情绪关键词>",
      "motif": "<右侧意象详细描述>",
      "bullets": ["<历史事件bullet 1>", ...]
    },
    ...
  ],
  "color_arc_summary": "<一句话描述整体色彩走向>",
  "verbatim_text": "<所有必须精确渲染的中文字符，逗号分隔>",
  "full_prompt": "<组装好的完整 gpt-image-2 prompt>"
}

要求：
- 阶段数：秦朝/宋朝/元朝用3段，其他用4段
- 配色必须绑定情绪弧（兴暖盛饱和衰冷亡暗）
- motif 必须是<朝代>特有的代表性器物/场景（不能所有朝代都用龙/凤）
- bullet points 是真实历史事件，不能编造
- 所有中文文字必须在 verbatim_text 中列出
```

---

## 技术 3：gpt-image-2 密集中文排版实战

gpt-image-2 是目前渲染中文文字最准的模型（2026/06 时点），但密集文字海报仍需特定技巧。

### 核心组合

1. **`--quality high`**：文字密集场景必开。
2. **`--text` 字段包裹所有 verbatim 中文**：把必须精确渲染的字符（朝代名、阶段标签、年份、副标题、亡国年份印）全部列在 `--text` 里，逗号分隔。
3. **`--size 1024x1792`**：竖版海报用 portrait 长边 1792，给文字带足够像素。
4. **在 prompt body 中用分段描述指明文字层级和位置**：不是只列文字，而是告诉模型"左徽记内是什么字、字号多大、什么颜色、什么字体风格；subtitle banner 是什么颜色底什么字；bullets 是小号中文"。

### prompt 中的文字层级描述范例（秦朝 Band 1）

> On the left, a large circular medallion/emblem with gold-leaf double-ring border containing the two bold Chinese characters **'统一'** in **seal script (篆体)** on a cream inner disc. Below the emblem: date **'221-214 BC'** in small gold text, then a 4-character subtitle box **'开国建制'** in cinnabar-red on a gold banner, then **four short bullets in small readable Chinese**.

关键技巧：
- 每个文字元素都描述了**字体风格**（seal script / regular script）、**颜色**、**大小层级**（large / small / short bullets）、**载体**（on cream disc / on gold banner）。
- bullet points 说"four short bullets"而不写具体文字内容——具体内容放在 `--text` 里，模型自己 layout；写死反而容易溢出。
- 徽记内的大字（如"统一"、"扩张"、"衰亡"）用 **bold** 标记强调 verbatim。
- 不要在 prompt body 里重复列所有 bullet 文字，只在 `--text` 里列。模型会根据空间自主 layout，避免 prompt 过长导致截断。

### 文字渲染准确率观察

7 张海报全部成功渲染了：
- ✅ 顶部大标题朝代名（书法大字，全部正确）
- ✅ 英文副标题（serif 小字体，正确）
- ✅ 圆徽记内的阶段名（篆体/楷体，正确）
- ✅ 年份数字（正确）
- ✅ 4字副标题横幅（正确）
- ✅ 底部红印亡国年份（"××年亡"，全部正确）
- ⚠️ Bullet points 的小字：整体可读，偶有个别字笔画粘连或错字（密集小字是 gpt-image-2 当前的已知边界）

结论：**大字/标签/标题/年份级别中文 100% 可用；paragraph 级密集小字仍需事后人工检查**，这与官方 cookbook 的描述一致。

---

## 技术 4：Scaffolding Preset 的实战验证

本系列是 [[image-gen-presets-are-scaffolding-not-molds]] 重构后第一个真实生产案例，完整验证了 scaffolding 设计的价值：

### 本系列使用了什么 preset？

**没有使用任何 preset 的 inspiration 层**。7 张海报：
- 没有用 editorial-pencil-sketch 的淡彩/铅笔色
- 没有用 editorial-essay 的杂志/水彩 palette
- 没有用 technical-diagram 的蓝图/科技蓝
- 没有用 education-science 的手账/教科书配色

**完全使用历史题材自己的 palette**（玄黑、朱砂赤、青铜金、元青花蓝、宫墙红……），这些颜色由 research agent 根据朝代特征生成。

### 保留了什么 scaffold？

prompt 中保留了**纯结构性**的约束：
- 竖版 format（1024×1792）
- 顶部 title band + 中部水平 timeline bands + 底部 seal band 的三段式/五段式布局
- 左侧 circular medallion + 右侧 motif illustration 的左右分栏
- decorative Chinese borders（回纹 corner ornaments）
- gold divider lines between bands
- 底部红印（seal/chop）

这些结构约束本质上定义了"中国历史信息海报"这个**格式**，而不是"风格"——任何朝代、任何叙事主题的同类海报都需要这套结构。

### 验证结论

这正是 scaffolding 设计的预期行为：
1. **Topic-only 场景**（无风格 brief）：preset 提供完整结构 + 默认 inspiration。
2. **强风格 brief 场景**（本案例：中国历史题材，自己带完整 palette/mood）：preset 的 inspiration 层完全 yield，只保留结构 scaffold。
3. 最终产出的 7 张海报风格高度统一（同一套 scaffold 结构），但每张的 palette/mood 完全贴合朝代气质——**结构统一、灵感自由**。

这与 iteration-4 的 VLM 盲评结论（[[scaffold-presets-win-strong-style-conflicts]]）在生产环境完全一致。

---

## 完整 prompt 结构模板

基于本次秦朝（workflow 生成，质量最好）的 prompt 抽象出可复用模板：

```
Use case: infographic-diagram
Primary request: A premium educational vertical poster/infographic about <topic>
in <cultural_context>, designed to match an existing <series_name> collection.
Strictly vertical poster layout, 1024x1792 proportions.

Overall background: <unifying_texture> with <subtle_pattern>, overlaid with
<border_decoration> at all four corners.

Top header band (~15% of height): <header_bg_description>; large bold Chinese
calligraphy title '<main_title>' in <title_style>; behind the title, <watermark>;
below the title, English serif subtitle '<english_title>' in <subtitle_color>;
a <divider_style> separates header from body.

<N> horizontal timeline bands flow top-to-bottom, separated by <divider_between_bands>,
each occupying roughly equal vertical space (~<pct>% each):

Band 1 (<phase_label>, <mood> phase): background <color_description_with_mood>.
On the left, <emblem_description> containing <characters> in <font_style>.
Below: date in <text_spec>; subtitle box '<subtitle>' in <banner_style>;
<N> short bullets in small readable Chinese.
On the right side, <motif_description> in <artistic_style>.

Band 2 (<phase_label>, <mood> phase): background <color_description>.
[... same structure ...]

... (repeat for each band)

Bottom footer band (~10% of height): returns to <footer_bg>.
Center: a prominent red seal/chop containing '<fall_year>' in <seal_style>.
<corner_decorations> flanking the seal.

Style: <overall_style_description>, hybrid of <artistic_tradition>, with
<accent_details> on all medallions and borders.
<lighting_description>.
All Chinese characters must be correctly rendered, legible, and crisp.
<unifying_texture> texture unifies the whole poster top to bottom.

Style/medium: <medium>
Composition/framing: vertical poster, top Chinese calligraphy title,
  <N> horizontal timeline bands top-to-bottom, circular emblems on left,
  motif illustrations on right, bottom red seal banner
Lighting/mood: <lighting>
Color palette: <overall_palette_summary>
Text (verbatim): "<all_verbatim_strings_comma_separated>"
Constraints: vertical poster format, Chinese text clearly readable,
  <N> phases top-to-bottom timeline, <cultural_aesthetic>, historically accurate
Avoid: photorealism, neon colors, modern UI, 3D render, watermark, <culture_specific_avoids>
```

关键 augmentation flag 映射：
- `--quality high`（文字密集必开）
- `--size 1024x1792`
- `--text` → verbatim_text 字段所有字符
- `--style` → Style/medium
- `--composition` → Composition/framing
- `--palette` → Color palette
- `--lighting` → Lighting/mood
- `--constraints` → Constraints
- `--negative` → Avoid

---

## 坑点记录

1. **Sub-agent 不继承 .env**：在 Workflow 中 spawn 的 generation agent 需要显式 `cd <root> && set -a && source ./.env && set +a` 才能拿到 API key。
2. **Reference image 在 gpt-image-2 中占用 prompt budget**：唐朝作为 reference 传给 generation agent 时，prompt 需要更精简，否则 ~2000 token 的 prompt + reference image 可能导致 API 截断。本次最终没用 `--reference-image` 传唐朝海报，而是在 research agent 阶段就消化了风格特征，generation agent 只用纯文本 prompt。
3. **3段 vs 4段的选择**：朝代寿命短/阶段分明的用 3 段（秦 15 年、宋 319 年但南北宋分界清晰、元 97 年）；寿命长且有明确巅峰+转折的用 4 段。不要强行统一段数——叙事逻辑优先于视觉对称。
4. **Bullet points 不要写太长**：每张海报每段 4 个 bullet，每个 bullet 控制在 8-14 个中文字符，否则小字溢出 band。
5. **`--text` 字段不要放太多非关键文字**：bullet 正文不需要放进 `--text`（放了反而增加模型混淆），只放"必须精确渲染"的标签词（朝代名、阶段名、年份、印鉴文字）。

---

## 参考

- 风格设计原则：[[image-gen-presets-are-scaffolding-not-molds]]
- VLM 盲评验证：[[scaffold-presets-win-strong-style-conflicts]]
- 视觉生成规范：[docs/reference/visuals.md](../reference/visuals.md)
- gpt-image-2 skill：[`.agents/skills/gpt-image-2/SKILL.md`](../../.agents/skills/gpt-image-2/SKILL.md)
- Prompt augmentation schema：[`.agents/skills/gpt-image-2/references/prompting.md`](../../.agents/skills/gpt-image-2/references/prompting.md)
