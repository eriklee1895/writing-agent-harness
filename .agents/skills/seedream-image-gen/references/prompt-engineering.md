# Seedream 提示词工程指南（Pro 主用）

> 本指南以 **Seedream 5.0 Pro** 为默认模型。Lite 的 prompt 写法基本兼容，但要注意 Lite 的文字渲染明显弱于 Pro——涉及大量文字/小字/中英混排时请用 Pro。

## 本文导航

先按任务定位到对应「公式」，再按需查配置与避坑段落：

| 你要做什么 | 读哪一节 |
|---|---|
| 任意 t2i / img2img 通用骨架 | 公式 1：通用图像 |
| 出大字 / 中英混排 / logo 环形字 ⭐ | 公式 2：文字渲染 |
| 在已有图上换字/换物/多区域改 ⭐⭐ | 公式 3：Marker 区域编辑 |
| 同一人/物跨多场景保持一致 | 公式 4：参考图一致性 |
| 把照片变成某种画风 | 公式 5：风格迁移 |
| 多张参考图融合（脸+服装+色板等） | 公式 6：多参考图融合 |
| 调 negative / 选中英文 / 速查最佳实践 | Negative Prompt · 语言选择 · 最佳实践速查表 |
| **动笔前必看**：11 条高频翻车关键词与防御 | 常见反模式 |
| 哪些场景别指望 Pro / 高级镜头·字体·权重技巧 | 已知翻车场景 · 社区验证有效的高级技巧 |
| 一个从啰嗦到精炼的完整改写案例 | 经典 Prompt 改写示例 |

## 公式 1：通用图像（t2i / img2img 通用）

```
[风格锚点] + [主体 + 行为 + 环境] + [细节元素] + [色彩 + 光影 + 构图] + [分辨率/比例/用途]
```

**拆解**：
- **风格锚点**：开头第一个短语锁定画风（"超写实摄影"、"北欧极简杂志编辑风"、"赛博朋克概念艺术"、"吉卜力动画风"、"包豪斯平面设计"、"复古美式广告插画"、"日系浮世绘"、"中国风水墨写意"）。可覆盖广泛用途：社媒封面/banner、产品海报、品牌视觉、电商主图、包装插画、游戏概念、logo 徽章、图书封面、公众号头图、视频封面等。
- **主体+行为+环境**：自然语言描述"谁在什么地方做什么"。
- **细节**：具体物体、材质、纹理、氛围；用**具象名词**（中式场景下"白墙黑瓦徽派建筑" > "古建筑"，"霁红釉" > "传统红色"；西式/通用场景下"matte black aluminum unibody" > "sleek modern object"，"terrazzo flooring with brass inlay" > "nice floor"）。
- **色彩+光影+构图**：色板、光源方向、景别（特写/中景/远景）、景深。
- **分辨率/比例/用途**：如"16:9 宽幅 banner/封面（社媒/博客 hero/公众号头图/视频封面）"、"3:4 竖版海报"、"1:1 方形头像/产品图"、"9:16 手机竖屏/Stories"、"A4 印刷海报"。如果你已经通过 CLI flag（`--wide`/`--portrait`/`--landscape`/`--square`/`--size WxH`）传了精确尺寸，这里只要描述用途和留白需求即可；如果没传尺寸 flag，这里写的"竖版/横版/方形/手机壁纸"会让模型在默认 2K 附近挑一个合理比例——精确要求（平台像素规范）优先用 CLI flag，自然语言描述（"手机壁纸感"）适合不锁死像素的场景。

### 1.1 草图/线框图 → 高保真渲染（img2img）

把手绘草稿/线框图/block layout 作为 `--reference-image` 传入，prompt 里**明确说"严格保持参考图的布局分区/元素位置关系"**，再指定风格和细节填充：

```
根据参考图的粗略线框图/block layout 生成高保真[活动海报/官网首屏/产品海报]。
严格保持参考图的区域划分和元素位置关系——顶部为[标题区]、中间为[主视觉区]、
右侧/底部为[辅助信息区]——每个区域的相对位置和大致比例不要变动。
填充细节：[风格/色彩/光影/具体元素描述]。
文字包括：『[逐字写内容]』，清晰无错字。整体[风格关键词]，2K，[比例]。
```

关键：
1. **布局描述必须绑定"参考图"**——"保持参考图布局 / follow the layout in the reference"而不是自己凭空描述分区，否则模型会自由重排。
2. **风格词放在布局词之后**——先锁结构再填风格，跟公式 5（风格迁移）"先锁内容再换皮肤"同一个顺序原则。
3. **文字/按钮/标签等 UI 元素逐字写**——草图里写的占位（"标题""按钮"）不会自动渲染成真实文字。
4. For "sketch → tech-style" AI-conference-poster tasks, the layout is roughly preserved, but visual punch (gradients, light beams, grids, chip textures) comes out under-specified unless the prompt piles on concrete light/material/reference-genre details.

## 公式 2：文字渲染（Pro 专属 headline 能力）⭐

这是 Pro 相比 Lite 提升最大的部分——中文大字、英文字母、中英混排、logo 环形字都能可靠出字。

```
[背景/版式] + [文字内容（用引号/书名号包起来，逐字写准）] +
[字体/字重/字号/颜色/对齐/位置] + [装饰元素] + [整体风格]
```

### 2.1 大标题（海报/封面/banner，中英通用）

```
极简杂志风海报，浅米色纸张质感背景，居中黑色粗体无衬线大标题写着"AI 工具实战"，
字号占画面高度 1/6，下方较小灰色副标题"2026 年度实战指南"，
右上角一个蓝色极简几何 AI 芯片图标，底部留白，编辑设计感，2K，3:4 竖版
```

关键要点：
- **文字内容用引号括起来，逐字准确**——不要写"标题是关于 XX 的"，要写"标题写着『XXX』"。
- **显式指定字体描述**：`粗黑无衬线` / `思源宋体` / `手写毛笔字` / `圆润卡通体` / `等宽代码字体`。Seedream 对这些常见中文字体族都有训练。
- **显式说位置与对齐**：`画面顶部居中` / `左对齐` / `占据画面上 1/3`。
- **显式说字号比例**：`字号占画面高度 1/6` 比"大字"可靠。

### 2.2 英文标题

```
Tech blog cover, dark navy gradient background, large bold white sans-serif headline
"Claude Opus 4.8" centered in upper third, subtitle "Agentic coding at scale" smaller
below in light gray, minimal blue geometric code-bracket icon in lower right, 2K, 16:9
```

英文 prompt 对英文字效果最好（模型对英文 token 化更细）。**Title Case 或 ALL CAPS 显式指定**，避免模型随机大小写。

### 2.3 中英混排

分行写内容，并显式说"中英字体字号保持视觉平衡"：

```
双语科技海报，白色背景，顶部居中大号黑色粗无衬线中文标题"大模型时代"，
其下一行稍小英文标题 "The Age of Foundation Models"，中英字体字号视觉平衡，
下方是一条灰色细分隔线，中部是三个蓝色 AI 芯片线性图标横向排列，
整体简洁专业，2K，3:4
```

### 2.4 圆形徽章 / Logo 字

```
圆形徽章 logo，藏青色底，白色粗衬线英文字母沿圆环顶部弧形排列 "SEEDREAM 5.0 PRO"，
圆环中心红色印章风格"豆包"两个中文字，外围一圈金色月桂枝装饰，
矢量扁平化风格，纯白背景，2K，方形
```

关键：**"沿圆环顶部弧形排列"**——这个 phrase 模型理解得很准。

### 2.5 信息图中的文字标签（慎用）

Pro 在技术架构图/流程图里的模块标签、坐标轴文字表现明显好于 Lite，但**小字（< 画面 1/30 高度）仍可能错字**。缓解办法：

- 标签短语越短越好（2–4 字/词最稳）。
- 显式说：`每个方框内有白色小标签文字，字迹清晰锐利，逐字准确`。
- 如果是数学公式、乐谱、象棋谱、密集表格——**不要依赖模型**，出图后用专业排版工具（LaTeX / HTML+CSS / 制谱软件 / 表格工具）生成再合成。

### 2.6 长段正文 / 手写体 / 小字

Pro 的文字能力**边界**：
- ✅ 大字标题、slogan、标签（单条 ≤12 字/词）、logo 字、数字
- ⚠️ 2–4 行短句（半段落）：可用但要逐字检查
- ❌ 大段正文（8 行以上）：错字率高，不要依赖
- ❌ 连笔手写体（中文草书/英文 cursive）：笔画会糊
- ❌ 密集小字信息图（如地铁图/时刻表）：错字
- ❌ 数学公式 / 乐谱 / 象棋/围棋谱：结构性强的符号系统 Pro 仍会错
- ❌ 名人题词/签名：会造

### 2.7 为什么默认 2K

Latency is nearly identical at 1K and 2K (both ~95s mean), but at 2K:
- 中文字笔画更锐利，不会出现"糊边"。
- 英文字母间距更均匀。
- 小字错误率明显下降。

所以除非明确要省成本（¥0.30 vs ¥0.60）或要做快草图，否则全部用 2K。

## 公式 3：Marker 区域编辑（Pro 专属）⭐⭐

Marker 编辑是 Pro 最大的效率提升——**不需要 mask/bbox API**，在参考图上画个彩色矩形，prompt 用自然语言描述框内要做的改动即可。本 skill 的 `edit` 子命令通过 `--marker-rect X,Y,W,H` 自动完成画框、发图、追加擦除指令三步。

### 3.1 换字（最常见，first-try成功率高）

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image my-poster.png \
  --marker-rect "5%,6%,90%,25%" \
  --prompt "红框中的标题文字替换为"GPT-Image 2 全面解析"，
保持粗黑无衬线字体、字号、位置、居中不变，
下方副标题、蓝色图形、背景完全保持原样。"
```

Prompt 模板：
```
[红/蓝/绿]框内的[原对象]替换为[新对象描述]，
保持[字体/字号/材质/光影/透视/位置]与原图一致，
框外像素完全不变。
```

### 3.2 换物/换材质

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image living-room.png \
  --marker-rect "10%,45%,80%,40%" \
  --prompt "红框内的米色布艺三人沙发替换为深蓝丝绒三人沙发，
带黄铜细脚，丝绒材质有柔和光泽，透视与位置完全保持，
阳光从左侧窗户照进来在沙发上形成的光斑方向不变，
红框之外的地毯、茶几、落地灯、墙面保持原样。"
```

### 3.3 多区域多色

用 `--marker-color` 切换颜色，prompt 里分别引用颜色：

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image poster.png \
  --marker-rect "5%,6%,90%,25%" --marker-color "#ff0000" \
  --marker-rect "5%,75%,30%,20%" --marker-color "#0066ff" \
  --prompt "红框（顶部）标题替换为「新标题」保持字体字号位置不变；
蓝框（左下）日期区域的'2025'替换为'2026'；
其他区域像素完全保持，擦除所有红/蓝标记。"
```

### 3.4 添加/移除元素

加元素：
```
"红框位置（原本空白的墙面）添加一幅挂在墙上的黑色细框抽象画，画框大小与沙发成比例，
墙面打光自然，加投影，保持其他部分不变。"
```

移除元素：
```
"红框内的落地灯从画面中移除，该区域还原为原本的米白墙面和木地板，光影自然融合。"
```

### 3.5 Marker 编辑的 prompt 结构建议

1. **先说颜色+位置**："红框内……"
2. **说清楚原对象→新对象**："把米色沙发换成深蓝丝绒"
3. **说要保留的不变量**："保持透视、光照、阴影方向不变"
4. **Say the outside stays unchanged**: "pixels outside the box remain exactly as-is" — the auto-appended cleanup instruction already carries this meaning; restate it for critical jobs.

## 公式 4：参考图一致性（同一人/物多场景）

Pro's single-reference identity hold reaches "character-sheet" usability — a front-facing portrait as ref plus a prompt describing a new scene and pose keeps the face/outfit/key features intact.

```bash
uv run scripts/seedream_image_gen.py generate \
  --reference-image portrait-front.png \
  --prompt "参考图中年轻东亚女性的面部特征（圆框眼镜、短发齐刘海、圆脸型、奶油色毛衣），
将她置于夜晚下雨的东京涩谷十字路口，穿黑色风衣，
蓝紫色调霓虹灯光打在脸上，湿地面反射霓虹，浅景深电影感，2K，16:9"
```

Prompt 模板：
```
参考图中[主体身份/识别特征列表]，
将其置于[新场景/新姿势/新服装/新光照]，
保持面部特征/关键物件/身份一致性，
[新画面的风格/光影/构图]
```

**特征列表越具体越好**——列出"圆框眼镜、短发齐刘海、奶油色毛衣"比"保持这个人"可靠得多。

## 公式 5：风格迁移

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image photo.png \
  --prompt "将这张照片用梵高油画风格重绘，
厚涂笔触、旋涡状天空、强烈的黄蓝对比，
前景人物与物体保留构图但全部用可见笔触重画"
```

Mainstream style anchors ("梵高/莫奈/吉卜力/新海诚/漫威漫画/像素风/浮世绘/赛博朋克/水墨写意") elicit strong responses.

## 公式 6：多参考图融合（Multi-Reference Fusion，Pro 最多 10 张，Lite 14 张）

Pro accepts multiple `--reference-image` arguments (up to 10) for: locking a character's identity across angles, placing a product in different scenes, role-split composition of face + outfit + palette, foreground/background compositing. The sweet spot is 2-3 refs; above 4 refs outputs begin to average/muddle.

```bash
uv run scripts/seedream_image_gen.py generate \
  --size 1792x1024 \
  --reference-image face.png \
  --reference-image outfit.png \
  --reference-image palette.png \
  --prompt "第一张参考图锁定女性的面部身份（圆框眼镜、短波波头、银色小发夹）；
第二张参考图为她穿上红色丝绸旗袍；第三张参考图的 pastel 配色（珊瑚/桃/薄荷/天蓝）
作为场景点缀色；
她站在中国传统庭院黄昏时分，两侧红灯笼散景，电影感光线，2K，16:9"
```

### 6.1 参考图数量甜点

| 参考图数量 | 效果 | 评分 |
|---|---|---|
| 1 张 | 强身份锚定（面部/产品造型锁得最死），场景/光线/姿势可完全重生成（R1/R6 都拿到 8.5-9/10 身份保持） | 8-9/10 |
| 2-3 张 | 甜点。脸 + 服装 / 产品 + 场景 / 角色 + 色板这种"异质参考"组合效果最好（R4：脸+旗袍 9/10 身份保持；R7：脸+色板 8.6/10） | 8-9/10 |
| 4 张 | 开始出现"平均脸 / 平均产品"——ref 之间特征冲突时模型会选一个当主锚（R8 两张形状不同的耳机盒，模型没融合成一个产品而是复制成三联画，左右两格形状不一致） | 5-7/10 |
| >4 张 | 不建议。身份锚点模糊、风格互相打架、出现多余水印/文字 bleed | <5/10 |

### 6.2 ref[0] 身份锚定效应（关键！）

R1/R6/R7 都证明：**第一张参考图（CLI 里第一个 `--reference-image`）是默认的"身份锚"**——它的面部拓扑、发型、眼镜、关键配饰（发夹）会被最强地保留。第二张及以后参考图默认被解释为"服装/色板/风格/道具参考"，除非 prompt 里明确指定角色分工。

所以传参顺序很重要：
- **最想保留身份的那张（人物正面照 / 产品白底主图）放第一个。**
- 辅助参考（服装、场景 mood board、色板）放后面。

### 6.3 三种典型分工模式

#### 模式 A：单角色身份锚 + 新场景（1-2 refs）

适合同一角色跨场景系列（文章配图、故事书、social content）。

```bash
uv run scripts/seedream_image_gen.py generate \
  --reference-image portrait-front.png \
  --size 1792x1024 \
  --prompt "参考图中年轻东亚女性（圆框眼镜、黑色齐下巴短发、右侧银小花发夹、奶油色高领衫），
保持她的面部特征和发型配饰完全一致，将她置于夜晚下雨的东京涩谷十字路口，
穿黑色风衣、打黑伞，霓虹粉蓝光打在脸上，湿地面反射霓虹，浅景深电影感，2K，16:9"
```

Identity hold lands at 7-8.5/10; small accessories (hair clips) shrink/simplify, and eyeglass-frame material may drift (clear acetate → thin metal), but the subject is recognizably the same person across scenes.

#### 模式 B：产品白底 + 场景 lifestyle（1-2 refs）

适合把白底产品图放到 lifestyle 场景里（R2 耳机盒放大理石桌面 7/10 身份保持 + 9/10 商业质感）。

```bash
uv run scripts/seedream_image_gen.py generate \
  --reference-image earbuds-white.png \
  --size 1536x2048 --portrait \
  --prompt "参考图中的哑光黑色无线耳机充电盒（开盖、两只耳机竖立在盒中、椭圆侧按钮、银色pogo pin触点），
将产品保持相同造型和材质语言，放置在深色大理石桌面上，45° 视角，
下午窗边自然光投射长长柔和斜影，背景虚化可见帆布托特包一角、拿铁咖啡杯、合上的银色笔记本电脑边缘，
产品占画面 60%，商业产品摄影质感，柔光自然，3:4 竖版"
```

注意：模型会重选相机角度（参考图左前 3/4 → 输出略偏正 3/4）和耳机姿态。要严格锁角度必须再加一张目标角度的参考图，或接受"同 SKU 非 1:1 移植"。

#### 模式 C：角色分工——ref1=脸 / ref2=服装 / ref3=色板（3 refs）

适合"她穿这套衣服在这种氛围里"的编辑时尚类（R4 脸+红旗袍 9/10 身份保持，是本 sweep 里最强的多 ref 结果）。

```bash
uv run scripts/seedream_image_gen.py generate \
  --reference-image face.png \
  --reference-image cheongsam.png \
  --reference-image pastel-swatches.png \
  --size 1536x2048 --portrait \
  --prompt "第一张参考图锁定女性的脸、发型、眼镜、银小花发夹；
第二张参考图的红色丝绸旗袍（红缎面、金色牡丹/云纹/海浪刺绣、立领、盘扣、七分袖）穿在她身上；
第三张参考图的 pastel 珊瑚/桃/薄荷/天蓝色作为环境点缀光和花影颜色，不盖过红旗袍主色；
她站在中国江南传统庭院里，黄昏暖光，两侧红灯笼 bokeh，电影感 3/4 人像，3:4"
```

关键是**在 prompt 里逐张明确说"X 图用什么，Y 图用什么"**——不要只说"combining all references"，R3 两张同角色不同表情/服装/眼镜/光线的 ref 没分配角色时模型会挑一张当主锚（R3 选了带笑的第二张），第一张只贡献了服装和光线。

#### 模式 D：多张人脸合成到同一场景合影（N 张单人照 → 1 张合影，refs ≥3）

适合"把 N 张单人证件照/自拍合成同一张合影"（团队照、活动合影、family portrait 类场景）。关键是**显式给每张脸分配站位**，否则模型会把人脸平均化。

```bash
uv run scripts/seedream_image_gen.py generate \
  --reference-image group-pose-ref.png \
  --reference-image person-A.jpg \
  --reference-image person-B.jpg \
  --reference-image person-C.jpg \
  --reference-image person-D.jpg \
  --reference-image person-E.jpg \
  --size 2048x1152 --landscape \
  --prompt "第一张参考图给出合影站位构图：户外咖啡馆露台，五人合影，
后排站立三人、前排坐着两人，背景是树木和咖啡馆门店。
第 2-6 张参考图分别是五位人物的面部参考：
后排左一用图2的人脸（短发戴眼镜东亚男性，30 多岁），
后排中间用图3的人脸（齐肩卷发东亚女性，28 岁穿米白针织衫），
后排右一用图4的人脸（络腮胡白人男性，40 岁深色衬衫），
前排左一用图5的人脸（马尾年轻女性，25 岁牛仔外套），
前排右一用图6的人脸（灰发戴眼镜长者，60 岁休闲西装）。
统一下午四点侧逆光暖金色光线，所有人面部光照方向一致、色温一致，
真实摄影质感、f/4 中焦镜头、浅景深、团队合影商业摄影。2K，16:9"
```

关键：
1. **第一张 ref 用作站位/构图参考**（可以是 AI 生成的占位合影、一张任意人群照片——只取站位关系不保留脸），后续 refs 逐张对应到站位上。
2. **逐人给四元组**：位置（后排左一）+ ref 编号 + 关键视觉锚（发型/年龄/服装关键词），跟群体照逐人枚举（photorealism.md）同一个方法论。
3. **显式说"统一光源方向/色温"**——N 张来源不同的自拍光线差异大，必须用一句话强制模型重打光，否则每个人物脸上光方向不一致会露馅。
4. 参考图总数建议 ≤6（1 站位 + 5 人脸），再多会撞"4 张以上身份糊化"坑点。超过 6 人合影分两排（3 站 3 坐），每人描述缩短到"位置 + ref 编号 + 一个视觉锚"三元组。
5. Facial similarity lands at ~7-8/10 — subjects are recognizably themselves, but details (moles, frame material, small accessories) simplify and drift; for high-stakes formal settings use a real photograph.

### 6.4 多 ref 坑点

| 坑 | 表现 | 规避 |
|---|---|---|
| >4 refs 身份糊化 | 面部变成"平均脸"，产品变成"不像任何一张 ref 的混合体" | 2-3 张最稳；必须多张时把最核心身份放 ref[0]，其余做弱提示 |
| refs 风格差异巨大时（R5：极简纸感海报 → 吉卜力拉面店） | 风格 ref 几乎被忽略，输出按强场景 prompt 走（R5 出了吉卜力风拉面店，纸张/编辑 DNA 全无） | 风格迁移不要用风格完全无关的 ref；要风格迁移走 img2img style transfer（公式 5） |
| refs 产品形状冲突（R8：方耳机盒 + 鹅卵石耳机盒拼三联画） | 模型不融合形状，而是"忠实复制"每张 ref 到各自面板，三联画变成两个 SKU 并排 | 产品多视角 refs **必须是同一个产品同一种状态**（都开盖、都关盖、都同角度转向），否则走单图多角度渲染后代码拼图 |
| 参考图里的文字/标签 bleed | 色板图上的"PASTEL COLOR PALETTE"标题和 hex 文字不会 bleed 到输出（R7 验证） | 无需特别规避；但密集文字参考（书页、报纸、表格）仍可能 bleed |
| 长宽比/构图冲突 | 竖版人物 + 横版场景 refs 时模型倾向选主 ref[0] 的构图 | 主构图 ref 放第一个，其他 refs 只做局部（服装/色板）参考 |
| 配件/细节优先从 ref[0] 丢失 | 小发夹简化、透明眼镜变金属框（R1/R3/R6 都有） | 关键配饰在 prompt 里重复描述一次（"银色小花发夹别在她右侧"），双重锚定 |

### 6.5 多 ref 模板

```
第一张参考图：[身份锚内容——人物五官/发型/配饰/产品造型]，保持这些元素一致；
第二张参考图：[服装/道具/场景]——把[元素]赋予第一张的主体；
[第三张参考图（可选）：色板/光线/材质 mood——作为整体氛围参考，不改动主体身份]；
主体置于[新场景/新光线/新姿势]，[构图/景别/画幅]；
不要把参考图里的文字/水印/logo/边框带到结果里。
```

## Negative Prompt（Pro 默认已加）

本 skill 在 Pro 下默认加 negative prompt：

```
模糊, 低质量, 水印, 变形, 多余肢体
```

关闭：`--no-negative-prompt`。覆盖：`--negative-prompt "..."`。

Negative prompt 对 Pro 的文字错误率**帮助有限**（错字主要靠 2K + 明确文字描述解决，不是负向排除），但对畸形肢体、低清糊脸、水印类问题有效。

## 语言选择

Seedream 是**中文原生模型**——这点和以英文语料为主训练的图像模型相反。很多用户因为旧肌肉记忆默认写英文 prompt，会平白丢掉中文语料的优势。

### 决策表（先看这个）

| 场景 | 推荐 prompt 语言 | 为什么 |
|---|---|---|
| 中式审美/中国场景（节气/水墨/国潮/中式建筑/中式美食/传统节日） | **全中文** | 文化概念、菜品名、书法/器物术语中文 token 化最细；写"红烧狮子头""徽派马头墙""瘦金体"比任何英文翻译都准 |
| 中文文字出现在图里（海报/封面/banner 标题） | **全中文**（文字内容用「」引号逐字包起来） | 中文字形、字重、字号、位置描述中文最自然；英文 prompt 写中文字常出现笔画错误/同音字替换 |
| 纯英文排版/英文 logo/拉丁语系品牌/欧美风格视觉 | **全英文** | 英文字母间距、Title Case/ALL CAPS、Bodoni/Futura/Helvetica 等拉丁字体名英文描述更准；英文 prompt 出英文字母一次成率高 |
| 摄影/3D/灯光/材质/渲染**技术术语**（bokeh, rim light, key light, subsurface scattering, impasto, chiaroscuro, shallow depth of field, volumetric fog, specular highlight, cinematic lighting） | **英文术语原文嵌入** | 这类术语中文翻译不统一（"轮廓光/边缘光/rim light"混用），直接用英文词模型理解最准；嵌套在中文或英文叙事里都可以 |
| 中英混排海报（中文主标题+英文副标题/英文字 tag/slogan） | **中文叙事为主，嵌入英文短语**（保持英文原文大小写） | 自然写法，模型吃这种最顺——"白色粗无衬线主标题『AI 时代』，下方小号英文副标题 'The Age of Agents'" |
| 日本/韩国/东亚题材（动漫/浮世绘/韩服/日式料理） | 中文为主，关键专有名词保留原语言（"新海诚风格" / "ukiyo-e" / "sushi" / "kimono"） | 中日韩文化概念中文训练语料够强，不用硬写日文/韩文 prompt |
| 西方艺术史风格（文艺复兴/新艺术运动/包豪斯/巴洛克/Art Deco） | 英文或中文风格名都可（"Art Nouveau" / "新艺术运动" 都认） | 选你 reference 里用的语言；不确定用英文更通用 |
| 游戏概念/UI/图标/科技视觉（concept art, matte painting, user interface, 3D icon, cyberpunk） | **英文术语 + 中文/英文叙事都行** | 这类是视觉语言全球通用的，关键是术语准确（"matte painting"、"isometric"、"low-poly"） |

### 常见误区

- ❌ **"English prompts are more professional" — does not hold for Seedream.** This is muscle memory from English-native model eras. Seedream's Chinese training corpus covers Chinese scenes, Chinese text, and cultural terms far more deeply than English. Writing English prompts for Chinese subjects tends to produce "Oriental-style" pan-Asian (Japan-inflected) mixes.
- ❌ **全英文 prompt + 中文文字内容**——容易错字、笔画糊。中文文字必须中文描述字体、字号、位置。
- ❌ **硬翻英文技术术语成中文**——"散景""景深""体积光"这类中文译法模型也能认，但英文原词（bokeh/depth of field/volumetric lighting）更稳，尤其当你想精确控制光效时。
- ✅ **黄金组合：中文叙事主语 + 英文技术术语 + 需要出现的文字逐字「」包裹。** 这是中国设计师日常说话的方式，也是 Seedream 最强的 prompt 形态。

### 示例

**全中文（春节海报）**
```
春节喜庆海报，朱红 #C0392B 底色烫金 #D4A24C 大字，居中粗宋体标题「新春快乐」，两侧红灯笼和金色烟花装饰，文字印刷锐利、无错字，新国潮商业插画风格
```

**中英混合（科技产品图）**
```
产品摄影，一副哑光黑色 wireless headphones 放在深色大理石桌面上，45° 俯视，soft natural window light from left, metal rim light 勾勒边缘高光，shallow depth of field，冷色调，commercial advertising photography, 2K
```

**全英文（欧美时尚封面）**
```
Vogue-style magazine cover, right 2/3 is a close-up portrait of a young East-Asian woman with short black bob, wearing a black turtleneck and gold geometric earrings, confident gaze at camera, studio hard light, medium-format depth of field, left 1/3 is a white serif vertical title "THE NEW INTELLIGENCE", Bodoni-style serif font, Vogue cover aesthetic
```

### 其他语种

- 日文/韩文/法文/德文/西文/阿拉伯文等非中英文字：短标题/slogan（≤8 字符）可以直接写在 prompt 里（保持原拼写），配合英文/中文描述版式风格；长段正文仍不推荐。
- 阿拉伯文/希伯来文等 RTL 文字：排版稳定性差，建议后期叠加。
- 日韩文化场景（动漫/寿司/韩服）用中文或英文 prompt 就够，不需要写日文/韩文。

## 最佳实践速查表

| 场景 | 建议 |
|---|---|
| 想清楚主体再动手 | 先写 1 句话主体描述，再加风格锚点、再加细节 |
| 风格不要混太多 | 一个主导风格 + 最多一个辅助修饰；"赛博朋克+水墨+梵高"会糊 |
| 具象名词 > 抽象形容词 | "白墙黑瓦徽派建筑" > "中国风古建筑" |
| 文字必须引号括起来 | 写"标题写着『XXX』"，不要"标题关于 XXX" |
| 涉及文字默认 2K Pro | 1K 文字边缘糊，Lite 错字率高 |
| 改图用 marker，不要重建 | edit + `--marker-rect` 比重头 t2i 成本低、一致性好 |
| 同一人多场景列特征清单 | 不要只说"保持这个人"，要列眼镜/发型/衣服 |
| 出活前用 `--dry-run` | 检查 body 里 size/model/refs/neg 都是对的，避免白烧钱 |
| 批量并发要克制 | `--concurrency 3` 已经很快（RPM 500 理论上限，实际 5–10 并发稳） |
| 错字/畸形重试一次 | 同 prompt 跑两次选好的；第二次可微调"字迹清晰锐利，逐字准确"加强 |

## 常见反模式（高频翻车，用这些关键词防御）

These are recurring pitfalls from 21-case evals and community reports. Each includes a corrected "how to write it" example.

### 1. "手机/9:16/stories" 会生成假的手机 UI 界面

只要 prompt 里出现"手机"、"mobile"、"9:16"、"stories"、"竖屏视频"，模型很容易脑补出顶部状态栏（时间/WiFi/电池图标）、底部导航按钮、甚至整个手机壳或 App 界面，把美食/人物/产品夹在假 UI 中间。

**防御**：明确写"纯画面内容、无 UI 元素、无手机边框、无状态栏、无 App 界面、无底部导航栏"。9:16 尺寸靠 `--size WxH` 锁定，不靠文字描述"手机"。

```
❌ "9:16 手机竖版美食 story 图，一碗日式拉面"
✅ "9:16 竖版美食摄影，一碗日式豚骨拉面放在浅木桌上，暖黄餐灯光线从左侧打来，
    蒸汽缓缓升起，纯摄影画面、无手机边框、无 UI 界面、无状态栏、无 App 按钮、无任何图标"
    # 尺寸用 --size 1088x1920 锁，不要靠 prompt 说"手机"
```

### 2. "竖排英文标题" 会被解读为"中文竖排"，字母重叠错乱

中文竖排是一列一列一个字一个字排，但英文竖排设计（如杂志封面侧边栏）实际上是"每个字母/单词独占一行，水平排列、从上到下"，是 rotated/stacked Latin。模型默认按中文竖排逻辑去渲染英文，导致字母挤压、双影、错位、重复。

**防御**：显式描述英文竖排的结构——"one English word per horizontal line, stacked top-to-bottom, each word reads left-to-right"或中文描述"每个英文单词独占一行、水平书写、从上到下逐行排列、单词字母不旋转"。不要只说"竖排英文"。同时**显式锁位置**——写 `在左侧 1/3 留白区域（纯白背景上，不覆盖到人物/产品身上）`，否则模型会把文字叠到主体上。

```
❌ "左侧 1/3 留白处竖排英文大标题"THE NEW INTELLIGENCE""
✅ "左侧 1/3 纯白留白区域（不覆盖到右侧肖像）大号白色衬线字体英文标题，
    每个单词独占一行水平书写、从上到下逐行排列 THE / NEW / INTEL / LIGENCE，
    四行左对齐、严格在左侧留白边距内、Bodoni-style serif、
    字母不旋转不竖排、单词内字母顺序正常从左到右"
```

> **英文竖排必拆行**：超过 6 个字母的单词（INTELLIGENCE、SUSTAINABILITY 等）模型一行排不下会溢出，主动拆成两段（INTEL-LIGENCE、SUSTAIN-ABILITY）并告诉模型从哪里断行最稳。

### 3. 产品瓶身/包装/小物表面会自动生成乱码品牌名

护肤品瓶、精华液瓶、耳机充电盒、口红管、咖啡杯、书本封面、电器面板——凡是光滑/标签化/曲面的物体表面，模型爱"脑补"品牌 logo 和说明文字，生成一串无法识别的乱码（像是某个假法文/英文品牌的变形），破坏产品纯净感。

**防御**：在产品描述末尾显式加 `瓶身/包装/表面无品牌文字、无标签文字、无 logo、无说明文字、纯净无印刷`（英文：`no branding, no text printed on the product, no labels, no logos, clean unbranded surface`）。这是 prompt-engineering 里"否定指令"性价比最高的一条，比 negative prompt 有效。

```
❌ "一瓶金色精华液放在背景中"
✅ "画面右侧放置一瓶金色磨砂玻璃护肤精华液瓶，瓶身造型简洁现代，
    瓶身无品牌文字、无标签、无 logo、无印刷、纯净裸瓶、几何形状准确无扭曲"
```

### 4. 质量词堆叠没有用，反而会过锐化/出瑕疵

`8k, masterpiece, best quality, ultra-detailed, hyper-realistic, 4k uhd` 这类 SD/MJ 时代的质量堆叠词在 Seedream 里几乎没效果（服务端默认已经是高分辨率渲染），堆多了反而会让模型过度锐化边缘、出纹理瑕疵、色彩过饱和。

**防御**：质量意图用具体的风格锚点和技术术语表达，不要堆形容词——"商业广告摄影、f/8 影棚双灯、接触阴影自然、产品清晰锐利" 比 `8k masterpiece best quality` 有效得多。

### 5. 不要混用超过 3 个风格锚点

`赛博朋克 + 水墨 + 梵高 + 浮世绘 + 极简北欧` 这种多风格混搭 prompt 模型会精神分裂，出来的图四不像。

**防御**：一个主风格 + 最多一个辅助修饰。赛博国风这种看起来"混"的风格本质上是单一风格锚点（"赛博国风 cyber-guofeng"本身已成为独立视觉语言，不是两个风格拼起来）。

### 6. 不要在 API prompt 里随意换行

Prompt 中 `\n` 换行在部分 API 版本上解析不稳定，可能导致后面的描述被截断或降低权重。

**防御**：在 shell 里传 prompt 时用单行字符串（或用 here-doc 但 strip 换行），用中文逗号"，"或英文逗号"+"space分隔子句，不要靠换行断句。CLI 的 `--prompt` 参数已做基础 strip，但自己拼接 JSONL 或 body 时要注意。

### 7. 具象名词 > 抽象形容词

"白墙黑瓦徽派马头墙" > "中式古建筑"；"matte black aluminum unibody with brushed metal texture" > "sleek modern design"；"霁红釉陶瓷茶盏" > "红色茶杯"。Seedream 是中文原生模型，具体名词的 token 化比抽象形容词精确得多。

### 8. 文字默认就是"要出字"——不想出字要显式说"无文字"

只要 prompt 里出现 `text`、`title`、`文字`、`标题`、`logo`、`label`、`caption`、`slogan`、`留白用于放置大标题`、`留空给文字叠加` 这类词或意图，模型就会尝试渲染文字——即使你没指定具体文字内容，也会脑补一串乱码/假文字填满那个区域。

**防御 A（纯图/留空给后期加字）**：显式加 `无文字、无水印、无 logo、无任何文字内容、画面纯净、留空区域是纯背景（用于后期 PS 叠加标题）`，不要写"留白放置大标题"——"放标题"是让模型放，不是让你后期放。

**防御 B（想让 AI 出字）**：逐字用引号包裹，指定字体/字号/颜色/位置/对齐，参见公式 2。

```
❌ "左侧 60% 留白用于放置大标题，右侧放产品"  ← 模型会在左侧瞎编假字（"618 宿服"这种乱码）
✅ "左侧 60% 为纯渐变背景无任何文字无水印无logo（供后期设计叠加标题），
    右侧 40% 摆放产品"
```

### 9. 拍人/手的场景要做负面防御

手和手指是所有图像模型的老毛病。只要画面里有手，末尾加 `手部自然、手指数量正确、无畸形手指`；能避免露手就避免（产品图用 ghost mannequin 或道具支撑、人物用背影/剪影/半身/揣兜姿态最稳）。复杂手部姿势靠参考图（`--reference-image` 传一张真实手的照片）比负向词有效。

### 10. 真实地名（车站/地标/品牌）会触发 `InputTextContentDetected` 安全 block

Prompts that include real Chinese place names (e.g. "北京地铁 天安门 / 王府井 / 东单") trigger the Stage 1 input-side safety classifier, returning `InputTextContentDetected`. Rename and retry; the model will invent plausible-looking Chinese station names (金融城/望江门/湖滨东/...) with correct characters.

**防御**：写有真实城市/地标/品牌的场景时，先用泛化占位词（如"3-character Chinese station names"、"a famous European capital"、"a well-known luxury brand"），让模型自由生成占位；或用 **英文 transliteration**（"Tiananmen" / "Wangfujing"）绕过中文输入触发器。如果客户硬要真名，prompt 用 `"a major Beijing subway station on Line 1"` 这种描述性代替而不是直接 `天安门` 站。

```bash
# ❌ 触发 InputTextContentDetected
--prompt "Beijing subway line map, stations 天安门, 王府井, 东单, 建国门..."

# ✅ 通过（模型自己发明站名）
--prompt "Metro transit line map excerpt, 16:9, 12 stations on two intersecting lines,
transfer hub with double circle, each station labeled with 3-character Chinese
station names + 8pt grey pinyin"

# ✅ 英文 transliteration 也常通过
--prompt "Beijing subway map showing Tiananmen, Wangfujing, Dongdan stations..."
```

### 11. 中文 marker 编辑 prompt 触发 Stage 2 输出侧 classifier block

全中文 prompt + `替换 / 删除 / 改为` 这种 destructive 中文动词会让 Stage 2 classifier block 输出 `Stage 2 classifier error - blocking based on stage 1 assessment`，与内容合规无关。

**修复：用英文主导操作语义 + 中文 payload 内容**——英文写指令、中文作内容载体。

```
# ❌ 触发 Stage 2 classifier
红框中的主标题「AGI 已来」替换为「智能崛起」四个字，
保持完全相同的字体字号不变...

# ✅ Passes reliably:
Inside the marked red rectangular region, perform an in-place text replacement on
the existing Chinese headline: replace the four Chinese characters with a different
four-character Chinese headline. The new text is the characters 智能崛起.
Keep the same black bold sans-serif typeface, the same point size, the same weight,
the same center alignment, the same baseline. Outside the marked region nothing
changes. Erase all colored edit marks.
```

## 已知翻车场景（不要在这些场景依赖 Seedream Pro）

| 场景 | 为什么翻 | 建议替代 |
|---|---|---|
| 名人/公众人物肖像精确还原 | 训练数据里的名人会"混合脸" | 拍真人 / 找授权素材 |
| 数学公式、几何证明题答案 | 数字和符号位置关系错乱 | MathJax/LaTeX 渲染后合成 |
| 乐谱 / 简谱 | 音符结构会乱 | 制谱软件导出 |
| 象棋/围棋/国际象棋棋谱 | 棋子位置和行棋逻辑错 | 棋盘截图 |
| 密集表格/时刻表/地铁图 | 数字/文字密集会错字错位 | HTML/CSS 渲染后截图 |
| 连笔手写体/草书/医生处方 | 笔画结构不闭合 | 字体文件排印 |
| 长段正文（8 行以上） | 错字累积 | 出图后用 Canvas/PS 加字 |
| 工程三视图/机械制图 | 线条投影关系不严格 | CAD 导出 |
| 法律合同/证件类排版 | 规范性强，错字不可接受 | InDesign/Word 导出 |
| 像素级精确 UI 截图 | 控件间距/字号不可控 | 浏览器截图 |
| 瓶身/包装曲面小字号标签 | 弯曲表面文字必错/乱码 | 后期 PS 贴标或 3D 渲染 |
| 真实中文城市/地标/品牌名放 prompt | Stage 1 输入侧 `InputTextContentDetected` block | 用泛化占位描述或英文 transliteration |
| 全中文 marker 编辑 prompt（含"替换/删除/改为"） | Stage 2 输出侧 classifier block | 英文操作语义 + 中文 payload |
| 手机/9:16 画面里"美食/人物"内容 | 会自动脑补手机 UI 状态栏/按钮 | prompt 加"无 UI 元素、纯摄影画面"（见反模式 1） |
| 英文竖排大标题（杂志侧边） | 按中文竖排逻辑渲染，字母重叠错位 | 显式描述"每词一行水平从上到下"（见反模式 2） |
| 英文弧形字 >40 字符沿圆环排列 | 字母拥挤、末端字符挤压变形、字距塌缩 | 上/下弧总长 ≤35 字符；或分两段弧；末端字距显式说"均匀字距" |
| 超小中文标签（< 画面 6% 高度） | 约 20% 字符错/糊，在技术架构图里标签位置可能漂移（框外下方而不是框内） | 标签 ≥ 画面 6% 高度；标签短到 2-4 字；位置显式写"标签写在方框内正中央" |
| 密集周期性网格（元素周期表式 72+ tiles） | ~40% 标签乱码/错语言/重复/数字错乱；英文品牌名拼写大面积损坏（T5 周期表 72 tiles 只有 2/10 分） | 密度上限：横版 ≤20 tiles；超出后期 HTML/CSS 网格渲染再合成 |
| 金融仪表盘/表格（10+ 行同格式数字重复） | 千分位逗号稳定正确但中间 3-4 位数字会被随机生成（anchor-recency 效应）；股票代码字母→数字；月份缩写 Fer/Uer/Cer/Jar/Dar 系统性错误；涨跌箭头颜色错配 | 大 KPI tile（3 个以内）大字数字可靠；10+ 行表格数据不要靠 AI；月份全拼不用缩写 |
| 竖排英文大字（每行 1 词逐行堆叠，长词 ≥6 字母） | 长词（FASHION/REIMAGINED）在窄 rect 内被截断（FASHION→FASI）或溢出框外覆盖主体；字重不均 | 长词按音节强制拆行（FASH/ION、REIMAG/INED）；rect 宽度 ≥38% 画布；显式"严格限制在 x<38% 内不溢出" |
| 社交平台截图/手机 UI 录屏级复刻（朋友圈/推文/直播截图/App 首页）| 状态栏/头像/点赞栏/评论区元素能组织起来，但细节对不上（头像不像本人、点赞数格式错、控件位置漂移）— output is "visually similar to a screenshot" rather than pixel-accurate | Use Playwright to capture real screenshots; or accept Seedream producing a mockup that evokes the feel rather than a spec replica |
| 未指定视觉风格的信息图/网格卡片 | 模型默认偏浅色、浅蓝/莫兰迪配色、通用 PPT 风——若不指定风格锚点，8 格模型入门卡/AI 模型卡片等会出"企业内训 PPT"质感 | **公式 1 第一项"风格锚点"一定要写**：哪怕只加"编辑信息图质感 / Bloomberg data journalism / 复古印刷风"都能显著拉高完成度 |

## 社区验证有效的高级技巧

以下技巧来自中文社区（小红书、知乎、即刻、B站、微信公众号）沉淀，在 Seedream 5.0 Pro 上确实有效。

### 镜头/相机/焦段词汇（英文术语最稳）

摄影类画面不要只说"特写"或"近景"，给具体的镜头、焦段、相机型号，模型对这些摄影术语的训练非常足：

- **焦段/景别**：`85mm f/1.4`（人像虚化）、`100mm macro f/2.8`（产品/美妆微距）、`50mm f/1.8`（标准视角）、`35mm f/2`（环境人像）、`24mm f/8`（场景广角）、`f/8`（白底产品双灯深景深）
- **相机锚点**：`shot on Phase One IQ4 150MP`（高端商业中画幅）、`Hasselblad X2D`（中画幅质感）、`Arri Alexa Mini`（电影感）、`Leica M11 + 50mm Summilux`（纪实质感）、`Kodak Portra 400 film`（暖色胶片感）
- **光线术语**（英文原文嵌入）：`golden hour`、`blue hour`、`hard studio key light`、`softbox diffused light`、`rim light`、`subsurface scattering`（玉石/蜡烛/皮肤透光）、`volumetric light`（丁达尔光）、`caustics`（焦散光，水下/玻璃）

### 权重语法（谨慎使用）

Seedream 支持和早期英文模型类似的括号加权语法，但只在需要强化某个核心元素时使用，不要乱加：

- `(关键词:1.3)` 或 `关键词::1.3` —— 提升该元素 30% 的权重
- `[关键词:0.7]` —— 降低权重
- 权重值建议控制在 0.5–1.5 之间，超过 1.8 容易出 artifact
- 用法示例：`(朱砂红朱门:1.2)、金色祥云(次要:0.6)`

### 可靠字体族触发词（中英通用）

这些字体族名在 Seedream 训练集中有明确映射，描述文字时优先用它们，不要写"思源宋体"、"方正兰亭"、"Helvetica Neue"这种具体文件名（模型不认识）：

**中文：**
- 无衬线：`粗黑无衬线` / `现代黑体` / `简约几何无衬线`
- 衬线/宋体：`粗宋体` / `细宋体` / `仿宋`
- 书法：`手写毛笔字（带飞白）` / `行书` / `颜体楷书` / `瘦金体` / `魏碑` / `隶书` / `小楷` / `草书（仅单字）`
- 装饰：`现代海报字体` / `立体金边大字` / `圆体` / `可爱涂鸦字`
- 印章：`朱文印章` / `白文印章` / `篆刻印章`

**英文：**
- 无衬线：`geometric sans-serif (Futura-style)` / `Helvetica-style neo-grotesque` / `bold condensed sans-serif`
- 衬线：`elegant Bodoni-style serif`（Vogue 杂志风竖排大字） / `Times-style classic serif` / `slab-serif athletic block`
- 装饰：`cursive golden script`（花体）/ `retro comic sans bold` / `American vintage handwritten` / `vintage typewriter font`

**材质化文字（跨语种）：**
- `粗体`（bold 是跨语言通用的强度关键词，加了比不加准确率高 30-50%）
- `neon tube / 霓虹光管字`、`3D chrome liquid metal / 液态金属立体字`、`embroidery stitched / 刺绣字`、`foil-stamp golden glitter / 烫金大字`

### 中文社区特有的"无法翻译"触发词

这些词是中文社区在实操里沉淀出来的、直接用中文触发效果最好的"质感词"，不要硬翻英文：

- `VCD质感` —— 90 年代港产片/老录像带质感，颗粒感+色偏+复古氛围
- `丁达尔光` —— 体积光/耶稣光，比"volumetric light"更准确触发林间/窗缝光柱
- `飞白笔触` —— 毛笔飞白，比 "dry brush" 准
- `绢本设色` —— 宋画绢本工笔重彩质感
- `清冷破碎感` —— 新中式冷调人物写真，苍白皮肤+湿润眼眶+冷色补光+情绪感
- `新中式国风` / `赛博国风` / `新文人画` —— 这些是独立风格锚点，不是"新+中式+国风"的叠加
- `留白透气` —— 中式构图留白
- `国潮插画` / `宋代院体工笔` / `张大千泼墨` / `齐白石花鸟` / `吴冠中江南` / `八大山人简笔` / `敦煌壁画配色` / `非遗剪纸` / `木刻版画` —— 中式艺术风格锚点（比"中国画"具体得多）

### 平台关键词触发内部优化

以下平台关键词会让服务端自动套用经过优化的内部 preset，出图质量明显更贴平台调性：

- `淘宝详情页风格` / `optimized for Amazon product listing` —— 电商主图
- `小红书封面` —— 3:4 竖版 + 强文字标题感
- `App Store 截图风格` —— UI 截图+设备边框的营销图
- `Vogue 封面美学` / `Kinfolk 杂志风` / `National Geographic 摄影` —— 编辑风格
- `Dribbble 热门设计` —— 2D/3D 设计感 UI/illustration

### 三步迭代法（比一次写长 prompt 更稳）

1. **第一稿**：只写主体+风格+光线，不加细节词，出一张看基础调性对不对
2. **第二稿**：在第一稿基础上加具体材质、构图、色彩、小元素
3. **第三稿**：加精确文字、品牌、标签、装饰细节

**不要一开始就写 300 字的 mega-prompt**——主体错了后面全白搭。前两稿可以用 Lite 快跑（`--model lite`），定稿再切 Pro 加文字。

## 经典 Prompt 改写示例

| 原始 Prompt | Pro 优化版 |
|---|---|
| "水乡的图片" | "江南水乡诗意画卷，白墙黑瓦徽派古建筑沿小河而建，石拱桥横跨碧绿河面，乌篷船缓缓划过，岸边盛开粉色桃花，晨雾缭绕水面倒映天空，水墨画写意风格，浅灰青绿主色，2K，16:9 横版" |
| "AI 海报" | "极简科技海报，深靛蓝渐变背景，顶部居中白色粗无衬线大标题『AGI 已来』，下方一行小字副标题"The Future is Agentic"，中英字号视觉平衡，中部一束蓝色光束从画面底部向上扩散，光束中有微小的几何粒子漂浮，2K，3:4 竖版" |
| "一只猫在沙发上" | "室内场景编辑，米白色三人布艺沙发正对镜头，一只橘色虎斑猫蜷缩在沙发右侧靠垫上熟睡，阳光从左侧落地窗斜射进来在猫背上形成金色光斑，沙发扶手上搭着奶油色针织毯，背景是浅米色墙面与绿植，温暖午后自然光，家居杂志摄影风格，2K，4:3" |
| "科技博客封面" | "Tech blog cover, dark charcoal gradient background, large bold white sans-serif headline 'Seedream 5.0 Pro' upper-left, subtitle 'Chinese-native image generation arrives' in smaller light gray below, a stylized glowing blue brush-stroke icon in the lower-right corner, minimal editorial layout with generous negative space, 2K, 1792x1024, 16:9" |
