# OpenAI official links for gpt-image-2

Use this file when you need the canonical OpenAI documentation. All URLs are verified live as of 2026/06.

## Model

- gpt-image-2 model page: https://developers.openai.com/api/docs/models/gpt-image-2
- gpt-image-1.5 model page: https://developers.openai.com/api/docs/models/gpt-image-1.5
- gpt-image-1 model page: https://developers.openai.com/api/docs/models/gpt-image-1
- gpt-image-1-mini model page: https://developers.openai.com/api/docs/models/gpt-image-1-mini

## Guides

- Image generation guide (capabilities, constraints, error handling): https://developers.openai.com/api/docs/guides/image-generation
- Images and vision guide: https://developers.openai.com/api/docs/guides/images-vision

## API references

- Images resource overview: https://developers.openai.com/api/reference/python/resources/images
- `client.images.generate`: https://developers.openai.com/api/reference/python/resources/images/methods/generate
- `client.images.edit`: https://developers.openai.com/api/reference/python/resources/images/methods/edit

## Cookbook

- GPT Image prompting guide (verbatim text, style transfer, edits): https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide
- Generate images with GPT Image: https://developers.openai.com/cookbook/examples/generate_images_with_gpt_image

## Pricing

Live pricing is not in the model page. Query https://openai.com/api/pricing or the dashboard before quoting a cost to the user. The skill does not hard-code prices.

## Notes for this skill

- The Image API guide and the model page sometimes disagree on streaming support; the guide is treated as authoritative.
- The cookbook's example code still passes `input_fidelity="high"` to gpt-image-2 in some sections, contradicting the guide's instruction to omit it. Follow the guide.
- The cookbook has no CJK-specific text-rendering section. Apply the verbatim-text rules generally.
