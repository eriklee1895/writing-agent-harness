# 摄影级真实感 (Photorealism & Portrait)

适合：肖像、产品写实、人物故事、风光大片、城市夜景、电影场景、纪实摄影、editorial 人像、social media hero image、博客 cover。

Seedream 5.0 Pro 在单主体静物摄影上是同价位模型中最强（平均 8.8/10）。物理光学（玻璃折射 / 金属反射 / 焦散 / SSS / 散景 / 蓝金光影 / 单点光衰减 / 旋转运动模糊）真实可信；残留弱点集中在手部复杂解剖、场景文字 logo。群体身份多样性、旋转运动模糊、默认美颜滤镜——这三项都可通过下方配方突破。

## 总览

| 类别 | 平均 | 典型最强 | 典型翻车 | 突破后 |
|---|---|---|---|---|
| 物理光学 | 8.8 | 玻璃焦散 9, 金属反射 9.5, 耳部 SSS 9.5, 火焰物理 9, 蓝金光影 10 | 旋转车轮运动模糊 7.5（轮子清晰，背景有 blur） | **9/10**（显式反细节 prompt）|
| 皮肤/材质 | 9.5 | 发丝 9.5, 织物编织 9, 织物垂坠 9, **raw 皮肤肌理 9.5** | 皮肤偏美颜 | **可达**（激进纹理枚举配方）|
| 群体 | 9 | 双人 9, 三人 9, 群像 distant 8, **10 人逐人枚举 9** | 5 人脸开始重复 6.5, 10 人彻底克隆 4.5 (通用 prompt) | **9/10**（逐人枚举配方）|
| 风格切换 | 9.3 | 摄影纪实 9, CGI cinematic 9.5 | — | — |
| 光影 | 9.6 | 金时刻 10, 蓝时刻 9.5, 单烛光 10 | 伦勃朗三角偶尔不到位 | — |

## 摄影真实感关键词

### 镜头/光圈（必加）

- `85mm` / `100mm macro` / `200mm telephoto` — prime lens look；不是 zoom
- `f/1.4` / `f/2.8` — 浅景深，bokeh 球
- `shot on Hasselblad` / `shot on Kodak Portra 400` / `35mm film` — 真相机签名（这类词直接把输出推向摄影域）
- `film grain` — 微纹理，让图像读为照片
- `bokeh`, `creamy bokeh`, `shallow depth of field`
- `catchlight in eye`

### 光线（必加 1-2 种）

- `golden hour`（金时刻）
- `blue hour`（蓝时刻）
- `Rembrandt lighting`（3/4 面光，三角光偶尔不全）
- `chiaroscuro`（明暗对比）
- `rim light` / `backlit`
- `volumetric lighting` / `god rays`
- `soft window light` / `natural window light`
- `studio lighting` / `beauty dish` / `softbox`

### 材质纹理（按需加）

- `visible skin pores` — anti-美颜关键词之一；单独用弱，和"人像肌理突破配方"的完整枚举组合可稳定打败默认磨皮
- `fine peach-fuzz hairs` / `vellus hairs`
- `individual hair strands`, `flyaways`
- `visible weave`, `thread detail` — 织物
- `NOT smoothed`, `no airbrushing`, `no over-smoothing` — 单独用弱；必须和"逐项纹理枚举 + 具象参考类比"组合（见"人像肌理突破配方"）才能真正打败默认美颜
- `photorealistic`, `hyperrealistic` — 基础
- `documentary photography`, `photojournalism`, `National Geographic` — 推向纪实

### 风格切换（photo vs CGI）

- 摄影：`photojournalism`, `documentary`, `film grain`, `shot on <camera>`, `natural light`, `no CGI`
- CGI cinematic：`cinematic CGI render`, `Unreal Engine 5`, `volumetric lighting`, `hyperrealistic CG`, `film still`, `concept art`, `movie still`, `octane render`

同一主体（如"宇航员在外星"），仅 style keywords 不同：

| Style keywords | 渲染结果 |
|---|---|
| `photorealistic editorial portrait, NASA documentary, Hasselblad, natural light, photojournalism, no CGI, film grain` | 火星纪实肖像，橙色调，磨损宇航服，胶片颗粒 |
| `cinematic CGI sci-fi movie still, volumetric lighting, cinematic CGI render, Unreal Engine 5, hyperrealistic CG, film still` | 紫绿青调，两个月亮，极光，水晶异星景观，体积光 |

**Seedream 5.0 Pro 仅凭 prompt 关键词即可在 photoreal 与 cinematic CGI 之间切换**，是 editorial 工作的实用能力。

> 注意：宇航员 prompt 即便写了 "helmet off" 也默认戴头盔；"fashion model" 触发 headless crop——某些 subject 类型有过度保守的安全默认。

## 群体照

Generic prompts like "10 diverse business people" hit a face-cloning cliff around 5 people and collapse at 10 (4.5/10, 7 men share one face + 3 women share one face). This is a prompt-engineering problem, not a model ceiling.

### 突破配方：逐人显式枚举（Explicit Per-Person Enumeration）

**核心：不要用"10 diverse coworkers"这种整体描述，给每一个人单独写一行——种族/年龄/发型/服装全部显式指定。** 5 人、7 人、10 人三个尺度都能拿到 9/10，零脸克隆：

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

| 人数 | Prompt 策略 | 身份多样性 | 评分 |
|---|---|---|---|
| 5 人 | 逐人枚举（种族+年龄+发型+服装）| 5 张完全不同脸 | **9/10** |
| 7 人 | 逐人枚举 | 7 张完全不同脸，年龄段分布正确 | **9/10** |
| 10 人（2 排：5 站 5 坐）| 逐人枚举 | 10 张完全不同脸，24-60 岁跨度正确 | **9/10** |
| 10 人（泛化 prompt）| "10 diverse business people (mixed ages/ethnicities)" | 7 男 1 脸 + 3 女 1 脸 | 4.5/10 |

**关键规则**：
1. **每人一行，四元组齐全**：种族 + 年龄 + 发型细节 + 服装颜色/款式，缺一不可
2. **年龄要给具体数字并跨度大**（24-60 而不是"mixed ages"）——具体数字比"diverse"更能防止收敛
3. **发型要给具体细节**（"box braids"/"short fade"/"grey-streaked bob"）而不是"different hairstyles"
4. **10 人以上排布用两排（站/坐）分层**——避免所有人脸在同一水平线上挤压变形
5. **手部策略延续**：手放两侧自然下垂、坐姿手放腿上，避免复杂手势——这条仍然有效，10 人测试里没有一处手部畸形

**核心杠杆是逐人枚举，不是 negative prompt**。保留的 negative prompt（extra hands, fused fingers 等）是辅助防御。

### 群体照策略

- **≤10 人，用逐人枚举 recipe**：production-ready，9/10 稳定
- **10 人以上（12-20人）**：未测试，枚举 prompt 会变长（token 限制 ≤300 字中文/600 词英文），需精简到"种族+年龄+1个视觉锚点"三元组
- **20+ 大群像**：远景通用脸即可，不需要逐人枚举
- **动作/围餐场景**：手部遮挡策略依然适用，可与逐人枚举组合使用

### 群体照 negative prompt 叠加

```
多只手, 手放口袋里的模糊变形, 手指融合, 拿筷子的手畸形
```

### 群体照 diversity 语言小心

> `10 diverse business people (5 men 5 women, mixed ages/ethnicities)` 触发 `OutputImageSensitiveContentDetected`。**"ethnicities" 词会触发安全检查**，改成 `ten coworkers, mixed men and women of various ages` 通过。**逐人枚举版本的 prompt（写具体种族如 "Black man" / "South Asian woman"）未触发安全检查**——触发点是抽象词 "ethnicities" 本身，不是具体种族描述。

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

### "物理光影全真模拟" — 约 90% 真（旋转模糊可实现）

- 真模拟：玻璃折射、焦散、镜面反射、SSS、散景、大气散射、彩色光混合、金/蓝时刻、烛光衰减、火焰色温、水焦散、单点光衰减、**车轮旋转模糊（用突破配方）**
- 近似/失败：曲面透明物体折射量略小、烟状态（闷 vs 燃烧混淆）

**静态单主体 + 产品/棚拍/肖像领域，物理光学表现为同价位最佳。**

#### 旋转运动模糊配方

Bare "motion blur on wheels" 渲染清晰车轮 + 背景 blur（7.5/10）。问题在于 prompt 没有显式禁止车轮细节，模型默认保留清晰车轮加背景 blur 纹理。**显式反细节语言 + "flying-saucer disc" 类比**即可触发真实旋转模糊：

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

Bare "motion blur" is too weak — the model defaults to adding background texture blur without touching the wheels. Explicitly forbid wheel detail and concretely describe the "disc" target to trigger real rotational-motion blur rendering.

### "人像肌理天花板" — 突破配方实现 raw dermatology 级皮肤

Default beauty-filter smoothing is a prompt gap, not a hard ceiling. Even `NOT smoothed` alone lands at ~80% polished-editorial skin; young East-Asian women are the hardest case for raw skin. The aggressive recipe below produces 9.5/10 raw dermatology-grade skin for both young women and young men: visible enlarged pores, nose/cheek sebaceous filaments, natural redness, acne marks and freckles, vellus hairs, T-zone oil sheen, no wax-figure look.

#### 突破配方：激进纹理枚举 + 具象参考类比 + 堆叠否定

**核心：`NOT smoothed` 单独太弱。三个杠杆缺一不可**——(1) 逐项枚举要出现的纹理，(2) 给一个具象的"生图目标"参考类比，(3) 堆叠否定 beauty 词。实测年轻男女都 9.5/10、可复现（非幸运种子）：

```
Raw unretouched documentary close-up portrait of a [年龄+人物], [自然光], no makeup.
CRITICAL SKIN REALISM: clearly visible enlarged pores across the nose and cheeks,
individual vellus peach-fuzz hairs [男性加 short stubble hairs] catching the light,
natural skin unevenness with slight redness around the nose and chin, a few tiny
visible blemishes and freckles, faint fine lines under the eyes, subtle oil sheen
on the T-zone, real skin micro-texture like a dermatology reference photograph.
Shot on 100mm macro lens f/5.6, sharp focus on skin.
This is a RAW UNRETOUCHED photo — absolutely NO beauty retouching, NO skin smoothing,
NO airbrushing, NO frequency-separation, NO beauty-campaign gloss, NO wax-figure skin.
Documentary realism like a National Geographic face portrait, not a cosmetics ad. 2K
```

**为什么有效**（与旋转模糊/群体照同一套方法论）：
1. **逐项枚举纹理**（enlarged pores / vellus hairs / redness / blemishes / freckles / fine lines / oil sheen）——不是笼统 "NOT smoothed"，而是把每一种要出现的皮肤特征点名
2. **具象参考类比**（"dermatology reference photograph" / "National Geographic face portrait, not a cosmetics ad"）——给模型一个明确的"生成目标图种"锚点，把它从默认的 beauty-campaign register 拉走
3. **堆叠否定**（NO beauty retouching / NO smoothing / NO airbrushing / NO frequency-separation / NO gloss / NO wax-figure）——一连串否定压制默认磨皮

**弱项残留**：深肤色、烈日下皮肤 less tested；dermatology macro 极端特写未测。但常规肖像的"美颜默认"已经可以稳定打败。

Raw 皮肤通过配方可稳定获得，发丝渲染 category-leading，常规肖像质量高。

## 翻车区

1. **群体身份多样性 ≥5 人** — 通用 prompt 触发脸克隆，逐人枚举配方可做到 10 人 9/10。**残留限制**：12+ 人未测，逐人枚举 prompt 长度可能撞 token 上限
2. **手部复杂解剖** — 筷子/伸/多物体互动（逐人枚举也没解决这个）
3. **场景文字/Logo** — 短招牌的英/日/韩文字仍产 gibberish Latin；长段中文段落好；散落小 logo 仍假
4. **旋转/动态模糊** — 弱 prompt（"motion blur on wheels"）仍会失败，需用完整配方
5. **安全过激** — diversity/ethnicities 抽象词触发安全；**具体种族描述（"Black man"/"South Asian woman"）不触发**
6. **美颜默认** — 弱 prompt（单写 `NOT smoothed`）仍失败，需用激进纹理枚举完整配方；年轻男女均可拿到 9.5/10 raw 皮肤
7. **保守 subject 默认** — 宇航员头盔不脱 / fashion model headless crop
8. **暗肤色/烈日皮肤** less tested 但偏弱

## Recipes

### Recipe 1：金时刻人像

```
Portrait of [SUBJECT], [LOCATION], golden hour, backlit with warm rim light on hair, f/1.4 85mm lens, extremely shallow depth of field, [FOREGROUND ELEMENT] soft bokeh circles, background creamy bokeh, individual hair strands and flyaways visible, catchlight in eyes, visible skin texture, photorealistic, shot on Kodak Portra 400, film grain, 2K
```

### Recipe 2：棚拍产品焦散

```
Studio product photo of a [OBJECT] on [SURFACE], strong backlight creating caustic light patterns, refraction distorting surface pattern visible through glass/transparent material, spectral rainbow dispersion at edges, photorealistic, 85mm macro, softbox reflected in surface, no text no logo, sharp focus, 2K
```

### Recipe 3：金属反射

```
Polished [chrome/silver/stainless MATERIAL] [OBJECT] on [black velvet / dark marble], studio environment reflected in mirror surface, gradient reflection showing softbox lights, spherical/geometric distortion accurate, photorealistic product photography, sharp focus, no fake people or text in reflection, 2K
```

### Recipe 4：特写皮肤/耳部 SSS

```
Extreme close-up of [SUBJECT'S FEATURE], lit from behind by warm sunlight, showing subsurface scattering through skin/ear, translucent glow, visible skin pores, fine vellus hairs rim-lit, catchlight in eye if eye present, realistic skin texture NOT smoothed, shallow DOF, 100mm macro, photorealistic, film grain, no airbrushing, 2K
```

### Recipe 5：雨天夜景

```
Night photo of [LOCATION] in heavy rain, wet asphalt with clear stretched neon reflections, raindrops visible as streaks, [SUBJECTS with umbrellas], cinematic rain photography, shallow focus, bokeh lights, no readable signs no logos, photorealistic, 2K
```

### Recipe 6：烛光人像

```
Portrait of [SUBJECT] [ACTIVITY] by candlelight only, warm firelight on face from camera-right, deep shadows, chiaroscuro lighting, Rembrandt-style portrait, visible skin texture and age details, photorealistic, single light source, fast falloff to black, 85mm f/1.4, 2K
```

### Recipe 7：蓝时刻城市

```
Blue hour cityscape of [CITY RIVERFRONT], [BRIDGE/TOWER] in distance, bridge lights reflecting in water as stretched vertical reflections, deep blue sky transitioning to night, long exposure car light trails on road, city lights warm against cool sky, professional cityscape photography, tripod mounted, 2K
```

### Recipe 8：金时刻风光

```
Golden hour landscape photo of [LOCATION, e.g., Tuscany hills with cypress trees], warm low-angle sun from [DIRECTION], long raking shadows across [FIELDS/HILLS], rolling foreground, atmospheric haze on distant mountains, warm orange light on land and clouds, professional landscape photography, National Geographic, shot on Phase One, f/11, deep focus, 2K
```

### Recipe 9：冷暖双色温室内

```
Indoor portrait of [SUBJECT] in [ROOM], lit by cool blue window light from camera-left and warm tungsten lamp light from camera-right, color contrast between cool and warm on face, Rembrandt triangle on cheek, deep shadows, photorealistic, f/1.8 85mm, natural interior, 2K
```

### Recipe 10：织物垂坠

```
Fashion editorial photo of [MODEL DESCRIPTION] wearing a flowing [SILK/CHIFFON/SATIN COLOR] dress, fabric draped in elegant folds, wind catching the hem, showing fabric weight and movement with tension lines along folds, soft studio lighting with rim light, photorealistic fashion photography, full body visible, face included, 2K
```

> Fashion-model prompts trigger a headless crop unless you explicitly add `face visible, full body framed from head to floor`.

### Recipe 11：高速定格美食摄影（腾空/飞溅食材）

适合寿司米粒/鱼籽腾空、咖啡/牛奶/水花飞溅、调料粉末悬浮、食材抛起中瞬间定格的商业美食广告类画面。关键是**显式描述"悬浮/定格/高速快门"和具体悬浮物体**，以及"哪些东西在静止台面上"——对比锚定（台面静 + 半空动）比只写 "high-speed photography" 有效：

```
高端商业美食广告摄影，[黑色石板/深色实木餐桌/哑光陶瓷盘]上放置[一枚三文鱼寿司/一只甜点/一份主菜]，
[米粒/橘色鱼籽/海苔碎/可可粉/柠檬皮屑/白葡萄酒液]从上方自然洒落被高速快门定格，
几粒[米粒和鱼籽]悬浮在半空中清晰可见（不模糊、有个体形状、有高光反射），
其他[寿司本体/盘子/桌面]静止锐利对焦，
顶部柔光箱单灯、暗调背景、食物有真实湿润质感和细腻反光，
f/5.6 100mm macro、高速快门凝固运动、无景深模糊、商业广告摄影质感、2K
```

关键杠杆：
1. **显式列举悬浮物体**（"米粒、橘色鱼籽悬浮在半空中清晰可见"），不能只写 "frozen motion"——模型需要知道具体是什么在飞。
2. **对比锚定**：桌面/主食物体静止锐利 + 半空物体也清晰（high-speed 定格、不是 motion blur），两者都要写。
3. **光源方向 + 材质质感**照常写——腾空食材的高光反射是"广告感"的关键。
4. 暗调背景比亮调更容易突出悬浮食材（亮背景会让浅色米粒/粉末融掉）。
5. 实测：单种食材腾空（鱼籽/米粒）9/10；多种同时腾空（粉末 + 液体 + 固体）容易糊成一团，建议一次只飞一种。