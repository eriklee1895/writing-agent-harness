# 摄影级真实感 (Photorealism & Portrait)

适合：肖像、产品写实、人物故事、风光大片、城市夜景、电影场景、纪实摄影、editorial 人像、social media hero image、博客 cover。

Seedream 5.0 Pro 在单主体静物摄影上是同价位模型中最强（实测 8.8/10 平均）。物理光学（玻璃折射 / 金属反射 / 焦散 / SSS / 散景 / 蓝金光影 / 单点光衰减）真实可信；弱点集中在动态模糊、群体身份多样性、手部复杂解剖、场景文字 logo、默认美颜滤镜。

## 总览（24 张实测图，按类别）

| 类别 | 平均 | 典型最强 | 典型翻车 |
|---|---|---|---|
| 物理光学 (8 张) | 8.8 | 玻璃焦散 9, 金属反射 9.5, 耳部 SSS 9.5, 火焰物理 9, 蓝金光影 10 | 旋转车轮运动模糊 7.5（轮子清晰，背景有 blur） |
| 皮肤/材质 (4 张) | 9.1 | 发丝 9.5, 织物编织 9, 织物垂坠 9 | 皮肤仍偏美颜 8.5 |
| 群体 (6 张) | 7.6 | 双人 9, 三人 9, 群像 distant 8 | 5 人脸开始重复 6.5, 10 人彻底克隆 4.5 |
| 风格切换 (2 张) | 9.3 | 摄影纪实 9, CGI cinematic 9.5 | — |
| 光影 (4 张) | 9.6 | 金时刻 10, 蓝时刻 9.5, 单烛光 10 | 伦勃朗三角偶尔不到位 |

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

## 群体照（重大限制）

群体照随人数急剧退化。**核心阈值：5 人是 cliff。**

| 人数 | 身份多样性 | 手部 | 身体融合 | 可用？ |
|---|---|---|---|---|
| 2 人 | 2 张不同脸，自然表情 | 全对 | 无 | ✅ 真 candid |
| 3 人 | 3 张不同脸（含孩子） | 对 | 无 | ✅ 家庭照 |
| 4 人（含道具/蒸汽遮挡） | 4 张不同脸（差异发型/眼镜/表情） | 筷子轻度融合，蒸汽遮多数 | 无 | ✅ social-media 分辨率可通过 |
| 5 人 | **脸开始重复**——3 个女性共享脸型 | 中间女性多 1 指；手臂边缘融合 | 轻度 | ⚠️ 氛围 OK，close-up 不行 |
| 10 人 | **大克隆**——7 个男性 1 张脸，3 个女性 1 张脸 | 模型把手藏口袋/身后；可见手模糊 | 后排头还行但西装重复 | ❌ uncanny |
| 30+ 群像 | 前景 5-6 张不同；中景/远景通用 | 摊档可见手，轻微 | 无 | ✅ 真新闻摄影感（远景小脸不需要多样性） |

**反直觉发现：大群像（30+）比 5-10 人合影好**，因为远景小脸"通用亚洲脸"反而读为自然差异。**4 人围桌带蒸汽/食材遮挡手部**也比 5 人干净合影好。

### 群体照策略

- **≤4 人**：production-ready，姿势可控，手基本对
- **5 人**：脸开始克隆，至少 1-2 处手错误
- **10 人正面合影**：不可用，需要后期换脸
- **20+ 群像**：可用，远景通用脸是正确输出
- **动作/围餐（4 人带蒸汽/餐具）**：比静止合影更好，因为蒸汽/餐具/手部忙碌遮挡问题

### 群体照 negative prompt 叠加

```
多只手, 手放口袋里的模糊变形, 手指融合, 拿筷子的手畸形
```

### 群体照 diversity 语言小心

> 实测 `10 diverse business people (5 men 5 women, mixed ages/ethnicities)` 触发 `OutputImageSensitiveContentDetected`。**"ethnicities" 词会触发安全检查**，改成 `ten coworkers, mixed men and women of various ages` 通过。

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

### "物理光影全真模拟" — 约 85% 真

- 真模拟：玻璃折射、焦散、镜面反射、SSS、散景、大气散射、彩色光混合、金/蓝时刻、烛光衰减、火焰色温、水焦散、单点光衰减
- 近似/失败：旋转运动模糊（R3 车轮清晰是真 miss）、曲面透明物体折射量略小、烟状态（闷 vs 燃烧混淆）、动态模糊（模型加"blur"纹理而非模拟物体运动）

**静态单主体 + 产品/棚拍/肖像领域，光的物理是真同价位最佳。**

### "人像肌理天花板" — 东亚柔光女性约 80% 真

- 真天花板：年轻东亚女性 + 柔金光 + SSS + 毛孔（muted 但有）+ 绒毛 + 头发 rim light + 眼睛 catchlight
- 默认美颜：即便写 `NOT smoothed` 也偏 polished editorial，需要 80% 努力才能拿到 raw 皮肤
- 发丝（P2）真的 category-leading，超过 Midjourney v6 / DALL-E 3
- 老龄皮肤（L4）皱纹/老年斑/白发/血管纹理都好
- 弱项：深肤色、强纹理皮肤、烈日下皮肤、dermatology macro

**"天花板"是营销话术，"当前最强之一，尤其东亚柔光"是真。**

## 翻车区（诚实清单）

1. **群体身份多样性 ≥5 人断裂** — marketing demo 多是单人/双人，10 人测试是真失败
2. **手部复杂解剖** — 筷子/伸/多物体互动
3. **场景文字/Logo** — 短招牌的英/日/韩文字仍产 gibberish Latin；长段中文段落好；散落小 logo 仍假
4. **旋转/动态模糊** — R3 是最清晰的 single fail
5. **安全过激** — diversity/ethnicities 词触发安全
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