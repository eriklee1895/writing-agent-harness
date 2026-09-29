# Runtime isolation — editorial variant v2

Mode: built-in image_gen edit.
Input role: v1 generated infographic is the edit target; preserve architecture and labels.
Original generation prompt: [v1 prompt](runtime-isolation-editorial-v1.prompt.md).
Output: `runtime-isolation-editorial-v2.png`.

```text
Edit the referenced technical infographic for PRINT READABILITY ONLY. Preserve the exact diagram content, all Chinese and English labels, the three-column layout, every box, and all dependency arrows.

Replace the ENTIRE backdrop with a perfectly uniform fully opaque warm ivory #faf9f5 background. No transparency anywhere; every pixel must have opaque alpha. Remove ALL dark haze, blurry gradients, vignetting, glass/frosted effects, drop shadows, glow, and dark edge shading. This is clean flat editorial print design.
Make the top title and subtitle fully legible in solid charcoal, with proper contrast against ivory. Make the footer takeaway and footnote equally crisp and legible. Use solid light terracotta, light blue, and light sage fills for column panels with solid darker headings. Retain existing hierarchy and line icons, but remove the penguin logo from the host kernel band and use only its centered text.
Technical invariants unchanged: container path directly uses shared host kernel; VM and microVM each retain independent Guest kernel; microVM has simplified VMM, not a removed kernel.
Do not add labels, do not change wording, do not remove existing diagram connections, and do not add decorative objects. Output one clean, fully opaque 3:2 infographic.
```
