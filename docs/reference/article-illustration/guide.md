# Article Illustration Guide

`article-illustration` 用于生成文章封面、正文插图、章节视觉分隔图和技术图示。它是项目级写作 workflow 的视觉能力，不只是“文档插图”工具。

## Current Behavior

- 脚本：`.agents/skills/article-illustration/scripts/generate_article_illustration.py`
- 默认风格：`--style-profile auto`
- 文章正式出图时，优先明确指定风格，不要把 `auto` 当成审美决策。
- 文学、生活散文、文化现象文章不再默认钉死水彩；应按文章气质选择风格。

## Style Profiles

- `editorial-atmospheric`：适合一般散文、文化观察、章节正文插图。
- `modern-guochao-editorial`：适合中国文化、城市、文旅、古风/国风主题。
- `cinematic-editorial`：适合舞台、现场、城市夜色和具有场景感的文章。
- `watercolor-illustration`：只在确实需要柔和绘画感时使用。
- `literary-picture-book`：扁平插画 + 水彩晕染 + 手绘线条。适合个人散文、随笔、哲思文章；强调留白、克制、文学感，色调偏暖金、墨蓝、森绿等低饱和度组合。

## Prompt Pattern

优秀的正文插图 prompt 不只是描述“画什么”，还要说明：

- 放在文章哪一节。
- 承担什么阅读功能。
- 用什么视觉隐喻承接论点。
- 需要出现哪些具体可见对象。
- 明确不要变成什么俗套方向。
- 明确移动端正文阅读、留白、不要文字等约束。

通用结构：

```text
正文插图，放在<文章标题>的<章节名>章节。画面表现：<文章论点或传播机制>，通过<一个具体视觉隐喻>连接<3-5 个可见对象或场景元素>。重点是<这张图要帮助读者理解的判断>，不是<需要避免的俗套方向>。风格<明确风格名或审美边界>，画面应有留白，适合移动端正文阅读。不要任何文字、字幕、logo、二维码、箭头或信息图标签。
```

## Stable Rules

- 封面必须服务标题和转发场景；正文插图必须服务阅读理解、情绪过渡或传播记忆点。
- 移动端优先，避免高密度细节和小字。
- 不要让 image model 直接生成精确中文标题；需要文字时优先本地 overlay exact text。
- 技术文章优先使用简洁信息图、结构图、流程图或有明确语义的插图。
- 散文、文化观察、音乐和城市文章优先选能承载气质的 editorial illustration，不要默认套技术图表框架。

## Case Memory

历史案例放在 [cases/](cases/)：

- [2026-06-08-handan-cultural-tourism.md](cases/2026-06-08-handan-cultural-tourism.md)
- [2026-06-07-guoshibu-literary-picture-book.md](cases/2026-06-07-guoshibu-literary-picture-book.md)
