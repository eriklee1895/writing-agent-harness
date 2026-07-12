# Marker-Based Local Editing (Pro 深度参考)

Marker 编辑是 Seedream 5.0 Pro 最具差异化的能力——不用画 mask、不用导出 bbox JSON，**在参考图上画一个彩色矩形，用自然语言说"这里改成什么"，模型识别彩色方框、在框内改图、自动擦除方框痕迹**，一张图一次 API call 完成换字、换物、换材质、加/减元素、多区域同时改等以前必须 Photoshop 才能做的事。本 skill 的 `edit` 子命令通过 Pillow 自动完成画框、发图、追加擦除指令三步。

> 本文件是 SKILL.md "Marker-based local editing" 一节的深度参考。快速入门请看 SKILL.md 的 Example 6/7；**首次用 marker 务必先读 §2 协议 + §3 检查清单 + §5 翻车阈值**。

---

## 1. 为什么它是 Pro 的差异化能力

| 对比项 | 传统 mask/bbox API（MJ inpaint、DALL·E edit、SD inpaint） | Seedream marker edit |
|---|---|---|
| 输入 | 黑白 mask PNG / `[x,y,w,h]` bbox JSON / 涂抹画布 | 彩色矩形 + 自然语言描述 |
| 精度要求 | mask 必须精确覆盖目标边缘，1-2 px 误差就漏/出血 | 矩形粗略框住即可（裁剪到引脚外一点，模型仍会把引脚一起改色） |
| 多区域 | 多个独立 mask + 多段独立 prompt | 多个彩色矩形（红/蓝/绿/紫），一段 prompt 分颜色描述 |
| 框外保持 | 理论上 100% 保持但实际模型常重绘 | 框外像素保持率 9-10/10 |
| Marker 残留 | N/A | 模型自动擦除（全部 critique 里 NO_MARKER_LEFTOVER 都是 10/10） |
| 上手成本 | 需要 PS/Figma/专业涂抹工具 | 命令行 `--marker-rect X%,Y%,W%,H%` + 一句话 prompt |

Pro's marker editing reliably handles: headline/subtitle/label text swaps, product material/color changes, adding icons/decorative dots, removing icons/objects and restoring the background, simultaneous multi-region multi-color edits, and combined outpaint+marker canvas-extension edits. **Marker editing is validated on Pro; Lite is untested for this workflow.**

---

## 2. 工作协议（CLI 自动完成，你只需传参数）

`uv run scripts/seedream_image_gen.py edit` 的 marker 流程：

1. **Pillow 画框**：读取 `--reference-image`，按每个 `--marker-rect` 坐标在图上叠加一个半透明彩色矩形（fill alpha 默认 80，stroke 3px），保存为 `*-annotated.png` 到输出目录。
2. **自动追加清理指令**：在 prompt 末尾追加中文指令"擦除所有红/蓝/绿/…彩色方框标记，方框线条和填充不要出现在结果里"。可用 `--no-marker-cleanup-prompt` 禁用（不建议，除非你自己在 prompt 里写了清理）。
3. **发图**：把带框 annotated 图作为 image 引用发给 `/images/generations` 编辑接口（edit 与 generate 共用一个 endpoint，传 `--reference-image` 即自动走 edit 模态）。
4. **出图**：API 返回 PNG，模型已经在框内改图 + 自动擦除了方框。**务必先目测 `*-annotated.png` 确认方框位置再看结果**——框画错了结果必然错。

---

## 3. 语法速查

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image <INPUT.png> \
  --marker-rect "X%,Y%,W%,H%" [--marker-rect "X2%,Y2%,W2%,H2%" ...] \
  [--marker-color "#rrggbb"] \
  [--marker-alpha 0-255] \
  [--marker-stroke <px>] \
  [--no-marker-cleanup-prompt] \
  --prompt "<分颜色描述改动>"
```

### 参数说明

| 参数 | 默认 | 说明 |
|---|---|---|
| `--marker-rect` | 必填，可重复 | 矩形坐标，支持两种格式：**百分比** `10%,15%,60%,20%`（推荐，自适应分辨率）；**像素** `100,150,800,300`（固定分辨率图用）。坐标是 `top-left-X, top-left-Y, width, height`，不是 `x1,y1,x2,y2`。 |
| `--marker-color` | `#ff0000` 红 | 矩形颜色。**可重复**，与 `--marker-rect` 一一对应实现多区域多色编辑：每次 `--marker-rect` 后紧跟一个 `--marker-color` 指定该框颜色（红 `#ff0000` / 蓝 `#0000ff` / 绿 `#00cc00` / 紫 `#9333ea`），prompt 里按颜色引用（"红框改 X；蓝框改 Y"）。如果颜色数少于框数，所有框用最后一个颜色。只传一个颜色或不传时，所有框默认红色。`*-annotated.png` 预览会正确显示每个框的独立颜色。 |
| `--marker-alpha` | `80` | 填充透明度 0-255。80 约为 30% 不透明，够模型识别又不会过度遮挡框内内容。**视觉陷阱：α=80 的红框叠加在浅黄/米色底色（如柠檬、白瓷、肤色）上时，下面的颜色会和红色混出"橘子/陶土橙"的效果，导致人眼看 annotated 预览误以为原图已经被替换了。**验证方法：用 Pillow 读 annotated 文件中心像素 RGB——如果底色是黄色（R>G, B≈0）但显示是橙色（R>>G, B 低），那是红框叠加造成的视觉混色，不是模型输出了橘子。规避：① 把 `--marker-alpha` 降到 40-50 让底色更可读；② 在浅黄/米色背景上改用蓝/绿 marker（如 `--marker-color "#0066ff"`）让叠加后视觉对比明显；③ 信任 PNG 实际像素，不要只看屏幕压缩渲染。 |
| `--marker-stroke` | `3` | 描边宽度（像素）。 |
| `--no-marker-cleanup-prompt` | off | 关闭自动追加的"擦除方框"指令。仅当你自己在 prompt 里写了明确清理指令时使用。 |
| `--outpaint <dir:pixels>` | off | 与 marker 可共存，用于扩图 + 局部改图组合（见 Recipe 7）。 |

### 输出文件

- `*-annotated.png`：画完框的预览图，**必须先看这张确认位置**。
- `*.png`：最终编辑结果（方框已擦除）。
- `*.json`：元数据（含实际发送的 prompt、marker_rects、outpaint 配置）。

---

## 4. 必看检查清单（每次用 marker 前过一遍）

1. **先看 `*-annotated.png` 再评估结果**。8%×8% 的小框容易只框住物体局部没框住主体——看 annotated 一眼就能发现框画歪了。
2. **框必须完全包围目标物体，四周留 5-10% padding**。图标/小物体推荐最小 15%×15%。不要紧贴物体边缘。
3. **不要画 >70% 画布的巨框**。用 5%,5%,90%,90%（留 5% 边距）改整体色调，结果模型按硬边界裁切，中央变成贴上去的色块而不是滤镜。要改整体色调直接 t2i 重出或在 prompt 里说"全图统一冷色调"不要画大框。
4. **PRESERVE 要和 CHANGE 写得一样仔细**。每一段红框/蓝框 prompt 都要包含两部分："框内 A 改成 B" + "保持 C/D/E/F 不变"。只说改成什么不说保持什么，模型会自由发挥（副标题"追加"而不是"替换"，就是没说"移除原文字"）。
5. **框外不动要显式重申**。写一句"框外像素完全保持原样"。本 skill 自动追加的清理指令已有类似意思，但关键任务里再写一遍更稳。
6. **文字替换必须显式指定字体/字号/颜色/对齐**。写"替换为『XXX』，保持原有粗黑无衬线字体、字号、居中、黑色不变"，不要只说"替换为 XXX"。
7. **多色多框必须在 prompt 里按颜色分别说明**。"红框改 X；蓝框改 Y；绿框加 Z；其他区域不变"——颜色名用中文（红框/蓝框/绿框）。
8. **文本替换失败时的重试策略**：如果模型追加文字而不是替换，把 prompt 改成"红框内**删除原有灰色英文副标题**'The Future is Agentic'，**替换为**'The Rise of Autonomous Agents'，同一位置同字体同色同字号"，明确"删除 + 替换"两个动作。

---

## 5. 翻车阈值（critique 里测得的具体数字，必记）

| 阈值 | 失败表现 | 规避 |
|---|---|---|
| **矩形 <8% 画布面积** | 模型无视框内目标，变成"在框处加点东西"（小框改芯片，模型在框顶加了一颗爱心，芯片本身没动） | 最小 15%×15% 框小物体；周围必须留 padding |
| **矩形 >70% 画布面积** | 模型按硬边界裁切，出现明显"贴块" seam，像打了块补丁而不是整体滤镜 | 整体改色不加框，直接走 t2i 或无框 edit |
| **矩形出血到框外 5-10%** | 框紧邻物体时，模型会向框外延伸 5-10 px 完成 inpaint（移除芯片时底部引脚超出红框 5-10 px 也被一起擦掉）——这是良性溢出，结果反而更干净 | 要完全保留的元素离框 ≥10% 画布距离 |
| **链式编辑（同一图连续 edit ≥2 轮）** | 每轮都有 5-10% 轻微漂移（颜色微偏、位置微移、纹理微糊），3 轮后漂移可感 | 能一次改完就不要链；必须链式时每轮只改一个最小区域，且每轮都把"保持 X/Y/Z 不变"写全；2 轮以上建议回到 t2i 重出 |
| **反射性表面（金属/玻璃/镜面）** | 只改物体颜色不改反射环境，金属高光/反射里会残留原色或者环境不匹配（玫瑰金耳机内盖变成高光镜面，比原哑光黑反射强） | 加"柔和环境反射（模糊白/环境光），无反射具体人像或文字，保持原有光线方向" |
| **多色框间距 <3% 画布** | 两个框太近时会合并成一个区域，或互相 bleed | 框与框之间留 ≥3% 间距 |
| **文字替换不写字体/字号/颜色** | 新文字可能变成新的字号/字体/颜色，看起来像贴上去的；或者追加而不是替换 | 逐字写"保持原字体/字号/颜色/对齐" |
| **英文长单词（≥6 字母）挤在窄 rect** | 单词被截断（FASHION 被裁成 FASI；REIMAGINED 溢出框外盖到人物头发上） | 长单词主动换行拆段（"FASH / ION" 分两行）或加宽 rect |
| **Hex 色值精度** | 指定 `#dc2626` 深绯红，模型渲染成 `#ef4444` 亮红偏暖；指定 `#ea580c` 深陶土橙，渲染成 `#f97316` 亮橙 | 色值是软引导不是硬校准，接受 ±1 档色偏；要精确色后期 PS 调 |

---

## 6. 详细分步 Recipe（含结果解读）

下面两个 Recipe 是 marker 编辑最常用的两类场景（标题换字、物体材质替换+加元素）的完整分步范例——命令、prompt、和逐条结果解读齐全。其它 Recipe 1-8 见 SKILL.md 和后续小节。

### Recipe 1：海报大标题替换（保字体保字号保颜色）

**场景**：把米色海报上的中文主标题"深秋来信"换成"立夏物语"，副标题保留。

**步骤**：

| 步骤 | 命令 |
|---|---|
| 1. 出 base 海报 | `uv run scripts/seedream_image_gen.py generate --portrait --no-negative-prompt --prompt "米色亚麻纸张背景的杂志封面海报 3:4 竖版，顶部 1/4 处有黑色粗无衬线中文主标题「深秋来信」居中，副标题灰色衬线英文「Letters from late autumn」..."` |
| 2. 框主标题 | `--marker-rect "10%,12%,80%,18%"` |
| 3. Marker edit | `uv run scripts/seedream_image_gen.py edit --reference-image poster-base.png --marker-rect "10%,12%,80%,18%" --prompt "红框内：原黑色粗无衬线中文主标题「深秋来信」四个字删除，替换为「立夏物语」四个字，保持原有粗黑无衬线字体、字号大小、黑色、居中对齐、顶部位置不变；下方灰色衬线英文副标题「Letters from late autumn」完全保持不变（即使部分在红框内也不改）；红框外的米色亚麻纸张背景、左下右下留白、整体光线完全保持原样；红框标记擦除不要出现在结果中"` |

**结果解读**：
- ✅ 主标题"深秋来信" → "立夏物语" 替换成功，**字体粗黑、字号大小、黑色、居中对齐、顶部位置完全一致**
- ✅ 副标题"Letters from late autumn" 即使部分坐标落在红框垂直范围内，**也被正确保留**（这是 §4 第 4 条 PRESERVE 写到位才生效的）
- ✅ 红框外所有像素（信封、枫叶、印章、光线、纹理）零变化
- ✅ 红框标记擦除干净，无残留

这就是 Marker Edit 最常用的"标题换字"场景，**8.5-9/10 通过率**。

---

### Recipe 2：物体材质/颜色替换 + 同一框内加元素

**场景**：把米白色客厅里深灰亚麻布艺沙发替换为墨绿色丝绒 + 加一只睡着的橘猫。marker 框覆盖沙发区域 `5%,35%,55%,55%`（覆盖沙发+靠背+扶手+抱枕，留 5% padding）。

**Prompt（一次 edit 同时换材质 + 加元素）**：

```text
红框内：原三人位深灰色亚麻布艺沙发整体替换为墨绿色丝绒三人位沙发，
丝绒有柔和反光、绒毛清晰、深墨绿 #14532d 色调，沙发形状大小位置不变，
抱枕替换为同色系深绿丝绒方枕一只、奶白色棉麻方枕一只；
沙发上右侧增加一只成年橘色短毛猫，蜷缩在扶手上睡觉，猫毛柔软写实；
红框外的茶几、咖啡杯、书本、地毯、窗户光、绿萝完全保持原样不变；
红框标记擦除。
```

**结果解读**：
- ✅ 沙发从深灰亚麻 → 墨绿丝绒，**反光质感、绒毛纹理、绿色调全部正确**
- ✅ 抱枕从奶白单只 → 同款深绿丝绒方枕 + 奶白方枕组合
- ✅ 扶手上**新增**一只睡着的橘猫，光线方向与原图一致
- ✅ 红框外茶几、咖啡杯、书本、地毯、窗帘、绿萝、窗外光线**零变化**
- ✅ 沙发腿、木扶手、扶手末端几何结构都保留

**为什么这一例能成功**：
1. 框 5%,35%,55%,55% 大小合适（覆盖沙发+靠背+扶手+抱枕，留 5% padding）
2. 框外元素（咖啡、书、窗帘、绿萝）**显式列名**说"完全保持原样"
3. 材质描述包含颜色 hex + 物理质感（丝绒 + 柔和反光 + 绒毛清晰）

---

## 7. 其它 Recipe 速查

> Recipe 1/2 有完整分步解读；其余 6 个 Recipe 见 SKILL.md Examples 6/7 或下方文字版。

### Recipe 3：在空白区域加装饰元素

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image poster.png \
  --marker-rect "5%,78%,28%,15%" \
  --prompt "红框内左下角原本留白的米色纸张区域，添加一枚小号橙色 #ea580c 圆形装饰点（直径占画面高度 2%）+ 橙色无衬线小字 tagline 'AI Agent Era'，圆点在左、文字在右水平排列；红框外标题、副标题、米色纸张背景完全保持原样；红框标记擦除。"
```

要点：尺寸必须用百分比（"直径占画面高度 2%"），不要说"小一点/大一点"。

### Recipe 4：移除物体 + 还原背景

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image poster.png \
  --marker-rect "72%,68%,22%,22%" \
  --prompt "红框内的蓝色芯片图标从画面中完全移除，该区域还原为与周围一致的米色亚麻纸张质感背景，纹理自然延续、无模糊色块、无接缝；红框标记擦除。"
```

要点：移除物体时框要覆盖目标 + 四周 5-10% padding；一定要说"还原为 XX 背景"。

### Recipe 5：多区域多色同时改

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image poster.png \
  --marker-rect "15%,18%,70%,20%" --marker-color "#ff0000" \
  --marker-rect "72%,68%,22%,22%" --marker-color "#0000ff" \
  --marker-rect "5%,78%,28%,15%" --marker-color "#00cc00" \
  --prompt "红框（顶部）：主标题'AGI 已来'替换为'未来已至'，保持字体字号位置颜色不变。
蓝框（右下）：蓝色芯片图标改为紫色 #9333ea 版本，形状大小位置不变。
绿框（左下）：在留白区域加一枚小号绿色圆形装饰点 + 绿色小字'v5.0'。
三个框的改动互相独立，各框内改各自的，不跨框 bleed；
框外像素和米色纸张背景完全保持原样；
红/蓝/绿所有彩色标记框都擦除不要出现在结果中。"
```

要点：多框数量建议 ≤4 个；框越多指令冲突概率越高。

### Recipe 6：链式编辑 + drift 警告

链式编辑（对同一张图连续 edit 多轮）能做但有累积漂移风险。能合并到一轮多框改完（Recipe 5）就不要链。超过 2 轮建议回到 t2i 重出一张干净版本。

```bash
# 轮 1
uv run scripts/seedream_image_gen.py edit \
  --reference-image v0.png --marker-rect "15%,18%,70%,20%" \
  --prompt "红框主标题替换为'未来已至'，保持字体字号黑色居中不变；其他所有像素不变；擦除红框。" \
  --out v1.png --force

# 轮 2：在 v1 基础上改芯片颜色
uv run scripts/seedream_image_gen.py edit \
  --reference-image v1.png --marker-rect "72%,68%,22%,22%" \
  --prompt "红框芯片图标颜色改为紫色 #9333ea，形状大小位置不变；主标题'未来已至'（已是新标题！）和其他背景像素完全保持不变；擦除红框。" \
  --out v2.png --force
```

注意：每轮 prompt 里必须写当前正确状态（轮 2 里主标题已经是"未来已至"不是"AGI 已来"），不要沿用老 prompt。

### Recipe 7：Outpaint 扩图 + Marker 改图组合

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image poster-cn.png \
  --outpaint left:500 \
  --size 1792x1024 \
  --prompt "将这张 3:4 竖版海报向左扩展约 30% 到 1792x1024 16:9 横版，新扩展的左侧区域延续原图的米色亚麻纸张背景，在左侧新区域添加竖排毛笔字'新智能'三个中文字（深色墨汁、中式书法风格、字号中等）；原有右侧海报区域保持 100% 原样不缩放不裁剪。"
```

注意：`--outpaint left:500 --size 1792x1024` 在竖版原图上会同时缩放原图高度到 1024，原图顶部/底部留白会被裁掉。如果需要原图 100% 不裁切，用 Pillow 手工扩画布再无框 edit 填充。

### Recipe 8：照片上加竖排英文大字（高难度，必拆词）

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image magazine-portrait.png \
  --marker-rect "0%,5%,38%,90%" \
  --prompt "红框内左侧留白区域添加大号白色 Bodoni-style serif 英文标题，严格以下结构：
第1行 FASH  第2行 ION  第3行 REIMAG  第4行 INED  第5行 2026  第6行 EDITION
共 6 行水平左对齐、白色 Bodoni 高对比衬线、字号占红框宽度约 80%；
所有文字严格限制在红框内（x<38%），绝对不能溢出到右侧人物头发/脸部/身体上；
右侧肖像和光线完全保持不变；红框标记擦除。"
```

关键防御：长单词必须主动拆段（FASH-ION、REIMAG-INED），让每行 ≤5 字母；红框宽度 ≥38% 给 10 字母单词留空间。

### Recipe 9：精准局部换色 + 五官特征改（9.5/10）

单眼虹膜变色（heterochromia 效果）——精度极高，能只改一只眼睛，另一只眼睛完全不动：

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image portrait.png \
  --marker-rect "20%,38%,25%,12%" \
  --prompt "Inside the marked red rectangular region covering the left eye (viewer's left),
change the iris color from dark brown to a warm hazel-green (hex #6B8E4E), keep the same
eye shape, same eyelid, same eyelashes, same catchlight position, natural realistic iris
texture with color variation. Outside the marked region, keep the entire face completely
unchanged including the right eye which stays dark brown, same skin, same hair, same
lighting, same background. Erase all colored edit marks."
```

**关键**：显式指定"viewer's left/right"避免左右混淆；显式说另一只眼睛"stays [原颜色]"防止两眼都被改。同样模式适用于唇色（hex 精准度 ±1 shade，见 Recipe 1 附近说明）、单侧腮红、单个痣的增减。

### Recipe 10：删除孤立物体 (9.5/10 for replaceable objects in daytime matte scenes)

**Daytime + matte-surface busy scenes** (street/parking/market) erase isolated objects (cars/bicycles/stall props) reliably at 9-9.5/10 when the object is replaceable/interchangeable:

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image busy-street.png \
  --marker-rect "35%,55%,15%,30%" \
  --prompt "Inside the marked red rectangular region, remove the blue SUV completely.
Restore the empty parking space naturally: continue the same cobblestone pavement
pattern where the car was, matching the lighting and texture, add a natural soft
shadow gap between the white hatchback and silver wagon that remain parked on
either side. The white hatchback (to the left) and silver wagon (to the right)
must remain exactly in place, untouched, unmoved. Outside the marked region, keep
everything else completely unchanged. Erase all colored edit marks."
```

**Key levers**: (1) Explicitly say "restore X naturally, continuing the Y pattern" to give the model a clear fill target; (2) **explicitly name adjacent objects that must remain** ("white hatchback... silver wagon... must remain exactly in place") — the core defense against collateral deletion; (3) daytime matte surfaces (cobblestone/asphalt/concrete) are far easier than nighttime reflective surfaces (wet asphalt + neon).

**Counter-example (same image, equally well-formed marker+prompt, yet fails)**: on the same street scene, attempting to delete a black bicycle leaning against a lamppost (midground, in the same composition) with an equally precise marker and a prompt that explicitly says "remove...restore cobblestone naturally...lamppost must remain exactly in place" — **the bicycle remains untouched; the edit does not take effect at all** (0/10; annotated.png confirms the marker position is accurate; the failure is not a misplaced box).

**Scene judgment (three axes)**:
- Busy but **daytime/matte/non-reflective** scenes → isolated-object deletion is reliable at 9+/10, **but only when the object is replaceable, not a compositional focal point** (one car in a row of similar vehicles — high visual interchangeability).
- Within that same daytime matte scene, **compositional anchor / visual-focal-point objects** (a bicycle leaning on a lamppost, center-depth, high-contrast silhouette) → **still cannot be removed**, even with a best-practice marker and prompt. This is a broader instance of the same failure mechanism as hero-object/primary-light-source failures — not limited to light sources, any isolated object that serves as a visual anchor can trigger the same resistance prior.
- **Nighttime + wet reflective ground + neon signs** → remains a high-failure zone at 1-4/10.

**Practical test**: before deleting, ask "is this object interchangeable with others of its kind in the scene, such that removing it won't leave a hole or break the composition?" (one car in a row of cars — yes) versus "is this object the visual anchor, such that removing it makes the scene feel empty or missing its subject?" (the bicycle leaning on the lamppost — no). The former deletes reliably; the latter is unlikely to delete, so regenerate the whole scene without the object (t2i) instead of retrying the marker.

### Recipe 11：坐标精准数学推导续写（9.5/10）

在手写数学题下方指定行数续写推导步骤，保持笔迹/笔色/位置一致：

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image math-worksheet.png \
  --marker-rect "17%,42%,50%,15%" \
  --prompt "Inside the marked red rectangular region (on the first faint ruled line
below the equation), add the next handwritten step of the derivation, matching the
EXACT same dark blue ballpoint pen style, same handwriting slant and size as the
equation above: factor the quadratic as '(x - 2)(x - 3) = 0'. Write it left-aligned
starting at the same x-position as the equation above. Do not modify the original
equation at the top — it must stay pixel-identical. Erase all colored edit marks."
```

**关键**：(1) marker 框住"下一行"而不是整页，给出精确写入位置；(2) 显式给出目标公式内容（不要指望模型自己推导——它照抄你给的答案，不会算错但也不会主动验证数学正确性，**你需要自己算对再喂给它**）；(3) "matching the EXACT same pen style/slant/size" 触发风格延续。**局限：这是"手写风格续写"不是"数学求解"——模型不会主动计算，只会按你写的内容渲染成手写体。复杂计算仍需你自己算，模型只负责视觉呈现。**

### Recipe 12：多图人物抠像 + 统一光影合成（8.5-9/10）

从两张独立参考图各提取一个人物，合成到统一场景+统一光影：

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image personA.png \
  --reference-image personB.png \
  --wide \
  --prompt "Extract the man from the FIRST reference image (Black, short fade
haircut, trimmed beard, navy sweater) and the woman from the SECOND reference
image (White, long strawberry-blonde wavy hair, mustard cardigan). Composite
them together standing side by side as two coworkers in a shared scene: a
bright modern office lounge with a large window letting in warm afternoon
sunlight from the right side. Both people must be lit consistently by the same
warm afternoon sun — matching shadow direction, matching warm color temperature
on skin and clothing, matching contrast level. Preserve each person's exact
facial identity, hair, and clothing from their respective reference image."
```

**关键**：(1) "Extract the X from the FIRST/SECOND reference image"显式绑定身份来源，防止两人特征互相污染；(2) 显式描述目标统一光源方向+色温+对比度，这是让两个原本在不同棚拍光线下拍摄的人"看起来在同一场景"的核心指令；(3) 该 recipe 是"多图融合抠像"目标的直接实现——2 张参考图上限内工作良好，见 prompt-engineering.md 公式 6 的 refs 数量甜点（2-3 张最佳）。

---

## 8. 通用 Edit Prompt 模板

```
[红/蓝/绿/…]框内[位置]的[原对象描述]，
[替换/添加/移除/改色为：新对象+材质+颜色+光影描述]；
保持[字体/字号/颜色/对齐/透视/材质/光影方向/阴影形状/接触点]与原图一致；
[其他框（如有）按颜色分别说明]
框外所有像素（[具体关键元素名]）完全保持原样不变；
所有[红/蓝/绿]彩色方框标记擦除，不出现在最终结果中。
```

## 9. API 层真相:没有 marker 字段,只有"图+文字"

> ⚠️ **Important**: The Seedream API does **not** accept a structured `marker.rectangle` coordinate field. The marker rectangle is a visual illusion produced entirely client-side by the CLI.

CLI 实际发给 `/images/generations` 的 body 是这样的:

```json
POST https://ark.cn-beijing.volces.com/api/v3/images/generations
{
  "model": "doubao-seedream-5-0-pro-260628",
  "image": ["data:image/png;base64,iVBORw0...（带红框的 annotated PNG）"],
  "prompt": "红框内：把原本的 medium rare 粉棕色切开的和牛牛排替换为...\n\n图中彩色方框/圆圈/涂写是我手工标出的编辑区域标记，请严格按上面的描述修改标记区域内的内容，标记区域之外的像素尽量保持不变，完成后清除所有彩色标记线条与填充。",
  "size": "2K",
  "output_format": "png",
  "negative_prompt": "模糊, 低质量, 水印, 变形, 多余肢体"
}
```

**没有** `marker.rectangle` / `mask` / `bbox` 任何坐标字段。CLI 做的全部事情是:

1. Pillow 在参考图上画半透明红色矩形(alpha=80,stroke=3)
2. 在 prompt 末尾追加中文"擦除标记"指令
3. 把带框图 base64 编码后作为 `image` 字段上传

模型靠**视觉识别红框 + 阅读 prompt 文字**理解编辑意图。坐标信息从未离开客户端。

| 字段 | 是否发到 API | 谁生成 |
|---|---|---|
| `image` (带红框的 PNG) | ✅ 是 | CLI 用 Pillow 画框 + base64 编码 |
| `prompt` (含"红框内..." + "擦除标记") | ✅ 是 | 用户原文 + CLI 自动追加清理后缀 |
| `--marker-rect X%,Y%,W%,H%` | ❌ 否 | 只在本地解析,从未发出去 |
| `marker_rects` (JSON 元数据) | ❌ 否 | CLI 写到本地 .json 日志 |

**为什么这种设计更巧妙**:API 只暴露普通的多模态接口(image + text),把所有"局部编辑"的复杂度压在模型视觉能力上。用户不用处理坐标系统、mask 边缘、抗锯齿;模型用眼睛读图、用语言读 prompt,组合起来做局部编辑。这是 Seedream 模型层训练出来的硬能力,不是 API 工程巧思。

---

## 10. 排错法则 + Marker 尺寸速查卡

90% 的 marker 失败都不是模型问题，而是**框画错了位置或大小**。每次 edit 跑完先打开 `*-annotated.png`：
- 框是否完整包围了要改的目标物体（四周有 5-10% padding）？
- 框是否不小心切到了要保留的元素（比如标题框切到了副标题）？
- 多色框的位置/大小是否合理？
- 框与框之间是否留了 ≥3% 间距？

确认 annotated 没问题再看最终出图。8% 小框和 90% 巨框的失败，看一眼 annotated 就能避免白烧一次 API。

### 附：Marker 尺寸速查卡（以 1536×2048 3:4 竖版为参考）

| 框尺寸占画布 | 典型像素 | 适合场景 | 风险等级 |
|---|---|---|---|
| <8%（如 8%×8%） | ≈123×164 px | 不够用（框不住主体） | ❌ 避免 |
| 10-15% | ≈150×200 px | 只能加单个小点/小图标 | ⚠️ 勉强，建议 ≥15% |
| 15-25% | ≈230-380 px | 图标换色、小标签替换、加 tagline | ✅ 甜点下半区 |
| 25-50% | ≈400-770 px | 标题替换、产品换材质、加装饰块 | ✅ 甜点区（成功率 8-9/10） |
| 50-70% | ≈770-1075 px | 大块区域改色、大幅面重绘 | ⚠️ 注意硬边界 seam |
| 70-90% | >1075 px | 接近全画布改色/改风格 | ❌ 出"贴块"seam |
| 90-100%（0%,0%,100%,100%） | 全画布 | 等同于无框 edit / 重绘 | ✅ 全覆盖时不留 seam |

1792×1024（16:9 横版）上百分比阈值一致；1024×1024（1:1 方图）按同样百分比换算即可。核心经验：**框宁可略大（留 5-10% padding）不要小，宁可一个框把目标完全包住不要切边，但框不要大到 70% 以上（除非是 100% 全画布）。**