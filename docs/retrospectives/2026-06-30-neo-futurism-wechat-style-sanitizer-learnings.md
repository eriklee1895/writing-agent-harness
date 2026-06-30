# 2026-06-30 国风编辑风（neo-futurism）微信样式 + sanitizer 踩坑总结

OpenMontage 唐朝兴衰史文章发布过程中，新样式迭代踩了一系列微信sanitizer的坑，沉淀下来。

## 新样式：neo-futurism 国风编辑风

最终确定的风格参数（已沉淀在 render-wechat-article.mjs）：

- **色系**：深朱砂 `#7a1f0f` → 朱红 `#b53d1f` → 陶土 `#c45a3a` → 琥珀金 `#d4873e`，120度斜向渐变
- **H2标题**：全宽渐变块（非全出血）+ 金色编号块（米黄→琥珀半透明渐变，带细金线） + 白字 + 3px圆角 + 顶部内光
- **H3标题**：左侧4px朱红竖线
- **正文**：16px / 行高1.8 / 段间距16px / 无首行缩进
- **列表**：原生 `<ul>` + `list-style-type:disc`（朱红色），内部span放黑色文字
- **引用**：衬线斜体 + 上下朱红细线
- **图片**：4px圆角 + 轻阴影，图说中灰 `#7a736c`
- **Hero**：简洁标题区（26px黑字粗体 + 灰色副标题），无多余装饰线，适配微信公众号自带标题区

关键决策：放弃赛博朋克/电光青配色，改用和封面（唐朝国风水墨 + 橙色科技线）协调的暖陶土色系，整体气质统一。

## 微信 Sanitizer 已知行为（新发现）

在之前已知的外链/script/style/class过滤基础上，本轮新增验证：

| 写法 | 微信行为 | 正确替代 |
|------|---------|---------|
| 空 `<span>` 只带style做装饰（如bullet点、竖线） | **直接删除整个span标签**，留下纯文字缩进 | 用真实文字字符（●、■等）作为bullet内容，放进span里就不会被删 |
| `transform: translateY()` / `transform: scale()` | 被剥离 | 不要依赖transform做垂直对齐，用vertical-align:middle |
| 负 `text-indent`（悬挂缩进） | 被剥离 | 不用悬挂缩进，直接padding-left + inline-bullet |
| `position: relative/absolute` 用于装饰层 | 部分保留但子元素定位失效 | 装饰层放在同一个style行内，不要依赖多层定位 |
| 特殊方块字符 `■`（U+25A0） | 部分微信版本过滤为空 | 改用 `●`（U+25CF 实心圆），所有版本保留 |
| **所有自定义 bullet span**（哪怕 `●` + `&nbsp;` inline span） | **span被换行，bullet圆点单独占一行，文字下一行** | ✅ **必须用原生 `<ul>` + `list-style-type:disc/decimal`**：给 `<li>` 设朱红 `color`，内部用 `<span style="color:#1a1a1a">` 包黑字。这是唯一100%稳定的方案 |
| `box-shadow` 内阴影 `inset` | 保留 ✅ | 可用于H2顶部高光质感 |
| 多色渐变 `linear-gradient`（120deg 多stop） | 保留 ✅ | 可用于H2渐变背景 |
| 5MB+ 大图通过 `--try-cover` 自动上传封面 | 约50%概率timeout | 封面手动设置（正文图粘贴上传100%稳定） |

## 踩坑教训

1. **本地Chrome preview ≠ 微信最终效果**：本地preview用完整Blink渲染，没有sanitizer；粘贴进微信编辑器后会走一轮过滤。最终效果必须以草稿箱为准。
2. **装饰元素必须有文本内容**：微信sanitizer会把空元素当作冗余节点删除。但即使span里有内容也可能被换行到独立行——列表bullet必须用原生 `<ul>`/`<ol>` + `list-style-type`，这是浏览器内建的，不会被拆开。
3. **样式兼容性优先保守**：能用最朴素的inline-style（color、font-size、margin、padding、background渐变、原生list-style）就不要用新CSS特性或自己造轮子。微信内置浏览器是魔改X5/WebView，不同手机版本兼容性差异大。
4. **新样式迭代流程**：本地改 → render预览快速迭代 → 推送到草稿箱实际查看 → 再调，不要在本地改到"完美"再推——必然有sanitizer问题。

## 发布结果

- 文章：《我用AI做了一支"唐朝兴衰史"视频，全程没写一行剪辑代码》
- 最终发布 appmsgid：`100000580`
- 正文图片：8张全部上传到微信CDN成功
- 封面：手动设置（自动上传timeout）
- 新样式 `neo-futurism` 可用，未来国风/历史/文化类文章默认使用这个风格
