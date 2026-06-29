# Seedance 2.0 API 参考

> 最后核对：2026-06-29（火山方舟视频生成 API 官方文档，2026-06-25 更新轮次；关键事实经 live API 实测验证）。本页覆盖 4 个端点、3 条 2.0 模型线、完整请求/响应字段。

## 基础信息

| 项目 | 内容 |
|---|---|
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| 鉴权 | `Authorization: Bearer $ARK_API_KEY` |
| 调用方式 | 异步任务：创建后通过轮询或列表查询拿结果；支持配置 callback URL 接收完成回调 |
| 任务 ID 保留 | **7 天**（从 `created_at` 起算），超时后自动清除，无法再查询 |
| 视频 URL 保留 | **24 小时**，生成后必须立即下载到本地或转存 TOS |
| cancelled 任务保留 | 取消后任务记录 **24 小时** 自动删除（区别于 succeeded/failed 的 7 天） |

## 4 个端点总览

| # | 方法 | 路径 | 用途 | 官方文档 |
|---|---|---|---|---|
| 1 | `POST` | `/contents/generations/tasks` | 创建视频生成任务 | [1520757](https://www.volcengine.com/docs/82379/1520757) |
| 2 | `GET` | `/contents/generations/tasks/{id}` | 查询单个任务状态与结果 | [1521309](https://www.volcengine.com/docs/82379/1521309) |
| 3 | `GET` | `/contents/generations/tasks?page_num=...` | 查询任务列表（最近 7 天） | [1521675](https://www.volcengine.com/docs/82379/1521675) |
| 4 | `DELETE` | `/contents/generations/tasks/{id}` | 取消排队中的任务 / 删除已完成记录 | [1521720](https://www.volcengine.com/docs/82379/1521720) |

## 模型

本 skill 只支持 Seedance 2.0 系列，未来加新模型也只更新下表这一行。

| 模型 ID | 状态 | 最高分辨率 | 时长 | 能力 |
|---|---|---|---|---|
| `doubao-seedance-2-0-260128` | ✅ 标准 | **4k**（10-bit H.265/HEVC） | [4, 15] s / -1 | 文生 / 首帧 / 首尾帧 / 多模态参考 / 有声 / 编辑 / 延长 / 联网搜索 |
| `doubao-seedance-2-0-fast-260128` | ✅ 快速 | 720p | [4, 15] s / -1 | 同上，更快更便宜；实测 token 用量 ~40% |
| `doubao-seedance-2-0-mini-260615` | ✅ 正式（2026-06-25 GA） | 720p | [4, 15] s / -1 | 同上，成本最低；适合大规模批量 |

> 模型 ID 内嵌的 `260128` / `260615` 是模型**构建日期**（YYMMDD），不是 GA 日期。Mini 模型 2026-06-15 构建，2026-06-15 ~ 06-24 仅控制台体验中心可试，2026-06-25 起 API 全量可调。

> 三个 2.0 模型**都不支持**入参 `frames` / `seed` / `draft` / `service_tier="flex"` / `camera_fixed`。这些字段存在 API 文档里但 2.0 系列不接受，传了会被拒（实测传 `frames` 返回 400 `InvalidParameter: the specified parameter frames is not supported`）。注意：`seed` 作为入参不支持（无法主动复现），但响应中**会返回**服务端随机种子值（实测 `seed=97146`），仅供 traceability。

### 4k 分辨率特殊说明

- 仅 `doubao-seedance-2-0-260128` 标准版支持。
- 编码为 **10-bit H.265/HEVC**。
- **并发上限 1**（普通 720p/1080p 实测并发 20），**RPM 15**。生成等待时间显著长于 1080p。
- 像素尺寸：16:9 = 3840×2160；4:3 = 3326×2494；1:1 = 2880×2880；3:4 = 2494×3326；9:16 = 2160×3840；21:9 = 4398×1886。

---

## 1) `POST /contents/generations/tasks` — 创建任务

### 请求参数（Body）

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `model` | string | ✅ | 模型 ID 或 Endpoint ID |
| `content` | object[] | ✅ | 多模态输入数组（见下表） |
| `duration` | int | ❌ | 时长秒数，默认 `5`；或 `-1` 让模型自适应（整数秒） |
| `ratio` | string | ❌ | `21:9`/`16:9`/`4:3`/`1:1`/`3:4`/`9:16`/`adaptive`；**默认 `16:9`**（实测省略时 API 返回 16:9；官方文档标注 `adaptive` 与实测不符。脚本 argparse 默认也是 `16:9`） |
| `resolution` | string | ❌ | `480p`/`720p`/`1080p`/`4k`（1080p 起仅标准版；4k 仅标准版）；**默认 `720p`**（实测省略时 API 返回 720p） |
| `generate_audio` | bool | ❌ | 是否生成音频；官方未明文给出 API 默认值，脚本默认 `true` 并显式传入；输出音频为**单声道 mono** |
| **input size** | — | — | **输入参考素材**体积上限：图片 ≤ 30 MB、**视频 ≤ 200 MB**、音频 ≤ 15 MB；请求体 base64 后 ≤ 64 MB（脚本 hard-fail 在 60 MB）。**这是输入限制，不是输出 video 体积限制** |
| `watermark` | bool | ❌ | 是否加水印，默认 `false` |
| `return_last_frame` | bool | ❌ | 返回尾帧图 URL，用于链式续写；尾帧格式 png，无水印，宽高同视频 |
| `priority` | int | ❌ | 任务优先级（`0-9`），数值越大越靠前（仅同 Endpoint 内 FIFO 排序） |
| `tools` | object[] | ❌ | 工具调用，目前仅支持 `[{"type": "web_search"}]`（联网搜索）；**仅纯文本输入可用**；由模型自主决定是否真的调用（可能 0 次），会增加延迟 |
| `safety_identifier` | string | ❌ | 终端用户唯一标识符（≤ 64 char，推荐传 hash 后的用户 ID/邮箱），用于平台滥用检测；若设置，查询接口会原样回显。单用户写作场景通常不需要传 |
| `callback_url` | string | ❌ | 任务完成后的 HTTP 回调地址（Webhook）；脚本暂未暴露该参数 |

> **Seedance 2.0 系列入参不接受**：`frames`、`seed`、`camera_fixed`、`service_tier="flex"`、`draft`。这些字段存在 API 文档里但 2.0 系列不接受，传了会被拒（实测传 `frames` 返回 400）。注意：`seed` 不能作为入参，但响应里会回传服务端使用的种子值（read-only，无法回填；实测 `seed=97146`）。

### `content[]` 项类型

每项必须包含 `type`，并匹配对应字段：

| `type` | 必填字段 | 可选 `role` | 说明 |
|---|---|---|---|
| `text` | `text` | — | 文本提示词 |
| `image_url` | `image_url.url` | `first_frame` / `last_frame` / `reference_image` | 图生视频或多模态参考 |
| `video_url` | `video_url.url` | `reference_video` | 视频参考 |
| `audio_url` | `audio_url.url` | `reference_audio` | 音频参考 |

### 生成模式组合

| 模式 | content 组合 |
|---|---|
| 文生视频 | 1 个 `text` |
| 首帧图生视频 | `text`（可选）+ 1 个 `image_url`（`first_frame`） |
| 首尾帧 | `text`（可选）+ 2 个 `image_url`（`first_frame` + `last_frame`） |
| 多模态参考 | `text` + 0–9 图 + 0–3 视频 + 0–3 音频（至少 1 图或 1 视频） |

> ⚠️ 首尾帧/首帧模式与多模态参考模式**互斥**，不能在一次请求中混用 `first_frame`/`last_frame` 与 `reference_*`。

### 工具调用（联网搜索）

| 配置 | 说明 |
|---|---|
| 启用 | `"tools": [{"type": "web_search"}]` |
| 限制 | **仅纯文本输入**（content 只能有 1 个 `text`） |
| 适用场景 | 提示词要引用当前事件、最新数据、新闻、股价等模型权重之外的信息 |
| 计费 | 按 `usage.tool_usage.web_search` 次数计费；脚本里用 `--enable-web-search` 开启 |

⚠️ 脚本会在 client 侧硬拦截：开启 web_search 时如果传 `--first-frame` / `--reference-*` 等多模态内容，会直接报错。

### 分辨率 × 比例 × 模型宽高像素表

| 分辨率 | 比例 | Seedance 2.0 宽高像素 |
|---|---|---|
| **480p** | 16:9 | 864×496 |
| | 4:3 | 752×560 |
| | 1:1 | 640×640 |
| | 3:4 | 560×752 |
| | 9:16 | 496×864 |
| | 21:9 | 992×432 |
| **720p** | 16:9 | 1280×720 |
| | 4:3 | 1112×834 |
| | 1:1 | 960×960 |
| | 3:4 | 834×1112 |
| | 9:16 | 720×1280 |
| | 21:9 | 1470×630 |
| **1080p** ⚠️ Fast/Mini 不支持 | 16:9 | 1920×1080 |
| | 4:3 | 1664×1248 |
| | 1:1 | 1440×1440 |
| | 3:4 | 1248×1664 |
| | 9:16 | 1080×1920 |
| | 21:9 | 2206×946 |
| **4k** ⚠️ 仅标准版；10-bit H.265/HEVC；并发 1、RPM 15 | 16:9 | 3840×2160 |
| | 4:3 | 3326×2494 |
| | 1:1 | 2880×2880 |
| | 3:4 | 2494×3326 |
| | 9:16 | 2160×3840 |
| | 21:9 | 4398×1886 |

### 响应（创建）

```json
{
  "id": "cgt-20260606160057-6bbjd"
}
```



---

## 2) `GET /contents/generations/tasks/{id}` — 查询单个任务

### 响应

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 任务 ID，**仅保留 7 天**（从 `created_at` 起算） |
| `model` | string | 实际使用的模型 |
| `status` | string | 任务状态（见下表） |
| `content.video_url` | string | 视频 URL，**24 小时有效** |
| `content.last_frame_url` | string | 尾帧图 URL（仅当 `return_last_frame:true`） |
| `seed` | int | 本次任务实际使用的随机种子值；**2.0 系列只读返回**，无法作为入参回填复现 |
| `usage.completion_tokens` | int | 计费 token 数；2.0 系列存在最低 token 用量限制，实际低于最低值时按最低值返回并计费 |
| `usage.total_tokens` | int | 总 token 数 |
| `usage.tool_usage.web_search` | int | 实际联网搜索次数（仅开启联网搜索时） |
| `tools[]` | object[] | 本次任务模型实际调用的工具；未调用时不返回；目前仅 `type="web_search"` |
| `service_tier` | string | 实际处理任务使用的服务等级；2.0 系列固定 `"default"` |
| `safety_identifier` | string | 终端用户唯一标识符；仅当创建任务时传入了该字段才回显 |
| `error` | object/null | 失败时的 `{code, message}` |
| `created_at` | int | 任务创建时间（Unix 秒） |
| `updated_at` | int | 状态更新时间（Unix 秒） |
| `resolution` | string | 实际分辨率 |
| `ratio` | string | 实际比例 |
| `duration` | int | 实际时长秒 |
| `framespersecond` | int | 帧率（24） |
| `execution_expires_after` | int | 任务执行超时秒数（默认 172800=48h，可配范围 3600-259200=1h~72h，超时进入 `expired` 状态） |
| `generate_audio` | bool | 是否生成音频；**仅 `doubao-seedance-2-0-260128` 与 `-fast-260128` 在响应中回显**；`mini-260615` 即使生成有声视频也不回显该字段 |
| `priority` | int | 优先级 |

```json
{
  "id": "cgt-2026****-****",
  "model": "doubao-seedance-2-0-260128",
  "status": "succeeded",
  "content": {
    "video_url": "https://ark-content-generation-cn-beijing.tos-cn-beijing.volces.com/xxx",
    "last_frame_url": "https://ark-content-generation-cn-beijing.tos-cn-beijing.volces.com/last.jpg"
  },
  "seed": 78674,
  "usage": { "completion_tokens": 108900, "total_tokens": 108900 },
  "service_tier": "default",
  "created_at": 1779348818,
  "updated_at": 1779348874,
  "resolution": "720p",
  "ratio": "16:9",
  "duration": 5,
  "framespersecond": 24,
  "execution_expires_after": 172800,
  "generate_audio": true,
  "priority": 0
}
```

---

## 3) `GET /contents/generations/tasks?page_num=...` — 查询任务列表

### Query 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page_num` | int | ❌ | 页码，默认 1，范围 [1, 500] |
| `page_size` | int | ❌ | 每页数量，默认 20，范围 [1, 500] |
| `filter.status` | string | ❌ | `queued`/`running`/`cancelled`/`succeeded`/`failed`/`expired` |
| `filter.task_ids` | string[] | ❌ | 多个任务 ID 精确搜索，重复参数名 |
| `filter.model` | string | ❌ | 模型精确搜索 |
| `filter.service_tier` | string | ❌ | 默认 `default`；取值 `default`/`flex`。2.0 系列入参不支持 `flex`，但此 filter 仍可用于按服务等级筛选历史任务 |

### 限制

> **仅能查询最近 7 天的任务记录**，时间区间 `[T-7天, T)`，T 为请求 UTC 时间戳（精确到秒）。视频 URL 24 小时有效，请及时下载或转存。

### 响应顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `total` | int | 符合筛选条件的任务总数（用于分页计算：`total_pages = ceil(total / page_size)`） |
| `items` | object[] | 任务记录数组，字段集与单任务查询一致 |

### 响应 items[] 字段

与单任务查询响应一致：`id, model, status, error, created_at, updated_at, content{video_url, last_frame_url}, seed, usage, tools[], service_tier, safety_identifier, resolution, ratio, duration, framespersecond, execution_expires_after, generate_audio, priority`。Seedance 2.0 系列**会返回 `seed`**（只读，无法作为入参回填）；不返回 `revised_prompt`。

---

## 4) `DELETE /contents/generations/tasks/{id}` — 取消 / 删除

无请求体，按当前状态执行不同操作：

| 当前状态 | DELETE 行为 | 操作后状态 |
|---|---|---|
| `queued` | 取消排队 | `cancelled` |
| `running` | ❌ 不支持 | - |
| `succeeded` / `failed` / `expired` | 删除任务记录 | -（后续无法查询） |
| `cancelled` | ❌ 不支持 | - |

成功后返回**空 JSON 对象 `{}`**（HTTP 200，无字段）；脚本按 JSON 解析，不要按空 body 处理。

---

## 任务状态机

| 状态 | 含义 |
|---|---|
| `queued` | 排队中 |
| `running` | 生成中 |
| `succeeded` / `completed` | 成功（官方文档两词混用） |
| `failed` | 失败（看 `error` 字段） |
| `cancelled` | 已被 DELETE 取消 |
| `expired` | 超时（任务执行超过 `execution_expires_after`） |

---

## 错误码

| HTTP 状态 | 含义 | 处理 |
|---|---|---|
| `400` | 参数错误 | 检查模型/分辨率/时长/比例组合、是否同时混用 `first_frame` 与 `reference_*`、是否传了 2.0 入参不接受的字段（`frames`/`seed`/`draft`/`camera_fixed`/`service_tier="flex"`） |
| `401` | API Key 无效 | 检查 `ARK_API_KEY` 是否正确 |
| `403` | 内容审核拦截 | 检查是否含真实人脸、违规内容 |
| `404` | 任务 ID 不存在或已过 7 天 | 用 `list-tasks` 找最近 7 天的任务 |
| `429` | 限流或余额不足 | 降低频率或充值 |
| `500` / `502` / `503` / `504` | 服务端错误 | 脚本已自动指数退避重试 3 次；终态失败看 `manifest.json` |

---

## 计费

- 按 token 计费：`费用 = token 单价 × usage.completion_tokens`
- 约 **1 元/秒（1080p）**，具体以控制台账单为准
- 提交时预扣，完成后多退少补；参数错误被拒不计费
- **Seedance 2.0 系列存在最低 token 用量限制**：若实际 token 用量低于最低值，按最低值计费
- 视频 URL **24 小时有效**，生成后必须立即下载；推荐配置 TOS 数据订阅自动转存
- 实测 token 用量（同一参数下稳定）：
  - Fast 4s 480p：**40,594 tokens**
  - Standard 5s 720p：**108,900 tokens**

---

## 实现说明

### REST 直调 vs volcengine-python-sdk

本 skill 走 **httpx 直调 4 端点**，没用官方 `volcengine-python-sdk[ark]`。决策和权衡：

| 维度 | httpx 直调（本 skill）| volcengine-python-sdk |
|---|---|---|
| 依赖体积 | 极小（只 `httpx>=0.28.0`）| 较重（含 OpenAI 兼容层、流式等无关能力）|
| 4 端点维护 | 30 行直白代码 | 0 行（SDK 维护）|
| 重试 / 退避 | 自己写（指数退避 + Retry-After 解析），透明可调 | SDK 内部，行为不直观 |
| 参数/响应字段 | 100% 透传 API（包括 `web_search` tool usage）| SDK 包装一层，新字段要等 SDK 升级 |
| 流式 | 不需要（视频生成是异步，无流式） | 过度设计 |

**结论**：视频生成 API 是 4 个稳定的 REST 端点 + 异步轮询，没有流式（Tool Use 只用于 `web_search` 且已自行处理），**SDK 的额外能力 0 价值、依赖成本 100%**。如果哪天官方推流式生成再切换。

### manifest.json 字段约定

每次任务成功后写 `manifest.json`，便于事后追溯和自动化处理：

| 字段 | 来源 | 用途 |
|---|---|---|
| `task_id` | API 响应 | 后续 poll / cancel / 下载 唯一 ID |
| `status` | API 响应 | `succeeded` / `failed` / `cancelled` / `expired` / `queued` / `running` |
| `model` / `ratio` / `duration` / `resolution` | API 响应（echo）| 记录实际生效参数（与请求可能不同）|
| `seed` | API 响应 | 服务端随机种子（2.0 实测返回，仅供追溯，不能回填入参复现）|
| `service_tier` | API 响应 | 实际服务等级（2.0 固定 `default`）|
| `usage.completion_tokens` | API 响应 | 计费 token 数（用于成本估算；2.0 有最低用量下限）|
| `usage.tool_usage.web_search` | API 响应 | 联网搜索实际调用次数（开启 web_search 时）|
| `video_url` | API 响应 | 24h 有效，本脚本已自动下载到 `video.mp4` |
| `last_frame_url` | API 响应 | 仅当 `return_last_frame:true` |
| `framespersecond` / `execution_expires_after` / `priority` | API 响应 | 帧率（24）/ 执行超时秒数 / 优先级 |
| `task_created_at` / `task_updated_at` | API 响应 | 任务创建 / 状态更新时间（Unix 秒）|
| `error` | API 响应 | 任务失败时的 `{code, message}` |
| `request_payload` | 本地构造 | 用户实际请求的 payload，方便重放 |
| `created_at` | 本地 | manifest 写入时间（ISO 8601）|
| `output_files` | 本地 | 实际下载的 video / last_frame 路径 |

> 响应中的 `tools[]` / `safety_identifier` 是 API 字段但**未写入 manifest**（仅开启 web_search / 传入 safety_identifier 时才有意义）；需要时直接调 `poll` 或 GET `/tasks/{id}` 查看原始响应。

> 想调试「为什么生成结果和我想的不一样」：优先对比你原始 prompt 与生成视频的实际画面，结合 `references/prompt-guide.md` 的公式排查（主体描写是否前置、运镜是否清晰、约束是否到位）。Seedance 2.0 不返回 `revised_prompt`，但 `seed` 已写入 manifest，可事后追溯哪次随机种子产出了哪段视频。

## 来源

- 视频生成 API 入口: https://www.volcengine.com/docs/82379/1520758
- 创建任务: https://www.volcengine.com/docs/82379/1520757
- 查询单任务: https://www.volcengine.com/docs/82379/1521309
- 查询任务列表: https://www.volcengine.com/docs/82379/1521675
- 取消/删除任务: https://www.volcengine.com/docs/82379/1521720
- Seedance 2.0 系列教程: https://www.volcengine.com/docs/82379/2291680
- Seedance 2.0 系列提示词指南: https://www.volcengine.com/docs/82379/2222480
- 视频生成教程: https://www.volcengine.com/docs/82379/2298881
