# Image API quick reference (gpt-image-2)

This file is the canonical endpoint and parameter reference for the gpt-image-2 skill. All values below are verified against the OpenAI Image API reference and cookbook (2026/06).

## Official OpenAI references

- [GPT Image 2 model page](https://developers.openai.com/api/docs/models/gpt-image-2)
- [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation)
- [Images and vision guide](https://developers.openai.com/api/docs/guides/images-vision)
- [Python `images.generate` reference](https://developers.openai.com/api/reference/python/resources/images/methods/generate)
- [Python `images.edit` reference](https://developers.openai.com/api/reference/python/resources/images/methods/edit)
- [Python Images resource overview](https://developers.openai.com/api/reference/python/resources/images)
- [GPT Image prompting guide (cookbook)](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide)
- [Generate images with GPT Image (cookbook)](https://developers.openai.com/cookbook/examples/generate_images_with_gpt_image)

## Endpoints

- Generate: `POST /v1/images/generations` → `client.images.generate(...)`
- Edit: `POST /v1/images/edits` → `client.images.edit(...)`

GPT image models always return base64-encoded image bytes. There is no `response_format=url` option.

## Generate parameters

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `prompt` | string | required | Max 32000 characters for GPT image models. |
| `model` | string | `gpt-image-2` | The skill's default. Override with `--model`. |
| `n` | int | 1 | Range 1-10. |
| `size` | string | `auto` | Preset enum or `WIDTHxHEIGHT` string. See constraints below. |
| `quality` | enum | `auto` | `low`, `medium`, `high`, `auto`. Use `high` for text-heavy images. |
| `background` | enum | unset | `opaque`, `auto`, `transparent`. `transparent` is supported by the API but the official cookbook recommends `opaque` + a downstream `rembg` step for the cleanest transparent assets. When `transparent` is used, `output_format` must be `png` or `webp`. |
| `output_format` | enum | `png` | `png`, `jpeg`, `webp`. |
| `output_compression` | int | unset | 0-100. jpeg/webp only. |
| `moderation` | enum | `auto` | `auto`, `low`. |

### `size` constraints (gpt-image-2)

- Both edges must be multiples of 16.
- Aspect ratio (long:short) ≤ 3:1.
- Total pixels in [655,360, 8,294,400].
- Maximum edge length ≤ 3840px.
- Outputs > 2560x1440 are flagged experimental.

Standard enum values: `auto`, `1024x1024`, `1024x1536`, `1536x1024`, `1536x864`, `1024x1792`, `1792x1024`, `2048x2048`, `2048x1152`, `3840x2160`, `2160x3840`. Any `WIDTHxHEIGHT` string satisfying the constraints is also accepted.

## Edit parameters

Edit inherits all generate parameters except `background` semantics change (still supports `transparent` with the same caveat), plus:

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `image` | list[file] | required | Up to 16 images. Each must be PNG, WebP, or JPG and <50MB. Order matters — reference by index in the prompt. |
| `mask` | file | unset | PNG with alpha channel. <4MB. When multiple images are passed, the mask is applied to the first image. |
| `input_fidelity` | — | — | **Not supported on gpt-image-2.** Do not pass it. |

## Response

```json
{
  "created": 1717761600,
  "data": [
    {"b64_json": "<base64 PNG bytes>"}
  ]
}
```

`data[].b64_json` is the only image payload. The `revised_prompt` field that DALL·E used to return is not documented for GPT image models.

## Error discriminators

The OpenAI SDK raises typed exceptions. Branch on `error.code`:

| `error.code` | HTTP | Behavior | Skill action |
| --- | --- | --- | --- |
| `rate_limit_exceeded` (429) | 429 | Transient | Retry with backoff. |
| `5xx` server errors | 500-599 | Transient | Retry with backoff. |
| `image_generation_user_error` | 400 | User-correctable | Print message, do NOT retry. |
| `moderation_blocked` | 400 | Content moderation | Print `error.moderation_details.moderation_stage` and category hints. Do NOT retry. |

`moderation_blocked` errors may include `error.moderation_details` with:

- `moderation_stage`: `input` (prompt or reference triggered it) | `output` (generation triggered it) | `unknown`.
- `categories`: coarse hints like `harassment`, `self-harm`, `sexual`, `violence`. Use as debugging context, not as classifier truth.

## Streaming (not implemented in this skill)

The Image API guide documents `stream=true` + `partial_images` (0-3, each +100 output tokens), but the model overview page for gpt-image-2 marks "Streaming — Not supported". The skill does not implement streaming; the discrepancy is preserved as an open question.

## Limits

- Input images / masks for edit: <50MB each.
- Prompt length: ≤32000 characters.
- gpt-image-2 outputs up to 3840x2160 (experimental above 2560x1440).
