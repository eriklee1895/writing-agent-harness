# BigMusic / Seed-Music — API 参考链接

火山引擎「音视频理解与处理 → AI 音乐生成大模型」官方文档。本 skill 调用
`GenBGMForTime`（按时长计费）提交 + `QuerySong` 轮询。

## 接口

| 主题 | 链接 |
| --- | --- |
| 生成纯音乐（本 skill 主接口，doc 含两个 Action） | https://www.volcengine.com/docs/84992/2100970 |
| 查询任务（Action=`QuerySong`，轮询 TaskID 拿 AudioUrl） | https://www.volcengine.com/docs/84992/2100960 |
| 异步回调 | https://www.volcengine.com/docs/84992/2100987 |
| 鉴权公共字段（Signature V4） | https://www.volcengine.com/docs/84992/1967910 |
| 常见错误码 | https://www.volcengine.com/docs/84992/1404675 |
| 曲风/可选参数（v5.0 不再需要） | https://www.volcengine.com/docs/84992/2097647 |

## 关键参数（实测确认）

- **Endpoint（提交）**：`https://open.volcengineapi.com/?Action=GenBGMForTime&Version=2024-08-12`
- **Endpoint（轮询）**：`https://open.volcengineapi.com/?Action=QuerySong&Version=2024-08-12`
- **service** = `imagination`，**region** = `cn-beijing`
- 音乐模型 `Version` = `v5.0`（`v1.0~v4.0` 返 `InvalidRequestParams`；旧 `GenSong/GenLyrics` 已废弃）
- 提交 `Duration` ∈ **[30, 120]** 秒；推荐 ≥ 60 避免版权校验
- v5.0 不再支持 `Genre/Mood/Instrument/Theme` 结构化枚举，**风格完全由中文 Text 驱动**
- 鉴权：Volc Signature V4（HMAC-SHA256），AK=`VOLC_ACCESSKEY`，SK=`VOLC_SECRETKEY`
- 提交返回 `Result.TaskID`；**轮询是异步的**，同步文档说"PredictedWaitTime 0 秒"是错的，实测要等 15-25s
- 轮询响应 `Status`：`0` 等待 / `1` 处理中 / `2` 成功 / `3` 失败
- 成功时音频 URL 在 `Result.SongDetail.AudioUrl`，临时签名 URL 有效期 **1 年**（官方原话）
- 真实格式是 **WAV**（PCM 16bit / 44.1kHz / stereo），`Content-Type: video/mp4` 是抖音 vod 默认头，**不要信**

## 关于"两个 Action 入口"

官方文档里只列了一个生成纯音乐入口，但请求参数表里 Action 字段被写成
"预付费：`GenBGM` / 后付费：`GenBGMForTime`"——同一服务，**两套计费入口**。
**入口不互通**：调错 Action 会被服务端以 `200028 APINoSource`（"没有可用
资源包"）拒掉，**与是否开通服务无关**。

Erik 账号是「按时长计费」开通，本 skill **写死 `GenBGMForTime`**，不再暴露
`GenBGM`（套餐包）入口。`scripts/generate_bgm.py` 顶部常量 `SUBMIT_ACTION`
是唯一的提交入口。

## 错误码（节选 + 实测解释）

| Code | Message | 含义 / 触发条件 |
| --- | --- | --- |
| `0` | Success | 正常 |
| `100001` | InternalError | 服务端内部错误（参数类型/枚举非法，或误用废弃接口） |
| `100010` | InvalidRequestParams | Duration 越界 / Version 非法 / 枚举值非法 |
| `100011` | ServerIpLimit | 海外 IP 限制 |
| `100013` | AuthFailed | AK/SK 错或过期 |
| `200020` | InvalidSign | 签名无效（区分主账号/子账号） |
| `200021` | AuthExpired | 授权过期 |
| `200022` | APIOutOfLimit | 资源包用完（套餐包账号场景） |
| `200023` | APIOutOfQps | 超过 QPS |
| `200024` | AuthDisable | 账号音乐功能被禁用 |
| `200026` | TosBucketLimit | 自建 TOS 桶名无效（我们不传，跳过） |
| `200027` | APIOutOfTime | 资源包过期（套餐包账号场景） |
| `200028` | **APINoSource** | **"没有可用资源包"**：Action 与计费方式不匹配，或「按时长计费」开关没在控制台勾上。**与"是否开通服务"无关**。 |
| `300030` | AlgorithmError | 算法错误，子类型 `50000001` 是相似度校验失败 |
| `300052` | TaskNotFound | TaskID 错或过期清理 |
| `400040` | QueueFull | 队列满，退避重试 |
| `429` | RateLimited | 触发限流 |
| `50000001` | **MusicSimilarityDetectionNotPassed** | 版权/相似度校验失败；通过丰富 Text + `--rewrite` + 换风格规避 |

## TosBucket

- 接口里 `TosBucket` 是**可选**字段（请求表里写"否"）
- **不传即可**：服务端复用共享桶 `tos-cn-v-*`（实测 `v3-default.douyinvod.com` / `v6-default...`），通过 URL query 里的 `l=` 签名参数保护，1 年有效
- **AIGC 即取即用场景完全不需要自建桶**；自建桶仅在「想永久归档到自家存储 / 想自定义路径 / 想避开 1 年签名过期」时才有意义

## 鉴权

Signature V4 流程：HMAC-SHA256 链 `secret → date → region → service → request`，
签 `string-to-sign = "HMAC-SHA256\n<X-Date>\n<credential_scope>\n<sha256(canonical_request)>"`。
`Authorization` header 形如 `HMAC-SHA256 Credential=<ak>/<scope>, SignedHeaders=host;x-content-sha256;x-date, Signature=<sig>`。

详见 SKILL.md 同目录 `scripts/generate_bgm.py:sign_and_post()` 的实现。
