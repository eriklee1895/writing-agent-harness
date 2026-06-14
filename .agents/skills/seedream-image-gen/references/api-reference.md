# Seedream 5.0 API Reference

## 官方文档

| 文档 | 链接 |
|------|------|
| Seedream 4.0-5.0 教程 | https://www.volcengine.com/docs/82379/1824121?lang=zh |
| 模型列表 | https://www.volcengine.com/docs/82379/1330310?lang=zh |
| 模型价格 | https://www.volcengine.com/docs/82379/1544106?lang=zh |
| 提示词指南 | https://www.volcengine.com/docs/82379/1829186?lang=zh |
| 官方风格参考列表 | https://mathmind.feishu.cn/wiki/RDvjwA9zDiVmI4katfFcRo3bnbb |
| API Key 管理 | https://console.volcengine.com/ark/region:ark+cn-beijing/apikey |
| ARK_BASE_URL 参考 | https://github.com/bytedance/agentkit-samples/tree/main/skills/byted-seedream-image-generate |

## API Endpoint

```
POST https://ark.cn-beijing.volces.com/api/v3/images/generations
```

## Authentication

使用 Bearer Token，从环境变量 `ARK_API_KEY` 读取：

```
Authorization: Bearer <ARK_API_KEY>
```

`ARK_BASE_URL` 可覆盖 base URL，默认 `https://ark.cn-beijing.volces.com/api/v3`。

## 可用模型

| Version | Model ID |
|---------|----------|
| 5.0 (默认) | `doubao-seedream-5-0-260128` |
| 4.5 | `doubao-seedream-4-5-251128` |
| 4.0 | `doubao-seedream-4-0-250828` |

## Request Body

### 必填参数

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | 模型 ID |
| `prompt` | string | 文本描述。中文推荐 ≤300 字，英文推荐 ≤600 词 |

### 可选参数

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | string | `2048x2048` | `2K`/`3K`/`4K` 或 `WIDTHxHEIGHT`。range: [2560×1440=3686400, 4096×4096=16777216]，aspect ratio [1/16, 16] |
| `output_format` | string | — | `png` 或 `jpeg`（**5.0 only**） |
| `response_format` | string | — | `url` 或 `b64_json` |
| `watermark` | boolean | `true` | 是否包含水印 |
| `image` | string\|array | — | 参考图 URL 或 base64（`data:image/<fmt>;base64,<data>`），最多 14 张 |
| `sequential_image_generation` | string | — | 批量组图模式，`"auto"` 开启 |
| `sequential_image_generation_options` | object | — | `{"max_images": <1-15>}` |
| `tools` | array | — | `[{"type": "web_search"}]`（**5.0 only**） |
| `stream` | boolean | — | 流式响应（仅 4.0/4.5/5.0-lite） |
| `optimize_prompt_options` | object | — | `{"mode": "standard" \| "fast"}` |

### 参考图格式要求

- 格式: jpeg, png, webp, bmp, tiff, gif, heic, heif
- Aspect ratio: [1/16, 16]
- 单边 > 14px
- 大小 ≤ 30MB
- 总像素 ≤ 36,000,000 (6000×6000)
- 最多 14 张参考图

### Size 参数说明

**方式一：字符串分辨率**
- `2K`、`3K`、`4K` — 模型自动决定具体尺寸
- 在 prompt 中描述 aspect ratio、形状或用途

**方式二：精确像素**
- `WIDTHxHEIGHT` 格式
- 总像素范围: [3,686,400, 16,777,216]
- Aspect ratio 范围: [1/16, 16]
- 例如: `2048x2048`, `4096x4096`, `2560x1440`

## Response Format (200 OK)

```json
{
  "data": [
    {
      "url": "https://ark.cn-beijing.volces.com/.../result.png",
      "size": "2K"
    }
  ],
  "usage": {
    "generated_images": 1,
    "output_tokens": 1234,
    "total_tokens": 5678
  }
}
```

### 字段说明

| Field | Type | Description |
|-------|------|-------------|
| `data[].url` | string | 生成图片的下载 URL（有时效性） |
| `data[].b64_json` | string | Base64 编码的图片数据（需 `response_format=b64_json`） |
| `data[].revised_prompt` | string | 模型改写后的 prompt |
| `data[].size` | string | 实际输出尺寸 |
| `usage.generated_images` | integer | 成功生成的图片数 |
| `usage.output_tokens` | integer | 图片花费的 token 数 |
| `usage.total_tokens` | integer | 总 token 消耗 |
| `usage.tool_usage.web_search` | integer | 联网搜索调用次数 |

## Error Codes

| HTTP Status | Error Code | Description | Retry? |
|-------------|-----------|-------------|--------|
| 400 | `InvalidParameter` | 参数无效 | No |
| 400 | `BadRequest` | 请求格式错误 | No |
| 401 | `AuthenticationError` | API Key 格式错误或过期 | No |
| 403 | `RequestForbidden` | 请求被拒绝 | No |
| 429 | `RequestLimitExceeded` | 请求超限 | **Yes** |
| 500 | `InternalError` | 服务内部错误 | **Yes** |
| 503 | `ServiceUnavailable` | 服务不可用 | **Yes** |

Error response body:
```json
{
  "error": {
    "code": "BadRequest",
    "message": "The request failed because it is missing one or multiple required parameters."
  }
}
```

## Python SDK Reference (from volcenginesdkarkruntime)

```python
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.images.images import (
    SequentialImageGenerationOptions,
    OptimizePromptOptions,
)

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('ARK_API_KEY'),
)

imagesResponse = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="...",
    size="2K",
    sequential_image_generation="auto",
    sequential_image_generation_options=SequentialImageGenerationOptions(max_images=4),
    optimize_prompt_options=OptimizePromptOptions(mode="standard"),
    output_format="png",
    response_format="url",
    watermark=False,
)

for image in imagesResponse.data:
    print(image.url)
```

## 提示词通用公式

```
[风格锚点] + [主体 + 行为 + 环境] + [细节元素] + [色彩 + 光影 + 构图] + [分辨率/比例]
```

**公式拆解**:
- **风格锚点**: 如"超写实"、"中国古风写意"、"赛博朋克"、"宫崎骏风格"，放在 prompt 开头锁定风格方向
- **主体+行为+环境**: 自然语言描述画面内容
- **细节**: 具体物体、质感、氛围等
- **色彩+光影+构图**: 审美方向
- **分辨率/比例**: 如"4K"、"16:9"、"适合手机壁纸"

**中文提示词关键技巧**:
- 使用具象化名词（白墙黑瓦 > 古建筑），而非抽象形容词
- 始终在开头放一个风格锚点
- 用引号包裹画面中的文字内容
- 避免混合冲突风格（如"赛博朋克+水墨"）
