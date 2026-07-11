# Seedream 5.0 API Reference (Pro + Lite)

This doc covers HTTP API details for both Seedream 5.0 Pro and 5.0 Lite on Volcengine Ark, plus client-side conventions for marker editing and outpaint used by this skill. Pro is the default model; Lite is the fast-sketch fallback.

## 官方文档

| 文档 | 链接 |
|------|------|
| Seedream 5.0 Pro 教程（官方） | https://www.volcengine.com/docs/82379/1824121 |
| 图片生成 API 参考（统一端点） | https://www.volcengine.com/docs/82379/1541523 |
| Seedream 5.0 提示词指南 | https://www.volcengine.com/docs/82379/1829186 |
| 模型列表 | https://www.volcengine.com/docs/82379/1330310 |
| 模型价格 | https://www.volcengine.com/docs/82379/1544106 |

## API Endpoint

```
POST https://ark.cn-beijing.volces.com/api/v3/images/generations
```

**Seedream 5.0 Pro 没有独立的 `/edits` 端点**——t2i、单图 img2img、多图融合、区域编辑、风格迁移都走同一个 `/images/generations`，靠 `image` 字段和 prompt 中的视觉标记协议区分（见下文「Marker 编辑协议」一节）。

## Authentication

Bearer Token，从环境变量 `ARK_API_KEY` 读取：

```
Authorization: Bearer <ARK_API_KEY>
Content-Type: application/json
```

`ARK_BASE_URL` 可覆盖 base URL，默认 `https://ark.cn-beijing.volces.com/api/v3`。脚本从 cwd `.env` 自动读取（如果 shell 未设置）。

## 可用模型

| Version | Model ID | 默认 | 预设 size | 像素范围 | Refs | web_search | sequential | neg_prompt | 延迟（2K） | 价格 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Seedream 5.0 Pro** | **`doubao-seedream-5-0-pro-260628`** | ✅ default | `1K`, `2K` | 921,600 – 4,624,220 (0.9MP–4.6MP，默认 1024²) | 10 | ❌ rejected | ❌ rejected | ✅ beta (undocumented; accepted by the API) | ~75–124s mean ≈95s | ≤2.36MP ¥0.30; >2.36MP ¥0.60; extra input image ¥0.02/each |
| Seedream 5.0 Lite | `doubao-seedream-5-0-260128` | `--model lite` | `2K`, `3K`, `4K` | 3,686,400 – 16,777,216 (3.7MP–16MP，默认 2048²) | 14 | ✅ | ✅ | ❌ | ~30–60s | ¥0.22/张（2K 档） |

> CLI 接受别名：`pro` / `seedream-pro` / `5-pro` → Pro；`lite` / `seedream-lite` / `5-lite` → Lite。传入未知完整 ID 时按 Pro 能力默认值透传（方便使用新的 dated build）。

### 关键差异要点

1. **Pro 不支持 3K/4K**——method-1 上限约 4.6MP（总像素 4,624,220，如 2048×2048 或 16:9 的 2816×1584）。想要更高分辨率请用 Lite 或出图后用超分模型。
2. **Lite 有 3.69MP 像素下限**（2560×1440 起步），**不允许 1K/1024²/1792×1024**。因此：
   - 宽幅 16:9 banner/cover（1792×1024≈1.84MP，例如微信公众号头图、博客 hero、YouTube 封面、视频封面、PPT cover）是 **Pro 专属**，Lite 跑不了。
   - 方形 1024×1024 图标、社交头像也是 Pro 专属。
3. **Pro rejects `tools:[{type:"web_search"}]`, `sequential_image_generation`, and `stream: true`** — these parameters return 400 on Pro. The CLI's `_build_request_body` filters them per-model capability; only Lite sends `tools`.
4. **`optimize_prompt_options.mode` accepts `"standard"` on both 5.0 Pro and 5.0 Lite (and 4.5)** — `"fast"` is Seedream 4.0 only; the CLI warns and ignores unsupported values rather than sending them to the API.
5. **`negative_prompt` works on Pro** (not yet in official docs); the CLI sends a gentle quality guard by default: `模糊, 低质量, 水印, 变形, 多余肢体`. Disable with `--no-negative-prompt` or override with `--negative-prompt "..."`. Lite accepts the field but produces negligible effect, so the CLI omits it.
6. Both models share a prompt-length ceiling: Chinese ≤300 characters, English ≤600 words; the server truncates silently rather than erroring.
7. **Default size is `2K`** — latency at 1K and 2K is nearly identical (~95s mean), and 2K produces noticeably sharper text. Price differs only at the ≤2.36MP tier (¥0.30).

## Request Body

### Pro 最小 t2i body

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "prompt": "充满活力的特写编辑肖像，模特眼神犀利，头戴雕塑感帽子，色彩拼接丰富，眼部焦点锐利，景深较浅，Vogue 杂志封面美学，中画幅，工作室强灯。",
  "size": "2K",
  "output_format": "png",
  "watermark": false
}
```

### Pro 最小 img2img / edit body（带 reference）

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "prompt": "把图中红色方框内的米色沙发替换为深蓝丝绒三人位，茶几上加一只橘猫，保持光线、背景、窗外绿植完全不变，擦除所有红色标记。",
  "image": "data:image/png;base64,<base64-of-annotated-png>",
  "size": "2K",
  "output_format": "png",
  "watermark": false
}
```

`image` 可传：
- 单个 URL 或 `data:image/<fmt>;base64,<b64>` 字符串（fmt 小写，jpg 写 `jpeg`）。
- 字符串数组，最多 max_refs 张（Pro 10 / Lite 14）；多图融合时用自然语言描述"用图1的人物、图2的服装、图3的背景"。

### 参数矩阵（按模型适用性）

| 参数 | 类型 | 默认 | Pro | Lite | 说明 |
|---|---|---|---|---|---|
| `model` | string | — | ✅ 必填 | ✅ 必填 | 模型 ID 或别名 |
| `prompt` | string | — | ✅ 必填 | ✅ 必填 | 文字描述；中 ≤300 字/英 ≤600 词 |
| `size` | string | Pro=`2K`, Lite=`2K` | ✅ | ✅ | 预设（见下）或 `WIDTHxHEIGHT` |
| `output_format` | string | — | `png`/`jpeg` | `png`/`jpeg` | 输出格式 |
| `response_format` | string | `url` (official default; the CLI omits this field and relies on the default) | ✅ | ✅ | `url` returns a 24h-valid TOS download link; `b64_json` returns inline base64 bytes. The CLI does not expose this parameter and always downloads via URL (rationale: url mode supports streaming download, avoids the +33% base64 overhead, and the CLI downloads immediately so the 24h expiry is irrelevant). |
| `watermark` | boolean | false | ✅ | ✅ | 是否加 Seedream 水印 |
| `image` | string\|string[] | — | 最多 10 | 最多 14 | 参考图，支持 URL 或 data URL |
| `optimize_prompt_options.mode` | string | `standard` | `standard` 唯一 | `standard` 唯一（fast 仅 4.0） | prompt 优化模式；CLI 传非法值会告警并忽略 |
| `negative_prompt` | string | none (CLI adds a default on Pro) | ✅ beta | ⚠️ ignored | Negative prompt; effective on Pro |
| `tools` | array | — | ❌ 拒绝 | `[{"type":"web_search"}]` | 联网搜索；Lite 上 `--web-search` 显式开启才发 |
| `sequential_image_generation` | string | — | ❌ 拒绝 | `"auto"` | 连续组图/分镜模式 |
| `sequential_image_generation_options.max_images` | int | — | ❌ | 1–15 | 连续组图张数 |
| `stream` | boolean | — | ❌ rejected | ✅ | Streaming response (not used by this CLI) |

**Fields not to send (unsupported on both Pro and Lite)**: `num_images`/`n` (use the CLI concurrency or Lite sequential for batches), `seed`, `guidance_scale`, `steps`, `mask`, `bbox`, `layers`, `control_image` — these are either silently ignored or return 400.

### Capabilities not exposed on the public API

The capabilities below appear in Seedream 5.0 Pro **official demo UI** or **marketing materials** but are **not exposed on the public Ark API** and cannot be implemented by the CLI. File product feedback with Volcengine if you need them.

| Capability | Demo UI? | Public API? | CLI workaround |
|---|---|---|---|
| **Auto layer separation** (split the scene into N transparent PNG layers + occlusion inpaint) | Yes (product demo video) | **No** | Impossible in a single call. Multi-region marker edits over multiple rounds can approximate "remove one element at a time", but never produce N independent alpha-channel layers. **For PS-grade layer separation, use LayerSwap / Segment Anything / a ComfyUI workflow.** |
| **Native mask input** (upload B/W mask to constrain edit area) | No | **No** | Marker rectangles are the alternative; only rough rectangles, no curved masks/feathered edges/multi-mask compositing. |
| **Bbox / polygon input** (precise non-rectangular region selection) | No | **No** | Marker rectangles are the only supported visual-marker protocol. |
| **ControlNet conditional input** (canny/depth/openpose) | No | **No** | Not available. Sketch-to-render relies on img2img + natural-language description; skeleton/depth references cannot be supplied. |
| **ControlNet-style strength slider** (style_strength 0-1) | No | **No** | Style strength is controlled through prompt wording ("inspired by" = weak, "fully re-painted" = strong); there is no numeric slider. |
| **Per-layer alpha / blend modes** (multi-channel output) | No | **No** | Output is always a single RGB PNG; no alpha channel, no multi-channel, no PSD/EXR. |
| **Native LoRA / fine-tune adapter upload** | Yes (developer) | Limited (`--reference-image` acts as an implicit adapter, but custom LoRA uploads are not accepted)| No `--lora <path>` interface. |
| **Rotational / motion blur physics** (wheels / fan blades) | No | **Yes (prompt-driven to 9/10)** | ❗ Bare "motion blur on wheels" is ignored. Use anti-detail phrasing describing the wheel as "flying-saucer disc, no spokes/rim/tread visible, smooth rotational blur disc" to produce natural wheel-motion blur. See photorealism.md recipe. The key is concretely describing the blur target (a disc with no spoke detail), not naming the effect. |
| **3D geometric prior** (multi-view consistency / 3D reconstruction) | No | **No** | Different views of the same object can be geometrically inconsistent. No multi-view diffusion / NeRF / 3D Gaussian Splatting capability. |
| **Pixel-perfect UI screenshot generation** | No | **No** | UI control position/size is not controllable. **For spec UI mockups, use Figma + a design system.** |

> **Honest note**: Marketing claims of "intelligent layer separation, PS-grade layering, movable/deletable objects" refer to capabilities that do **not** exist on the public Ark API. This CLI delivers marker-based multi-region edits (region recolor/swap/add/remove), **not** alpha-channel layered PSD output. For PS-grade layer separation, switch to a dedicated toolchain (Segment Anything + manual export / Photoshop Generative Fill / a ComfyUI workflow).

### Size：两种指定方式（不可混用）

**Method 1 — Explicit pixels `WIDTHxHEIGHT`** (all CLI shortcuts use this method; you control pixels exactly):
- Pro：默认值 `1024×1024`；总像素 921,600（1280×720）–4,624,220（2048²×1.1025），长宽比 ∈ [1/16, 16]
- Lite：默认值 `2048×2048`；总像素 3,686,400（2560×1440）–16,777,216（4096×4096），长宽比 ∈ [1/16, 16]
- 约束是**总像素乘积** + 长宽比，两者需同时满足；不是对单边像素设限。模型可出这两个区间内的**任意**宽高比，不局限于下表列的几个。
- 客户端在发请求前校验范围，越界直接报错不浪费 API call。

**方式 2 — 分辨率档位 `1K`/`2K`/`3K`/`4K` + 在 prompt 里用自然语言描述宽高比/形状/用途**，最终由**模型判断**输出尺寸。Pro 支持 `1K`/`2K`，Lite 支持 `2K`/`3K`/`4K`。下表是官方给出的「当 prompt 只描述某个常见比例时，模型实际映射的宽高**参考值**」——是参考/默认值，不是硬合同；换个 prompt 或非常规比例，模型会给出该档位下对应比例的其它像素。

**Pro 官方 method-2 参考映射表**（`--size 1K/2K` + prompt 描述该比例时的典型输出像素）：

| 宽高比 | 1K | 2K |
|---|---|---|
| 1:1 | 1024×1024 | 2048×2048 |
| 4:3 | 1152×864 | 2368×1776 |
| 3:4 | 864×1152 | 1776×2368 |
| 16:9 | 1424×800 | 2816×1584 |
| 9:16 | 800×1424 | 1584×2816 |
| 3:2 | 1248×832 | 2496×1664 |
| 2:3 | 832×1248 | 1664×2496 |
| 21:9 | 1568×672 | 3136×1344 |

> **Lite 的 method-2 映射与 Pro 不同**（Lite 2K 16:9 = 2848×1600 ≠ Pro 2816×1584），且多 3K/4K 两档。完整 Lite 官方参考表如下：

**Lite 官方 method-2 参考映射表**（authoritative，`--size 2K/3K/4K` + prompt 描述该比例时的典型输出像素）：

| 宽高比 | 2K | 3K | 4K |
|---|---|---|---|
| 1:1 | 2048×2048 | 3072×3072 | 4096×4096 |
| 4:3 | 2304×1728 | 3456×2592 | 4704×3520 |
| 3:4 | 1728×2304 | 2592×3456 | 3520×4704 |
| 16:9 | 2848×1600 | 4096×2304 | 5504×3040 |
| 9:16 | 1600×2848 | 2304×4096 | 3040×5504 |
| 3:2 | 2496×1664 | 3744×2496 | 4992×3328 |
| 2:3 | 1664×2496 | 2496×3744 | 3328×4992 |
| 21:9 | 3136×1344 | 4704×2016 | 6240×2656 |

> **Method 1 vs Method 2, when to use which**: For deterministic pixels (platform uploads, print, matching an existing layout) → Method 1 (`--size WxH` or a shortcut). For a "feel" where the ratio matters more than exact pixels → Method 2 (`--size 2K` + describe the ratio in the prompt). The CLI's `--wide`/`--landscape`/`--square` shortcuts are Method-1 exact-pixel presets, separate from the Method-2 preset tiers.

常用精确尺寸（Pro 下）：
- 1024×1024 = 1.05MP（1:1 方图：产品主图、头像、logo、app icon、social 方图）—— `--square`
- 1536×2048 = 3.15MP（3:4 竖版海报、封面、social 竖图）—— `--portrait`
- 1792×1024 = 1.84MP（16:9 宽幅 banner/cover：公众号头图、博客 hero、YouTube/视频封面、PPT cover）—— `--wide`
- 2048×1152 = 2.36MP（16:9 横版 2K 壁纸、PPT slide、电影帧、横版插图）—— `--landscape`
- 2048×2048 = 4.19MP（最大方图；method-1 总像素上限 4.62MP，非方形比例可略大，如 2816×1584=4.46MP）
- 1024×1536 = 1.57MP（2:3 竖版，legacy 精确像素；多数场景建议用 --portrait）

常用精确尺寸（Lite 下，最低 2560×1440）：
- 2048×2048 = 4.19MP（1:1 方图）—— `--square`
- 2048×2732 = 5.59MP（3:4 竖版）—— `--portrait`
- 2560×1440 = 3.69MP（16:9 横版下限，刚好踩 pixel floor；不推荐，细节不足）
- 2732×1536 = 4.20MP（16:9 横版）—— `--landscape`
- 3072×3072 = 9.44MP（3K 方图）—— `--size 3K` + prompt 描述 1:1
- 4096×4096 = 16.78MP（4K 方图，接近 Lite 16MP 上限）—— `--size 4K` + prompt 描述 1:1

> 其它比例的 method-2 参考像素见上方 Lite 映射表。非方图高分辨率（如 16:9 4K=5504×3040≈16.7MP）直接走 `--size 4K` + prompt 描述比例即可，模型会按表输出。

### CLI size shortcut flags

CLI 提供以下 aspect-ratio shortcut，按模型自动解析为合法精确像素，避免手动算分辨率：

| Flag | Pro 分辨率 | Lite 分辨率 | 比例 | 典型用途 |
|---|---|---|---|---|
| `--wide` | 1792×1024 | ❌ Pro-only | 16:9 | 宽幅 banner / cover / hero / YouTube / 视频封面 / PPT cover |
| `--portrait` | 1536×2048 | 2048×2732 | 3:4 | 竖版海报、封面、社交竖图、stories |
| `--landscape` | 2048×1152 | 2732×1536 | 16:9 | 横向 2K 壁纸、PPT slide、电影帧、横版插图 |
| `--square` | 1024×1024 | 2048×2048 | 1:1 | 方图（Pro 走量快成本低；Lite 自动升到 2K 方图满足像素下限） |

`--wechat-header` 是 `--wide` 的向后兼容别名（二者等价，都产出 1792×1024）。`--size WIDTHxHEIGHT` 可覆盖任意 shortcut，优先级最高。注意 1792×1024 低于 Lite 的 3.69MP 像素下限，所以 `--wide`/`--wechat-header` 只能在 Pro 上使用；CLI 在 Lite 下会显式报错而非静默降级。

### Common Use-Case Size Reference（常见场景尺寸指引）

> **使用前须知**：平台尺寸会随版本调整（小红书 3:4/9:16 来回切过、Instagram 多次改 stories 规范）。下表给的是 **aspect ratio + 推荐 shortcut + 像素区间**，不是精确到个位的合同式尺寸——上传平台会做自动缩放/裁切，比例对即可。对像素有硬要求的印刷/官网 hero/广告投放位请查平台官方 spec 后用 `--size WxH` 精确指定。连环画/comics 是多格排版问题，不是单一尺寸，请走 `visual-narrative.md` style preset。

| 场景 | 比例 | 推荐 shortcut | Pro 像素 | Lite 像素 | 备注 |
|---|---|---|---|---|---|
| 公众号头图 / 博客 hero / YouTube 封面 / B站/视频封面 / PPT 首页 | 16:9 | `--wide` | 1792×1024 | ❌ Pro-only | 最常用宽幅；公众号关键信息留左 60% 避免右侧裁切 |
| 电商主图（淘宝/京东/Amazon/Shopify/抖音小店） | 1:1 | `--square`（走量）/ `--size 2K`（首图细节） | 1024×1024 / ~2048² | 2048×2048 | SKU 铺量用 --square 快；首图建议 2K |
| 电商详情页长图 | 3:4 | `--portrait` | 1536×2048 | 2048×2732 | 单张详情模块图，长图拼接由后期做 |
| 小红书 / Instagram feed / 微博配图 | 3:4 或 1:1 | `--portrait` / `--square` | 1536×2048 / 1024×1024 | 2048×2732 / 2048×2048 | 小红书 2026 推荐 3:4，1:1 也可用；9:16 易被裁切 |
| 小红书 / Instagram / TikTok / 视频号 Stories / Reels 竖版 | 9:16 | `--size 1088x1920`（Pro）/ `--size 1440x2560`（Lite，踩 Lite 像素下限） | 1088×1920≈2.09MP | 1440×2560≈3.69MP | ⚠️ 9:16 prompt 里必须显式加"无UI界面、无手机边框、无状态栏、无App按钮、纯画面内容"，否则"手机/9:16/stories"词会让模型脑补假手机UI；Stories 文字避开顶部 15%/底部 20%（UI 遮挡区） |
| 小红书封面竖图 | 3:4 | `--portrait` | 1536×2048 | 2048×2732 | 小红书笔记封面比 feed 图大，文字集中在上半部分 |
| 抖音/TikTok 视频封面 | 9:16 或 1:1 | `--size 1088x1920`（9:16）/ `--square`（1:1） | 同上 | 同上 | 视频封面文字居中，不要贴边 |
| 微博/推特/X 头图 cover | 3:1 | `--size 1500x500` | 1500×500 = 0.75MP ❌（低于 Pro 0.9MP 下限） | ❌ | 这种细长条 Pro 也跑不了；建议出 3:1 或 16:9 后 PS 裁切，或出 2048×1152 landscape 后手动裁 |
| 公众号正文插图（非封面） | 16:9 或 2.35:1 | `--landscape` | 2048×1152 | 2732×1536 | 正文中插图宽比 2.35:1 电影感也可（`--size 1792x768`≈1.37MP，Pro 可用） |
| Desktop wallpaper（PC/Mac） | 16:9 或 21:9 | `--landscape` 或 `--size 2560x1440` | 2048×1152 / 2560×1440 | 2732×1536 / 2560×1440 | 21:9 超宽屏：Pro `--size 2560x1080`≈2.76MP；Lite `--size 3440x1440`≈4.95MP |
| Mobile wallpaper（手机壁纸） | 9:19.5 左右 | `--size 1088x2340`（Pro）/ `--size 1440x3120`（Lite） | 1088×2340≈2.55MP | 1440×3120≈4.49MP | 各机型有差异，9:16–9:20 区间平台自动适配；避开顶部刘海/底部 dock 区 |
| 海报 / 杂志封面 / A4 印刷 | 3:4 或 2:3 | `--portrait` 或 `--size 1440x2160` | 1536×2048 / 1440×2160≈3.11MP | 2048×2732 | 印刷建议出图后超分到 300dpi，AI 直出像素不够印 A4 以上 |
| App icon / 头像 / 方形 logo | 1:1 | `--square` | 1024×1024 | 2048×2048 | 1024 是移动端标准尺寸；Pro 1024×1024 够 |
| PPT slide 背景（16:9） | 16:9 | `--landscape` | 2048×1152 | 2732×1536 | 投到 4K 投影用 Lite 2732×1536 或 3K preset |
| 电商大促 banner（首页轮播） | 宽幅 2:1 至 4:1 | `--size 1792x768`（Pro，≈2.35:1）或 `--size 1920x800`（Pro≈2.4:1） | 1792×768≈1.37MP / 1920×800≈1.54MP | ❌（均低于 Lite 下限） | 大促轮播多是 750×390/990×430 类尺寸，AI 直出后前端等比缩放即可 |
| 圆形徽章 / Logo / 头像框 | 1:1 | `--square` | 1024×1024 | 2048×2048 | 出方图后后期裁圆；模型对圆形字在方 canvas 上响应最准 |
| 外卖/本地生活商家图（美团/饿了么/大众点评） | 1:1 或 3:4 | `--square` / `--portrait` | 1024×1024 / 1536×2048 | 2048×2048 / 2048×2732 | 菜品图 1:1 走量快 |

**一般规律**：
- **1:1 方图** 是最通用的 social + e-commerce 尺寸，Pro 1024×1024（`--square`）成本最低、走量最快。
- **3:4 竖版** 是小红书/Instagram/magazine cover 的通用比例，Pro 1536×2048（`--portrait`）覆盖大多数竖版需求。
- **16:9 横版** 有两个档位：`--wide`=1792×1024（banner/hero，Pro-only，短边 1024）和 `--landscape`=2048×1152（壁纸/slide/电影帧，Pro/Lite 都能跑，短边 1152+）。选 `--wide` 还是 `--landscape` 看你要不要 1080p 级短边。
- **9:16 stories** 必须显式 `--size WxH`（没有 shortcut，因为 9:16 在 Pro 下踩到 <1024 短边的特殊情况）。
- **Lite 不能跑 1792×1024、1024×1024、1088×1920 这类 <3.69MP 的尺寸**——凡是 Lite 列里打 ❌ 的都只能用 Pro 或 `--size 2K`/`3K` 让 server 选更大尺寸再后期裁切。
- 当你只知道"感觉像手机壁纸"而不锁像素时，直接在 prompt 里写"手机壁纸 9:16" 不传 size flag，server 会在 2K 预设里挑接近比例的尺寸；需要精确比例一定用 `--size WxH` 或 shortcut flag。

### 参考图格式要求

- 格式：jpeg / png / webp / bmp / tiff / gif / heic / heif
- Aspect ratio：[1/16, 16]
- 单边 > 14px
- 单张 ≤ 30MB，总像素 ≤ 36MP（6000×6000）
- Data URL 形式：`data:image/<fmt>;base64,<b64>`（fmt 小写）

## Response (200 OK)

The CLI omits `response_format` and relies on the official default `url`. Actual response shape:

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "created": 1757321139,
  "data": [
    {
      "url": "https://ark-content-generation-*.tos-cn-*.volces.com/*.png?...",
      "size": "2848x1600",
      "output_format": "png"
    }
  ],
  "usage": {
    "generated_images": 1,
    "input_images": 1,
    "output_tokens": 15990,
    "total_tokens": 15990
  }
}
```

If the client explicitly sends `response_format: b64_json` (not done by the CLI, but natively supported by the API), fields inside `data[]` use `b64_json` (base64-encoded bytes) instead of `url`.

| 字段 | 说明 |
|---|---|
| `data[].url` | URL returned by the API — a 24h-valid download link; `_download_image` fetches and saves it immediately (with 8-attempt exponential-backoff retry) |
| `data[].b64_json` | Present only when the caller explicitly sends `response_format=b64_json`; not used by the CLI |
| `data[].revised_prompt` | 模型改写后的 prompt（不一定有） |
| `data[].size` | 实际输出分辨率（精确 `WxH`） |
| `data[].output_format` | 实际输出格式 |
| `usage.generated_images` | 生成图片数（Pro 恒为 1） |
| `usage.input_images` | 输入参考图数（计费用，第一张免费，多的 ¥0.02/张） |
| `usage.output_tokens` | 图像 token 数（可用于近似计费） |
| `usage.total_tokens` | 总 token |

## Marker 编辑协议（客户端约定，不是 API 原生字段）

Marker editing is one of Pro's headline capabilities and is the default path for the `edit` subcommand. **The API itself has no mask/bbox parameter** — Pro's "local edit" works entirely by "drawing a colored marker on the reference image + describing the change in natural language"; the model reads the image to recognize the marker, performs the local edit, and erases the marker automatically.

### Protocol steps (automated by the CLI)

1. The user specifies rectangular regions to edit via repeatable `--marker-rect X,Y,W,H` arguments, accepting pixel coordinates or percent (e.g. `20%,10%,60%,25%`).
2. The CLI draws a **semi-transparent filled rectangle with a solid outline of the same color** on the reference using Pillow (default `#ff0000` red, fill alpha=80/255, stroke=3px).
3. Color can be changed per rectangle with `--marker-color #00ff00` (for multi-color multi-region edits, say "红框内换 XX，蓝框内加 YY" in the prompt).
4. An annotated copy is saved to the output directory (`*-annotated.png`) for visual inspection, and the annotated image is sent as the `image` field.
5. The CLI **auto-appends a marker-cleanup instruction** to the end of the prompt (Chinese/English chosen by prompt-language heuristic):
   - Chinese: `图中彩色方框/圆圈/涂写是我手工标出的编辑区域标记，请严格按上面的描述修改标记区域内的内容，标记区域之外的像素尽量保持不变，完成后清除所有彩色标记线条与填充。`
   - English: `The colored rectangles/circles/scribbles in the image are edit markers I drew by hand. Apply the change described above strictly inside the marked regions, keep pixels outside the markers unchanged, and remove all colored marks once done.`
6. `--no-marker-cleanup-prompt` disables the auto-appended instruction (for advanced users who write their own cleanup prompt).

### Validated marker scenarios

- ✅ Headline/subtitle **text swaps** on posters/covers (matching font/size/position; surrounding pixels preserved).
- ✅ Object replacement (swap a sofa for a navy-velvet sofa and add a cat; lighting/background unchanged).
- ✅ Material change (metal sculpture → transparent glass, preserving reflection structure).
- ✅ Multi-region multi-color edits (red box: swap title, blue box: add element).
- ❌ Only rectangles are supported out of the box; circles/arbitrary scribbles require pre-drawing with Pillow.

## Outpaint protocol (client-side canvas extension; not an API field)

The API has no `outpaint` parameter; true pixel-level outpaint is implemented via a client-side technique:

1. Specify directions and pixel amounts with repeatable `--outpaint <dir>:<pixels>` (e.g. `--outpaint left:400 --outpaint right:400`).
2. The CLI pastes the source image onto the center of a larger canvas and fills empty space with an edge-sampled neutral color to mask seams.
3. A Chinese/English fill instruction is auto-appended to the prompt (e.g. "The center of this canvas is the original image. Naturally extend and fill the surrounding blank areas...").
4. The extended canvas is sent as `image`; the model fills the extended region (the center is likely to be slightly repainted rather than being pixel-locked — sufficient for most article-illustration use cases).

> Strict outpaint that leaves the center pixel-identical requires a local inpaint mask; the public Ark API does not expose this capability.

## Pricing

| Model | Price |
|---|---|
| Seedream 5.0 Pro, output ≤ 2.36MP | ¥0.30/image |
| Seedream 5.0 Pro, output > 2.36MP | ¥0.60/image |
| Pro additional input images (from the 2nd) | ¥0.02/image |
| Seedream 5.0 Lite | ¥0.22/image (2K tier) |

RPM ≈ 500; the CLI defaults to concurrency 3 with 8-attempt exponential backoff (2/4/8/16/30/30/30/30s) and honors the `retry-after` header, so normal usage stays under the 429 throttle.

## Error Codes

| HTTP | Code | Meaning | Retry? |
|---|---|---|---|
| 400 | `InvalidParameter` / `BadRequest` | Parameter error (e.g. web_search on Pro, size out of range, corrupt reference) | No |
| 401 | `AuthenticationError` | API key malformed or expired | No |
| 403 | `RequestForbidden` | Authenticated but not permitted (model not enabled, account in arrears) | No |
| 429 | `RequestLimitExceeded` | Rate limited; honor `retry-after` header | **Yes** |
| 500 | `InternalError` | Server-side error | **Yes** |
| 502/503/504 | — | Gateway / service unavailable | **Yes** |

Error response body:

```json
{ "error": { "code": "BadRequest", "message": "..." } }
```

## Why the CLI downloads via URL

The CLI omits `response_format` so the API defaults to returning `url`. Rationale:

1. The official API default is `url` across all models; aligning with the default avoids unnecessary divergence.
2. base64 adds a hard +33% size overhead and must be parsed and decoded entirely in memory; for large images (Lite up to 16MP) this becomes noticeable. URL mode supports streaming download without that overhead.
3. The 24h URL expiry is irrelevant in the CLI's workflow — the image is downloaded in-process immediately after generation, with no intervening queue or human-review window.
4. Keeping a single code path (no `--response-format` flag) is simpler than plumbing the option through the capability dict, CLI flags, body builder, and batch pipeline.
5. `_download_image` has its own 8-attempt exponential-backoff retry (matching `_call_api`'s backoff curve), so transient network failures only retry the cheap download step and never waste a successful (and already billed) generation call.

The API still natively supports `b64_json` for environments that cannot reach the image-host domain; add `"response_format": "b64_json"` inside `_build_request_body` if you need it.

## Out of scope for this CLI

- **No volcengine Python SDK** — uses `httpx` against the raw REST endpoint for minimal, auditable dependencies and zero-install `uv run`.
- **No ControlNet / depth-map / pose-pose control** — the public API does not expose these controls.
- **No pixel-perfect layer separation** — the "split into a dozen layers" capability shown in ByteDance marketing is client-side UI functionality and is not exposed on the public Ark API.
- **No n>1 batch in a single request** — Pro returns 1 image per request; batches use client-side concurrency via `generate-batch --concurrency N`.
