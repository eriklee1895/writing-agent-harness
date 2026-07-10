# 3D 图标 / 等距微缩 / 毛玻璃 / 粘土风 (3D Icon & Stylized Illustration)

适合：App icon、SaaS landing page 插画、产品空状态图、空数据页、PPT 元素、社媒配图插画、Dribbble 风格 3D 元素、emoji/sticker 包、盲盒潮玩手办风 IP、等距 diorama 微缩场景、毛玻璃/全息/液态金属风格 logo、立体文字特效。

Seedream 5.0 Pro 在 3D 渲染风插画上表现非常强，特别是以下子风格：
- **Frosted / glassmorphism**（毛玻璃半透明图标）：App icon、SaaS 产品插画、iOS/macOS 风格 UI 元素
- **Claymorphism / Pop-Mart blind-box**（粘土潮玩盲盒风）：圆润 Q 版手办、IP 形象、3D 角色、emoji
- **Isometric miniature diorama**（等距微缩场景）：等距 tiny room、城市/办公室/日式街区/节庆场景
- **3D chrome / liquid metal / neon**（液态金属/霓虹/镀铬立体字）：logo、海报大字、3D text effects
- **Low-poly / paper craft / origami**（低多边形/纸艺/折纸）：风格化插画、editorial 插图

Lite 也能跑 3D 风格（出概念快），但玻璃折射/金属反射细节明显弱于 Pro，正式交付用 Pro 2K。

## 结构 Guardrails（所有 3D 风格通用）

### 1. 风格锚点关键词（开宗明义第一个短语）

- 毛玻璃：`frosted glass 3D app icon` / `毛玻璃 3D 图标` / `glassmorphism 3D icon, translucent frosted milky-white glass`
- 粘土潮玩：`3D claymorphism Pop-Mart-style blind-box figurine` / `潮玩盲盒手办，3D 立体粘土风，Q 版圆润造型`
- 等距微缩：`isometric miniature diorama` / `3D isometric tiny room` / `等距微缩场景，tilt-shift 微缩模型感`
- 液态金属：`3D chrome liquid-metallic text logo` / `3D 镀铬液态金属立体字，镜面反射`
- 霓虹：`3D neon tube text` / `3D 霓虹光管字，pink-cyan 双色发光`
- 低多边形/纸艺：`low-poly 3D render` / `paper-craft origami illustration`

### 2. 配色与材质

| 子风格 | 推荐色板 | 材质关键词 |
|---|---|---|
| Frosted glass icon | 马卡龙 pastel：薄荷绿、薰衣草紫、奶黄、婴儿蓝、淡粉；或品牌单色 | `translucent frosted milky-white glass, subtle spectral iridescence on edges, soft volumetric light, subtle inner shadow, C4D Octane render` |
| Claymorphism | 高饱和马卡龙 + 1-2 主色 + 少量金/银点缀 | `matte clay texture, soft subsurface scattering, smooth rounded edges, chubby proportions, Pop-Mart blind-box vinyl figurine, soft studio key light` |
| Isometric diorama | 场景色（夜街暖黄窗光/办公室冷白/日式樱花粉/节庆红金）+ 黑或淡色底 | `isometric 3D render, tiny cute buildings, warm lit windows, miniature diorama, tilt-shift shallow depth of field, soft ambient occlusion, Blender/C4D quality` |
| Chrome / liquid metal | 深黑/深蓝/酒红暗底突出金属反射 | `mirror-polished liquid chrome, pink-cyan neon rim lighting, dark wet reflective floor, 80s synthwave, 3D Octane render` |
| Neon | 纯黑底 + 霓虹粉/青/紫/橙 | `neon tube glow, bloom and light spill, dark background, 3D glass tube letters` |

### 3. 构图与视角

- **App icon**：方图 1:1（`--square`），主物体居中占画面 60-70%，柔和渐变底或纯色底，无文字（图标本身不需要文字标签）
- **等距 diorama**：方图 1:1 或 3:4（`--square` / `--portrait`），等距投影是 30° 倾斜（写 `30° isometric perspective` / `等距 2:1 透视`），场景微缩感靠 `tilt-shift lens blur`、`miniature diorama`
- **3D 立体字 logo**：方图，字居中，暗底反光地面（`dark reflective floor with soft shadow and light reflection`）
- **盲盒手办**：方图 1:1，正前 45° 微微俯视，影棚双灯，纯浅灰/米色底，接触阴影柔和，像官方产品宣传照

### 4. AI 瑕疵规避关键词

- 玻璃/折射：`玻璃折射真实合理，边缘有彩虹色散（spectral dispersion）但不过度，内部无杂质无穿帮`
- 粘土/手办：`造型圆润无尖锐角，肢体融合自然，Q 版比例 2-3 头身，面部可爱但不恐怖谷`
- 等距场景：`等距透视准确，所有物体沿同一消失轴，无透视混乱，建筑不穿模`
- 金属反射：`镜面反射柔和，反射内容是模糊的环境光和光源（粉色/青色光带），不反射具体照片或人脸`
- 通用：`无水印、无乱码文字、无 logo、C4D/Octane 渲染质感、柔和全局光照、环境光遮蔽自然`
- **手办/角色 3D 模型手部**：能不露手就不露，必须露手时加 `手部圆润、手指融合为一体的 Q 版造型（无单独手指）` 最稳

### 5. 尺寸

- App icon/盲盒/立体字：`--square`（Pro 1024² 足够清晰）
- 等距微缩场景/landing 插画：`--portrait` (3:4) 或 `--landscape` (16:9)
- 全宽 hero 场景：`--wide` 1792×1024

## Inspiration Defaults

| 子风格 | 默认方向 |
|---|---|
| App icon（通用） | 方图 1:1、毛玻璃半透明、马卡龙渐变底（薄荷绿→薰衣草紫）、主体图标居中（云/文件夹/聊天气泡/齿轮等）、柔和体积光、边缘有轻微彩虹色散、纯白或同色渐变背景、C4D Octane render 质感 |
| 潮玩盲盒手办 | 方图 1:1、Q 版 2.5 头身、圆润造型、哑光粘土/vinyl 材质、马卡龙主色、纯色浅灰/米色渐变背景、影棚左右双灯 + 顶光、柔和接触阴影、Pop-Mart 官方宣传照风格 |
| 等距微缩场景 | 方图 1:1、30° 等距视角、tiny 微缩建筑/房间、暖黄窗光、浅景深 tilt-shift、环境光遮蔽、Blender/C4D 3D 渲染、底部柔和投影 |
| 3D 立体 logo 字 | 方图 1:1、深黑或深酒红底、液态金属/镀铬/霓虹材质、字居中、底部反光地面、粉青双光轮廓光、Octane render |

---

## Recipes

### Recipe 1：毛玻璃 App icon

```bash
uv run scripts/seedream_image_gen.py generate \
  --square \
  --prompt "A single frosted glass 3D app icon of a cloud storage folder, translucent frosted milky-white glass with subtle spectral iridescence on edges, cloud badge on top of the folder tab, macaron pastel gradient background (mint green to lavender purple), soft volumetric light, subtle inner shadow and gentle drop shadow below, C4D Octane render quality, clean minimalist iOS-style icon, centered composition, no text, no logo, no watermark, 2K, 1:1 square"
```

- 替换主体：把 `cloud storage folder` 换成 `chat bubble / gear settings / music note / camera / rocket ship / heart / lightning bolt / shopping bag / coffee cup / book` 等。
- 变体：品牌色版本加 `in brand colors [主色] and [辅色]`，全息版加 `holographic iridescent, mother-of-pearl sheen`，哑光版改 `matte silicone rubber instead of glass`。

### Recipe 2：Pop-Mart 盲盒潮玩手办

```bash
uv run scripts/seedream_image_gen.py generate \
  --square \
  --prompt "3D claymorphism Pop-Mart-style blind-box vinyl figurine of a chubby cute astronaut cat, Q-version 2.5-head chibi proportions, rounded body with no sharp edges, matte clay texture with soft subsurface scattering, wearing a white and pastel-blue spacesuit with tiny gold fishbowl helmet, pastel macaron color palette, sitting pose on a simple rounded display base, soft studio three-point lighting on a clean light-gray gradient background, soft contact shadow underneath, official product photography for designer toy, C4D render, centered, no text, no logos, no watermark, 2K, 1:1 square"
```

- 角色替换：`astronaut cat` → `cyber-panda in streetwear` / `cherry-blossom fairy girl` / `moon rabbit with hanfu` / `dumpling character` / `coffee cup mascot` / `space penguin`。
- 风格微调：国潮汉服版加 `wearing mini hanfu with red and gold Chinese cloud patterns`，赛博版加 `neon visor, holographic jacket, cyberpunk backdrop`。

### Recipe 3：等距微缩日式夜街

```bash
uv run scripts/seedream_image_gen.py generate \
  --square \
  --prompt "3D isometric miniature diorama of a tiny cozy Japanese neighborhood at night, miniature buildings with warm lit windows, tiny ramen shop with red lantern in foreground, vending machine with glowing buttons, cherry blossom tree with pink petals, small streetlamp casting warm glow, 30-degree isometric perspective, tilt-shift shallow depth of field (foreground and background softly blurred), soft ambient occlusion, Blender 3D render, clean dark-blue night sky gradient background, no text, no logos, no watermark, highly detailed, cute cozy atmosphere, 2K, 1:1 square"
```

- 场景替换：`tiny coffee shop interior` / `tiny bookstore with reading nook` / `tiny Chinese tea-house with red lanterns` / `tiny space station interior` / `tiny Christmas village in snow` / `tiny izakaya alley` / `tiny startup office with laptops`。
- 节日变体：中秋换成 `tiny moon-viewing platform with rabbit and full moon, warm golden light`；春节换成 `tiny Chinese courtyard with red lanterns and fireworks`。

### Recipe 4：3D 液态金属霓虹字（logo/标题）

```bash
uv run scripts/seedream_image_gen.py generate \
  --square \
  --prompt "3D chrome liquid-metallic text logo spelling 'NEON' in bold geometric sans-serif font, letters have mirror-polished liquid-chrome reflective surface, pink and cyan neon rim lighting outlining the letters, letters sitting on a dark wet reflective black floor with soft pink-cyan light reflections, dark black background, 80s synthwave retro-futuristic aesthetic, Octane render, centered composition, letters spelling exactly N-E-O-N in order, no other text, no watermark, 2K, 1:1 square"
```

- 替换词：`NEON` → 你的品牌/标题（建议 ≤6 个字母）。
- 材质变体：`polished gold / brushed silver / rose gold / frosted glass / crystal / jade / ice / gummy candy / glossy plastic`。
- 注意：**单词拼写要逐字母准确**，在 prompt 里显式写"letters spelling exactly X-Y-Z in order"（或中文"字依次是 X、Y、Z"）；中文立体字一次 ≤4 字最稳。

### Recipe 5：等距 Landing 插画（SaaS 风格）

```bash
uv run scripts/seedream_image_gen.py generate \
  --landscape \
  --prompt "3D isometric SaaS landing-page illustration of a tiny cloud server room, cute isometric server racks with glowing green status LEDs, floating cloud icons connected by thin glowing blue data lines, small cartoon human figure pointing at a holographic data chart, 30-degree isometric perspective, soft corporate blue and white color palette with orange accents, soft studio lighting, ambient occlusion, clean light-gray gradient background, lots of negative space on the left for headline text overlay, Blender 3D render, no text, no logos, no watermark, 2K, 16:9 landscape"
```

适合：官网 hero、博客头图、产品功能介绍页配图。左侧或右侧留 40-50% 负空间给后期加标题/CTA。

---

## 翻车提醒

1. **App icon 里文字/字母**：App icon 本身不应有文字（系统会自动加 app 名标签），所以 prompt 里写 `no text, no letters, no words, no logos` 防止模型乱加"App"或假 app 名。
2. **3D 手办/角色的手**：3D 粘土手办的手指是重灾区——Q 版角色让手简化为圆球状（mitten hands），或把手藏在衣服/道具后面，或插兜。
3. **等距透视混乱**：必须显式写 `30-degree isometric perspective / 30° 等距视角`，否则模型会出两点透视或自由透视，失去 diorama 的"微缩模型"感。
4. **折射过强变彩色塑料**：毛玻璃图标加 `subtle spectral iridescence on edges only`（仅边缘有彩虹色散），否则会像廉价全息塑料。
5. **金属反射里出现具体人脸/照片**：加 `reflections show only blurred colored lights and environment gradients, no faces, no photos, no real-world scenes reflected`。
6. **长单词 3D 字拼写错误**：超过 6 个字母的单词建议拆音节或全大写逐字母写 `"A-R-T-I-F-I-C-I-A-L"`，并加 `letters spelling exactly in order, each letter legible`。中文立体字 ≤4 字最稳。
