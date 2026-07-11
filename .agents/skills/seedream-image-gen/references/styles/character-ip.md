# Seedream 5.0 Pro — Character IP Consistency Recipe

> Works on `doubao-seedream-5-0-pro-260628`; a single 1:1 character sheet reliably holds a stylized IP across kitchen/debug/standup/beach scenes with accessories, lighting, and clothing changing as prompted.

---

## 1. TL;DR

Character consistency works with **a single front/three-quarter reference image at 1:1**, and every scene prompt **opens with a physical-feature recap in parentheses** before describing the scene. The CLI defaults `optimize_prompt` to `"standard"` (prompt optimization is always on unless explicitly changed); prompt optimization may slightly soften identity for stylized IPs, but a strong physical-feature recap in the prompt anchors identity well enough for production use. For strictest identity hold, edit mode with `--reference-image` (marker edit on an existing character scene) is more reliable than generate mode.

No IP-Adapter, no LoRA, no multi-angle character sheet needed. One 1024×1024 ref is enough for stylized 3D / illustration IPs.

---

## 2. Step 1 — 生成角色设定图 (character sheet)

```bash
uv run scripts/seedream_image_gen.py generate --square \
  --prompt "角色设定图, 正方形1:1, 纯白摄影棚背景,
一个{风格描述, e.g. Q版紫色小章鱼拟人IP形象}:
{身体形态}: 圆头、八只触手、两只大眼睛戴黑粗框眼镜,
{持物/动作}: 其中两只触手抱着一台银色MacBook笔记本电脑、一只触手举着一杯咖啡、一只触手比耶,
{材质/颜色}: 皮肤是亮紫色带少许粉色腮红、触手底部有浅蓝色渐变吸盘,
{风格/光线}: 3D Pixar/Blender风格、柔和天光棚拍光、材质是略带光泽的硅胶PVC质感,
{表情}: 表情友好开心,
{构图}: 身体居中占画面60%、完整全身、纯色白底不要任何其他元素,
作为角色参考图使用"
```

Key requirements for the ref sheet:
- **1:1 square** (`--square` = 1024×1024 on Pro)
- **Pure white / seamless studio background** — no scene elements, no props the IP shouldn't carry everywhere
- **Front or three-quarter view, full body**
- **Verbose physical enumeration** (colors, materials, accessories, anatomy count like "八只触手") — this becomes the source of truth
- **Style explicitly stated** (3D Pixar/Blender, clay, PVC, watercolor storybook, anime, etc.)

Output: `character-ref.png` — this is your IP anchor.

If you don't like the first one, regenerate with `--n 4` and pick the best; this ref will be reused across all scenes, so invest 1-2 iterations getting it right.

---

## 3. Step 2 — 生成场景图 (scene generations)

For each new scene, pass the ref as `--reference-image` and use this prompt template:

```bash
uv run scripts/seedream_image_gen.py generate {--phone|--portrait|--square|--wide} \
  --reference-image character-ref.png \
  --prompt "延续参考图中的{角色称呼}形象（{physical-feature recap, 逐字重复关键识别特征}）：
{具体场景描述，包括：位置、服装、动作、每只触手/手在干什么、周围环境、光线、色调、氛围},
{风格，与ref一致，如3D Pixar风格}"
```

**The parenthetical physical-feature recap is non-negotiable.** Copy the core identifiers from the ref prompt:
```
延续参考图中的紫色Q版戴眼镜小章鱼程序员形象（紫色身体、粉色腮红、八只触手、黑粗框眼镜、触手末端蓝色吸盘）：
```

This does three things:
1. Reminds the model which visual attributes are identity-defining (don't drift these)
2. Lets you specify deliberate identity changes in the scene (e.g. "戴着墨镜" overrides black-frame glasses for a beach scene; the recap still anchors everything else)
3. Supplies the anchoring description explicitly; prompt optimization (`standard` mode) rewrites prompts and a strong recap compensates for any softening of identity

### Scene-specific sizing

| Scene type | Size flag | Resolution |
|---|---|---|
| Social avatar / product photo | `--square` | 1024×1024 |
| 3:4 poster / magazine cover scene | `--portrait` | 1536×2048 |
| 9:16 phone/Stories scene | `--phone` | 1152×2048 |
| 16:9 wide scene / landscape | `--landscape` | 2048×1152 |

### Scene prompt structure

Good scene prompts follow this order:
1. Identity anchor (recap)
2. **Wardrobe change** (if any): "穿着格子睡衣" / "戴着墨镜、穿花衬衫"
3. **Location**: "坐在厨房餐桌前" / "在沙滩椅上"
4. **Per-limb action breakdown** (critical for multi-tentacle/hand characters): "一只触手拿着叉子吃吐司煎蛋早餐，一只触手翻杂志，一只触手端牛奶杯"
5. **Environment details**: "桌上有黄油碟、玻璃杯牛奶、窗外晨光、瓷砖墙面"
6. **Lighting + color**: "暖色调，柔和晨光从左侧窗户照进来"
7. **Style coda**: "3D Pixar风格"

### Example scene prompts (tested)

Kitchen morning:
```
延续参考图中的紫色Q版戴眼镜小章鱼程序员形象（紫色身体、粉色腮红、八只触手、黑粗框眼镜、触手末端蓝色吸盘）：
清晨场景，小章鱼穿着格子睡衣坐在厨房餐桌前，一只触手拿着叉子吃吐司煎蛋早餐，一只触手端着牛奶杯，一只触手翻看杂志，桌上有黄油碟和一小盆绿植，窗外是柔和晨光，暖色调，3D Pixar风格
```

Late-night debug:
```
延续参考图中的紫色Q版戴眼镜小章鱼程序员形象（紫色身体、粉色腮红、八只触手、黑粗框眼镜、触手末端蓝色吸盘）：
深夜debug场景，小章鱼坐在电脑桌前四只触手同时敲击四把不同的键盘（笔记本+外接键盘+iPad+手机），触手飞舞，周围环绕飞舞的bug图标和红色错误提示框，屏幕冷蓝色光照在脸上，戏剧化照明，3D Pixar风格
```

Beach vacation (identity override: sunglasses):
```
延续参考图中的紫色Q版小章鱼程序员形象（紫色身体、粉色腮红、八只触手、触手末端蓝色吸盘）：
周五下班后的场景，小章鱼戴着墨镜坐在沙滩椅上，一只触手举着鸡尾酒杯（带菠萝片和小伞），一只触手比耶，一只触手玩Switch，一只触手举着手机自拍，背景是金色夕阳下的海滩和椰子树，温暖金色夕阳逆光，度假氛围，3D Pixar风格
```

Note the beach version omits "黑粗框眼镜" from the recap and adds "戴着墨镜" — deliberate identity override works when you remove the overridden feature from the recap list.

---

## 4. Do / Don't

### Do
- ✅ Use `--reference-image` pointing at your original character sheet (1:1, white bg)
- ✅ Start EVERY scene prompt with the identity recap parenthetical
- ✅ Describe per-limb actions explicitly ("一只触手X，一只触手Y") if your character has many appendages
- ✅ Specify wardrobe/hair/accessory changes IN the scene prompt (they override the ref)
- ✅ Match lighting to the scene (morning warm, screen blue, sunset golden) — the model will follow
- ✅ Accept that pose/tentacle-count can flex slightly (tentacles can hide behind body, that's fine)
- ✅ Re-run 2-3 times if the first scene has identity drift; consistency is probabilistic, not deterministic

### Don't
- ❌ Don't skip the physical-feature recap — without it, identity drifts ~30% of the time (color shifts, accessory loss)
- ❌ Don't send multiple different costume/angle refs unless you want fusion; a single front-three-quarter ref is most reliable
- ❌ Don't expect perfect pixel-identical tentacle/hand count across scenes — count can flex ±2 when the scene requires interacting with many objects
- ❌ Don't change art style mid-series (e.g. one scene 3D Pixar, next watercolor) without regenerating the ref; style is identity
- ❌ Don't use `--n > 1` for character scenes — concurrent generations share the same body but diverge on pose/environment; generate one at a time and iterate

---

## 5. Character-in-scene fusion (ref character + ref background)

For placing the IP into an existing scene photo (vs generating a new scene from text), use TWO `--reference-image` passes:

```bash
uv run scripts/seedream_image_gen.py generate --landscape \
  --reference-image character-ref.png \
  --reference-image living-room-photo.png \
  --prompt "第一张参考图中的紫色Q版小章鱼（紫色身体、粉色腮红、八只触手、黑粗框眼镜、蓝色吸盘）放到第二张参考图的客厅场景里：让小章鱼坐在沙发上，一只触手捧咖啡杯，一只触手翻书，一只触手摸旁边熟睡的金毛幼犬；场景的家具位置、灯光、色调与第二张参考图一致；3D Pixar风格渲染的小章鱼与真实摄影风格的场景融合"
```

The model will:
- Compose the subject (first ref) into the scene (second ref) with coherent placement
- Invent props that "should" exist given the prompt (e.g. if you say "摸着旁边熟睡的金毛幼犬" but the photo has no dog, the model will add one coherently)
- Match lighting direction if specified
- Make small position adjustments (e.g. move a vase) to make room for the character

Works well when the subject is ~20-40% of the frame. Larger subjects can overpower the background.

---

## 6. What drifts, what holds

Across the octopus test:

| Attribute | Holds? | Notes |
|---|---|---|
| Body color (紫色) | ✅ Strong | Never shifted across 4 scenes |
| Pink cheeks (粉色腮红) | ✅ Strong | Never lost |
| Glasses (黑粗框眼镜) | ✅ Strong unless overridden | Beach scene "墨镜" correctly replaced glasses |
| Blue suction cups (蓝色吸盘) | ✅ Strong | Always present on visible tentacles |
| Material (硅胶PVC质感) | ✅ Strong | Consistent 3D look |
| 8-tentacle anatomy | ⚠️ Flexes | Usually 4-6 visible (remainder behind body), extras sometimes added when task demands (4 keyboards = 4 tentacles) |
| Clothing | ✅ Per prompt | Pajamas / beachwear all rendered correctly |
| Held objects | ✅ Per prompt | MacBook/coffee/peace-sign/Switch/cocktail all correct |
| Scene lighting | ✅ Per prompt | Morning/blue-screen/office-white/golden-hour all distinct |
| Facial expression | ⚠️ Prompt-driven | "友好开心" in ref doesn't constrain scene expressions (debug scene showed concentration/stress) |

For photoreal human portraits rather than stylized 3D, expect weaker hold on facial features (eyes/nose ratio can shift 5-10% per generation). Stylized IPs hold far better than realistic humans.

---

## 7. When to use a different approach

- **Photoreal human likenesses (named people, real faces)** — weak on identity even with reference; use a dedicated IP-Adapter/face-swap workflow or a human-focused model.
- **Brand mascots with precise geometric rules** (e.g. exact proportions defined in a brand book) — may need multiple rounds of inpainting/touch-up.
- **5+ scene series with zero tolerance for drift** — generate in one call via Lite `--sequential` mode if you're using Lite, or hand-curate; Pro single-ref is ~90% identity hold per scene, so a 10-scene series will have some drift.

For article illustrations, social content, comic panels, marketing assets, and any application where "recognizable as the same character" is the bar rather than "pixel-identical", the single-ref + recap recipe works and is essentially free (¥0.60 per scene at 2K Pro).
