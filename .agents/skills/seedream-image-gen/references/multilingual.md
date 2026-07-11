# 多语种排版与本地化 (Multilingual Typography & Localization)

适合：跨境电商 hero banner、海外宣传海报、多语种菜单/会议海报、品牌 VI 跨国版本、海外社媒 cover、节日跨文化版本、宗教/地区性主题内容、产品本地化素材库。

Seedream 5.0 Pro 在多语种排版上**整体 9/10 平均**，覆盖 10+ 语言，是跨境内容的高性价比选择。强项是字符精度高、脚本隔离干净；弱项是高特异风格（瘦金体、Diwani 严格版）会落到通用变体上，本地化文化场景的人脸/服装/建筑会偏通用。

## 强项

- **CJK 字符精度极高**：中文/日文/韩文字符几乎零误差（包括冷门字如「和」印章、「戊戌年制」落款、「越境EC」中日混排）
- **拉丁变音字符全准**：法文带音标（RÉVOLUTION、é è）、土耳其语 İ/ş、德语 ä/ö/ü、西语 ñ、越南语 ơ/ư/Hồ/đ——全部正确
- **脚本隔离干净**：多语种同屏（4 语种 hero banner）无字符串位、无跨脚本污染
- **Hangul 字符组合正确**：5 个音节 blocks 拼装无误，几何/衬线字体切换稳定
- **Arabic RTL + 字符连接**：lam-alef ligature、shadda、final-ha 都正确渲染
- **本地化文化（人种/服装/建筑）整体通过**：东亚/中东/欧洲/东南亚人种识别对、传统服装（kimono/abaya/Tracht/lodden jacket）渲染准确
- **脚本-specific 字体联想**：Arabic 联想到 Diwani、Naskh；CJK 联想到 hanko 印章、瘦金体候选；Korean 联想到 cheonil bo

## 弱项

- **严格书法字体缺失**：瘦金体 (Slender Gold) 落到 generic 行书/草书；Diwani 落到 Naskh-cursive 混合；prompt 越精确越容易缺。**修复**：负 prompt 加 `避免行书/草书`；给风格细节签名描述（如 "Song Huizong 秾芳诗帖 风格的瘦金体 knife-thin horizontals sharp angular terminals"）
- **本地化"具体到城市"漂移**：Dubai 渲染成 Abu Dhabi 的 Sheikh Zayed 清真寺；Tokyo Shibuya 看不到具体 109 大楼。**修复**：要具体地标时 prompt 加 landmark 细节描述（"109 building cylinder shape with 109 logo signage"）
- **脸清晰度限制**：中等距离 portrait 脸偏 small/soft/featureless，难以确认具体国别。**修复**：close-up 特写或显式给族裔特征（"distinct Gulf Arab features: stronger brows, fuller lips"）
- **文化细节粒度**：Bavarian Tracht 通用而非 strict Bavarian（无 Hirschhorn 鹿角扣、无 Lederhosen）；Tokyo 街头无 109、无 X-pattern scramble。**修复**：加 `Hirschhorn deer-horn buttons + Lederhosen + Trachtenhemd + Tirolerhut with Gamsbart` 这种具体文化签名词
- **脚本风格走向中性**：Arabic 倾向于 Naskh-cursive 而非严格 Diwani；Korean 倾向于 geometric 而非手写 brush。**修复**：在 prompt 里 explicit style signature 词

## Per-Language 评分（满分 10）

| 语言 | 脚本 | 单语海报 | 同屏混排 | 本地化文化 | 最佳用例 | 反模式 |
|---|---|---|---|---|---|---|
| 中文 | CJK | 10 (L1) | 10 (L12) | — | 海报、书法国风 | 严格瘦金体 |
| 日文 | CJK | 9 (L2) | 9 (L12) | 9 (L15) | 浮世绘、和风海报 | 严格 Shodō 流派 |
| 韩文 | Hangul | 9 (L3) | 9 (L12) | — | 韩式品牌、editorial | 传统 cheonil bo 笔触 |
| 泰文 | Thai | — | — | — | 东南亚菜单/品牌 | 高尖角 ornamental Thai |
| 阿拉伯文 | Arabic | 8.7 (L5) | 8 (L12) | 8 (L16) | 跨境中东、海湾 VI | 严格 Diwani |
| 西班牙文 | Latin | — | — | — | 拉美社媒、菜单 | 带 ñ/í 重音排版 |
| 德文 | Latin | — | — | 9 (L17) | 巴伐利亚、奥地利文化 | 严格 Bavarian Tracht |
| 法文 | Latin | — | — | — | 法式 editorial、RÉVOLUTION 风 | — |
| 土耳其文 | Latin | — | — | — | 伊斯坦布尔 VI、İ/ş/ğ | dotted/dotless İ 区分 |
| 印尼文 | Latin | — | — | — | 东南亚群岛 VI | — |
| 越南文 | Latin (diacritic) | — | — | — | 越南本地品牌、diacritic 密集 | — |

（同屏混排 L12 = 4 语种同 banner；本地化文化指人种/服装/建筑/道具匹配）

## Recipes

### Recipe 1：4 语种跨境电商 hero banner（L12 验证 9/10）

```bash
uv run scripts/seedream_image_gen.py generate \
  --wide \
  --prompt "Cross-border e-commerce hero banner, 16:9 horizontal. LEFT third has large
  simplified Chinese 「跨境电商」 in white bold sans-serif on a deep crimson red panel;
  MIDDLE-LEFT third has Japanese 「越境EC」 in white bold gothic typeface on a navy blue
  panel; MIDDLE-RIGHT third has Korean 「크로스보더」 in white bold geometric Hangul on
  a warm beige panel; RIGHT third has Arabic 「التجارة الإلكترونية」 in white flowing
  Diwani script on a deep emerald green panel. Each panel has the language name in
  small ALL CAPS English (CHINESE / JAPANESE / KOREAN / ARABIC) in tiny text below
  the headline. Panels separated by 2% white gutters, clean editorial design, 2K"
```

**关键**：每语种在独立 panel、显式逐字 quoted、显式字体类型。脚本不会跨 panel 串位。

### Recipe 2：单语种海报（瘦金体防御版）

```bash
uv run scripts/seedream_image_gen.py generate \
  --portrait \
  --negative-prompt "行书, 草书, 楷书, modern calligraphy, sans-serif brush" \
  --prompt "极简中式美学海报，3:4竖版，米白宣纸背景 #f5efe0，正中竖排四个中文大字
  「宁静致远」，瘦金体 calligraphy (Song Huizong 秾芳诗帖 style: knife-thin
  horizontals, sharp angular terminals, slender wiry strokes, NO thick soft
  brushwork, NO 行书 drifting)，深墨色 #1A1A1A，字体占画面高度55%。
  落款「戊戌年制」四字小字在右下角用朱砂红 #B22222 square seal style (white
  characters on red background, NOT brush handwriting)。
  左上角一枚朱砂红圆形篆刻印章 (red circle seal with seal-script 「和」 character)。
  纯白无其他元素，无水印无英文，2K 高清印刷质感"
```

**关键**：瘦金体要 (a) 显式给出宋徽宗 + 秾芳诗帖锚点，(b) 列出 knife-thin/sharp/slender 的特征签名，(c) 加 negative prompt 防行书漂移。

### Recipe 3：本地化人物 + 建筑 + 服装（L15-L17 模板）

```bash
# Tokyo
uv run scripts/seedream_image_gen.py generate \
  --wide \
  --prompt "Photorealistic Tokyo Shibuya street scene at dusk, 16:9 horizontal,
  East-Asian Japanese young woman age 25 with short black bob, in stylish oversized
  beige trench coat (modern Harajuku streetwear, NOT traditional kimono),
  walking across the iconic Shibuya scramble crossing (X-pattern zebra stripes),
  Shibuya 109 building cylinder shape with 109 logo signage visible behind,
  Tokyo Tower red/orange international-orange lattice structure in distance,
  wet pavement reflecting pink/cyan neon, soft bokeh, 85mm editorial photography,
  no text no watermark, 2K"
```

```bash
# Dubai / UAE
uv run scripts/seedream_image_gen.py generate \
  --wide \
  --prompt "Photorealistic Dubai mosque courtyard at golden hour, 16:9 horizontal,
  Middle-Eastern woman age 28 with stronger brows, fuller lips (distinct Gulf
  Arab features, NOT generic Mediterranean), wearing white khimar-style hijab
  + long flowing beige abaya (NOT black formal abaya), walking through the
  Sheikh Zayed Grand Mosque marble colonnade, white marble columns with gold
  capitals, multi-foil horseshoe arches, intricate arabesque tilework in
  cobalt/turquoise/gold, mashrabiya screens, palm trees behind courtyard wall,
  warm golden hour sunlight, photorealistic travel photography, no text no
  watermark, 2K"
```

```bash
# Bavaria
uv run scripts/seedream_image_gen.py generate \
  --wide \
  --prompt "Photorealistic Bavarian Alps village scene, 16:9 horizontal,
  Northern-European man age 30 with fair skin, light brown hair, light stubble,
  wearing TRADITIONAL Bavarian Tracht: loden wool jacket with embroidered chest
  panel + Hirschhorn deer-horn buttons + paired Lederhosen + Trachtenhemd +
  Tirolerhut with Gamsbart chamois tuft (NOT generic Alpine jacket),
  standing in front of classic Bavarian Bauernhaus chalet with whitewashed
  ground floor + heavy timber Blockbau upper + wide overhanging Schindeldach +
  geranium-decked Blumenkasten balcony, cobblestone path, stacked firewood pile,
  Watzmann/Berchtesgaden snow-capped limestone Alps in background,
  warm golden hour light, photorealistic editorial photography, 2K"
```

## Anti-patterns

1. **严格书法体丢风格**——瘦金体/Diwani/Song Huizong 这种高特异性风格词会漂到通用变体
   - **修复**：加作者锚点（Song Huizong）+ 风格签名描述（knife-thin/sharp/slender）+ negative prompt 排除行书
2. **本地化 landmark 漂移**——Dubai→Abu Dhabi、Tokyo→generic
   - **修复**：具体 landmark 描述（Sheikh Zayed Grand Mosque、Shibuya 109 cylinder + 109 logo、X-pattern scramble）
3. **Bavarian Tracht 通用化**——无 Hirschhorn 鹿角扣、无 Lederhosen
   - **修复**：列出 `Hirschhorn deer-horn buttons + Lederhosen + Trachtenhemd + Tirolerhut with Gamsbart` 全部签名特征
4. **脸 distant → 族裔不清楚**——中东脸太远看不出 Gulf Arab vs Mediterranean
   - **修复**：close-up 特写 + 显式 `stronger brows + fuller lips + distinct Gulf Arab features`
5. **真实中文地名触发输入侧 safety block**——见 prompt-engineering.md 反模式 10
6. **高特异性 Thai/Arabic 装饰缺**——Thai ornamental flourishes、Islamic arabesque corner ornaments 渲染偏弱
   - **修复**：列出装饰元素清单 + reference image 引导
7. **多语种同屏无独立 panel**——所有语言共享画面时模型会冲突
   - **修复**：每个语种独立 panel，2% gutter 分隔

## Multilingual Prompt Formula

```
[Style] poster, [aspect ratio].
[Background layer]
[Title language 1] 「[exact text]」 in [script-specific typography], [position], [size].
[Title language 2] 「[exact text]」 in [script-specific typography], [position], [size].
[Decorative elements authentic to each script's culture]
[Negative space for iconography]
Authentic [cultural origin], no [conflicting scripts], 2K.
```

**核心**: 逐字 quoted + script-specific 字体描述 + 独立空间分配 + 显式负向冲突脚本。