# Case: 《过时不候》文学绘本式插图

## Context

- Article: `content/drafts/article-draft.md`
- Style profile: `literary-picture-book`
- Size: `wechat-cover-hd` + `doc-hd`
- Documentation images:
  - `docs/assets/article-illustration/guoshibu-cover.png`
  - `docs/assets/article-illustration/guoshibu-procrastination.png`
  - `docs/assets/article-illustration/guoshibu-firefly.png`

![过时不候封面](../../../assets/article-illustration/guoshibu-cover.png)

## Why It Worked

- 三图色调统一但不重复：暖金 + 墨蓝、暖橙 + 冷灰、森绿 + 金光。
- `flat-illustration` 在 gpt-image-2 上稳定，适合公众号配图这种“不需要极致细节但需要气质统一”的场景。
- `watercolor + hand-drawn linework` 增加手绘温度，降低 AI 塑料感。
- `generous negative space` 保证手机窄屏阅读时主体清楚、不杂乱。
- 三幅图分别承接“过期”“拖延”“捕捉”三个核心意象。

## Reusable Mechanism

- 先判断文章核心意象数量，再决定封面和正文插图数量。
- 每张图对应一个独立阅读功能，不要为了配图而配图。
- 散文/哲思文章可以用低饱和色调 + 留白 + 手绘质感，制造温度和余味。
- 封面可以抓眼，正文图应更克制，避免抢走文字节奏。

## Do Not Copy

- 不要把所有散文都固定成水彩或绘本。
- 不要机械复用火柴、房间、萤火虫等意象。
- 不要把 `literary-picture-book` 当成默认风格；它只适合需要柔和、克制、文学感的文章。
