# Volcengine TTS API Reference

Official documentation links and error code reference for the Doubao Speech Synthesis Model 2.0 (seed-tts-2.0).

## Official Docs

| Document | URL |
|----------|-----|
| HTTP 单向流式语音合成 (API reference) | https://www.volcengine.com/docs/6561/2528925 |
| WebSocket 双向流式语音合成 | https://www.volcengine.com/docs/6561/2532486 |
| WebSocket 单向流式-V3 | https://www.volcengine.com/docs/6561/1719100 |
| 异步长文本接口文档 | https://www.volcengine.com/docs/6561/1829010 |
| 模型列表 | https://www.volcengine.com/docs/6561/2499930 |
| 音色列表 (seed-tts-2.0) | https://www.volcengine.com/docs/6561/1257544 |
| SSML 标记语言 | https://www.volcengine.com/docs/6561/1330194 |
| 错误码查询 | https://www.volcengine.com/docs/6561/2534853 |
| 语音指令与标签 | https://www.volcengine.com/docs/6561/1871062 |
| API Key 使用 | https://www.volcengine.com/docs/6561/1816214 |
| 产品简介 | https://www.volcengine.com/docs/6561/163032 |

## TTS V3 HTTP Unidirectional Error Codes

These are the error codes returned by the `POST /api/v3/tts/unidirectional` endpoint.

### Client Errors (4xxxxxxx)

| Code | Message Pattern | Meaning | Action |
|------|----------------|---------|--------|
| `45000000` | `payload unmarshal` | Invalid JSON payload | Fix the JSON structure |
| `45000000` | `quota exceeded for types: concurrency` | Rate limit / concurrency exceeded | Reduce `--concurrency`, wait, or purchase more concurrency |
| `45000000` | `single request size too large` | Payload too large | Shorten the text |
| `45000001` | `[Invalid argument] EmptyRequest` | Missing `req_params` field | Ensure request body has `req_params` |
| `45000001` | `[Invalid argument] speaker not found` | Invalid speaker ID | Check speaker ID spelling, use `--list-speakers` |
| `45000001` | `[Invalid argument] InvalidModel` | Invalid model param | Only set `--model` when using cloned (ICL) voices (e.g. `seed-tts-2.0-standard`). For public `_bigtts` voices, omit it. |
| `45000001` | `[Invalid argument] InvalidDialect` | Invalid dialect param | Check dialect value |
| `45002000` | `TTS invalid speaker` | Empty speaker parameter | Provide a speaker ID |
| `45002001` | `No readable text!` | No readable text content | Check the input text |

### Server Errors (55000000) — Retryable

| Code | Message Pattern | Meaning | Action |
|------|----------------|---------|--------|
| `55000000` | Service internal error | Generic server error | Retry with backoff |
| `55000000` | `connect downstream service timeout` | Gateway timeout to TTS service | Retry with backoff |
| `55000000` | `synthesis processing timeout` | TTS processing timeout (text too long or high load) | Shorten text or retry later |
| `55000000` | `client send timeout` | WebSocket idle timeout (not applicable to HTTP) | N/A for HTTP mode |
| `55000000` | `resource ID is mismatched with speaker` | Speaker not found for this resource ID | Check speaker exists for `seed-tts-2.0` |

### Retry Strategy

Our script retries **3 times** with exponential backoff (1s → 2s → 4s) on:
- HTTP status: 429, 500, 502, 503, 504
- Volcano code: `55000000` (all variants)

Non-retryable errors (all `4xxxxxxx` except rate-limit variants) are returned immediately with the error message and `log_id`.

### Debugging

Always include the `log_id` from the error response when contacting Volcengine support. The log ID is returned in both the `X-Tt-Logid` response header and the JSON error output.

## Request Headers

| Header | Required | Value |
|--------|----------|-------|
| `X-Api-Key` | Yes | Your API key from [console](https://console.volcengine.com/speech/new/setting/apikeys) |
| `X-Api-Resource-Id` | Yes | `seed-tts-2.0` |
| `X-Api-Request-Id` | Yes | UUID string |
| `X-Control-Require-Usage-Tokens-Return` | No | Set to `*` to get `text_words` in response |
| `Content-Type` | Yes | `application/json` |
| `Connection` | Yes | `keep-alive` |
