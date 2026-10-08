# Article readiness — 2026-09-29

## Verdict

**Blog published; WeChat draft reviewed.** 用户已确认公众号草稿`<见 .local-archive 发布态>`无误，并授权发布博客。博客已上线且完成线上验证；公众号尚未收到正式发表/群发信息。

## Scope

- Canonical：[index.md](index.md)。
- 检查方式：fix-and-check；已完成用户明确要求的polish-article精修，收紧重复与转场，不改核心论点和章节顺序。
- 事实基线：本轮对话截至2026-09-29的官方原文、性能规范及论文正文。未进行产品同条件实测，不以这份检查报告新增厂商实现断言。

## Done

- 标题、开头、技术比较与结尾围绕个人工作环境连续性展开；容器/VM/microVM及运行生命周期分开讲。
- 两张技术表格分别承担运行方式比较和实现机制比较，保留用户要求的技术深度。
- Manus四月Cloud Computer与九月2.0区别清楚；Work/Cowork各自的执行与持久化边界带官方来源；microVM数字保留测量口径；TClone标注研究状态。
- Markdown必需frontmatter齐全，summary≤60字，无author或渠道发布ID，无TODO/TBD/空图片引用。
- ImageGen图的提示词、编辑链和manifest齐全；选择版本为RGB不透明PNG，Mermaid技术参照保留。
- 生成暖纸张风格渠道预览，canonical source与派生稿保持单向关系，图片引用origin。
- HTML静态检查：无script、外部href、base64图片、table标签；图片data-local-path有效。
- 浏览器检查：390/390、430/430、1280/1280（scrollWidth/clientWidth）；图片成功加载；430px时未发现超出视口的article子元素；无页面错误。
- 已目视检查移动端开场、两张表格、分层图和桌面开场。
- 补充两张竖幅信息图后重新检查：全篇3张图片均加载成功；390px下无横向溢出，两张新增图的主要标签可读，来源提示词与manifest已更新。
- 后续按用户要求增加Manus2.0首图和结尾场景图，当前共5张。列宽优化为20/40/40与20/32/48，首列标签保持单行；360px与390px复核无溢出，图片全部加载。
- 重渲染使用文章专用`content/wechat/2026-09-29-cloud-agent-runtime/render-preview.mjs`，保留此次列宽优化，不修改共享renderer默认。
- 首尾图按用户反馈加入品牌标识，官方素材来源及SVG/PNG参考已登记manifest；正文选用首尾v2，旧图保留。仍为概念插图，非官方界面截图。
- Cloudflare小节图改为依据官方Workspace/执行后端图的中文重绘，区分binding直连与FUSE挂载同步；图注保留官方来源链接。原泛化架构图退出正文但保留资产。
- 全文精修后保留16处来源链接、5张图、两张表格及此前视觉修改；中文篇幅缩减约10%。逐段检查无超过约240中文字符的正文段落，移动端重新验证无溢出。

## Remaining before external publication

- 用户已确认精修预览并要求继续；仍需检查最终微信草稿并决定正式发表。
- 发布封面已生成、上传并设置；五张正文图在保存后的微信预览中均已加载且尺寸非零。
- 微信实际渲染保留两张表的定制列宽，未发现单元格溢出或正文外链；图内细注可配合正文与图片放大查看。
- 原创声明由用户最终检查时决定，本次未自动勾选。
- 如进入博客，需要独立的渠道元数据、构建及页面验证。

## Evidence

- 渠道输出：[index.html](../../wechat/2026-09-29-cloud-agent-runtime/index.html)。
- QA截图位于`content/drafts/2026-09-29-cloud-agent-runtime/qa/`，属于本机scratch，不作为发布素材。
- 图像来源与使用状态：[assets/manifest.json](assets/manifest.json)。

## Handoff

Blog：https://eriklee-blog.pages.dev/posts/2026-09-29-cloud-agent-runtime/ 已公开上线。微信公众号草稿与博客发布是独立状态，公众号正式发表仍由用户决定。
