# Seedream 5.0 API Reference (Pro + Lite)

本 skill 当前**以 Seedream 5.0 Pro 为默认模型**，并保留 Seedream 5.0 Lite 作为 fast-sketch 备用。本文件记录两个模型在火山方舟（Volcengine Ark）上的 HTTP API 细节，以及本 skill 在客户端侧做的 marker 编辑与 outpaint 约定。

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
| **Seedream 5.0 Pro** | **`doubao-seedream-5-0-pro-260628`** | ✅ default | `1K`, `2K` | 921,600 – 4,194,304 (0.9MP–4MP) | 10 | ❌ 拒绝 | ❌ 拒绝 | ✅ beta（未入文档，实测可用） | ~75–124s 均值 ≈95s | ≤2.36MP ¥0.30；>2.36MP ¥0.60；额外输入图 ¥0.02/张 |
| Seedream 5.0 Lite | `doubao-seedream-5-0-260128` | `--model lite` | `2K`, `3K`, `4K` | 3,686,400 – 16,777,216 (3.7MP–16MP) | 14 | ✅ | ✅ | ❌ | ~30–60s | ¥0.22/张（2K 档） |

> CLI 接受别名：`pro` / `seedream-pro` / `5-pro` → Pro；`lite` / `seedream-lite` / `5-lite` → Lite。传入未知完整 ID 时按 Pro 能力默认值透传（方便使用新的 dated build）。

### 关键差异要点

1. **Pro 不支持 3K/4K**——最大 ~4MP（2048×2048）。想要更高分辨率请用 Lite 或出图后用超分模型。
2. **Lite 有 3.69MP 像素下限**（2560×1440 起步），**不允许 1K/1024²/1792×1024**。因此：
   - 宽幅 16:9 banner/cover（1792×1024≈1.84MP，例如微信公众号头图、博客 hero、YouTube 封面、视频封面、PPT cover）是 **Pro 专属**，Lite 跑不了。
   - 方形 1024×1024 图标、社交头像也是 Pro 专属。
3. **Pro 不接受 `tools:[{type:"web_search"}]`、`sequential_image_generation`、`stream: true`**——这些参数会被 API 400 拒绝。本 skill 的 `_build_request_body` 会按模型能力自动裁剪，Lite 才发 `tools`。
4. **Pro 上 `optimize_prompt_options.mode` 只接受 `"standard"`**（不接受 `"fast"`）。
5. **`negative_prompt` 在 Pro 上实测可用**（官方暂未写入文档），本 skill 默认发一条温和的质量守护 "模糊, 低质量, 水印, 变形, 多余肢体"，可通过 `--no-negative-prompt` 关闭或 `--negative-prompt "..."` 覆盖。Lite 上不发送（API 接受但效果不显著）。
6. 两模型共享最长 prompt 字符数：中文 ≤300 字、英文 ≤600 词，服务端截断但不报错。
7. Pro 实测 1K→2K 延迟几乎无差（~95s 均值），所以**默认 size 是 `2K`**——2K 下文字渲染细节明显更好，价格只在 ≤2.36MP 档和 1K 差 ¥0.30。

## Request Body

### Pro 最小 t2i body

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "prompt": "充满活力的特写编辑肖像，模特眼神犀利，头戴雕塑感帽子，色彩拼接丰富，眼部焦点锐利，景深较浅，Vogue 杂志封面美学，中画幅，工作室强灯。",
  "size": "2K",
  "output_format": "png",
  "watermark": false,
  "response_format": "b64_json"
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
  "watermark": false,
  "response_format": "b64_json"
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
| `response_format` | string | Pro=`b64_json`, Lite=`url` | ✅ | ✅ | `b64_json` 省一次 HTTP hop 且无 URL 过期；`url` 是 24h 有效的 TOS 链接 |
| `watermark` | boolean | false | ✅ | ✅ | 是否加 Seedream 水印 |
| `image` | string\|string[] | — | 最多 10 | 最多 14 | 参考图，支持 URL 或 data URL |
| `optimize_prompt_options.mode` | string | `standard` | `standard` 唯一 | `standard`/`fast` | prompt 优化模式 |
| `negative_prompt` | string | 无（本 skill 默认加） | ✅ beta | ⚠️ 忽略 | 反向提示词，Pro 上实测有效 |
| `tools` | array | — | ❌ 拒绝 | `[{"type":"web_search"}]` | 联网搜索；Lite 上 `--web-search` 显式开启才发 |
| `sequential_image_generation` | string | — | ❌ 拒绝 | `"auto"` | 连续组图/分镜模式 |
| `sequential_image_generation_options.max_images` | int | — | ❌ | 1–15 | 连续组图张数 |
| `stream` | boolean | — | ❌ 拒绝 | ✅ | 流式响应（本 skill 不使用） |

**不要发的字段（Pro/Lite 都不支持）**：`num_images`/`n`（批量要用本 skill 的并发或 Lite sequential）、`seed`、`guidance_scale`、`steps`、`mask`、`bbox`、`layers`、`control_image`——这些要么被静默忽略要么 400。

### Size 预设

| 预设 | 典型分辨率（服务端按 prompt 比例选） | Pro | Lite |
|---|---|---|---|
| `1K` | ~1024×1024 / 1024×1792 / 1792×1024，约 1MP | ✅ | ❌（低于像素下限） |
| `2K` | ~2048×2048 / 2560×1440 / 1440×2560，约 4MP | ✅ | ✅ |
| `3K` | ~3072×3072 / 4096×2304 / 2304×4096，约 9MP | ❌ | ✅ |
| `4K` | ~4096×4096，约 16MP | ❌ | ✅ |

精确像素格式 `WIDTHxHEIGHT`：
- Pro：总像素 921,600–4,194,304，长宽比 ≤16:1
- Lite：总像素 3,686,400–16,777,216，长宽比 ≤16:1

常用精确尺寸（Pro 下）：
- 1024×1024 = 1.05MP（1:1 方图：产品主图、头像、logo、app icon、social 方图）—— `--square`
- 1536×2048 = 3.15MP（3:4 竖版海报、封面、social 竖图）—— `--portrait`
- 1792×1024 = 1.84MP（16:9 宽幅 banner/cover：公众号头图、博客 hero、YouTube/视频封面、PPT cover）—— `--wide`
- 2048×1152 = 2.36MP（16:9 横版 2K 壁纸、PPT slide、电影帧、横版插图）—— `--landscape`
- 2048×2048 = 4MP（2K 方图上限，产品细节、高分辨率方图）
- 1024×1536 = 1.57MP（2:3 竖版，legacy 精确像素；多数场景建议用 --portrait）

常用精确尺寸（Lite 下，最低 2560×1440）：
- 2048×2048 = 4.19MP（1:1 方图）—— `--square`
- 2048×2732 = 5.59MP（3:4 竖版）—— `--portrait`
- 2560×1440 = 3.69MP（16:9 横版下限，刚好踩 pixel floor；不推荐，细节不足）
- 2732×1536 = 4.20MP（16:9 横版）—— `--landscape`
- 3072×3072 = 9.44MP（3K 方图）—— `--size 3K` server-picked

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

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "created": 1757321139,
  "data": [
    {
      "b64_json": "<base64 PNG bytes>",
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

| 字段 | 说明 |
|---|---|
| `data[].url` | `response_format=url` 时返回，24h 有效 |
| `data[].b64_json` | `response_format=b64_json` 时返回，base64 图片字节 |
| `data[].revised_prompt` | 模型改写后的 prompt（不一定有） |
| `data[].size` | 实际输出分辨率（精确 `WxH`） |
| `data[].output_format` | 实际输出格式 |
| `usage.generated_images` | 生成图片数（Pro 恒为 1） |
| `usage.input_images` | 输入参考图数（计费用，第一张免费，多的 ¥0.02/张） |
| `usage.output_tokens` | 图像 token 数（可用于近似计费） |
| `usage.total_tokens` | 总 token |

## Marker 编辑协议（客户端约定，不是 API 原生字段）

这是 Pro 的 headline 能力之一，也是本 skill 的 edit 子命令的默认路径。**API 本身没有 mask/bbox 参数**——Pro 的"区域编辑"完全靠"在参考图上画彩色标记 + prompt 自然语言描述该区域改动"实现，模型读取输入图像识别这些标记，执行局部改动后自动擦除标记。

### 协议步骤（本 skill 已自动化）

1. 用户通过 `--marker-rect X,Y,W,H`（可传多次）指定要编辑的矩形区域，支持像素坐标或百分比（如 `20%,10%,60%,25%`）。
2. 客户端用 Pillow 在参考图上绘制**半透明填充矩形 + 同色描边**（默认 `#ff0000` 红，fill alpha=80/255，stroke=3px）。
3. 可通过 `--marker-color #00ff00` 改色（多区域多色时，在 prompt 里分别说"红框内换 XX，蓝框内加 YY"）。
4. 保存 annotated 副本到输出目录供人检查（`*-annotated.png`），同时把 annotated 图作为 `image` 字段发送。
5. 客户端**自动在 prompt 末尾追加"擦除标记"指令**（中文/英文按 prompt 语言自动选择）：
   - 中文：`图中彩色方框/圆圈/涂写是我手工标出的编辑区域标记，请严格按上面的描述修改标记区域内的内容，标记区域之外的像素尽量保持不变，完成后清除所有彩色标记线条与填充。`
   - 英文：`The colored rectangles/circles/scribbles in the image are edit markers I drew by hand. Apply the change described above strictly inside the marked regions, keep pixels outside the markers unchanged, and remove all colored marks once done.`
6. `--no-marker-cleanup-prompt` 可关闭自动追加（高级用户想自写清理指令时用）。

### 已验证的典型 marker 场景（实测）

- ✅ 海报/封面**换标题文字**（同字体同字号同位置换字，周围像素保持）。
- ✅ 物体替换（把红框内沙发换成深蓝丝绒，茶几上加猫，周围光影不变）。
- ✅ 材质替换（金属雕塑变透明玻璃，保留反光结构）。
- ✅ 多区域多色（红框换字、蓝框加元素）。
- ❌ 目前 marker 只支持矩形；圆形/任意 scribble 需要手动预处理（用 Pillow 自己画）。

## Outpaint 协议（客户端画布扩展，不是 API 原生字段）

API 没有 `outpaint` 参数，真正的像素级 outpaint 通过客户端 trick 实现：

1. 用 `--outpaint <dir>:<pixels>`（多传多方向，如 `--outpaint left:400 --outpaint right:400`）指定要扩展的方向与像素。
2. 客户端把原图粘贴到更大的空白 canvas 中央，空白用图像边缘采样的中性色填充（避免硬接缝）。
3. 自动在 prompt 末尾追加中文/英文填充指令（"画布中央是原图片，请自然延伸填充四周的空白区域，使整张图变成一张完整的 [W×H/横版/竖版] 图片，延续原有风格、光照、色调与材质，不要让中心与新填充区域有可见接缝。"）。
4. 把扩展后的 canvas 作为 `image` 发送；模型填充扩展区域（中心大概率会被轻微重绘，不是 Photoshop 那种像素锁死的扩展，但对大部分文章配图场景够用）。

> 如果需要"中心像素一个不动"的严格 outpaint，需要配合局部 inpaint mask（Pro 当前公开 API 没有这个能力，要么等官方要么换栈）。

## 定价（截至 2026-07）

| 模型 | 单价 |
|---|---|
| Seedream 5.0 Pro，输出 ≤ 2.36MP | ¥0.30/张 |
| Seedream 5.0 Pro，输出 > 2.36MP | ¥0.60/张 |
| Pro 额外输入图（第 2 张起） | ¥0.02/张 |
| Seedream 5.0 Lite | ¥0.22/张（2K 档） |

RPM ≈ 500；本 skill 默认并发 3，且带 8 次指数退避（2/4/8/16/30/30/30/30s）并尊重 `retry-after` header，正常使用不会触发 429 熔断。

## Error Codes

| HTTP | Code | 说明 | Retry? |
|---|---|---|---|
| 400 | `InvalidParameter` / `BadRequest` | 参数错误（如 Pro 传了 web_search、size 超出范围、引用图损坏） | No |
| 401 | `AuthenticationError` | API Key 格式错误或过期 | No |
| 403 | `RequestForbidden` | 鉴权通过但无权限（模型未开通、欠费） | No |
| 429 | `RequestLimitExceeded` | 限流；尊重 `retry-after` header | **Yes** |
| 500 | `InternalError` | 服务端错误 | **Yes** |
| 502/503/504 | — | 网关/服务不可用 | **Yes** |

错误响应体：

```json
{ "error": { "code": "BadRequest", "message": "..." } }
```

## 为什么本 skill 默认用 `b64_json`

1. 省一次 HTTP hop（url 模式需要再 GET 一次图片，增加失败面与延迟）。
2. 没有 24h URL 过期问题——b64 立即解码写盘。
3. 体积 overhead 可接受（base64 比二进制大 33%，但 2K PNG 约 3–6MB，在本地 SSD 上毫无压力）。
4. Lite 默认还是 `url`（历史默认，且 Lite 主要用于快速批量迭代时可让用户自己处理 URL）。

## 本 skill 不做的事

- **不调 volcengine Python SDK**——只用 `httpx` 直连 REST，依赖最小、可审计、`uv run` 无额外安装成本。
- **不实现 ControlNet/深度图/姿态控制等外部控制手段**——公开 API 没暴露这些控制方式。
- **不做 pixel-perfect 图层分离**——官方营销里的"拆十余图层"是火山引擎客户端 UI 能力，未在 Ark 公开 API 提供。
- **不做 batch n>1 单次请求**——Pro 单次请求只出 1 张；批量用客户端并发（`generate-batch --concurrency N`）。
