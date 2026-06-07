# OpenAI Image Workflow

## Use this file when

- You need to understand how the script authenticates
- You need to understand how `text-only` and `reference+text` requests are normalized
- You need to debug request construction or output saving

## Authentication

- Read `OPENAI_API_KEY` from the current shell environment first.
- Read `OPENAI_BASE_URL` from the current shell environment second.
- If `OPENAI_API_KEY` is missing and the script is attached to a TTY, prompt securely for a temporary key.
- If `OPENAI_API_KEY` is missing and the script is not attached to a TTY, fail with a clear `export OPENAI_API_KEY=...` example.
- Do not write credentials to disk.
- Do not modify `~/.zshrc` or any `.env` file automatically.

## Provider-safe defaults

- Default `size` to `auto` for best compatibility across OpenAI-compatible gateways.
- Default `quality` to `auto` so the provider can choose the best supported fidelity.
- Offer an explicit `doc-hd` preset that resolves to `1536x1024` for landscape document illustrations.
- Offer `doc-2k` -> `2048x1152` and `doc-4k` -> `3840x2160` for higher-resolution document illustrations.
- Do not send unsupported custom sizes such as `1024x768` to the Images API.

## Provider-specific model mapping

- Official OpenAI base URL: use `gpt-image-2`
- `https://aihubmix.com/v1`: use `gpt-image-2`
- `https://api.ofox.ai/v1`: use `openai/gpt-image-2`
- Unknown providers: default to `gpt-image-2` unless the provider documents a namespaced variant

## Request modes

### `text-only`

- Build the illustration from the normalized brief only.
- Use the selected style profile or the default `flat-tech-infographic`.
- Prefer document-friendly landscape composition unless the caller overrides size.
- Call `client.images.generate(model="gpt-image-2", ...)`.

### `reference+text`

- Treat reference images as style guidance, not literal content to reproduce.
- Extract and preserve style-level qualities:
  - palette
  - line weight
  - icon treatment
  - spacing
  - container shape
  - annotation density
- Keep the user’s requested subject matter primary.
- Call `client.images.edit(model="gpt-image-2", image=[...], prompt=...)`.

### `dry-run`

- Build the exact prompt and request payload summary.
- Skip live API calls.
- Allow dry-run to succeed even when `OPENAI_API_KEY` is missing.

## Official OpenAI docs to consult

- Model page: `https://developers.openai.com/api/docs/models/gpt-image-2`
- Image generation guide: `https://developers.openai.com/api/docs/guides/image-generation`
- Images and vision guide: `https://developers.openai.com/api/docs/guides/images-vision`
- Python create image reference: `https://developers.openai.com/api/reference/python/resources/images/methods/generate`
- Python image edit reference: `https://developers.openai.com/api/reference/python/resources/images/methods/edit`
- Prompting guide: `https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide`

## Output contract

- Save a PNG file for each generated image.
- Save a JSON sidecar with:
  - `title`
  - `brief`
  - `mode`
  - `style_profile`
  - `size`
  - `model`
  - `reference_images`
  - `prompt`
  - `created_at`
  - `output_files`
- Print a Markdown image snippet using the absolute output path.
