# OpenAI Official Links

Use this file when you need the official documentation for GPT Image and the Images API.

## Core docs

- GPT Image 2 model page
  - `https://developers.openai.com/api/docs/models/gpt-image-2`
- Image generation guide
  - `https://developers.openai.com/api/docs/guides/image-generation`
- Images and vision guide
  - `https://developers.openai.com/api/docs/guides/images-vision`

## Python API references

- Create image
  - `https://developers.openai.com/api/reference/python/resources/images/methods/generate`
- Edit image
  - `https://developers.openai.com/api/reference/python/resources/images/methods/edit`
- Images resource overview
  - `https://developers.openai.com/api/reference/python/resources/images`

## OpenAI cookbook references

- GPT Image prompting guide
  - `https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide`
- Generate images with GPT Image
  - `https://developers.openai.com/cookbook/examples/generate_images_with_gpt_image`

## Default parameter guidance for this skill

- Default `size`: `auto`
- Explicit landscape document preset: `doc-hd` -> `1536x1024`
- Explicit 2K landscape document preset: `doc-2k` -> `2048x1152`
- Explicit 4K landscape document preset: `doc-4k` -> `3840x2160`
- Default `quality`: `auto`
- Default output format: PNG

## Notes

- If a provider rejects a request, verify the supported `size`, `quality`, and model names against the official docs first.
- Some OpenAI-compatible gateways lag behind the latest official model and parameter support.
