# Seedance 2.0 提示词技巧

纯技巧和词汇参考。使用前先读 `key-constraints.md` 了解能力边界，场景示例见 `scene-cookbook.md`。

## 进阶公式

```text
精准主体 + 动作细节 + 场景环境 + 光影色调 + 镜头运镜 + 视觉风格 + 画质 + 约束条件
```

Seedance 2.0 在内部拆成「空间层」（画面里有什么）和「时间层」（事情如何随时间变化）。好提示词是工程型指令，不是文案型形容。

## 定义主体

### 基本句式

`将<图片/视频N>中的[2-3个清晰的静态特征]定义为<主体N>`

```
将图片1中穿红色连衣裙、戴草帽的女人定义为张红
```

### 多人分角色

每个角色必须明确定义，后续全程使用同一标签指代：

```
将图片1中穿蓝色卫衣、戴眼镜的男孩定义为小明
将图片2中扎马尾、穿校服的女孩定义为小红
```

### 人脸参考最佳实践

- 使用**大头照（仅面部，无表情）+ 全身照**，不要用三视图/多视图
- 提示词中明确：`主体1的面部特征参考图片1（大头照），妆造参考图片2（全身照）`
- 重要素材放在提示词**越靠前**的位置

## 分镜时序

复杂视频最理想形态是时间轴化分镜：

```
镜头1：[运镜/切换方式] [主体动作与表情] [位置/空间变化] [音频]
镜头2：[运镜/切换方式] [主体动作与表情] [位置/空间变化] [音频]
镜头3：...
```

**节奏策略**：文戏用视频延长一镜到底，武戏分段独立生成后剪辑拼接。实际制作通常先延长生成连贯对话，再拼接空镜/转场。

## 动作描述

1. **肢体细化 + 程度量化**：`缓慢抬手、快速转头、用力蹬地、微微低头`
2. **优先低缓连续小动作**：优先 `缓慢行走、轻轻抬手`，规避 `狂奔、大跳、剧烈翻滚`
3. **补充动作过渡衔接**：`借着转身惯性顺势抬手、从停顿状态自然过渡到举手`
4. **情绪具象外化**（用身体细节替代抽象词）：

| 情绪 | 外化动作 |
|---|---|
| 悲伤 | 低头、肩膀颤抖、眼眶泛红、手指攥紧衣角 |
| 喜悦 | 嘴角上扬、眉眼舒展、脚步轻快、哼小曲 |
| 紧张/焦虑 | 频繁看手表、手指敲击桌面、呼吸急促、眼神闪躲 |
| 愤怒 | 双拳紧握、下颌紧绷、胸口起伏 |
| 释然 | 长舒一口气、肩膀放松、露出久违淡淡的微笑 |

## 运镜词表

**一个镜头只指定 1 种运镜**，不要同时要求推拉摇移。

### 运动

| 英文 | 中文 |
|---|---|
| `push-in` / `dolly in` | 推进 |
| `pull-back` / `dolly out` | 拉远 |
| `tracking shot` | 跟拍 |
| `orbit` | 环绕 |
| `handheld follow` | 手持跟拍 |
| `locked-off` / `static` | 固定机位 |
| `slow pan` | 慢速摇镜 |
| `tilt up/down` | 仰拍/俯拍 |
| `crane up/down` | 升/降镜头 |
| `whip pan` | 快速甩镜 |

### 角度

`eye-level`、`low-angle`、`high-angle`、`overhead`/`top-down`、`Dutch angle`、`POV`

### 景别

`extreme wide`/`establishing shot` → `wide` → `medium shot` → `medium close-up` → `close-up` → `extreme close-up`

## 光影词表

| 类型 | 关键词 |
|---|---|
| 自然光 | `golden hour`, `soft morning light`, `warm sunlight`, `natural window light` |
| 戏剧光 | `dramatic studio lighting`, `hard light pool`, `rim light`, `chiaroscuro` |
| 霓虹/都市 | `neon-lit`, `reflections on wet pavement`, `cyberpunk glow` |
| 柔和 | `soft focus`, `diffused light`, `pastel tones`, `hazy light` |
| 电影感 | `cinematic light and shadow`, `film grain`, `anamorphic lens flare` |

## 风格词表

| 类型 | 关键词 | 适用 |
|---|---|---|
| 2D 动画 | `2D animation`, `clean vector illustration`, `flat design`, `soft gradients` | 教育动画 |
| 3D 动画 | `3D animation`, `3D guofeng CG`, `Pixar-style`, `smooth shading` | 教育/产品 |
| 日漫 | `2D Japanese anime style` | 短剧 |
| 国风 | `3D guofeng CG`, `classical ink painting style` | 短剧/文化 |
| 电影纪实 | `cinematic documentary`, `film grain`, `shallow depth of field` | 短剧 |
| 赛博朋克 | `cyberpunk blue-purple tone`, `neon-lit` | 科幻 |
| 复古胶片 | `vintage film`, `Kodak film grain`, `low saturation` | 情感短剧 |

## 约束词模板

放在提示词末尾：

```
无字幕，无Logo，无水印，无闪烁，画面流畅不卡顿，人物面部稳定不变形，动作自然流畅
```

含多人物场景追加：
```
视频全程禁止出现外形着装配饰完全一致的人物，禁止生成同款分身或双胞胎效果
```

## 特殊符号

| 类型 | 符号 | 示例 |
|---|---|---|
| 音乐 | `（）` | `（背景中播放着快节奏的摇滚乐）` |
| 音效 | `<>` | `<远处传来狗叫声>` |
| 台词 | `{}` | `{你好，世界}` |
| 小语种台词 | `{}` + 标注 | `用日语说道{こんにちは}` |
| 字幕 | `【】` | `【第一章：启程】` |

## 语言与素材引用规则

- 运镜/光影/风格推荐英文，台词可用中文
- 台词语言统一，避免中英混用（专有名词除外）
- 素材引用必须用 `图片n`/`视频n`/`音频n` 格式（n 为同类素材排序，从 1 开始），不支持 Asset ID 直接指代
- 提示词不能直接用完整剧本原文，需精简无关表述

## 来源

- [火山方舟视频生成 API 参考](https://www.volcengine.com/docs/82379/1520758?lang=zh)
- [Doubao Seedance 2.0 系列教程](https://www.volcengine.com/docs/82379/2291680?lang=zh)
- [Doubao Seedance 2.0 系列提示词指南](https://www.volcengine.com/docs/82379/2222480?lang=zh)
- [视频生成教程](https://www.volcengine.com/docs/82379/2298881?lang=zh)
