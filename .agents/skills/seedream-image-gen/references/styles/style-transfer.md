# 风格迁移 (Style Transfer)

适合：把任意一张参考照片 / 已有海报 / 已有插图，转化为另一种艺术风格 —— 中国水墨、浮世绘、梵高、剪纸、宫崎骏、皮克斯、赛博朋克、Low-poly、油画、水彩、铅笔速写、波普艺术、荷兰黄金时代静物、wallpaper、概念艺术。

风格迁移是 Seedream 5.0 Pro 的中高位能力（实测整体 ~9/10），且 prompt 完全决定成败——5 个高分与 3 个低分差距全部来自"承诺强度"的措辞。

## 关键发现（务必先看）

**承诺强度决定一切。** 同样的"中国水墨"主题，措辞不同实测分差 1 → 9.5：

| 措辞 | 实测分 | 模型行为 |
|---|---|---|
| "Inspired by Chinese ink painting aesthetic" | 1/10 | 当滤镜用，几乎不重绘 |
| "Rendered in Chinese ink-wash painting style" | 4/10 | 上了点彩色水彩味 |
| "Fully re-painted as a traditional Chinese ink-wash painting on rice paper, no photographic elements whatsoever, pure ink and brush" | **9.5/10** | 完全重绘，水墨专精领域 |
| "Fully re-painted... no photographic elements whatsoever" + negative prompt `photograph, photorealistic, 3D render` | 9.5/10 | 同上，负 prompt 边际改进 |

> **核心原则：开头用 "Fully re-painted as a X on Y surface, no photographic elements whatsoever"；中段逐字列出保留的主体元素；末尾加 "No text, no signature"。** 命名艺术家比描述技法强 2-3 倍（"Van Gogh" 比 "thick impasto" 强很多）；指定物理介质（"on rice paper"、"on rough canvas"、"on washi paper"）是隐藏触发器。

## 必加结构 Guardrails（按场景选）

- **开头（必填）**：`Fully re-painted as a <MEDIUM> in the <STYLE/ARTIST> tradition`
- **去照片化（必填）**：`no photographic elements whatsoever`
- **物理介质（强烈推荐）**：`on rice paper` / `on rough canvas` / `on washi paper with foxing` / `on torn notebook paper` / `on screen print with halftone dots`
- **保留主体（必填）**：`Preserve the composition exactly: <关键元素清单>`
- **末尾约束**：`No text, no signature, no watermark`
- **可选艺术家**：`<NAME> oil painting in the style of Starry Night over the Rhone` 显著强于 `<NAME>-style oil painting`

## 双参考 vs 单参考 vs 文字-only

| 方式 | VvG | 浮世绘 | 备注 |
|---|---|---|---|
| 文字-only，无风格参考 | **9.5** | 9.5 | 基线，对知名风格表现最好 |
| Subject ref + 风格 ref 双参考 | 8.5 | 9.5 | 略弱：风格 ref 的色板/构图会污染主体 |
| 仅风格 ref，无主体 | 10/10 风格, 5/10 主体 | — | 适用于"画一张 X 风格的新东西"，不适用"把现有照片转风格" |

**经验法则：** 知名风格（VvG / 莫奈 / 宫崎骏 / 毕加索）用文字-only 即可；冷门或专属风格（自家插画师、未公开艺术家）才需要风格 ref。**风格 ref + subject ref 容易互相稀释**，谨慎组合。

## Top 5 风格（实测稳定 9.5/10）

按稳定性排序：

1. **传统中国水墨 (Chinese ink wash)** — 9.5/10。黑白水墨、飞白笔触、朱印、宣纸肌理。中国模型训练数据强项。短 prompt 也行：`Chinese ink wash painting, black ink on rice paper`。
2. **浮世绘 (Ukiyo-e Japanese woodblock)** — 9.5/10。扁平色面、ぼかし渐变、靛蓝/粉色调、清晰轮廓。
3. **梵高 (Van Gogh post-impressionist)** — 9.5/10。漩涡天空、厚涂笔触、钴蓝/黄色调。`Van Gogh` 关键词能解锁整套笔触词汇。
4. **中国剪纸 (Jianzhi paper-cut)** — 9.5/10。红剪影、白底、繁复剪纸细节、传统祥云图案。
5. **波普艺术 (Pop art Warhol/Lichtenstein)** 与 **荷兰黄金时代静物 (Dutch Golden Age still life)** 并列 9.5/10。前者粗轮廓 + Ben-Day 半色调点；后者暗背景 + 厚涂 + 17世纪调色板。

提名：**宫崎骏人物肖像 (9.5/10)**、**针毡羊毛手作 (9.5/10)**、莫奈 (9/10)、像素艺术 (9/10)、纯线条艺术 (9/10)、水彩 (8.5/10)。

## 翻车区（实测 4-6.5/10）

1. **赛博朋克 + 已有点光的夜景照** — 5.5/10。原因是赛博朋克本质是 photorealistic 风格（Blade Runner 2049 是实拍），img2img 没有"风格距离"可跨越。**修复：** 改用 daylight 参考图 + 显式写 `sci-fi concept art painting, NOT cyberpunk photo`；或加 `--negative-prompt "photograph, photorealistic"`。
2. **宫崎骏式风景背景** — 6/10。柔化边缘 + 暖色调 + 滤镜感，没有 cel-shading / 硬轮廓 / 动漫化。**修复：** 显式写 `anime cel-shaded background with hard outlines, flat color, stylized clouds`。**注意：宫崎骏人物肖像工作完美（9.5/10）**，因为角色 cel 风格有强视觉签名。
3. **Low-poly 几何 3D** — 6.5/10。天空/水面三角面切得好，但建筑保留 photoreal。**修复：** 显式写 `every surface is flat triangular facets, no texture, no windows, no photorealism`。

附加小心区：
- **铅笔/石墨速写 (8/10)** — 渲染偏炭笔调子，不是清晰线+排线。
- **泛泛 "thick impasto oil" 无艺术家名 (8/10)** — 缺个性。

## Recipe

### Recipe 1：水墨山水（Chinese ink wash，9.5/10）

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image landscape.jpg \
  --no-negative-prompt \
  --prompt "Fully re-painted as a traditional Chinese ink-wash painting on rice paper, no photographic elements whatsoever, pure black ink and brush.
Preserve the composition exactly: karst mountain peaks, winding river, lone fisherman on a bamboo raft, dawn light from upper-right.
Flying-white brushwork on the mountains, soft ink wash in the sky, fine dry brush on foreground rocks, blank misty space between peaks, small red seal stamp at bottom right corner.
On rice paper with subtle foxing. No text, no signature, no watermark."
```

### Recipe 2：浮世绘 (Ukiyo-e, 9.5/10)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image seascape.jpg \
  --no-negative-prompt \
  --prompt "Fully re-painted as a traditional Japanese ukiyo-e woodblock print, no photographic elements whatsoever, no perspective depth.
Flat color planes with bokashi color gradation in sky and water, bold indigo and rose-pink palette, clean black outlines on every shape, stylized woodblock grain visible on all surfaces.
Preserve composition: large wave curling in foreground, Mt Fuji silhouette in distance, three fishing boats dwarfed by the wave.
Hokusai ukiyo-e aesthetic, on washi paper. No text, no signature."
```

### Recipe 3：梵高 (Van Gogh, 9.5/10)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image nightscape.jpg \
  --no-negative-prompt \
  --prompt "Re-render this exact scene as a Vincent Van Gogh oil painting in the style of Starry Night over the Rhone.
Thick impasto brushstrokes, swirling dynamic sky with curving cypress-like forms, bold yellows and cobalt blues, directional brushwork following the forms, canvas texture visible, post-impressionist oil painting.
Preserve the composition exactly: river bend, low horizon, glowing lights along the bank, stars in the sky.
No text, no signature, no watermark."
```

### Recipe 4：剪纸 (Jianzhi paper-cut, 9.5/10)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image scene.jpg \
  --no-negative-prompt \
  --prompt "Fully reimagined as a traditional Chinese paper-cut (剪纸 jianzhi) art piece.
Pure crimson red #C8102E silhouette on cream-white background, intricate scissor-cut detail showing every internal pattern, stylized ruyi cloud motifs and geometric lattice patterns throughout.
Preserve composition subject and silhouette exactly, but render the entire scene in two-tone red-on-cream paper-cut aesthetic.
Traditional Chinese New Year decorative style, on rice paper. No text, no signature, no watermark."
```

### Recipe 5：荷兰黄金时代静物 (Dutch Golden Age still life, 9.5/10)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image stilllife.jpg \
  --no-negative-prompt \
  --prompt "Fully re-painted as a 17th-century Dutch Golden Age still life oil painting.
Deep black background, dramatic chiaroscuro with single warm key light from upper-left, thick impasto oil paint with visible brushwork, rich saturated palette of deep reds, ochres, browns, with bright highlights on fruits and metal.
Preserve the composition exactly: arrangement of fruits, glassware, metal bowl on wooden table edge.
Caravaggio-influenced tenebrism, on stretched canvas with visible weave. No text, no signature, no watermark."
```

### Recipe 6：皮克斯 / 3D 渲染（Pixar 3D render，9/10）

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image photo.jpg \
  --no-negative-prompt \
  --prompt "Re-render as a Pixar-quality 3D animated film still.
Soft subsurface scattering on skin, oversized expressive eyes, rounded exaggerated forms, gentle ambient occlusion, stylized subsurface lighting, soft global illumination.
Pixar character design aesthetic, Disney/Pixar 3D animation quality, 24fps film still.
Preserve the basic pose and composition of the subject. No text, no signature."
```

## Anti-patterns

1. **"Inspired by" / "hints of" / "with a touch of"** — 模型当滤镜用，留在 photoreal 区域。**要风格迁移就用强承诺词。**
2. **不带物理介质** — `on rice paper` / `on rough canvas` / `on washi paper` 是最强的承诺触发器，缺失会让模型停留在"软化边缘"层级。
3. **不带"no photographic elements whatsoever"** — 单靠风格词不够，要显式禁止照片感。
4. **"fully re-painted" 放在 prompt 末尾** — 开头放效果强于末尾（model attention 衰减）。
5. **不写保留主体的清单** — "Preserve composition exactly: <关键元素>" 是必须的，否则主体乱飘。
6. **冷门风格无参考图** — 文字描述能力有限，冷门艺术家 / 自家插画师必须带风格 ref。
7. **双 ref 混用同源风格** — 比如梵高 + 另张梵高画作做风格 ref，会稀释主风格（Provence 风格 ref 拉走 Starry Night 调色板）。
8. **赛博朋克 / neon noir 转 photoreal 夜景照** — 风格距离不够，模型只会上滤镜。

## 负面 Prompt 何时加

> 实测 negative prompt 边际贡献极小（C3 vs C4 双 9.5，肉眼无差）。**正 prompt 强则负 prompt 可省**；正 prompt 弱则负 prompt 也救不回来。

- 已知要加 `--negative-prompt "photograph, photorealistic, 3D render, camera, lens, pixels, digital"` 的场景：仅当你担心 model drift 回 photoreal 时作为额外保险
- 加了别指望救场——把投资放在正 prompt 的承诺强度上