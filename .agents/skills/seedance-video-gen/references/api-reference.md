# Seedance 2.0 API 参考

## 基础信息

| 项目 | 内容 |
|---|---|
| 默认 Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| 创建任务 | `POST /contents/generations/tasks` |
| 查询任务 | `GET /contents/generations/tasks/{id}` |
| 认证 | `Authorization: Bearer $ARK_API_KEY` |
| 调用方式 | 异步任务，创建后需轮询 |

## 模型

| 模型 ID | 说明 |
|---|---|
| `doubao-seedance-2-0-260128` | 标准版，支持 1080p、首尾帧、编辑 |
| `doubao-seedance-2-0-fast-260128` | 快速版，最高 720p，生成更快、成本更低 |

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `model` | string | 是 | 模型 ID |
| `content` | array | 是 | 多模态输入数组 |
| `duration` | int | 否 | 4–15 秒，或 `-1` 自适应，默认 5 |
| `ratio` | string | 否 | `16:9`、`4:3`、`1:1`、`3:4`、`9:16`、`21:9`、`adaptive` |
| `resolution` | string | 否 | `480p`、`720p`、`1080p`（1080p 仅标准版） |
| `generate_audio` | bool | 否 | 是否生成/使用音频，默认 `true` |
| `watermark` | bool | 否 | 是否添加水印，默认 `false` |
| `return_last_frame` | bool | 否 | 成功后是否返回最后一帧图 URL |
| `seed` | int | 否 | 随机种子，`-1` 表示随机 |

## `content` 数组

每项必须包含 `type`，并匹配对应字段：

| `type` | 必填字段 | 可选 `role` |
|---|---|---|
| `text` | `text` | — |
| `image_url` | `image_url.url` | `first_frame`、`last_frame`、`reference_image` |
| `video_url` | `video_url.url` | `reference_video` |
| `audio_url` | `audio_url.url` | `reference_audio` |

### 生成模式

| 模式 | content 组合 |
|---|---|
| 文生视频 | 1 个 `text` |
| 首帧图生视频 | `text`（可选）+ 1 个 `image_url`（`first_frame`） |
| 首尾帧 | `text`（可选）+ 2 个 `image_url`（`first_frame` + `last_frame`） |
| 多模态参考 | `text` + 0–9 图 + 0–3 视频 + 0–3 音频（至少 1 图或 1 视频） |

**注意**：首尾帧/首帧模式与多模态参考模式互斥，不能混用 `first_frame`/`last_frame` 与 `reference_*`。

## 响应示例

### 创建成功

```json
{
  "id": "cgt-20260606160057-6bbjd"
}
```

### 查询成功

```json
{
  "id": "cgt-20260606160057-6bbjd",
  "model": "doubao-seedance-2-0-260128",
  "status": "succeeded",
  "ratio": "16:9",
  "duration": 5,
  "resolution": "720p",
  "content": {
    "video_url": "https://example.com/generated-video.mp4",
    "last_frame_url": "https://example.com/last-frame.jpg"
  },
  "usage": {
    "completion_tokens": 87300,
    "total_tokens": 87300
  }
}
```

## 任务状态

| 状态 | 含义 |
|---|---|
| `queued` | 排队中 |
| `running` | 生成中 |
| `succeeded` / `completed` | 成功 |
| `failed` | 失败 |
| `expired` | 过期 |

## 错误码

| HTTP 状态 | 含义 | 处理 |
|---|---|---|
| `400` | 参数错误 | 检查模型/分辨率/时长/比例组合 |
| `401` | API Key 无效 | 检查 `ARK_API_KEY` |
| `403` | 内容审核拦截 | 检查是否含人脸、违规内容 |
| `429` | 限流或余额不足 | 降低频率或充值 |
| `500` | 服务端错误 | 稍后重试 |

## 计费

- 按 token 计费：`费用 = token 单价 × usage.completion_tokens`。
- 约 1 元/秒（1080p），具体以控制台账单为准。
- 提交时预扣，完成后多退少补；参数错误被拒不计费。
- 视频 URL 通常 24 小时有效，生成后尽快下载。

## 来源

- [火山方舟视频生成 API 参考](https://www.volcengine.com/docs/82379/1520758)
- [Doubao Seedance 2.0 系列教程](https://www.volcengine.com/docs/82379/2291680)
- [Doubao Seedance 2.0 系列提示词指南](https://www.volcengine.com/docs/82379/2222480)
- [视频生成教程](https://www.volcengine.com/docs/82379/2298881)
