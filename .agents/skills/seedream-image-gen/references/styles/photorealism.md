# 摄影级真实感 (Photorealism & Portrait)

适合：肖像、产品写实、人物故事、风光大片、城市夜景、电影场景、纪实摄影、editorial 人像、social media hero image、博客 cover。

Seedream 5.0 Pro 在单主体静物摄影上是同价位模型中最强（实测 8.8/10 平均）。物理光学（玻璃折射 / 金属反射 / 焦散 / SSS / 散景 / 蓝金光影 / 单点光衰减 / 旋转运动模糊-需突破配方）真实可信；残留弱点集中在手部复杂解剖、场景文字 logo、默认美颜滤镜。**群体身份多样性、旋转运动模糊两项原以为是模型能力天花板，2026-07-10 复测证实是 prompt 工程问题，均有突破配方（见下文）。**

## 总览（24 张初测 + 补测，按类别）

| 类别 | 平均 | 典型最强 | 典型翻车（初测）| 突破后 |
|---|---|---|---|---|
| 物理光学 (8 张) | 8.8 | 玻璃焦散 9, 金属反射 9.5, 耳部 SSS 9.5, 火焰物理 9, 蓝金光影 10 | 旋转车轮运动模糊 7.5（轮子清晰，背景有 blur） | **9/10**（显式反细节 prompt，见下文突破配方）|
| 皮肤/材质 (4 张) | 9.1 | 发丝 9.5, 织物编织 9, 织物垂坠 9 | 皮肤仍偏美颜 8.5 | 未突破，仍需接受 ~80% |
| 群体 (6 张 + 补测 3 张) | 7.6→9 | 双人 9, 三人 9, 群像 distant 8, **10人逐人枚举 9** | 5 人脸开始重复 6.5, 10 人彻底克隆 4.5 | **9/10**（逐人枚举配方，见下文）|
| 风格切换 (2 张) | 9.3 | 摄影纪实 9, CGI cinematic 9.5 | — | — |
| 光影 (4 张) | 9.6 | 金时刻 10, 蓝时刻 9.5, 单烛光 10 | 伦勃朗三角偶尔不到位 | — |

## 摄影真实感关键词（实测稳定）

### 镜头/光圈（必加）

- `85mm` / `100mm macro` / `200mm telephoto` — prime lens look；不是 zoom
- `f/1.4` / `f/2.8` — 浅景深，bokeh 球
- `shot on Hasselblad` / `shot on Kodak Portra 400` / `35mm film` — 真相机签名（D1 实测这种词直接迁移到 photoreal 域）
- `film grain` — 微纹理，让图像读为照片
- `bokeh`, `creamy bokeh`, `shallow depth of field`
- `catchlight in eye`

### 光线（必加 1-2 种）

- `golden hour`（金时刻）— L1 满分
- `blue hour`（蓝时刻）— L2 9.5
- `Rembrandt lighting`（3/4 面光，部分到位，三角光偶尔不全）
- `chiaroscuro`（明暗对比）— L4 满分，单点光源戏剧化
- `rim light` / `backlit` — P2, R5 边缘光极佳
- `volumetric lighting` / `god rays` — D2 cinematic 用
- `soft window light` / `natural window light`
- `studio lighting` / `beauty dish` / `softbox`

### 材质纹理（按需加）

- `visible skin pores` — P1 帮 anti-美颜，但不会完全打败默认
- `fine peach-fuzz hairs` / `vellus hairs` — R5, P1 边缘绒毛
- `individual hair strands`, `flyaways` — P2 关键
- `visible weave`, `thread detail` — P3 织物
- `NOT smoothed`, `no airbrushing`, `no over-smoothing` — 弱有效，不能单独依赖
- `photorealistic`, `hyperrealistic` — 基础
- `documentary photography`, `photojournalism`, `National Geographic` — D1, L1, G5 推向纪实

### 风格切换（photo vs CGI）

- 摄影：`photojournalism`, `documentary`, `film grain`, `shot on <camera>`, `natural light`, `no CGI`
- CGI cinematic：`cinematic CGI render`, `Unreal Engine 5`, `volumetric lighting`, `hyperrealistic CG`, `film still`, `concept art`, `movie still`, `octane render`

实测同一 prompt（"宇航员在外星"），仅 style keywords 不同：

| Style keywords | 渲染结果 |
|---|---|
| `photorealistic editorial portrait, NASA documentary, Hasselblad, natural light, photojournalism, no CGI, film grain` | 火星纪实肖像，橙色调，磨损宇航服，胶片颗粒 |
| `cinematic CGI sci-fi movie still, volumetric lighting, cinematic CGI render, Unreal Engine 5, hyperrealistic CG, film still` | 紫绿青调，两个月亮，极光，水晶异星景观，体积光 |

**Seedream 5.0 Pro 仅凭 prompt 关键词即可在 photoreal 与 cinematic CGI 之间切换**，是 editorial 工作的实用能力。

> 注意：宇航员 prompt 即便写了 "helmet off" 也默认戴头盔；"fashion model" 触发 headless crop——某些 subject 类型有过度保守的安全默认。

## 群体照（2026-07-10 更新：10 人断裂已被突破）

**早期结论已被修正。** 最初 sweep（用通用 prompt "10 diverse business people"）发现 5 人是身份多样性 cliff，10 人大合照彻底崩（4.5/10，7 男 1 张脸 + 3 女 1 张脸）。**但这是 prompt 工程问题，不是模型能力天花板。**

### 突破配方：逐人显式枚举（Explicit Per-Person Enumeration）

**核心改动：不要用"10 diverse coworkers"这种整体描述，给每一个人单独写一行——种族/年龄/发型/服装全部显式指定。** 实测在 5 人、7 人、10 人三个尺度上都拿到 9/10，零脸克隆：

```
Editorial team photograph of exactly TEN coworkers arranged in two rows
(5 standing back row, 5 seated front row), half-body framing, bright office atrium.
Each person is a completely different person with completely distinct facial features,
listed left to right, back row first then front row:

Back row:
Person 1: East Asian woman, age 45, short grey-streaked bob, wearing navy blazer
Person 2: Black man, age 38, shaved head, thick-framed glasses, wearing charcoal turtleneck
Person 3: White woman, age 29, long blonde wavy hair, wearing mustard cardigan
Person 4: Middle Eastern man, age 50, salt-and-pepper beard, wearing brown suit vest
Person 5: Southeast Asian woman, age 34, long straight black hair with side part, wearing emerald blouse

Front row (seated):
Person 6: Latino man, age 26, short curly dark hair, wearing light blue denim jacket
Person 7: South Asian woman, age 31, long black hair in ponytail, wearing burgundy kurta
Person 8: White man, age 60, bald with grey beard, wearing forest green sweater vest
Person 9: Black woman, age 24, box braids, wearing coral top
Person 10: East Asian man, age 42, short black hair with glasses, wearing grey suit jacket

All TEN faces must be visibly distinct — different nose shapes, different eye shapes,
different skin tones, different hair textures, different ages ranging 24-60. They smile
naturally at camera. Sharp focus on all 10 faces, soft bokeh background, 50mm lens,
photorealistic corporate editorial photography, 2K, 16:9
```

**为什么有效**：模型的 face-cloning 问题根源是"生成式随机采样在没有约束时会收敛到少数几个 face template"。**逐人给出具体锚点（种族+年龄+发型+服装四元组）**相当于给每个人一个独立的采样种子提示，阻止收敛。整体式描述（"10 diverse people"）没有个体锚点，模型自由采样时就会重复。

**实测数据（本次 sweep）**：

| 人数 | Prompt 策略 | 身份多样性 | 评分 |
|---|---|---|---|
| 5 人 | 逐人枚举（种族+年龄+发型+服装）| 5 张完全不同脸 | **9/10** |
| 7 人 | 逐人枚举 | 7 张完全不同脸，年龄段分布正确 | **9/10** |
| 10 人（2 排：5 站 5 坐）| 逐人枚举 | 10 张完全不同脸，24-60 岁跨度正确 | **9/10** |
| 10 人（原始 sweep，泛化 prompt）| "10 diverse business people (mixed ages/ethnicities)" | 7 男 1 脸 + 3 女 1 脸 | 4.5/10（旧结论）|

**关键规则**：
1. **每人一行，四元组齐全**：种族 + 年龄 + 发型细节 + 服装颜色/款式，缺一不可
2. **年龄要给具体数字并跨度大**（24-60 而不是"mixed ages"）——具体数字比"diverse"更能防止收敛
3. **发型要给具体细节**（"box braids"/"short fade"/"grey-streaked bob"）而不是"different hairstyles"
4. **10 人以上排布用两排（站/坐）分层**——避免所有人脸在同一水平线上挤压变形
5. **手部策略延续**：手放两侧自然下垂、坐姿手放腿上，避免复杂手势——这条仍然有效，10 人测试里没有一处手部畸形

**旧版 negative prompt 仍建议保留**（extra hands, fused fingers 等），但**核心杠杆是逐人枚举，不是 negative prompt**。

### 群体照策略（更新）

- **≤10 人，用逐人枚举 recipe**：production-ready，9/10 稳定，参考上面模板
- **10 人以上（12-20人）**：未测试，理论上枚举 prompt 会变得很长（token 限制 ≤300 字中文/600 词英文），需要精简描述（缩短到"种族+年龄+1个视觉锚点"三元组）
- **20+ 大群像**：仍推荐原策略（远景通用脸），不需要逐人枚举——远景小脸不需要个体区分
- **动作/围餐场景**：手部遮挡策略依然适用，可与逐人枚举组合使用效果更佳

### 群体照 negative prompt 叠加

```
多只手, 手放口袋里的模糊变形, 手指融合, 拿筷子的手畸形
```

### 群体照 diversity 语言小心

> 实测 `10 diverse business people (5 men 5 women, mixed ages/ethnicities)` 触发 `OutputImageSensitiveContentDetected`。**"ethnicities" 词会触发安全检查**，改成 `ten coworkers, mixed men and women of various ages` 通过。**逐人枚举版本的 prompt（写具体种族如 "Black man" / "South Asian woman"）实测未触发安全检查**——推断触发点是"ethnicities"这个抽象词汇本身，不是具体种族描述。

## Realism 推荐的 Negative Prompt（替换默认）

针对 portrait / product / photo 工作：

```
模糊, 低质量, 水印, 变形, 多余肢体, 六指, 融合手指, 塑料皮肤, 过度磨皮, 美颜滤镜,
蜡像感, AI绘画感, 橡胶皮肤, 头发结块, 假文字, 伪日文, 伪韩文, 乱码, logo, 品牌名,
死鱼眼, 不对称眼睛, 畸变牙齿, 过饱和, 卡通, 动漫, 插画, 3D渲染, C4D质感
```

英文版：
```
blurry, low quality, watermark, deformed, extra limbs, six fingers, fused fingers, plastic skin, over-smoothed, beauty filter, wax figure, AI painting, rubber skin, clumped hair, fake text, pseudo-Japanese, pseudo-Korean, garbled text, logo, brand names, dead fish eyes, asymmetric eyes, distorted teeth, oversaturated, cartoon, anime, illustration, 3D render, C4D aesthetic
```

CGI cinematic 工作去掉 anti-3D 词（`3D渲染, C4D质感`），加 `photograph, film grain, documentary` 到负 prompt。

群体照（≥4 人）额外加：`extra hands, blobby hands-in-pockets, fused fingers, deformed chopstick grip`。

## Marketing Claim 诚实对照

### "物理光影全真模拟" — 约 90% 真（2026-07-10 更新：旋转模糊已被突破）

- 真模拟：玻璃折射、焦散、镜面反射、SSS、散景、大气散射、彩色光混合、金/蓝时刻、烛光衰减、火焰色温、水焦散、单点光衰减、**车轮旋转模糊（用突破配方后）**
- 近似/失败：曲面透明物体折射量略小、烟状态（闷 vs 燃烧混淆）

**静态单主体 + 产品/棚拍/肖像领域，光的物理是真同价位最佳。**

#### 旋转运动模糊突破配方（原 R3 miss 已修复）

最初测试（"motion blur on wheels"）车轮渲染清晰，只有背景/路面模糊，7.5/10。**问题是 prompt 没有显式禁止车轮细节**，模型默认保留清晰车轮 + 加背景 blur 纹理。**修复：显式反细节语言 + "flying-saucer disc" 类比**：

```
❌ 弱（7.5/10，车轮仍清晰）：
"panning shot, motion blur on wheels, background streaked"

✅ 强（9/10，车轮变真实旋转模糊盘）：
"CRITICAL PHYSICS REQUIREMENT: The WHEELS must be rendered as solid circular
discs of rotational motion blur — NO individual spokes, NO rim detail, NO tire
tread visible, the entire wheel is a uniform grey/silver radial blur disc.
The car body silhouette is sharp but the WHEELS specifically are NOT sharp,
they appear as two grey flying-saucer discs at the contact patches.
Background streaked horizontally with motion blur. Road surface streaked.
ONLY the car body and driver helmet are in sharp focus; WHEELS and BACKGROUND
and ROAD are motion-blurred. Reference: real F1 panning photos by Darren Heath
or Porsche AG press shots."
```

**关键杠杆**：
1. **显式否定车轮细节**（"NO individual spokes, NO rim detail, NO tire tread"）——不写这条模型默认保留清晰车轮
2. **"uniform grey/silver radial blur disc" / "flying-saucer discs" 具象类比**——给模型一个清晰的视觉目标而不是抽象的"blur"
3. **显式列出哪些部分保持清晰**（车身+头盔）vs 哪些部分必须模糊（车轮+背景+路面）——对比锚定比单纯说"motion blur"有效
4. **Reference 真实摄影师名字**（"Darren Heath" F1 摄影、"Porsche AG press shots"）——锚定到已知视觉语言

**结论：R3 miss 不是模型能力天花板，是 prompt 工程问题。** "motion blur" 这个词本身太弱，模型会默认加背景纹理而不动车轮；需要显式禁止车轮细节 + 具象化"disc"目标才能触发真正的旋转模糊渲染。

### "人像肌理天花板" — 东亚柔光女性约 80% 真

- 真天花板：年轻东亚女性 + 柔金光 + SSS + 毛孔（muted 但有）+ 绒毛 + 头发 rim light + 眼睛 catchlight
- 默认美颜：即便写 `NOT smoothed` 也偏 polished editorial，需要 80% 努力才能拿到 raw 皮肤
- 发丝（P2）真的 category-leading，超过 Midjourney v6 / DALL-E 3
- 老龄皮肤（L4）皱纹/老年斑/白发/血管纹理都好
- 弱项：深肤色、强纹理皮肤、烈日下皮肤、dermatology macro

**"天花板"是营销话术，"当前最强之一，尤其东亚柔光"是真。**

## 翻车区（诚实清单，2026-07-10 更新）

1. ~~群体身份多样性 ≥5 人断裂~~ — **已被逐人枚举配方突破**，10 人测试 9/10（见上文"群体照"章节）。**残留限制**：未测试 12+ 人，逐人枚举 prompt 长度可能撞 token 上限
2. **手部复杂解剖** — 筷子/伸/多物体互动（这条仍然真实存在，逐人枚举也没解决这个）
3. **场景文字/Logo** — 短招牌的英/日/韩文字仍产 gibberish Latin；长段中文段落好；散落小 logo 仍假
4. ~~旋转/动态模糊~~ — **已被显式反细节 prompt 突破**（见上文"旋转运动模糊突破配方"）。弱形式 prompt（"motion blur on wheels"）仍会失败，需要用突破配方
5. **安全过激** — diversity/ethnicities 抽象词触发安全；**具体种族描述（"Black man"/"South Asian woman"）实测未触发**
6. **美颜默认难以关闭** — 强 anti-smoothing prompt 也只能拿到 ~80%
7. **保守 subject 默认** — 宇航员头盔不脱 / fashion model headless crop
8. **暗肤色/烈日皮肤** less tested but 弱

## Recipes

### Recipe 1：金时刻人像（portrait, R4/P2 style）

```
Portrait of [SUBJECT], [LOCATION], golden hour, backlit with warm rim light on hair, f/1.4 85mm lens, extremely shallow depth of field, [FOREGROUND ELEMENT] soft bokeh circles, background creamy bokeh, individual hair strands and flyaways visible, catchlight in eyes, visible skin texture, photorealistic, shot on Kodak Portra 400, film grain, 2K
```

### Recipe 2：棚拍产品焦散（R1 style）

```
Studio product photo of a [OBJECT] on [SURFACE], strong backlight creating caustic light patterns, refraction distorting surface pattern visible through glass/transparent material, spectral rainbow dispersion at edges, photorealistic, 85mm macro, softbox reflected in surface, no text no logo, sharp focus, 2K
```

### Recipe 3：金属反射/R2 style

```
Polished [chrome/silver/stainless MATERIAL] [OBJECT] on [black velvet / dark marble], studio environment reflected in mirror surface, gradient reflection showing softbox lights, spherical/geometric distortion accurate, photorealistic product photography, sharp focus, no fake people or text in reflection, 2K
```

### Recipe 4：特写皮肤/R5, P1 style

```
Extreme close-up of [SUBJECT'S FEATURE], lit from behind by warm sunlight, showing subsurface scattering through skin/ear, translucent glow, visible skin pores, fine vellus hairs rim-lit, catchlight in eye if eye present, realistic skin texture NOT smoothed, shallow DOF, 100mm macro, photorealistic, film grain, no airbrushing, 2K
```

### Recipe 5：雨天夜景/R7 style

```
Night photo of [LOCATION] in heavy rain, wet asphalt with clear stretched neon reflections, raindrops visible as streaks, [SUBJECTS with umbrellas], cinematic rain photography, shallow focus, bokeh lights, no readable signs no logos, photorealistic, 2K
```

### Recipe 6：烛光人像/L4 style

```
Portrait of [SUBJECT] [ACTIVITY] by candlelight only, warm firelight on face from camera-right, deep shadows, chiaroscuro lighting, Rembrandt-style portrait, visible skin texture and age details, photorealistic, single light source, fast falloff to black, 85mm f/1.4, 2K
```

### Recipe 7：蓝时刻城市/L2 style

```
Blue hour cityscape of [CITY RIVERFRONT], [BRIDGE/TOWER] in distance, bridge lights reflecting in water as stretched vertical reflections, deep blue sky transitioning to night, long exposure car light trails on road, city lights warm against cool sky, professional cityscape photography, tripod mounted, 2K
```

### Recipe 8：金时刻风光/L1 style

```
Golden hour landscape photo of [LOCATION, e.g., Tuscany hills with cypress trees], warm low-angle sun from [DIRECTION], long raking shadows across [FIELDS/HILLS], rolling foreground, atmospheric haze on distant mountains, warm orange light on land and clouds, professional landscape photography, National Geographic, shot on Phase One, f/11, deep focus, 2K
```

### Recipe 9：冷暖双色温室内/L3 style

```
Indoor portrait of [SUBJECT] in [ROOM], lit by cool blue window light from camera-left and warm tungsten lamp light from camera-right, color contrast between cool and warm on face, Rembrandt triangle on cheek, deep shadows, photorealistic, f/1.8 85mm, natural interior, 2K
```

### Recipe 10：织物垂坠/P4 style

```
Fashion editorial photo of [MODEL DESCRIPTION] wearing a flowing [SILK/CHIFFON/SATIN COLOR] dress, fabric draped in elegant folds, wind catching the hem, showing fabric weight and movement with tension lines along folds, soft studio lighting with rim light, photorealistic fashion photography, full body visible, face included, 2K
```

> P4-style 实测 prompt 即便写 fashion model 也被 headless crop，必须显式 `face visible, full body framed from head to floor` 才能保留脸。