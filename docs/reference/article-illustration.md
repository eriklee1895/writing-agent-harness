# Article Illustration Skill

`article-illustration` 用于生成文章封面、正文插图、章节视觉分隔图和技术图示。它是项目级写作 workflow 的视觉能力，不只是“文档插图”工具。

## Current Behavior

- 脚本：`.agents/skills/article-illustration/scripts/generate_article_illustration.py`
- 默认风格：`--style-profile auto`
- 文章正式出图时，优先明确指定风格，不要把 `auto` 当成审美决策。
- 文学、生活散文、文化现象文章不再默认钉死水彩；应按文章气质选择风格。

常用艺术风格：

- `editorial-atmospheric`：适合一般散文、文化观察、章节正文插图。
- `modern-guochao-editorial`：适合中国文化、城市、文旅、古风/国风主题。
- `cinematic-editorial`：适合舞台、现场、城市夜色和具有场景感的文章。
- `watercolor-illustration`：只在确实需要柔和绘画感时使用。

## Prompt Pattern

优秀的正文插图 prompt 不只是描述“画什么”，还要说明：

- 放在文章哪一节；
- 承担什么阅读功能；
- 用什么视觉隐喻承接论点；
- 需要出现哪些具体可见对象；
- 明确不要变成什么俗套方向；
- 明确移动端正文阅读、留白、不要文字等约束。

通用结构：

```text
正文插图，放在<文章标题>的<章节名>章节。画面表现：<文章论点或传播机制>，通过<一个具体视觉隐喻>连接<3-5 个可见对象或场景元素>。重点是<这张图要帮助读者理解的判断>，不是<需要避免的俗套方向>。风格<明确风格名或审美边界>，画面应有留白，适合移动端正文阅读。不要任何文字、字幕、logo、二维码、箭头或信息图标签。
```

## Example: Cultural Tourism Body Illustration

用于文章：

- Article: `content/source/2026-06-08-luolebai-handanxuebu/article.md`
- Section: `泼天的流量，邯郸接住了`
- Style profile: `modern-guochao-editorial`
- Size: `portrait-hd`
- Local archive output: `.local-archive/2026-06-08-落了白-邯郸学步/images/handan-traffic-caught-by-city.png`
- Metadata: `docs/assets/article-illustration/handan-traffic-caught-by-city.json`

为什么这次效果好：

- 明确了图片在文章中的位置和功能：从短视频热闹过渡到城市文旅分析。
- 用具体视觉隐喻承接论点：手机短视频里的旋律，以声波和光带形式落到城市。
- 把文化元素列成可见对象：邯郸古城、赵文化礼宴、成语典故、学步桥、城市夜色。
- 明确反风格：不是旅游广告，不要文字、字幕、logo、二维码、箭头或信息图标签。
- 明确阅读场景：微信公众号正文、移动端阅读、需要留白。

Brief:

```text
正文插图，放在微信公众号文章《我只是听了首〈落了白〉，怎么就掉进了邯郸学步宇宙？》的‘泼天的流量，邯郸接住了’章节。画面表现：一段来自手机短视频的《落了白》旋律，像流动的声波与光带，从竖屏手机里延展出来，落到邯郸古城、赵文化礼宴、成语典故、学步桥意象和城市夜色之间。重点是‘短视频流量被城市文旅接住’，不是旅游广告。风格克制、有文化感、现代国潮编辑插图，画面应有留白，适合移动端正文阅读。不要任何文字、字幕、logo、二维码、箭头或信息图标签。
```

Command:

```bash
uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
  --title "handan-traffic-caught-by-city" \
  --brief "正文插图，放在微信公众号文章《我只是听了首〈落了白〉，怎么就掉进了邯郸学步宇宙？》的‘泼天的流量，邯郸接住了’章节。画面表现：一段来自手机短视频的《落了白》旋律，像流动的声波与光带，从竖屏手机里延展出来，落到邯郸古城、赵文化礼宴、成语典故、学步桥意象和城市夜色之间。重点是‘短视频流量被城市文旅接住’，不是旅游广告。风格克制、有文化感、现代国潮编辑插图，画面应有留白，适合移动端正文阅读。不要任何文字、字幕、logo、二维码、箭头或信息图标签。" \
  --style-profile modern-guochao-editorial \
  --size portrait-hd \
  --quality auto \
  --language zh \
  --output-dir content/source/2026-06-08-luolebai-handanxuebu/assets/images
```
